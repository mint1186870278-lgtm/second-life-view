# Second Life View — Phase 1B Architecture Review

**Review date:** 2026-09-23  
**Baseline:** 7e41f3ac8bedb98d477cf159aa29ce79b50a6dec  
**Scope:** Read-only architecture review of the uncommitted Phase 1B implementation.

## Executive Verdict

The frontend is structurally healthy enough to scale into W01, W02-A/W02-B, and D01. There are no P0 architectural blockers, no circular source dependencies, no duplicated canonical entity definitions, and no page-owned fixture graphs.

The strongest boundaries are the framework-neutral domain, repository contract, invariant validation, pure selectors/read models, typed D01 navigation context, and small shared visual primitives.

The main risk is at the application composition/state boundary. CreationFlowProvider is cohesive for the completed Creation Flow, but it is mounted around every route and directly defaults to the fixture repository and fixture project ID. It also exposes both the loaded Project and an editable draft, while W01 currently reads the draft as project identity. If future Workspace state is added to this provider, it will become a God Provider and create competing sources of truth.

Phase 1C may start, but its first implementation slice should establish a neutral Project/session data boundary and keep W01 feature state outside CreationFlowProvider. This is a focused remediation, not a state-library rewrite.

## 1. Current Architecture Map

### Module map

| Layer | Current modules | Responsibility |
|---|---|---|
| Domain | src/domain | Canonical entities, IDs, frozen enums, ProjectGraph |
| Repository contract | src/data/ProjectDataRepository.ts | Framework-neutral read interface |
| Repository implementation/composition | FixtureProjectDataRepository.ts, creationRepository.ts | Validated in-memory fixture reads and current demo assembly |
| Fixtures | src/fixtures | Empty fixture builders and coherent Phase 1B demo graph |
| Validation | src/validation | Runtime graph invariants and fail-loud fixture validation |
| Selectors/read models | src/selectors | Project counts, active verification policy, Creation summary, W02 summaries/grouping |
| Navigation | src/navigation, src/app/routes.ts | Typed D01 source/return context and implementation-only paths |
| Application state | CreationFlowContext.tsx | Repository loading, Creation draft, current graph snapshot, demo rename projection |
| Route composition | App.tsx | Provider and route assembly |
| Shared UI | src/ui | Shells, controls, status presentation, state surfaces, guidance, media fallback |
| Creation pages | src/pages/C01, C02, C03 | Page orchestration and page-local interaction state |
| Workspace | WorkspaceShell.tsx, W01 placeholder | Global header/sidebar/context shell and inert destination |
| Styles | src/styles | Tokens, base, shared components, Creation, Workspace |
| Tests | colocated tests plus src/test | Domain graph, validation, repository, selectors, UI status, routing and Creation behavior |

### Actual dependency direction

Healthy paths:

    domain
      ↑ repository contract
      ↑ selectors and validation
      ↑ application provider
      ↑ pages

    fixtures → domain
    concrete fixture repository → repository contract + validation + fixture graph
    pages → provider + selectors + navigation + shared UI
    App composition → pages + provider

Shared UI is mostly React/Lucide-only. StatusPill intentionally depends on the formal SceneIngestionStatus domain type, which is appropriate for a domain-aware reusable status primitive.

### Dependencies pointing in the wrong direction

1. CreationFlowContext imports creationProjectRepository from the data barrel and CREATION_DEMO_PROJECT_ID from fixtures. The provider accepts injected alternatives, but its default composition points an application-state module directly at demo infrastructure.
2. FormControls imports ProjectOption from src/config. A general shared Select primitive therefore depends on Creation-specific demo configuration.
3. ProjectGraph in the domain layer includes optional FixtureMetadata. This is explicit and harmless today, but fixture provenance is an infrastructure concern embedded in a formal graph contract.

No domain module imports React, router, CSS, fixtures, pages, or repositories. No selector imports React. No page imports the concrete fixture graph or FixtureProjectDataRepository.

## 2. Coupling Findings

### P1 — Global provider scope and concrete fixture defaults

**Module:** src/app/CreationFlowContext.tsx and src/app/App.tsx  
**Issue:** CreationFlowProvider wraps C01, C02, C03, W01, W02, D01, and 404. It directly defaults to a concrete fixture repository singleton and fixture project ID.  
**Why it matters:** Real W01/W02/D01 code would either inherit Creation-specific state and loading behavior or continue expanding this provider. API replacement is possible, but composition is hidden inside the provider instead of being explicit at the app boundary.  
**Required boundary:** Keep a neutral current-Project/read-snapshot provider or query hook separate from Creation draft state. Inject repository/project selection at composition. Do not add viewer, review filters, or D01 form state to CreationFlowProvider.

### P1 — Loaded Project versus editable draft ambiguity

**Module:** CreationFlowContext.tsx, C01ProjectSetupPage.tsx, C02SceneIngestionPage.tsx, W01WorkspacePlaceholderPage.tsx  
**Issue:** The provider owns both project and draft. C01 edits draft without updating project, while C02 and W01 use draft.name as the displayed current Project identity. The repository remains unchanged.  
**Why it matters:** This is the beginning of two Project truths: loaded canonical data and an unsaved Creation projection. W01/W02/D01 need a clear current Project identity.  
**Required boundary:** Keep draft explicitly Creation-only. Workspace pages should consume a committed/session Project projection, not the C01 draft, until a create/update contract exists.

### P1 — Mutation behavior has no command/service seam

**Module:** ProjectDataRepository.ts and CreationFlowContext.tsx  
**Issue:** The repository is read-only, while renameScene mutates the provider’s copied Scene collection. C01 creation and future D01 fact saving will also be commands, not reads.  
**Why it matters:** Swapping to a real API would leave reads replaceable but require mutation behavior to be redesigned inside the provider/pages. D01 dirty/save/error behavior should not be added as another ad hoc context mutation.  
**Required boundary:** Introduce feature-level command interfaces or application services only when each mutation contract is implemented. Preserve the existing read repository; do not guess backend endpoints.

### P1 — Workspace shell encodes W01 as permanently active

**Module:** src/ui/WorkspaceShell.tsx  
**Issue:** WorkspaceSidebar hardcodes two non-interactive divs and always marks 再生视图 active.  
**Why it matters:** W02 and D01 will need the same shell with different active/return behavior. Copying the shell would cause drift; adding route-specific conditionals internally would over-couple it.  
**Required boundary:** Before W02, make shell navigation accept the active product destination and navigation elements/callbacks while retaining W02-A/B as one top-level W02 destination.

### P1 — Shared Select depends on Creation demo configuration

**Module:** src/ui/FormControls.tsx → src/config/demoProjectOptions.ts  
**Issue:** The reusable Select component imports ProjectOption from a demo option-source module.  
**Why it matters:** W02 filters and D01 controls should reuse visual controls without importing C01 demo semantics. Visual reuse must not carry feature-specific business types.  
**Required boundary:** Define a neutral option shape with the control or accept structural/generic options; keep demoProjectOptionSource in the Creation feature/config layer.

### P2 — C02 derives visible counts in the page

**Module:** src/pages/C02SceneIngestionPage.tsx  
**Issue:** receivedCount and total Scene count are computed with page-local filter/length expressions. They still derive from the canonical collection and are not hardcoded.  
**Why it matters:** This is not a second source of truth, but allowing page-local aggregate conventions to spread will make W01/W02 cross-page consistency harder to audit.  
**Recommendation:** Add a small C02 ingestion read model if the page gains more status counts or backend ingestion rules.

### P2 — Page imports the demo option source directly

**Module:** C01ProjectSetupPage.tsx  
**Issue:** C01 consumes the correct abstraction shape but selects the demo implementation through a module import.  
**Why it matters:** Production option replacement would require changing page composition, though not its domain types.  
**Recommendation:** Inject the ProjectOptionSource at a Creation composition boundary when a production source exists. Do not add an abstraction layer before there is a second implementation.

### P2 — Fixture metadata lives in the formal graph type

**Module:** src/domain/graph.ts  
**Issue:** FixtureMetadata is defined in the domain module and optionally attached to ProjectGraph.  
**Why it matters:** A future API graph should not need fixture provenance.  
**Recommendation:** Move provenance to a fixture wrapper or adapter configuration when API DTOs are introduced.

## 3. Cohesion Review

### CreationFlowProvider

The provider is not currently a God Provider. Its responsibilities share one lifecycle:

- load one Project and the collections required by C01–C03;
- retain a Creation draft across Creation routes;
- expose loading/error/retry;
- retain deterministic demo Scene rename state across C02/C03.

That is cohesive for Phase 1B. The warning sign is scope, not current field count. It wraps Workspace routes, and W01 already consumes it. The boundary that prevents future expansion should be:

- Project/session data: neutral read snapshot scoped to the current Project;
- Creation Flow: C01 draft and temporary Creation interactions;
- W01: viewer/Scene/mode/zoom/focus state scoped to W01 and its D01 return context;
- W02: tab/filter/search/accordion/page state scoped to W02;
- D01: selected instance and dirty verification form scoped to D01.

No Redux, Zustand, or other global state library is justified.

### Other cohesion assessments

- **Selectors:** Cohesive and framework-neutral. projectSelectors owns shared domain derivations; creationSelectors and w02Selectors own page/read-model projections.
- **Fixture option source:** Cohesive as config, with the exception of its type leaking into FormControls.
- **Shared UI:** Components are small and responsibility-focused. There are no giant configuration objects or boolean-prop matrices.
- **Workspace shell:** Visually cohesive, but navigation behavior needs parameterization before reuse.
- **System states:** LoadingState, ErrorState, and EmptyState are appropriately presentational.
- **Styles:** Separation by tokens/base/components/Creation/Workspace is coherent and leaves room for review.css and detail.css.

## 4. Single Source of Truth Review

### PASS

- Project, Scene, ComponentInstance, AssessmentBatch, and VerificationItem have one canonical type definition in src/domain.
- The coherent fixture graph is validated at repository construction.
- C03 totals flow through buildCreationAnalysisSummary and existing selectors.
- C01 demo options remain strings outside formal domain enums.
- IDs, not display labels, establish entity relationships.
- W01 placeholder contains no hidden counts, Pathway projections, hotspots, or potential calculation.
- W02 selector summaries derive from canonical batches/scenes/items and preserve the explicit Summary policy seam.

### Emerging dual-truth risks

1. project versus draft: both are exposed as Project-like truth, and Workspace currently displays draft.name.
2. repository Scenes versus provider Scenes: renameScene modifies the client snapshot without an explicit demo/optimistic command type.

These are controlled Phase 1B projections, not data corruption. They must be made explicit before Workspace and backend mutation behavior depend on them.

## 5. Data Adapter and API Replaceability

### What remains unchanged with a real read adapter

- Domain entity types and frozen enums;
- ProjectDataRepository consumers;
- core selectors and W02 read models;
- C02/C03 presentation components;
- status primitives;
- routing and typed D01 return context;
- invariant tests for fixture data.

### Correct isolation

- Pages do not import creationDemoGraph or FixtureProjectDataRepository.
- The concrete fixture adapter implements the same async repository interface expected by the provider.
- Selector inputs are plain collections, not repository or React objects.
- Runtime fixture validation fails loudly rather than repairing contradictions.

### Leakage and missing seams

- Concrete fixture selection is a provider default rather than explicit app composition.
- The provider orchestrates five separate reads. This is workable, but a future API may need a coherent snapshot/query service to prevent cross-request version skew and repeated orchestration.
- Creation/update/rename/save commands are intentionally absent, so read replacement is easier than write replacement.
- C01 option retrieval is configuration-based, not repository-based; this is correct until a production option contract exists.

**Conclusion:** A real read API would not require major page rewrites. App composition/provider wiring would change. Real write behavior would require a new command/application-service seam, especially for C01, C02 rename, and D01.

## 6. State Ownership Review

| Category | Current owner | Assessment |
|---|---|---|
| Domain/server data | CreationFlowProvider after repository load | Acceptable snapshot; should become neutral Project/session ownership for Workspace |
| Derived/read-model data | Pure selectors; C03 computes its summary | Healthy |
| Application/session state | load status, error, reload version, current projectId prop | Cohesive |
| Page-local form state | C01 validation errors; SceneCard edit buffer/mode | Healthy |
| Cross-page Creation draft | CreationFlowProvider | Appropriate for C01→C03; must not become Workspace canonical Project |
| Navigation state | React Router; typed D01 navigation contracts | Good foundation; typed contract not yet wired to runtime storage/navigation |
| Demo-only state | default repository/ID and Scene rename projection | Explicit in documentation but insufficiently explicit in provider API naming/types |

### Forward state placement

- W01 viewer mode, selected Scene, zoom, opaque viewer state, and focus belong in a W01 feature state boundary. Only the return snapshot crosses into D01.
- W02 tabs, filters, search, page boundary, and expanded Material belong in W02 route state, a W02 feature provider, or URL/session state chosen during implementation.
- D01 dirty values, selected ComponentInstance, save/error state, and unsaved-change protection belong inside D01.
- Shared current Project data may be read from a neutral Project/session provider; feature interaction state should not be placed there.

## 7. Component Architecture

### PASS — healthy reuse

- Button, form controls, state surfaces, media fallback, guidance, brand, and status pill are product primitives rather than page clones.
- CreationShell and WorkspaceShell represent distinct product shells.
- C03 AnalysisStage/MetricCard and C02 SceneCard remain page-local, which avoids premature generalization.
- No business component attempts to unify W02-A and W02-B.

### Under-sharing risk

- WorkspaceSidebar must become reusable across W01/W02/D01 instead of being copied.
- Future Pathway/Evidence/Review/Verification status primitives should extend the current status family, not create page-local badge systems.

### Over-abstraction risk

There is no current over-abstraction. Preserve the rule:

> Visual reuse does not imply business-semantic reuse.

W02-A should remain AssessmentBatch-centric and W02-B VerificationItem-centric. They may share tabs, filter controls, table geometry, Material headers, pills, and empty states without sharing one row/business component.

## 8. CSS and Design-System Architecture

### PASS

- The five stylesheets have clear ownership and deterministic import order.
- No !important rules are present.
- Shared selectors use stable class names rather than page IDs or DOM-depth selectors.
- Creation-specific geometry is not embedded in shared component CSS.
- Workspace can grow via separate W01/review/detail style layers without rewriting Creation styles.
- Core frame, semantic colors, radii, and surfaces have tokens.

### P2 — incomplete token adoption

Repeated border and text colors such as #dfe4ea, #667085, #718097, and #f0f2f4 remain in components.css, creation.css, and workspace.css despite close token equivalents.

This is maintainability debt, not a scalability blocker. Consolidate recurring semantic values when W01/W02 introduces the next shared status/table/filter vocabulary; do not replace every one-off geometry value with a token.

### Layout assumptions

The deliberate 1050px minimum and 1586×992 frame match current authority. Workspace columns are centralized in workspace.css. W02/D01 should extend the Workspace body rather than override app-frame or global body rules.

## 9. Test Architecture

### Current protection is useful

- Invariant tests detect duplicate IDs, broken references, Scene/Batch mismatch, denormalized drift, invalid enums, and fail-loud behavior.
- Repository tests verify the abstraction and validation gate.
- Selector tests cover shared counts, active-status policy, W02 summary policy seam, and Material grouping.
- Creation tests cover validation, navigation, rename, ingestion presentation, derived metrics, and route rendering.
- Tests avoid pixel snapshots.

### Gaps to add during W01/W02/D01

1. Provider tests with an injected fake repository for loading, failure, retry, project change, and stale-request protection.
2. Contract tests shared by fixture and future API repository implementations.
3. W01 selector/projection tests proving every hotspot uses batch_id and Raw/Regeneration visibility does not mutate domain data.
4. D01 navigation round-trip tests for all three sources and return-state restoration.
5. W02-A filter/read-model tests and W02-B filter/accordion tests kept separate by business entity.
6. D01 per-ComponentInstance draft, dirty, save-success, save-failure, and unsaved-navigation tests.
7. Loading/error/empty/filtered-empty route tests, especially repository failure and no-Scene states.

### P2 — fixture-value assertions

The Creation selector and route tests assert current demo totals 4/4/2/2. These protect the current coherent fixture but should not become the only proof of selector correctness. Add small purpose-built graphs for edge cases as each feature grows.

## 10. W01 / W02 / D01 Scale Assessment

### W01

The repository supplies Scenes, Batches, instances, and VerificationItems; canonical IDs and navigation types are ready. W01 can add pure read models and a feature-local viewer state boundary without circular dependencies. Do not put viewer state into CreationFlowProvider. Hotspot components should receive batch_id directly.

### W02-A

W02-A summary selectors already exist. Filters, Material sections, and optional page boundary can remain feature-local projections. The Workspace shell needs active-navigation input first. W02-A should own AssessmentBatch row semantics.

### W02-B

W02-B summary scope is already explicit, and Material grouping consumes VerificationItems without React. Filters and expanded Material can remain W02-local. W02-B should own VerificationItem row semantics and share only visual table/filter primitives with W02-A.

### D01

The discriminated navigation context covers view, review-draft, and review-verification sources. Repository reads exist for evidence, human facts, references, and opportunities. D01 can remain an independent drill-down, but it needs a command seam for HumanVerifiedFact writes and page-local dirty state. It must not import W01/W02 page state directly; return snapshots should travel through the navigation contract.

### Circular dependency risk

There is no current circular dependency. The future risk arises only if:

- Workspace pages import each other to restore state;
- shared UI imports page read models;
- CreationFlowProvider becomes the owner of viewer, review, and D01 form state.

The recommended feature-state boundaries prevent all three.

## 11. Findings Summary

### P0 — 0

No architectural blocker prevents Phase 1C.

### P1 — 5

1. CreationFlowProvider is globally scoped and owns concrete fixture defaults.
2. Loaded Project/Scene data and editable draft/demo projections are not sharply distinguished.
3. Write/mutation behavior lacks an application command boundary.
4. WorkspaceSidebar hardcodes W01 active state and is not navigation-ready.
5. Shared FormControls depends on the Creation demo option type.

### P2 — 6

1. C02 performs small visible-count derivations locally.
2. C01 selects the demo option source directly.
3. FixtureMetadata resides in the domain graph contract.
4. CSS token adoption is incomplete for repeated semantic colors/borders.
5. Creation tests rely partly on current fixture totals.
6. Multi-read repository orchestration may later need a coherent Project snapshot/query boundary.

### PASS — boundaries to preserve

- One canonical domain model and ID vocabulary;
- React-free domain, selectors, validation, repository contracts, and navigation context;
- validated fixture adapter behind an async interface;
- no page imports of fixture graph or concrete repository class;
- selector-derived C03 and W02 summaries;
- explicit active VerificationItem and W02 Summary policy boundaries;
- independent W02-A and W02-B semantics;
- small shared components with no giant configurable abstraction;
- layered CSS with no !important usage;
- strong invariant, selector, repository, routing, and Creation behavior tests;
- W01 placeholder contains no invented product logic.

## 12. Recommended Remediation Sequence

1. **First Phase 1C task:** move repository/project-ID selection to explicit app composition and establish a neutral Project/session read boundary. Keep Creation draft state scoped to Creation routes.
2. Clarify in types/state which values are canonical loaded data, unsaved Creation draft, and demo-only rename projection.
3. Make WorkspaceShell accept active destination and navigation elements/callbacks before implementing W02.
4. Remove the shared Select dependency on demoProjectOptions.
5. Add command/application-service interfaces only when C01 persistence, Scene rename persistence, or D01 saving is implemented.
6. Add W01 feature-local viewer state and selectors; do not expand the Project/session or Creation providers.
7. Address P2 items incrementally with the feature that needs them.

## GO / STOP Decision

**GO for Phase 1C:** yes. The architecture is healthy and has no P0 blockers.

**Remediation first:** yes, but narrowly. The first Phase 1C slice should correct provider/composition scope and Project truth boundaries before real W01 state is added. This should be a small refactor with behavior-preserving tests, not a redesign or state-library migration.

**STOP remains in force:** unresolved W01 bucket mapping, group projection, Regeneration Potential, status ownership/lifecycle, full D01 fields, W02-B Summary policy, canonical demo reconciliation, and deferred child layers must remain explicit boundaries.
