# Exact A0-18 collector ERROR analysis

**The existing ERROR remains ERROR. No rerun or correction is performed.** Its primary cause is the parent's unconditional read of an active operational byte-lock file during evidence snapshot, after child collection completed.

## Two distinct PermissionErrors

| Field | Child operation | Parent collector |
|---|---|---|
| Exception | PermissionError, WinError5 | PermissionError, Errno13; trace has no filename/winerror field |
| Operation | os.replace(COPY/budget.json.pending, COPY/budget.json) in unchanged Ledger._write | Path.read_bytes → f.read in saved probe_workers.snapshot:49 |
| Handling | Caught in perform/register_bypass; recorded as RAISED | Uncaught in case18; runner records ERROR |
| Process result | Child PID24156 exit0 after writing complete JSON evidence | Parent probe process exit1 after writing ERROR result and stop |
| State | Existing ledger remains pinned/unchanged; foreign-registration pending envelope survives | Parent before/after delta calculation and result-return code never reached |
| Implication | Existing data protection worked, but namespace exclusion was incomplete | Harness failed to collect all post-state evidence; not a production verifier or serialization failure |

## Exact failing chain

Saved case18:130 evaluates zero_worker(collect(spawn(...))) completely, assigns r, then evaluates snapshot(pub.directory) within its existing with-block. Saved snapshot:49 uses sorted(root.rglob('*')), retains every file, and unconditionally reads all file bytes. It does not use the distinction that data_paths uses when deciding which paths to pin. ExistingLock:95 locks byte0 through a read/write descriptor. snapshot subsequently opens another descriptor and tries to read that same active control file's bytes.

The first preserved sorted candidate is COPY/.a0-L2.lock; next is COPY/.publication.lock. The raw trace stops at f.read without a filename, so the exact first path is a deterministic source/preserved-membership reconstruction, not a new native syscall observation. The recorded Errno13 is consistent with byte-lock enforcement at that read. This investigation neither reproduces that native condition nor infers a generic filesystem ACL defect from it.

The child result/exit JSON already existed and was decoded successfully. No A0-18 timeout receipt or child exception escaped collect. The ERROR is not child-process orchestration, a missed ready marker, an unjoined worker, timeout handling or invalid JSON serialization. Its source location is evidence acquisition in test scaffolding. The runner was able to serialize the later ERROR/trace. Its generic catch did not falsely return success.

## Reporting blind spot

The in-memory before snapshot was never persisted independently. The exception prevented creation of after, additions, changed and the function's material_blocker=true return. Consequently the raw status/error and empty observed_events must remain unchanged. The child event plus preserved pending bytes support a separate causal finding, not retroactive execution of the unreached parent assertions. A later corrected collector must save phase-level evidence before any assertion that could fail.

The saved runner's finally clause attempts to collect any remaining children and native context-manager exits close their own handles. No cleanup failure is recorded here, but the full immediate-release sequence has no separate timing trace. Do not claim a new cleanup control passed merely because the process later exited. Any proposed correction must exercise cleanup under its own separately authorized failure paths.

## Minimal A0-local correction proposal — not applied

Keep complete membership enumeration, including operational controls, unknown names, .pending files and unexpected .lock names. Replace the monolithic hash dictionary with per-entry records distinguishing readable captured data, explicit expected absence, known held control descriptor and read-unavailable error. Persist the initial inventory before entering the mutation phase and the child result/exit before the post-scan.

For known active controls, use the actual owned handle's identity/declared role, and record content as not read while held when appropriate. Whether any owned-handle read is safe must be tested rather than assumed. An unreadable control must not become a fabricated byte hash or disappear from inventory. Unknown files ending in .lock are not automatically trusted controls. Record OSError narrowly at the read operation and preserve path/errno/winerror; propagate or mark a required-data read failure instead of silently continuing as complete.

Evaluate two separate conclusions after evidence collection: did the collector faithfully record the full state, and did an unenrolled writer invalidate strong exclusion? Detecting the latter can satisfy a targeted negative-test expectation, while the overall strong profile remains blocked. Collector repair is not writer enrollment, an expanded catch-to-success boundary or permission to weaken R1.

Only future A0 test files probe_workers.snapshot/case18 and narrowly related report scaffolding would need a precise approved diff. No change to Ledger, F01, existing pins, F02 source eligibility or historical assertions is needed to propose this collector fix. No fix or rerun is authorized by this investigation.

## Additional inventory-label limitation

The original writer-coverage CSV labels both current-r3 and historical Session.__init__ rows with a dynamic19 string. The original post_stop_reports helper keys its dynamic map by the unqualified symbol spelling, so that field alone cannot prove the historical version was invoked. Saved worker imports and module-path setup designate the current-r3 Session. Preserve the old CSV, and require module-qualified path/hash evidence for any future coverage claim. This is a metadata over-attribution risk, not the cause of Errno13 or evidence of a new historical runtime execution.
