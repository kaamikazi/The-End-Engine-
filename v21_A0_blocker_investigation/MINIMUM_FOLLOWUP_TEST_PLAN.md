# Minimum targeted follow-up plan — separate approval required

**No test below is executed or authorized by this investigation.** A0-18 remains ERROR, current strong feasibility remains blocked, and the four saved recursive negatives remain unchanged PASS with their six original scoring fields. Do not rerun all twenty simply to obtain a green aggregate. Approve an exact A0-only collector/detection diff and a new evidence checkpoint first.

## Fixed bounds and preservation common to all families

Use only new synthetic copies of the same manifest-verified public/mock inputs, unchanged checkpoint source and no reservation/dispatch/provider calls. Use an isolated new output directory and save executable hashes before execution. Record all worker PIDs/start identities, readiness/phase markers, operation outcomes, exits, joins, cleanup and monotonic durations. Keep current raw runs/fixtures/scoring byte-identical; do not overwrite any prior result.

Proposed short test bounds: readiness <=5s; each experimental guard wait <=0.5s (within the frozen <=5s ceiling), at most2 acquisitions; expected post-readiness completion <=3s; failed-child termination/join cleanup <=3s; overall worker watchdog <=12s including readiness/cleanup. Record the timed-wait threshold, watchdog trigger and cleanup completion separately. These are proposed test limits, not measured performance or changes to production/contract bounds. Unexpected timeout/deadlock, wrong sentinel, missing child or cleanup failure is FAIL; do not retrospectively extend a bound after seeing a failure. No polling evidence until it becomes valid.

## FT-COLLECT: isolate collector behavior

Proposed code scope: add an A0-only case18 collection helper in probe_workers.py and change only its call sites in test_lock_domain_feasibility.py case18, preserving all original assertions/intents and leaving the default unrelated snapshot behavior unchanged unless separately reviewed. The helper must not execute a writer or change input files.

| Subcase | Positive / negative expected outcome | Evidence and stop condition |
|---|---|---|
| C1 unlocked baseline | Full complete membership and actual readable data hashes agree with a known synthetic baseline; no input/owner changes | Persist initial inventory, per-entry IDs/types/read outcomes and manifest. Any omitted name or invented hash fails |
| C2 exact held controls plus new pending member | With actual test G/L1/L2 held, retain known control paths/owned-descriptor identities and explicit content-read limitations; still enumerate and preserve budget.json.pending. No uncaught Errno13 abort. No A/S or complete byte snapshot claimed from unreadable inputs | Preserve path/errno/winerror for each refused read, child/phase receipts before delta analysis, main ledger hashes and pending raw bytes. Unknown member loss or false completeness fails |
| C3 unreadable required data / unknown lock-shaped name | A required-data read refusal remains an explicit failed/incomplete observation. A new unexpected .lock filename is retained and cannot inherit trusted-control status by suffix | Use a separately approved test-held incompatible handle in new scratch, not ACL edits on historical data. Unexpected blanket catch-to-success, erased error or dropped .lock member fails |
| C4 collector exception cleanup | Inject a collector-side failure after resources are acquired; all its own handles/guards release and a fresh supervised child reacquires before parent exit | Check joins/exit/read-write eligibility after release. Any leaked/borrowed owner descriptor, forced success or watchdog miss fails and stops |

The objective is faithful evidence collection. A negative read can be correctly recorded while the candidate is still not a valid strong capture. The corrected control's verdict must distinguish those facts; no production source change is needed to investigate them.

## FT-SOURCE: narrow unchanged-verifier regression

Because the proposed helper is test-only, source checks remain unchanged. Before the deliberate real-writer fault, repeat only the necessary nonowning positive/negative subset against new synthetic copies:

- Positive: a valid existing synthetic source passes unchanged _verify_completed under the intended nonrecursive guard/data-pin arrangement; input bytes, owner/fence and original ledger rows do not change, no constructor or dispatch/reserve is invoked by the reader.
- Negative1: exact complete-extra-record corruption produces genuine RecoveryIntegrityHold, is not called a successful capture, and preserves source/evidence bytes.
- Negative2: removed bound reservation leaves standalone graph status and completed-source status separately recorded. The completed source must reject the changed report with ArtifactIntegrity(PROPOSED_PROVENANCE_REPORT_NOT_CURRENT); it is not reserialized/repaired to pass.

Record all run-data opens as pinned data or explicitly declared preexisting operational controls, exact core exception/cause, and per-phase source hashes. Any new source incompatibility, new write, broad exception substitution or failure to reach the intended boundary fails. The four prior recursive controls are not changed or weakened; no new recursive production arrangement is proposed.

## FT-WRITER: exact exclusion/detection pair

| Subcase | Positive / negative expected outcome | Evidence and stop condition |
|---|---|---|
| W1 explicitly cooperating registered caller | Admission attempt is observed before refusal/block, all admitted writers drain through final logging before candidate L1/L2, and no writer touches the relevant namespace during that declared two-participant test window | Actual phase/PID/exit/guard evidence; a worker merely not scheduled is insufficient. This remains a bounded simulation, not coverage of all40 classes |
| W2 exact unenrolled real Ledger.register | Repeat the same unchanged source registration on a new scratch ledger while proposed guards/data pins are held. Collector must record the real pending write and denied target replace separately, retain the foreign registration bytes and unchanged original attempt count, and reject/abort strong authority | Use the actual API/canonical pending envelope, not an easier arbitrary orphan-file substitute. A correct negative detection can satisfy the control expectation while overall strong feasibility remains unsupported. The material writer stop rule applies immediately; no subsequent probes or retries in that epoch |

Order nondestructive collector/source checks before W2, with that planned fault last. Do not use scheduling order to suppress an unexpected earlier failure. If any participating writer escapes its proved domain, stop there regardless of a green collector assertion. Do not register/settle an actual new model attempt; the test concerns run registration only and is guarded against reserve/dispatch/network calls.

## What these minimal families cannot discharge

A collector correction or a two-worker positive does not prove full production enrollment, all forty producer classes, external/admin absence, authenticated recording origin, complete accounting, provider compatibility or universal concurrency correctness. Broader all-writer proof is a separately reviewed coordination/deployment undertaking. If that proof needs protected source/API/native changes, request exact scope before implementation. Do not authorize A1 or declare A0 acceptance from these proposed tests.
