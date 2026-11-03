# Versioned CR2 acceptance suite plan

No test has been migrated, installed or executed by this task. Keep old244/154/49 sources, IDs, raw outcomes and assertions unchanged. CR2 is a NEW separately authorized suite, proposed under experimental_architectures_v1_r3/cr2_v21_tests/, outside existing tests/ discovery. Historical discovery must not silently include new tests and then mislabel the total as the old244.

## Individual historical property preservation

_evidence/CR2_HISTORICAL_MAPPING.csv has exactly31 rows CR2-H01..H31. Each copies the exact previous original test ID/source/assertion/mutation/scientific intent/status/classification and keeps its previous proposed mapping, replacement assertion and mandatory conditions. It adds the accepted v2.1 capture/authority predicates. The CSV is an implementation input, not evidence that a replacement ran or passed.

The sixteen JournalIntegrityTests cases keep the exact MUTATIONS source/helpers: wire/decoded/hash changes, invalid base64, moved settled journal/receipt, duplicate file/record, wrong run/stage/attempt, reversed records, torn append, current-row disagreement and recomputed chain that disagrees with independent anchor. Future C controls require the fourteen conditional A-count1/two S-group1 conclusions only under new proven capture, plus I fallback for all16. BLOCKED provenance, bytes, no replay, limits and no normal certification remain mandatory; do not merely replace physical_attempts1 with a nullable value.

Torn-C0 recovery preserves actual candidate/handle bytes, scoped count and no replay, with an intact-C0 positive. Direct finish on corrupt provenance keeps typed rejection/grounded diagnostic and no source result. Serializer fallback cannot conceal corruption, and gets a separate valid-provenance unsafe-metadata fallback positive. Stale object is admitted BEFORE mutation; a separately fresh constructor must reject after mutation. Missing-journal concurrency retains original two admitted workers and additional four-process contention. Existing final corruption rejects current verification while preserving exact final/prepared bytes and a valid immutable positive. Eight reviewer race rows retain their precise IDs and vectors, not generic catches. Every row's original invariant remains visible in the CSV.

## Required race catalogue

V0=(0,0,0,0), V1=(0,.015,.03,.045), V2=(.045,.03,.015,0), V3=(.02,0,.04,.01). Preserve exact original worker delays/ordering. Four-process cases use all four vectors. Faults: complete extra JSON bytes b'{"extra":true}\n', missing registered receipt with moved bytes retained, missing registered journal with moved bytes retained, and valid unchanged history.

Twenty primary schedules:16 four-process schedules (four histories × four vectors) and4 independently ordered two-process schedules (the same four histories with the original both-admitted-before-claim valid/missing-journal coverage). The original eight RACE_journal-corrupt_0..3/RACE_missing-receipt_0..3 IDs map to eight of the16; do not count them again as eight additional schedules. Exact byte/hash/path/move receipts are mandatory. Wrong malformed corruption is additive only.

Use separate admission and work rendezvous. For corrupt history, every actual worker reports before constructing Session, then returns its genuine constructor rejection or later failure; rejection cannot masquerade as reaching publication. For valid histories, both two-process workers must actually be admitted before the claim/finalize release. Four-process workers may have declared valid outcomes, but at least one must publish one independently verified source with original C0/handle/attempt and exactly one normal prepared/final hash. Rejecting every valid writer fails liveness. Original constructor-before-ready workers remain unchanged historical harness evidence; new CR2 workers use separately reviewed phase records.

Every schedule records code origins, PID/start identity, ready/admitted/claimed/seam phases, bounded waits/joins, exit code, exact exception class/cause, result/pending/prepared/source hashes, candidate/handle/usage and provider-dispatch observations. Missing worker, timeout, unexpected exception, invalid success, fake readiness or unaccounted child fails. Expected killed exits are allowed only at their designated crash vector, with exact observed boundary. Unexpected generic ValueError cannot satisfy an integrity-hold expectation.

## Native publication controls retained exactly

Keep all13 PublicationWindowTests source controls without replacement by constructor failure or sequential simulation:

1. test_wire_write_at_link
2. test_wire_delete_at_link
3. test_wire_rename_at_link
4. test_settlement_write_at_link
5. test_ledger_write_at_link
6. test_closure_write_at_link
7. test_owner_write_at_link
8. test_prepared_write_at_link
9. test_pending_write_at_link
10. test_change_after_initial_validation_rejected
11. test_new_orphan_at_exclusive_link_seam_is_rejected
12. test_native_link_hook_cannot_mutate_existing_wire
13. test_real_process_writer_denied_until_after_link

The last control must really publish valid history once while a real child write is denied, then show later damage rejects verification without changing completed bytes. EvidencePin/exclusive_publish/_CURRENT and owner machinery stay unchanged. Synthetic OSError and genuine Windows share-denial outcomes are distinguished. A sandbox denying os.link does not establish the native property; a later authorized native offline run must execute on NTFS with appropriate permissions or record a blocked test, never PASS.

## Crash, ownership and recovery coverage

Four named crash windows ×2 source/new-observer perspectives =8 planned vectors: prepared-before-link, after-exclusive-link, raw-response-before-settlement, numeric-invalid raw-before-inspection. Retain pending/prepared/final/raw and independent witness bytes. Actual terminated processes, not only raised exceptions, test OS cleanup. Lost unsealed memory is not recoverable proof. A new observer may retain lower facts or typed failure, never reserve/replay/repair or reset an unknown charged attempt.

Four owner vectors: active same-process owner; live other-process owner; owner death/relinquish followed by a newer fence; stale fencing token rejection. Four stale/existing vectors: valid pre-admitted stale caller, stale caller after fault, existing valid completed result, existing immutable suspect result. Four interruption vectors: reserved-no-dispatch; durable header-only; response-received/usage-unknown; supported C0 with later unknown usage. Preserve the original Engine three-cycle and A/B/C caps by source hashes rather than executing a new empirical experiment.

F budget is53 primary vectors:20 races+13 seams+8 crash+4 owner+4 stale/existing+4 interruption. Thirty-one historical properties map onto C/E/F vectors and are not an extra31 execution schedules automatically added to53. The actual future runner must publish a resolved per-vector manifest and counts for parameterized subcases; no invented final unittest count.

## R1 and R3 coexistence

CR2 additionally references A0/A1/B/C/D/E plans:20 feasibility controls; two coverage controls per41 writer/actor rows plus8 lifecycle controls;20 required snapshot scenarios (including3 positive histories),17 distinct fault-free counterpart controls and8 failure cleanup controls; all16 conditional accounting cases and I fallback; full structural and real-evidence semantic negative tests; all30 API cells and current/archived readers. Tests for future source proofs must invoke actual unchanged core at a proved cut, not a synthetic oracle. Existing independent schema corpus remains a separate seed corpus and cannot substitute for OS/capture proof.

## Acceptance and evidence protocol

Future driver must run in a NEW isolated source checkout/copy and never reuse old validation/scratch directories. Set PYTHONDONTWRITEBYTECODE=1 and -B, offline socket/HTTP denial in every child, unique output root and exact loaded-source hashes. Do not invoke validate.py: it also runs wiring and old fixed green assertions. Keep old suites as explicit preserved rosters in their own output records and CR2 as a separate roster. Run unaffected Engine/native/runtime/lab regressions in copied sources where available; compare actual outcomes, not an assumed count. No live/provider/benchmark or frozen-evaluator execution.

G acceptance requires every mandatory NEW publication/provenance/capture/API control actually pass, no skipped/unreached seam or unjoined worker, no unexplained source/default-interface regression, protected hashes unchanged and independently reviewed raw evidence. Old known outcomes stay244:222PASS/16FAIL/6ERROR;154:146PASS/8FAIL;49:48PASS/1FAIL as historical baseline. Do not relabel them green when CR2 supersedes a contract. Any unexpected new FAIL/ERROR, lost original property or provenance bypass blocks runtime acceptance and any later implementation commit. Every initial setup/fixture/assertion failure remains visible in an append-only evidence checkpoint.
