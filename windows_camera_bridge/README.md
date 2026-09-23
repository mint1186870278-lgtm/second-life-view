# Windows Insta360 Camera Bridge

该目录把 **Windows 上的 Insta360 CameraSDK / MediaSDK** 封装成仅监听本机回环地址的 HTTP 网关。Linux 上的 `spatial_agent` 通过 **SSH 反向隧道** 调用它，因此：

- 相机 USB 线只连接 Windows；`CameraSDK.dll` 和 `MediaSDK.dll` 只在 Windows 运行；
- Linux 不加载 Windows DLL，也不直接访问 Windows USB；
- Windows 网关不暴露在局域网或公网，服务器只访问其反向转发后的 `127.0.0.1:18081`；
- 每次拍摄都执行 `DeviceDiscovery → Open → TakePhoto → DownloadCameraFile → Close`，下载的 `.insp` 可用 MediaSDK 转为 ERP 全景 JPEG；
- Linux 将 JPEG 保存到 `run_artifacts/camera/`；配置 OSS 时还会上传私有 OSS 并使用签名 URL。

官方接口说明见 [Insta360 Desktop CameraSDK 文档](https://insta360develop.github.io/Insta360-Developer_Docs/ch/x/desktop/camera/)；本桥接器基于 `CameraSDK 2.2.0` 和 `MediaSDK 3.1.7` 的 Windows 包实现。

## 1. Windows 前置条件

1. 在相机上选择 **Android USB 模式**：X4 / X4 Air / X5 / X6 接线后在相机弹窗中选择 `Android`；较早机型按官方文档中的 USB / U 盘模式设置为 `Android`。
2. 在 Windows 安装 `libusbK` 驱动（可用官方安装包或 Zadig）。该驱动是 CameraSDK 发现 USB 相机所需；安装后，原本的 U 盘模式行为可能变化。
3. 安装 Visual Studio 2022 Build Tools（含 MSVC x64 和 CMake）与 Python 3.10+。
4. 将 **Windows 版** SDK ZIP 解压到 Windows 本机。服务器目录中的 SDK 压缩包不会自动传到 Windows。

若 Windows 无法发现设备或无法打开 libusbK 设备，请用“以管理员身份运行”打开终端后重试。

建议目录：

```text
C:\Insta360SDK\CameraSDK\CameraSDK-2.2.0-...-win64\
C:\Insta360SDK\MediaSDK\MediaSDK-3.1.7-...-win64\
C:\src\second-life-view\windows_camera_bridge\
```

`MediaSDK` 不是连接或下载必需项；它只在 `stitch=true` 时把 Insta360 原始图片拼接为后端可直接分析的 JPEG。

## 2. 构建 Windows 原生 CLI

在 **x64 Native Tools Command Prompt for VS 2022** 或 PowerShell 中执行。路径请换成实际解压目录：

```powershell
cd C:\src\second-life-view

cmake -S .\windows_camera_bridge -B .\windows_camera_bridge\build `
  -G "Visual Studio 17 2022" -A x64 `
  -DCAMERA_SDK_ROOT="C:\Insta360SDK\CameraSDK\CameraSDK-2.2.0-20260918_164435-win64" `
  -DMEDIA_SDK_ROOT="C:\Insta360SDK\MediaSDK\MediaSDK-3.1.7-20260917_192552-win64"

cmake --build .\windows_camera_bridge\build --config Release
```

构建后使用：

```text
windows_camera_bridge\build\Release\camera_bridge_cli.exe
```

`CMakeLists.txt` 会复制 `CameraSDK.dll`、`jsons/` 和 MediaSDK 的运行时 DLL / `models/` 到 `Release` 目录。不要只拷贝 EXE，否则 CameraSDK 的机型能力 JSON 或 MediaSDK 依赖可能缺失。

如只想验证 CameraSDK 控制与下载、暂时不拼接图片：

```powershell
cmake -S .\windows_camera_bridge -B .\windows_camera_bridge\build `
  -G "Visual Studio 17 2022" -A x64 `
  -DCAMERA_SDK_ROOT="C:\Insta360SDK\CameraSDK\CameraSDK-2.2.0-20260918_164435-win64" `
  -DSECOND_LIFE_ENABLE_MEDIA_SDK=OFF
cmake --build .\windows_camera_bridge\build --config Release
```

此模式下 API 请求必须带 `"stitch": false`；返回的是 `.insp` / `.dng` 原始文件，不会自动进入图像分析。

## 3. 启动 Windows 网关

```powershell
cd C:\src\second-life-view\windows_camera_bridge
Copy-Item .env.example .env
notepad .env

py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

uvicorn app:app --host 127.0.0.1 --port 18080
```

在 `.env` 中至少设置：

```dotenv
CAMERA_BRIDGE_EXECUTABLE=C:\src\second-life-view\windows_camera_bridge\build\Release\camera_bridge_cli.exe
CAMERA_BRIDGE_OUTPUT_DIR=C:\Insta360Bridge\captures
CAMERA_BRIDGE_TOKEN=<使用随机生成的长密钥>
CAMERA_BRIDGE_SERVICE_PORT=9099
```

`CAMERA_BRIDGE_SERVICE_PORT` 是 **CameraSDK 内部文件传输服务端口**，与网关 HTTP 端口 `18080` 不同。若 `9099` 被占用，修改该值并重启 Windows 网关；CLI 会在 `Open()` 前调用 `SetServicePort()`。

网关只接受包含 `Authorization: Bearer <CAMERA_BRIDGE_TOKEN>` 的 `/v1/*` 请求。不要将 Uvicorn 绑定到 `0.0.0.0`。

## 4. 从 Windows 建立 SSH 反向隧道

Windows 上执行（将用户名和服务器主机替换为实际值）：

```powershell
ssh -NT `
  -o ExitOnForwardFailure=yes `
  -o ServerAliveInterval=30 `
  -o ServerAliveCountMax=3 `
  -R 127.0.0.1:18081:127.0.0.1:18080 `
  <linux-user>@<linux-server>
```

这条命令要求 Linux SSH 服务允许 TCP 转发（`AllowTcpForwarding yes`）。务必保留 `127.0.0.1:` 绑定；不要使用 `0.0.0.0` 或开启公网监听。

在 Linux 服务器验证隧道：

```bash
curl http://127.0.0.1:18081/health
```

应返回 Windows 网关健康状态。SSH 窗口必须保持运行；生产使用可将同一命令配置为 Windows 计划任务或 `autossh` 替代方案。

## 5. 配置并重启 Linux 服务

在服务器项目根目录 `.env` 中设置与 Windows **完全相同** 的 token：

```dotenv
WINDOWS_CAMERA_GATEWAY_URL=http://127.0.0.1:18081
WINDOWS_CAMERA_GATEWAY_TOKEN=<CAMERA_BRIDGE_TOKEN 的相同值>
WINDOWS_CAMERA_GATEWAY_TIMEOUT=720
```

然后重启 `python3 run.py` 或你的部署进程。服务启动后验证：

```bash
curl -s http://127.0.0.1:8000/api/v1/camera/status | jq
curl -s http://127.0.0.1:8000/api/v1/camera/files | jq
```

如果状态接口返回 `503`，说明 Linux `.env` 尚未配置 token；返回 `502` 通常表示反向隧道或 Windows 网关不可达；返回 CameraSDK 错误则检查相机 Android 模式、libusbK、USB 线和 `9099` 端口。

## 6. 从服务器拍摄和分析

拍摄、下载、拼接并创建新的 LangGraph 分析 run：

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/camera/capture \
  -H 'content-type: application/json' \
  -d '{
    "raw_type":"off",
    "stitch":true,
    "output_width":4096,
    "output_height":2048,
    "user_goal":"评估这个空间的构件再利用机会"
  }' | jq
```

响应包含：

- `asset.image_url`：本地 `/camera-assets/...` URL，或配置 OSS 时的私有 OSS 签名 URL；
- `gateway.remote_paths`：相机内原始素材路径；
- `yolo`：Linux 实时 YOLO-World 的标注图 URL、检测 JSON URL、检测数和去重组数；
- `run`：首次拍摄创建的分析状态、证据和后续 `capture_actions`。

下载相机 SD 卡上已有文件：先查询 `/api/v1/camera/files`，然后将其返回的精确路径传入：

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/camera/download \
  -H 'content-type: application/json' \
  -d '{"remote_path":"<从 files 返回的精确路径>","stitch":true}' | jq
```

若已有 run 需要补拍，将 `run_id` 和当前待处理的 `capture_actions[].id` 一并传入；后端会沿用同一 run：

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/camera/capture \
  -H 'content-type: application/json' \
  -d '{
    "run_id":"<run_id>",
    "action_id":"<capture_actions 中的 id>",
    "stitch":true,
    "user_goal":"补拍材质和边缘细节"
  }' | jq
```

## 7. Windows 已下载本地 JPEG 时主动上传 Linux

如果 CameraSDK 已经在 Windows 本地生成 ERP JPEG，可以不走反向隧道下载，而是将文件直接推送到 Linux 的 `POST /api/v1/camera/ingest`。YOLO-World 仍只在 Linux 上运行；Windows 不应运行模型或上传检测框。

先在 Linux `.env` 配置：

```dotenv
CAMERA_INGEST_TOKEN=<独立的高强度随机 token>
CAMERA_INGEST_MAX_UPLOAD_MB=256
YOLO_DEVICE=auto
```

然后在 Windows PowerShell 执行（Linux API 必须使用 HTTPS、VPN 或其他受控网络入口）：

```powershell
$metadata = '{"frame_id":"x5-20260923-001","camera_model":"Insta360 X5","projection":"equirectangular"}'
curl.exe -X POST 'https://<linux-host>/api/v1/camera/ingest' `
  -H 'Authorization: Bearer <CAMERA_INGEST_TOKEN>' `
  -F 'file=@C:\Insta360Bridge\captures\stitched-room.jpg;type=image/jpeg' `
  -F "metadata=$metadata"
```

需恢复证据补拍时，再追加 `-F 'run_id=<run_id>'` 与 `-F 'action_id=<capture_actions 中的 id>'`。响应的 `yolo.annotated_image_url`、`yolo.detections_url` 和 `run` 可直接交给 Windows UI 或上层业务。

## 8. 运维边界

- CameraSDK 桌面端连接相机使用 USB；SSH 是控制数据的传输通道，不会把 USB 设备“穿透”到 Linux。
- `stitch=true` 需要 Windows 版 MediaSDK；`ImageStitcher` 以 CPU `TEMPLATE` 模式输出 ERP JPEG，优先保证稳定性。若需要 AI 拼接、ColorPlus 或实时预览，可在 Windows 端单独扩展 MediaSDK 处理。
- 未配置 OSS 时，素材只保存在服务器 `run_artifacts/camera/` 并由 `/camera-assets/` 提供。外部 3D / VLM 服务需要公网可访问图片时，应配置 OSS。
- 本项目没有为 Linux 业务 API 增加额外的用户鉴权；若该 API 对公网开放，请在反向代理、VPN 或应用层加访问控制。Windows 网关本身仍坚持“回环监听 + SSH 隧道 + Bearer token”。
