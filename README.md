# Second Life View · Spatial Agent + React

这是一个面向建筑改造与空间再利用的全栈黑客松 demo。React 前端已经与 **FastAPI + LangGraph + YOLO-World + Evidence / Research / Design Agent + Aholo Spatial Gen** 融合；Windows 端的 Insta360 CameraSDK 仍保持解耦，后续只需要替换现场素材入口。

## Demo 故事

1. Windows 上传一张全景图和 YOLO JSON（或直接调用 demo fixture）。
2. Perception Agent 把目标变成结构化 `SpatialObject`，并标记材质、状态、再利用判断和证据来源。
3. Evidence Agent 检查置信度与必填字段；如果柜体背面、材质或结构状态不确定，图在证据闸门暂停，并返回 `capture_actions`。
4. Windows bridge 执行 `zoom_region`/`request_user_photo`，把新图和 YOLO JSON 回传；同一个 run 恢复。
5. Research Agent 从本地材料知识库检索依据，并可显式开启网页搜索和本地机会连接器；每条结果标注 `verified`、`inferred` 或 `to_confirm`，再传给 Design Agent 生成“保留结构、替换表面”的翻新方案。
6. 可选调用国内 Lux3D：`POST /api/v1/reconstruct`，提交图片 URL 后返回异步任务 ID；默认 mock 便于离线展示。
7. Windows 的素材演示可以直接使用 Linux 本地文件；OSS 适配器保留为可选部署能力，不影响本地 demo。

## 运行

### 单服务完整 Demo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
cp .env.example .env  # 只在本机填写密钥，文件已被 gitignore
npm start
```

访问 `http://localhost:8000/create/project`，依次进入“项目设置 → 现场素材接入 → 分析处理完成”。`npm start` 会先构建 React，再由 FastAPI 同时托管 SPA、样例图片和 API。API 文档仍位于 `http://localhost:8000/docs`。

如果 `8000` 已被占用，可运行 `PORT=8011 npm start`。

没有任何密钥和相机也可以运行：

- 第二页读取 `data/samples/pictures` 的 11 张全景图，并默认选择前 5 张作为 Demo 输入；
- YOLO-World 使用仓库内可复现的跨视角检测/去重 fixture（589 个原始框、263 个构件组）；
- Evidence Agent 对低置信度与缺失字段设闸，Demo 自动模拟补拍并写入 `verified` 证据；
- Research / Design Agent 输出本地知识库支撑的翻新草案；
- Aholo 未启用时返回带预览图的 mock，启用 `AHOLO_API_KEY` 和 `USE_EXTERNAL_TOOLS=true` 后会上传首张场景并提交 Spatial Gen。

### 前后端开发模式

```bash
# terminal 1
npm run dev:api

# terminal 2
npm run dev
```

Vite 会把 `/api` 和 `/demo-assets` 代理到 `http://127.0.0.1:8000`。

## API 快速演示

```bash
# 查看第二页使用的本地样例素材
curl -s http://localhost:8000/api/v1/demo/scenes | jq

# 一次执行 Aholo → YOLO/Perception → Evidence → Research/Design 全链路
curl -s -X POST http://localhost:8000/api/v1/demo/analyze \
  -H 'content-type: application/json' \
  -d '{
    "scene_ids":["hotel_room","en_suite"],
    "user_goal":"评估空间构件的再利用机会并提出低碳翻新方案",
    "region":"南京 · 江苏",
    "spatial_prompt":"保留布局，更新为明亮、低碳、可逆施工的现代空间"
  }' | jq

# 启动主动感知 run；省略 detections 会载入演示木柜和门
curl -s -X POST http://localhost:8000/api/v1/runs \
  -H 'content-type: application/json' \
  -d '{"user_goal":"评估旧木柜是否值得翻新，并给出现代化方案"}' | jq

# 把上一步返回的 run_id 和 capture_actions[0].id 填入；Windows bridge 也使用同一个接口
curl -s -X POST http://localhost:8000/api/v1/runs/<run_id>/capture/complete \
  -H 'content-type: application/json' \
  -d '{"run_id":"<run_id>","action_id":"<action_id>","image_url":"https://edge.example/frame-close.jpg"}' | jq

# 交互式重做设计
curl -s -X POST http://localhost:8000/api/v1/runs/<run_id>/design \
  -H 'content-type: application/json' \
  -d '{"brief":"保留木柜结构，换成浅色耐磨表面和黑色可拆卸五金"}' | jq

# 国内 Lux3D 图生 3D；没配 key 时返回 mock task
curl -s -X POST http://localhost:8000/api/v1/reconstruct \
  -H 'content-type: application/json' \
  -d '{"run_id":"<run_id>","image_url":"https://edge.example/frame-close.jpg","version":"G1-Turbo"}' | jq

# Tripo V3 对象级异步建模；输入应是 YOLO crop 的实体图 URL
curl -s -X POST http://localhost:8000/api/v1/tripo/reconstruct \
  -H 'content-type: application/json' \
  -d '{"image_url":"https://signed-oss-url/object.jpg","wait":false}' | jq

# Windows CameraSDK bridge：首帧直接创建 run，并把相机元数据写入审计状态
curl -s -X POST http://localhost:8000/api/v1/camera/frame \
  -H 'content-type: application/json' \
  -d '{"image_url":"https://signed-oss-url/room.jpg","detections":[{"class":"wood_cabinet","bbox":[0.1,0.2,0.4,0.8],"confidence":0.9}],"metadata":{"camera_model":"Insta360 X5","projection":"equirectangular","frame_id":"f-001"}}' | jq

# 查询 Lux3D 对象建模任务（使用国内 Skill 的 task_id）
curl -s http://localhost:8000/api/v1/reconstruct/<task_id> | jq

# MP4/INSV 直接上传 Aholo Asset 并提交 World 3DGS
curl -s -X POST http://localhost:8000/api/v1/3dgs/reconstruct-upload \
  -F 'file=@./room.mp4' -F 'quality=low' | jq

# 本地 JPG + prompt → Aholo Spatial Gen（AI 空间改造生成）
curl -s -X POST http://localhost:8000/api/v1/3dgs/spatial-gen-upload \
  -F 'file=@./room.jpg' \
  -F 'prompt=保留房间布局，将沙发替换成深蓝色布艺，增加现代低碳家具和暖色灯光' | jq

# World 完成后下载本地可视化文件
curl -s -X POST http://localhost:8000/api/v1/3dgs/world/3FO4K4QU7R1T/download | jq

# 直接在官方 Aholo Viewer 打开完成的 SPZ（浏览器会收到 307 跳转）
open "http://localhost:8000/api/v1/3dgs/world/3FO4K4QU7R1T/open?asset=spz"

# Research Agent：默认本地 RAG + 本地机会记录；include_web=true 才访问网页搜索
curl -s -X POST http://localhost:8000/api/v1/research \
  -H 'content-type: application/json' \
  -d '{"run_id":"<run_id>","query":"旧木柜翻新和本地回收","region":"本地","include_web":false}' | jq
```

`/open?asset=spz`、`ply`、`lod` 会直接跳转到 Aholo Viewer；`pano` 会打开
Spatial Gen 返回的全景图。这个路径不需要把文件再次拖入网页。Studio 的
`/editor?projectId=...` 是另一套登录后的项目编辑器，不能把 World ID 当作
Project ID 使用；如果需要 Studio 项目，必须在 Studio 登录态下创建或导入项目。

`GET /api/v1/runs/{run_id}/events` 返回审计事件；`GET /api/v1/runs/{run_id}/stream` 提供 SSE，便于未来前端实时显示“相机补拍 → VLM → 检索 → 设计”的过程。

## Agent 和状态

`spatial_agent/graph.py` 使用 LangGraph `StateGraph`：`supervisor → perception → evidence`，证据不足时结束本轮并等待 `/capture/complete`；证据充分后进入 `research → design`。`RunState` 同时保存对象、Evidence、空间关系、待执行 CaptureAction、来源、设计结果、错误和事件，所以每一次判断都可以回放和解释。

当前能力边界：YOLO-World 已验证“ERP 全景 → 透视视图 → 检测框 → 跨视角 ComponentBatch → 实体 crop”；路径判断是可解释规则引擎。Agent 契约预留 `segmentation`，但当前 Pipeline B 尚未把像素级 mask 接入后端。图片翻新可以调用 qwen-image 生成效果图；若需要严格只修改 bbox 内区域，还需要增加 mask/inpainting 适配。

Research Agent 当前采用离线优先的轻量检索：`data/knowledge/material_reuse.json` 作为本地语料，按关键词召回；`local_opportunities.json` 是可替换的机会连接器示例。`include_web=true` 会尝试网页搜索。它不是生产级向量数据库或真实城市商家 API，网页结果和机会记录分别标记为 `inferred` 与 `to_confirm`。

外部模型适配器在 `spatial_agent/providers/`：

- 百炼 OpenAI-compatible：文本 `deepseek-v4-pro`，视觉 `qwen3.8-max`，图片生成 `qwen-image-3.0-pro`。
- Aholo Lux3D 国内 Skill：使用 `/root/.codex/skills/lux3d-cn/lux3d_client.py`，固定 `LUX3D_REGION=cn` 和 `https://api.aholo3d.cn`，不会使用海外端点。
- Aholo World：通过国内 Asset/World SDK 或 REST 提交空间重建。
- Aholo Spatial Gen：`POST /api/v1/3dgs/spatial-gen-upload` 对应 MCP 的 `world_generate(localPath, prompt)`，用于 AI 生成/改造空间；结果仍返回 World ID，可查询 `imagery.panoUrl`（AI 全景改造效果）、SPZ 和 PLY。
- Research Agent：本地 `data/knowledge/material_reuse.json` 是离线 RAG 语料，`local_opportunities.json` 是可替换的城市机会连接器；`include_web=true` 时增加网页检索线索。网页结果只标记为 `inferred`，实时商家记录标记为 `to_confirm`。
- Tripo V3：`POST /api/v1/tripo/reconstruct`，适合单个实体图或同一物体的 2-4 个视角；任务查询为 `GET /api/v1/tripo/tasks/{task_id}`。Tripo 官方 API 没有房间级全景视频重建接口。
- OSS：作为可选扩展保留；没有 RAM AccessKey 时不影响本地文件演示。

默认关闭外部调用。配置 `DASHSCOPE_API_KEY`/`LUX3D_API_KEY` 后，再显式设置 `USE_LLM=true` 或 `USE_EXTERNAL_TOOLS=true`。

## Windows + SSH 真机桥接

相机 USB 线连接 Windows，不通过 SSH 让 Linux 加载 Windows DLL。仓库现在提供了可运行的 `windows_camera_bridge/`：它在 Windows 使用 `DeviceDiscovery → Open → TakePhoto → DownloadCameraFile → Close`，可选用 MediaSDK 把 `.insp` 拼接为 ERP JPEG；Linux 通过 SSH **反向**隧道调用该网关、拉取图片并直接创建或恢复 LangGraph run。

Linux 侧新增接口：

- `GET /api/v1/camera/status`、`GET /api/v1/camera/files`
- `POST /api/v1/camera/capture`：拍照、下载、可选拼接、保存素材并开始/恢复分析
- `POST /api/v1/camera/download`：下载相机现有文件并可选拼接分析
- `POST /api/v1/camera/frame`：保留给已有 Windows 客户端直接提交图片 URL 和检测 JSON 的兼容入口

完整的 Windows 驱动、构建、SSH 隧道、服务器 `.env` 和 curl 验证步骤位于 `windows_camera_bridge/README.md`。网关始终监听 Windows `127.0.0.1`，服务器端也只接受 `http://127.0.0.1:<反向转发端口>` 作为网关 URL。

## 安全与部署

百炼和 Aholo key 只放权限为 `600` 的本地 `.env`、云 Secret 或进程环境变量；不要提交 `百炼api.txt`、`.env` 或 SDK 压缩包。SkillHub 的 Lux3D 国内 Skill 已安装在 `/root/.codex/skills/lux3d-cn`，版本 4.1.2。

## TAY-LI Pipeline B 融合

`origin/TAY-LI` 的 Pipeline B 现在作为一个检测工具层接入，而不是另起一套 Agent：

- `pipeline/panorama.py`：ERP 全景图到透视视图和 yaw/pitch 投影；
- `pipeline/detection.py`：YOLO-World 开放词汇检测；
- `pipeline/grouping.py`：跨重叠视角去重，形成 ComponentBatch；
- `pipeline/assessment.py`：只根据可观测事实评估 KEEP_IN_PLACE、DIRECT_REUSE、REFURBISH、REPURPOSE、MATERIAL_RECOVERY、DISPOSAL；
- `spatial_agent/yolo_adapter.py`：把 `detections.json` / `batches.json` 标准化为 Perception Agent 的 Detection/Evidence 输入。

可以直接使用已有真实 fixture 验证融合：

```bash
curl -s http://localhost:8000/api/v1/yolo/scenes | jq
curl -s -X POST http://localhost:8000/api/v1/runs \
  -H 'content-type: application/json' \
  -d '{"scene_slug":"hotel_room"}' | jq '.status, .metadata.scene_slug, (.objects | length), (.capture_actions | length)'
```

如果要重新从全景图跑 YOLO，需要安装 `ultralytics` 和权重，再运行 `python pipeline/run_demo.py --scene hotel_room`；没有 GPU 时可直接用提交的 fixture，不会阻塞 Agent 集成测试。

当前服务器已经安装 `ultralytics`，并下载 `weights/yolov8s-worldv2.pt`。RTX 5090 上的 `hotel_room` smoke test 已完成 10 个透视视角、25 个检测对象和 14 个 ComponentBatch。权重文件被 `.gitignore` 忽略，部署时由安装脚本或模型制品提供。

对 `data/samples/pictures` 中的 11 张新全景图批量运行时，结果为 589 个原始检测框、263 个跨视角 ComponentBatch；每张图片使用 10 个 ERP 投影视角。这个目录的输入不要求与 TAY-LI fixture 同名，接入 Windows 时只需把检测 JSON 映射到 `Detection` 契约即可。

### 3DGS 与 Lux3D 的区别

Aholo 有两条不同能力链，接口不能混用：

- `POST /api/v1/reconstruct`：Lux3D G1/G1-Turbo，适合单个柜体、门、椅子等物体图生 3D；国内 Skill 直接提交公开图片 URL。
- `POST /api/v1/3dgs/reconstruct`：Aholo World，适合室内空间 3DGS。全景 `INSV` 或普通视频可单条提交；纯图片重建必须至少 20 张。World 的本地文件必须先经过 Aholo Asset 上传，代码提供 `AholoWorldClient.upload_local_file()`。
- `GET /api/v1/3dgs/world/{world_id}`：查询 World 异步状态。
- `GET /api/v1/3dgs/world/{world_id}/open?asset=spz|ply|lod|pano`：就绪后 307 跳转到官方 Viewer 或全景图。
- `POST /api/v1/3dgs/world/{world_id}/download`：任务成功后把 `cover`、`spz`、`ply`、`lod-meta` 下载到本地 `run_artifacts/`。
- `GET /api/v1/3dgs/world/{world_id}/asset/{asset_name}`：按需代理 `cover`/`spz`/`ply`/`lod-meta`，便于前端或展示页读取。

已用国内 Key 做过真实连通性验证：Lux3D G1-Turbo 返回 task `3687106`（创建请求已受理；用室内全景直接作为物体输入，后续任务终态为失败，说明应先裁剪单个构件再调用）；World 文生空间返回 world ID `3FO4K4XJJEQP`，状态查询返回 `PENDING`；World 单图外部 URL 被服务拒绝，这是预期的资产上传约束。

### 已验证的模型调用

- 百炼 `deepseek-v4-pro`：真实文本 JSON 调用成功；
- 百炼 `qwen3.8-max`：用 TAY-LI 的 `hotel_room.jpg` 真实图像调用成功，返回 `objects`；
- 百炼 `qwen-image-3.0-pro`：使用官方 `multimodal-generation` 的 `input.messages` schema 和 `parameters.prompt_extend=true`。当前账号不支持异步请求，因此 `DASHSCOPE_IMAGE_ASYNC=false`；同步请求已验证成功，通常耗时约 90–110 秒，响应图片位于 `output.choices[0].message.content[*].image`，适配器会同时暴露稳定的 `image_url` 字段。返回图片 URL 是临时签名地址，应立即下载或复制到自己的 OSS。
- Aholo Lux3D/World：国内端点、key、任务创建与状态查询均通过。

要在 Linux GPU 上重新执行 TAY-LI 的 YOLO-World 检测，可安装可选依赖：

```bash
pip install -e '.[yolo]'
# 准备 yolov8s-worldv2.pt 后
python3 pipeline/run_demo.py --scene hotel_room
```

World 的真实本地资源链也已验证：通过官方 `manycore-aholo-sdk-asset` 将 `hotel_room.jpg` 上传到国内 OUS，再提交 World 生成任务；因此 Windows bridge 后续可以把 CameraSDK 下载的 `.insv`/关键帧直接交给 `upload_local_file()`，不会把本地路径误传给 World API。

最近一次 MP4 任务 `3FO4K4QU7R1T` 已返回成功结果。典型 World 状态响应包含：

```json
{
  "worldId": "3FO4K4QU7R1T",
  "status": "SUCCEEDED",
  "progress": 1.0,
  "cover": "https://...jpg",
  "assets": {
    "splats": {
      "urls": {
        "plyPath": "https://...point_cloud.ply",
        "spzPath": "https://...compressed.spz",
        "lodMetaPath": "https://...lod-meta.json"
      }
    },
    "semanticsMetadata": {"upAxis": "Z"}
  }
}
```

`plyPath` 可用于离线点云处理，`spzPath` 适合压缩后的 Gaussian Splat 查看，`cover` 可用于演示封面。URL 是服务端资源地址，应在业务系统中保存任务 ID 和状态，不要把临时 URL 当作永久凭证。

`cover` 只是重建结果的预览图，不能替代三维模型。对实景重建，优先保存 `spz`；对 Spatial Gen，优先保存 `imagery.panoUrl` 和 `spz`：前者是 AI 改造后的全景效果图，后者是可交互的 Gaussian Splat。它们都可以由 MCP/后端直接返回，不需要停留在网页端。没有 Splat viewer 时，可先展示 `imagery.panoUrl`，同时保留 `ply` 供 Three.js、SuperSplat 或离线工具转换/查看。完成任务后可以运行：

```bash
curl -X POST http://localhost:8000/api/v1/3dgs/world/3FO4K4QU7R1T/download | jq
```

### 输入选择速查

| 素材 | 处理链 | 说明 |
| --- | --- | --- |
| 单张 ERP 全景图 | ERP 投影 → YOLO → 实体 crop → VLM/Lux3D/Tripo | Lux3D/Tripo 不应直接吃整张房间全景 |
| `.insv` 或 MP4/MOV | OSS/Asset → Aholo World | 空间级 3DGS；单个视频资源可提交 |
| 20 张以上普通 JPG/PNG/WebP | OSS/Asset → Aholo World | 同一房间不同位置/朝向、视野有重叠；不是同机位重复全景图 |
| YOLO crop 的实体图 | Lux3D 或 Tripo | 对象级 3D；Tripo 可先扩四视图再多视图建模 |
