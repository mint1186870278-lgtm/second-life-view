# Second Life View — Phase 1B.5 Architecture Remediation Report

**Date:** 2026-09-23  
**Scope:** Focused remediation of the five Phase 1B P1 architecture findings, including the C01 draft hydration race discovered during recovery. No Phase 1C/W01 product content was implemented.

## Outcome

All five original P1 findings are resolved. Canonical Project/session data and the editable C01 draft now have separate owners, mutations have an application-service boundary, Workspace navigation is reusable, and shared Select is independent of Creation demo configuration.

The recovery-only C01 hydration race is also resolved. Tests, production build, and live route smoke checks pass. Phase 1C is **GO**, subject to the preserved P2 and product-authority boundaries below.

## Original P1 Findings and Final Status

| Original P1 finding | Final status | Resolution |
|---|---|---|
| CreationFlowProvider was globally scoped and owned concrete fixture defaults | **Complete** | App composition now injects repository, project ID, and mutation service into a neutral ProjectSessionProvider. CreationFlowProvider wraps only C01–C03 routes. |
| Loaded Project/Scene data and editable draft/demo projections were ambiguous | **Complete** | ProjectSession owns canonical Project and collection snapshots. CreationFlowProvider owns only the distinct ProjectFormDraft used by C01. Workspace consumes ProjectSession directly. |
| Write/mutation behavior lacked an application command boundary | **Complete** | ProjectMutationService defines the Scene rename command contract. ProjectSession calls the injected service and updates its session snapshot from the service result. |
| WorkspaceSidebar hardcoded W01 as active and was not navigation-ready | **Complete** | Workspace navigation uses a typed destination model, caller-provided active destination, and a navigation callback. The shell is reusable without importing Creation state. |
| Shared FormControls depended on the Creation demo option type | **Complete** | Select owns/accepts a neutral structural option shape. Demo option values remain in the Creation configuration layer. |

## Project and Session Ownership

ProjectSessionProvider is the neutral application-level owner of:

- the canonical Project returned by ProjectDataRepository;
- canonical session snapshots for Scenes, ComponentInstances, AssessmentBatches, and VerificationItems;
- loading, error, and reload lifecycle;
- mutation orchestration through ProjectMutationService.

Repository, current project ID, and mutation-service selection occur explicitly in App composition. ProjectSession does not own Creation form fields, Workspace viewer state, W02 filters, or D01 editing state.

No duplicate canonical Project/session truth was introduced. The session snapshot remains the single application-level canonical read projection.

## CreationFlowProvider Responsibility

CreationFlowProvider is scoped to the C01–C03 route branch and owns only Creation-specific, cross-step local state. Its current state is ProjectFormDraft, an explicitly separate editable form type rather than a Project domain entity.

It does not own the canonical Project, repository loading, canonical collections, Scene mutations, Workspace state, persistence, autosave, or discard behavior.

## C01 Hydration-Race Fix

The previous provider initialized an empty draft and later overwrote it in an effect when the canonical Project loaded. That timing allowed C01 to render an empty draft and allowed an edit or validation attempt to race with late hydration.

The provider now uses an explicit one-time initialization guard:

- the first available canonical Project is synchronously projected into ProjectFormDraft while the draft is untouched;
- the first user patch creates the editable draft snapshot from that initialized value;
- once edited, subsequent ProjectSession updates cannot replace the draft;
- there is no hydration effect and therefore no late draft write.

This preserves the canonical Project/Creation draft separation and adds no autosave, persistence, discard semantics, global state, or duplicate Project truth.

Tests prove that C01 starts with canonical Project values, edited draft data remains separate and survives a later session reload, clearing a required field remains cleared after async work, invalid current draft state cannot navigate, and valid current draft state does navigate.

## Mutation Service Boundary

ProjectMutationService is a framework-neutral application contract. C02 requests Scene rename through ProjectSession; ProjectSession awaits the injected service and then updates the Scene snapshot from the returned result. The page does not mutate fixture data or the session collection directly.

The current LocalProjectMutationService is intentionally local/demo infrastructure. Future API mutation adapters can replace it at App composition without redesigning C02.

## Workspace Navigation Architecture

Workspace navigation is represented by typed WORKSPACE_NAVIGATION_ITEMS. WorkspaceSidebar receives the active destination and delegates destination handling through onNavigate. W01 and W02 remain distinct top-level destinations, while no Phase 1C/W01 real content or W02/D01 behavior was added.

No Workspace consumer imports CreationFlowProvider or useCreationFlow.

## Shared Select Decoupling

The shared Select control accepts caller-provided neutral options, including disabled state. It has no dependency on demoProjectOptionSource or other Creation configuration. C01 remains responsible for selecting its explicitly demo-scoped option source.

## Test Infrastructure Fix

The unsupported jest-dom matchers were replaced with readable native DOM assertions:

- textContent for rendered text;
- getAttribute/hasAttribute for aria-current;
- HTMLOptionElement.disabled for option state.

No jest-dom dependency or additional test setup stack was added. TypeScript and Vitest use only the currently installed testing dependencies.

## Architecture Verification

The post-fix import and boundary audit confirms:

- no Workspace consumer imports CreationFlowProvider or useCreationFlow;
- ProjectSession remains neutral and application-level;
- CreationFlowProvider owns Creation-only draft state;
- Scene rename goes through ProjectMutationService;
- shared Select is demo-config agnostic;
- no duplicate Project/session truth exists;
- pages do not import fixture graph data or concrete fixture repositories; the only direct page demo import is the explicitly allowed C01 option configuration;
- selectors remain framework-neutral and do not import React.

## Verification Results

### Automated tests

`npm test` — **PASS**

- 9 test files passed;
- 34 tests passed;
- 0 failures.

### Production build

`npm run build` — **PASS**

- TypeScript project build passed without suppression;
- Vite production bundle completed successfully;
- 1,930 modules transformed.

### Runtime QA

The Vite app was run locally and inspected with headless Chrome at the 1586 × 992 desktop reference viewport. A 3-second browser virtual-time budget allowed repository-backed React rendering to settle.

- C01 rendered the canonical HSBC MKK draft values and stable form UI;
- C02 rendered the ingestion page and canonical Scene names;
- C03 rendered selector-derived metrics, including the expected 4 and 2 counts;
- W01 rendered the Workspace shell, canonical Project context, and placeholder;
- all four direct routes rendered expected content;
- no page-console uncaught/error messages were detected.

The passing jsdom interaction tests additionally verify C01 invalid/valid navigation, C02 back/forward navigation, Scene rename through the mutation service, C03-to-W01 navigation, and route rendering. No W01 real content was exercised or introduced.

## Remaining P2 and Deferred Risks

The following remain intentionally deferred and do not block Phase 1C:

1. C02 still performs its small visible received/total count derivation locally; extract a read model only if ingestion rules expand.
2. C01 directly selects demoProjectOptionSource; inject an option source only when a production implementation exists.
3. FixtureMetadata remains optional in the formal ProjectGraph type; move it to an adapter wrapper when API DTOs arrive.
4. Repeated CSS colors/borders are not fully tokenized.
5. Some Creation tests intentionally assert current coherent fixture totals; future features should add purpose-built edge-case graphs as well.
6. ProjectSession orchestrates multiple repository reads; a coherent snapshot/query contract may be useful when a real API introduces version-skew concerns.
7. ProjectSession does not yet guard overlapping reloads by request generation. Add stale-request protection when project switching or concurrent retries become real behavior.
8. C01 persistence/create-update contracts, D01 HumanVerifiedFact save behavior, and their dirty/error semantics remain undefined and must not be inferred.

Preserved STOP boundaries include unresolved W01 bucket mapping, group projection, Regeneration Potential, status ownership/lifecycle, full D01 fields, W02-B Summary policy, canonical demo reconciliation, and deferred child layers.

## Phase 1C Decision

**GO for Phase 1C.**

The five P1 architecture findings and the recovery hydration race are resolved, with passing tests, build, and runtime smoke checks. Phase 1C may implement the authorized W01 scope while keeping W01 feature state outside ProjectSession and CreationFlowProvider and preserving all unresolved product-authority STOP boundaries.

No commit or remote Git operation was performed.
