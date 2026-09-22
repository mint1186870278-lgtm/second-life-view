# Second Life View · Spatial Agent

这是一个面向建筑改造与空间再利用的黑客松后端 demo。它把 **Windows 上的 Insta360 CameraSDK/YOLO** 与 **Linux 上的 LangGraph、VLM、Research、设计和 3D 工具** 解耦：Windows 只负责采集和执行拍摄动作，Linux 负责判断“还缺什么证据”、调度 Agent 并生成可追溯结果。

## Demo 故事

1. Windows 上传一张全景图和 YOLO JSON（或直接调用 demo fixture）。
2. Perception Agent 把目标变成结构化 `SpatialObject`，并标记材质、状态、再利用判断和证据来源。
3. Evidence Agent 检查置信度与必填字段；如果柜体背面、材质或结构状态不确定，图在证据闸门暂停，并返回 `capture_actions`。
4. Windows bridge 执行 `zoom_region`/`request_user_photo`，把新图和 YOLO JSON 回传；同一个 run 恢复。
5. Research Agent 返回带来源和事实类型的再利用依据；Design Agent 生成“保留结构、替换表面”的翻新方案。
6. 可选调用国内 Lux3D：`POST /api/v1/reconstruct`，提交图片 URL 后返回异步任务 ID；默认 mock 便于离线展示。
7. Windows 将原始 `.insv`、全景图和 YOLO crop 上传到 `POST /api/v1/assets/upload`；Linux 返回私有 OSS 的短时签名 URL，后续模型无需访问 Windows 文件系统。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 只在本机填写密钥，文件已被 gitignore
python3 run.py
```

访问 `http://localhost:8000/docs`。没有任何密钥和相机也可以运行，模型与外部工具会返回可解释的 mock/fixture 结果。

## API 快速演示

```bash
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

# 上传相机素材到私有阿里云 OSS（返回 url 可作为模型输入）
curl -s -X POST http://localhost:8000/api/v1/assets/upload \
  -F 'session_id=demo-001' -F 'file=@./frame-00042.jpg' | jq

# Tripo V3 对象级异步建模；输入应是 YOLO crop 的实体图 URL
curl -s -X POST http://localhost:8000/api/v1/tripo/reconstruct \
  -H 'content-type: application/json' \
  -d '{"image_url":"https://signed-oss-url/object.jpg","wait":false}' | jq
```

`GET /api/v1/runs/{run_id}/events` 返回审计事件；`GET /api/v1/runs/{run_id}/stream` 提供 SSE，便于未来前端实时显示“相机补拍 → VLM → 检索 → 设计”的过程。

## Agent 和状态

`spatial_agent/graph.py` 使用 LangGraph `StateGraph`：`supervisor → perception → evidence`，证据不足时结束本轮并等待 `/capture/complete`；证据充分后进入 `research → design`。`RunState` 同时保存对象、Evidence、空间关系、待执行 CaptureAction、来源、设计结果、错误和事件，所以每一次判断都可以回放和解释。

外部模型适配器在 `spatial_agent/providers/`：

- 百炼 OpenAI-compatible：文本 `deepseek-v4-pro`，视觉 `qwen3.8-max`，图片生成 `qwen-image-3.0-pro`。
- Aholo Lux3D 国内 Skill：使用 `/root/.codex/skills/lux3d-cn/lux3d_client.py`，固定 `LUX3D_REGION=cn` 和 `https://api.aholo3d.cn`，不会使用海外端点。
- Aholo World：通过国内 Asset/World SDK 或 REST 提交空间重建。
- Tripo V3：`POST /api/v1/tripo/reconstruct`，适合单个实体图或同一物体的 2-4 个视角；任务查询为 `GET /api/v1/tripo/tasks/{task_id}`。Tripo 官方 API 没有房间级全景视频重建接口。
- OSS：`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`、`OSS_BUCKET`、`OSS_ENDPOINT` 只放 `.env`；桶建议保持私有，用服务端签名 URL 交给模型。

默认关闭外部调用。配置 `DASHSCOPE_API_KEY`/`LUX3D_API_KEY` 后，再显式设置 `USE_LLM=true` 或 `USE_EXTERNAL_TOOLS=true`。

## Windows bridge 契约

相机不应通过 SSH 让 Linux 加载 Windows DLL。建议 Windows 进程暴露：

- `GET /health`、`GET /camera/status`
- `POST /capture`：接收 `action_type`、`target_bbox`、分辨率和任务 ID，调用 CameraSDK `TakePhoto`/`StartLiveStreaming`。
- `GET /capture/{id}` 或上传回调：返回 `frame_id`、`capture_time_ms`、`asset_uri`、相机型号、投影类型和 `detections[]`。

Linux 只依赖这个 JSON 协议，不依赖 CameraSDK ABI。MediaSDK 的 realtime stitcher 可放在 Windows bridge，或后续单独部署 Linux media worker；第一版用关键帧/短视频上传更适合黑客松稳定演示。

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

### 3DGS 与 Lux3D 的区别

Aholo 有两条不同能力链，接口不能混用：

- `POST /api/v1/reconstruct`：Lux3D G1/G1-Turbo，适合单个柜体、门、椅子等物体图生 3D；国内 Skill 直接提交公开图片 URL。
- `POST /api/v1/3dgs/reconstruct`：Aholo World，适合室内空间 3DGS。全景 `INSV` 或普通视频可单条提交；纯图片重建必须至少 20 张。World 的本地文件必须先经过 Aholo Asset 上传，代码提供 `AholoWorldClient.upload_local_file()`。
- `POST /api/v1/3dgs/world/{world_id}`：查询 World 异步状态。

已用国内 Key 做过真实连通性验证：Lux3D G1-Turbo 返回 task `3687106`（创建请求已受理；用室内全景直接作为物体输入，后续任务终态为失败，说明应先裁剪单个构件再调用）；World 文生空间返回 world ID `3FO4K4XJJEQP`，状态查询返回 `PENDING`；World 单图外部 URL 被服务拒绝，这是预期的资产上传约束。

### 已验证的模型调用

- 百炼 `deepseek-v4-pro`：真实文本 JSON 调用成功；
- 百炼 `qwen3.8-max`：用 TAY-LI 的 `hotel_room.jpg` 真实图像调用成功，返回 `objects`；
- 百炼 `qwen-image-3.0-pro`：请求体已改为 `multimodal-generation` 的 `input.messages` schema。当前 workspace 返回 `AccessDenied: current user api does not support asynchronous calls`；同步请求会进入生成超时，说明模型网关可达但该 workspace 尚未开通对应生成权限。生成结果会以 `submitted` task ID 保存在 DesignProposal，待权限开通后可直接轮询；
- Aholo Lux3D/World：国内端点、key、任务创建与状态查询均通过。

要在 Linux GPU 上重新执行 TAY-LI 的 YOLO-World 检测，可安装可选依赖：

```bash
pip install -e '.[yolo]'
# 准备 yolov8s-worldv2.pt 后
python3 pipeline/run_demo.py --scene hotel_room
```

World 的真实本地资源链也已验证：通过官方 `manycore-aholo-sdk-asset` 将 `hotel_room.jpg` 上传到国内 OUS，再提交 World 生成任务；因此 Windows bridge 后续可以把 CameraSDK 下载的 `.insv`/关键帧直接交给 `upload_local_file()`，不会把本地路径误传给 World API。

### 输入选择速查

| 素材 | 处理链 | 说明 |
| --- | --- | --- |
| 单张 ERP 全景图 | ERP 投影 → YOLO → 实体 crop → VLM/Lux3D/Tripo | Lux3D/Tripo 不应直接吃整张房间全景 |
| `.insv` 或 MP4/MOV | OSS/Asset → Aholo World | 空间级 3DGS；单个视频资源可提交 |
| 20 张以上普通 JPG/PNG/WebP | OSS/Asset → Aholo World | 同一房间不同位置/朝向、视野有重叠；不是同机位重复全景图 |
| YOLO crop 的实体图 | Lux3D 或 Tripo | 对象级 3D；Tripo 可先扩四视图再多视图建模 |
