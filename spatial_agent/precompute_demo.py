"""Pre-generate reusable artifacts for the picture-demo presentation path.

Examples:

    # Fast local preparation for every picture (YOLO manifest, annotation, crop)
    python3 -m spatial_agent.precompute_demo --all-scenes

    # Default five-scene walkthrough: six representative object previews,
    # object 3D jobs and one Aholo spatial-generation record per scene.
    python3 -m spatial_agent.precompute_demo --external --wait

The command is intentionally idempotent.  Every artifact is keyed by its
source/prompt fingerprint, so a valid result is reused; a changed source
picture or user prompt goes through the ordinary online implementation.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from spatial_agent.config import get_settings
from spatial_agent.demo import (
    ANNOTATION_ENDPOINT_WIDTH,
    DEMO_ARTIFACTS,
    _group_fingerprint,
    _run_spatial_generation,
    _select_scenes,
    build_demo_component_design_advice,
    demo_spatial_generation_cache_key,
    find_demo_group,
    list_demo_component_groups,
    load_demo_annotated_preview,
    load_demo_component_crop,
)
from spatial_agent.graph import SpatialAgentGraph
from spatial_agent.models import DemoAnalyzeRequest, DemoComponentPreviewRequest
from spatial_agent.providers.aholo_world import AholoWorldClient


DEFAULT_REGION = "南京 · 江苏"
DEFAULT_GOAL = "对现有构件进行 360° 审计，识别可能被保留、复用或再生的构件，为后续改造与资源循环提供依据。"
DEFAULT_SPATIAL_PROMPT = "保留原空间结构与尺度，更新为明亮、低碳、可逆施工的现代室内空间"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="预热分析用素材，保留在线缺失回退")
    result.add_argument("--scene", action="append", default=[], help="指定 scene id；可重复使用")
    result.add_argument("--all-scenes", action="store_true", help="处理 data/samples/pictures 下全部 11 张样例")
    result.add_argument("--external", action="store_true", help="允许调用已配置的百炼与 Aholo；省略时只生成本地 YOLO/裁切")
    result.add_argument("--wait", action="store_true", help="轮询 Aholo 任务至完成或超时，并保存最新状态")
    result.add_argument("--all-eligible", action="store_true", help="为所有符合翻新条件的构件生成预览/对象 3D；默认每类别选一个代表")
    result.add_argument("--skip-previews", action="store_true", help="不调用 Design Agent 或 qwen-image；适合只补跑 3D")
    result.add_argument("--skip-world", action="store_true", help="不提交 Aholo 空间再生")
    result.add_argument("--skip-object-3d", action="store_true", help="不提交 Lux3D 对象图生 3D")
    result.add_argument("--skip-analysis-cache", action="store_true", help="不生成默认全链路响应缓存")
    result.add_argument("--max-components", type=int, default=0, help="最多处理多少个代表对象；0 表示不设上限")
    result.add_argument("--max-worlds", type=int, default=0, help="最多处理多少个场景 3D；0 表示不设上限")
    result.add_argument("--region", default=DEFAULT_REGION)
    result.add_argument("--spatial-prompt", default=DEFAULT_SPATIAL_PROMPT)
    result.add_argument("--max-wait-seconds", type=int, default=900)
    return result


def selected_scenes(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.scene:
        return _select_scenes(args.scene)
    if args.all_scenes:
        fixture_scenes = _select_scenes([])
        # _select_scenes([]) intentionally means default selection; load the
        # remaining ids from the public catalog without duplicating fixture IO.
        from spatial_agent.demo import _load_fixture
        return _load_fixture()["scenes"]
    return _select_scenes([])


def preview_candidates(scenes: list[dict[str, Any]], *, all_eligible: bool) -> list[dict[str, Any]]:
    scene_ids = {scene["id"] for scene in scenes}
    candidates = [
        item for item in list_demo_component_groups([scene["id"] for scene in scenes])
        if item["scene_id"] in scene_ids and item.get("can_generate_preview")
    ]
    if all_eligible:
        return candidates
    # A single representative from every detected type provides a complete,
    # varied presentation without silently submitting dozens of billable image
    # and mesh jobs.  --all-eligible intentionally expands this scope.
    chosen: list[dict[str, Any]] = []
    seen_categories: set[str] = set()
    for item in sorted(candidates, key=lambda group: float(group["confidence"]), reverse=True):
        if item["category"] not in seen_categories:
            chosen.append(item)
            seen_categories.add(item["category"])
    return chosen


async def materialize_local(scenes: list[dict[str, Any]]) -> None:
    for scene in scenes:
        load_demo_annotated_preview(scene["id"], ANNOTATION_ENDPOINT_WIDTH)
    for group in list_demo_component_groups([scene["id"] for scene in scenes]):
        load_demo_component_crop(group["id"])


async def warm_component_preview(group_id: str, region: str, graph: SpatialAgentGraph) -> dict[str, Any]:
    """Use the same endpoint logic as a user click, including local retention."""
    from spatial_agent.app import demo_component_preview

    advice = await build_demo_component_design_advice(group_id, region=region, agent=graph)
    response = await demo_component_preview(
        group_id,
        DemoComponentPreviewRequest(
            region=region,
            advice={key: advice[key] for key in ("material", "color", "surface", "construction", "rationale")},
        ),
    )
    return response


async def warm_lux3d_model(
    group_id: str,
    graph: SpatialAgentGraph,
    aholo: AholoWorldClient,
    *,
    wait: bool,
    max_wait_seconds: int,
) -> dict[str, Any]:
    scene, group, _ = find_demo_group(group_id)
    fingerprint = _group_fingerprint(scene, group)
    model_key = "lux3d:G1-Turbo:glb"
    cached = DEMO_ARTIFACTS.cached_model(group_id, fingerprint, model_key)
    if cached:
        if not wait or cached.get("status") in {"SUCCEEDED", "FAILED", "CANCELED"}:
            return {"cache_hit": True, **cached}
        record = dict(cached)
    else:
        # Lux3D needs an HTTP(S) URL.  Aholo Asset accepts the local component
        # crop and returns a provider-reachable URL, so no public OSS bucket is
        # required just for demonstration precompute.
        from spatial_agent.demo import demo_component_crop_path
        crop_path = demo_component_crop_path(group_id)
        asset_url = await aholo.upload_local_file(str(crop_path))
        submitted = await graph.lux3d.image_to_3d([asset_url], version="G1-Turbo", wait=False)
        record = {**submitted, "asset_url": asset_url, "provider": "aholo-lux3d-cn"}
    task_id = str(record.get("task_id") or "")
    if wait and task_id:
        attempts = max(1, max_wait_seconds // 10)
        for index in range(attempts):
            task = await graph.lux3d.get_task(task_id)
            status = task.get("status")
            record["task"] = task
            if status == 3:
                record["status"] = "SUCCEEDED"
                break
            if status in {4, 6}:
                record["status"] = "FAILED" if status == 4 else "CANCELED"
                break
            record["status"] = "running"
            if index + 1 < attempts:
                await asyncio.sleep(10)
    DEMO_ARTIFACTS.save_model(group_id, fingerprint, model_key, record)
    return record


async def warm_world(
    scene: dict[str, Any],
    prompt: str,
    aholo: AholoWorldClient,
    *,
    wait: bool,
    max_wait_seconds: int,
) -> dict[str, Any]:
    response = await _run_spatial_generation(aholo, scene, prompt)
    world_id = str(response.get("world_id") or "")
    if not wait or not world_id or response.get("status") in {"mock", "failed", "SUCCEEDED"}:
        return response
    attempts = max(1, max_wait_seconds // 10)
    for index in range(attempts):
        status = await aholo.world_status(world_id)
        normalized = {
            **response,
            "status": status.get("status") or response.get("status"),
            "world": status,
        }
        if status.get("viewer_urls"):
            normalized["viewer_urls"] = status["viewer_urls"]
        if status.get("imagery_url"):
            normalized["imagery_url"] = status["imagery_url"]
        if str(normalized["status"]).upper() in {"SUCCEEDED", "FAILED", "CANCELED", "TIMEOUT", "REJECTED"}:
            response = normalized
            break
        response = normalized
        if index + 1 < attempts:
            await asyncio.sleep(10)
    from spatial_agent.demo import _scene_fingerprint
    DEMO_ARTIFACTS.save_world(
        scene["id"],
        _scene_fingerprint(scene),
        demo_spatial_generation_cache_key(prompt),
        response,
    )
    return response


async def run(args: argparse.Namespace) -> dict[str, Any]:
    scenes = selected_scenes(args)
    await materialize_local(scenes)
    result: dict[str, Any] = {
        "scenes": [scene["id"] for scene in scenes],
        "local": DEMO_ARTIFACTS.status(),
        "external": {"enabled": False, "previews": [], "models": [], "worlds": []},
    }
    if not args.external:
        return result

    settings = get_settings()
    graph = SpatialAgentGraph(settings)
    aholo = AholoWorldClient(settings)
    if not graph.bailian.enabled or not aholo.enabled or not graph.lux3d.enabled:
        raise RuntimeError(
            "外部预热需要 USE_LLM=true、USE_EXTERNAL_TOOLS=true，以及 DASHSCOPE/LUX3D/AHOLO 三个密钥。"
        )
    candidates = preview_candidates(scenes, all_eligible=args.all_eligible)
    if args.max_components > 0:
        candidates = candidates[:args.max_components]
    result["external"]["enabled"] = True
    for candidate in candidates:
        if not args.skip_previews:
            preview = await warm_component_preview(candidate["id"], args.region, graph)
            result["external"]["previews"].append({"id": candidate["id"], "status": preview.get("status"), "cache_hit": bool(preview.get("cache_hit"))})
        if not args.skip_object_3d:
            model = await warm_lux3d_model(
                candidate["id"], graph, aholo, wait=args.wait, max_wait_seconds=args.max_wait_seconds,
            )
            result["external"]["models"].append({"id": candidate["id"], "status": model.get("status"), "task_id": model.get("task_id")})
    if not args.skip_world:
        world_scenes = scenes[:args.max_worlds] if args.max_worlds > 0 else scenes
        for scene in world_scenes:
            world = await warm_world(scene, args.spatial_prompt, aholo, wait=args.wait, max_wait_seconds=args.max_wait_seconds)
            result["external"]["worlds"].append({"id": scene["id"], "status": world.get("status"), "world_id": world.get("world_id"), "cache_hit": bool(world.get("cache_hit"))})
    if not args.skip_analysis_cache:
        from spatial_agent.demo import analyze_demo
        request = DemoAnalyzeRequest(
            scene_ids=[scene["id"] for scene in scenes],
            user_goal=DEFAULT_GOAL,
            region=args.region,
            spatial_prompt=args.spatial_prompt,
            include_web=False,
        )
        _, analysis = await analyze_demo(request, agent=graph, aholo_world=aholo)
        result["external"]["analysis"] = {"status": analysis.get("status"), "cache_hit": bool(analysis.get("cache_hit"))}
    result["cache"] = DEMO_ARTIFACTS.status()
    return result


def main() -> None:
    args = parser().parse_args()
    outcome = asyncio.run(run(args))
    print(json.dumps(outcome, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
