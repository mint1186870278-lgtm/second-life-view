# Second Life View｜Current Information Architecture v1.2｜Coding-Ready

**Date:** 2026-09-22  
**Status:** Current / Coding-Ready Main IA  
**Supersedes:** `Second_Life_View_Current_Information_Architecture_v1.1`  
**Primary UI Authority:** `Second_Life_View_W02_Dual_View_Project_Review_Prototype_v2.4.html` + existing accepted C01/C02/C03/W01/D01 prototype structure  
**W02 Authority:** `W02_Dual_View_Review_Final_Closure_Boundary_v0.6_DRAFT.md`  
**Pre-Coding Data Authority:** `Second_Life_View_Pre_Coding_Master_Framework_Data_Boundary_v1.0_DRAFT.md`  

---

# 0. IA Status

Second Life View 当前主 IA 已足够稳定，可作为 Frontend Coding 的页面与导航主框架。

当前冻结的是：

```text
Page hierarchy
Primary navigation
Core user journey
Main page responsibilities
Drill-down boundaries
W02 dual-view structure
D01 shared-detail role
Back / return semantics
```

当前不冻结的是：

```text
Sample counts
Sample dates
Sample entity inventory
Sample thumbnails
C01 option source
W01 legacy summary semantics
Child-page final IA（明天继续）
```

因此：

> **可以进入 Coding，但 Coding 必须把 IA Authority 与 Fixture Data 分离。**

---

# 1. Product-level Information Architecture

```text
Second Life View
│
├─ Creation Flow
│  ├─ C01｜项目设置
│  ├─ C02｜素材接入
│  └─ C03｜分析处理
│
└─ Project Workspace
   ├─ W01｜再生视图
   │  └─ D01｜AssessmentBatch Detail / Human Verification
   │
   └─ W02｜项目审查
      ├─ W02-A｜评估草案
      │  └─ D01｜AssessmentBatch Detail / Human Verification
      │
      └─ W02-B｜待核实
         └─ D01｜AssessmentBatch Detail / Human Verification
```

D01：

```text
共享 Drill-down
```

不是：

```text
一级 Sidebar 页面
```

---

# 2. Canonical User Journey

```text
收到 retrofit / renovation assessment
↓
查看已有资料
↓
第一次现场踏勘
↓
Insta360 / 360° 快速完整采集
↓
C01 / C02 建立项目并接入素材
↓
C03 AI 处理 Scene / Component / Assessment Draft
↓
W01 从空间上下文发现对象与问题
↓
D01 查看 AssessmentBatch / Evidence / Verification
↓
Human Verification
↓
Assessment refresh
↓
Reference Pathway / Local Opportunity
↓
W02-A 审查 AssessmentBatch 判断结果
↓
W02-B 清理未完成 VerificationItem
↓
专业人员最终复核 / Audit Draft
```

实际使用不要求严格线性。

进入 Workspace 后，用户可以在：

```text
W01 再生视图
↔
W02 项目审查
```

之间切换。

---

# 3. Creation Flow Boundary

Creation Flow：

```text
C01
→ C02
→ C03
→ W01
```

Creation Flow 不显示 Workspace Sidebar。

Top Stepper：

```text
1 项目设置
2 素材接入
3 分析处理
```

不增加：

```text
4 再生视图
```

因为：

```text
W01 已进入 Project Workspace
```

---

# 4. C01｜项目设置

## Page Responsibility

```text
创建 Project
建立后续评估上下文
```

## Current Field Inventory

```text
项目名称 *
所在地区 *
项目类型 *
项目阶段 *
项目说明（选填）
```

## Exit

```text
下一步：素材接入
→ C02
```

## Authority Boundary

正式：

```text
字段存在
Required / Optional
页面层级
下一步行为
```

Fixture / unresolved：

```text
Region options
Project Type options
Project Stage options
```

Coding 不得将 Prototype sample options 自动升级为 production enum。

---

# 5. C02｜素材接入

## Page Responsibility

```text
接收当前 Project 的现场 360° Scene 素材
展示 ingestion state
允许 Scene rename
进入分析
```

## Core Structure

```text
SDK / ingestion connection state
Scene list
Scene card
Scene rename
Start Analysis
```

## Scene State

```text
waiting
receiving
received
ingestion_error
```

## Navigation

```text
Back
→ C01

Start Analysis
→ C03
```

Prototype 中定时自动完成属于 Demo implementation，不属于正式 IA。

---

# 6. C03｜分析处理

## Page Responsibility

```text
展示当前项目本轮 AI processing 结果
向用户确认 Workspace 已可进入
```

## Core Information

```text
processing state
Scene count
Component count
AssessmentBatch count
VerificationItem count
Processed Scene cards
```

## Exit

```text
进入再生视图
→ W01
```

所有数字必须来自 canonical data / selector，不作为页面 hardcode。

---

# 7. Project Workspace｜一级导航

一级 Sidebar 当前只保留：

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

除非未来新的用户任务需要独立一级页面。

---

# 8. Workspace Global Header

正式：

```text
leaf-only BrandMark
Second Life View｜再生视图
从旧建筑到新的开始

Project Context Switcher
Project Name
Region
```

Project Context Switcher 内：

```text
＋ 新建再生评估项目
```

进入：

```text
C01
```

不恢复：

```text
Avatar
undefined ellipsis
duplicate project card
```

---

# 9. W01｜再生视图

## Page Responsibility

回答：

> 在现场空间上下文里，哪些对象值得进一步查看、核实或评估？

## Primary Information Structure

```text
Global Header
Workspace Sidebar
Viewer Header
360 Viewer
├─ Viewer Mode
├─ Viewer Controls
├─ Hotspots
├─ Pending / Task Card
├─ Assessment Info Card
└─ Regeneration Potential Summary
Scene Filmstrip
```

---

# 10. W01｜Viewer Mode

只属于 W01：

```text
现场视图
再生视图
```

## 现场视图

```text
clean / raw panorama
```

隐藏：

```text
AI hotspots
assessment cards
regeneration overlay information
```

## 再生视图

显示：

```text
Hotspots
待处理事项
评估说明
再生潜力摘要
```

---

# 11. W01｜Viewer Controls

正式：

```text
North / Orientation
Zoom +
Zoom -
```

删除：

```text
MiniMap
Fullscreen square
```

---

# 12. W01｜Hotspot

Hotspot entity target：

```text
AssessmentBatch
```

点击：

```text
Hotspot
→ D01(batch_id)
```

不得依赖：

```text
显示名称字符串匹配
```

Coding 使用 canonical `batch_id`。

---

# 13. W01｜待处理事项

每个 item 是 contextual shortcut。

例如：

```text
确认固定方式
→ D01 / Human Verification / 固定方式

确认表面涂层
→ D01 / Human Verification / 表面处理

检查隐藏损伤
→ D01 / Human Verification / 隐藏腐朽

核实候选渠道
→ D01 / Local Opportunity
```

如果未来 item 没有正式 D01 target contract：

```text
不得自行创建新 section
```

---

# 14. W01｜再生潜力 Card

正式：

```text
Informational only
```

不可点击。

进入项目级 review 的唯一页面级入口：

```text
进入项目审查
→ W02-A
```

---

# 15. W01｜仍未冻结的内部语义

当前视觉遗留：

```text
保留
复用
待确认
回收
```

与正式六 Pathway：

```text
KEEP_IN_PLACE
DIRECT_REUSE
REFURBISH
REPURPOSE
MATERIAL_RECOVERY
DISPOSAL
```

尚未建立正式 Mapping Contract。

因此：

```text
W01 UI shell 可以 Coding
W01 4-bucket semantics 暂不冻结
```

同样未冻结：

```text
W01「构件分组」到底是哪种 projection
Regeneration Potential count algorithm
```

这三项不阻塞主框架 Coding，但阻塞真实数据绑定。

---

# 16. D01｜AssessmentBatch Detail / Human Verification

## Page Responsibility

D01 是：

```text
AssessmentBatch Detail
+
Human Verification Workspace
```

是 W01 / W02 共用的 detail layer。

---

# 17. D01｜Entry / Return Context

从 W01：

```text
D01 Back
→ W01
→ 恢复 Scene / Viewer context
```

从 W02-A：

```text
D01 Back
→ W02 / 评估草案
→ 恢复 filters / summary / search / page
```

从 W02-B：

```text
D01 Back
→ W02 / 待核实
→ 恢复 filters / search / expanded Material
```

因此 D01 Navigation Context 至少包含：

```text
source
source_tab
batch_id
focus_target?
return_state?
```

---

# 18. D01｜Information Hierarchy

当前正式阅读顺序：

```text
Batch Identity / Breadcrumb
↓
Top Classification Summary
↓
Spatial Evidence
↓
Current Assessment
↓
Pending Verification Summary
↓
Observable Facts
↓
360 Evidence / Reference Pathway / Local Opportunity
↓
Human Verification
```

Human Verification 是大模块，但不置于页面中部阻断前面的 evidence / pathway exploration。

---

# 19. D01｜Material Tree

正式层级：

```text
Material
→ Component Type
→ AssessmentBatch
```

例如：

```text
木材
└─ 围栏
   ├─ A组
   └─ B组
```

左侧 Tree 不继续下钻到 ComponentInstance。

Instance navigation 属于 Human Verification。

---

# 20. D01｜Human Verification

正式核实单位：

```text
ComponentInstance
```

不是：

```text
整个 AssessmentBatch 一次确认
```

因此：

```text
AssessmentBatch A组 ×6
→ Instance 01–06
→ 每个 instance 分别核实
```

当前已确认的正式 field 示例：

```text
固定方式
隐藏腐朽
表面处理
```

其他 VerificationItem field 尚未完成完整 D01 Field Contract。

Coding 不得自行扩充 options / fields。

---

# 21. D01｜Assessment Refresh

Demo canonical transition：

```text
Before Human Verification
REFURBISH
conditional

↓ HumanVerifiedFact

After Verification
REFURBISH
supported
```

Pathway 可以不变，EvidenceStatus 可以提升。

不显示：

```text
aggregate confidence
```

---

# 22. D01｜Reference Pathway

回答：

> 类似构件 / 材料在真实 precedent、行业方法或指南中通常还能怎么处理？

内容类型：

```text
global case
industry method
guideline
technical reference
reuse / repair / repurpose precedent
```

Hackathon 可使用 cached real research。

不允许虚构真实来源。

当前 detail layer 明天继续冻结。

---

# 23. D01｜Local Opportunity

回答：

> 在项目所在地，真实存在什么 Second Life 机会、资源或主体？

可以包括：

```text
repair
refurbisher
fabricator
maker / upcycling studio
reclaimed material producer
reuse channel
recycling / material recovery pathway
```

当前 detail layer 明天继续冻结。

---

# 24. W02｜项目审查

W02 当前正式为：

```text
Dual-View Project Review Workspace
```

内部 Tabs：

```text
评估草案
待核实
```

不是两个一级页面。

---

# 25. W02-A｜评估草案

## Page Question

> 每个 AssessmentBatch 当前被判断成什么？

## Summary｜v0.6 Current

正式只保留四张：

```text
评估分组
已审查
需关注
场景
```

删除：

```text
待核实分组
```

原因：

```text
它只是 AssessmentBatch table 的 unresolved subset
与顶部「待核实」任务入口产生重复概念
```

---

# 26. W02-A｜Summary Interaction

```text
评估分组
→ All / Reset

已审查
→ reviewed filter

需关注
→ attention filter

场景
→ display-only
```

Summary state：

```text
all
reviewed
attention
```

不再存在：

```text
unresolved
```

---

# 27. W02-A｜Main Table

组织：

```text
Material Section
→ AssessmentBatch Row[]
```

正式列：

```text
构件 / 分组
数量
当前路径
证据状态
待核实
审查状态
操作
```

Material 是 section，不恢复 Material column。

---

# 28. W02-A｜待核实 Column

继续保留：

```text
3项
1项
0项
```

意义：

```text
Batch-level unresolved VerificationItem count
```

交互：

```text
>0
→ D01 / Human Verification

0
→ display-only
```

它不是项目级 task queue。

项目级待核实任务统一进入：

```text
W02-B
```

---

# 29. W02-A｜Attention Rail

```text
需要关注
```

是当前 W02-A projection：

```text
attention == true
```

跟随 W02-A 当前 filters。

点击：

```text
→ D01 relevant focus
```

---

# 30. W02-B｜待核实

## Page Question

> 当前项目具体还有哪些 VerificationItem 没有解决？

它不是 W02-A 的 filter state。

它是独立任务模式。

---

# 31. W02-B｜Visual / Information Hierarchy

最终：

```text
Summary Cards
↓
Filter Toolbar
↓
Global Table Header
↓
Material Accordion
→ VerificationItem Rows
```

数据关系仍然：

```text
Material
→ AssessmentBatch
→ VerificationItem
```

但 AssessmentBatch 不再额外渲染 visible full-width Batch Header。

Batch identity 在每条 VerificationItem Row 第一列中表达。

---

# 32. W02-B｜Summary

正式五张：

```text
待核实事项
涉及评估分组
现场观察
文件核对
专业复核
```

其中：

```text
涉及评估分组
```

是当前 Verification task context metric。

它不等同于已删除的 W02-A「待核实分组」quick filter。

---

# 33. W02-B｜Filter Toolbar

```text
Material
Scene
Verification Type
Status
Search
```

Search targets：

```text
Batch
VerificationItem field
Question
Scene
```

AND combination。

---

# 34. W02-B｜Material Accordion

Material 是唯一 visible grouping level。

Header：

```text
Material Name
Pending Item Count
Affected Batch Count
Chevron
```

默认：

```text
第一个有 pending item 的 Material expanded
其余 collapsed
```

0 pending Material 可以显示，用于 coverage context。

---

# 35. W02-B｜VerificationItem Row

一行：

```text
one VerificationItem
```

正式列：

```text
构件 / 分组
待核实事项
相关说明
状态
发现于
操作
```

待核实事项：

```text
统一 Search icon + field label
```

Status：

```text
unverified
→ 待核实 / amber

unable_to_verify
→ 无法现场确认 / red

verified
→ 已核实 / green

not_applicable
→ 不适用 / gray
```

---

# 36. W02-B｜Action

```text
unverified
→ 去核实

unable_to_verify
→ 查看详情
```

目标：

```text
D01 exact VerificationItem
```

如果 D01 尚无正式 field mapping：

```text
→ Human Verification section
```

不得自行创建新 field contract。

---

# 37. W02-B｜Attention Rail

保持与 W02-A 同一视觉 family。

数据 projection：

```text
与当前 Verification task context 相关的 attention batches
```

点击：

```text
→ D01 relevant focus
```

---

# 38. Page / Entity Projection Map

```text
C01
→ Project create/edit context

C02
→ Scene ingestion projection

C03
→ Project processing summary

W01
→ Scene + spatial AssessmentBatch projection

W02-A
→ AssessmentBatch review projection

W02-B
→ VerificationItem task projection

D01
→ one AssessmentBatch + ComponentInstance + VerificationItem detail
```

这是 Coding 时最重要的 Data-to-Page 映射。

---

# 39. Canonical Entity Relationships

```text
Project
├─ Scene[]
│  └─ ComponentInstance[]
│
├─ AssessmentBatch[]
│  ├─ ComponentInstance[]
│  ├─ VerificationItem[]
│  ├─ EvidenceAsset[]
│  └─ HumanVerifiedFact[]
│
├─ ReferenceSource[]
└─ LocalOpportunity[]
```

页面不能各自维护一套同名 fixture truth。

---

# 40. Navigation Context

D01 必须知道来源。

概念模型：

```text
view
review-draft
review-verification
```

用途：

```text
Back target
return filters
return search
expanded material
Scene context
scroll context
```

这不是 URL route taxonomy。

---

# 41. Route Authority Boundary

当前已经冻结：

```text
哪些内容是独立 Page
哪些内容是 W02 internal Tab
哪些内容是 D01 shared drill-down
```

当前尚未强制冻结具体 URL path string。

Frontend Coding 可以选择 router implementation，
但不得改变以下 Page Boundary：

```text
C01 / C02 / C03
W01
W02
D01
```

如果需要 deep-link：

```text
D01 必须能够由 batch_id 恢复页面内容
```

---

# 42. Deferred Child Pages / Layers｜明天继续

当前明确存在入口但尚未完成 Product Boundary：

```text
360 Evidence Viewer
Pathway Detail
Reference Source Detail / Drawer
Local Opportunity Detail
```

当前状态：

```text
Deferred Product Closure
```

不是：

```text
Coding Agent freedom
```

在确认之前：

```text
可建立 interface / placeholder boundary
不得自行扩展 workflow
```

---

# 43. Not Separate Pages

当前明确不单独建立一级页面：

```text
Scene Management
Component List
Assessment Draft
Verification Dashboard
Project Overview
Data & Settings
```

其中：

```text
评估草案
待核实
```

属于 W02 internal views。

---

# 44. Formal State Ownership

当前正式 domain enums：

```text
Pathway
→ 6 states

EvidenceStatus
→ 4 states

ReviewStatus
→ 3 states

VerificationStatus
→ 4 states

VerificationType
→ 3 states
```

页面只消费 / 展示 / 触发合法 action。

Frontend 不创建第二套 domain truth。

---

# 45. Coding-Ready vs Data-Ready

## Coding-Ready

以下可以立即实现：

```text
App Shell
Creation Flow
Workspace Shell
W01 UI / interaction shell
W02-A
W02-B
D01 main page
Shared components
Navigation context
Loading / Error / Empty scaffolding
Canonical types
Fixture adapter
Selectors
```

## Not Yet Fully Data-Ready

真实数据绑定前仍需冻结：

```text
W01 4-bucket summary semantics
W01 group projection semantics
Regeneration Potential derivation
C01 option source
ReviewStatus lifecycle
EvidenceStatus ownership implementation detail
D01 full Verification field coverage
W02-B Summary vs Status-filter semantics
Child layers tomorrow
```

---

# 46. Coding Rule｜Prototype Translation

Coding 不能：

```text
把当前 HTML 的 page-local constants 原样搬到 React
```

正确顺序：

```text
Canonical Domain Model
↓
Canonical fixture / API adapter
↓
Selectors / Read Models
↓
Page Components
↓
v2.4 visual / interaction reconstruction
```

---

# 47. Current Main Framework Freeze

从本版开始，以下主结构视为冻结：

```text
Creation Flow = C01 → C02 → C03
Workspace = W01 + W02
W02 = A 评估草案 + B 待核实
D01 = shared AssessmentBatch detail
W02-A = Material Sections + AssessmentBatch rows
W02-B = Material Accordion + VerificationItem rows
Human Verification = ComponentInstance-level
Material-first organization
Six-path assessment model
```

只有新的用户明确决定或新 Revision Boundary 可以改变。

---

# 48. Current Deprecated IA

禁止恢复：

```text
W02 single-view
W02 flat VerificationItem table
W02-A「待核实分组」Summary Card
Material column in W02-A
D01 as top-level sidebar page
W01 MiniMap
Screenshot-as-page
```

---

# 49. Tomorrow IA Extension Points

明天补子页面时，只能接在以下已知入口：

```text
D01 / 360 Evidence
→ 360 Evidence Viewer

D01 / Current Assessment / Pathway
→ Pathway Detail

D01 / Reference Pathway
→ Reference Source Detail / Drawer

D01 / Local Opportunity
→ Local Opportunity Detail
```

需要逐一确认：

```text
Page / Drawer / Modal
独立 URL 是否必要
Back semantics
Data lifecycle
Loading / Empty / Error
```

在确认前不把它们写进主一级 IA。

---

# 50. Final IA Definition

当前 Second Life View 的正式信息架构是：

```text
先创建并采集一个 Project
↓
进入以 Scene 为入口的 W01
↓
从空间上下文进入 AssessmentBatch Detail
↓
通过 D01 完成理解、证据检查与 Human Verification
↓
在 W02-A 审查 Batch 判断结果
↓
在 W02-B 清理项目级 Verification task
↓
回到 D01 完成具体核实
```

它不是：

```text
一组独立 dashboard 页面
```

而是：

```text
一个围绕 Project
以 Scene / AssessmentBatch / VerificationItem 三种信息尺度
共同工作的评估 Workspace
```

---

# 51. Coding Entry Decision

**Main Framework：可以进入 Coding。**

Coding 开始条件：

```text
使用本 IA 作为 Page / Navigation Authority
使用 v2.4 作为主视觉 / interaction reference
使用 v0.6 作为 W02 authority
使用 Pre-Coding Data Boundary v1.0 作为 fixture / data interpretation authority
```

Coding 中如果发现问题属于：

```text
IA
Product semantics
Data meaning
formal enum
permission
lifecycle
new page / new workflow
```

必须：

```text
STOP
→ 回到 Product Contract
→ 不自行决定
```

如果只是：

```text
React component split
TypeScript implementation
CSS layout
router library
selector implementation
loading skeleton detail
technical error handling
```

属于 Coding implementation freedom。
