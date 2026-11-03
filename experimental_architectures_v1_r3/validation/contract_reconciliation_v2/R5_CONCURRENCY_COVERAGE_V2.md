# R5 — mandatory prospective concurrency coverage

Namespace: CR2-v1 (proposed only). Existing tests remain unchanged. A rejected constructor cannot signal a post-admission ready marker; a timeout remains a failure, never a safe-rejection PASS. Put the new rendezvous BEFORE admission without removing synchronization, then collect every actual OS child's PID, exit, typed outcome and independent dispatch observations under bounded joins. Busy/already-completed outcomes are valid only on declared paths; crashes, unjoined workers, missing output or unrelated exceptions fail.

## Original vectors and fault definitions retained

Four-process vectors: V0=(0,0,0,0), V1=(0,.015,.03,.045), V2=(.045,.03,.015,0), V3=(.02,0,.04,.01). Preserve all eight reviewer IDs RACE_journal-corrupt_0..3 and RACE_missing-receipt_0..3 as historical outcomes; their prospective CR2 counterparts retain the exact vector and four OS processes.

- journal-corrupt EXACT mutation: append complete extra JSON record `{"extra":true}` plus newline to settled journal. A malformed BROKEN line is a separate variant, not a substitute.
- missing-receipt: move registered receipt to preserved.response.json; preserve moved bytes and registered absence.
- missing-journal: rename journal to .missing; preserve renamed bytes. Retain original focused TWO-process cardinality plus FOUR-process stress for every vector.
- valid: same partial one-attempt/C0 history, no mutation; pair every invalid vector with a valid four-process publication case. At least one genuine successful verifier/terminal is required. All-rejected valid history fails.

## Coverage obligations and precise ordering

| Scenario | Processes / ordering | Required property |
|---|---|---|
| Corrupt complete-extra journal / malformed-line variant / missing receipt / missing journal | Four workers at pre-admission barrier for all original vectors; focused two-process versions independently retained | Every rejection/diagnostic is explicitly noncertifying; no new RESULT or normal prepared certificate; no replay; ledger, wire, reservation/dispatch/response/settlement anchors and moved evidence unchanged; R1 observations retained at correct tier |
| Valid partial simultaneous finalization | Four workers for V0..V3 plus focused two-process ordering: A admitted, B admitted, release before claim | Eligible worker actually publishes; exactly one prepared normal anchor/final hash; other successful observers same hash; declared RunBusy/FileExistsError allowed; one original attempt/C0/handle, no duplicate dispatch |
| Stale finalizer after corruption | Create stale object before mutation; new admission after mutation; release stale finish after rejection check | Both new admission and stale object reject; cannot create normal BLOCKED certificate; preserves all original evidence |
| Existing valid completion | Two concurrent admission/finish callers, then four-process stress as separate property | Verify old result, refuse new admission or return original through supported finish; never overwrite, identical hash/candidate/handle |
| Existing completion then evidence corruption | Two callers after explicit mutation, stale pre-mutation object retained | Direct completed verifier rejects; old RESULT/prepared bytes unchanged; diagnostic references suspect file and never certified return |
| Live owner and fencing | Two processes, B tries claim while A live; then A relinquishes/owner dies and B claims newer fence; old A attempts finish | No lease theft; stale fencing token rejected; ownership/exclusive mechanisms unchanged |
| Process termination mid-attempt | Kill actual child after durable reservation/header or raw response before settlement; recovery on same run | Kernel lease release; same charged attempt, unknown usage; no replay/reset; no fabricated candidate/FINAL |
| Publication crashes | Exact windows prepared-before-link, after-link, raw-before-settlement, numeric-before-inspection | Preserve pending/prepared/final/raw evidence; compatible recovery only; immutable final and no false success |
| Last validation-to-link mutation | Original13 F01 seam/read-pin controls, actual Windows native semantics | Deny writes or reject changed snapshot before exclusive link; never publish false VERIFIED; valid history positive still publishes |

Every invalid-history control independently inspects RESULT and prepared paths and every child completion tag, not just exception strings. Every valid-history control compares file hashes, original candidate content/output handles, physical reservation count, scoped usage and no-replay. Diagnostic uniqueness does not replace normal publication exclusivity. Never downgrade four-process contention into a single-threaded test; focused two-process schedules prove ordering while four-process schedules stress a different property.

Historical mappings are explicit in FAILURE_CLASSIFICATION_V2.csv and REPLACEMENT_TEST_MATRIX_V2.csv: eight races, missing-journal two-process test and stale-object test are harness incompatibilities. Other original valid race/crash/fence/pin controls are retained unchanged as prerequisites, not superseded. Reviewer62 observations (61 PASS/1 fixture FAIL) and author 37 reexecution are evidence only; they do not install CR2 tests or make original suites green. No exhaustive scheduling, hostile-host, network-filesystem or hardware power-loss guarantee is claimed.
