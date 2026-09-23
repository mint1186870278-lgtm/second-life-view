# Second Life View｜SDK 后续开发流程（真正项目目录）

**项目根目录（正式开发）：** `E:\second-life-view`  
**旧 handoff / SDK 试验目录：** `E:\second-life-view-backend-handoff-v0.4`  
**机型：** Insta360 X4 Air  
**策略：** 只用 **Camera SDK**；全景靠 **机内照片拼接**；不用 Media SDK  

**文档目的：** 在真正项目里重新整理 SDK 采集链路，并把拍到的图送进现有 `pipeline` 做后续分析。

---

## 0. 先搞清两个文件夹

| 路径 | 角色 |
|------|------|
| `E:\second-life-view` | **小组正式仓库**：pipeline、fixtures、以后提交代码 |
| `E:\second-life-view-backend-handoff-v0.4` | 历史 handoff 文档 + 已跑通的 Camera SDK 包；可当「SDK 安装来源」 |

开发时请用 Cursor：**File → Open Folder → `E:\second-life-view`**。

当前正式仓库形态（截至本文撰写）：

```text
E:\second-life-view\
  pipeline\          # 检测 → enrichment → assessment（本地 Python，暂无 FastAPI）
  data\samples\panoramas\   # ERP 全景输入（pipeline 读这里）
  data\fixtures\     # 分析结果 JSON
  requirements.txt
```

**结论：** 在本仓库里，「上传到软件」的第一版落地 = **把 SDK 拍的全景放进 `data/samples/panoramas/`，注册 scene，跑 `pipeline/run_demo.py`**。等后端 HTTP 上传接口有了，再改成调 API。

---

## 1. 在真正项目里「重新弄 SDK」的推荐布局

不要把整个 SDK 大包强行 commit 进 git。建议：

```text
E:\second-life-view\
  tools\
    insta360\
      CameraSDK\          # Windows Camera SDK（从 handoff 拷贝或再解压）
        bin\
          CameraSDKDemo.exe
          CameraSDK.dll
          jsons\
      README_SDK.md       # 可指向本文件
  data\
    samples\
      panoramas\          # ← SDK 拍完最终放到这里
      captures_raw\       # 可选：临时下载目录（建议 gitignore）
  docs\
    SDK_DEV_FLOW.md       # 本文件（若你放在 docs 下）
```

### 1.1 从已跑通的环境拷贝 Camera SDK（推荐）

在 PowerShell（可先开管理员）执行：

```powershell
# 在真正项目里建目录
New-Item -ItemType Directory -Force -Path "E:\second-life-view\tools\insta360" | Out-Null

# 拷贝已解压好的 Windows Camera SDK（体积较大，见下方 gitignore）
Copy-Item -Recurse -Force `
  "E:\second-life-view-backend-handoff-v0.4\CameraSDK_MediaSDK\Windows_CameraSDK\CameraSDK-2.2.0-20260918_164435-win64" `
  "E:\second-life-view\tools\insta360\CameraSDK"
```

拷贝后 Demo 路径应为：

```text
E:\second-life-view\tools\insta360\CameraSDK\bin\CameraSDKDemo.exe
```

### 1.2 务必加入 .gitignore（避免把 SDK 推进 GitHub）

在 `E:\second-life-view\.gitignore` 中增加类似规则（若尚未有）：

```gitignore
# Insta360 desktop SDK (local only — do not push)
tools/insta360/CameraSDK/
tools/insta360/**/*.dll
tools/insta360/**/*.exe

# Local camera dumps before renaming into panoramas/
data/samples/captures_raw/
```

只把本流程文档、脚本说明提交仓库即可。

### 1.3 驱动与模式（已验证过可跳过细读）

- Windows 需 **libusbK**（Zadig）  
- USB 弹窗选 **「安卓手机控制」**（即文档说的安卓模式）  
- 笔记本供电弱时可能切换失败；驱动装好后你已成功连上 X4 Air  

---

## 2. 端到端目标链路（SDK → 本仓库 pipeline）

```text
X4 Air + CameraSDKDemo
  → 拍照并下载到 data/samples/captures_raw\（或任意临时目录）
  → 确认约 2:1 全景 jpg
  → 重命名复制到 data/samples/panoramas/<slug>.jpg
  → 在 pipeline/scenes.py 注册 SceneSpec
  → python pipeline/run_demo.py --scene <slug>
  → 产出 data/fixtures/scenes/<slug>/ 与 analysis
```

`source_type` 语义上记为：`insta360_camera`（即使当前没有 HTTP 字段，也在 run_notes / 对接说明里写明）。

---

## 3. 日常采集操作（在新项目目录）

### 3.1 准备

```powershell
cd E:\second-life-view
New-Item -ItemType Directory -Force -Path "data\samples\captures_raw" | Out-Null
```

相机：开机、SD 卡、尽量开 **照片机内拼接**、USB → **安卓手机控制**。

### 3.2 运行 Demo

**PowerShell（不要用 cmd 的 `cd /d`）：**

```powershell
cd E:\second-life-view\tools\insta360\CameraSDK\bin
.\CameraSDKDemo.exe --cn --debug
```

若尚未拷贝 SDK，仍可用旧路径临时跑：

```powershell
cd E:\second-life-view-backend-handoff-v0.4\CameraSDK_MediaSDK\Windows_CameraSDK\CameraSDK-2.2.0-20260918_164435-win64\bin
.\CameraSDKDemo.exe --cn --debug
```

### 3.3 菜单（已验证）

```text
主菜单 → 1 拍照
      → 1 选择模式（普通照片/全景照片）
      → 10 拍照并下载
保存目录示例：
E:/second-life-view/data/samples/captures_raw
```

退出：菜单 `0`，再拔线。

### 3.4 纳入 pipeline 输入

假设新场景 slug 叫 `x4air_lab`（自行改名，只用小写+下划线）：

1. 把下载的 jpg **复制并改名**为：
   ```text
   E:\second-life-view\data\samples\panoramas\x4air_lab.jpg
   ```
2. 编辑 `pipeline/scenes.py`，在 `SCENES` 列表末尾追加：

```python
    SceneSpec(
        slug="x4air_lab",
        scene_id="scene_x4air_lab",
        panorama_id="pano_x4air_lab",
        image_name="x4air_lab.jpg",
        title="X4 Air Lab Capture",
        page="insta360_camera",
        author="team",
        license="internal",
        order=6,
    ),
```

3. 在项目根运行：

```powershell
cd E:\second-life-view
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python pipeline/run_demo.py --list
python pipeline/run_demo.py --scene x4air_lab
```

4. 查看输出：
   - `data/samples/runs/x4air_lab/`
   - `data/fixtures/scenes/x4air_lab/`

---

## 4. 与前后端 / 算法队友对接清单

本仓库目前是 **本地 pipeline**，未必已有 `POST /media`。对接时按现状问：

### 问 pipeline / 后端负责人
1. 新全景是否统一走 `data/samples/panoramas/<slug>.jpg` + `scenes.py`？  
2. 现场图是否允许 commit？还是只本地跑、fixtures 再决定是否提交？  
3. 以后若做 FastAPI，`POST /projects/{id}/media` 的字段与本目录如何映射？  
4. `source_type=insta360_camera` 要写在哪个 JSON 字段或 run_notes 里？

### 问前端负责人（若另有前端仓库）
1. 前端读的是 `data/fixtures/analysis.json` 还是别的 API？  
2. 新增 scene 后前端如何切换到 `x4air_lab`？  
3. Demo 是否需要你提供固定 canonical 文件名？

### 你可主动提供的交付物
| 交付 | 说明 |
|------|------|
| `panoramas/<slug>.jpg` | SDK 实拍 ERP |
| `scenes.py` 中的 SceneSpec | 可开 PR |
| 简短 run_notes | 机型 X4 Air、固件、SDK 2.2.0、机内拼接与否 |
| 本流程文档 | 方便队友复现采集 |

---

## 5. 分阶段计划（建议）

### Phase 1 — 环境迁入真正项目（0.5 天）
- [ ] Cursor 打开 `E:\second-life-view`  
- [ ] 拷贝 Camera SDK 到 `tools/insta360/CameraSDK`  
- [ ] 更新 `.gitignore`  
- [ ] Demo 在新路径再跑通一次拍照下载  

### Phase 2 — 接入 pipeline（0.5–1 天）
- [ ] 实拍 1–2 张室内全景 → `panoramas/<slug>.jpg`  
- [ ] 注册 `scenes.py`  
- [ ] `run_demo.py --scene <slug>` 跑通  
- [ ] 把结果路径同步给负责 fixtures / 前端的人  

### Phase 3 — 体验优化（有余力）
- [ ] 小脚本：提示保存目录默认 `captures_raw`，拷贝并重命名到 `panoramas`  
- [ ] 一键：`capture_notes` 模板（日期、机型、固件、slug）  
- [ ] 若后端提供 upload API：脚本在下载后 `curl`/Python 上传  

### 明确不做
- Media SDK 拼接  
- 把 Camera SDK 嵌进网页  
- 提交 `tools/insta360/CameraSDK` 二进制到 GitHub  

---

## 6. 快速命令备忘

```powershell
# 打开 SDK Demo（新项目内路径）
cd E:\second-life-view\tools\insta360\CameraSDK\bin
.\CameraSDKDemo.exe --cn --debug

# 跑某一实拍场景
cd E:\second-life-view
python pipeline/run_demo.py --scene x4air_lab

# 列出已配置且图片存在的场景
python pipeline/run_demo.py --list
```

---

## 7. 故障与兜底

| 问题 | 处理 |
|------|------|
| Demo 找不到相机 | USB → 安卓手机控制；管理员运行；检查 libusbK |
| 图不是 2:1 全景 | 开机制内拼接后重拍 |
| pipeline 读图失败 | 确认路径 `data/samples/panoramas/<slug>.jpg` 与 `scenes.py` 中 `image_name` 一致 |
| 无 GPU / 环境装不动 torch | 先把图和 SceneSpec 交给有环境的队友跑 `run_demo` |
| 笔电又切不了安卓模式 | 带电 Hub；或暂时用文件传输拷图，但 Demo 控拍需安卓手机控制 |

---

## 8. 验收标准（SDK 在真正项目里算完成）

- [ ] 在 `E:\second-life-view\tools\insta360\CameraSDK` 能独立跑 Demo（或不依赖旧盘路径）  
- [ ] 至少 1 张 X4 Air 实拍全景进入 `data/samples/panoramas/`  
- [ ] `scenes.py` 已注册并可 `run_demo.py --scene <slug>`  
- [ ] 队友知道实拍图路径与 slug  
- [ ] SDK 大文件未误提交到 git  

---

## 9. 相关旧文档（只读参考）

| 文档 | 位置 |
|------|------|
| Windows USB 操作手册 | `E:\second-life-view-backend-handoff-v0.4\SDK_WINDOWS_USB_操作手册.md` |
| Runbook 填空本 | `E:\second-life-view-backend-handoff-v0.4\SDK_RUNBOOK.md` |
| 产品 handoff | `E:\second-life-view-backend-handoff-v0.4\second-life-view-backend-handoff-v0.4\` |

正式流程以 **本文 + `E:\second-life-view` 仓库** 为准。

---

**版本：** v1  
**日期：** 2026-09-22  
**维护：** SDK 负责人；接口变更时更新 §4、§5
