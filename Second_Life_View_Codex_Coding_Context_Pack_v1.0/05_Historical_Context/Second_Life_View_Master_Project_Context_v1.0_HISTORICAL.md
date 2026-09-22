# Second Life View｜再生视图 — Master Project Context v1.0

**Date:** 2026-09-22  
**Purpose:** 把截至目前围绕 Insta360 Bold Maker 黑客松项目 **Second Life View｜再生视图** 已经讨论、确认、推翻、实现和仍待处理的内容，整理成一个可继续设计 / Prototype / Frontend / Pitch / 用户调研的统一上下文。  
**使用原则：** 后续若旧文档、旧截图、旧 Prototype 与本文冲突，优先以本文中标注为 **Current / Confirmed** 的内容以及最新 Revision Boundary 为准。

---

# 0. 一句话理解这个项目

Second Life View 是一个面向 **既有建筑改造 / 拆除前评估** 的 AI + 360° 影像工具。

它不是做：

```text
Reusable?
Yes / No
```

而是回答：

> 一个已经使用过、可能存在磨损、老化、局部破损或其他约束的构件 / 材料，下一步还能以什么方式继续保留价值？

核心工作流：

```text
360° Capture
→ Understand
→ Verify
→ Explore
→ Decide
→ Audit
```

AI 的角色是生成 **可审查的 draft**，专业人员拥有最终判断权。

---

# 1. 项目背景与问题来源

## 1.1 黑客松

- 项目：**Second Life View｜再生视图**
- 黑客松：Insta360 BOLD MAKER 2026
- 赛道：Track 3 / AI + ESG / 社会公益方向
- 目标：在黑客松中跑通真实可演示的核心体验，而不是生产级 SaaS。

## 1.2 Problem Ownership

真实工作经验来源：

```text
HSBC MKK Building Refurbishment
```

项目工作流中的真实痛点：

```text
改造 / 翻新项目
→ 前期已有资料有限
→ 现场踏勘主要靠走访、拍照、观察
→ 真正耗时的工作大量发生在回到办公室之后
→ 识别构件 / 材料
→ 搜集 reuse / repair / repurpose / recycle 路径
→ 查案例 / 指南 / 法规 / 本地企业 / 渠道
→ 再形成评估建议
```

因此 Second Life View 的价值不只是“现场识别”，而是：

> 把现场信息保存下来，并把后续的理解、核实、路径探索和专业审查连起来。

---

# 2. 360° 为什么不是 gimmick

早期产品思路已经明确：

普通照片要求人在现场提前判断：

```text
什么值得拍？
拍哪一个角度？
什么信息以后会需要？
```

360° 的价值是：

```text
现场先广泛捕获
→ 回来后再发现
→ 再判断
→ 再补证据
```

即：

```text
Capture first
→ discover later
```

360 的价值中心不是单纯的“360 自动识别”，而是：

```text
完整空间上下文
+
可回看的空间证据
+
后续专业判断的入口
```

---

# 3. Product Core｜Second Life Pathway

## 3.1 正式六路径

当前 Product Baseline：

```text
1. KEEP_IN_PLACE
   原位继续使用 / 原位保留

2. DIRECT_REUSE
   整件直接复用

3. REFURBISH
   修复 / 翻新后复用

4. REPURPOSE
   改造再利用 / Upcycle

5. MATERIAL_RECOVERY
   材料级再生 / 回收利用

6. DISPOSAL
   合规处置
```

另有：

```text
UNKNOWN / INSUFFICIENT_EVIDENCE
```

但它不是 Pathway。

它表示：

> 当前证据不足，系统暂时不能可靠判断最合适的路径。

## 3.2 核心原则

```text
有使用痕迹 ≠ 失去价值
局部损伤 ≠ 自动废弃
不能整件直接复用 ≠ 没有 Second Life
```

路径是价值保留 / 探索顺序，不是机械评分表。

Canonical Question：

> 这个构件 / 材料目前的状态是什么？还缺哪些关键信息？在现有状态与约束下，哪一种价值保留路径最合适？进入这条路径前还需要做什么？

---

# 4. AI / Recommendation Authority

AI / CV / VLM 不直接独立决定：

```text
能不能复用
能不能回收
是否合规
是否安全
是否达到专业性能要求
```

AI 主要负责：

```text
识别
观察事实提取
空间关系
可见损伤
材料 / 构件候选分类
证据缺口发现
```

正式 recommendation 应来自：

```text
Observable Facts
+
Human Verified Facts
+
Verified Rules / Knowledge Layer
+
Reference Pathway
+
Local Opportunity
```

专业属性无法从图像确认时：

```text
保持 unknown
```

不把视觉推断包装成认证 / 合规 / 安全结论。

---

# 5. User

## Primary User

正在进行以下任务的专业人员：

```text
pre-renovation material inventory
Second Life / circularity assessment
```

典型角色：

- sustainability consultant
- circular economy / material consultant
- architect with sustainability responsibility
- ESG / environment consultant

## Secondary User

- architect
- retrofit team
- facility / property team
- contractor
- relevant design / construction stakeholder

---

# 6. Canonical User Journey

当前核心 Journey：

```text
收到 retrofit / renovation assessment
→ 查看已有资料
→ 第一次现场踏勘
→ Insta360 / 360° 快速完整采集
→ 素材自动进入项目
→ AI Scene + Component Inventory Draft
→ Observable Facts
→ Six-path Assessment
→ 浏览 AssessmentBatch
→ Human Verification
→ Assessment refresh
→ Reference Pathway
→ Local Opportunity
→ Project Review / Audit Draft
→ 专业人员最终复核
```

---

# 7. 当前总体 IA

## 7.1 Creation Flow

```text
C01｜项目设置
→ C02｜素材接入
→ C03｜分析处理
→ W01｜再生视图
```

Creation Flow 不使用 Workspace Sidebar。

Top Stepper：

```text
1 项目设置
2 素材接入
3 分析处理
```

没有“第 4 步 再生视图”。

---

## 7.2 Project Workspace

一级导航当前只保留：

```text
再生视图
项目审查
```

不增加：

```text
构件
场景管理
评估草案
项目概览
数据与设置
```

D01 Component Detail 是共享 drill-down，不是一级导航。

---

# 8. Global Shell / Header

## Workspace Global Header

正式：

```text
leaf-only BrandMark
Second Life View｜再生视图
从旧建筑到新的开始

Project Context Switcher
HSBC MKK
南京 · 江苏
```

不保留：

```text
Avatar
undefined ellipsis
duplicate project card
legacy CTA
```

项目切换器中保留：

```text
＋ 新建再生评估项目
```

这是新建项目入口。

---

# 9. C01｜项目设置

## 9.1 Page Responsibility

创建一个新的再生评估项目。

## 9.2 当前字段

```text
项目名称 *
所在地区 *
项目类型 *
项目阶段 *
项目说明（选填）
```

当前 Demo fixture：

```text
项目名称：HSBC MKK
所在地区：南京 · 江苏
项目类型：改造 / 翻新
项目阶段：拟拆改前评估
```

已确认修改：

```text
项目名称
≠ HSBC MKK · 屋顶花园

屋顶花园是 Scene，不是 Project Name。
```

旧字段：

```text
建筑状态
拟拆改前审计
```

已改成：

```text
项目阶段
拟拆改前评估
```

## 9.3 UI 已确认

- 右上角 Avatar 删除；
- `退出创建` 靠右对齐；
- 项目名称下方多余留白压缩；
- Dropdown 必须真的能点、有最小 Demo options；
- 但这些 Demo options **不自动升级为 production enum**；
- 删除“黑客松原生 Demo / 不作为正式业务枚举”等用户可见 disclaimer。

---

# 10. C02｜素材接入

## 10.1 产品方向变化

早期是：

```text
手动上传 360 素材
```

后来因队友接 Insta360 SDK，正式方向改成：

```text
现场采集通道直连
→ 新素材自动进入当前项目
```

因此 C02 不再以 File Upload 为核心。

## 10.2 页面核心组件

```text
IngestionStatusPanel
SceneCard list
Start Analysis CTA
```

示意文案：

```text
现场采集通道已连接
正在接收现场素材
来自 Insta360 的新素材会自动进入当前项目
```

## 10.3 Scene Contract

一个主要 360° 采集资产对应一个 Scene。

Scene：

```text
可重命名
```

当前 Demo 场景常用 fixture：

```text
Scene 01｜屋顶花园
Scene 02｜休息区
Scene 03｜入口
Scene 04｜办公区
Scene 05｜后勤区
```

真实照片不是 asset authority，Neutral placeholder 可以。

## 10.4 已确认 UI

- `开始分析` CTA 靠右；
- CTA 下方多余说明文字删除；
- CTA 不要文字箭头；
- `返回上一步` 保留；
- 不使用 Avatar；
- 不显示不必要 Demo disclaimer。

## 10.5 仍待技术确认

如果 SDK 能提供：

```text
本轮采集结束
```

可靠 signal，则可进一步决定：

```text
自动进入分析
vs
用户点击开始分析
```

当前不要自行假设。

---

# 11. C03｜分析处理

Page responsibility：

```text
展示现场素材进入 AI pipeline 后的处理过程 / 结果
```

视觉结构仍保持此前成熟稿：

```text
分析处理完成
progress / completion
processing stages
result summary
processed scenes
进入再生视图
```

重要规则：

```text
Scene count
Component count
Group count
Verification count
```

都是 Demo / pipeline-derived data。

不把截图中的具体数字当正式业务常量。

---

# 12. W01｜再生视图

## 12.1 Page Purpose

用户从空间里发现要进一步评估的对象。

核心：

```text
360 Viewer
+
Hotspots
+
Scene Switcher
+
Project-level status context
```

---

## 12.2 Viewer Mode

顶部：

```text
现场视图
再生视图
```

只属于 W01。

### 现场视图

```text
raw / clean panorama
```

当切换到现场视图：

- AI hotspots / assessment cards 隐藏；
- 右侧信息卡隐藏；
- Viewer Controls 贴右侧边缘。

### 再生视图

显示：

```text
Hotspots
待处理事项
评估说明
再生潜力摘要
```

---

## 12.3 Viewer Controls

最终保留：

```text
North / Compass
Zoom +
Zoom -
```

删除：

```text
Fullscreen square
MiniMap
```

Zoom + / - 是一组固定 UI control。

普通 UI icon：

```text
使用固定 icon library
```

禁止用：

```text
文字箭头
随手画 SVG
```

---

## 12.4 Hotspot Style

Hotspot 由：

```text
外圈白边
→ 与中间彩色圆点之间有明显间隙
→ Dark Label Pill
→ Chevron / fixed UI icon
```

组成。

不是：

```text
彩色圆点 + 一圈紧贴白边
```

Hotspot：

```text
→ AssessmentBatch
→ 点击进入 D01
```

---

## 12.5 待处理事项

每个 item 应直接进入 D01 对应的核实位置：

```text
确认固定方式
→ Human Verification / 固定方式

确认表面涂层
→ 表面处理

检查隐藏损伤
→ 隐藏腐朽 / 损伤

核实候选渠道
→ Local Opportunity
```

---

## 12.6 再生潜力 Card

当前正式：

```text
纯信息摘要
不可点击
```

删除箭头。

页面级进入 W02 的入口是：

```text
进入项目审查
```

---

## 12.7 当前 W01 需要注意的 legacy semantics

当前视觉中仍曾出现：

```text
已识别构件 41
保留
复用
待确认
回收
构件分组
```

这些属于较早视觉模型。

它和当前正式六路径 / Evidence Status 并不完全等价。

因此：

> 如果后续继续精修 W01，应避免把“保留 / 复用 / 待确认 / 回收”当成正式六路径 taxonomy。

这仍是一个需要最终语义 review 的点。

---

# 13. D01｜Component Detail / Verification

## 13.1 页面身份

D01 是：

```text
AssessmentBatch Detail
+
Human Verification Workspace
```

不是一级页面。

Canonical Example：

```text
木质围栏 · A组 ×6
```

Breadcrumb：

```text
HSBC MKK
/ Scene01 · 屋顶花园
/ 木材
/ 围栏
/ A组
```

---

## 13.2 Entry Context

从 W01：

```text
Back → 再生视图
```

从 W02-A：

```text
Back → 项目审查 / 评估草案
```

从 W02-B：

```text
Back → 项目审查 / 待核实
```

需要保存 source context。

---

## 13.3 Top Classification Summary

正式字段：

```text
材料组
构件类型
分组
实例数量
所属场景
建议路径
证据状态
上次更新
```

示例：

```text
木材
围栏
A组
6件
Scene01 / 屋顶花园
修复翻新
条件性
2026.09.22
```

---

## 13.4 图标

已确认：

- 材料组 / 构件类型必须使用统一固定 icon library；
- 不接受随手画的 icon；
- `当前评估` 顶部 icon 与 Pathway icon 应复用同一 semantic source；
- `REFURBISH` 可以使用 Regeneration Leaf。

---

## 13.5 Spatial Evidence / Image Area

结构：

```text
主视图
细节 01
细节 02
细节 03
细节 04
添加照片
```

重点：

```text
主视图必须是主视图
细节按 01–04 排列
添加照片是独立入口
```

真实照片属于 Dynamic / Fixture asset，不要求 1:1 复原。

Evidence Count 的最终 copy / count semantics 仍应在真实数据接入时统一，避免“已有张数 / 添加后总数”混淆。

---

# 14. D01｜Current Assessment

当前 Hero 正式：

```text
Primary Pathway
Evidence Status
Rationale
Alternative Pathways
```

不显示：

```text
aggregate confidence
可信度较高
```

最终 Demo 核心状态：

### Before Human Verification

```text
REFURBISH / 修复翻新
Evidence: conditional / 条件性
```

### After verified facts

用户确认：

```text
固定方式
= 可拆卸螺丝 / 螺栓

隐藏腐朽
= 未发现

表面处理
= 已确认有
```

刷新后：

```text
REFURBISH / 修复翻新
Evidence: supported / 有依据
```

注意：

> 路径可以不变，证据状态从 conditional → supported。

这是一个有意设计的 Demo transition。

---

# 15. D01｜Verification Summary / Types

核心三类：

```text
固定方式
隐藏腐朽
表面处理
```

它们影响 Pathway 判断。

不是简单判断：

```text
能不能 reuse
```

而是帮助系统完成路径分流。

---

# 16. D01｜Human Verification

这是后期一个重要修正：

AssessmentBatch：

```text
A组 ×6
```

不意味着一次表单直接代表 6 件。

Human Verification 必须是：

```text
逐实例核实
```

因此 UI：

```text
实例 01
实例 02
实例 03
实例 04
实例 05
实例 06
```

每个实例分别填写：

### 固定方式

```text
可拆卸螺丝 / 螺栓
钉固
胶粘
不可判断
```

### 隐藏腐朽

```text
未发现
发现局部损伤
无法现场确认
```

### 表面处理

```text
已确认有
已确认无
无法确认
```

可选备注。

保存：

```text
保存当前实例
```

保存后：

```text
HumanVerifiedFact
→ Effective Fact
→ Assessment refresh
```

---

# 17. D01｜页面内容顺序

用户认为 Human Verification 模块太大，因此后续进行了布局调整。

当前更合理的阅读节奏：

```text
Top Classification
↓
Spatial Evidence
↓
Current Assessment
↓
Pending Verification Types
↓
Observable Facts
↓
360° 现场证据 / Reference Pathway / Local Opportunity
↓
Human Verification（较大模块）
```

Human Verification 不应横在页面中间，把 Reference / Local / 360 压到过低位置。

---

# 18. D01｜Material Tree

左侧 Material Tree：

```text
木材
└─ 围栏
   ├─ A组
   └─ B组

户外地板
木质花箱
金属
玻璃
混凝土
植栽
其他
```

用户确认：

> 可展开 / 可进入的层级到 Group 即可。

即：

```text
Material
→ Component Type
→ AssessmentBatch
```

不在左侧 Tree 继续下钻到 Instance。

Instance 在 Human Verification 内选择。

---

# 19. Reference Pathway

回答：

> 这种材料 / 构件在全球案例、行业方法、指南和 precedent 中通常还能怎么做？

内容：

- global cases
- industry method
- guideline
- technical reference
- reuse / repair / repurpose precedent

产品作用：

```text
打开可能性
```

Hackathon：

```text
不要求 live web search
```

可以：

```text
cached real research
```

禁止：

```text
编造假案例 / 假公司 / 假来源
```

---

# 20. Local Opportunity

回答：

> 在项目所在地，真实存在什么 Second Life 机会 / 资源 / 主体？

不等于单一“接收方”。

可以包括：

- repair
- refurbisher
- fabricator
- maker / upcycling studio
- reclaimed material producer
- local reuse channel
- recycling / material recovery pathway

当前 Demo 目标：

```text
南京 / 江苏
2–3 个真实 local opportunities
```

可具有不同 verification state：

```text
lead_only
existence_verified
capability_verified
eligibility_conditional
project_acceptance_confirmed
```

---

# 21. W02｜项目审查 — 当前最终 IA

最新有效边界是 **Dual-view v0.4**。

早先 Single-view v0.3 已经被 superseded。

最终：

```text
W02 项目审查
├─ 评估草案
└─ 待核实
```

两个 internal tabs，不是一级 Sidebar。

---

# 22. W02-A｜评估草案

## 22.1 Page Question

> 每个 AssessmentBatch 当前被判断成什么？

## 22.2 Summary

```text
评估分组
待核实分组
已审查
需关注
场景
```

正式语义：

```text
评估分组
= AssessmentBatch count

待核实分组
= unresolved AssessmentBatch count

已审查
= review_status == reviewed

需关注
= attention == true

场景
= Scene count
```

所有数字：

```text
dynamic
```

截图里的 18 / 7 / 6 / 4 / 4 不是业务常量。

---

## 22.3 Summary Interaction

```text
评估分组
→ All / Reset

待核实分组
→ unresolved batches

已审查
→ reviewed batches

需关注
→ attention=true

场景
→ display-only
```

状态卡再次点击：

```text
→ All
```

Summary filter 与 Toolbar filter 独立。

---

## 22.4 Filter Toolbar

```text
Material
Scene
Evidence Status
Review Status
Search
```

AND combination。

---

## 22.5 Material Sections

最新正式结构：

```text
木材 · N个分组
----------------
AssessmentBatch rows

金属 · N个分组
----------------
AssessmentBatch rows
```

**不恢复 Material column。**

Material 是组织结构。

---

## 22.6 正式列

```text
构件 / 分组
数量
当前路径
证据状态
待核实
审查状态
操作
```

Scene / Location 是第一列 secondary metadata。

---

## 22.7 Pathway Icon System

当前正式要求：

> 不能所有 Pathway 都用叶子。

需要固定 PathwayIconMap。

当前推荐：

```text
KEEP_IN_PLACE
→ Anchor / Keep semantic icon

DIRECT_REUSE
→ Repeat / Refresh icon

REFURBISH
→ Regeneration Leaf

REPURPOSE
→ Layers / Transform

MATERIAL_RECOVERY
→ Recycle

DISPOSAL
→ Trash / Circle-X
```

所有 icon 来自统一固定 UI icon library。

---

## 22.8 待核实列

显示：

```text
3项
1项
0项
```

视觉：

```text
固定列宽
居中
轻量文本
```

交互：

```text
>0
→ D01 Human Verification

0
→ muted
→ no click
```

---

## 22.9 Attention Rail

右侧：

```text
需要关注
```

是：

```text
attention == true
```

的 projection。

跟随当前 filters。

点击：

```text
→ D01 relevant section
```

---

# 23. W02-B｜待核实

## 23.1 Page Question

> 当前项目具体还有哪些 VerificationItem 没有解决？

这不是 W02-A 的简单筛选。

---

## 23.2 正式组织

不是 flat table。

正式：

```text
Material Accordion
→ AssessmentBatch
→ VerificationItem
```

例如：

```text
木材
5项待核实（涉及3个分组）
▼
  VerificationItem rows

金属
4项待核实（涉及2个分组）
>
```

---

## 23.3 Row Columns

```text
构件 / 分组
待核实事项
相关说明
状态
发现于
操作
```

第一列：

```text
thumbnail
Batch Name
Scene metadata
```

---

## 23.4 Verification Status

```text
unverified
→ 待核实

unable_to_verify
→ 无法现场确认

verified
→ 已核实

not_applicable
→ 不适用
```

默认 active work queue：

```text
unverified
+
unable_to_verify
```

---

## 23.5 Action

```text
unverified
→ 去核实

unable_to_verify
→ 查看详情
```

都：

```text
→ D01 exact VerificationItem
```

---

## 23.6 W02-B Summary

当前基于已有 Contract 可安全计算：

```text
待核实事项
涉及评估分组
现场观察
文件核对
专业复核
```

不直接使用旧稿里的：

```text
待核实类型 5种
已超时
```

因为当前没有对应正式 Data Contract。

---

## 23.7 “发现于”

第三张视觉中这个 column 有价值。

但当前 Data Contract 尚未正式冻结。

Hackathon Prototype 可以 fixture：

```text
discovered_at
discovered_source
```

例如：

```text
2026.09.22
现场采集
```

但 source taxonomy 当前仍是 Draft。

---

# 24. Data Model

核心 pipeline：

```text
360 Panorama
→ Perspective Views
→ DetectedObject
→ dedup
→ ComponentInstance
→ classification + similarity grouping
→ AssessmentBatch
→ Verification
→ Pathway Assessment
→ Reference / Local
→ Project Review
```

---

## 24.1 ComponentInstance

表示：

> 一个稳定存在、可以独立处理 / 拆卸 / 判断的真实物理构件。

ObservableFact 主要属于 ComponentInstance。

---

## 24.2 AssessmentBatch

表示：

> 一组共享同一评估上下文的 ComponentInstance。

例如：

```text
木质围栏 · A组 ×6
```

它是主要 assessment unit。

---

## 24.3 Count Semantics

必须区分：

```text
Material Group count
AssessmentBatch count
Physical quantity
Detection count
```

例如：

```text
木材 7组
→ 7 个 AssessmentBatch

A组 6件
→ 6 个 physical ComponentInstance
```

不允许出现：

```text
A组 (6件) 4
```

这种 mystery number。

---

# 25. Verification Data

核心对象：

```text
ObservableFact
HumanVerifiedFact
VerificationItem
```

VerificationItem type：

```text
onsite_observation
document_check
specialist_review
```

VerificationItem status：

```text
unverified
unable_to_verify
verified
not_applicable
```

---

# 26. Evidence Status

正式四态：

```text
supported
conditional
insufficient_evidence
not_applicable
```

不使用：

```text
aggregate confidence score
```

EvidenceStatus 与 ReviewStatus 分开。

---

# 27. Review Status

正式：

```text
unreviewed
in_review
reviewed
```

W02 当前：

```text
display + filter
```

没有正式定义 inline review status editor。

因此 Prototype 不自行补一个。

---

# 28. Frontend Data Boundary

推荐结构：

```text
UI
↓
Data Adapter Interface
↓
Fixture Adapter / Real API Adapter
```

优先级：

```text
LIVE
>
CACHED_REAL
>
FIXTURE
```

Fixture 是开发 fallback，不是最终产品真相。

前端不自己推断：

```text
pathway
evidence status
attention
review status
unresolved count
```

这些应该来自 data layer。

---

# 29. Technical Architecture / Hackathon Boundary

当前技术方向：

```text
Insta360 capture / SDK
→ 360 media
→ AI / VLM / CV observable facts
→ Component grouping
→ Assessment reasoning
→ Human verification
→ Reference / Local
→ Review
```

明确不把以下作为 Hackathon 必做核心：

```text
实时直播流
完整 SLAM
完整 video tracking
3DGS 作为核心依赖
生产级权限体系
复杂响应式
完整 error taxonomy
```

前端 / demo 先保证：

```text
核心 flow 可点通
状态可信
数据层可替换
```

---

# 30. Visual System

Master desktop frame：

```text
1586 × 992
```

Surface：

```text
Canvas        #F7F7F7
Card          #FFFFFF
Subtle        #F5F6F8
Border        #E6E8EB
Primary Text  #111214
Secondary     #667085
Dark CTA      #17191C
```

Accent：

```text
Yellow
```

Status：

```text
Green
Blue
Yellow
Gray
Red where necessary
```

整体：

```text
neutral
professional
clean
low-saturation
```

避免：

```text
cream / beige enterprise theme
navy SaaS look
过度 dashboard 化
```

---

# 31. Typography

Current stack：

```css
Inter,
"SF Pro Display",
"PingFang SC",
"Microsoft YaHei",
Arial,
sans-serif
```

主要层级：

```text
PageTitle
32 / 40 / 700–800

SectionTitle
18 / 26 / 700

SummaryValue
28–32 / 36 / 700–800

Primary Row Label
13–14 / 18–20 / 600–700

Body / Metadata
12–13 / 18–20

Table Header
12–13 / 18 / 600

Status Pill
11–12 / 16 / 600–700
```

---

# 32. Icon System

普通 UI：

```text
固定 icon library
```

当前 Prototype 多数使用 Lucide-like family。

规则：

```text
同一语义
→ 同一个固定 icon

禁止：
text arrow
emoji
随手画 SVG
同一语义多种 silhouette
```

Brand：

```text
leaf-only BrandMark
```

Pathway：

```text
PathwayIconMap
```

是独立 semantic system。

---

# 33. Screenshot / Asset Authority Rules

非常重要。

Prototype 不是 Screenshot Specification。

优先级：

```text
Interaction correctness
>
State completeness
>
IA correctness
>
Component consistency
>
Visual system fidelity
>
dynamic fixture pixel match
```

必须高保真：

- IA
- layout
- spacing
- alignment
- component structure
- states
- interaction
- navigation
- colors
- typography hierarchy
- formal copy
- icons
- tokens

动态素材默认不是 1:1 authority：

- 真人照片
- stock image
- demo avatar
- placeholder illustration
- dynamic project photo
- mock content

重点复原：

```text
container
size
aspect ratio
crop
radius
overlay
loading
fallback
responsive behavior
```

---

# 34. Prototype Hard Rule｜绝不再犯

**不允许把 Screenshot 直接嵌进 HTML 当页面。**

历史上曾出现：

```text
用截图作为 page image/background
```

用户明确否定。

正式要求：

```text
UI 必须是真实 DOM / CSS / JS Component
```

即使是真实照片，也只能作为 dynamic media asset，不得替代 UI。

---

# 35. Prototype → Frontend 工作原则

Coding 前先理解：

```text
IA
→ Page / Route
→ Component
→ Field
→ State
→ Interaction
→ Content / Asset
→ Product Semantics
```

不能：

```text
看到 Screenshot
→ 直接写 React
```

如果发现未定义问题涉及：

- IA
- Route
- Journey
- Data semantics
- Permission
- Lifecycle
- Formal options
- User-visible state transition
- Public / Private boundary

必须：

```text
STOP
→ 描述 ambiguity
→ 给出方案
→ 等确认
```

不能把 Product gap 当 Implementation freedom。

---

# 36. Hackathon Demo Contract

当前目标不是生产级产品。

必须有：

```text
视觉 coherent
主流程可点通
真实 DOM / CSS / JS
最小 validation
SDK / Scene 接入逻辑可演示
D01 verification interaction
关键 Hero state transition
W02 review
```

不阻塞于：

```text
完整 enum
完整权限
复杂 lifecycle
所有异常状态
复杂 responsive
生产监控
```

---

# 37. Prototype 状态与版本历史

## 早期失败版本

### v0.1

问题：

```text
组件 / icon 自行发明
视觉偏离成熟截图
```

### v0.2

问题：

```text
截图嵌入 HTML
```

已永久否定。

### v0.3

回到：

```text
真实 DOM / CSS / JS
```

### v0.4 以后

开始逐页修正：

```text
C01
C02
C03
W01
D01
W02
```

---

# 38. W02 版本历史

## v2.0

首次做 W02：

```text
W02-A Material Sections
W02-B flat VerificationItem table
```

问题：

```text
视觉偏工程化
W02-B 太像 database projection
```

## v2.1

尝试删除 W02-B，改 single-view。

问题：

```text
误删 w02DraftFilters
→ 页面无法显示
```

## v2.1.1

Hotfix：

```text
恢复 w02DraftFilters
runtime 能显示
```

## Single-view v0.3

后来发现：

```text
虽然 IA 简单
但丢失真实的 Verification Task 工作模式
```

已 superseded。

## Dual-view v0.4

当前最新 Product Boundary：

```text
评估草案
+
待核实 Material Accordion
```

## v2.2

当前最新 Prototype Candidate：

```text
Second_Life_View_W02_Dual_View_Project_Review_Prototype_v2.2
```

已生成并通过 JS syntax check。

**但截至本文生成时，还没有完成用户视觉验收。**

---

# 39. User Research

已经完成：

```text
至少 1 位正式用户访谈
```

并转为结构化 Markdown。

当前最大的研究风险：

已有约 20 位潜在访谈 / 受访结构中：

```text
建筑
既有建筑改造
可持续建筑
材料循环
```

相关专业从业者仍偏少。

因此后续用户研究优先：

```text
补充真正做 retrofit / renovation / sustainability assessment 的专业用户
```

需要验证：

- 现场采集真的痛不痛；
- 回办公室后的 research 占多少工作量；
- 专业人员最需要哪些 verification；
- 什么情况下会信任 / 不信任 AI draft；
- Reference / Local 是否真正有用；
- Project Review 的 review workflow 是否符合真实习惯。

---

# 40. Competitor / Precedent 结论

此前研究得到的重要结论：

### Madaster

已经在做：

```text
Material Passport
```

因此：

> 不把 Material Passport 本身当项目核心创新。

### CIC Material Exchange

已有材料 exchange / marketplace 方向。

因此：

> 不把 Second Life View 做成另一个材料交易平台。

### 360 / deconstruction precedent

已有用 360 支持 deconstruction planning 的先例。

因此项目的创新重点逐渐从：

```text
360 自动识别
```

后移到：

```text
Identify 之后
→ Verify
→ Pathway reasoning
→ Reference research
→ Local Opportunity
→ Audit / Review
```

---

# 41. Pitch 中最重要的产品叙事

推荐叙事不是：

> 我们用 AI 识别材料。

而是：

```text
现场信息不完整
→ 传统照片容易漏
→ 360 把空间完整带回来
→ AI 先生成 inventory / facts draft
→ 专业人员核实关键事实
→ 系统不是问“能不能复用”
→ 而是探索六条 Second Life Pathway
→ 再连接行业 precedent 与本地机会
→ 最后生成可审查的项目判断
```

一句产品向表达候选：

> 拆掉之前，先看见它的下一段生命。

该句适合作为产品叙事候选，不自动等于最终 Brand Slogan。

---

# 42. Presentation / Booth

当前方向：

```text
极简
高级
瑞士风
```

不要：

```text
普通企业 PPT
大量装饰
比例错误
无意义白边
```

曾确认：

- PPT 第 05 页暂时较可接受；
- 其余页面仍需继续统一比例 / 留白 / 视觉；
- 易拉宝 / 宣传单仍需最后尺寸、二维码、出血与 print-ready 导出。

这部分与产品 Prototype 分开处理。

---

# 43. 当前最重要的 Source-of-Truth 层级

建议后续使用：

```text
1. 最新用户明确确认
2. 最新 Revision Boundary
3. 当前 Product / Data Contract
4. 当前 Visual Authority Screenshot
5. Current Prototype
6. 旧 Prototype / 旧 Draft
```

Current Prototype 从来不能因为“已经写出来了”就自动成为 Product Authority。

---

# 44. Current Authority Documents

目前最重要的文档：

```text
Second_Life_View_Current_Information_Architecture_v1.1
Second_Life_View_ComponentInstance_AssessmentBatch_Data_Contract_v0.1
Second_Life_View_Page02_Component_Detail_Revision_Boundary_Contract_v0.2
Second_Life_View_Backend_Technical_Brief_v0.2
second_life_pathway_contract_v0.1
Second_Life_View_Canvas_Shell_Uniformity_Rules_v0.2
Second_Life_View_Visual_Tokens_Surface_Rules_v0.1
W02_Dual_View_Final_Revision_Boundary_v0.4_DRAFT
```

注意：

```text
W02_Single_View_Review_Revision_Boundary_v0.3
```

已经 superseded。

---

# 45. Deprecated / Do Not Resurrect

以下内容不要在后续实现中“顺手恢复”：

```text
截图作为网页
所有 Pathway 共用 Leaf icon
W02 flat VerificationItem table
W02 single-view v0.3
W01 MiniMap
W01 Fullscreen square
Avatar
undefined ellipsis
duplicate project card
aggregate confidence score
“UNKNOWN 是一条 pathway”
硬编码 Summary demo counts
Material column in W02-A
Human Verification 一次代表整个 A组 ×6
```

---

# 46. Still Open / Need Final Closure

## Product / UI

1. W01 左侧 legacy `保留 / 复用 / 待确认 / 回收` 与六路径正式语义是否继续保留；
2. C03 的真实 processing state 是否需要在 Demo 里演示 running；
3. C02 SDK 是否有稳定的“本轮采集结束” signal；
4. D01 Spatial Evidence 的 count copy 如何与 add-photo 行为完全统一；
5. W02-B `发现于` 的真实 backend field / source taxonomy；
6. W02 v2.2 需要视觉验收；
7. Reference / Local 的真实 cached source 内容需要最终落数据。

## Technical

1. SDK capture → Scene payload；
2. Scene / Component / Batch ID 对齐；
3. real pipeline output → Data Adapter；
4. Human Verification save / refresh；
5. cached Reference / Local data；
6. demo fallback fixture。

---

# 47. Recommended Immediate Next Steps

当前最合理顺序：

```text
1. 打开并视觉验收 W02 v2.2
2. 修 W02-A pathway icon / row rhythm
3. 修 W02-B Material Accordion / task row
4. 完成 W02 → D01 → Back regression
5. 再全量走一遍：
   C01 → C02 → C03 → W01 → D01 → W02
6. 对齐 SDK / backend real payload
7. 替换关键 fixture 为 real / cached-real
8. 最后再做 PPT / booth / print material
```

---

# 48. 全流程验收清单

## C01

- Project Name = HSBC MKK
- Dropdown 可点
- no Avatar
- no Demo disclaimer
- spacing 正常

## C02

- SDK connected state
- Scene cards 出现
- Scene 可 rename
- Start Analysis 对齐
- no helper garbage text

## C03

- processing / completed state
- dynamic counts
- Scene result cards
- enter W01

## W01

- viewer toggle
- clean现场视图
- hotspots style正确
- fixed UI icons
- no MiniMap
- regeneration card non-clickable
- pending items → D01
- enter review → W02

## D01

- Material Tree 到 Group
- top summary icons统一
- main + detail evidence layout
- current assessment = REFURBISH / conditional
- no confidence
- per-instance Human Verification
- Reference / Local / 360 cards
- save → evidence refresh

## W02-A

- dual tab
- Material Sections
- PathwayIconMap
- Summary reset
- filters
- pending count
- attention rail
- D01 drill-down

## W02-B

- Material Accordion
- VerificationItem task rows
- correct statuses
- discovered fixture
- filters/search
- D01 exact focus
- back restores tab

---

# 49. 最后一句产品定义

Second Life View 不是：

```text
“AI 看一眼，告诉你这个东西能不能复用。”
```

它更准确地是：

> **用 360° 保存既有建筑现场，用 AI 帮用户理解可观察事实、发现证据缺口，并在专业人员核实后，为构件探索最合适的 Second Life Pathway、行业参考与本地机会，最终形成一份可审查的改造前材料判断。**

