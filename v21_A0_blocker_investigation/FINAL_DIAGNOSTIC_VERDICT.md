# Final diagnostic verdict

**A0_STRONG_PROFILE_NOT_SUPPORTED**

The available raw evidence and exact source identify both causes. The tested candidate domain did not enroll/exclude an actual Ledger.register caller, which wrote a pending envelope before its replace of the pinned ledger was denied. Separately, the parent test snapshot tried to read operational controls while its byte locks were held, producing the retained Errno13 ERROR after successful child collection.

The first issue is missing writer-domain coverage, not evidence of an incorrect participating lock order or a universally impossible quiescence model. The second is a local A0 evidence-collector defect, not automatically a production-source or verifier defect. The parent trace has no filename; .a0-L2.lock is the first-file reconstruction from exact sorted source/membership, not a new syscall observation.

An A0-local collector proposal can improve evidence collection and preserve a detected dangerous operation, but cannot itself make the unenrolled API participate or prove complete producer quiescence. A broader operational domain or separately scoped coordination design is needed before strong A/S claims. Under current evidence, only justified per-source I facts or unsupported X outcomes are available; observed candidate-window interference invalidates stronger claims. No numeric completeness, complete cost, selected certified output or inferred provider call is granted.

The original A0 verdict remains A0_FEASIBILITY_BLOCKED. Attempt_002 remains19PASS/1ERROR; attempt_001 remains10PASS/1FAIL/9NOT_EXECUTED. The four saved recursive negatives retain bounded-negative PASS and their six required scoring fields, without safe-reentrancy claims. Neither an old ERROR nor an expected failed lock operation is silently recast as a successful capture.

This investigation performed only raw/source/AST/hash/Git-state analysis and remediation planning. It did not import or execute runtime/A0 code, rerun A0-18, launch concurrency controls, change implementation/scaffolding/scoring, or perform provider/inference/benchmark activity. PRESERVATION_REPORT.json records the before/after byte and Git comparisons after analysis completes.

Minimum proposed follow-up: a separately approved A0-only collector/detection correction with targeted tests and strict evidence/bounds, plus independent review of whether actual all-writer operational exclusion can be established. If protected coordination changes are needed, the exact conditional source scope is listed separately. Correcting a report is not authority to modify F01 or Engine.

The R1/R3 contract remains frozen. No A0 feasibility acceptance, A1 enrollment, production implementation, test migration, commit/push/merge/rebase/tag/release or human scientific approval is granted. This verdict does not assert protected source changes are the only possible remedy; it states that the tested strong strategy is not supported by available evidence.
