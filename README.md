# Second Life View · Spatial Agent

这是一个面向建筑改造与空间再利用的黑客松后端 demo。它把 **Windows 上的 Insta360 CameraSDK/YOLO** 与 **Linux 上的 LangGraph、VLM、Research、设计和 3D 工具** 解耦：Windows 只负责采集和执行拍摄动作，Linux 负责判断“还缺什么证据”、调度 Agent 并生成可追溯结果。

## Demo 故事

1. Windows 上传一张全景图和 YOLO JSON（或直接调用 demo fixture）。
2. Perception Agent 把目标变成结构化 `SpatialObject`，并标记材质、状态、再利用判断和证据来源。
3. Evidence Agent 检查置信度与必填字段；如果柜体背面、材质或结构状态不确定，图在证据闸门暂停，并返回 `capture_actions`。
4. Windows bridge 执行 `zoom_region`/`request_user_photo`，把新图和 YOLO JSON 回传；同一个 run 恢复。
5. Research Agent 返回带来源和事实类型的再利用依据；Design Agent 生成“保留结构、替换表面”的翻新方案。
6. 可选调用国内 Lux3D：`POST /api/v1/reconstruct`，提交图片 URL 后返回异步任务 ID；默认 mock 便于离线展示。

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
```

`GET /api/v1/runs/{run_id}/events` 返回审计事件；`GET /api/v1/runs/{run_id}/stream` 提供 SSE，便于未来前端实时显示“相机补拍 → VLM → 检索 → 设计”的过程。

## Agent 和状态

`spatial_agent/graph.py` 使用 LangGraph `StateGraph`：`supervisor → perception → evidence`，证据不足时结束本轮并等待 `/capture/complete`；证据充分后进入 `research → design`。`RunState` 同时保存对象、Evidence、空间关系、待执行 CaptureAction、来源、设计结果、错误和事件，所以每一次判断都可以回放和解释。

外部模型适配器在 `spatial_agent/providers/`：

- 百炼 OpenAI-compatible：文本 `deepseek-v4-pro`，视觉 `qwen3.8-max`，图片生成 `qwen-image-3.0-pro`。
- Aholo Lux3D 国内 Skill：使用 `/root/.codex/skills/lux3d-cn/lux3d_client.py`，固定 `LUX3D_REGION=cn` 和 `https://api.aholo3d.cn`，不会使用海外端点。

默认关闭外部调用。配置 `DASHSCOPE_API_KEY`/`LUX3D_API_KEY` 后，再显式设置 `USE_LLM=true` 或 `USE_EXTERNAL_TOOLS=true`。

## Windows bridge 契约

相机不应通过 SSH 让 Linux 加载 Windows DLL。建议 Windows 进程暴露：

- `GET /health`、`GET /camera/status`
- `POST /capture`：接收 `action_type`、`target_bbox`、分辨率和任务 ID，调用 CameraSDK `TakePhoto`/`StartLiveStreaming`。
- `GET /capture/{id}` 或上传回调：返回 `frame_id`、`capture_time_ms`、`asset_uri`、相机型号、投影类型和 `detections[]`。

Linux 只依赖这个 JSON 协议，不依赖 CameraSDK ABI。MediaSDK 的 realtime stitcher 可放在 Windows bridge，或后续单独部署 Linux media worker；第一版用关键帧/短视频上传更适合黑客松稳定演示。

## 安全与部署

百炼和 Aholo key 只放权限为 `600` 的本地 `.env`、云 Secret 或进程环境变量；不要提交 `百炼api.txt`、`.env` 或 SDK 压缩包。SkillHub 的 Lux3D 国内 Skill 已安装在 `/root/.codex/skills/lux3d-cn`，版本 4.1.2。
