# Independent corrected A0-18 collector review

**A0_COLLECTOR_INDEPENDENTLY_ACCEPTED**

This verdict accepts the exact corrected A0-18 negative-evidence collector in its demonstrated scope. It does not accept a production observer, runtime, A1 enrollment, or a strong A/S profile. The material writer-domain obstacle remains present.

The review was performed in a fresh reviewer context separate from the collector author. I read the supplied mission, actual historical A0 source/evidence, blocker investigation, corrected source, saved two-file diffs, negative artifacts and preservation receipts. No relevant AGENTS.md was found in the workspace or its checked parent locations. Original directories were used read only. The coordinating reviewer owns the broad fresh preservation comparison in PRESERVATION.json; this review separately recomputed the saved evidence manifests and implementation hashes.

## Outcomes remain separate

| Evidence owner and scope | Actual saved/observed outcome | Driver exit |
| --- | --- | --- |
| Historical A0 attempt_002, not rerun | 19 PASS / 1 ERROR; A0-18 remains ERROR | 1, as recorded in its historical report |
| Corrected author-owned targeted run, not rerun | 1 PASS / 0 FAIL / 0 ERROR | 0, saved command receipt |
| This independent exact targeted run | **1 PASS / 0 FAIL / 0 ERROR** | **0, directly observed** |

The independent run executed once, requested only A0-18, and used fresh `runs/independent_001/A0-18/copy` scratch. The child exited 0 after recording its expected failed writer operation. Child exit 0 means its evidence recording completed; the ledger registration did not succeed. No full historical runner was executed, no failed test was repaired, and no rerun to green occurred.

The original A0-18 parent traceback is preserved as PermissionError/Errno13 in `snapshot/read_bytes`, with an empty observed_events list. The original child separately recorded the failed replacement with WinError5 and a surviving pending envelope. The historical parent exception has no filename; `.a0-L2.lock` as its first failed candidate remains a source/order reconstruction, not a newly observed native path. Neither that ERROR nor its unreached blocker return has been rewritten.

## Exact correction and executable identity

The six historical scaffold files were compared byte for byte with the corrected files. Only `probe_workers.py` and `test_lock_domain_feasibility.py` differ. Independent AST comparison found exactly one added top-level function, `collect_a018_namespace`, and exactly one modified function, `case18`. No original worker function/class changed; the original `snapshot`, `recursive` scoring function and all unrelated cases remain unchanged. All four other scaffold files are identical.

The correction author's saved two-file diffs equal the independently generated diffs byte for byte. The reviewer's driver and all six harness files are exact copies, and the actually executed six-file archive has identical hashes. Driver SHA-256 is `49eabd09fc32238a4eb2db0aecdc32dab4f0c8504d72b97c243c36e51c3919c8`. Corrected worker hash is `2da7bdfb67aec9741d8dbb04440d80912c85186ef6246052824985ca45317348`; corrected cases hash is `aa37b4c8d15bda9697e5802e2fa97045b1a5aea452f8d260c3efd6f7c5f497f3`.

Before execution I inspected the driver, the collector, case18, its register_bypass child branch, fixture cloning, native guards/pins, tripwires and unchanged Ledger implementation. The exact driver fixes the read-only checkout, verifies the implementation manifest, bounds output to its own new runs directory, calls case18 only, retains failures and collects children. Synthetic relocation updates only the new copied fixture. It neither performs a provider event nor establishes authenticated historical origin.

## Ten required checks

| Requirement | Independent finding |
| --- | --- |
| Explicit operational controls | Exact declared paths classify controls. Six internal operational entries are visible; the external admission gate is separately recorded. A filename suffix does not confer control status. |
| Active controls remain visible | Two internal active controls, `.a0-L2.lock` and `.publication.lock`, plus external `ADMISSION.lock`, retain owned-descriptor identity. All three explicitly record NOT_READ_ACTIVE_LOCK_CONTROL with null hash and null content. |
| Pending evidence inventoried | PRE has 34 entries; POST has 35. The only addition is `budget.json.pending`, category C, with captured bytes, raw SHA-256 and native identity. |
| Unknown members visible | All 12 category-D entries remain. Independent comparison against the actual post-run tree found no omitted or invented members. Directories remain entries with explicit non-byte status. |
| Main-ledger bytes unchanged | PRE, POST, child-before, child-after and current raw main-ledger hashes agree at `de3f151a8b66d79dfccbe92a1f1f8713a70ba929a066d18c01660cd15c740a43`. |
| Foreign registration recorded | Captured pending state contains A0_UNENROLLED_REGISTER; main ledger does not. Pending hash is `4d558735078b814d143dc00a3945be927f126cff0f80101f405f448d57441a23`. Both envelope checksums validate; entire attempt arrays are identical with one inherited fixture row. |
| No fabricated hashes | Independently decoded all PRE/POST captured bytes and recomputed their lengths/hashes. They match, and POST captured-file hashes match actual scratch bytes. Active control bytes are expressly unclaimed while held. All 246 implementation-manifest hashes match. |
| Native handles released | Owned descriptors are closed and pin handle list empty. All three guards are reacquired/released, and 22 read/write/delete-access opens of formerly pinned files succeed and close without byte mutation. L3 state read retains one attempt. |
| No provider calls | Parent and child network/dispatch/reservation tripwires are all zero. Source review confirms this one control uses registration and existing copied evidence, with zero new reservations or dispatches. No live inference, replay or benchmark occurred. |
| Original evidence preserved | Recomputed all entries of the original A0, blocker-investigation and correction evidence hash manifests with zero mismatches. The implementation manifest also has zero mismatches. Fresh broader before/after byte, membership and Git comparison is supplied separately in PRESERVATION.json. |

POST internal categories are A operational 6, B historical fixture evidence 16, C pending 1 and D unknown 12. Required read failures are zero. The policy's completeness flag describes this explicitly limited A0 inventory; it does not claim captured bytes for active controls or a simultaneous membership/content boundary.

The native environment was Windows 11 build 26300, Python 3.12.14, volume E:\\ on NTFS, serial `bc08b541`. Observed case duration was 1.422 seconds; this is control timing and conveys no Engine or model performance result.

## Bounds and retained safety

The collector persists PRE inventory before entering the mutation phase, saves child exit/results before scanning POST, and saves POST before later mutation assertions. Ordinary per-member read failures preserve the path, operation, exception and errno/winerror and make collection incomplete; assertions then reject an incomplete collection. This source behavior was reviewed. The exact authorized vector did not inject an arbitrary unreadable file, unexpected new .lock member, reparse point, or forced cleanup failure; those broader behaviors are not independently certified by this one run. The supplied unknown inherited members provide only the observed retention check. No universal leak-freedom claim follows from the completed-path release checks.

The collector does not establish a common cut. Operational controls carry metadata while held, and namespace traversal is a bounded test evidence procedure. A passing detector is compatible with its detected material blocker. The actual result retains `authority=U`, `material_blocker=true`, `strong_profile_supported=false`, and `A_or_S_awarded=false`. Grounded individual facts do not confer strong authority or complete accounting. Independent certification requirements remain mandatory.

No production source, historical test/report, contract, Engine, Harness, evaluator, algorithm, prompt, ceiling or Git state was changed by this reviewer. No new scientific implementation direction is chosen in this collector-only finding.

## Inspectable evidence

- `COLLECTOR_RETEST_RESULTS.json`: actual separate outcomes, exits, checks, identities, hashes and limits.
- `_control/COPY_RECEIPT.json`, `EXACT_COMMAND.json`, `COMMAND_EXIT.json`, `TARGETED_STDOUT.txt`, `TARGETED_STDERR.txt`: exact copies, argv, environment and observed process result.
- `runs/independent_001/TARGETED_RESULT.json`, `EXECUTED_HARNESS_RECEIPT.json`, `executed_harness/`, and the two `.diff` files: raw execution and exact source archive.
- `runs/independent_001/A0-18/PRE_NAMESPACE_INVENTORY.json`, `POST_NAMESPACE_INVENTORY.json`, `CHILD_COLLECTION_RECEIPT.json`, child request/result/exit files, `PENDING_MUTATION_RECEIPT.json`, `RESOURCE_RELEASE_RECEIPT.json`, and retained copied files: raw negative and release evidence.
- `_control/INDEPENDENT_EVIDENCE_AUDIT.json` and `review_evidence.py`: reviewer-owned read-only administrative rehash/membership audit, not an additional A0 control.
