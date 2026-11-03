# Independent R5 concurrency review

**ACCEPT_WITH_CONDITIONS** as a prospective coverage design. V2 retains real OS concurrency and adds publication liveness to invalid-history rejection. Full CR2 execution and implementation acceptance remain separate gates.

The original source puts Session construction before ready markers (`tests/corrections/process_worker.py:12,26`). A rejected constructor cannot reach that rendezvous. The original stale-object test constructs its stale Session after corruption (`test_interactions.py:4`), so it cannot exercise a stale finalizer. Moving the rendezvous before admission and creating the stale object before mutation are sound harness corrections; historical timeouts/errors remain failures.

| Required property | Proposed coverage and independent assessment |
|---|---|
| Eight original reviewer race IDs | R5:7 retains journal-corrupt and missing-receipt IDs 0–3 and exact four-process V0, V1, V2, V3 vectors. No sequential substitute is allowed. |
| Exact corruption | R5:9 keeps complete `{"extra":true}` plus newline. A malformed line is additive, not equivalent replacement evidence. |
| Missing receipt/journal | Registered absence and moved bytes retained. Original missing-journal TWO-process test remains, with additional FOUR-process stress and all vectors. |
| Valid publication | Every invalid vector has a valid four-process partial-history counterpart; at least one verified terminal must publish, exactly one normal prepared/final hash, all successful observers share it. All-rejected valid histories fail. |
| Original two-process ordering | R5:19 expressly requires A and B admitted before release/claim, in addition to four-process stress. This reaches publication contention instead of only post-completion admission. |
| Stale finalizers | Pre-admit stale object, corrupt, reject fresh admission, then stale finish; keep independent valid immutable-result stale return. |
| Existing completion | Concurrent two-call and separate four-process stress preserve original result/candidate/handle/hash; later corruption rejects current verification but preserves suspect bytes. |
| Owner/fence | Live owner cannot be stolen; death/relinquish permits newer fence; stale token cannot publish. |
| Interruption/recovery | Actual killed child after reservation/header or raw response; charged attempt, unknown cost and no replay/reset/imagined candidate. |
| Crash windows | Prepared-before-link, after-link, raw-before-settlement and numeric-before-inspection stay explicit, with compatible recovery and preserved pending/prepared/final/raw evidence. |
| Last publication seam | All original 13 read-pin/seam controls remain, using native Windows sharing/hard-link semantics; mutable bytes must be denied or changed snapshot rejected before link. |
| Evidence and every worker | PIDs, bounded joins, exit code, typed outcome, dispatch observation, RESULT/prepared paths and bytes must all be checked. Diagnostic uniqueness cannot substitute for normal exclusivity. |

The relevant retained source includes test_f01.py:24 (two independent finalizers), :27 (owner death), :35 (after-link crash), :19 (stale fence), and thirteen distinct controls in test_publication_guard.py:25–66. R5:30 keeps these unchanged as prerequisites, rather than declaring them superseded by constructor rejection.

Fresh reviewer controls execute twenty actual process schedules: four V0 two-process cases and sixteen four-process cases spanning V0–V3 for valid, exact-extra corruption, missing receipt and missing journal. All 72 race children are joined with exit zero. Valid histories actually publish and independently verify one C0/attempt/handle with one prepared normal anchor; followers return allowed outcomes. Invalid histories return explicit noncertifying outcomes, retain inputs and publish no new normal final/prepared record. A separate actual child is killed at a durable-header window and recovers with one charged reservation, null cost, no FINAL and no replay. These are 73 observed child processes. They do not execute the full promised crash/fence/read-pin or explicit both-admitted ordering matrix. Prior reviewer crash/pin observations remain historical evidence, not freshly rerun here. The initial 39 and additive manifests are retained separately, so later coverage is not misrepresented as present in the first run.

Conditions for later acceptance: execute every promised exact vector/fault/cardinality pair, retain explicit both-admitted two-process ordering, execute the named crash/fence/read-pin controls, compare all output and moved-evidence bytes/handles, and fail on missing workers/unexpected exceptions/timeouts. Record separate pass/fail/error counts and do not count original failures as new passes. The present probes establish operational valid publication for bounded current paths; they do not establish exhaustive schedules, network filesystems or hardware power-loss guarantees.

The 31-row coverage matrix preserves each original scientific property with these conditions and the R1/R3/R4 dependencies. No old test is deleted, skipped or rewritten. R5's design acceptance cannot override the overall REVISE decision.
