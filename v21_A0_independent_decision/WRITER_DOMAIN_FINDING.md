# Independently grounded writer-domain finding

**A0-18 demonstrates a writer-domain exclusion failure in the tested arrangement. It remains an obstacle to granting A/S for that arrangement after the collector correction.**

The corrected collector successfully records the negative. It does not make the actual Ledger writer participate in the proposed outer controls. The independent exact A0-18 result is 1 PASS, while strong_profile_supported remains false and material_blocker remains true.

## Source and actual mutation

The unchanged approved checkout's `cognitive_architecture_lab_v1/src/accounting/ledger.py` implements `lock` at line 19, `_write` at line 41 and `register` at line 48. Independent rehash confirms that source matches the saved approved implementation manifest. `register` enters only its ordinary ledger lock, L3 (`budget.json.lock`), reads state, inserts its run contract, and calls `_write`. It neither acquires the test admission gate nor the publication L1 or proposed L2 guard. `_write` opens `budget.json.pending` with `wb`, writes the canonical envelope, flushes, fsyncs, closes, then calls `os.replace(pending, main)`.

Corrected case18, at `harness/test_lock_domain_feasibility.py:127`, creates a fresh rebased synthetic copy and records PRE state. Its parent then acquires the admission gate, run L1 and test L2 and pins existing data. Only after entering all those contexts does it launch the unchanged `register_bypass` worker branch. The worker creates request identity A0_UNENROLLED_REGISTER and calls real `Ledger.register`; it does not call reserve, dispatch or a provider. L3 is free for its ordinary use, so this is not an experiment in recursive L3 acquisition.

The independent child's operation raises PermissionError/WinError5 on `os.replace`. Its child process exits 0 after recording that exception. POST inventory is captured while the parent outer guards/pins are still held. The only new namespace member is `budget.json.pending`; the captured envelope contains the foreign registration. The main ledger lacks that registration, and its raw bytes remain identical. No new or modified attempt row appears.

This causal order follows reviewed program order plus persisted receipts and bytes. It is not an invented syscall-time trace or an atomic-boundary claim.

| Distinct event | Observed result | Meaning |
| --- | --- | --- |
| Pinned main-ledger replacement | Failed; PermissionError/WinError5 | Existing target replacement protection held in this control. The register API did not return successfully. |
| Pending-file creation | Succeeded; new captured `budget.json.pending` | Relevant namespace/content changed during the attempted outer exclusion window. This survives the denied replacement. |
| All-writer exclusion | Failed for the tested outer arrangement | This real API caller used L3 without enrolling in the held admission/L1/L2 domain. Existing-file pins do not freeze newly created names. |
| Historical collector | ERROR/Errno13 after child collection | Its unconditional read of active controls prevented the intended parent report. The raw historical ERROR remains unchanged. |
| Corrected collector | Independent targeted PASS | It inventories the pending mutation, unknown members and active-control identities and preserves the negative without awarding A/S. |

## Independent byte evidence

- Main ledger PRE/POST and child-before/after SHA-256: `de3f151a8b66d79dfccbe92a1f1f8713a70ba929a066d18c01660cd15c740a43`.
- New pending SHA-256: `4d558735078b814d143dc00a3945be927f126cff0f80101f405f448d57441a23`.
- Both raw envelope checksums independently validate. Pending and main attempt arrays are exactly equal and contain one copied historical fixture row. The foreign run identity exists only in pending state.
- PRE has 34 entries; POST has 35; actual saved POST tree and inventory have no missing or invented members. The raw namespace addition is precisely `budget.json.pending`.
- All three parent guard descriptors close, pins close, all three guards are reacquired, 22 formerly pinned files admit subsequent read/write/delete-access opens, and L3 state remains readable. This is observed-path cleanup, not a claim about every failure path.
- Parent/child forbidden network and reservation/dispatch counts are all zero. These hashes and inherited fixture records do not authenticate provider inference or fabricate a new call.

Raw support is in `runs/independent_001/A0-18/`: PRE/POST inventories; child request/result/exit and collection receipt; pending mutation receipt; resource release receipt; and the retained scratch ledger and pending envelope. `_control/INDEPENDENT_EVIDENCE_AUDIT.json` independently recomputes captured hashes, checksums, membership and source identity. See COLLECTOR_RETEST_RESULTS.json for exact process IDs, command/exit references and full bounds.

## Authority implication and limits

The tested candidate arrangement lacks the required all-writer coverage and common membership/content cut. A successful exclusion claim cannot be inferred from unchanged main-ledger bytes when a relevant unenrolled writer has created a pending member. Correcting collection changes neither that writer's lock domain nor the negative mutation.

No evidence here proves all possible strong-profile implementations impossible. An implementation that demonstrably enrolls, excludes or drains every relevant writer could have a different result; it would require its own explicit scope and independent evidence. This review does not award that authority in advance, prescribe a production lock change, or implement enrollment.

The finding is also not a demonstrated F01 bypass, falsified final-result certification, owner/fence takeover, new reserved attempt, unrecorded provider call, or malicious-host resistance result. Those events were not observed in this vector. Existing independent final eligibility and certification gates remain mandatory. The local synthetic fixture and its rebased checksums establish inspectable test evidence only.

Historical A0 remains 19 PASS / 1 ERROR; the author's separate targeted correction remains 1 PASS; this reviewer's separate exact targeted control is 1 PASS. No sum of those outcomes establishes strong feasibility or runtime acceptance.
