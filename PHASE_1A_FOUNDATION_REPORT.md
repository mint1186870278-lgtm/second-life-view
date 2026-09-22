# Second Life View — Phase 1A Foundation Report

**Date:** 2026-09-22  
**Scope:** Application initialization and canonical TypeScript domain/data foundation only.

## Outcome

Phase 1A is complete. The repository is now a runnable Vite + React + TypeScript application with React Router, Lucide React, and Vitest. All product pages remain plain development placeholders; no prototype page UI was translated or reconstructed.

## Technical Setup

- npm package management with committed `package-lock.json`
- Vite application and production build
- React with TypeScript strict mode
- React Router using implementation-only paths
- Lucide React installed for the later fixed icon system
- Vitest using the Node environment for framework-neutral data tests
- local Git repository initialized; no remote configured and no commit created
- no Tailwind, UI framework, component library, lint stack, or backend connection

Literal route paths are documented in `src/app/routes.ts` as implementation choices, not Product Authority. W02-A and W02-B intentionally share one W02 route and remain future internal views. Deferred child layers have typed destination identifiers only and no routes.

## Created Structure

```text
src/
  app/
    App.tsx
    PlaceholderPage.tsx
    app.css
    routes.ts
  data/
    ProjectDataRepository.ts
    FixtureProjectDataRepository.ts
  domain/
    entities.ts
    enums.ts
    graph.ts
    ids.ts
  fixtures/
    builders.ts
    emptyProjectGraph.ts
  navigation/
    context.ts
  selectors/
    projectSelectors.ts
    w02Selectors.ts
  test/
    testGraph.ts
  validation/
    types.ts
    validateProjectGraph.ts
```

Tests live beside the data, selector, and validation modules.

## Domain Contracts

Implemented canonical contracts for:

- Project
- Scene
- ComponentInstance
- AssessmentBatch
- VerificationItem
- EvidenceAsset
- HumanVerifiedFact
- ReferenceSource
- LocalOpportunity

Canonical string ID aliases cover Project, Scene, Component/ComponentInstance, AssessmentBatch, VerificationItem, EvidenceAsset, HumanVerifiedFact, ReferenceSource, and LocalOpportunity.

Runtime value arrays and TypeScript unions implement the frozen enums:

- Pathway
- EvidenceStatus
- ReviewStatus
- VerificationStatus
- VerificationType
- SceneIngestionStatus

Region, Project Type, Project Stage, and `discovered_source` remain strings. No W01 coarse-bucket enum was created. Attention is stored only as a consumed boolean/reason projection.

Optional `denormalized_quantity` and `denormalized_pending_verification_count` fields exist only as transport-cache boundaries. Validation rejects them when they disagree with canonical entities.

## Navigation Context

The D01 navigation contract is a discriminated union for:

- `view`
- `review-draft`
- `review-verification`

It preserves the confirmed W01 viewer/Scene state and W02-A/W02-B filter, search, tab, page-boundary, expanded-Material, focus, and scroll state without defining URL strings as Product Authority. W02-A page is optional because the final pagination strategy is unresolved.

## Data Adapter Design

`ProjectDataRepository` is the frontend-facing async read boundary. It exposes Project, Scene, ComponentInstance, AssessmentBatch, VerificationItem, EvidenceAsset, HumanVerifiedFact, ReferenceSource, and LocalOpportunity reads.

`FixtureProjectDataRepository` implements this interface in memory and validates the full graph at construction. A future API adapter can implement the same interface without changing page components.

No prototype-local `W02_BATCHES`, `D01_BATCH_FIXTURE`, W01 groups, C03 counts, or other page fixture arrays were imported.

## Fixture Strategy

`emptyProjectGraph` contains one explicitly non-authoritative placeholder Project and empty entity collections. It is sufficient to test the architecture without choosing a 6/12/25 Batch inventory or manufacturing ComponentInstance allocation.

The small populated graph in `src/test/testGraph.ts` exists only for automated architecture tests and is explicitly marked as not being the product demo dataset.

## Selectors and Read Models

Implemented:

- Project Scene count
- Project ComponentInstance count
- Project AssessmentBatch count
- reviewed Batch count
- attention Batch count
- Batch quantity from ComponentInstances
- active VerificationItems for a Batch
- active VerificationItems for a Project
- Batch pending VerificationItem count
- distinct affected Batch count
- VerificationType counts
- W02-A summary read model
- W02-B summary read model
- W02-B Material grouping projection, including optional zero-pending coverage groups

The current active-status candidate is isolated in `ACTIVE_VERIFICATION_STATUSES` and `isActiveVerificationItem`.

W02-B summary scope is an explicit required selector option:

- `active-task-context`
- `status-filtered-result`

This is a technical seam only; it deliberately does not close the outstanding Product decision.

Not implemented: W01 four buckets, W01 group projection, Regeneration Potential, ReviewStatus transitions, EvidenceStatus recalculation, or any attention scoring.

## Invariant Validation

Validation returns structured issues, and `assertValidProjectGraph` throws `DomainInvariantError`. It never repairs data.

Enforced checks include:

- duplicate IDs in every canonical collection;
- missing Project references;
- missing Scene references;
- missing Batch references, including VerificationItems;
- missing ComponentInstance and VerificationItem references from related data;
- cross-Project relationship mismatch;
- ComponentInstance Scene mismatch with its canonical Batch Scene;
- denormalized Batch quantity drift;
- denormalized pending VerificationItem count drift;
- invalid runtime Pathway, EvidenceStatus, ReviewStatus, VerificationStatus, VerificationType, and SceneIngestionStatus values.

## Automated Tests

Three test files provide 17 tests covering:

- all required count/selectors and W02 read models;
- active-status policy isolation;
- explicit W02-B scope behavior;
- Material grouping and zero-pending coverage;
- valid graph acceptance;
- all requested contradiction/error categories;
- fail-loud adapter construction;
- repository reads through the adapter interface.

Verification result:

```text
npm test
3 test files passed
17 tests passed

npm run build
TypeScript project build passed
Vite production build passed
```

No lint configuration was added, so there was no lint command to run.

## Preserved STOP Boundaries

Phase 1A deliberately leaves unresolved:

- the canonical demo inventory and 6/12/25 Batch contradiction;
- allocation of 41 ComponentInstances to Batches/Scenes;
- 16 cached pending counts versus 7 active task rows;
- W01 four-bucket semantics and six-Pathway mapping;
- W01 group projection and Regeneration Potential;
- C01 production option sources;
- ReviewStatus lifecycle;
- EvidenceStatus ownership/recalculation;
- full D01 verification field schema/options;
- final W02-B Summary-versus-Status behavior;
- production `discovered_source` taxonomy;
- final W02-A pagination strategy;
- 360 Evidence Viewer, Pathway Detail, Reference Source Detail/Drawer, and Local Opportunity Detail.

## Recommended Phase 1B

Phase 1B should establish the shared visual foundations and shell infrastructure while continuing to consume only the adapter/selectors:

1. design tokens, typography, icon maps, status primitives, and state surfaces;
2. Creation Shell and Workspace Shell;
3. Project Context Switcher and navigation/return-state storage;
4. loading/error/empty scaffolding;
5. C01 structure using adapter-supplied option interfaces, followed by C02/C03;
6. no populated canonical demo dataset until its allocations are explicitly approved.

Page reconstruction should still not copy the prototype’s DOM/state architecture.
