# A0 blocker root-cause investigation

**A0_STRONG_PROFILE_NOT_SUPPORTED.** The tested domain does not exclude an actual unenrolled ledger writer. The collector has a separate, locally diagnosable reporting defect. Correcting the collector cannot supply the missing domain proof. This is a read-only diagnosis and remediation proposal, not A0 acceptance or A1 authorization.

## Evidence identity and method

Source checkpoint:783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e, local A0 branch codex/v21-a0-feasibility. The exact executed attempt_002 scaffolds, their saved SHA-256 receipt, raw request/result/exit/vector files and surviving synthetic ledger/pending files were inspected. Current implementation bytes match all246 recorded source-manifest entries. All721 previously manifested A0 evidence members and the separate scoring-clarification receipt matched their hashes at investigation start. No A0/runtime module was imported, no process experiment launched, and no test rerun.

Primary evidence is in E:/The End Engine/v21_A0_feasibility/runs/attempt_002/A0-18/, not merely the later summary label. This investigation's _evidence/RAW_CAUSAL_EVIDENCE.json retains the parsed raw evidence, reconstructed membership order and exact source references; EXACT_SOURCE_BLOCKS.json contains the source excerpts and line identities. Original evidence remains in place and is hash-protected.

## Root cause 1: coverage gap before ledger replacement

The actual child PID24156 ran the saved probe_workers.perform register_bypass branch. It constructed a nonowning context for the scratch copy, changed only the requested registration ID to A0_UNENROLLED_REGISTER, and called the unchanged cognitive_architecture_lab_v1/src/accounting/ledger.py Ledger.register:48. That method acquires only Ledger.lock/L3, reads the ledger, updates the runs map in memory, and calls Ledger._write:41.

The parent case18:127 held, in order, its test admission gate ADMISSION.lock, existing run L1 copy/.publication.lock, distinct test L2 copy/.a0-L2.lock, and read pins on existing data paths. These facts follow from the exact executed with-statement and the fact that its body reached the completed child collection. They are source-grounded ordering facts, not a new live lock inspection. The parent intentionally did not hold L3, allowing legitimate unchanged verifier reads; the child could therefore acquire its ordinary copy/budget.json.lock L3.

The child never entered the test admission gate or L1/L2. Ledger._write opened copy/budget.json.pending with wb, wrote the canonical envelope, flushed and fsynced it, then attempted os.replace onto copy/budget.json. Existing read pins prevented replacement: the child caught PermissionError with WinError5. However, the new pending-file content/membership already existed. Its preserved state includes the foreign registration; the main ledger still contains only the original registration. Both contain the same one original attempt row: there was no new reservation or model dispatch.

| Object | Observed state |
|---|---|
| budget.json | Child before hash = child after hash = preserved current hash: de3f151a8b66d79dfccbe92a1f1f8713a70ba929a066d18c01660cd15c740a43 |
| budget.json.pending | Hash4d558735078b814d143dc00a3945be927f126cff0f80101f405f448d57441a23; contains A0_UNENROLLED_REGISTER; checksum validates as a recorded envelope |
| Registered attempts and other state | Entire attempt arrays identical, one original row; limits/halted/schema and all existing run contracts unchanged; only A0_UNENROLLED_REGISTER added to pending runs. Exact comparison in _evidence/STATE_DELTA.json |
| Child completion | Worker exit0; operation event explicitly says RAISED/PermissionError/WinError5, followed by pending_created=true |

Exit0 means the worker successfully recorded its negative operation, not that registration succeeded. Likewise, a denied final replace is not proof of namespace stability. An unsuccessful mutation transaction can leave relevant newly written evidence. Ignoring the pending name because the main ledger hash matches would violate the R1 complete-membership requirement.

The demonstrated problem is **incomplete cooperative-domain coverage**, not a demonstrated L1/L2/L3 inversion or production deadlock. An assumption that all relevant producers were excluded would be invalid in this arrangement. A0-17's two deliberately cooperating admission workers cannot justify that assumption for all40 source classes and the unknown external actor. The child was deliberately unenrolled; this does not prove every operationally closed cooperative deployment is impossible, or that hostile-host exclusion is required. It does prove the strong guarantee is unavailable in the tested setup.

## Root cause 2: collector reads its own byte-locked control

After the child returned and zero_worker validated its exit0, the parent immediately called snapshot(pub.directory) inside the same held guard/pin scope. The saved snapshot:49 recursively sorts every file and calls Path.read_bytes on each, with no distinction between historical data and active operational lock controls.

The parent trace records PermissionError: [Errno13] Permission denied at pathlib.read_bytes → f.read. It does not record a failing filename. The preserved membership sorted by the exact executed algorithm begins with copy/.a0-L2.lock, then copy/.publication.lock. The first is the byte-locked L2 file held by the parent through another descriptor. Thus **.a0-L2.lock is the source-derived first failing-read object**, not a newly captured syscall filename. Native byte-range read denial is consistent with the recorded operation, lock ownership and earlier native controls; no new native reproduction or causal timestamp is invented.

This is a test evidence-collection/resource-classification defect interacting with native Windows locking. It is not the child's replace exception, a worker collection timeout, a JSON serialization error, or evidence that the unchanged completed-source verifier failed. collect had already returned; the error is the subsequent indiscriminate snapshot. The source core is not called in case18 at that point. Other saved controls tested the core and its independent F02 rejection separately.

Because this read raised before case18 computed additions/changed and returned its result, the raw vector has ERROR, empty observed_events and material_blocker=false. The runner correctly retained the exception and stopped; the false raw blocker flag reflects unreachable reporting code, not absence of the independently recorded child mutation. The administrative blocker finding must remain a separate derivation. It cannot overwrite ERROR with PASS.

## Boundaries and scientific interpretation

The mutation occurred inside the **intended test candidate window** with G/L1/L2/pins held. It was not inside a successfully proved R1 B..E authoritative capture: the required all-writer domain assurance was absent, so A/S prerequisites were never met. Existing source plus these test locks cannot safely assert A or S in this profile. Useful per-source recorded facts may remain I; unsupported facts are X; observed candidate-window interference must abort strong claims, with U used only in its qualified prospective sense. No graph-wide complete count/cost, selected certified answer or provider-inference claim follows.

The four saved A0-04/A0-05 recursive negatives retain their bounded-negative PASS and all six scoring fields. Their child termination/blocked operations remain explicit; they do not prove successful recursive acquisition or safe production reentrancy. Latest A0 remains19PASS/1ERROR; first attempt10PASS/1FAIL/9NOT_EXECUTED stays historical. No result or scoring definition is changed.

## Remedy conclusion

Option A can repair the collector's evidence handling in isolated A0 tooling after approval. It can also make refusal of unsupported strong authority explicit. It cannot, merely by collecting better or ignoring controls, exclude the unenrolled writer. Option B is a separately reviewed possible production-coordination route, not proven necessary or authorized here. Option C is the currently supported capability limit: retain only justified lower facts and withhold strong A/S. The approved contract remains unchanged; the tested strategy's proof is incomplete.
