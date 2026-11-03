"""Preserve all previous research and evidence; copy only six A0 scaffolds."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;E=H.parent;A=Path('E:/The End Engine/v21_A0_feasibility');I=Path('E:/The End Engine/v21_A0_blocker_investigation');C=A/'checkout';W=Path('E:/END-v102-V21-Contract-Checkpoint');R=Path('E:/END-Cognitive-Architectures-Fix-v102')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def git(p,*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),'-c','safe.directory='+p.as_posix(),*args],text=True).strip()
def states():return {str(p):{'HEAD':git(p,'rev-parse','HEAD'),'branch':git(p,'branch','--show-current'),'status':git(p,'status','--porcelain=v1'),'staged':git(p,'diff','--cached','--name-status')} for p in (C,W,R,Path('E:/END-v102-WIP-Checkpoint-20261019'))}
def snapshot():
 prior=json.loads((I/'_evidence/BEFORE.json').read_text(encoding='utf-8'));maps={}
 for label,files in prior.items():maps[label]={p:sha(Path(p)) for p in files};print(label+': '+str(len(files)),flush=True)
 maps['investigation_all_files']={str(p):sha(p) for p in I.rglob('*') if p.is_file()}
 return maps
if __name__=='__main__':
 if sys.argv[1]=='before':
  assert not (H/'BEFORE.json').exists()
  old=json.loads((A/'_control/EVIDENCE_FILE_HASHES.json').read_text(encoding='utf-8'));assert all(sha(A/n)==v['sha256'] for n,v in old['files'].items())
  inv=json.loads((I/'_evidence/INVESTIGATION_FILE_HASHES.json').read_text(encoding='utf-8'));assert all(sha(I/n)==v['sha256'] for n,v in inv['files'].items())
  raw=A/'runs/attempt_002';result=json.loads((raw/'RUN_RESULT.json').read_text(encoding='utf-8'));assert result['counts']=={'PASS':19,'FAIL':0,'ERROR':1,'NOT_EXECUTED':0}
  q=next((raw/'A0-18').glob('*.request.result.json'));child=json.loads(q.read_text(encoding='utf-8'));assert child['events'][0]['winerror']==5 and child['events'][-1]['pending_created'] and child['events'][-1]['ledger_before']==child['events'][-1]['ledger_after']
  receipt=json.loads((raw/'EXECUTED_SOURCE_RECEIPT.json').read_text(encoding='utf-8'));assert all(sha(C/n)==v['sha256'] for n,v in receipt['unchanged_implementation_sources'].items())
  for n,h in receipt['new_scaffolding_files'].items():
   src=raw/'executed_scaffolding'/n;assert sha(src)==h;dest=E/'harness'/n;assert not dest.exists();shutil.copyfile(src,dest);assert sha(dest)==h
  save(H/'PRE_CORRECTION_BASELINE.json',{'original_counts':result['counts'],'original_vector':json.loads((raw/'A0-18/VECTOR_RESULT.json').read_text(encoding='utf-8')),'original_child_result':child,'source_commit':states()[str(C)]['HEAD'],'original_scaffolding':receipt['new_scaffolding_files'],'copied_files':6,'original_failing_filename':'NOT_RECORDED_IN_TRACE; .a0-L2.lock is source reconstruction only','production_source_manifest_entries':len(receipt['unchanged_implementation_sources'])});save(H/'GIT_BEFORE.json',states());print('Pre-correction identities verified; six files copied unchanged',flush=True);save(H/'BEFORE.json',snapshot())
 else:
  before=json.loads((H/'BEFORE.json').read_text(encoding='utf-8'));after=snapshot();changed={k:[p for p in set(v)|set(after[k]) if v.get(p)!=after[k].get(p)] for k,v in before.items()};assert not any(changed.values()),changed;assert states()==json.loads((H/'GIT_BEFORE.json').read_text(encoding='utf-8'))
  membership={}
  for label,root,expected in [('original_A0',A,set(before['all_original_A0_evidence_including_scoring_and_six_files'])|set(before['checkout_tracked'])|set(before['six_current_A0_scaffold_files'])),('original_investigation',I,set(before['investigation_all_files'])),('approved_checkpoint',W,set(before['v21_checkpoint'])),('original_correction',R,set(before['correction'])|set(before['original_v21']))]:
   actual={str(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts};membership[label]={'added':sorted(actual-expected),'removed':sorted(expected-actual)};assert not any(membership[label].values()),membership[label]
  save(E/'SOURCE_PRESERVATION.json',{'passed':True,'changed':changed,'membership_delta':membership,'counts':{k:len(v) for k,v in before.items()},'original_Git_states_unchanged':True,'git_states':states(),'original_A0_evidence_and_scaffolding_unchanged':True,'historical_scores_and_assertions_unchanged':True,'production_source_changes':0,'Engine_Harness_evaluator_algorithms_prompts_F01_F02_F03_F04_preserved':True,'engine_fingerprint_preserved':'29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82','frozen_evaluator_payload_root_preserved_by_per_file_hashes':'23a923ebb224a162ba98c673a9f4f97e8c0571807a893ed72d6a07d65f181a09','commit_push_merge':False});print('Collector correction preservation PASS',flush=True)
