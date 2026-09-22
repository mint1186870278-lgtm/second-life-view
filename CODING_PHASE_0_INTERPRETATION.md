# Second Life View — Coding Phase 0 Interpretation

**Review date:** 2026-09-22

**Purpose:** Authority-led implementation handoff completed before any frontend code, framework setup, or prototype modification.

**Phase 0 scope:** Interpretation only. This report does not choose URL paths, a framework, new product semantics, new fields, or new child-page behavior.

---

## 1. Executive Interpretation

The current **main framework is ready to enter coding**, but it is not fully ready for real-data binding and it is not a license to translate the monolithic prototype directly into React.

```text
Canonical domain model
→ one canonical fixture/API adapter boundary
→ selectors and page read models
→ shared application shell
→ page components
→ reconstruction of the accepted visual and interaction system
```

The v2.4 prototype is authoritative for hierarchy, major layout, component hierarchy, interactions, navigation, visual system, formal labels, and accepted states. It is not authoritative for sample counts, dates, images, scene-to-batch assignments, VerificationItem inventory, related-content counts, or page-local aggregates.

The repository is a **context pack only**. There is no application codebase to preserve or migrate.

---

## 2. Authority Order Used

The review followed `00_CODEX_START_HERE.md`:

```text
1. Latest explicit user decision
2. Current Authority Map v2.0
3. Current IA v1.2 Coding-Ready
4. Latest module Revision Boundary
5. Pre-Coding Data Boundary v1.0
6. Current Prototype v2.4
7. Historical Master Context
8. Old drafts / prototypes
```

Consequences:

- W02 is the v0.6 dual-view workspace, not the old single-view/flat-table design.
- W02-A has exactly four summary cards; old `待核实分组` summary/filter is removed.
- W02-B has one global header, Material accordions, and VerificationItem rows; visible Batch headers/repeated headers are deprecated.
- Current data rules override historical suggestions. W02-A pending counts and W02-B task counts derive from canonical `VerificationItem[]`.
- Historical material is background for rationale, six-path context, journey, and visual principles only.

### Files reviewed

- `00_CODEX_START_HERE.md`
- Current Authority Map v2.0
- Current Information Architecture v1.2 Coding-Ready
- Pre-Coding Master Framework & Data Boundary v1.0
- W02 Final Closure Boundary v0.6
- current v2.4 prototype HTML
- Current Open Questions Before Real Data Binding
- Deferred Product Closure README
- Implementation Entry Checklist and Manifest
- Historical Master Project Context v1.0, background only

The pack also contains two W02 v2.4 reference PNGs and superseded historical documents. Superseded documents are not implementation authority.

---

## 3. Current Repository State

The root contains one directory: `Second_Life_View_Codex_Coding_Context_Pack_v1.0/`. It contains 13 Markdown files, one HTML prototype, and two PNG references.

This is **context-only**, not an initialized application.

| Item | Present? | Interpretation |
|---|---:|---|
| `package.json` | No | No scripts/dependency contract. |
| `src/` | No | No application source. |
| TypeScript config | No | TypeScript not initialized. |
| framework config | No | No Vite/Next/Webpack choice. |
| lockfile / `node_modules` | No | No package-manager choice/install. |
| `.git/` | No | Root is not a Git working tree. |
| tests/config | No | No existing harness/conventions. |

No framework was initialized and the prototype was not modified.

### Technical constraints for setup

- Primary authority is a **1586 × 992 desktop composition**. Hackathon V0 need not add mobile redesign; smaller viewports may scroll.
- Current language is `zh-CN`; accepted font stack is Inter, SF Pro Display, PingFang SC, Microsoft YaHei, Arial, sans-serif.
- Visual system is neutral, professional, low-saturation, card-based, yellow-accented, with semantic green/amber/red/gray states.
- Use real DOM/components, never screenshots as pages/backgrounds.
- Use one Lucide-style UI icon system, leaf-only brand, and six-icon `PathwayIconMap`; no emoji/text arrows/ad-hoc icons.
- Dynamic photos are replaceable; media container/proportion/crop/radius/fallback/loading behavior is authoritative.
- Creation Flow has a three-step topbar and no Workspace sidebar. Workspace sidebar has only W01 and W02.
- URL strings are not frozen. Preserve page boundaries and keep W02-A/B internal. D01 must recover by `batch_id`.
- Loading/error/empty/filtered-empty scaffolding is required.
- Do not copy `innerHTML`, query-selector binding, mutable globals, timer simulation, final hash routing, `window.confirm`, or hardcoded arrays as truth.
- Full permissions, SLAM, live streaming, video tracking, 3DGS, complex responsive redesign, and complete error taxonomy are not Hackathon-core requirements.

---

## 4. A — Page / Route Inventory

No URL strings are specified because authority freezes boundaries, not paths.

### C01 — 项目设置

- **Responsibility/task:** Create Project context via name, Region, Project Type, Project Stage, optional Description.
- **Entry:** start/new-project flow and Project Context Switcher.
- **Exit:** next → C02.
- **Boundary:** independent Creation page, step 1/3.
- **Return state:** form draft, validation, selections, description where future navigation policy preserves them. Persistence/discard policy is not defined.
- **Stop:** sample selector options are not production enums.

### C02 — 素材接入

- **Responsibility/task:** Receive/display 360° Scenes, expose ingestion state, rename Scenes, start analysis.
- **Entry/exit:** C01 → C02; Back → C01; Start Analysis → C03.
- **Boundary:** independent Creation page, step 2/3.
- **Return state:** canonical Scene IDs, names, and ingestion states.
- **Formal states:** `waiting`, `receiving`, `received`, `ingestion_error`.
- **Stop:** 1.2-second auto-completion is demo-only.

### C03 — 分析处理

- **Responsibility/task:** Present processing results and confirm Workspace readiness.
- **Entry/exit:** C02 → C03; Back → C02; Enter Regeneration View → W01.
- **Boundary:** independent Creation page, step 3/3.
- **Return state:** same canonical Project result graph.
- **Counts:** Scene, ComponentInstance, AssessmentBatch, and active VerificationItem are selected. `评估草案 1份` lacks a canonical count contract.

### W01 — 再生视图

- **Responsibility/task:** In Scene context, find objects worth viewing, verifying, or assessing.
- **Entry:** C03, Workspace sidebar, D01 return from W01.
- **Exit:** hotspot/task → D01; Project Review → W02-A; New Project → C01.
- **Boundary:** independent primary Workspace page.
- **Return state:** selected Scene and Viewer context; source=`view`, `scene_id`, view mode, zoom/viewer state where applicable, scroll, focus.
- **Behavior:** Raw hides AI hotspots/cards/overlays; Regeneration shows them. Controls are North/orientation and Zoom +/−. MiniMap/fullscreen remain removed.
- **Hotspots:** canonical `batch_id`, never label matching.
- **Regeneration Potential:** informational, not clickable.

### W02-A — 评估草案

- **Responsibility/task:** Review what each AssessmentBatch is currently judged to be.
- **Entry:** W01 defaults here, sidebar, tab, D01 review-draft return.
- **Exit:** Batch/pending/attention → D01; tab → W02-B; sidebar → W01; 360 is deferred.
- **Boundary:** internal W02 view.
- **Return state:** tab, summary, Material/Scene/Evidence/Review filters, search, page if used, scroll, focus.
- **Summary:** exactly `评估分组 / 已审查 / 需关注 / 场景`; `all | reviewed | attention`; Scene display-only.
- **Grouping:** Material Section → AssessmentBatch rows.

### W02-B — 待核实

- **Responsibility/task:** Review and clear unresolved project VerificationItems.
- **Entry:** W02 tab and D01 review-verification return.
- **Exit:** Batch/task/attention → D01; tab → W02-A; sidebar → W01.
- **Boundary:** internal W02 view, not a W02-A filter.
- **Return state:** tab, Material/Scene/Type/Status filters, search, expanded Material, scroll.
- **Structure:** five summary cards → filters → one global header → Material accordions → VerificationItem rows.
- **Default:** expand first Material with visible pending items; zero-pending Materials may show for default coverage.
- **Pagination:** none in Hackathon V0.

### D01 — AssessmentBatch Detail / Human Verification

- **Responsibility/task:** Understand one Batch, inspect evidence/assessment, and record HumanVerifiedFacts per ComponentInstance.
- **Entry:** W01 or W02 actions using canonical `batch_id` and optional confirmed focus.
- **Exit:** source-aware Back, sidebar, or New Project; child affordances remain placeholders.
- **Boundary:** shared drill-down, not primary navigation.
- **Return state:** `source`, `source_tab`, `batch_id`, optional `focus_target`, and `return_state`; restore W01 viewer or W02 filter/tab/page/accordion/scroll state.
- **Verification unit:** ComponentInstance, never entire Batch.
- **Confirmed fields only:** 固定方式, 隐藏腐朽, 表面处理.
- **Demo transition:** `REFURBISH + conditional` may become `REFURBISH + supported`; no aggregate confidence.

Do not create primary pages for Scene Management, Component List, Assessment Draft, Verification Dashboard, Project Overview, or Data & Settings.

---

## 5. B — Component Inventory

The following are product/UI responsibilities, not a required one-file-per-item React split.

### Shared shell and patterns

- leaf-only BrandMark/lockup; Creation Topbar and three-step Stepper;
- Workspace GlobalHeader, ProjectContextSwitcher, Sidebar, and PageHeader;
- primary/secondary/light actions; loading/error/empty/filtered-empty surfaces;
- `PathwayIconMap`, EvidenceStatusPill, ReviewStatusPill, VerificationStatusPill, ingestion status;
- Summary Card, Filter Toolbar, stable Search, Material header/accordion, Attention Rail;
- Batch identity cell, media fallback, fixed W02-B Search marker, fixed ChevronRight action icon.

### Page-specific

- **C01:** Project form, option-backed selectors, counters, validation, guidance/tips.
- **C02:** ingestion panel, Scene list/card, rename control, Start Analysis state, capture guidance.
- **C03:** completion hero, processing stages, result metrics, processed Scenes, Workspace action.
- **W01:** viewer header, mode switch, panorama/media surface, orientation/zoom, hotspots, task/info cards, non-clickable potential card, filmstrip, stats/group-projection shell.

### W02 shared and specific

- Shared: ReviewTabs, summaries, filters/search, review workspace, Attention Rail, D01 context builder, statuses/icons/typography.
- W02-A: four-card summary, Material Section, AssessmentBatch row, Pathway, pending count, result footer, filtered-empty, pagination boundary.
- W02-B: five-card summary, single Global Header, Material Accordion, VerificationItem row, repeated Batch identity, Search marker, status/action mapping, zero-pending coverage.

### D01

- source-aware Back, breadcrumb/object header;
- Material → Component Type → AssessmentBatch tree, never ComponentInstance depth;
- Summary Strip, Evidence Gallery, Current Assessment, Pending Summary, Observable Facts;
- Human Verification, Instance switcher, confirmed-field renderer, note, dirty/saving feedback, variance warning;
- 360 Evidence, Reference Pathway, and Local Opportunity entry cards.

### Product behavior vs implementation splitting

Authority freezes responsibilities, hierarchy, visual families, and interaction—not React file granularity. Hooks, folder layout, shared primitives, styling solution, caching, retry, skeleton details, accessibility, testing, lazy loading, and code splitting are implementation freedom. Splitting must not merge distinct enums, turn W02-B into a W02-A filter, flatten D01 into W02, or introduce routes/workflows.

---

## 6. C — Domain / Data Inventory

### Canonical graph

```text
Project
├─ Scene[]
│  └─ ComponentInstance[]
├─ AssessmentBatch[]
│  ├─ ComponentInstance[]
│  ├─ VerificationItem[]
│  ├─ EvidenceAsset[]
│  └─ HumanVerifiedFact[]
├─ ReferenceSource[]
└─ LocalOpportunity[]
```

Storage normalization may vary, but identity/relationships must remain consistent across pages.

### Entities and confirmed relationships

- **Project:** identity `project_id`; name, region, project type, stage, optional description. Region/type/stage domains remain adapter-supplied, not enums. All pages resolve one Project.
- **Scene:** identity `scene_id`; belongs to Project; name and ingestion status. C02/C03/W01/W02/D01 must resolve the same name for an ID.
- **ComponentInstance:** one stable physical component independently handled/dismantled/judged; exists in Project/Scene context and may belong to an AssessmentBatch. Human verification is per instance. Whether unbatched/excluded instances are allowed is unresolved.
- **AssessmentBatch:** identity `batch_id`; a set of instances sharing assessment context. Confirmed read data: Project relation, Material classification, component type, label, Scene, Pathway, EvidenceStatus, ReviewStatus, attention/reason. Quantity derives from instances or is validated denormalized data. W01/W02/D01 resolve the same record.
- **VerificationItem:** identity `verification_id`; relates to `batch_id`; includes source-provided field, question/rationale, VerificationType, VerificationStatus, optional `focus_key`. `discovered_at/source` remain draft/fixture semantics. W02-A count, W02-B row, and D01 consume the same items.
- **EvidenceAsset:** evidence associated through Batch detail; supports galleries/360 projections. Current counts/images/inventories are fixtures; full production fields and child-viewer model are not closed.
- **HumanVerifiedFact:** human-confirmed fact at ComponentInstance level; feeds domain assessment refresh. Only three current field examples are confirmed. Saving must not create frontend-owned EvidenceStatus truth.
- **ReferenceSource:** real case, method, guideline, technical reference, or precedent. May project into D01; real sources must not be fabricated. Detail/drawer is deferred.
- **LocalOpportunity:** real regional repair/refurbishment/fabrication/maker/reuse/recycling opportunity. Names/counts/statuses are fixtures; detail is deferred.

### Frozen enums

```text
Pathway
KEEP_IN_PLACE
DIRECT_REUSE
REFURBISH
REPURPOSE
MATERIAL_RECOVERY
DISPOSAL

EvidenceStatus
supported
conditional
insufficient_evidence
not_applicable

ReviewStatus
unreviewed
in_review
reviewed

VerificationStatus
unverified
unable_to_verify
verified
not_applicable

VerificationType
onsite_observation
document_check
specialist_review

SceneIngestionStatus
waiting
receiving
received
ingestion_error
```

`UNKNOWN`/`INSUFFICIENT_EVIDENCE` is not a Pathway. `unable_to_verify` means `无法现场确认`, not `证据不足`. ReviewStatus values are frozen but transition rules are not.

### Projections, not new entities/enums

- Attention boolean/reason is a domain/backend projection; frontend does not score it.
- W01 four coarse buckets are not a frozen Pathway mapping.
- Material grouping is a presentation/classification dimension, not authorization for a new production Material entity.
- Page read models/accordion groups are UI projections, never independent truth.

---

## 7. D — Derived Data / Selector Inventory

No visible aggregate may remain an independent page constant when canonical data can derive it.

### Core and Creation selectors

| Value | Derivation/source | Consumers |
|---|---|---|
| Scene count | count Scenes for Project | C02, C03, W02-A |
| received/receiving count | Scene count by ingestion status | C02 |
| Component count | count ComponentInstances in formally defined scope | C03, W01 |
| AssessmentBatch count | count Project AssessmentBatches | C03, W02-A |
| active VerificationItem count | count items in domain active-status set | C03, W02-B |
| Batch quantity | related ComponentInstance count or validated denormalized value | W01, W02, D01 |

Prototype candidate active statuses are `unverified` and `unable_to_verify`; backend/domain authority may revise this.

### W02-A

- `评估分组`: all project AssessmentBatches.
- `已审查`: batches where `review_status == reviewed`.
- `需关注`: batches where `attention == true`.
- `场景`: canonical Project Scene count; do not merely count scenes referenced by sample batches unless scope is formally changed.
- row `待核实 X项`: active VerificationItems for that `batch_id`.
- Material count: visible batches in the Material projection.
- result/footer count: rows after current filters/search/summary.
- Attention Rail: attention batches after current W02-A filters.

The cached v2.4 `unresolved_verification_count` is prototype debt, not editable truth.

### W02-B

- `待核实事项`: active VerificationItem count in applicable task context.
- `涉及评估分组`: distinct `batch_id` count among active items.
- `现场观察 / 文件核对 / 专业复核`: active item counts by VerificationType.
- per-Material pending count: active visible items in the Material.
- per-Material affected batches: distinct Batch IDs among those items.
- zero-pending coverage and Attention Rail: derived from canonical coverage/task projection.

Whether Summary responds to Status filter is unresolved. The prototype keeps Summary on active tasks while applying non-status filters/search; preserve this behind a replaceable selector boundary, not as hidden final semantics.

### W01, D01, and C03 special cases

- W01 total components derives from ComponentInstances; hotspot quantities derive from the target Batch instances; task rows derive from contracted VerificationItems/targets.
- W01 four-bucket counts, group rows, and Regeneration Potential are **blocked selectors** until their semantics are closed.
- D01 derives Material/type Batch counts, Batch instance count, EvidenceAsset count, verified-instance progress, per-confirmed-field progress, and Batch pending items.
- ReferenceSource/LocalOpportunity result counts derive only after their scopes are contracted.
- D01 local `all instances + no variance → supported` is prototype behavior, not frontend ownership of EvidenceStatus.
- C03 `评估草案 1份` has no canonical entity/count contract; do not hardcode it or reinterpret it as Batch count.

---

## 8. E — Fixture Classification

### 1. System-authoritative

- C01 → C02 → C03 → W01 flow; W01/W02 primary navigation; W02 dual tabs; D01 shared drill-down.
- Page responsibilities, information hierarchy, formal interactions, navigation/return behavior.
- W01 modes/controls/hotspots/filmstrip/cards and non-clickable Potential card.
- W02-A four-card summary, filters, Material Sections, columns, pending drill-down, Attention Rail.
- W02-B five-card summary, filters, one global header, Material accordion, item rows, statuses/actions, Attention Rail.
- D01 tree depth, per-instance verification, information order, source-aware return.
- Formal labels, visual tokens, typography/icon rules, desktop composition, and state scaffolding requirement.

### 2. Formal product/data contract

- canonical entities/IDs: `project_id`, `scene_id`, `batch_id`, `verification_id`;
- one graph shared by all pages;
- frozen enums and AssessmentBatch/ComponentInstance/VerificationItem units;
- Material-first organization;
- W02 pending/active/affected/type counts derived from VerificationItems;
- separate EvidenceStatus and ReviewStatus; consumed Attention projection; no aggregate confidence;
- real/cached-real Reference Sources, never invented real sources.

### 3. Replaceable fixture/demo content

- Project name/region/copy, dates, C01 option values, all current headline numbers and entity inventories;
- Scene/Batch/VerificationItem/evidence/reference/local content and Scene-to-Batch assignments;
- hotspot positions, names, quantities, thumbnails, gradients, attention ranks/reasons;
- `discovered_at/source`, D01 counts `12` references/`3` opportunities, evidence counts;
- C03 `1份`, C02 1.2s simulation, D01 save/toast timing, hash navigation and confirm dialogs;
- W02-A page size 7 and all sample images.

### 4. Known prototype data debt

1. C03 says 6 groups, W02 has 12 AssessmentBatches, D01 tree has 25.
2. C03/W01 say 41 components, W02 quantities total 27, D01 instance quantities total 40.
3. W02-A cached pending counts total 16 across 8 batches; W02-B has 7 active items across 5 batches.
4. Several per-Batch W02-A pending counts lack matching W02-B active items.
5. Identical Batch IDs have conflicting Scenes: W02 uses Scenes 2–5 while D01 hardcodes many to Scene01/屋顶花园.
6. W02 has per-Batch Pathway/EvidenceStatus; D01 formally assesses only `wood_fence_a` and defaults others to `主路径待确认`.
7. W02 stores EvidenceStatus while D01 locally calculates conditional/supported: two truths.
8. W01 hotspot identity is a display string and only `木质围栏` opens D01; production requires `batch_id`.
9. W01 group rows total 24 while headline is 41, with undefined projection scope.
10. `12/18/7/4 = 41` is arithmetically consistent but lacks a six-Pathway mapping.
11. Regeneration Potential 30 happens to equal 12+18; that coincidence is not an algorithm.
12. W02-B includes fields absent from D01’s three confirmed fields.
13. Project/Scene labels are duplicated across page-local arrays/markup.
14. Formatted dates do not distinguish assessment/update/review/discovery timestamps.

Do not select, average, or invent totals. The data document mentions a provisional demo headline of 5 Scenes, 41 ComponentInstances, 12 AssessmentBatches, and 7 active VerificationItems, but explicitly leaves the 41-to-12 allocation and task distribution unapproved.

---

## 9. F — State Inventory

| View | Default | Loading / Error | Empty / Filtered Empty | Local and return state |
|---|---|---|---|---|
| C01 | Project form | option/context loading; option/create failure | blank form; no filtered state | field draft, validation, selects, counts; persistence policy unresolved |
| C02 | connected ingestion + Scenes | connection/receiving; page error and `ingestion_error` | no Scenes; no filtered state | rename draft; canonical Scene state; back/forward |
| C03 | completed summary | processing scaffold; processing/read error | no usable/processed Scenes; no filtered state | no interaction inferred from decorative chevrons; back/enter |
| W01 | Regeneration mode + selected Scene | Project/viewer/media/read-model loading/error | no Scenes, no hotspots/tasks, media fallback; no filtered state | Scene, mode, zoom, context switcher; restore viewer after D01 |
| W02-A | all batches | 4 summary/table/rail skeletons; shared reload error | no Batches; filtered message + clear all filters | summary, 4 filters, search, page, scroll; restore after D01 |
| W02-B | active tasks, default expansion | 5 summary/toolbar/table/section/rail skeletons; shared error | no tasks; filtered message + clear and reset expansion | 4 filters, stable search/caret, expanded/collapsed Material, scroll |
| D01 | resolved Batch detail | Batch/media loading; save in progress; load/not-found/save errors | empty evidence/tasks/references/opportunities as section projections; no formal filtered state | tree, Batch, Instance, field drafts, note, dirty/saving, added evidence, focus; source-aware Back |

W02-A empty copy is `没有符合当前筛选条件的评估分组`; W02-B is `没有符合当前筛选条件的待核实事项`. Both provide `清除筛选`. D01’s final dirty-navigation UX must replace prototype `window.confirm` while still protecting unsaved work. State visuals not expanded in v2.4 may follow the accepted system without changing product meaning.

---

## 10. G — Unresolved Product Questions: STOP, Do Not Decide in Coding

Typed interfaces, adapter seams, unsupported states, or inert placeholders are allowed. Hidden product decisions are not.

### W01

1. Mapping, if any, between `保留 / 复用 / 待确认 / 回收` and six Pathways.
2. `构件分组` scope: current-Scene component types, whole Project, AssessmentBatches, or highlights.
3. Regeneration Potential source/derivation.

### Creation and processing

4. Production sources for C01 Region, Project Type, and Project Stage.
5. Real SDK/backend completion signal and C03 processing-state contract beyond generic scaffolding.
6. Source/meaning of C03 `评估草案` count, if retained.

### Canonical dataset/scope

7. Approved unified seed replacing the contradictory fixture universes.
8. ComponentInstance allocation to AssessmentBatches and Scenes.
9. Whether every in-scope instance is batched; otherwise formal unbatched/excluded semantics.
10. Whether active VerificationStatus is permanently `{unverified, unable_to_verify}` or backend-supplied.

### Status ownership/lifecycle

11. Actions/authority causing `unreviewed → in_review → reviewed`; no editor or automatic transition may be added.
12. Domain/backend EvidenceStatus calculation/persistence after Human Verification; no frontend parallel truth.
13. Attention projection source; no frontend scoring model.

### D01/data fields

14. Full VerificationItem field inventory, options, validation, and mapping beyond three confirmed fields.
15. Whether future fields are schema-driven, fixed inventory, or other workflows.
16. Production fields/ownership for EvidenceAsset and HumanVerifiedFact persistence.
17. Timestamp meanings for assessment/update/review/discovery instead of formatted fixtures.

### W02

18. Whether W02-B Summary is overall active context or follows Status-filtered results.
19. Production `discovered_source` taxonomy.
20. Long-term W02-A grouping/pagination strategy; page size 7 is not a contract.

### Deferred child layers

21. 360 Evidence Viewer.
22. Pathway Detail.
23. Reference Source Detail / Drawer.
24. Local Opportunity Detail.

Each child layer still needs Purpose, Entry, Exit/Back, Page/Route/Drawer/Modal boundary, independent URL need, read model, Loading/Empty/Error, interactions, and permissions. Until then preserve only affordances and typed navigation/interface placeholders.

---

## 11. Phase 1 Recommended Implementation Order

### 1. Canonical domain contract

Create TypeScript definitions for confirmed entities, IDs, frozen enums, and navigation context. Keep unresolved value domains adapter-supplied. Add runtime fixture/invariant checks for duplicate IDs, broken relations, Scene mismatches, and count drift.

### 2. Data adapter boundary

Define one UI-facing interface with fixture and future API implementations. Pages must not own data truth. Do not relocate `W02_BATCHES`, `D01_BATCH_FIXTURE`, `w01Groups`, and C03 constants as though they form one dataset.

### 3. One approved canonical fixture dataset

Populate one Project only when relationships are coherent and explicitly demo data. Before approval it is safe to define schema/builders, empty/loading/error fixtures, referential validation, and fixture-source notes.

Do not choose 6/12/25 batches by fiat, invent 41 instance allocations, keep 16 pending beside 7 tasks, guess Scene remapping, or manufacture W01 formulas. The provisional 5/41/12/7 headline requires explicit allocation approval.

### 4. Selectors and page read models

Implement/test Project Scene/component/batch counts; Batch quantity; reviewed/attention counts; Batch/project active VerificationItems; pending/affected/type counts; W02-A/W02-B/D01 read models. Add cross-page invariant tests.

### 5. Route and navigation-context skeleton

Represent C01/C02/C03/W01/W02/D01 without elevating chosen path strings to Product Authority. Keep W02 tabs internal. Resolve D01 by `batch_id` with source/focus/return context. Child targets remain typed placeholders.

### 6. Shared visual foundations and shells

Implement tokens, typography, icons, status systems, media fallback, Creation/Workspace shells, Project switcher, state patterns, and return-state infrastructure.

### 7. Page reconstruction

```text
C01 → C02 → C03 → W01 shell → W02-A → W02-B → D01
```

All consume selectors/read models, never page-local aggregates.

### 8. Acceptance/invariant verification

- One Project and consistent Scene names across pages.
- One Batch truth for Material/type/Scene/quantity/Pathway/EvidenceStatus.
- W02-A pending equals active items for each Batch.
- W02-B enters D01 for the same Batch/focus.
- C03/W01 totals equal the canonical graph.
- Filters change projections, not domain data.
- D01 Back restores actual source context.
- Fixture images/dates can change without identity changes.

---

## 12. Safe Now vs Interface Placeholders

### Safe now

- framework setup after explicit Phase 1 start;
- confirmed entity types/enums, adapter interfaces, invariant validation, frozen selectors;
- loading/error/empty architecture, shared shells/components, statuses/icons;
- C01/C02/C03 structure; W01 contracted shell/interactions; W02-A/B; D01 hierarchy and three confirmed fields;
- D01 return-state infrastructure and automated selector/navigation/invariant tests.

### Placeholder/interface only

- W01 buckets, group projection, and Potential value;
- C01 production option providers;
- ReviewStatus-changing actions and EvidenceStatus recalculation;
- unconfirmed D01 fields/options;
- W02-B Summary scope, production discovery-source typing, final pagination;
- all four deferred child layers;
- fully populated demo data until relationships are approved.

A placeholder is an explicit typed boundary, unsupported/coming-later state, or preserved inert affordance—not a hidden workflow or fabricated model.

---

## 13. Recommended First Implementation Task

Create the framework-neutral TypeScript domain contract and invariant test specification for canonical IDs, confirmed entities, frozen enums, relationships, and D01 navigation context—without page components or imported prototype fixture arrays. Follow with the fixture/API adapter interface and selector tests. Populate the demo dataset only after contradictory allocations are resolved or approved.

---

## GO / STOP Decision

### Coding-ready — GO

The **MAIN FRAMEWORK is ready for coding**: canonical types/adapters/selectors, shells, C01/C02/C03, W01 contracted shell, W02-A/B, D01 main page/confirmed verification, shared components, navigation context, state scaffolding, tests, and implementation-level technical choices.

### Fully data-ready — STOP / not yet

The project is **not fully data-ready**. Prototype inventories/assignments conflict, and the canonical seed’s ComponentInstance/AssessmentBatch/VerificationItem relationships are not closed. Real binding also awaits option sources, lifecycle/ownership contracts, full D01 fields, and several selector semantics. Do not copy one page’s fixtures or invent missing records.

### Deferred product closure — STOP at boundary

W01 bucket mapping/group projection/Potential, C01 option sources, ReviewStatus lifecycle, EvidenceStatus ownership, D01 full field contract, W02-B Summary behavior, final production pagination/source/timestamp contracts, and all four child layers remain Product work.

**Final decision:** GO for the main framework and data architecture; STOP on invented data reconciliation, unresolved semantics, and deferred child-layer implementation.
