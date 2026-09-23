# Second Life View — Phase 1C W01 Regeneration View Report

**Date:** 2026-09-23  
**Scope:** Current-authority W01 再生视图 implementation only. W02 and D01 remain placeholders.

## Outcome

W01 is now a real React page that consumes the neutral ProjectSession and canonical repository collections. It supports canonical Scene browsing, site/regeneration modes, isolated viewer zoom, AssessmentBatch hotspots, contextual VerificationItem shortcuts, formal assessment information, an informational Regeneration Potential shell, Scene filmstrip navigation, W02 entry, and typed D01 navigation context.

No W02 or D01 product content, deferred child workflow, global state library, real panorama SDK, or unresolved W01 business algorithm was introduced.

## State Ownership

ProjectSession remains the owner of canonical Project, Scene, ComponentInstance, AssessmentBatch, and VerificationItem snapshots.

W01 owns only route-local interaction state:

- selected canonical scene_id;
- viewer mode: site or regeneration;
- frontend zoom presentation level.

The selected Scene is initialized from the first canonical Project Scene. Scene changes use scene_id and reset only the local zoom level. W01 state is not stored in CreationFlowProvider or ProjectSessionProvider.

## Component Structure

The implementation is split by cohesive W01 responsibilities:

- W01RegenerationViewPage: ProjectSession consumption, local state, route navigation, and read-model composition;
- ViewerModeSwitch: the two formal W01 modes;
- W01SidebarSupplement: canonical component total plus explicitly demo-only unresolved projections;
- SceneViewer: replaceable visual surface and overlay coordination;
- ViewerControls: North indicator and zoom controls;
- HotspotLayer: canonical AssessmentBatch targets;
- ContextTaskCard: VerificationItem shortcuts;
- AssessmentInfoCard: canonical Batch, Pathway, and EvidenceStatus presentation;
- RegenerationPotentialCard: non-clickable demo shell;
- SceneFilmstrip: canonical Scene selection.

WorkspaceShell gained narrow composition slots for a center header control, page action, sidebar supplement, Project context label, and content class. Its navigation model remains shared and business-light.

## Scene and Viewer Architecture

The filmstrip is derived from canonical Scene records and keyed by scene_id. The selected record drives the main viewer, context label, hotspots, tasks, and assessment card.

SceneViewer owns no domain data and can be replaced by a real panorama/SDK implementation later. The current surface uses CSS media fallbacks with preserved crop, aspect, contrast, layering, and transform behavior. Zoom transforms only the scene layer; controls and cards remain stable overlays.

Site mode renders clean Scene media plus the formal controls. It omits hotspots, tasks, assessment information, and Regeneration Potential. Regeneration mode renders the allowed overlays.

No MiniMap, fullscreen control, spherical renderer, SLAM, 3DGS, stitching, or tracking behavior was added.

## W01 Read Model

selectW01SceneReadModel is framework-neutral. It derives:

- canonical Project Scene filmstrip items;
- selected Scene by scene_id;
- Project ComponentInstance count;
- Scene AssessmentBatches through the canonical scene_id relationship;
- Batch quantities from ComponentInstances;
- active VerificationItems per Batch;
- formal Pathway and EvidenceStatus presentation;
- hotspots only when both a canonical Batch and explicit UI placement exist.

A Scene without a placed canonical Batch renders normally with no fabricated hotspot, task, or assessment card data.

## Hotspot Identity Strategy

Each hotspot carries canonical batch_id. Display labels and component names are never used as entity keys or routing conditions.

Only the two AssessmentBatches in the coherent canonical demo graph can appear. Placement coordinates and color emphasis live in w01DemoProjection as UI-only metadata. Clicking a hotspot navigates to the existing D01 route with that canonical batch_id and source=view context.

## Task Shortcut Strategy

Contextual tasks derive from active canonical VerificationItems for the selected Scene's Batches. The current two fixture items use the already-contracted optional focus_key field:

- fixing_method;
- hidden_damage.

A task is actionable only when focus_key exists. Unknown items remain explicitly non-actionable rather than creating a new D01 target or field contract.

## D01 Navigation Context

W01 builds the existing typed D01NavigationContext with:

- source=view;
- canonical batch_id;
- optional confirmed focus_target;
- selected scene_id;
- viewer_mode;
- zoom_level;
- scroll_y.

D01 remains a development placeholder. It displays this context only so route tests and runtime QA can verify the boundary. No D01 assessment, evidence, verification, save, or child-layer behavior was implemented.

## W02 Entry

The header action and Workspace sidebar both navigate to the single existing W02 route. W02 remains the existing placeholder; W02-A/W02-B were not split into product routes and no review logic was added.

## Demo-only Projection Boundaries

w01DemoProjection is explicitly non-authoritative and contains only:

- hotspot x/y placement and visual tone keyed by canonical batch_id;
- the visual four-row coarse summary shell, with neutral em-dash values;
- the visual group-list shell and demo rows;
- a neutral Regeneration Potential placeholder.

The four coarse labels are not domain enums and are not mapped to the six formal Pathways. Group rows drive no business behavior. Regeneration Potential displays no number or formula and is non-clickable. None of these demo projections are used for navigation, canonical filtering, or status derivation.

## States

ProjectSessionGate continues to supply loading and error/retry states. W01 adds a no-Scenes empty state. Scenes without hotspots/tasks retain the viewer and present appropriate empty card behavior. CSS gradients provide the replaceable media fallback.

## Tests

`npm test` — **PASS**

- 11 test files passed;
- 45 tests passed;
- 0 failures.

New coverage verifies:

- W01 renders from ProjectSession without CreationFlowProvider;
- default Scene selection and scene_id-based switching;
- selected Scene viewer/read-model updates;
- site mode hides regeneration-only UI;
- regeneration mode restores allowed UI;
- zoom is isolated presentation state and resets on Scene change;
- hotspot navigation uses canonical batch_id and source=view;
- task navigation carries the confirmed focus_target;
- W02 entry uses the single review route;
- Regeneration Potential is non-clickable;
- Scenes without a placed Batch receive no fake hotspot;
- unresolved demo labels are not formal Pathways.

## Build

`npm run build` — **PASS**

- TypeScript project build passed without suppression;
- Vite production build passed;
- 1,935 modules transformed.

## Runtime and Visual QA

The local Vite app was inspected in headless Chrome at 1586 × 992.

W01 visual inspection confirmed:

- GlobalHeader, mode switch, Project context, and Project Review action alignment;
- accepted 228px Workspace sidebar and dominant viewer proportion;
- viewer controls separated from the zoomed scene layer;
- readable canonical hotspot and overlay hierarchy;
- non-overlapping task, assessment, and Potential cards;
- four canonical Scenes fitting the filmstrip without overflow;
- stable Chinese typography and neutral/yellow visual system;
- no page screenshot used as the application background.

Headless route checks passed for C01, C02, C03, and W01, with zero detected uncaught/page-console errors. Interaction tests cover mode switching, Scene switching, zoom, hotspot/task transitions, and W02 navigation.

Temporary QA screenshots and browser profiles were removed after inspection.

## Known Visual Deviations from v2.4

- Neutral CSS panorama fallbacks replace prototype photography.
- The coherent canonical graph supplies four Scenes and two Batches rather than the prototype's larger sample inventory.
- Only canonical placed Batches render hotspots, so visual density is intentionally lower.
- The four-bucket values are neutral em dashes because their Pathway mapping is unresolved.
- The Potential value is neutral because its numeric derivation is unresolved.
- The group list is visibly labeled as an unresolved demo projection and is not interactive.
- Project Context switching/New Project behavior remains disabled rather than inventing persistence/discard behavior.
- D01 and W02 remain explicit placeholders.

## Preserved STOP Boundaries

Phase 1C does not define:

- a four-bucket-to-six-Pathway mapping;
- W01 group-list semantic scope;
- a Regeneration Potential algorithm;
- new domain enums or status lifecycles;
- EvidenceStatus or ReviewStatus derivation;
- uncontracted D01 fields or focus targets;
- W02 review behavior;
- deferred 360 Evidence, Pathway, Reference Source, or Local Opportunity workflows.

W01 imports neither CreationFlowProvider nor fixture graph modules. Selectors remain React-free. No global/God provider was introduced.

## Recommended Phase 1D

Proceed to the current-authority W02 dual-view Project Review workspace:

- W02-A AssessmentBatch-centric 评估草案;
- W02-B VerificationItem-centric 待核实;
- shared Workspace shell/navigation;
- canonical selectors and typed D01 context;
- no D01 real content until its own authorized phase.

Before real W01 data binding, Product/Data authority must still close the four-bucket mapping, group projection scope, and Regeneration Potential derivation.

No commit or remote Git operation was performed.
