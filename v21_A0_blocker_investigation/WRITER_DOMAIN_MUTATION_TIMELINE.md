# Source-grounded writer-domain timeline

No new clocks, processes, locks or mutations were exercised. This is a partial-order reconstruction from the saved executable and raw artifacts. Where no timestamp was recorded, sequence follows program order; the table is not an invented syscall trace.

Let ROOT = E:/The End Engine/v21_A0_feasibility/runs/attempt_002/A0-18 and COPY = ROOT/copy.

| Step | Actor and causal event | Evidence and confidence |
|---|---|---|
| T0 | Parent enters case18 and creates a NEW rebased synthetic copy from the preserved public/mock fixture; not a provider execution or original-origin attestation | case18:127; clone_fixture:145; copy.clone_receipt.json. Raw vector start Unix1792509955.200613 |
| T1 | Parent creates ROOT/ADMISSION.lock, reads its pre-window snapshot and own attempt count | case18:128. Before snapshot existed in memory but was not persisted as a separate pre-boundary manifest; do not claim an independent atomic absence trace |
| T2 | Parent acquires G then L1 COPY/.publication.lock then test L2 COPY/.a0-L2.lock and pins existing data | case18:129 and ExistingLock/Pins source. All entries completed before body/spawn. Operational *.lock controls are excluded by data_paths from data pins |
| T3 | Parent launches register_bypass child with fixture COPY; child PID24156 | Saved *.request.json and *.request.exit.json. Request filename includes parent time_ns1792509955457376300; this is an identifier/approximate parent wall clock, not a separate acquisition timestamp |
| T4 | Child reads context and builds request run_id A0_UNENROLLED_REGISTER; does not acquire G, L1 or L2 | perform:180 register_bypass branch. Source-derived; no runtime trace claiming other locks |
| T5 | Child calls unchanged Ledger.register:48 and acquires ordinary L3 COPY/budget.json.lock | Current source matches saved implementation manifest. Parent holds no L3, so this is not lock recursion or an L2→L1 cycle |
| T6 | Child reads the existing envelope and adds the foreign registration to in-memory state | Ledger.register body. No new attempt reservation; raw child attempt_rows_after=1 |
| T7 | Ledger._write:41 writes, flushes and fsyncs COPY/budget.json.pending | Preserved pending file, valid canonical state checksum and raw hash4d558735078b814d143dc00a3945be927f126cff0f80101f405f448d57441a23. The foreign registration and exact source write path establish new writer-produced content; no full atomic pre-inventory was persisted |
| T8 | os.replace(pending, ledger) fails with child PermissionError/WinError5 because replacement of the pinned target is denied | Raw child event names both source/destination paths. Existing ledger before/after hash remains de3f151a8b66d79dfccbe92a1f1f8713a70ba929a066d18c01660cd15c740a43 |
| T9 | Child catches that operation exception, records pending_created=true, its hash, unchanged ledger hash and one attempt; exits0 | Request result and exit receipts. Exit0 is successful negative-evidence recording, not successful registration |
| T10 | Parent collect returns, then zero_worker accepts exit0 while parent G/L1/L2/pins remain active | case18:130 left side and collect:130. No collector TimeoutExpired and no missing child outcome in this vector |
| T11 | Parent calls snapshot(COPY), tries all files including active operational controls, and raises Errno13 at read_bytes/f.read | Raw A0-18 traceback. Exact sorted preserved membership starts .a0-L2.lock. That filename is reconstructed from source/order, not present in the exception itself |
| T12 | Exception unwinds guard/pin context before case18 can compute additions or return its blocker fields | Source context-manager control flow. No specific cleanup failure is recorded; immediate cleanup timing was not separately measured |
| T13 | Runner catches the non-AssertionError as ERROR, retains trace/result and stops | probe_runner.main:9 catch/finally; run counts19PASS/1ERROR; vector duration0.75s. Raw material_blocker=false is retained because the returning code was never reached |
| T14 | Later administrative analysis verifies the surviving pending file and unchanged ledger and separately records the material writer-domain gap | Original _control/BLOCKER_ANALYSIS.json and this investigation's read-only evidence hashes. No original vector overwritten or rerun |

## Guards and namespaces

G is a test-only admission control, not an existing global Ledger API lock. L1 is the run publication guard. New L2 is separate from both the existing Gateway D guard COPY/budget.boundary.lock and L3 COPY/budget.json.lock. The parent L1/L2 order was not the demonstrated defect. The unenrolled child used L3 and never participated in the new outer gates; that is why a correct order among participating actors did not exclude it.

Native read pins protect existing handles' content/replacement access. They do not prevent the writer from creating a previously unpinned pending filename. No evidence shows a changed owner/fence, new attempt, provider request, completed-source overwrite or falsely verified RESULT in this vector. Those hypothetical failures must not be added to the observed timeline.

The test window is an attempted coordination arrangement, not a validated A/S capture boundary. A supported quiescence-first claim would require proving every relevant producer is enrolled, excluded or drained before B and cannot reenter through an untracked administrative/direct call. The saved two-participant success proves less than that. Correcting the parent snapshot alone cannot change T4–T8.
