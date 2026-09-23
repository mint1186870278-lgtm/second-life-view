# Windows Insta360 Camera Bridge

该目录把 **Windows 上的 Insta360 CameraSDK / MediaSDK** 封装成仅监听本机回环地址的 HTTP 网关。它支持两种完全不同的工作模式：

1. **公网网页采集（推荐）**：用户在连接相机的 Windows 电脑打开公网前端；浏览器只调用该电脑的 `127.0.0.1:18080` 网关；网关把拼接 JPEG 用 HTTPS 上传 Linux，Linux 统一执行 YOLO。这是“任意已配置 SDK 的 Windows 电脑都能使用”的模式，**不需要 SSH 隧道**。
2. **服务器主动控制（可选、旧流程）**：Linux 经 SSH 反向隧道调用某一台 Windows 网关。它只适合运维人员从服务器控制一台固定相机，不适合面向任意 Windows 电脑的公网网页。

无论采用哪个模式：

- 相机 USB 线只连接 Windows；`CameraSDK.dll` 和 `MediaSDK.dll` 只在 Windows 运行；
- Linux 不加载 Windows DLL，也不直接访问 Windows USB；
- Windows 网关绝不暴露在局域网或公网；公网模式中只有本机浏览器访问 `127.0.0.1:18080`，图片由网关主动上传到 Linux；
- 每次拍摄都执行 `DeviceDiscovery → Open → TakePhoto → DownloadCameraFile → Close`，下载的 `.insp` 可用 MediaSDK 转为 ERP 全景 JPEG；
- Linux 将 JPEG 保存到 `run_artifacts/camera/`；配置 OSS 时还会上传私有 OSS 并使用签名 URL。

## 公网网页模式的连接关系

```text
Windows 浏览器（https://qushanhesy.com）
       │ 仅本机回环、带 Origin 校验
       ▼
Windows Camera Bridge（http://127.0.0.1:18080）
       │ HTTPS multipart：ERP JPEG + 相机元数据 + Linux ingest token
       ▼
Linux（https://qushanhesy.com/api/v1/camera/ingest）
       │ 保存原图 → YOLO-World → 生成标注图、检测 JSON、RunState
       ▼
Windows 浏览器显示 Linux 返回的结果
```

每一台要使用相机的 Windows 都必须各自安装 SDK、构建 CLI、启动一个本机 Bridge；它们共用同一个 Linux URL 和上传 token，但不共享 USB、也不让 Linux 远程加载 Windows SDK。

## 公网入口的必要配置

公网 HTTPS 入口必须把整个域名（SPA、`/api/` 和 `/camera-assets/`）反向代理到运行本项目的 Linux Nginx。本项目的 Linux origin 默认监听 `192.168.110.48:80`，并已把上传上限和推理超时配置为 300 MB / 900 秒。若 TLS 在另一台边缘 Nginx 终止，可使用以下结构（证书路径按入口机实际配置保留）：

```nginx
server {
    listen 443 ssl http2;
    server_name qushanhesy.com;
    # ssl_certificate ...;     # 使用入口机上仍有效的证书
    # ssl_certificate_key ...;
    client_max_body_size 300m;

    location / {
        proxy_pass http://192.168.110.48:80;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $host;
        proxy_request_buffering off;
        proxy_connect_timeout 30s;
        proxy_send_timeout 900s;
        proxy_read_timeout 900s;
    }
}
```

入口机变更后，先验证 `https://qushanhesy.com/health` 返回 JSON（而不是旧站点的 HTML/404），再从 Windows 网页测试采集。不要把 `18000` 或 Windows 的 `18080` 端口暴露到公网。

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

### 让 Windows 网关自动推送（推荐）

不需要让业务程序自行处理 multipart。将下面三项加入 Windows 网关的 `.env`，其中 token 与 Linux 的 `CAMERA_INGEST_TOKEN` 相同：

```dotenv
LINUX_CAMERA_INGEST_URL=https://<linux-host>/api/v1/camera/ingest
LINUX_CAMERA_INGEST_TOKEN=<CAMERA_INGEST_TOKEN>
LINUX_CAMERA_INGEST_TIMEOUT=900
```

该 URL 必须是 HTTPS 且路径必须精确为 `/api/v1/camera/ingest`；网关不接受 HTTP，以免上传照片和 bearer token 时降级为明文传输。重启 Windows 网关后，已在 `CAMERA_BRIDGE_OUTPUT_DIR` 中的拼接 JPEG 可由本机调用：

```powershell
$gatewayToken = '<CAMERA_BRIDGE_TOKEN>'

curl.exe -X POST 'http://127.0.0.1:18080/v1/local-file/ingest' `
  -H "Authorization: Bearer $gatewayToken" `
  -H 'Content-Type: application/json' `
  -d '{"filename":"stitched-room.jpg","user_goal":"评估这个空间的构件再利用机会","metadata":{"frame_id":"x5-20260923-001","camera_model":"Insta360 X5","captured_at":"2026-09-23T12:00:00Z"}}'
```

`filename` 只能是输出目录内的相对 `.jpg` / `.jpeg` 路径，因此该接口不能被用来上传 Windows 上的任意文件。它的响应直接包含 Linux 的 `asset`、`yolo` 和 `run`；没有 `detections` 入参。补拍时在 JSON 中添加 `run_id` 和 `action_id`。

如果希望 Windows SDK 拍完并拼接后立即上传，可改调：

```powershell
curl.exe -X POST 'http://127.0.0.1:18080/v1/capture-and-ingest' `
  -H "Authorization: Bearer $gatewayToken" `
  -H 'Content-Type: application/json' `
  -d '{"stitch":true,"output_width":4096,"output_height":2048,"user_goal":"评估这个空间的构件再利用机会","metadata":{"site":"一层大厅"}}'
```

此接口只接受 `stitch=true` 且 Windows MediaSDK 产出的 JPEG；它会先保留本地原图，再用 HTTPS multipart 推送 Linux。Linux 检测失败时原图仍会留在 Windows 输出目录中，可以重试 `local-file/ingest`，不会重新控制相机。

### 让公网第二页按钮直接采集并推理

部署前端后，在 **连接相机的同一台 Windows** 上打开网页。网页第二页的“采集现场照片”会访问 `http://127.0.0.1:18080/v1/browser/capture-and-ingest`；该路由只允许一个明确配置的网页 Origin，且不会把任何 bearer token 交给浏览器。

当前部署到 `qushanhesy.com` 时，每台 Windows 的 `windows_camera_bridge/.env` 至少应为（Windows 路径按实际安装位置替换）：

```dotenv
CAMERA_BRIDGE_EXECUTABLE=C:\src\second-life-view\windows_camera_bridge\build\Release\camera_bridge_cli.exe
CAMERA_BRIDGE_OUTPUT_DIR=C:\Insta360Bridge\captures
CAMERA_BRIDGE_TOKEN=<仅供本机受保护接口使用的独立随机密钥>
CAMERA_BRIDGE_SERVICE_PORT=9099
CAMERA_BRIDGE_ALLOWED_WEB_ORIGIN=https://qushanhesy.com
LINUX_CAMERA_INGEST_URL=https://qushanhesy.com/api/v1/camera/ingest
LINUX_CAMERA_INGEST_TOKEN=<由 Linux 管理员通过安全渠道发放的 CAMERA_INGEST_TOKEN>
LINUX_CAMERA_INGEST_TIMEOUT=900
```

`CAMERA_BRIDGE_TOKEN` 与 `LINUX_CAMERA_INGEST_TOKEN` 是两把不同的密钥：前者只保护 Windows 本机的运维接口；后者才是 Windows 向 Linux 上传图片的凭据。可在 Windows PowerShell 生成前者：

```powershell
py -c "import secrets; print(secrets.token_hex(32))"
```

Linux 的上传 token 不要写入 Git、截图或聊天记录；由服务器管理员通过受控渠道分发。前端构建时可设置（默认已经是下列值）：

```dotenv
VITE_WINDOWS_CAMERA_GATEWAY_URL=http://127.0.0.1:18080
```

Linux 服务还必须设置与公网反向代理一致的地址，使返回的原图、标注图和检测 JSON 都是可被该 Windows 浏览器加载的 HTTPS URL：

```dotenv
PUBLIC_BASE_URL=https://qushanhesy.com
```

首次从公网网页访问本机网关时，Chrome/Edge 可能提示“允许此网站访问本地网络”；必须允许。网关会精确校验 `Origin`，并要求浏览器发送 CORS 预检的 `X-Second-Life-Client` 请求头，其他网站不能调用相机接口。Windows 网关始终只监听 `127.0.0.1`，请勿将 `18080` 暴露到公网。

## 8. 运维边界

- CameraSDK 桌面端连接相机使用 USB；SSH 是控制数据的传输通道，不会把 USB 设备“穿透”到 Linux。
- `stitch=true` 需要 Windows 版 MediaSDK；`ImageStitcher` 以 CPU `TEMPLATE` 模式输出 ERP JPEG，优先保证稳定性。若需要 AI 拼接、ColorPlus 或实时预览，可在 Windows 端单独扩展 MediaSDK 处理。
- 未配置 OSS 时，素材只保存在服务器 `run_artifacts/camera/` 并由 `/camera-assets/` 提供。外部 3D / VLM 服务需要公网可访问图片时，应配置 OSS。
- 本项目没有为 Linux 业务 API 增加额外的用户鉴权；若该 API 对公网开放，请在反向代理、VPN 或应用层加访问控制。Windows 网关本身仍坚持“回环监听 + SSH 隧道 + Bearer token”。
