# import_latest — 从相机导入最新照片（非遥控拍摄）

本工具封装 Insta360 Camera SDK：

- `GetCameraFilesList()`
- `DownloadCameraFile(remote, local)`

**不调用** `TakePhoto`。用户在机身拍完后，由软件触发本助手把照片拉到电脑。

## 输出约定（给 Python Bridge）

### `--health`

```json
{"camera_connected": true, "camera_model": "X4 Air", "firmware": null, "detail": "ok"}
```

退出码 0；连不上时 `camera_connected: false`，仍建议退出码 0（由 Bridge 解读）。

### `--download-latest --out C:\path\cap.jpg`

成功 stdout：

```json
{
  "local_path": "C:\\path\\cap.jpg",
  "camera_file": "/DCIM/Camera01/IMG_....jpg",
  "width": 7680,
  "height": 3840,
  "in_camera_stitch": true
}
```

失败时 stderr 含错误码关键字之一：`CAMERA_NOT_FOUND` / `NO_NEW_FILE` / `DOWNLOAD_FAILED`，非 0 退出码。

## 编译（需本机 Visual Studio + 已解压的 CameraSDK）

SDK 根目录示例：

`E:\second-life-view\tools\insta360\CameraSDK`

（含 `include/`、`lib/`、`bin/CameraSDK.dll`）

```powershell
cd E:\second-life-view\tools\insta360\import_latest
# 用 VS Developer PowerShell，或按你们环境改工具链
cmake -S . -B build -A x64
cmake --build build --config Release
New-Item -ItemType Directory -Force -Path ..\bin | Out-Null
Copy-Item build\Release\import_latest.exe ..\bin\
Copy-Item ..\CameraSDK\bin\CameraSDK.dll ..\bin\
```

实现源码见 `main.cpp`（骨架，需按官方 Demo 补全 DeviceDiscovery / Open）。

## 与 Demo 的关系

| | CameraSDKDemo | import_latest |
|--|---------------|---------------|
| 用途 | 厂商调试菜单 | 产品导入助手 |
| 拍摄 | 可遥控 TakePhoto | **不拍**，只下载 |
| 谁用 | 开发自测 | Capture Bridge / 软件按钮 |
