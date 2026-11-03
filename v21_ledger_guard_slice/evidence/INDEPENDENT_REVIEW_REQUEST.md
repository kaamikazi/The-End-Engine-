# Independent review request — pending

Requested verdict: review this narrow Ledger slice only. Author testing is not independent acceptance or authenticated human approval. Current author recommendation is LEDGER_GUARD_SLICE_READY_FOR_INDEPENDENT_REVIEW; whole END runtime and scientific readiness remain withheld.

Checkout: `E:/The End Engine/v21_ledger_guard_slice/checkout`
Branch: `codex/v21-ledger-guard-slice`
Base HEAD: `783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e`
New commit: none (scoped working-tree patch)
Candidate source digest: `e1f62915f944854ef340db8f43a6454ceb077c6a5c61b888e46eeea59182eecd`
Evidence: `E:/The End Engine/v21_ledger_guard_slice/evidence`

Read EXACT_SOURCE_DIFF.md and `_control/EXACT.patch`, source map/digest, OPT_IN_COORDINATION_CONTRACT.md, all targeted/raw regression receipts and preservation. Independently verify only Ledger.__init__/lock/_write changed plus one stdlib module and new isolated tests. Inspect every old `_write` entry, first L2 before L3/control/pending, ordinary readers, same-resource canonical identity, checked thread/reentry and exception release. No automatic environment/sidecar enrollment; default callers explicitly remain outside the guarantee.

Reproduce actual Windows/NTFS enrolled register/constructor/reserve/finish exclusion while the **actual** L2 is held; confirm no pending/main/L3 initialization from the excluded child, then a legitimate post-release write. Preserve unenrolled pending bypass separately. Review real processes/threads, killed holders and pending crash window; native errno/winerror must be recorded exactly. Do not infer WinError5 from errno13. Validate stale pending preservation and old default differential behavior. Existing source core under L1→L2→ordinary L3 must remain nonowning with owner/fence/source bytes unchanged. No borrowed lease, D/L3 reentrancy or F01/F02 bypass.

Exact author targeted command: Python3.12 `-B evidence/_control/targeted.py attempt_004`, with PYTHONDONTWRITEBYTECODE=1 and PYTHONUTF8=1. That output exists and must not be overwritten. A reviewer can use `python -B -m unittest -v tests_coordination_v1.test_coordination` from the checkout with LEDGER_TEST_OUTPUT set to a **fresh reviewer-owned empty path** inside new evidence. This variable routes test output only, never production coordination. Test39 reads the preserved public A0 profile/template and records its synthetic relocation; if unavailable, disclose it, never substitute authenticated history. New paths must remain below evidence because native workers enforce that boundary.

Original suites: `evidence/_control/regressions.py baseline` and `candidate_final` (existing outputs, not safe to overwrite). Run each original project unittest discovery in a new reviewer directory/process; preserve original helpers/scratch behavior. Engine303, lab58, isolation85, native53 pass; r3 remains244 with16 failures/6 errors. REGRESSION_RESULTS.json compares every parent/subtest status/type/message exactly with no deltas. No old test is obsolete. Historical31 and N12 are not rewritten.

Retain initial attempt00136PASS/4ERROR, attempt00240PASS, attempt00340PASS/1FAIL and final attempt00441PASS as separate versions. Initial errors were new-test blind reads of a held control; corrected tests inspect all control bytes through the actual owner FD and after release. The path-policy failure was raw-name normalization before validation; final checks raw names before abspath. Production/test source snapshots and hashes accompany the earlier attempts. Neither is silently greened.

If the reviewer finds an introduced deadlock, unguarded enrolled write, unexpected compatibility regression, outside-scope source change, lost evidence or need to change F01/another production writer, return BLOCKED/SCOPE_EXPANSION_REQUIRED with precise evidence. Do not patch neighboring source, broaden the approved slice, publish or make A/S/complete-accounting/readiness claims. Independent acceptance remains pending after this author handoff.
