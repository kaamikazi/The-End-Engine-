"""Administrative report consistency/manifest only. No tests or runtime imports."""
import csv,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent;A=Path('E:/The End Engine/v21_A0_feasibility')
required=['A0_BLOCKER_ROOT_CAUSE.md','WRITER_DOMAIN_MUTATION_TIMELINE.md','A0_18_COLLECTOR_ERROR_ANALYSIS.md','SOURCE_AND_LOCK_INVOLVEMENT.csv','REMEDIATION_OPTIONS.md','MINIMUM_FOLLOWUP_TEST_PLAN.md','SCOPE_AUTHORIZATION_REQUIRED.md','PRESERVATION_REPORT.json','FINAL_DIAGNOSTIC_VERDICT.md']
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,value):checks.append({'check':name,'passed':bool(value)});assert value,name
check('all9 required reports present',all((D/n).is_file() and (D/n).stat().st_size for n in required))
pres=read(D/'PRESERVATION_REPORT.json');check('original source/evidence/scoring/Git states preserved',pres['passed'] and pres['git_states_before_equal_after'] and not any(pres['changed'].values()) and not any(any(x.values()) for x in pres['membership_delta'].values()))
check('no new probe or runtime execution',pres['new_test_runs']==0 and pres['new_concurrency_experiments']==0 and pres['no_evaluator_or_Engine_execution'])
raw=read(H/'RAW_CAUSAL_EVIDENCE.json');check('child exit0 distinct from parent ERROR',raw['raw_child_exit']['exit_code']==0 and raw['raw_A0_18']['status']=='ERROR' and raw['run_counts']=={'PASS':19,'FAIL':0,'ERROR':1,'NOT_EXECUTED':0})
check('child errorWin5 distinct parentErrno13',raw['raw_child_result']['events'][0]['winerror']==5 and '[Errno 13]' in raw['raw_A0_18']['error'])
check('first-control filename reconstructed, not invented trace field',raw['raw_error_has_filename'] is False and raw['first_candidate_data_path_by_exact_sorted_iteration'].endswith('.a0-L2.lock') and 'reconstruction' in raw['filename_evidence_limit'])
delta=read(H/'STATE_DELTA.json');check('exact pending registration delta, all attempts/other state unchanged',delta['added_run_keys']==['A0_UNENROLLED_REGISTER'] and not delta['removed_run_keys'] and not delta['existing_run_contracts_changed'] and not delta['other_state_fields_changed'] and delta['attempt_arrays_identical'])
source=A/'scoring_clarification_20261021/A0_NEGATIVE_CONTROL_SCORING.json';copy=H/'NEGATIVE_SCORING_VERBATIM.json';check('negative scoring bytes verbatim',source.read_bytes()==copy.read_bytes())
scores=read(copy);fields=['observed_event','expected_event','elapsed_time','bound_satisfied','control_verdict','feasibility_implication'];check('all4 bounded negatives retain six fields and original PASS',len(scores['records'])==4 and all(all(k in r for k in fields) and r['control_verdict']=='PASS' for r in scores['records']))
old=read(A/'_control/EVIDENCE_FILE_HASHES.json');check('all721 prior manifested members still byte-identical',len(old['files'])==721 and all(sha(A/n)==v['sha256'] for n,v in old['files'].items()))
table=list(csv.DictReader((D/'SOURCE_AND_LOCK_INVOLVEMENT.csv').open(encoding='utf-8',newline='')));check('18 source/lock causal roles with exact source hashes',len(table)==18 and all(sha(Path(r['source_file']))==r['source_sha256'] for r in table))
check('selected diagnostic verdict appears explicitly','**A0_STRONG_PROFILE_NOT_SUPPORTED**' in (D/'FINAL_DIAGNOSTIC_VERDICT.md').read_text(encoding='utf-8'))
result={'scope':'READ_ONLY_DIAGNOSTIC_DOCUMENT_CONSISTENCY; not A0 control acceptance','passed':True,'checks':checks,'diagnostic_verdict':'A0_STRONG_PROFILE_NOT_SUPPORTED','original_A0_verdict':'A0_FEASIBILITY_BLOCKED_UNCHANGED','original_latest_results':'19PASS/1ERROR_UNCHANGED','new_probe_executions':0,'implementation_or_scaffold_changes':0,'A1_authorization':False,'required_reports':len(required)}
(H/'FINAL_INVESTIGATION_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
manifest={p.relative_to(D).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in D.rglob('*') if p.is_file() and p.name!='INVESTIGATION_FILE_HASHES.json'}
(H/'INVESTIGATION_FILE_HASHES.json').write_text(json.dumps({'files':manifest,'self_excluded':True,'no_original_evidence_modified':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'diagnostic_verdict':result['diagnostic_verdict'],'required_reports':len(required),'administrative_checks':len(checks),'new_tests':0,'preservation':'PASS','manifest_files':len(manifest)}))
