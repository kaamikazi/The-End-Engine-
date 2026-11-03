# Remediation options — proposals only

**Decision: current strong A/S profile is not supported.** The collector cause is sufficiently understood for a local A0 fix proposal, but neither that fix nor a lower-authority label establishes writer exclusion. No remedy is applied here. Do not prefer a local patch merely because its approval is simpler.

## Blocker 1: actual unenrolled Ledger.register mutation

| Option | Concrete proposal and capability | Assessment / scope |
|---|---|---|
| A — A0-local | Improve the test-only domain receipt and collector so this exact unregistered caller/pending write reliably invalidates the candidate and remains visible; separately test a deliberately cooperating registered caller blocked at admission | Feasible detection/reporting work, not a fix for strong exclusion. Changing the result wording, checking only the main ledger hash, filtering pending files or treating the caller as harmless is unacceptable. A local closed-worker simulation cannot establish coverage of every source/API/admin producer |
| B — separately expanded coordination scope | Review actual resource identity and all permitted producers/inner-lock users; either establish an operational admission/drain/exclusion protocol that every supported caller truly uses, or explicitly enroll writer entry boundaries under a compatible shared domain | Possible engineering path, not proven implemented/necessary in its exact form. Touching Ledger.register/reserve/finish/state/init, Gateway/native registration, Session witness hooks or Publication lifecycle requires an exact separate source/synchronization authorization and independent deadlock/F01/F02/API review. Do not add a blanket outer wrapper that recursively reacquires D or L3 |
| C — lower authority | Withhold A/S, full-set graph cardinality, absence/completeness, complete costs and current eligible v2.1 views; retain only justified per-source observations | Supported limit under current evidence/permissions. I can describe strictly parsed recorded identity/registration/usage metadata in a captured file with exact raw hash and origin limitations. X applies when no grounded attempt fact exists; no false zero or fabricated run envelope. U can describe an aborted purported candidate cut after observed interference, without upgrading its lower facts |

An unchanged matching main-ledger hash is not an A proof: the pending envelope is a new relevant member. The child does not have to succeed at os.replace to invalidate membership stability. A caller explicitly outside a cooperating profile is not proof of malicious-host resistance failure, but the operator cannot claim the tested setup covers all supported writers while this real API path bypasses it. A0-17 proves only its two cooperating toy participants.

It remains possible in principle that a rigorously constrained operational profile could prove full quiescence without protected code edits. The evidence does not establish that profile, nor does it prove every such strategy impossible. Therefore the investigation does not choose A0_SCOPE_EXPANSION_REQUIRED as if protected-source edits were the only logically possible remedy. It chooses the narrower evidence-supported A0_STRONG_PROFILE_NOT_SUPPORTED.

## Blocker 2: parent collector Errno13

| Option | Concrete proposal and capability | Assessment / scope |
|---|---|---|
| A — A0-local | Add a case18-specific evidence collector over complete membership, preserve per-entry read outcomes, distinguish declared active controls from required data, retain unknown files, persist pre/post phase records outside the candidate inputs | Directly addresses the demonstrated harness error without changing protected source or any historic assertion. Keep the existing snapshot behavior for unrelated controls unless an exact separate diff justifies otherwise. Historical A0-18 stays ERROR until a new authorized run has its own result |
| B — synchronization/source expansion | Alter production byte locks, F01 pins, native sharing or writer semantics to make blind read_bytes succeed | Not justified by this error. The failing read is in test scaffolding and the same control can be recorded without pretending its bytes were captured. Changing protection to accommodate a collector is not a safe remedy. Any truly necessary native/production change would need its own scope and evidence |
| C — unavailable/lower-authority result | Record unreadable required evidence explicitly and refuse a strong result; preserve readable facts | Safe fallback, not a collector repair or an invented successful complete capture. Known operational-control descriptors do not automatically waive whatever the frozen contract requires for a future production view; unresolved production capture semantics remain a separate engineering gate |

## Required invariant set for any route

Keep all names/types/absences, unknown/temporary/pending members and exact raw bytes where readable. Do not ignore every filename ending .lock. Never replace a failed read with a fabricated hash, an empty set or known zero. Ordinary storage/programming errors remain real errors; only expected, precisely identified test outcomes may satisfy their registered negative expectation.

Preserve L1→outer L2→ordinary L3 ordering, no L3 across reacquiring verifier calls, <=2 acquisition attempts, <=5s per guard wait, no retry that erases an observed in-epoch violation. Owner leases/fences, exclusive publication, current F02 BLOCKED rejection, F03/F04, existing APIs and the frozen R1/R3 contract remain unchanged. No current failure is retroactively PASS/SKIP and no scientific score or inference claim is produced.
