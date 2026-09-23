# Second Life View｜Capture Bridge

**当前推荐（可验证）：一键导入 = 自动开 Demo 完成拍照并下载，再载入程序。**

## 你怎么验证

1. 相机开机，USB 选 **安卓手机控制**，开启 **照片机内拼接**
2. **不要自己开 Demo**（程序会自动开）
3. 启动 Bridge：

```powershell
cd E:\second-life-view
$env:CAPTURE_BRIDGE_BACKEND = "demo_auto"
.\.venv\Scripts\python.exe -m capture_bridge
```

4. 另开终端调用一键导入：

```powershell
Invoke-RestMethod -Method POST http://127.0.0.1:18765/import/latest `
  -ContentType "application/json" `
  -Body '{"project_id":"proj_demo","scene_label":"lab"}'
```

程序会自动：

```text
启动 CameraSDKDemo
  → 主菜单 1 拍照
  → 1 选择模式
  → 0 普通拍照   （X4 Air 开机制内拼接后即为全景 ERP）
  → 10 拍照并下载
  → 保存到 data/samples/captures_raw
  → 退出 Demo
  → 返回 preview_url
```

5. 浏览器打开返回的 `preview_url` 看图；不要则：

```powershell
Invoke-RestMethod -Method POST http://127.0.0.1:18765/capture/<capture_id>/discard
```

## 说明

| 项 | 说明 |
|----|------|
| 「全景」 | Demo 菜单里是 **普通拍照 [0]**；全景靠相机机内拼接，不是单独菜单项 |
| 模式下标 | 可用 `$env:CAPTURE_BRIDGE_DEMO_PHOTO_MODE_INDEX="0"` 改 |
| 耗时 | 拍照+下载可能 30–120 秒，请求会卡住直到完成 |
| 黑窗口 | Demo 可能闪一下控制台，属正常 |

## 其它 backend

| 值 | 用途 |
|----|------|
| `demo_auto` | **默认推荐**，自动 Demo |
| `mock` | 无相机测 API |
| `watch` | 你手动操作 Demo |
| `sdk_import` | 原生助手（未编好前不可用） |
