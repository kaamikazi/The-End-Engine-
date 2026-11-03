"""Summarize the single authorized A0-18 rerun; no additional controls execute."""
import base64,collections,ctypes,hashlib,json,platform,sys
from ctypes import wintypes as wt
from pathlib import Path
H=Path(__file__).resolve().parent;E=H.parent;A=Path('E:/The End Engine/v21_A0_feasibility');R=E/'runs/attempt_001';V=R/'A0-18'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def text(n,x):(E/n).write_text(x.strip()+'\n',encoding='utf-8')
result=read(R/'TARGETED_RESULT.json');before=read(V/'PRE_NAMESPACE_INVENTORY.json');after=read(V/'POST_NAMESPACE_INVENTORY.json');mutation=read(V/'PENDING_MUTATION_RECEIPT.json');cleanup=read(V/'RESOURCE_RELEASE_RECEIPT.json');child=read(V/'CHILD_COLLECTION_RECEIPT.json');pres=read(E/'SOURCE_PRESERVATION.json');baseline=read(H/'PRE_CORRECTION_BASELINE.json');source=read(R/'EXECUTED_HARNESS_RECEIPT.json')
assert result['status']=='PASS' and result['executed_controls']==1 and result['material_blocker'] and not result['strong_profile_supported'] and not result['A_or_S_awarded']
assert child['exit_code']==0 and mutation['writer_operation']['winerror']==5 and mutation['foreign_registration_detected'] and mutation['attempt_arrays_identical'] and not after['required_read_failures'] and pres['passed']
pending=mutation['pending_entry'];raw=base64.b64decode(pending['raw_base64'],validate=True);state=json.loads(raw)['state'];ledger=read(V/'copy/budget.json')['state'];assert sha(V/'copy/budget.json.pending')==pending['sha256']==hashlib.sha256(raw).hexdigest()
assert all(child['worker_result']['counters'][k]==0==result['parent_tripwire_counters'][k] for k in result['parent_tripwire_counters'])
K=ctypes.WinDLL('kernel32',use_last_error=True);volume=ctypes.create_unicode_buffer(1024);label=ctypes.create_unicode_buffer(1024);fs=ctypes.create_unicode_buffer(128);serial=wt.DWORD();maxlen=wt.DWORD();flags=wt.DWORD()
K.GetVolumePathNameW.argtypes=[wt.LPCWSTR,wt.LPWSTR,wt.DWORD];K.GetVolumePathNameW.restype=wt.BOOL
K.GetVolumeInformationW.argtypes=[wt.LPCWSTR,wt.LPWSTR,wt.DWORD,ctypes.POINTER(wt.DWORD),ctypes.POINTER(wt.DWORD),ctypes.POINTER(wt.DWORD),wt.LPWSTR,wt.DWORD];K.GetVolumeInformationW.restype=wt.BOOL
assert K.GetVolumePathNameW(str(V.resolve()),volume,len(volume)) and K.GetVolumeInformationW(volume.value,label,len(label),ctypes.byref(serial),ctypes.byref(maxlen),ctypes.byref(flags),fs,len(fs))
assert fs.value=='NTFS'
environment={'python':sys.version,'python_executable':sys.executable,'windows':platform.platform(),'actual_rerun_volume':volume.value,'filesystem':fs.value,'volume_serial':format(serial.value,'08x'),'volume_query_scope':'Post-run metadata verification, not an extra control or performance experiment'}
counts={'actual_new_controls_executed':1,'PASS':1,'FAIL':0,'ERROR':0,'historical_attempt_002':{'PASS':19,'FAIL':0,'ERROR':1,'NOT_EXECUTED':0},'historical_attempt_001':{'PASS':10,'FAIL':1,'ERROR':0,'NOT_EXECUTED':9},'saved_recursive_negatives':'Four prior bounded-negative PASS unchanged; not rerun','do_not_combine_historical_and_new_counts':True}
save('A0_18_RAW_RERUN.json',{'verdict':'A0_COLLECTOR_CORRECTED_STRONG_PROFILE_BLOCKED','raw_targeted_result':result,'raw_child_receipt':child,'actual_counts':counts,'environment':environment,'executed_harness_receipt':source,'raw_artifacts':{str(p.relative_to(E)):sha(p) for p in V.glob('*.json') if p.is_file()},'target_command_output':(H/'TARGETED_COMMAND_OUTPUT.txt').read_text(encoding='utf-8'),'target_command_exit_code_observed':0})
save('NAMESPACE_INVENTORY.json',{'before':before,'after':after,'added_namespace_members':mutation['added_namespace_members'],'changed_readable_members':mutation['changed_readable_members'],'category_counts_after':dict(collections.Counter(x['category'] for x in after['entries'])),'active_control_handling':'Two internal controls and the external admission gate are inventoried from owned descriptor identities, without reading locked bytes or manufacturing hashes','no_extension_or_dotfile_exclusion':True,'required_read_failures':after['required_read_failures'],'not_a_production_snapshot_or_complete_byte_certificate':True})
save('PENDING_LEDGER_MUTATION.json',{'child_exit':child['exit_code'],'writer_operation':mutation['writer_operation'],'pending_evidence':pending,'pending_envelope':json.loads(raw),'foreign_registration':'A0_UNENROLLED_REGISTER','foreign_in_pending':True,'foreign_in_main_ledger':False,'main_ledger_before_sha256':mutation['main_ledger_sha256'],'main_ledger_after_sha256':sha(V/'copy/budget.json'),'main_ledger_unchanged':mutation['main_ledger_sha256']==sha(V/'copy/budget.json'),'attempt_arrays_identical':state['attempts']==ledger['attempts'],'attempt_rows':len(ledger['attempts']),'existing_run_contracts_unchanged':all(state['runs'][k]==v for k,v in ledger['runs'].items()),'other_ledger_state_fields_unchanged':all(state[k]==v for k,v in ledger.items() if k!='runs'),'no_new_reservation_or_dispatch':True,'writer_domain_gap_unchanged':True})
save('A0_18_BEFORE_AFTER.json',{'original_A0_18':{'status':'ERROR','error':baseline['original_vector']['error'],'traceback':baseline['original_vector']['traceback'],'exact_failing_pathname':'NOT_CAPTURED_BY_ORIGINAL_TRACE; .a0-L2.lock was only source reconstruction','historical_suite_counts':baseline['original_counts'],'child_exit':0,'child_operation':'RAISED PermissionError/WinError5','pending_created':True,'main_ledger_unchanged':True},'corrected_scoped_rerun':{'status':'PASS','expected_contract':'The exact unenrolled writer must be detected and strong capability refused; no count/claim promotion','actual_controls_executed':1,'child_exit':child['exit_code'],'child_operation':mutation['writer_operation'],'pending_bytes_captured':True,'foreign_registration_detected':True,'added_members':mutation['added_namespace_members'],'required_read_failures':[],'resources_released':cleanup,'strong_profile_supported':False,'A_or_S_authority_awarded':False},'historical_records_not_rewritten':True,'counts':counts})
text('STRONG_PROFILE_LIMITATION.md','''# Strong-profile limitation remains

**A0_COLLECTOR_CORRECTED_STRONG_PROFILE_BLOCKED**

The corrected collector faithfully recorded the known negative control. The actual unchanged Ledger.register child still bypassed the test admission/L1/L2 protocol and wrote budget.json.pending before its attempted replace of the pinned ledger was denied with WinError5. Both the old and new observations retain that writer-domain gap. The existing main ledger and original attempt array remain unchanged; failed replacement is not unchanged directory membership.

The new test's PASS means the expected hazard was detected, the pending bytes and control metadata were captured, and the original negative assertions held. It is not a production snapshot verification, proof of full writer exclusion, safe reentrancy, completed A0 strong feasibility, or A1 readiness. The raw material_blocker remains true. No A/S authority or new v2.1 source certificate is issued. Any prospective U marker describes the aborted test candidate only; independently justified source facts remain limited I, and unsupported observations X.

Active control content was deliberately NOT read while held. Each control retains path, role, native file identity and metadata, with explicit NOT_READ_ACTIVE_LOCK_CONTROL and null byte hash/content. That is faithful A0 evidence handling, not a waiver of frozen production-capture requirements. Unknown names are retained; no global dotfile, .lock or .pending filter is used by this collector. Required-data access errors are recorded with exact pathname/operation/errno/winerror and fail collection rather than becoming PASS.

This scoped rerun exercised the actual new pending member, active known controls, retained unknown fixture members and cleanup. It did not separately inject every possible unknown filename, permission failure, link/reparse condition or storage failure; code handling is not represented as exhaustive runtime coverage. No full all-writer domain was established, and forty-source-class inventory or the absence of an observed external process would not supply that proof.

The approved R1/R3 contract, F01/F02/F03/F04, Engine/Harness/evaluator, algorithms/prompts/settings/ceilings, provider bridge, old tests, original A0 outcomes and recursive-negative scoring remain unchanged. No A1 enrollment, production observer, model/provider call, benchmark, migration or Git publication is authorized by this correction.''')
text('NEXT_SCOPE_RECOMMENDATION.md','''# Next scope recommendation

First review the two-file collector diff, single A0-18 negative-control receipt, native metadata/pending-byte inventory and preservation evidence. The collector correction is complete within this harness scope; it does not close the writer-exclusion question.

Before any strong profile, require a separately reviewed operational/coordination design showing which actual shared-ledger writers, constructors, registration paths, witness/event producers, native consumers and administrative callers are enrolled/excluded/drained. The actual source/API path exercised here remains outside the test domain. If safe exclusion requires protected writer/source/native changes, identify exact symbols, compatibility, lock order and invariants and obtain separate authorization. Do not silently add F01 locks or assume a new outer mutex covers unchanged callers.

Until that proof exists, withhold A/S, graph-wide completeness, complete costs and eligible new v2.1 views. A separately reviewed lower-authority I/X profile may retain justified facts without claiming completion of the strong contract. No implementation of that profile is part of this task.

No A1, production observer, old-test migration, Engine/Harness/evaluator change, commit/push/merge or live/provider/benchmark activity follows automatically from this passing negative control. Do not replace original19PASS/1ERROR with a new20PASS historical result.''')
argv=[sys.executable,'-B',str(H/'targeted_rerun.py'),'--output',str(R)]
save('_control/EXACT_COMMAND.json',{'argv':argv,'environment':{'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1','A0_SOURCE_CHECKOUT':'Set by driver to '+str(A/'checkout')},'shell_output_receipt':str(H/'TARGETED_COMMAND_OUTPUT.txt'),'observed_exit_code':0,'native_permissions':'Authorized native Windows/NTFS execution; no provider/network access'})
text('COLLECTOR_CORRECTION_REPORT.md',f'''# A0-18 collector correction and scoped rerun

**A0_COLLECTOR_CORRECTED_STRONG_PROFILE_BLOCKED**

Exactly one authorized control was executed: A0-18 PASS,0FAIL,0ERROR. Historical attempt_002 remains19PASS/1ERROR; attempt_001 remains10PASS/1FAIL/9NOT_EXECUTED. Four saved recursive-lock negatives remain PASS under their unchanged scoring and were not rerun. No historical total is rewritten or combined with the new one-control result.

## Baseline and exact scope

The original child exited0 after recording a failed Ledger.register replacement (PermissionError/WinError5), while budget.json.pending contained the additional registration and the main ledger stayed unchanged. The original parent then raised Errno13 in snapshot.read_bytes. Its exact failing pathname was not captured; the earlier .a0-L2.lock finding remains explicitly a source reconstruction.

Six saved scaffold files were copied to this new directory's harness/. Only copied probe_workers.py (one new A0-only collection function) and copied test_lock_domain_feasibility.py case18 changed. Every unrelated original function/class and the recursive scoring function was checked unchanged. The original runner, four other copied files and ALL original A0/investigation/source files remain unchanged. No new Git checkout/branch/commit was needed; source reads use the existing pinned783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e checkout without tracked edits.

## Collector behavior

The new case-specific collector recursively inventories all names/types. It distinguishes A operational controls by exact declared paths and owned descriptors, B known historical fixture evidence, C pending/temporary evidence, and D unknown/unexpected members. It does not infer a control from a .lock suffix and does not exclude dotfiles or pending files. Active controls have native identity/metadata and NOT_READ_ACTIVE_LOCK_CONTROL with no fabricated hash or content. Other read failures retain exact path/operation/errno/winerror and make collection incomplete; case18 then fails. Unrelated programming errors still propagate.

Before-state inventory, child receipt, post-state inventory and mutation evidence are persisted outside the candidate input namespace before later assertions. Historical/unknown/pending readable file bytes are retained in base64 plus raw-byte hashes. This is a test evidence record with explicit limits, not a production snapshot or strong-authority API.

## Actual result

Child PID{child['pid']} exited{child['exit_code']}; its writer operation remained RAISED PermissionError/WinError5. Only added namespace member: budget.json.pending. The captured envelope contains A0_UNENROLLED_REGISTER. Its raw SHA256 is {pending['sha256']}; it matches the child's own digest. The main ledger before/after SHA256 is {mutation['main_ledger_sha256']}. Entire attempt arrays are identical with one prior copied row; no new attempt/reservation, dispatch, replay or provider call occurred.

Post inventory categories: {dict(collections.Counter(x['category'] for x in after['entries']))}. The two active internal controls are .a0-L2.lock and .publication.lock; the external ADMISSION.lock is recorded separately. Required read failures:0. New pending bytes are captured; unknown inherited fixture members and all additions remain visible. No new arbitrary unknown-member fault was injected beyond this exact vector; complete generic unknown/error coverage is not claimed.

Cleanup succeeded: all three owned guard descriptors closed, pin handle list emptied, all three guards reacquired/released, and {len(cleanup['write_delete_access_checks'])} native read/write/delete-ACCESS opens of the pinned scratch files succeeded after release without changing their bytes. Ordinary L3 state read after release retained one attempt. The nonowning context's owner/fence/token remained absent and owner bytes unchanged. Worker/parent network and reservation/dispatch tripwires all recorded0. These resource checks are assertions within this one authorized vector, not extra A0 suite controls.

Python: {environment['python']}. Windows: {environment['windows']}. Actual rerun volume {environment['actual_rerun_volume']}, filesystem {environment['filesystem']}, serial {environment['volume_serial']}. Targeted control duration {result['elapsed_seconds']}seconds is observed test duration, not Engine/model performance. Driver exit0 and exact stdout are retained. No dependency install or download.

## Safety, preservation and limits

The raw material_blocker remains true and strong_profile_supported=false. A passing detector does not exclude the unenrolled writer; denied replace did not stop new membership. No A/S award, A1 enrollment, production observer or source/API change. The frozen contract and original writer-domain finding remain intact.

SOURCE_PRESERVATION.json passes the full original source/evidence/Git comparison. It covers all original A0 raw/scoring/scaffolds, investigation documents, protected research, Engine/Harness/evaluator, algorithms/prompts/tasks/settings, F01/F02/F03/F04 and historical assertions. Original tracked files and dirty research/index states are unchanged. Only this new correction directory contains modifications and output. No commit/push/merge occurred.

## Exact scoped reproduction

Do not invoke the copied historical full probe_runner.py or its README's full-suite command. Reproduce ONLY the targeted driver, using a new output path that does not exist:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
& '{sys.executable}' -B '{H/'targeted_rerun.py'}' --output '{E/'runs/independent_001'}'
```

Native Windows permissions are required for the actual NTFS locks/pins; syscall denial is not a PASS. The driver fixes A0_SOURCE_CHECKOUT to the immutable original source location, verifies all246 implementation-manifest entries and captures the six executed harness hashes plus a two-file diff. EXACT_COMMAND.json and TARGETED_COMMAND_OUTPUT.txt preserve the actual executed command/exit/output. No independent reproduction was run beyond the one recorded control.

The next decision is review of this negative-control correction and a separately scoped all-writer exclusion strategy. Strong feasibility remains blocked; no scientific performance claim or human approval is made.''')
print(json.dumps({'verdict':'A0_COLLECTOR_CORRECTED_STRONG_PROFILE_BLOCKED','actual_controls':1,'PASS':1,'historical_counts_unchanged':True,'NTFS':fs.value,'pending_sha256':pending['sha256'],'preservation':pres['passed']}))
