# Opt-in shared-Ledger coordination — author implementation report

**LEDGER_GUARD_SLICE_READY_FOR_INDEPENDENT_REVIEW**

Implemented only in the new isolated worktree at the explicitly approved source commit. Owner approved this production slice in chat on 2026-10-24 (Asia/Dhaka); earlier feasibility approvals were not reused. No source outside Ledger.__init__/lock/_write and one new stdlib coordination module changed. New tests/reproductions are isolated in tests_coordination_v1. Branch `codex/v21-ledger-guard-slice`, base HEAD `783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e`, no new commit or publication. Managed worktree creation failed ownership checks; per-command safe.directory Git fallback created the authorized worktree without a global exception.

## Result and exact gain

Explicit Coordinator configuration now guards every enrolled Ledger transaction before ordinary L3, including constructor data/L3-control initialization, register/reserve/finish, pending creation/flush/fsync/replace and exception release. Existing parent directory is mandatory; no opt-in pre-guard mkdir. Actual excluded enrolled children could not create pending evidence, while actual unenrolled default clients could still create it. That is the coverage boundary, not all-writer exclusion.

Internal logical outer reentry is checked across attached objects and threads; native L3 and D are unchanged and not assumed recursive. Private _write validates ownership only. Opt-in preserves stale pending via exclusive create; default legacy wb behavior stays. Public budget/request/accounting/candidate/source certification semantics are untouched. Old/default clients and nonowning facades without explicit coordination remain unenrolled. This intentional current opt-in contract does not implement earlier ideas of auto-discovery.

Final targeted suite: **41 PASS,0 FAIL,0 ERROR,0 SKIP**, exit0. Separate final-source native errno reproduction PASS; source error is PermissionError/errno13/winerror=null behind L2_CONTENTION_DEADLINE, not assumed WinError5. The unenrolled pinned-main replacement separately recorded WinError5. Actual Windows/NTFS processes, threads, killed holders, pending crash, logical reentry, recursive/order rejection, write/fsync/replace errors, stale evidence, identity/case/hardlinks and original source owner/fence preservation were exercised. Source-core fixture is explicitly rebased synthetic data and performs no provider/reservation call.

Initial author runs remain: attempt00136PASS/4ERROR (test collector re-read held control through second handle); attempt00240PASS; attempt00340PASS/1FAIL (raw trailing-name validation happened after Windows normalization); final attempt00441PASS. Exact prior sources/raw failures are preserved. The collector correction retained all bytes/control checks and used the owning descriptor plus post-release comparison; it did not catch-to-PASS. The path fix remained inside the one approved module. No actual introduced deadlock, out-of-scope writer edit or legacy regression was found. Historical N12 remains FAIL and was not edited or rerun.

## Original regressions on exact final revision

| Suite | Actual tests | Pass | Fail | Error |
|---|---:|---:|---:|---:|
| engine | 303 | 303 | 0 | 0 |
| lab | 58 | 58 | 0 | 0 |
| isolation | 85 | 85 | 0 | 0 |
| native | 53 | 53 | 0 | 0 |
| r3 | 244 | 222 | 16 | 6 |

Total **743 original tests:721 PASS,16 FAIL,6 ERROR**. Baseline and final outcomes, exception types/messages and subtests match exactly; **zero new regressions**. The r3 failures/errors are the actual unmodified baseline, not accepted as green or declared obsolete. Each suite's real exit/stdout/stderr and full unittest tracebacks are retained. Separate baseline/intermediate/final runs are not combined into one test count. Network attempts were zero under active no-network guards. Original unit tests may execute canned/mock paths; no live model, provider request or benchmark ran.

## Source/evidence identity and preservation

Current candidate digest: `e1f62915f944854ef340db8f43a6454ceb077c6a5c61b888e46eeea59182eecd` over sorted compact JSON raw-file SHA/byte map for changed/new implementation/tests. Exact files/diff are in `_control/SCOPED_SOURCE_REVIEW.json` and `_control/EXACT.patch`. The clean initial4181-file snapshot leaves4180 tracked files byte-identical, with only Ledger changed in its three allowed symbols. Engine0.3.5.2, Harness, frozen evaluator, A/B/C, inputs/prompts/settings/ceilings and old F01/F02/F03/F04 source fingerprints are unchanged. Existing manifests/history are retained; a new candidate receipt does not overwrite old source hashes.

Before/after preservation verified **52917 prior files**, all old worktree states and all preexisting local branch refs (excluding only the newly authorized branch) unchanged. The original dirty correction worktree and both WIP branches are preserved. No reset/clean/rebase/force push, main edit, local commit, push, merge, tag or release.

All13 requested deliverables are present with raw commands/PIDs/exits/phase markers and source snapshots. Code review and fresh independent acceptance are pending; author tests are not external human approval. No AUTHORITATIVE_CONSISTENT_SNAPSHOT, STABLE_BUT_INCOMPLETE_OBSERVATION, COMPLETE_RUN_ACCOUNTING, FULL_WRITER_ENROLLMENT or SCIENTIFIC_EXPERIMENT_READINESS is awarded. Other writer namespaces, native witnesses, R1 observer, R3 adapter and complete cost validation remain unimplemented. See REMAINING_WRITER_GAPS.md and INDEPENDENT_REVIEW_REQUEST.md.
