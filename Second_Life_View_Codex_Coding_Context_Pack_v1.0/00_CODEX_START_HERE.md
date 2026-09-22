# Second Life View｜Codex Coding Context Pack｜START HERE

**Date:** 2026-09-22  
**Purpose:** Frontend Coding handoff for the current Second Life View main framework.  
**Current Prototype:** `03_Prototype/Second_Life_View_W02_Dual_View_Project_Review_Prototype_v2.4.html`

---

## 1. Current decision

The main framework is **Coding-Ready**.

You may implement:

- application shell;
- C01 / C02 / C03;
- W01;
- W02-A / W02-B;
- D01 main page;
- shared components;
- routing / return context;
- canonical domain types;
- a unified fixture adapter;
- selectors / derived read models;
- loading / empty / error scaffolding.

Do **not** interpret Coding-Ready as “copy the current HTML architecture into React”.

Correct implementation order:

```text
Canonical domain model
→ one canonical fixtureProject / API adapter
→ selectors / derived read models
→ page components
→ reconstruct current visual + interaction authority
```

---

## 2. Read these files in this exact order

### Highest priority

1. `01_Current_Authority/Second_Life_View_Current_Authority_Map_v2.0.md`
2. `01_Current_Authority/Second_Life_View_Current_Information_Architecture_v1.2_Coding_Ready.md`
3. `04_Data_Contracts/Second_Life_View_Pre_Coding_Master_Framework_Data_Boundary_v1.0_DRAFT.md`
4. `02_Product_Contracts/W02_Dual_View_Review_Final_Closure_Boundary_v0.6_DRAFT.md`
5. `03_Prototype/Second_Life_View_W02_Dual_View_Project_Review_Prototype_v2.4.html`

### Background only

6. `05_Historical_Context/Second_Life_View_Master_Project_Context_v1.0_HISTORICAL.md`

The historical file contains valuable product reasoning, six-path context, W01 / D01 background, research and technical notes, but it also contains older W02/version state. When anything conflicts, the current files above win.

---

## 3. Source-of-truth precedence

Use this order whenever two sources disagree:

```text
1. Latest explicit user decision
2. Current Authority Map v2.0
3. Current IA v1.2 Coding-Ready
4. Latest Revision Boundary for the affected module
5. Pre-Coding Data Boundary v1.0
6. Current Prototype v2.4
7. Historical Master Context
8. Old prototype / old draft
```

A prototype does not become Product Authority merely because code exists.

---

## 4. Critical interpretation rule

The current HTML is authoritative for:

```text
IA / page hierarchy
major layout
component hierarchy
interaction behavior
navigation flow
visual system
typography hierarchy
formal labels
current accepted states
```

The current HTML is **not** authoritative for:

```text
sample counts
sample dates
sample thumbnail assets
sample scene-to-batch assignments
sample VerificationItem inventory
sample reference/local-opportunity counts
page-local hardcoded aggregate numbers
```

Do not copy these fixture values into production logic.

---

## 5. Canonical entities required before page implementation

Use one data graph shared by all pages:

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

Related entities / projections:

```text
EvidenceAsset[]
HumanVerifiedFact[]
ReferenceSource[]
LocalOpportunity[]
Pathway
EvidenceStatus
ReviewStatus
Attention projection
```

Every page is a projection of this same data, not a separate fixture universe.

---

## 6. Hard data rules

Never keep independent truth such as:

```text
C03 says 6 batches
W02 says 12 batches
D01 says 25 batches
```

All counts must be derived from the same canonical data.

Especially:

```text
W02-A pending verification count
= derive from VerificationItem[]

W02-B active task count
= derive from VerificationItem[]

C03 batch count
= derive from AssessmentBatch[]

W01 component count
= derive from ComponentInstance[]
```

Do not use display labels as IDs.

Use canonical IDs:

```text
project_id
scene_id
batch_id
verification_id
```

---

## 7. Product gaps: STOP, do not invent

If implementation reaches any of these, stop and request Product Contract clarification rather than designing silently:

- W01 four-bucket summary (`保留 / 复用 / 待确认 / 回收`) mapping to the formal six Pathways;
- exact meaning/source of W01 `构件分组` projection;
- Regeneration Potential count derivation;
- production option source for C01 Region / Project Type / Project Stage;
- ReviewStatus lifecycle transitions;
- final authoritative EvidenceStatus derivation/ownership details;
- D01 full Verification field inventory/options beyond currently confirmed fields;
- whether W02-B Summary follows Status filter or remains overall active-task context;
- any new page / route / modal / drawer not defined by current IA;
- tomorrow's deferred child layers.

These are Product/Data gaps, not implementation freedom.

---

## 8. Deferred child layers

Do not design these independently yet:

```text
360 Evidence Viewer
Pathway Detail
Reference Source Detail / Drawer
Local Opportunity Detail
```

They may have interface/route placeholders only until their boundaries are confirmed.

See `06_Deferred_Tomorrow/README.md`.

---

## 9. Prototype → frontend rules

Restore the Product System, not the screenshot implementation.

High authority:

```text
interaction correctness
state completeness
IA correctness
component consistency
visual system fidelity
```

Replaceable:

```text
stock / demo imagery
sample names
sample dates
sample counts
future API content
```

Do not mechanically preserve prototype implementation details such as:

```text
innerHTML rerender architecture
querySelector event binding
page-local mutable globals
setTimeout demo simulation
location.hash as final router design
window.confirm as final UX
hardcoded arrays as domain truth
```

---

## 10. Current W02 rule

W02 is a Dual-View Project Review Workspace:

```text
W02-A 评估草案
→ AssessmentBatch-centric review

W02-B 待核实
→ VerificationItem-centric task review
```

W02-A Summary is exactly:

```text
评估分组
已审查
需关注
场景
```

Do not resurrect `待核实分组` Summary.

W02-B uses:

```text
one global table header
Material Accordion
VerificationItem rows
```

Do not resurrect the old flat table, visible Batch headers, or repeated per-Batch headers.

---

## 11. Coding freedom

You may decide without Product confirmation:

```text
React component decomposition
hooks / utilities
TypeScript implementation details
CSS Grid / Flex implementation
API client internals
caching / retry details
skeleton visual details
accessibility implementation
technical fallbacks
testing
performance optimization
lazy loading / code splitting
fixture asset substitution
```

Provided these decisions do not alter Product semantics or accepted interaction.

---

## 12. First implementation milestone

Before reconstructing pages, produce/verify:

```text
1. canonical entity types
2. one unified fixture dataset
3. selectors / derived-count utilities
4. page read-model adapters
5. route + navigation-context skeleton
```

Then reconstruct:

```text
C01 → C02 → C03 → W01 → W02 / D01
```

Do not “fix” unresolved fixture contradictions by inventing product rules.
