"""Read-only evidence/source analysis. Never imports or executes A0 or runtime code."""
import ast,csv,hashlib,json,re,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent;A=Path('E:/The End Engine/v21_A0_feasibility');C=A/'checkout';W=Path('E:/END-v102-V21-Contract-Checkpoint');R=Path('E:/END-Cognitive-Architectures-Fix-v102')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def git(p,*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),'-c','safe.directory='+p.as_posix(),*a],text=True).strip()
def states():
 return {str(p):{'HEAD':git(p,'rev-parse','HEAD'),'branch':git(p,'branch','--show-current'),'status':git(p,'status','--porcelain=v1'),'staged':git(p,'diff','--cached','--name-status')} for p in (C,W,R,Path('E:/END-v102-WIP-Checkpoint-20261019'))}
def snapshot():
 source= json.loads((A/'_control/BEFORE.json').read_text(encoding='utf-8'));maps={}
 for label,files in source.items():
  maps[label]={p:sha(Path(p)) for p in files};print(label+': '+str(len(files)),flush=True)
 maps['all_original_A0_evidence_including_scoring_and_six_files']={str(p):sha(p) for p in A.rglob('*') if p.is_file() and not p.is_relative_to(C)}
 feasibility=C/'experimental_architectures_v1_r3/feasibility_v21';maps['six_current_A0_scaffold_files']={str(p):sha(p) for p in feasibility.rglob('*') if p.is_file()}
 return maps
def source_blocks(path,names):
 text=path.read_text(encoding='utf-8-sig');tree=ast.parse(text);out={}
 def walk(node,prefix=''):
  for n in ast.iter_child_nodes(node):
   if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
    key=prefix+n.name
    if key in names:out[key]={'line':n.lineno,'end_line':n.end_lineno,'source':ast.get_source_segment(text,n)}
    walk(n,key+'.')
   else:walk(n,prefix)
 walk(tree);assert set(out)==set(names),(path,names,set(out));return out
def inspect():
 old= json.loads((A/'_control/EVIDENCE_FILE_HASHES.json').read_text(encoding='utf-8'));assert all(sha(A/n)==v['sha256'] for n,v in old['files'].items())
 scoring=A/'scoring_clarification_20261021';receipt=json.loads((scoring/'SCORING_RECEIPT.json').read_text(encoding='utf-8'));assert all(sha(scoring/n)==v['sha256'] for n,v in receipt['files'].items())
 scores=json.loads((scoring/'A0_NEGATIVE_CONTROL_SCORING.json').read_text(encoding='utf-8'));assert len(scores['records'])==4 and all(x['control_verdict']=='PASS' for x in scores['records'])
 raw=A/'runs/attempt_002';request=next((raw/'A0-18').glob('*.request.json'));child=json.loads(request.with_suffix('.result.json').read_text(encoding='utf-8'));exit_record=json.loads(request.with_suffix('.exit.json').read_text(encoding='utf-8'));vector=json.loads((raw/'A0-18/VECTOR_RESULT.json').read_text(encoding='utf-8'));run=json.loads((raw/'RUN_RESULT.json').read_text(encoding='utf-8'));clone=raw/'A0-18/copy'
 original=json.loads((raw/'EXECUTED_SOURCE_RECEIPT.json').read_text(encoding='utf-8'));assert all(sha(raw/'executed_scaffolding'/n)==h for n,h in original['new_scaffolding_files'].items())
 pending=clone/'budget.json.pending';ledger=clone/'budget.json';pe=json.loads(pending.read_text(encoding='utf-8'));le=json.loads(ledger.read_text(encoding='utf-8'));events=child['events'];fact=events[-1]
 assert sha(pending)==fact['pending_sha256'] and sha(ledger)==fact['ledger_before']==fact['ledger_after'];assert 'A0_UNENROLLED_REGISTER' in pe['state']['runs'] and 'A0_UNENROLLED_REGISTER' not in le['state']['runs'];assert len(pe['state']['attempts'])==len(le['state']['attempts'])==fact['attempt_rows_after']==1
 sorted_files=[p for p in sorted(clone.rglob('*')) if p.is_file()];assert sorted_files[0].name=='.a0-L2.lock'
 native_ids={}
 pin_source=json.loads((raw/'A0-10/VECTOR_RESULT.json').read_text(encoding='utf-8'))
 paths={'saved_test':raw/'executed_scaffolding/test_lock_domain_feasibility.py','saved_workers':raw/'executed_scaffolding/probe_workers.py','saved_runner':raw/'executed_scaffolding/probe_runner.py','Ledger':C/'cognitive_architecture_lab_v1/src/accounting/ledger.py','publication':C/'experimental_architectures_v1_r3/src/shared/publication.py','transport':C/'runtime_isolation_v1/src/trusted_transport/transport.py','pins':C/'experimental_architectures_v1_r3/src/shared/publication_guard.py'}
 wanted={'saved_test':['case18','case17','case10','case11','recursive'],'saved_workers':['snapshot','ExistingLock.__enter__','ExistingLock.__exit__','Pins.__enter__','Pins.__exit__','spawn','collect','perform','clone_fixture','protected_core'],'saved_runner':['main'],'Ledger':['Ledger.lock','Ledger.register','Ledger._read','Ledger._write'],'publication':['Publication.lock','Publication._take_lease','Publication.release','Publication._verify_completed','Publication.verify_semantics','Publication.publish'],'transport':['dispatch_lock'],'pins':['EvidencePin.inventory','EvidencePin.pin']}
 blocks={key:{'path':str(path),'sha256':sha(path),'symbols':source_blocks(path,wanted[key])} for key,path in paths.items()}
 save(H/'EXACT_SOURCE_BLOCKS.json',blocks)
 result={'raw_A0_18':vector,'raw_child_request':json.loads(request.read_text(encoding='utf-8')),'raw_child_result':child,'raw_child_exit':exit_record,'run_counts':run['counts'],'raw_error_has_filename':False,'first_candidate_data_path_by_exact_sorted_iteration':str(sorted_files[0]),'first_path_classification':'existing test L2 operational guard, excluded by data_paths() and actively byte-locked by parent','filename_evidence_limit':'The trace records Errno13 at f.read without filename. First-path identification is deterministic source/preserved-membership reconstruction, not a newly captured syscall filename or rerun.','sorted_preserved_membership':[p.relative_to(clone).as_posix() for p in sorted_files],'pending_sha256':sha(pending),'ledger_sha256':sha(ledger),'ledger_state_sha256_before_after_equal':True,'pending_added_run':'A0_UNENROLLED_REGISTER','attempt_rows_unchanged':True,'pending_state_checksum_valid':hashlib.sha256(json.dumps(pe['state'],sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()==pe['state_sha256'],'source_file_refs':{key:{'path':v['path'],'sha256':v['sha256'],'lines':{n:r['line'] for n,r in v['symbols'].items()}} for key,v in blocks.items()},'four_negative_controls':scores['records'],'existing_A0_manifest_members_verified':len(old['files']),'current_source_is_same_as_executed_manifest':all(sha(C/n)==v['sha256'] for n,v in original['unchanged_implementation_sources'].items()),'new_tests_or_concurrency_experiments':0,'source_or_scaffold_imports':0}
 assert result['pending_state_checksum_valid'] and result['current_source_is_same_as_executed_manifest']
 save(H/'RAW_CAUSAL_EVIDENCE.json',result);print(json.dumps({'old_manifest_members':len(old['files']),'child_exit':exit_record['exit_code'],'parent_status':vector['status'],'ledger_unchanged':True,'new_pending_run':'A0_UNENROLLED_REGISTER','source_reconstructed_failing_path':str(sorted_files[0]),'new_test_runs':0}),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='before':
  assert not (H/'BEFORE.json').exists();inspect();save(H/'GIT_BEFORE.json',states());save(H/'BEFORE.json',snapshot())
 else:
  before=json.loads((H/'BEFORE.json').read_text(encoding='utf-8'));after=snapshot();delta={k:[p for p in set(v)|set(after[k]) if v.get(p)!=after[k].get(p)] for k,v in before.items()};state=states();assert state==json.loads((H/'GIT_BEFORE.json').read_text(encoding='utf-8'));assert not any(delta.values()),delta
  membership={}
  for label,root,expected in [('original_A0_evidence',A,set(before['all_original_A0_evidence_including_scoring_and_six_files'])|set(before['checkout_tracked'])|set(before['six_current_A0_scaffold_files'])),('approved_checkpoint',W,set(before['v21_checkpoint'])),('original_correction',R,set(before['correction'])|set(before['original_v21']))]:
   actual={str(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts};membership[label]={'added':sorted(actual-expected),'removed':sorted(expected-actual)};assert not any(membership[label].values()),membership[label]
  save(D/'PRESERVATION_REPORT.json',{'passed':True,'mode':'READ_ONLY_EVIDENCE_ANALYSIS_AND_REMEDIATION_PLANNING','new_test_runs':0,'new_concurrency_experiments':0,'changed':delta,'membership_delta':membership,'counts':{k:len(v) for k,v in before.items()},'git_states_before_equal_after':True,'git_states':state,'source_implementation_scaffold_contract_evidence_scoring_modified':False,'provider_calls':0,'live_inference':0,'benchmarks':0,'commit_push_merge_rebase_tag_release':False,'engine_fingerprint_preserved':'29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82','frozen_evaluator_root_covered_by_prior_source_file_inventory':'23a923ebb224a162ba98c673a9f4f97e8c0571807a893ed72d6a07d65f181a09','no_evaluator_or_Engine_execution':True});print('Investigation preservation PASS',flush=True)
