# Second Life View｜W02 Dual-View Review Final Closure Boundary v0.6 DRAFT

**Date:** 2026-09-22  
**Scope:** W02｜项目审查  
**Status:** Draft for confirmation before implementation  
**Supersedes:** `W02_Dual_View_Review_Layout_Closure_Boundary_v0.5_DRAFT.md`  
**Visual Authority:** 用户最新确认的 W02-A「评估草案」截图 + W02-B「待核实」截图 + v2.3 当前实现对比  
**Product Authority:** 当前 AssessmentBatch / VerificationItem / EvidenceStatus / ReviewStatus / D01 contracts  
**Master Frame:** 1586 × 992 desktop

---

# 1. 本轮结论

W02 继续保持双视图：

```text
W02 项目审查
├─ 评估草案
└─ 待核实
```

正式语义：

```text
评估草案
→ AssessmentBatch-centric project review

待核实
→ VerificationItem-centric task review
```

本轮正式收口两件事：

```text
A.
W02-A 删除「待核实分组」Summary Card

B.
W02-B 固定 VerificationItem icon 与 VerificationStatus color mapping
```

因此：

```text
W02-A
→ 不再提供「待核实分组」Summary filter

W02-B
→ 成为项目级待核实任务的唯一完整工作区
```

但：

```text
W02-A AssessmentBatch Row 内的「待核实 X项」
继续保留
```

它承担：

```text
Batch-level signal
+
Single-Batch drill-down
```

---

# 2. 为什么删除 W02-A「待核实分组」

当前双视图结构下：

```text
顶部 Tab：
待核实
→ VerificationItem task view
```

同时 W02-A 内又存在：

```text
待核实分组
→ 只筛选 unresolved AssessmentBatch
```

实际结果：

```text
评估分组
→ AssessmentBatch table

待核实分组
→ 同一张 AssessmentBatch table
→ 仅减少部分 rows
```

信息结构、列、row action、用户任务均没有变化。

因此：

```text
待核实分组
```

不构成一个足够独立的 Summary state。

它会与上层：

```text
待核实 Tab
```

形成重复入口与概念竞争。

正式删除。

---

# 3. 删除后如何保持核实信息完整

W02-A 仍保留每个 Batch 的：

```text
待核实 X项
```

例如：

```text
3项
1项
0项
```

语义：

```text
当前 AssessmentBatch unresolved VerificationItem count
```

因此用户仍然可以：

```text
在评估草案中
→ 看见哪个 Batch 有待核实事项
```

并可：

```text
点击 >0
→ D01 Human Verification
```

如果用户要查看项目级全部待核实任务：

```text
点击顶部「待核实」Tab
→ W02-B
```

因此最终分工：

```text
W02-A 待核实列
→ Batch-level signal / drill-down

W02-B 待核实 Tab
→ Project-level task review
```

不再需要第三个：

```text
待核实分组 Summary
```

---

# 4. Final IA

```text
Project Workspace
├─ W01 再生视图
└─ W02 项目审查
   ├─ W02-A 评估草案
   └─ W02-B 待核实
```

W02-A / W02-B：

```text
internal tabs
```

不是一级 Sidebar 页面。

---

# 5. Shared Shell

W02-A / W02-B 共用：

```text
GlobalHeader
WorkspaceSidebar
PageHeader
ReviewTabs
Summary Card System
Filter System
Right Attention Rail
Typography System
Status Pill System
D01 drill-down
Back / return context
```

不得做成两套互不相关的视觉产品。

---

# 6. Global Header

保持：

```text
leaf-only BrandMark
Second Life View｜再生视图
从旧建筑到新的开始

ProjectContextSwitcher
HSBC MKK
南京 · 江苏
```

不恢复：

```text
Avatar
W01 viewer toggle
legacy CTA
```

---

# 7. Workspace Sidebar

只保留：

```text
再生视图
项目审查
```

W02 当前状态：

```text
项目审查 active
```

视觉：

```text
light yellow active surface
no yellow left stripe
```

---

# 8. Page Header

正式：

```text
项目审查
HSBC MKK / 南京 · 江苏 / Review Date
```

Project Name 不包含 Scene。

---

# 9. ReviewTabs

正式：

```text
评估草案
待核实
```

视觉：

```text
active
→ dark surface
→ white text

inactive
→ subtle gray surface
→ secondary text
```

正式 label：

```text
评估草案
待核实
```

不增加：

```text
括号
副标题
count
```

---

# 10. W02-A｜Page Purpose

W02-A 回答：

> 项目中的每个 AssessmentBatch 当前被判断成什么？

用户查看：

```text
quantity
pathway
evidence status
pending verification count
review status
attention
```

W02-A 不承担：

```text
项目级 VerificationItem task queue
```

---

# 11. W02-A｜Final Summary Cards

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

---

# 12. W02-A｜Summary Semantics

```text
评估分组
= AssessmentBatch count

已审查
= review_status == reviewed

需关注
= attention == true

场景
= Scene count
```

所有 count：

```text
dynamic
```

---

# 13. W02-A｜Summary Interaction

正式：

```text
评估分组
→ All / Reset

已审查
→ review_status = reviewed

需关注
→ attention = true

场景
→ display-only
```

支持：

```text
click active 已审查 again
→ All

click active 需关注 again
→ All
```

`评估分组`：

```text
无条件回 All
```

---

# 14. W02-A｜Summary Filter State

正式：

```ts
summary_filter:
  | 'all'
  | 'reviewed'
  | 'attention'
```

删除：

```text
unresolved
```

原因：

```text
W02-A 不再提供 unresolved-batch Summary mode
```

---

# 15. W02-A｜All / Reset Contract

点击：

```text
评估分组
```

只重置：

```text
summary_filter = all
```

不清：

```text
Material
Scene
Evidence
Review
Search
```

---

# 16. W02-A｜Summary Visual

四张卡：

```text
equal width
same height
same padding
same icon footprint
same label baseline
same metric baseline
```

推荐：

```text
grid-template-columns: repeat(4, 1fr)
```

默认：

```text
评估分组
→ 可以显示 subtle selected state
```

但必须克制：

```text
subtle yellow inset ring / outline
```

不要：

```text
strong yellow fill
```

---

# 17. W02-A｜Summary Internal Layout

正式结构：

```text
Icon
+
Content Stack
├─ Label
└─ Metric Row
   ├─ Number
   └─ Unit
```

例如：

```text
评估分组
12 个分组
```

不要把 unit 单独推到 Card 最右侧。

---

# 18. W02-A｜Filter Toolbar

继续：

```text
Material
Scene
Evidence Status
Review Status
Search
```

多个 filter：

```text
AND combination
```

Search：

```text
Batch title
Component Type
Scene
```

---

# 19. W02-A｜Material Sections

继续：

```text
MaterialSection
→ AssessmentBatchRow[]
```

Material 是 visible Section Header。

不恢复独立：

```text
材料 column
```

---

# 20. W02-A｜正式列

```text
构件 / 分组
数量
当前路径
证据状态
待核实
审查状态
操作
```

Scene / Location：

```text
第一列 secondary metadata
```

---

# 21. W02-A｜Row Visual

正式组成：

```text
thumbnail
primary batch label
secondary scene metadata
semantic pathway icon + label
evidence status pill
pending verification count
review status pill
compact secondary action
```

保持大 row。

避免：

```text
dense admin table
```

---

# 22. W02-A｜Pathway Icon System

正式：

```text
PathwayIconMap
```

六条 Pathway 不得共用同一 Leaf icon。

推荐：

```text
KEEP_IN_PLACE
→ anchor / pin semantic icon

DIRECT_REUSE
→ repeat / refresh semantic icon

REFURBISH
→ Regeneration Leaf

REPURPOSE
→ layers / transform semantic icon

MATERIAL_RECOVERY
→ recycle semantic icon

DISPOSAL
→ trash / circle-x semantic icon
```

规则：

- 固定 icon library；
- 一个 Pathway 对应一个稳定 icon；
- icon + label 同时表达；
- 不只靠颜色表达；
- 不逐行手绘 icon。

---

# 23. W02-A｜Evidence Status

正式四态：

```text
supported
→ 有依据

conditional
→ 条件性

insufficient_evidence
→ 证据不足

not_applicable
→ 不适用
```

视觉：

```text
localized light tint pill
dot + text
```

不显示 aggregate confidence。

---

# 24. W02-A｜待核实列

继续正式保留。

语义：

```text
当前 AssessmentBatch unresolved VerificationItem count
```

显示：

```text
3项
1项
0项
```

视觉：

```text
fixed width
center aligned
12–13px
medium weight
secondary text
```

交互：

```text
>0
→ clickable
→ D01 Human Verification

0
→ muted
→ display-only
```

不做成重 Pill。

---

# 25. W02-A｜待核实列 vs W02-B

必须明确：

```text
W02-A 待核实列
≠ W02-B 待核实 Tab
```

W02-A：

```text
这个 Batch 还有多少 unresolved item？
```

W02-B：

```text
整个项目具体有哪些 unresolved VerificationItem？
```

用户要处理单个 Batch：

```text
W02-A 待核实 X项
→ D01
```

用户要连续处理项目级任务：

```text
W02-B
```

---

# 26. W02-A｜Review Status

正式：

```text
unreviewed
in_review
reviewed
```

UI：

```text
未审查
审查中
已审查
```

Evidence Status 与 Review Status 分开。

---

# 27. W02-A｜Row Action

保留：

```text
打开360°
```

作为 secondary action。

主入口：

```text
BatchIdentity
→ D01
```

---

# 28. W02-A｜Attention Rail

保持：

```text
需要关注
```

语义：

```text
attention == true
```

跟随当前 W02-A filters。

点击：

```text
→ D01
→ relevant focus
```

---

# 29. W02-A｜Summary Read Model

正式最小 UI read model：

```ts
type W02DraftSummary = {
  assessment_batch_count: number
  reviewed_batch_count: number
  attention_batch_count: number
  scene_count: number
}
```

不再要求 W02-A Summary UI 消费：

```text
unresolved_batch_count
```

注意：

```text
backend 可以仍然拥有 unresolved_batch_count
```

但：

```text
不是 W02-A 当前页面必须字段
```

---

# 30. W02-A｜Local UI State

```ts
type W02DraftUIState = {
  summary_filter:
    | 'all'
    | 'reviewed'
    | 'attention'

  material_filter: string | 'all'
  scene_filter: string | 'all'
  evidence_filter: EvidenceStatus | 'all'
  review_filter: ReviewStatus | 'all'

  search: string
  page: number
}
```

删除：

```text
summary_filter = unresolved
```

---

# 31. W02-B｜Page Purpose

W02-B 是：

```text
Project-level Verification Task Review
```

它回答：

> 当前项目具体还有哪些 VerificationItem 没有解决？

不是：

```text
Batch summary
```

也不是：

```text
flat admin table
```

---

# 32. W02-B｜正式视觉结构

最终：

```text
Page Header
Review Tabs
Summary Cards
Review Workspace
├─ Filter Toolbar
├─ Global Verification Table Header
├─ Material Accordion Section[]
│  ├─ Material Accordion Header
│  └─ VerificationItem Row[]
└─ Attention Rail
```

不得恢复：

```text
Visible Batch Header
Per-Batch Table Header
```

---

# 33. W02-B｜数据 hierarchy 与视觉 hierarchy

数据关系：

```text
Material
→ AssessmentBatch
→ VerificationItem
```

视觉：

```text
Material Accordion Header
→ VerificationItem Row[]
```

AssessmentBatch：

```text
通过 Row BatchIdentity 表达
```

不额外渲染 full-width Batch Header。

---

# 34. W02-B｜Global Table Header

整页只保留一个：

```text
构件 / 分组
待核实事项
相关说明
状态
发现于
操作
```

位置：

```text
Filter Toolbar
↓
Global Table Header
↓
Material Accordion Sections
```

---

# 35. W02-B｜Column Grid

推荐 desktop grid：

```css
grid-template-columns:
  220px
  125px
  minmax(230px, 1fr)
  108px
  116px
  88px;
```

允许实现中：

```text
4–12px 微调
```

但所有 row 必须：

```text
共享同一 column definition
```

---

# 36. W02-B｜Material Accordion Header

结构：

```text
Material Icon / Swatch
Material Name
Pending Item Count
Affected Batch Count
Chevron
```

例如：

```text
木材
5项待核实（涉及3个分组）
```

行为：

```text
expand / collapse
```

默认：

```text
第一个有 visible pending items 的 Material 展开
其余 collapsed
```

---

# 37. W02-B｜0 Pending Material

如果：

```text
pending_count = 0
```

仍可显示：

```text
植栽
0项待核实（已全部确认）
```

默认 collapsed。

Filters 后：

```text
0 visible rows
```

的 Material 可以临时隐藏。

---

# 38. W02-B｜VerificationItem Row

正式：

```text
一行 = 一个 VerificationItem
```

Row 包含：

```text
Batch Identity
VerificationItem field
Question / rationale
VerificationStatus
Discovered metadata
Action
```

---

# 39. W02-B｜Batch Identity

第一列：

```text
thumbnail
Batch Name
Scene metadata
```

例如：

```text
木质围栏 · A组
Scene01 · 屋顶花园
```

Batch Name：

```text
clickable
→ D01
```

同 Batch 多行重复：

```text
允许
```

因为 row 必须 self-contained。

---

# 40. W02-B｜待核实事项 Icon System

每条 VerificationItem 的：

```text
待核实事项
```

前固定显示统一 semantic icon。

正式：

```text
Lucide Search
```

视觉：

```text
16–18px
fixed icon slot
secondary blue-gray / neutral stroke
与 item label baseline 对齐
```

结构：

```text
[Search Icon] 固定方式
[Search Icon] 隐藏腐朽
[Search Icon] 表面处理
```

目的：

- 建立稳定纵向视觉轴；
- 提高 item column 可扫描性；
- 对齐已确认高保真稿；
- 不通过不同 icon 猜测不同 VerificationItem 类型。

---

# 41. W02-B｜待核实事项 Icon Interaction

Search icon：

```text
display-only
```

不单独点击。

点击范围：

```text
Item label / Row Action / Batch Identity
```

按既定 Contract 进入 D01。

不把 Search icon 变成新的 action。

---

# 42. W02-B｜待核实事项字段

显示：

```text
VerificationItem.field
```

例如：

```text
固定方式
隐藏腐朽
表面处理
现状尺寸
构件来源
连接状态
回收条件
```

Frontend：

```text
不自行生成新的业务 taxonomy
```

---

# 43. W02-B｜相关说明

显示：

```text
VerificationItem.question / rationale
```

例如：

```text
确认是否可无损拆卸
检查内部是否存在腐朽或结构损伤
确认是否有涂层 / 防腐处理
```

前端不自由生成文案。

---

# 44. W02-B｜Verification Status

正式 enum 保持：

```text
unverified
unable_to_verify
verified
not_applicable
```

正式 UI label：

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

不把：

```text
unable_to_verify
```

改名成：

```text
证据不足
```

因为两者不是同一业务语义。

---

# 45. W02-B｜Verification Status Color Mapping

正式视觉映射：

```text
unverified / 待核实
→ amber / light yellow

unable_to_verify / 无法现场确认
→ red / light red

verified / 已核实
→ green / light green

not_applicable / 不适用
→ neutral gray
```

这是：

```text
Visual semantic mapping
```

不是：

```text
业务 enum 变化
```

---

# 46. W02-B｜Status Visual Tokens

推荐：

```text
待核实
background: light amber
text: amber / orange
optional dot: amber

无法现场确认
background: light red
text: red
optional dot: red

已核实
background: light green
text: green
optional dot: green

不适用
background: light neutral gray
text: secondary gray
optional dot: gray
```

避免：

```text
unable_to_verify
→ blue-gray informational style
```

因为它需要表达：

```text
当前任务无法在现场完成确认
→ higher attention than normal informational state
```

---

# 47. W02-B｜Status Pill Geometry

统一：

```text
compact pill
light tint
single-line label
12px around
```

Status column：

```text
fixed width
consistent alignment
```

不要：

```text
heavy saturated block
oversized pill
```

---

# 48. W02-B｜发现于

保留：

```text
发现于
```

当前：

```text
UI authority
→ 正式保留

Data semantics
→ Hackathon fixture / draft
```

最小：

```ts
discovered_at?: string

discovered_source?:
  | 'site_capture'
  | 'ai_detection'
  | 'document_review'
  | 'human_review'
```

在正式 backend contract 冻结前：

```text
source taxonomy 不作为 production truth
```

---

# 49. W02-B｜Action

正式：

```text
unverified
→ 去核实

unable_to_verify
→ 查看详情
```

点击：

```text
→ D01
→ exact VerificationItem if mapping exists
```

若没有正式 D01 field mapping：

```text
→ D01 Human Verification section
```

不得为了精确跳转：

```text
自行新增 D01 verification field
```

---

# 50. W02-B｜Action Button Visual

正式：

```text
secondary action
```

推荐：

```text
light gray / white surface
dark text
subtle border
Lucide ChevronRight
compact rectangular button
```

例如：

```text
去核实  ›
查看详情 ›
```

禁止：

```text
每行 black filled primary CTA
```

---

# 51. W02-B｜Final Summary Cards

正式五张：

```text
待核实事项
涉及评估分组
现场观察
文件核对
专业复核
```

---

# 52. W02-B｜Summary Semantics

```text
待核实事项
= active VerificationItem count

涉及评估分组
= distinct AssessmentBatch count among current active VerificationItems

现场观察
= verification_type == onsite_observation

文件核对
= verification_type == document_check

专业复核
= verification_type == specialist_review
```

全部 dynamic。

---

# 53. W02-B｜为什么保留「涉及评估分组」

这里的：

```text
涉及评估分组
```

与已删除的 W02-A：

```text
待核实分组
```

不是同一个 UI role。

W02-B 中：

```text
涉及评估分组
```

回答：

> 当前这些待核实任务分布在多少个 AssessmentBatch 中？

它是：

```text
Verification task context metric
```

不是：

```text
AssessmentBatch quick filter
```

因此保留。

---

# 54. W02-B｜Summary Internal Layout

正式：

```text
Icon
+
Content Stack
├─ Label
└─ Metric Row
   ├─ Number
   └─ Unit / contextual metric
```

五张：

```text
same height
same internal padding
same icon footprint
same label baseline
same metric baseline
```

---

# 55. W02-B｜不采用的旧 Summary

不恢复：

```text
待核实类型 5种
证据不足
已超时
```

原因：

```text
Verification Type 正式只有 3 类

没有 deadline / due_at / SLA / overdue contract

证据不足属于 Evidence / Verification semantics 尚未冻结的问题
```

---

# 56. W02-B｜Filter Toolbar

正式：

```text
Material
Scene
Verification Type
Status
Search
```

Search：

```text
Batch
VerificationItem field
Question
Scene
```

Filters：

```text
AND combination
```

---

# 57. W02-B｜Search Interaction

用户必须能连续输入。

不得：

```text
每 keystroke 全量重建 input
→ focus 丢失
```

可实现：

```text
stable input
partial results rerender
or focus/caret restoration
```

属于 implementation freedom。

---

# 58. W02-B｜Accordion Filter Behavior

Filters 改变后：

- 重新计算 Material visible item count；
- 重新计算 affected Batch count；
- 0 visible row 的 Material 可隐藏；
- 当前 expanded Material 变成 0 visible rows 时，自动展开第一个有结果的 Material；
- Search 与 filters AND 组合。

---

# 59. W02-B｜Pagination

Hackathon V0：

```text
Accordion 内不分页
```

fixture 数据量小，直接滚动。

未来：

```text
pagination / virtualization
```

defer。

---

# 60. W02-B｜Attention Rail

保持：

```text
需要关注
```

与 W02-A：

```text
same width
same item geometry
same rank badge
same thumbnail footprint
same copy hierarchy
```

数据 projection：

```text
与当前 W02-B VerificationItems 相关
```

点击：

```text
→ D01 relevant focus
```

---

# 61. Tab Return Context

W02 → D01 记录：

```text
source_tab
filters
search
expanded_material
scroll
```

D01 Back：

```text
→ 回原 Tab
```

至少恢复：

```text
tab
filters
search
expanded material
```

Scroll restoration：

```text
recommended
```

---

# 62. D01 Entry Context

正式：

```text
review-draft
review-verification
```

用途：

```text
决定 Back 返回哪个 W02 tab
```

不是独立产品页面。

---

# 63. W01 → W02

默认：

```text
进入项目审查
→ W02-A 评估草案
```

---

# 64. W02-A → D01

来源：

```text
BatchIdentity
VerificationCount
AttentionItem
```

返回：

```text
W02-A
```

---

# 65. W02-B → D01

来源：

```text
BatchIdentity
去核实
查看详情
AttentionItem
```

返回：

```text
W02-B
```

---

# 66. D01 Exact Verification Focus

已有正式 mapping：

```text
→ exact field
```

没有正式 mapping：

```text
→ Human Verification section
```

不得新增：

```text
现状尺寸 field
构件来源 field
连接状态 field
回收条件 field
```

除非 Product Contract 后续确认。

---

# 67. Shared Status Systems

继续区分：

```text
EvidenceStatusPill
ReviewStatusPill
VerificationStatusPill
```

它们共享：

```text
light tint
semantic color
compact geometry
text label
```

但不共享：

```text
业务 enum
```

---

# 68. Shared Typography

继续：

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
Page Title
Tab
Summary Label
Summary Metric
Material Name
Row Primary
Row Secondary
Status / Metadata
```

---

# 69. Shared Icon System

普通 UI：

```text
Lucide
```

W02-B VerificationItem Marker：

```text
Lucide Search
```

Pathway：

```text
PathwayIconMap
```

Brand：

```text
leaf-only BrandMark
```

禁止：

- text arrow；
- emoji；
- per-row hand-drawn icon；
- 同一 semantic 多个 silhouette。

---

# 70. Asset Classification

Replaceable：

```text
Batch thumbnails
Attention thumbnails
dates
counts
fixture item rows
discovered source fixture
```

System-authoritative：

```text
dual-tab IA
W02-A four-card summary
W02-A pending verification column
W02-B five-card verification summary
Material Sections
Material Accordion
single global W02-B table header
row geometry
column axis
VerificationItem Search icon
VerificationStatus color mapping
filters
Attention rail
D01 drill-down
Pathway icon mapping
typography hierarchy
```

---

# 71. Vertical Rhythm

建议：

```text
Tabs → Summary
≈ 14–16px

Summary → Workspace
≈ 12–14px

Toolbar
≈ 56–60px

Global Table Header
≈ 38–42px

Material Header
≈ 54–58px

Verification Row
≈ 66–72px
```

目标：

```text
宽松但统一
```

---

# 72. Horizontal Rhythm

W02-A：

```text
4 equal Summary Cards
```

W02-B：

```text
5 equal Summary Cards
```

Table：

```text
single horizontal grid
```

Material Header：

```text
full-span allowed
```

但 row columns 不漂移。

---

# 73. Empty State｜W02-A

显示：

```text
没有符合当前筛选条件的评估分组
```

Action：

```text
清除筛选
```

清除：

```text
Summary Filter
Material
Scene
Evidence
Review
Search
page
```

---

# 74. Empty State｜W02-B

显示：

```text
没有符合当前筛选条件的待核实事项
```

Action：

```text
清除筛选
```

清除：

```text
Material
Scene
Verification Type
Status
Search
```

并恢复：

```text
第一个有 pending items 的 Material expanded
```

---

# 75. Loading State

W02-A：

```text
4 Summary skeletons
Table skeleton
Attention Rail skeleton
```

W02-B：

```text
5 Summary skeletons
Toolbar skeleton
Global table skeleton
Material section skeleton
Attention Rail skeleton
```

Prototype 同步 fixture：

```text
visual implementation 可 defer
```

Product state 保留。

---

# 76. Error State

统一：

```text
项目审查数据暂时无法加载
重新加载
```

W02-A / W02-B 不建立两套 Error pattern。

---

# 77. Responsive / Master Frame

Primary authority：

```text
1586 × 992 desktop
```

小 viewport：

```text
保持 desktop composition
允许 page / horizontal scroll
```

不为了小 viewport：

```text
压缩正式 column 到不可读
```

Hackathon V0 不新增 mobile redesign。

---

# 78. Data Model｜W02-A Row

```ts
type W02AssessmentBatchRow = {
  batch_id: string

  material_group: string
  component_type: string
  batch_label: string
  quantity: number

  scene_id: string
  scene_name: string

  pathway: Pathway
  evidence_status: EvidenceStatus

  unresolved_verification_count: number

  review_status: ReviewStatus

  attention: boolean
  attention_reason?: string

  thumbnail_url?: string
}
```

---

# 79. Data Model｜W02-B Row

```ts
type W02VerificationItemRow = {
  verification_id: string

  batch_id: string
  batch_label: string
  component_type?: string

  material_group: string

  scene_id: string
  scene_name: string

  field: string
  question: string

  verification_type:
    | 'onsite_observation'
    | 'document_check'
    | 'specialist_review'

  status:
    | 'unverified'
    | 'unable_to_verify'
    | 'verified'
    | 'not_applicable'

  focus?: string

  discovered_at?: string
  discovered_source?: string

  thumbnail_url?: string
}
```

---

# 80. W02-B Derived Material Model

前端可 derive：

```ts
type W02VerificationMaterialGroup = {
  material_group: string
  visible_item_count: number
  affected_batch_count: number
  items: W02VerificationItemRow[]
}
```

这是 UI projection。

不是新 production entity。

---

# 81. W02-B Local UI State

```ts
type W02VerificationUIState = {
  material_filter: string | 'all'
  scene_filter: string | 'all'
  type_filter: VerificationType | 'all'
  status_filter: VerificationStatus | 'active' | 'all'

  search: string

  expanded_material: string | null
}
```

Hackathon V0：

```text
无 page
```

---

# 82. W02 Shared Navigation State

```ts
type W02NavigationContext = {
  source_tab:
    | 'review-draft'
    | 'review-verification'

  filters: unknown
  search: string

  expanded_material?: string | null
  scroll_y?: number
}
```

---

# 83. Keep / Modify / Delete / Defer

## Keep

```text
Dual Tab IA
W02-A Material Sections
W02-A Filter Toolbar
W02-A Attention Rail
W02-A AssessmentBatch Row
W02-A 待核实 X项 column
W02-B Summary Cards
W02-B Filter Toolbar
W02-B Material Accordion
W02-B Attention Rail
D01 drill-down
```

## Modify

```text
W02-A Summary Cards: 5 → 4
W02-A summary filter state
W02-A summary read model
W02-B VerificationItem icon
W02-B VerificationStatus colors
```

## Delete

```text
W02-A 待核实分组 Summary Card
W02-A unresolved Summary filter
Visible Batch Header
Repeated per-Batch Table Header
Black filled row CTA
v2.0 flat VerificationItem table
all-pathways-use-leaf behavior
```

## Defer

```text
production discovered_source taxonomy
pagination / virtualization
mobile redesign
new D01 verification fields not covered by contract
```

---

# 84. W02-A Acceptance Checklist

1. ReviewTabs 存在。
2. `评估草案` 默认 active。
3. W02-A Summary 只有四张。
4. 四张依次为 `评估分组 / 已审查 / 需关注 / 场景`。
5. 不存在 `待核实分组` Summary Card。
6. Summary 四张等宽。
7. `评估分组` = All / Reset。
8. `已审查` 可筛选 reviewed。
9. 再次点击 active `已审查` 回 All。
10. `需关注` 可筛选 attention。
11. 再次点击 active `需关注` 回 All。
12. `场景` display-only。
13. W02-A summary state 不再存在 unresolved。
14. Material Sections 保留。
15. Material column 不恢复。
16. Pathway icons 按 pathway 区分。
17. `待核实 X项` column 保留。
18. `0项` muted + non-clickable。
19. `>0` 进入 D01 Human Verification。
20. Row 保持大 row。
21. Attention Rail 保留。
22. W02-A → D01 → Back 返回 W02-A。
23. Filters / Search / Summary state 恢复。

---

# 85. W02-B Acceptance Checklist｜Structure

24. `待核实` Tab 正常打开。
25. 页面不是 flat VerificationItem table。
26. Material Accordion 存在。
27. Material Header 显示 pending item count。
28. Material Header 显示 affected batch count。
29. 第一个有 pending item 的 Material 默认展开。
30. 0 pending Material 可显示且默认 collapsed。
31. 页面只有一个 Global Table Header。
32. 不存在 visible Batch Header。
33. 不存在 repeated per-Batch Table Header。
34. AssessmentBatch 通过 Row BatchIdentity 表达。
35. Material 是唯一 visible grouping level。

---

# 86. W02-B Acceptance Checklist｜Item / Status

36. 一行 = 一个 VerificationItem。
37. 待核实事项前显示统一 Lucide Search icon。
38. Search icon size / slot 全行一致。
39. Search icon display-only。
40. `unverified` = 待核实。
41. `待核实` 使用 amber / light yellow。
42. `unable_to_verify` = 无法现场确认。
43. `无法现场确认` 使用 red / light red。
44. `verified` = 已核实。
45. `已核实` 使用 green / light green。
46. `not_applicable` = 不适用。
47. `不适用` 使用 neutral gray。
48. 不把 `无法现场确认` 改成 `证据不足`。
49. Status Pill geometry 全部统一。

---

# 87. W02-B Acceptance Checklist｜Rows / Actions

50. 第一列含 thumbnail。
51. 第一列含 Batch Name。
52. 第一列含 Scene metadata。
53. Item field 来自 VerificationItem data。
54. Question 来自 source-provided rationale。
55. Discovered column 保留。
56. `unverified` 显示 `去核实`。
57. `unable_to_verify` 显示 `查看详情`。
58. Action 使用轻量 secondary button。
59. 不使用全黑 primary CTA。
60. Button 使用统一 ChevronRight。
61. 有正式 field mapping 时聚焦 exact VerificationItem。
62. 无正式 field mapping 时进入 Human Verification section。
63. 不因 UI 需要新增 D01 fields。

---

# 88. W02-B Acceptance Checklist｜Summary / Filter

64. Summary 为五张。
65. 五张依次为：
    - 待核实事项
    - 涉及评估分组
    - 现场观察
    - 文件核对
    - 专业复核
66. `涉及评估分组` 保留。
67. 它只作为 Verification task context metric。
68. Summary values dynamic。
69. 不出现 `待核实类型 5种` hardcode。
70. 不出现 `已超时`。
71. Summary metric number + unit 同一 content stack。
72. 五张 Summary baseline 对齐。
73. Filters 包含 Material / Scene / Verification Type / Status。
74. Search 可匹配 Batch / Item / Question / Scene。
75. Filters 与 Search AND 组合。
76. Search 连续输入不丢 focus。

---

# 89. W02-B Acceptance Checklist｜Accordion / Attention

77. Filters 后 Material count 重新计算。
78. 0 visible row Material 可隐藏。
79. Expanded Material 无结果时自动展开第一个有结果 Material。
80. W02-B 不分页。
81. Attention Rail 保留。
82. Attention Rail 与 main panel 顶部对齐。
83. Attention projection 与当前 VerificationItems 相关。
84. AttentionItem → D01 relevant focus。

---

# 90. Navigation Acceptance

85. W01 → W02 默认进入 `评估草案`。
86. W02-A → D01 → Back 返回 W02-A。
87. W02-B → D01 → Back 返回 W02-B。
88. 返回恢复 Tab。
89. 返回恢复 filters。
90. 返回恢复 search。
91. W02-B 返回恢复 expanded Material。
92. Scroll restoration 推荐保留。

---

# 91. Visual Acceptance｜Final

W02-A：

```text
4-card AssessmentBatch overview
```

不能再出现：

```text
待核实分组 Summary
```

W02-B：

```text
5-card Verification task overview
+
continuous Material Accordion task table
```

必须形成：

```text
稳定 column axis
统一 VerificationItem marker
明确 Status color hierarchy
轻量 row actions
```

最终页面层级：

```text
Tab
= 当前任务模式

Summary
= 当前模式内的概览 / quick filter

Row / Item
= 具体对象状态与 drill-down
```

---

# 92. Final Product Meaning

W02 最终：

```text
Dual-View Project Review Workspace
```

W02-A：

```text
评估草案
→ 哪些 AssessmentBatch 当前被判断成什么？
```

W02-B：

```text
待核实
→ 当前项目具体还有哪些 VerificationItem 没完成？
```

W02-A 不再提供：

```text
待核实分组
```

因为它只是同一 AssessmentBatch table 的 unresolved subset，
无法形成新的任务层级。

W02-A 通过：

```text
待核实 X项 column
```

继续表达 Batch-level verification signal。

W02-B 通过：

```text
待核实事项
涉及评估分组
Material Accordion
VerificationItem rows
```

承担完整的 project-level verification workflow。

本轮最终原则：

```text
同一个概念只保留一个主要任务入口
```

以及：

```text
Summary 必须带来独立的信息价值或交互价值
```

而不是：

```text
为了凑齐五张卡
重复一个已经存在于上层 Tab 的任务入口
```
