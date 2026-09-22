# Deferred Product Closure｜Do Not Invent During Coding

These entry points exist in the current main framework, but their final product boundary is intentionally deferred:

```text
1. 360 Evidence Viewer
2. Pathway Detail
3. Reference Source Detail / Drawer
4. Local Opportunity Detail
```

For each, tomorrow's closure should define:

```text
Purpose
Entry
Exit / Back
Page vs Route vs Drawer vs Modal
Independent URL requirement
Data read model
Loading
Empty
Error
Core interaction
Permission boundary if applicable
```

Until then Codex may:

```text
create a typed navigation target
create a placeholder route/interface if architecturally necessary
preserve current click affordance
```

Codex must not:

```text
invent the page hierarchy
invent new user workflows
invent production data fields/options
invent new permissions
invent new state transitions
```
