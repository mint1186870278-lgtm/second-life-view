# Current Open Questions Before Real Data Binding

These do not block main-shell/component coding, but they block final real-data semantics.

## 1. W01 four-bucket summary

Current UI uses:

```text
保留 / 复用 / 待确认 / 回收
```

Formal pathways are:

```text
KEEP_IN_PLACE
DIRECT_REUSE
REFURBISH
REPURPOSE
MATERIAL_RECOVERY
DISPOSAL
```

No mapping is frozen yet.

## 2. W01 构件分组 projection

Need to define whether it is:

```text
current Scene component-type summary
project component-type summary
AssessmentBatch summary
highlight-only projection
```

## 3. Regeneration Potential

Need formal derivation/source. Current sample value is not an algorithm contract.

## 4. C01 select data sources

Region / Project Type / Project Stage sample options are not frozen production enums.

## 5. ReviewStatus lifecycle

Need authoritative transition rules for:

```text
unreviewed → in_review → reviewed
```

## 6. EvidenceStatus ownership

Frontend must not maintain an independent second truth. Final domain/backend derivation needs to be aligned.

## 7. D01 Verification field coverage

Currently confirmed UI fields are limited. W02-B contains additional fixture VerificationItems. Do not create new formal D01 fields/options without Product Contract.

## 8. W02-B Summary scope

Need final decision whether Summary cards reflect:

```text
overall active Verification task context
```

or:

```text
current Status-filtered result
```

## 9. Deferred child layers

360 Evidence / Pathway Detail / Reference Detail / Local Opportunity Detail require tomorrow's IA closure.
