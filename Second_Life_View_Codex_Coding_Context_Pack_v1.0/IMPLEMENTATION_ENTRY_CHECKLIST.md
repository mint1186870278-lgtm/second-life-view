# Implementation Entry Checklist

Before page reconstruction starts, confirm:

- [ ] canonical `Project` type exists
- [ ] canonical `Scene` type exists
- [ ] canonical `ComponentInstance` type exists
- [ ] canonical `AssessmentBatch` type exists
- [ ] canonical `VerificationItem` type exists
- [ ] one shared fixture/API adapter is used by all pages
- [ ] no page-local aggregate counts are treated as domain truth
- [ ] selectors derive Scene / Component / Batch / Verification counts
- [ ] `batch_id` is the common identity across W01 / W02 / D01
- [ ] `verification_id` identifies W02-B tasks
- [ ] navigation context distinguishes W01 / review-draft / review-verification
- [ ] unresolved Product gaps are documented rather than guessed
- [ ] deferred child layers remain placeholders only

Then implement visual/page layers against v2.4.
