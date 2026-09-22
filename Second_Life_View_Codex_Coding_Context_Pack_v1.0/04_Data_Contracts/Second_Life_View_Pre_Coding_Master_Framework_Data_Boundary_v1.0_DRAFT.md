# Second Life View｜Pre-Coding Master Framework & Data Boundary v1.0 DRAFT

**Date:** 2026-09-22  
**Prototype Authority:** `Second_Life_View_W02_Dual_View_Project_Review_Prototype_v2.4.html`  
**Status:** Pre-Coding interpretation / data closure draft  
**Purpose:** 将当前高保真 Prototype 从“页面展示样例”收口为可进入 Frontend Coding 的 Product System Authority。  

---

# 0. Final Decision｜v2.4 的 Authority 边界

当前 v2.4 可以作为正式 Coding 的**主框架**，但它的 Authority 必须拆成两层：

```text
System Authority
→ IA
→ Page / Route boundary
→ Component hierarchy
→ Interaction
→ Navigation
→ State model
→ Typography / Color / Spacing
→ Formal terminology
→ Existing product enums already frozen by contract

Fixture Authority
→ sample 数字
→ sample 日期
→ sample thumbnail
→ sample scene / batch 分布
→ sample VerificationItem rows
→ sample evidence counts
→ sample reference / local opportunity counts
→ demo ingestion timing
```

因此：

> **v2.4 是主框架 Authority，但不是当前样例数据的 Production Truth。**

Coding 时不允许把当前 HTML 中散落的数字直接当正式业务常量复制到 React / backend。

---

# 1. Coding 前总原则

正式实现优先级：

```text
Product semantics
>
Data identity consistency
>
Interaction correctness
>
State completeness
>
IA correctness
>
Component consistency
>
Visual fidelity
>
Fixture 数字一致
```

当前 Prototype 已经基本完成：

```text
IA
Interaction
Visual system
Core page hierarchy
```

当前最需要收口的是：

```text
Data identity
Cross-page count derivation
Fixture ownership
State source
```

---

# 2. Page Inventory｜当前主框架

## C01｜项目设置

职责：

```text
创建 Project
填写项目基本上下文
```

当前正式结构：

```text
Project Name
Region
Project Type
Project Stage
Description
```

注意：

```text
Region / Project Type / Project Stage
当前 HTML 中的 option set 是 Hackathon fixture
不是 frozen production enum
```

---

## C02｜素材接入

职责：

```text
接收 / 展示 Scene ingestion 状态
允许 Scene rename
进入分析处理
```

当前正式 Scene 状态概念：

```text
waiting
receiving
received
ingestion_error
```

当前 1.2 秒自动完成：

```text
Demo behavior only
```

不是正式 ingestion contract。

---

## C03｜分析处理完成

职责：

```text
展示本轮处理结果
进入 W01 再生视图
```

正式信息类别：

```text
Scene count
Detected component count
Assessment batch count
Verification item count
Processing stages
```

当前具体数字仍为 fixture。

---

## W01｜再生视图

职责：

```text
空间 / Scene-first 浏览
查看 Component / Batch hotspot
查看项目级 regeneration overview
进入 D01 或 W02
```

核心正式结构：

```text
Scene viewer
Hotspot
Scene filmstrip
Project stats
Task / info floating cards
Regeneration potential
```

---

## W02｜项目审查

正式为 Dual View：

```text
W02-A 评估草案
→ AssessmentBatch-centric review

W02-B 待核实
→ VerificationItem-centric task review
```

v0.6 边界继续成立。

---

## D01｜构件 / 分组详情

职责：

```text
查看一个 AssessmentBatch
查看其 ComponentInstance
查看 Assessment
查看 Evidence
执行 Human Verification
查看 Reference / Local Opportunity
```

D01 是 W01 / W02 的共同 drill-down 页面。

---

# 3. Deferred Child Layers｜明天继续补充

当前 HTML 已经明确存在入口、但页面尚未正式实现的 child layers：

```text
Pathway Detail
360 Evidence Viewer
Reference Source Drawer / Source Detail
Local Opportunity Detail
```

这些页面：

```text
本轮不由 Coding Agent 自行补设计
```

明天 Prototype / Product Contract 完成后再进入正式 Coding。

在此之前：

```text
可以保留 route / interface placeholder
不能自行扩展产品功能
```

---

# 4. Canonical Entity Graph｜Coding 必须统一

Coding 后不能再存在 C03 / W01 / W02 / D01 各自维护一套同名 fixture。

正式最小 Entity Graph：

```text
Project
↓
Scene[]
↓
ComponentInstance[]
↓
AssessmentBatch[]
↓
VerificationItem[]
```

辅助数据：

```text
EvidenceAsset[]
HumanVerifiedFact[]
ReferenceSource[]
LocalOpportunity[]
```

状态 / projection：

```text
Pathway
EvidenceStatus
ReviewStatus
Attention projection
```

---

# 5. Canonical Identity Rules

## Project

所有页面必须引用同一个：

```text
project_id
project_name
region
project_type
project_stage
```

不得：

```text
每页再次 hardcode "HSBC MKK"
```

---

## Scene

唯一 identity：

```text
scene_id
```

所有：

```text
C02
C03
W01
W02
D01
```

必须从同一 `Scene[]` 读取。

---

## AssessmentBatch

唯一 identity：

```text
batch_id
```

W01 hotspot、W02 row、W02 VerificationItem、D01 Tree / Detail 必须引用同一 AssessmentBatch。

不得再出现：

```text
W02_BATCHES
D01_BATCH_FIXTURE
W01 text-only batch label
```

三套独立事实源。

---

## VerificationItem

唯一 identity：

```text
verification_id
```

必须关联：

```text
batch_id
```

W02-A：

```text
只显示 derived unresolved count
```

W02-B：

```text
显示 task projection
```

D01：

```text
消费相同 VerificationItem
```

---

# 6. Current Fixture Snapshot｜项目级数字盘点

以下数字只是**当前 v2.4 HTML 的实际 snapshot**，不是正式业务常量。

| Area | 当前显示 / 数据 | 当前来源 |
|---|---:|---|
| Scene | 5 | C02 / W01 / W02 基本一致 |
| C03 已识别构件 | 41 | hardcoded fixture |
| C03 构件分组 | 6 | hardcoded fixture |
| C03 待核实事项 | 7 | hardcoded fixture |
| C03 评估草案 | 1 | hardcoded fixture |
| W01 已识别构件 | 41 | hardcoded fixture |
| W01 保留 | 12 | hardcoded fixture |
| W01 复用 | 18 | hardcoded fixture |
| W01 待确认 | 7 | hardcoded fixture |
| W01 回收 | 4 | hardcoded fixture |
| W01 再生潜力 | 30 | hardcoded fixture |
| W01 sidebar group qty 合计 | 24 | `w01Groups` |
| W02 AssessmentBatch | 12 | `W02_BATCHES.length` |
| W02 Batch quantity 合计 | 27 | `W02_BATCHES.quantity` |
| W02 已审查 Batch | 5 | derived |
| W02 需关注 Batch | 4 | derived |
| W02 Scene | 5 | derived |
| W02-A unresolved count 合计 | 16 | Batch-local cached count |
| W02-A unresolved Batch | 8 | Batch-local cached count |
| W02-B VerificationItem 总数 | 9 | fixture rows |
| W02-B active VerificationItem | 7 | 5 unverified + 2 unable_to_verify |
| W02-B active affected Batch | 5 | derived |
| W02-B active onsite | 5 | derived |
| W02-B active document | 1 | derived |
| W02-B active specialist | 1 | derived |
| D01 fixture Batch | 25 | `D01_BATCH_FIXTURE` |
| D01 fixture instance qty 合计 | 40 | `D01_BATCH_FIXTURE.qty` |
| D01 Human Verification field | 3 | fixed fixture keys |
| D01 primary evidence assets | 6 | fixture |
| D01 non-primary evidence assets | 5 | fixture |
| D01 Reference “查看全部” | 12 | hardcoded fixture |
| D01 Local Opportunity “查看全部” | 3 | hardcoded fixture |

---

# 7. 当前内部一致的数字

以下关系当前是自洽的，但数值本身仍是 fixture：

## C03 ↔ W01 Component headline

```text
C03 detected components = 41
W01 detected components = 41
```

---

## W01 coarse status total

```text
12 保留
+ 18 复用
+ 7 待确认
+ 4 回收
= 41
```

数学上自洽。

但四种状态的业务语义尚未与正式六 Pathway 建立映射。

---

## C03 ↔ W02-B active VerificationItem

```text
C03 待核实事项 = 7
W02-B active VerificationItem = 7
```

当前 snapshot 一致。

---

## W02-A Summary

当前 `W02_BATCHES` 内：

```text
12 batches
5 reviewed
4 attention
5 scenes
```

全部为代码 derive，没有额外 hardcode。

---

# 8. P0 Data Identity Mismatch｜Coding 前必须消灭

## P0-1｜同一项目有三套 Batch 总量

当前：

```text
C03
→ 6 个分组

W02
→ 12 AssessmentBatch

D01 Tree
→ 25 Batch
```

这三者不能在 Coding 后继续并存为三个事实源。

如果它们是同一业务实体：

```text
必须统一
```

如果它们不是同一实体：

```text
必须重新命名 + 定义关系
```

当前 Product Contract 不支持静默认为三者不同。

---

## P0-2｜Component / Instance 总数不一致

当前：

```text
C03 / W01
→ 41 components

W02 Batch quantity sum
→ 27

D01 instance quantity sum
→ 40
```

Coding 前必须明确：

```text
AssessmentBatch.quantity
是否等于该 Batch 中 ComponentInstance count？
```

如果是：

```text
所有 Batch quantity 总和应能与被纳入评估范围的 ComponentInstance 对上
```

如果不是所有 41 个 ComponentInstance 都进入 AssessmentBatch：

必须正式定义：

```text
unbatched / excluded / out-of-scope component semantics
```

不得继续只靠数字碰巧接近。

---

## P0-3｜W02-A pending count 与 W02-B task rows 不一致

当前 W02-A：

```text
unresolved_verification_count sum = 16
涉及 8 个 Batch
```

当前 W02-B：

```text
active VerificationItem = 7
涉及 5 个 Batch
```

逐 Batch：

| Batch | W02-A `unresolved_verification_count` | W02-B active items |
|---|---:|---:|
| 木质围栏 · A组 | 3 | 3 |
| 木质围栏 · B组 | 1 | 0 |
| 户外地板 · A组 | 4 | 1 |
| 木质花箱 · A组 | 2 | 1 |
| 栏杆 · A组 | 0 | 0 |
| 栏杆 · B组 | 2 | 1 |
| 玻璃构件 · A组 | 0 | 0 |
| 玻璃构件 · B组 | 1 | 0 |
| 混凝土构件 · A组 | 0 | 0 |
| 花池 · A组 | 0 | 0 |
| 花池 · B组 | 1 | 0 |
| 其他构件 · A组 | 2 | 1 |

正式 Coding 规则：

```text
unresolved_verification_count
不能作为独立手填前端字段维护
```

必须：

```text
derive from VerificationItem[]
```

至少 active statuses：

```text
unverified
unable_to_verify
```

具体是否还包括其他状态，后端 Contract 统一定义。

---

## P0-4｜同一个 batch_id 在 W02 与 D01 Scene 不一致

数量字段在当前重叠 Batch 中基本一致，
但 Scene 大量不一致。

例如：

| batch_id | W02 Scene | D01 Scene |
|---|---|---|
| wood_deck_a | 入口 | 屋顶花园 |
| wood_planter_a | 休息区 | 屋顶花园 |
| metal_railing_a | 入口 | 屋顶花园 |
| metal_railing_b | 休息区 | 屋顶花园 |
| glass_component_a | 办公区 | 屋顶花园 |
| concrete_component_a | 后勤区 | 屋顶花园 |
| other_component_a | 后勤区 | 屋顶花园 |

原因：

```text
D01 fixture 当前把绝大多数 Batch 都硬编码到 Scene01 · 屋顶花园
```

Coding 后禁止。

D01 必须通过：

```text
batch_id
→ canonical AssessmentBatch
→ scene_id
→ canonical Scene
```

解析。

---

## P0-5｜D01 与 W02 Assessment 数据不是同一事实源

当前 W02 每个 Batch 已有：

```text
pathway
evidence_status
review_status
```

但 D01：

```text
只有 wood_fence_a 显示正式「修复翻新」
其他 Batch 默认显示「主路径待确认」
```

同时 D01 EvidenceStatus 由本地 Human Verification 完成度即时计算：

```text
全部实例核实 + 无 variance
→ 有依据
否则
→ 条件性
```

因此可能发生：

```text
W02 = 证据不足
D01 = 条件性
```

或：

```text
W02 pathway = MATERIAL_RECOVERY
D01 pathway = 主路径待确认
```

正式 Coding 必须建立单一 Assessment source。

---

# 9. P1 Product / Data Semantics Gap｜需在正式数据绑定前冻结

## P1-1｜W01 四类状态 vs 正式六 Pathway

W01 当前：

```text
保留
复用
待确认
回收
```

正式 Pathway：

```text
KEEP_IN_PLACE
DIRECT_REUSE
REFURBISH
REPURPOSE
MATERIAL_RECOVERY
DISPOSAL
```

目前没有正式 Mapping Contract。

不得由 Coding Agent 自行猜：

```text
REFURBISH 算复用？
REPURPOSE 算复用？
DISPOSAL 算什么？
待确认是 Pathway 还是 Evidence / Review 状态？
```

这是 Coding 前需要确认的 Product/Data semantics。

---

## P1-2｜W01「构件分组」到底是什么 projection

当前 sidebar：

```text
木质围栏 ×6
花池 ×8
户外地板 ×1
金属面板 ×4
栏杆 ×3
草坪 ×2
```

合计：

```text
24
```

但页面同时显示：

```text
已识别构件 = 41
```

而且这些 row 看起来更像：

```text
Component Type summary
```

而不是正式：

```text
AssessmentBatch list
```

Coding 前应冻结它到底是：

```text
A. current Scene 的 Component Type summary
B. whole Project 的 Component Type summary
C. AssessmentBatch summary
D. highlighted groups only
```

当前 Authority 不足。

---

## P1-3｜W01「再生潜力 30件」语义未冻结

当前：

```text
再生潜力 = 30
```

它看起来恰好等于：

```text
保留 12 + 复用 18
```

但 Prototype 没有正式定义这个公式。

Coding Agent 不得自行把这个巧合冻结为算法。

需要定义：

```text
regeneration_potential_count
```

是：

```text
backend read model
```

还是：

```text
由 Pathway derive
```

---

## P1-4｜ReviewStatus lifecycle 来源未定义

正式 enum 已有：

```text
unreviewed
in_review
reviewed
```

W02 当前只：

```text
display + filter
```

没有 inline editor。

但当前 Prototype 没有回答：

```text
什么动作使 Batch
unreviewed → in_review → reviewed？
```

Coding 可以先把它作为 server/domain field 读取，
但不得自行增加状态修改按钮或自动转换规则。

---

## P1-5｜EvidenceStatus 的 source of truth

正式 enum：

```text
supported
conditional
insufficient_evidence
not_applicable
```

当前同时存在：

```text
W02 fixture field
D01 local derived state
```

正式实现必须只有一个 authoritative source。

推荐架构：

```text
Domain / backend derives EvidenceStatus
Frontend reads status
Human Verification action triggers domain update
```

Frontend 不维护第二套独立 EvidenceStatus 算法。

---

## P1-6｜D01 Verification field coverage 不完整

D01 当前只正式实现三个 Human Verification field：

```text
固定方式
隐藏腐朽
表面处理
```

W02-B 当前 fixture 还包含：

```text
现状尺寸
构件来源
连接状态
回收条件
```

目前这些进入 D01 时只能：

```text
focus Human Verification section
```

Coding 时不要因为 W02-B 有这些 sample row，
就自行新增正式表单字段。

正式选择需要后续 Product Contract：

```text
A. D01 Human Verification 是 schema-driven dynamic field
B. 固定 field inventory 扩充
C. 某些 VerificationItem 进入其他 child workflow
```

当前未冻结。

---

## P1-7｜W02-B Summary 与 Status filter 的关系

当前实现：

```text
Table rows
→ 跟随 Status filter

Summary Cards
→ 始终统计 active VerificationItems
→ 忽略 Status filter
```

例如用户筛选：

```text
已核实
```

table 可能只显示 verified row，
但 Summary 仍然显示：

```text
待核实事项 7
```

这可能是合理的“work queue context”，
也可能让用户误以为 Summary 应跟随当前 filter。

需要冻结：

```text
Summary = project/task context
还是
Summary = current filtered result
```

Coding Agent 不自行改。

---

## P1-8｜W02-A Pagination 与 Material grouping

当前：

```text
page size = 7 batches
```

分页发生在 Batch row 层，
因此同一个 Material 可能被拆到两页。

但 W02-A 正式 IA 是：

```text
MaterialSection
→ AssessmentBatch[]
```

真实数据量增大后需要决定：

```text
A. project-level pagination 允许 Material 被拆页
B. material-aware pagination
C. no pagination + virtualization
D. server grouping
```

当前 `7` 只是 fixture implementation，不是产品常量。

---

# 10. P2 Demo-only Data｜Coding 时不得当正式 Contract

以下内容明确是 replaceable fixture：

```text
HSBC MKK
南京 · 江苏
2026.09.22 等日期
Batch 名称与数量
Thumbnail gradients
Attention ranking 1–4
discovered_at
W02 discovered_source sample taxonomy
D01 Evidence 6 / 5 张
Reference 查看全部 12
Local Opportunity 查看全部 3
C03 评估草案 1份
C02 1.2s 自动接入完成
W01 非主 Batch hotspot toast behavior
```

---

# 11. C01 Field Contract Boundary

当前 UI 可以保留作为主框架。

但以下选项仍为 fixture：

## Region

当前示例：

```text
南京 · 江苏
上海
深圳 · 广东
香港
```

未冻结正式 source。

---

## Project Type

当前示例：

```text
改造 / 翻新
局部更新
拆除 / 清退
```

未冻结正式 enum。

---

## Project Stage

当前示例：

```text
拟拆改前评估
方案设计中
施工前确认
```

未冻结正式 enum。

---

Coding 规则：

```text
不要因为 select 需要 options
把这些 sample 固化成 production enum
```

应通过：

```text
fixture adapter / config / API contract
```

承载。

---

# 12. Recommended Canonical Fixture Strategy｜进入 Coding 后

不要继续让每页拥有自己的 fixture 常量。

建议建立一份：

```text
fixtures/project-hsbc-mkk.ts
```

概念上包含：

```ts
const fixtureProject = {
  project,
  scenes,
  componentInstances,
  assessmentBatches,
  verificationItems,
  evidenceAssets,
  referenceSources,
  localOpportunities
}
```

页面全部通过 selector / adapter 读取。

---

# 13. No Page-local Aggregate Constants

正式禁止：

```ts
const detected = 41
const batchCount = 6
const pending = 7
```

散落在页面组件内。

必须使用 derive：

```text
scene_count
→ Scene[]

component_count
→ ComponentInstance[]

assessment_batch_count
→ AssessmentBatch[]

active_verification_count
→ VerificationItem[]

reviewed_batch_count
→ AssessmentBatch.review_status

attention_batch_count
→ attention projection
```

---

# 14. Formal Derived Count Contracts

## Scene Count

```text
count(Scene)
```

---

## Component Count

```text
count(ComponentInstance in current project / assessment scope)
```

若有 excluded entity，必须明确 scope。

---

## AssessmentBatch Count

```text
count(AssessmentBatch)
```

---

## Batch Quantity

推荐正式语义：

```text
count(ComponentInstance where batch_id == current batch)
```

如果 backend 返回 denormalized `quantity`：

```text
它必须与 ComponentInstance relation 一致
```

---

## Pending Verification Count

```text
count(VerificationItem where batch_id == current batch
and status in ACTIVE_VERIFICATION_STATUSES)
```

前端不单独维护另一份数字。

---

## W02-B Active Task Count

```text
count(VerificationItem where status in ACTIVE_VERIFICATION_STATUSES)
```

---

## Affected Batch Count

```text
distinct count(batch_id among active VerificationItems)
```

---

# 15. Proposed Active Verification Semantics

当前 Prototype 实际采用：

```text
ACTIVE_VERIFICATION_STATUSES =
[
  unverified,
  unable_to_verify
]
```

这与当前 W02-B 工作队列一致。

可以作为 Coding candidate，
但如果 backend Contract 后续调整，应以 domain contract 为准。

---

# 16. One Assessment Read Model

建议 Coding 统一：

```ts
type AssessmentBatch = {
  batch_id: string
  project_id: string
  material_group: string
  component_type: string
  batch_label: string
  scene_id: string

  pathway: Pathway
  evidence_status: EvidenceStatus
  review_status: ReviewStatus

  attention: boolean
  attention_reason?: string
}
```

数量不要成为另一套事实：

```text
quantity
→ derive or backend-consistent denormalized field
```

---

# 17. VerificationItem Read Model

```ts
type VerificationItem = {
  verification_id: string
  batch_id: string

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

  focus_key?: string

  discovered_at?: string
  discovered_source?: string
}
```

注意：

```text
discovered_source enum 仍未 production-freeze
```

因此可暂时：

```ts
discovered_source?: string
```

不要在 frontend type 里过早锁死 fixture taxonomy。

---

# 18. Project / Scene Contract

建议：

```ts
type Project = {
  project_id: string
  name: string
  region: unknown
  project_type: unknown
  project_stage: unknown
  description?: string
}
```

在 C01 option source 未冻结前：

```text
region / type / stage
不要提前写死生产 enum
```

Scene：

```ts
type Scene = {
  scene_id: string
  project_id: string
  name: string
  ingestion_status:
    | 'waiting'
    | 'receiving'
    | 'received'
    | 'ingestion_error'
}
```

---

# 19. W01 Coding Boundary

v2.4 的以下部分是正式视觉 / interaction authority：

```text
Header
Sidebar
Scene Viewer
Raw / Regeneration toggle
Viewer controls
Hotspots
Floating task card
Info card
Filmstrip
Project Review entry
```

以下是 fixture / unresolved：

```text
41
12 / 18 / 7 / 4
30
6 sidebar group rows
Hotspot quantities
Hotspot-to-batch mapping
```

Coding 时 Hotspot 必须：

```text
hotspot.batch_id
→ canonical AssessmentBatch
```

不得再：

```text
通过字符串 startsWith('木质围栏') 判断是否能进入 D01
```

---

# 20. D01 Coding Boundary

D01 主页面 layout / interaction 可以进入 Coding。

正式保留：

```text
Material / Type / Batch tree
Batch Summary Strip
Evidence Gallery
Current Assessment
Verification Summary
Observable Facts
Human Verification
360 entry
Reference Pathway
Local Opportunity
```

但数据层必须改成：

```text
D01 receives batch_id
↓
fetch / select canonical AssessmentBatch
↓
resolve Scene / VerificationItems / Evidence / Assessment
```

删除概念上的：

```text
D01_BATCH_FIXTURE as independent source of truth
```

---

# 21. D01 Human Verification Coding Strategy

当前可先实现：

```text
schema / item-driven renderer boundary
```

而不是把当前三个字段永久写死成整个产品只支持：

```text
固定方式
隐藏腐朽
表面处理
```

但在正式 field contract 未补齐前：

```text
只实现已确认字段的正式组件
未知 VerificationItem 使用 generic / unsupported state
```

不得自行编造 options。

---

# 22. ReviewStatus / EvidenceStatus Ownership

推荐 Coding architecture：

```text
Frontend
→ display / filter / submit verification action

Domain / backend
→ calculate / persist EvidenceStatus
→ persist ReviewStatus
→ return Attention projection
```

Frontend 不自行创造第二套 domain truth。

---

# 23. Attention Boundary

当前正式 UI contract：

```text
attention: boolean
attention_reason?: string
```

Frontend：

```text
只消费 projection
```

不在 Coding 阶段自行实现：

```text
attention scoring algorithm
priority model
```

除非 backend/product contract 后续明确。

---

# 24. Dates / Time Boundary

当前：

```text
2026.09.22
2026.09.21
2026.09.20
```

全部视为 fixture。

正式实现：

```text
存 timestamp / ISO data
UI layer format display
```

不要把格式化后的字符串作为数据 identity。

需要后续区分：

```text
assessment_date
updated_at
reviewed_at
discovered_at
```

当前 Prototype 不足以将它们混为同一个 date field。

---

# 25. Fixture Asset Boundary

以下不要求与 Prototype 1:1：

```text
Batch thumbnail
Panorama image
Scene thumbnail
Reference thumbnail
Local opportunity thumbnail
```

Coding 重点：

```text
container
aspect ratio
crop
radius
fallback
loading
responsive behavior
```

---

# 26. Current Fixture Material Comparison

当前 W02 与 D01 的数据量：

| Material | W02 Batch | W02 qty | D01 Batch | D01 qty |
|---|---:|---:|---:|---:|
| 木材 | 4 | 10 | 7 | 13 |
| 金属 | 2 | 4 | 4 | 6 |
| 玻璃 | 2 | 2 | 3 | 3 |
| 混凝土 | 1 | 1 | 1 | 1 |
| 植栽 | 2 | 9 | 8 | 15 |
| 其他 | 1 | 1 | 2 | 2 |
| **总计** | **12** | **27** | **25** | **40** |

这张表证明：

```text
当前 D01 Tree 不能直接当 W02 数据的 detail projection
```

Coding 时必须合并数据源。

---

# 27. Recommended Provisional Headline Fixture｜仅建议，不自动冻结

为了让 Coding 初期有一份可工作的 seed，当前最容易形成跨页面一致性的 headline 是：

```text
Scenes = 5
Detected ComponentInstances = 41
AssessmentBatches = 12
Active VerificationItems = 7
```

理由：

```text
5
→ C02 / C03 / W01 / W02 已共同使用

41
→ C03 / W01 已一致

12
→ 当前成熟度最高的 W02-A 主框架

7
→ C03 / W02-B 已一致
```

但这四个数字仍然只是：

```text
recommended canonical demo fixture
```

不是 Product Contract。

在正式 seed 建立前，需要补齐：

```text
41 ComponentInstances 如何分配到 12 AssessmentBatches
7 active VerificationItems 如何对应到 Batch pending counts
```

未经确认不由 Coding Agent自行编造。

---

# 28. Coding 可以立即开始的部分

即使上面的 fixture 数字还没有最终统一，以下工作可以直接开始：

```text
App shell
Route structure
Shared Header / Sidebar
C01 / C02 / C03 page components
W01 layout
W02-A / W02-B layout
D01 layout
Design tokens
Status Pill components
PathwayIconMap
Filter components
Accordion
Table / row components
Loading / Error / Empty scaffolding
TypeScript entity interfaces
Fixture adapter layer
Selector / derived-count utilities
Navigation context
```

前提：

```text
不得把当前错误 sample 数字写成业务逻辑
```

---

# 29. Coding 暂时不能自行决定的部分

以下必须等待 Product / Data Contract：

```text
W01 四类状态与六 Pathway 的映射
W01 构件分组 projection 语义
Regeneration Potential 算法
C01 正式 enum / lookup source
ReviewStatus transition
EvidenceStatus authoritative derivation
D01 全量 Verification field contract
W02-B Summary 是否跟随 Status filter
真实 pagination / virtualization strategy
child pages tomorrow 的正式 IA / interaction
```

这些属于：

```text
Product gap
```

不是 Implementation freedom。

---

# 30. Tomorrow Child-page Closure Queue

建议明天按这个顺序补：

```text
1. 360 Evidence Viewer
2. Pathway Detail
3. Reference Source Detail / Drawer
4. Local Opportunity Detail
```

每个页面补：

```text
Purpose
Entry
Exit / Back
Route / Modal / Drawer boundary
Data read model
Loading / Empty / Error
Core interactions
Permission if applicable
```

---

# 31. Coding Data Architecture｜推荐目录概念

```text
src/
  domain/
    project.ts
    scene.ts
    component.ts
    assessment.ts
    verification.ts

  fixtures/
    project-hsbc-mkk.ts

  selectors/
    projectSummary.ts
    assessmentSummary.ts
    verificationSummary.ts

  pages/
    creation/
    regeneration/
    review/
    detail/

  components/
    shared/
    review/
    verification/
```

具体文件拆分属于 implementation freedom，
目录不构成 Product Authority。

---

# 32. Selector Principle

所有 UI 统计通过 selector 得到。

例如：

```ts
getProjectSceneCount(projectId)
getProjectComponentCount(projectId)
getAssessmentBatchCount(projectId)
getReviewedBatchCount(projectId)
getAttentionBatchCount(projectId)
getActiveVerificationItems(projectId)
getBatchPendingVerificationCount(batchId)
getAffectedBatchCount(projectId)
```

不是：

```text
Page component 内写 41 / 12 / 7
```

---

# 33. Cross-page Invariants｜Coding Acceptance

正式 Coding 后必须满足：

1. 同一个 `project_id` 在所有页面读取同一 Project。
2. 同一个 `scene_id` 在 C02 / C03 / W01 / W02 / D01 名称一致。
3. 同一个 `batch_id` 在 W01 / W02 / D01 的 Material / Type / Scene / Quantity 一致。
4. W02-A pending count 与 W02-B active VerificationItems 一致。
5. W02-B VerificationItem 点击进入的 D01 必须仍是同一个 `batch_id`。
6. D01 Pathway 与 W02 Pathway 不得冲突。
7. D01 EvidenceStatus 与 W02 EvidenceStatus 不得存在两个独立 truth。
8. C03 Batch count 与项目实际 AssessmentBatch count 使用同一 source。
9. C03 Verification count 与 active VerificationItems 使用同一 source。
10. W01 Project component count 与 canonical ComponentInstance count 一致。
11. 所有 Summary count 均由数据 derive。
12. Filter 后只影响 view projection，不修改 domain data。
13. Demo 日期与正式 timestamps 分离。
14. Fixture thumbnail 替换不影响实体 identity。
15. 不允许通过 display label 作为 entity key。

---

# 34. State Inventory｜Coding 必须有接口

核心页面至少支持：

```text
Default
Loading
Error
Empty
Filtered Empty
```

适用页面额外：

```text
C02 ingestion state
D01 saving state
D01 dirty draft state
W02 filter / accordion state
D01 return context
```

当前 Prototype 未视觉展开的 Loading / Error：

```text
Coding 可以按已确认系统视觉补实现细节
```

但不得修改产品语义。

---

# 35. Interaction Authority｜v2.4 保留

以下交互视为当前正式主框架：

```text
C01 → C02 → C03 → W01
W01 Scene switch
W01 Raw / Regeneration toggle
W01 zoom
W01 → W02
W01 / W02 → D01
W02 dual tabs
W02-A filters / summary filters
W02-B filters / material accordion
W02-B VerificationItem → D01
D01 Batch tree
D01 ComponentInstance switch
D01 Human Verification save
D01 Back restores W01 / W02 context
```

---

# 36. Prototype Behaviors That Must NOT Be Copied Literally

```text
setTimeout(1200) 模拟 ingestion
location.hash 直接等同正式 router
window.confirm 直接等同最终 dirty-state UX
DOM innerHTML rerender architecture
querySelector event binding architecture
page-local mutable globals
hardcoded fixture arrays
```

这些只是 Prototype implementation。

Coding Agent 可使用正式 React / TypeScript / router / state solution。

---

# 37. Main Framework Freeze｜本轮可以冻结的内容

可以冻结：

```text
C01 / C02 / C03 / W01 / W02 / D01 主页面存在
核心 user journey
W02 dual-view IA
W02-A structure
W02-B Material Accordion structure
D01 main information hierarchy
shared visual system
Pathway six-enum
EvidenceStatus four-enum
ReviewStatus three-enum
VerificationStatus four-enum
VerificationType three-enum
Material-first organization
D01 drill-down pattern
```

---

# 38. 本轮不要冻结的内容

```text
当前所有 headline 数字
当前 sample Batch inventory
当前 sample Scene assignment
当前 D01 25 Batch tree
当前 W01 six sidebar groups
当前 W01 4-bucket status semantics
当前 date values
当前 discovered_source taxonomy
C01 dropdown sample options
Reference / Local Opportunity sample counts
```

---

# 39. Coding-ready Definition｜当前判断

## 已满足

```text
用户从哪里进入？
→ 已明确

核心任务是什么？
→ 已明确

主页面信息层级？
→ 已明确

主页面之间怎么导航？
→ 已明确

W02 双视图是什么？
→ 已明确

D01 是什么？
→ 已明确

主要状态 enum？
→ 大部分已明确

哪些素材只是 fixture？
→ 本文已分类
```

## 仍需在数据接通前冻结

```text
统一 seed dataset
W01 status semantics
W01 group projection
EvidenceStatus ownership
ReviewStatus lifecycle
D01 dynamic verification coverage
```

## 明天继续

```text
child pages
```

---

# 40. Final Coding Boundary

从现在开始：

> **v2.4 作为 Second Life View 主框架进入 Coding。**

但 Coding Agent 读取 Prototype 时必须使用以下解释：

```text
UI structure
→ authoritative

Interaction
→ authoritative

Current entity names / sample rows
→ fixture

Current counts
→ fixture

Current cross-page inconsistencies
→ prototype debt
→ 禁止复制为 production logic
```

Coding 的第一步不是：

```text
把 HTML 拆成 React
```

而应该是：

```text
建立 canonical domain model
→ 建立一份 fixtureProject
→ 建 selectors / derived read models
→ 让所有页面消费同一数据
→ 再复原 v2.4 UI / interaction
```

最终目标：

```text
同一个 Product System
+
同一套 Data Identity
+
多个不同 Page Projection
```

而不是：

```text
六张看起来一致、实际上各自 hardcode 的页面
```

---

# 41. Pre-Coding Acceptance Checklist

1. v2.4 标记为 Main Framework Authority。
2. 当前 sample 数字全部标记 fixture。
3. Coding 不复制 page-local aggregate constants。
4. 建立单一 Project fixture / API read model。
5. Scene 使用统一 `scene_id`。
6. Batch 使用统一 `batch_id`。
7. VerificationItem 使用统一 `verification_id`。
8. D01 不再维护独立 Batch truth。
9. W02 pending count 从 VerificationItem derive。
10. C03 batch count 从 AssessmentBatch derive。
11. C03 verification count 从 VerificationItem derive。
12. W01 component count 从 ComponentInstance derive。
13. Pathway / Evidence / Review enum 使用现有正式 Contract。
14. W01 四类 coarse status 不擅自映射六 Pathway。
15. W01 group projection 未确认前不固化 semantics。
16. D01 未确认 Verification fields 不自行扩充。
17. ReviewStatus 不自行增加状态转换规则。
18. EvidenceStatus 不在前端维护第二套 truth。
19. discovered_source 保持 fixture / extensible。
20. child pages 等明天 Contract 后再正式实现。
21. Loading / Error / Empty scaffold 可以 Coding。
22. Dynamic image asset 使用 replaceable fixture。
23. 页面 visual hierarchy 以 v2.4 为准。
24. W02 视觉与 v0.6 为准。
25. 后续任何发现涉及 Product semantics 的 gap 必须 STOP 并回到 Contract。
