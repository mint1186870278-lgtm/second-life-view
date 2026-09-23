# Second Life View｜一键采集（Camera SDK）详细设计

**文档类型：** SDK / 采集链路设计（对接用）  
**关联产品页：** 新建项目 → 上传素材（「一键采集」）→ 分析处理  
**机型约束：** Insta360 X4 Air  
**SDK 策略：** 仅 **Camera SDK**；全景依赖 **机内照片拼接**；不使用 Media SDK  
**相关文档：** `docs/SDK_DEV_FLOW.md`、`capture_bridge/README.md`  
**版本：** v0.4  
**日期：** 2026-09-23  
**维护：** SDK 负责人（采集方式变更时同步本文全文，勿只改附录）

---

## 1. 目标与范围

### 1.1 当前已验证的采集方式（主路径）

> **用户不操作 Demo 菜单、也不在机身单独「拍完再导入」。**  
> 软件（或本机脚本）调用 Bridge → Bridge **自动启动** `CameraSDKDemo.exe` → **自动输入菜单**完成拍照并下载 → 本机得到 ERP JPG。

```text
[步骤1 项目设置 · C01] 用户填写项目信息 → 创建项目（SDK 不参与）
        ↓
  点击「下一步：上传素材 / 现场素材接入」→ 进入 C02（不自动采集）
        ↓
  【触发点】用户在 C02 采集框点击「采集现场照片」
        ↓
  前端调用 Capture Bridge：POST /import/latest
  （开发自测仍可用 curl / Invoke-RestMethod 模拟这一跳）
        ↓
  Capture Bridge（backend=demo_auto）：
      启动 CameraSDKDemo --cn
      → 主菜单 1 拍照
      → 1 选择模式
      → 0 普通拍照   （X4 Air + 机内拼接 = ERP 全景；Demo 无单独「全景」项）
      → 10 拍照并下载
      → 保存到 data/samples/captures_raw
      → 退出 Demo
        ↓
  C02 采集框 ready：预览 + 填写空间名称 →「重新采集」或「确认」
        ↓
  确认后：实拍卡片进入下方「分析用素材」网格（可与样例一并勾选展示）
        ↓
[步骤3 分析处理] 本期仍只把样例 scene_id 交给 /api/v1/demo/analyze；
  仅选实拍时提示「实拍分析待后端接入」。后续对接点：实拍上传 API。
```

**触发约定（产品）：**


| 用户操作             | 系统行为                                 |
| ---------------- | ------------------------------------ |
| C01 点「下一步」进入素材接入 | 仅路由进入 C02，**不**自动采集                  |
| C02 点「采集现场照片」    | 调 Bridge `POST /import/latest` 开始拍+下 |
| C02 预览态「重新采集」    | 再次调用 Bridge，覆盖未确认预览                  |
| C02 预览态「确认」      | 以空间名生成卡片，插入下方素材网格                    |


**用户现场只需保证：**

1. 相机开机，USB 选 **「安卓手机控制」**
2. 开启 **照片机内拼接**
3. 本机已启动 Capture Bridge（进 C01 前或进 C02 前）
4. **不要自己先开着 Demo**（由程序拉起）

### 1.2 SDK 负责 / 不负责


| 负责                                          | 不负责                          |
| ------------------------------------------- | ---------------------------- |
| 本机 Capture Bridge（localhost API）            | 项目 CRUD、权限、地区政策              |
| 自动拉起 Demo 并完成「拍照并下载」                        | 用户手工点 Demo 菜单（产品路径不做）        |
| 下载目录、2:1 校验、返回 `preview_url` / `local_path` | 把 Camera SDK 嵌进浏览器           |
| 拍摄元数据（`source_type=insta360_camera` 等）      | Media SDK；改前端 C02（本期可零改动 FE） |


### 1.3 本期明确边界

- **连接：** Windows + USB + 安卓模式 + libusbK。  
- **全景：** ERP JPG（约 2:1），靠机内照片拼接。  
- **实现手段（过渡/已验证）：** 通过 **自动化 CameraSDKDemo** 调用厂商能力（内部仍是 SDK 的 TakePhoto + Download），避免用户碰命令行。  
- **长期可选：** 原生 `import_latest` 助手（C++ 直接调 DLL）；当前不作为主验收路径。  
- SDK 二进制不进 Git：`tools/insta360/CameraSDK/`。

### 1.4 已废弃 / 勿再按旧文档执行的说法


| 旧说法（v0.1–v0.2 部分章节）                                            | 现状                                            |
| -------------------------------------------------------------- | --------------------------------------------- |
| 用户在机身按快门，再「导入最新一张」                                             | **已改**：一键即自动拍照下载                              |
| 主路径 = `GetCameraFilesList` + `DownloadCameraFile`（不 TakePhoto） | **暂非主路径**；`sdk_import` 仅预留                    |
| 必须做 discard「要 / 不要」                                            | **已改**：产品用「重新采集 / 确认 + 空间名」入库卡片，非 discard API |
| 「明确不做 Demo 遥控 TakePhoto」                                       | **已改**：当前正是用 Demo 自动化完成遥控拍+下                  |


---

## 2. 端到端时序（当前实现）

```text
用户              前端 C01/C02           Capture Bridge              CameraSDKDemo           相机            后端(可选)
 │                     │                      │                          │                  │               │
 │ C01 填完点「下一步」  │                      │                          │                  │               │
 │────────────────────▶│ 路由进入 C02（idle）   │                          │                  │               │
 │ 点「采集现场照片」    │                      │                          │                  │               │
 │────────────────────▶│ POST /import/latest  │                          │                  │               │
 │                     │─────────────────────▶│                          │                  │               │
 │                     │                      │ 启动 Demo --cn            │                  │               │
 │                     │                      │─────────────────────────▶│ Open/连接         │               │
 │                     │                      │  stdin: 1,1,0,10,path    │─────────────────▶│ TakePhoto      │
 │                     │                      │                          │◀── 下载 JPG ──────│               │
 │                     │                      │◀── 新文件出现 ────────────│                  │               │
 │                     │◀── preview_ready ────│                          │ 退出             │               │
 │ 预览+填空间名→确认    │ 实拍卡加入下方网格     │                          │                  │               │
 │ （或重新采集）        │ （以后）上传 media ───────────────────────────────────────────────────────▶│
```

开发自测可不经前端：

```powershell
$env:CAPTURE_BRIDGE_BACKEND = "demo_auto"
.\.venv\Scripts\python.exe -m capture_bridge

# 另一终端
Invoke-RestMethod -Method POST http://127.0.0.1:18765/import/latest `
  -ContentType "application/json" `
  -Body '{"project_id":"proj_demo","scene_label":"lab"}'
```

成功：`status=preview_ready`，图在 `data/samples/captures_raw/`。  
注意：`preview_url` 仅在 **当前 Bridge 进程、当次 capture_id** 有效；重启 Bridge 后请直接打开磁盘 jpg。

---

## 3. 模块划分

```text
┌─────────────────────────────────────────────────────────────┐
│  前端                                                          │
│  · C02 点「采集现场照片」→ POST /import/latest（产品触发点）     │
│  · 预览 + 空间名 → 确认入库卡片 / 重新采集                      │
│  · 样例仍走 demo/analyze；实拍展示可选，分析待上传对接           │
└───────────────┬────────────────────────────▲────────────────┘
                │                            │ （以后）media 列表
┌───────────────▼────────────────────────────┴────────────────┐
│  后端 spatial_agent（FastAPI :8000）                          │
│  · 现有 demo 样例分析；相机图上传接口对接后补                   │
└───────────────▲─────────────────────────────────────────────┘
                │ （以后）上传
┌───────────────┴─────────────────────────────────────────────┐
│  Capture Bridge :18765（SDK 主交付）                          │
│  · demo_auto：自动 Demo 菜单拍照下载                          │
│  · 暴露：/health、/import/latest、/capture/{id}/preview 等    │
└───────────────▲─────────────────────────────────────────────┘
                │ 子进程 + stdin
┌───────────────┴─────────────────────────────────────────────┐
│  tools/insta360/CameraSDK/bin/CameraSDKDemo.exe + X4 Air     │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Capture Bridge

### 4.1 形态

**已采用方案 A：** 本机 Agent + `http://127.0.0.1:18765`。


| backend         | 含义                    | 状态               |
| --------------- | --------------------- | ---------------- |
| `**demo_auto`** | 自动开 Demo，菜单拍+下        | **当前主路径（已实机验证）** |
| `mock`          | 假图测 API               | 已实现              |
| `watch`         | 人工操作 Demo，Bridge 只等文件 | 降级/调试            |
| `sdk_import`    | 原生助手只下载不遥控拍           | 未编好助手前不可用        |


默认建议：`CAPTURE_BRIDGE_BACKEND=demo_auto`。

### 4.2 一次采集生命周期（demo_auto）

1. 客户端 `POST /import/latest`（或兼容 `POST /capture/start`）。
2. Bridge 启动 Demo，等待进入主菜单。
3. 自动发送：`1` → `1` → `{mode_index}` → `10` → 保存目录。
4. 监视 `captures_raw` 出现新 JPG，拷贝到 `_sessions/<capture_id>.jpg`。
5. 校验约 2:1，返回 `preview_ready`。
6. 结束 Demo 进程。
7. **本期无「要/不要」**；文件已落盘即可。

模式默认下标 `0` = 普通拍照（环境变量 `CAPTURE_BRIDGE_DEMO_PHOTO_MODE_INDEX`）。

### 4.3 API（已实现）

#### `GET /health`

```json
{
  "ok": true,
  "sdk_version": "2.2.0",
  "camera_connected": true,
  "camera_model": "X4 Air (CameraSDKDemo auto)",
  "backend": "demo_auto",
  "detail": "Will launch ... CameraSDKDemo.exe ..."
}
```

#### `POST /import/latest`（主接口；`/capture/start` 同逻辑）

请求：

```json
{
  "project_id": "proj_demo",
  "scene_label": "lab"
}
```

成功响应要点：

```json
{
  "capture_id": "cap_...",
  "status": "preview_ready",
  "local_path": ".../captures_raw/_sessions/cap_....jpg",
  "preview_url": "http://127.0.0.1:18765/capture/cap_.../preview",
  "width": 7680,
  "height": 3840,
  "meta": {
    "source_type": "insta360_camera",
    "camera_model": "X4 Air",
    "backend": "demo_auto"
  }
}
```

#### 其它


| 方法     | 路径                      | 说明             |
| ------ | ----------------------- | -------------- |
| `GET`  | `/capture/{id}/preview` | 当次进程内预览 JPG    |
| `POST` | `/capture/{id}/discard` | 删本机临时文件（产品可不接） |


#### 错误码


| code               | 含义               | 提示方向                              |
| ------------------ | ---------------- | --------------------------------- |
| `CAMERA_NOT_FOUND` | Demo 未进主菜单 / 未连上 | USB、安卓模式、供电                       |
| `SDK_INIT_FAILED`  | 找不到 Demo exe     | 检查 `tools/insta360/CameraSDK/bin` |
| `DOWNLOAD_FAILED`  | 超时无新图或损坏         | 重试；勿拔线；看 Bridge 日志                |
| `NOT_ERP_ASPECT`   | 非约 2:1           | 开机内拼接后重采                          |
| `BUSY`             | 上一次未结束           | 等待                                |


### 4.4 代码位置

- Python：`capture_bridge/`（`camera/demo_auto.py`）  
- 说明：`capture_bridge/README.md`  
- Demo：`tools/insta360/CameraSDK/bin/CameraSDKDemo.exe`

---

## 5. 与前端对接

### 5.1 现状（已接通）

- C01 点「下一步：素材接入」→ 进入 C02（**不**自动采集）。  
- C02 采集框点「采集现场照片」→ Bridge `POST /import/latest`（`demo_auto`）。  
- 成功后：预览 + 空间名称 →「重新采集」或「确认」；确认后实拍卡进入下方网格。  
- 「开始全链路分析」只提交样例 `scene_id`；仅勾选实拍时提示待后端接入。  
- 前端：`src/api/captureBridge.ts`、`CreationFlowContext` 的 `liveScenes`。

### 5.2 前端接入约定


| 时机              | 行为                                                      |
| --------------- | ------------------------------------------------------- |
| C01 → 下一步进入 C02 | 仅路由；采集框为 idle                                           |
| C02「采集现场照片」     | `POST http://127.0.0.1:18765/import/latest`（可能 30–120s） |
| ready 态         | 左侧预览 + 右侧空间名；「重新采集」「确认」                                 |
| 确认              | `live_<capture_id>` 卡片加入网格并可勾选                          |
| Bridge 未启       | 点采集后提示先启动本机采集服务                                         |


**产品确认：** 用「重新采集 / 确认」完成入库，不走 discard API。

### 5.3 【前端待填】


| #   | 问题                                | 结论                           |
| --- | --------------------------------- | ---------------------------- |
| F1  | 触发点                               | **已实现：C02「采集现场照片」按钮；进页不自动采** |
| F2  | 成功后图如何进入分析链路（仍样例 / 新 upload API）？ | 本期展示闭环；分析仍样例；后续对接上传          |
| F3  | Bridge 未启动时的降级（仅本地上传 / 样例）？       | 可只用样例继续分析                    |
| F4  | 超时与 loading 文案                    | 采集中态已有                       |
| F5  | 是否允许用户跳过实拍、只用样例继续分析？              | **允许**                       |


---

## 6. 与后端对接

### 6.1 关系

SDK **不创建项目**；`project_id` 由前端传入。  
现有后端：`spatial_agent`（`:8000`）。样例分析走 `/api/v1/demo/`*。  
相机实拍进项目 media：待后端提供上传 API（或复用 `/api/v1/assets/upload`，需 OSS）。

### 6.2 【后端待填】


| #   | 问题                                 | 结论                                      |
| --- | ---------------------------------- | --------------------------------------- |
| B1  | 实拍 JPG 正式上传路径与字段                   |                                         |
| B2  | `source_type=insta360_camera` 是否入库 |                                         |
| B3  | 与 C02 样例场景并存时的分析输入规则               | **本期：仅样例 ID 进 analyze；实拍 `live_`* 过滤掉** |


### 6.3 与 pipeline 旁路

可选：把 `captures_raw` 中 jpg 拷到 `panoramas/<slug>.jpg` 再跑 `pipeline/run_demo.py`。  
产品主路径以 Bridge +（未来）后端上传为准。

---

## 7. 相机与拍摄策略

### 7.1 前置

1. libusbK（Zadig）
2. USB → **安卓手机控制**
3. **照片机内拼接**
4. 供电不足时用带电 Hub

### 7.2 Demo 自动化参数


| 项    | 当前默认                                      |
| ---- | ----------------------------------------- |
| 功能入口 | 主菜单 → 拍照                                  |
| 模式   | 下标 `0` 普通拍照                               |
| 动作   | `10` 拍照并下载                                |
| 保存目录 | `data/samples/captures_raw`（正斜杠路径写入 Demo） |


### 7.3 校验

- 可读 JPEG  
- `width/height ≈ 2`

---

## 8. 安全与运维


| 项       | 说明             |
| ------- | -------------- |
| 监听      | 仅 `127.0.0.1`  |
| Demo 窗口 | 可能短暂弹出控制台，属预期  |
| 预览 URL  | 进程内有效；重启后看磁盘文件 |
| SDK 分发  | 不进 Git         |


---

## 9. 分阶段与验收

### 已完成（SDK）

- `demo_auto` 实机：自动 Demo → 拍照下载 → `captures_raw` 有约 7680×3840 JPG  
- `GET /health`、`POST /import/latest`、当次 `preview`  
- 不依赖用户手点 Demo 菜单

### 待前后端

- C02「采集现场照片」调 Bridge + 确认入库卡片  
- 实拍图上传进项目 media / 进入分析

### SDK 验收标准（当前）

1. 本机只开 Bridge + 调一次 `/import/latest`，即可在 `captures_raw` 得到新全景。
2. 用户无需操作 Demo 菜单。
3. 未连相机时有明确错误（如 `CAMERA_NOT_FOUND`）。

---

## 10. 联调议程（精简）

1. 确认实拍上传 API 与 analyze 接入。
2. 冻结 `source_type=insta360_camera` 入库字段。
3. 可选：原生 `import_latest` 替换 demo_auto。

---

## 11. 附录

### A. 文案与接口


| 产品/开发用语      | 实际                                |
| ------------ | --------------------------------- |
| C02「采集现场照片」  | `POST /import/latest`（demo_auto）  |
| 「重新采集」       | 再次 `POST /import/latest`（覆盖未确认预览） |
| 「确认」         | 前端生成 `live_`* 卡片入库网格              |
| 全景模式         | Demo「普通拍照」+ 机内拼接                  |
| 要/不要 discard | **产品侧用重新采集/确认替代**                 |


### B. 路径

```text
E:\second-life-view\capture_bridge\
E:\second-life-view\tools\insta360\CameraSDK\bin\CameraSDKDemo.exe
E:\second-life-view\data\samples\captures_raw\
```

### C. 修订记录


| 版本     | 日期         | 变更                                                                |
| ------ | ---------- | ----------------------------------------------------------------- |
| v0.1   | 2026-09-22 | 初稿：一键采集 + 要/不要                                                    |
| v0.2   | 2026-09-22 | 改为「机身拍 + SDK 导入」；部分章节与实现脱节                                        |
| v0.3   | 2026-09-23 | **与实机一致**：主路径改为 `demo_auto` 自动 Demo 拍+下；去掉要/不要为必做；废弃 v0.2 机身导入主叙述 |
| v0.3.1 | 2026-09-23 | 触发点改为：C01 点下一步进入 C02 即自动采集                                        |
| v0.4   | 2026-09-23 | 触发点改为：C02「采集现场照片」；确认入库卡片；进页不再自动采；分析仍过滤 `live_`*                   |


