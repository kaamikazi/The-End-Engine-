"""Administrative output consistency and hashes; no further test execution."""
import base64,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;E=H.parent;A=Path('E:/The End Engine/v21_A0_feasibility');R=E/'runs/attempt_001';V=R/'A0-18'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
required=['COLLECTOR_CORRECTION_REPORT.md','A0_18_BEFORE_AFTER.json','A0_18_RAW_RERUN.json','NAMESPACE_INVENTORY.json','PENDING_LEDGER_MUTATION.json','SOURCE_PRESERVATION.json','STRONG_PROFILE_LIMITATION.md','NEXT_SCOPE_RECOMMENDATION.md']
checks=[]
def check(name,value):checks.append({'check':name,'passed':bool(value)});assert value,name
check('all8 requested deliverables present',all((E/n).is_file() and (E/n).stat().st_size for n in required))
raw=read(R/'TARGETED_RESULT.json');check('one actual expected-negative PASS, strong profile blocked',raw['executed_controls']==1 and raw['status']=='PASS' and raw['material_blocker'] and raw['strong_profile_supported'] is False and raw['A_or_S_awarded'] is False)
historical=read(A/'runs/attempt_002/RUN_RESULT.json');check('historical19PASS1ERROR unchanged',historical['counts']=={'PASS':19,'FAIL':0,'ERROR':1,'NOT_EXECUTED':0})
pre=read(V/'PRE_NAMESPACE_INVENTORY.json');post=read(V/'POST_NAMESPACE_INVENTORY.json');index={x['relative_path']:x for x in post['entries']};before={x['relative_path']:x for x in pre['entries']}
check('all actual namespace members retained',set(index)=={p.relative_to(V/'copy').as_posix() for p in (V/'copy').rglob('*')})
check('new pending member included as evidence',set(index)-set(before)=={'budget.json.pending'} and index['budget.json.pending']['category']=='C_PENDING_TEMPORARY_EVIDENCE')
for row in post['entries']:
 if row['read_status']=='BYTES_CAPTURED':check('raw captured digest '+row['relative_path'],hashlib.sha256(base64.b64decode(row['raw_base64'],validate=True)).hexdigest()==row['sha256']==sha(Path(row['path'])))
controls=[x for x in post['entries']+post['external_active_controls'] if x.get('active')]
check('three active controls inventoried without fake byte hashes',len(controls)==3 and all(x['category']=='A_OPERATIONAL_CONTROL' and x['read_status']=='NOT_READ_ACTIVE_LOCK_CONTROL' and x['sha256'] is None and x['raw_base64'] is None and x['descriptor_is_owned'] for x in controls))
check('unknown members retained without fabricated control role',any(x['category']=='D_UNKNOWN_UNEXPECTED_MEMBER' for x in post['entries']))
check('no required read errors hidden',post['required_read_failures']==[] and pre['required_read_failures']==[])
mutation=read(E/'PENDING_LEDGER_MUTATION.json');check('child completion distinct from failed writer operation',mutation['child_exit']==0 and mutation['writer_operation']['outcome']=='RAISED' and mutation['writer_operation']['winerror']==5)
check('foreign pending registration captured, main ledger unchanged, no attempt mutation',mutation['foreign_in_pending'] and not mutation['foreign_in_main_ledger'] and mutation['main_ledger_unchanged'] and mutation['attempt_arrays_identical'] and mutation['attempt_rows']==1 and mutation['other_ledger_state_fields_unchanged'])
cleanup=read(V/'RESOURCE_RELEASE_RECEIPT.json');check('own guards/pins released and access checked',cleanup['owned_guard_fds_closed'] and cleanup['pin_handles_closed'] and len(cleanup['guard_reacquisitions'])==3 and len(cleanup['write_delete_access_checks'])==22 and cleanup['existing_L3_read_after_release_attempt_rows']==1)
check('protected source evidence and Git states preserved',read(E/'SOURCE_PRESERVATION.json')['passed'] and read(E/'SOURCE_PRESERVATION.json')['original_Git_states_unchanged'])
source=read(R/'EXECUTED_HARNESS_RECEIPT.json');check('only two copied harness files changed, old scoring definitions intact',set(source['changed_files'])=={'probe_workers.py','test_lock_domain_feasibility.py'} and source['all_unrelated_original_definitions_unchanged'] and source['recursive_negative_scoring_unchanged'])
check('executed copied harness equals current reviewed files',all(sha(E/'harness'/n)==h==sha(R/'executed_harness'/n) for n,h in source['corrected_six_hashes'].items()))
check('parent and child tripwires zero',not any(raw['parent_tripwire_counters'].values()) and not any(read(V/'CHILD_COLLECTION_RECEIPT.json')['worker_result']['counters'].values()))
receipt={'scope':'Administrative evidence checks only; no additional A0 control execution','passed':True,'checks':checks,'actual_new_control_counts':{'executed':1,'PASS':1,'FAIL':0,'ERROR':0},'historical_counts_unchanged':historical['counts'],'verdict':'A0_COLLECTOR_CORRECTED_STRONG_PROFILE_BLOCKED','A1_or_A_S_authorized_or_awarded':False}
(H/'FINAL_EVIDENCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
manifest={p.relative_to(E).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in E.rglob('*') if p.is_file() and p.name!='EVIDENCE_FILE_HASHES.json'}
(H/'EVIDENCE_FILE_HASHES.json').write_text(json.dumps({'files':manifest,'self_excluded':True,'original_evidence_not_modified':True,'publication':'NONE'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verdict':receipt['verdict'],'required_reports':len(required),'administrative_checks':len(checks),'executed_controls':1,'control_PASS':1,'preservation':'PASS','manifest_files':len(manifest),'manifest_sha256':sha(H/'EVIDENCE_FILE_HASHES.json')}))
