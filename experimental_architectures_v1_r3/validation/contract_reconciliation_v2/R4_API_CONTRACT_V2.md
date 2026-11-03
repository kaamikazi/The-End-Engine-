# R4 — current APIs versus prospective opt-in contract

No API implementation changes are authorized or made here. Existing APIs remain the low-level behavior described below. Prospective `execute_outcome_v2` is a documentation name for an opt-in adapter requiring separate scope/review; it does not exist in the current implementation. Direct Session/Publication are declared engineering interfaces with typed errors; stable external-consumer compatibility remains unverified. Do not silently replace execute's return schema or restore unsafe normal BLOCKED results for compatibility.

Artifact persistence, provenance, termination and response validity are separate axes. UNKNOWN is normally an attempt status aggregated as INTERRUPTED. INVALID_RESPONSE is a reason, not a provenance status. Supported UNCERTAIN reasons are exactly INTERRUPTED, EXTERNAL_BLOCKER, TIME_EXHAUSTED, BUDGET_EXHAUSTED, PROTOCOL_FAILURE, INVALID_RESPONSE, UNRESOLVED; all other semantic/closure checks still apply.

| API | State/reason | Current observed implementation | Prospective contract, NOT implemented |
|---|---|---|---|
| Session.finish() | VERIFIED | Returns new verified terminal or immutable existing valid result. | Same low-level return/verification; optional future v2 adapter wraps only after verification. |
| Session.finish() | BLOCKED | Raises RecoveryIntegrityHold before _build/publication; existing final verification may wrap as ArtifactIntegrity. | Keep typed rejection; adapter may expose separate diagnostic and mandatory R1 observations, never normal result. |
| Session.finish() | INTERRUPTED | Recomputes report, forces INTERRUPTED for interrupted evidence; compatible terminal persists. | Retain supported C0 and scoped counts, unknown cost; no provider replay. |
| Session.finish() | UNKNOWN | Normally aggregate INTERRUPTED; unknown/inflight reservations may persist restricted terminal. | Explicit unknown coverage; no success reason or guessed missing candidate/usage. |
| Session.finish() | INVALID_RESPONSE | Orthogonal reason; provenance must be eligible; rejected raw candidate retained without invalid FINAL. | Same provenance gate; v2 labels raw observation versus selected authority. |
| execute() | VERIFIED | Returns legacy normal terminal; valid completed Session admission can raise FileExistsError. | Keep existing behavior; proposed opt-in execute_outcome_v2 adapter emits v2 union, not silently substituted return. |
| execute() | BLOCKED | Translates only grounded RecoveryIntegrityHold to abc-r3-blocked-recovery-v1 diagnostic. | V2 adapter would require R1 structured observations; full accounting unverified; generic errors still propagate. |
| execute() | INTERRUPTED | Restores without dispatch and finishes compatible interruption. | Preserve known candidates/reservations, no replay or reset; explicit restricted terminal tag. |
| execute() | UNKNOWN | Unknown usage/reservation blocks continuation; compatible terminal reports unknown cost. | Separate known identity/count from unknown settlement/usage; no refund, replay or fake zero. |
| execute() | INVALID_RESPONSE | Catches NumericFault and finishes INVALID_RESPONSE with raw evidence when eligible. | Preserve invalid raw data; no fabricated FINAL; BLOCKED overrides certification independently. |
| blocked_recovery() | VERIFIED | Rethrows non-BLOCKED or ungrounded error, not generic fallback. | Retain strict internal preconditions; no normal-success conversion. |
| blocked_recovery() | BLOCKED | Requires grounded context, hold flag and real failed invariants; writes unique diagnostic only. | Prospective diagnostic builder must add R1 claims at justified tier; storage errors remain real errors. |
| blocked_recovery() | INTERRUPTED | Non-BLOCKED input rethrows. | Do not route legitimate interrupted state through integrity-failure builder. |
| blocked_recovery() | UNKNOWN | Non-BLOCKED input rethrows. | Do not equate unknown evidence with contradictory provenance. |
| blocked_recovery() | INVALID_RESPONSE | Termination alone does not satisfy builder preconditions. | Only aggregate BLOCKED context permits diagnostic; keep reason and provenance independent. |
| Publication.publish() | VERIFIED | Caller lock/lease/fence; semantic checks, prepared anchor, read pins, exclusive link. | Preserve every F01 operation and independent eligibility check; adapter cannot publish diagnostics. |
| Publication.publish() | BLOCKED | Independent semantic eligibility rejects, usually wrapped ArtifactIntegrity. | Unchanged; R1 observation object cannot grant eligibility. |
| Publication.publish() | INTERRUPTED | Only allowed uncertainty termination and valid other bindings/closure. | Unchanged restricted terminal, explicit v2 class if separately adapted. |
| Publication.publish() | UNKNOWN | UNCERTAIN mapping admits only restricted reasons after all checks. | No COMPLETED or NO_ACTIONABLE_REVISION from uncertain provenance. |
| Publication.publish() | INVALID_RESPONSE | May publish faithfully bound rejection if provenance/closure valid. | No scientific success implication or selected numeric-invalid answer. |
| Publication.verify_semantics() | VERIFIED | Returns validated input data after independently recomputed graph/result/closure bindings. | Same low-level verifier; no file publication or normalization side effect. |
| Publication.verify_semantics() | BLOCKED | Raw direct call raises grounded RecoveryIntegrityHold; wrappers may wrap ArtifactIntegrity. | Unchanged; do not trust caller report, false hold flag or precomputed observations. |
| Publication.verify_semantics() | INTERRUPTED | Verifies exact current report plus restricted reason and bindings. | Unchanged; observations never stand in for full-report equality. |
| Publication.verify_semantics() | UNKNOWN | Maps to UNCERTAIN; incompatible success reason rejected. | Unknown aggregate names outside supported enum fail closed, not guessed. |
| Publication.verify_semantics() | INVALID_RESPONSE | Validates provenance separately from response termination/eligibility. | Preserve raw invalid response, forbid uncertified selected content. |
| Publication.verify_completed() | VERIFIED | Verifies payload/prepared/owner plus current semantics; returns stored normal record. | Same immutable-byte return; adapter only decorates outside stored payload. |
| Publication.verify_completed() | BLOCKED | Raises ArtifactIntegrity with underlying cause; existing file stays unchanged. | Same; diagnostic may reference suspect file hash only, never return currently verified=true. |
| Publication.verify_completed() | INTERRUPTED | Can verify a valid persisted interruption, not successful reasoning. | Keep restricted artifact identity distinct from successful terminal reason. |
| Publication.verify_completed() | UNKNOWN | Unknown reservations/usage permitted only in eligible restricted persisted terminal. | No success upgrade, inferred usage or replay. |
| Publication.verify_completed() | INVALID_RESPONSE | Can verify the integrity of a recorded rejection if all bindings pass. | Never equate artifact verification with answer correctness. |

RecoveryIntegrityHold subclasses ArtifactIntegrity/BoundaryError/ValueError and carries a grounded report/publication context. It is not interchangeable with arbitrary ValueError, numeric faults, I/O errors or a programming RuntimeError. Keep only the existing narrow hold translation. No broad catch converts unrelated programming/F01/storage errors into diagnostic success; preserve original causes. A missing/corrupt ledger or failed diagnostic write can remain a real error. An unknown/mixed schema or forged hold fails closed.

## Consumer inventory and compatibility gates

Known repository consumers: src/shared/wiring.py uses execute and direct publication; tests/helpers.py ScenarioCase assumes legacy RunResult fields; tests/accounting/test_resources.py reads final_candidate/count/closure; tests/corrections test_f02 reads count1 on BLOCKED; test_interactions/test_provenance_r3/test_recovery_hold call direct finish; tests/corrections/process_worker.py constructs Session before its barrier; reproduce.py and versioned validation helpers use legacy records. Private historical reviewer races expect ready after admission and normal terminal hashes; prior FINAL_JOURNAL_HASH_MISMATCH expects execute to throw an exact class name. These are affected consumers, not permission to edit them.

External caller reach is UNKNOWN. A separately authorized migration must inventory import/call sites, designate supported public/internal boundaries, publish schema and exception specifications, supply an explicit opt-in adapter, and test old readers on archived original-contract records plus new readers on each v2 union variant. Existing recorded schemas/bytes and historical tests remain frozen. Current legacy APIs cannot promise unsafe certification to preserve an obsolete return shape. Document any intentional incompatible change prospectively, with a named version and independent approval.

Prospective controls cover all thirty cells above, valid complete/interrupted/failed/unknown/invalid positives, direct and orchestrated blocked negatives, forged reports/holds, missing ledger, generic F01/storage and programming exceptions, and old/new readers. No API test is installed in this proposal task.
