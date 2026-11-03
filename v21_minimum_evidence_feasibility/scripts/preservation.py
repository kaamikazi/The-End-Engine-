"""Read-only byte inventories with concurrent reads; writes only new receipts."""
import hashlib,json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('E:/The End Engine')
REVIEW=BASE/'v21_A0_independent_decision'
PROTECTED=[BASE/x for x in ('v21_A0_feasibility','v21_A0_blocker_investigation','v21_A0_collector_correction','v21_A0_independent_decision')]
def save(name,data):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def members(root):return sorted(str(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts)
def git_state(p):
 def g(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),'-c','safe.directory='+p.as_posix(),*a],text=True).strip()
 return {k:g(*a) for k,a in [('HEAD',('rev-parse','HEAD')),('branch',('branch','--show-current')),('status',('status','--porcelain=v1')),('staged',('diff','--cached','--name-status')),('tracked_diff',('diff','--binary','--no-ext-diff'))]}
def capture():
 prior=json.loads((REVIEW/'_control/BEFORE.json').read_text(encoding='utf-8'))['maps'];sets={k:set(v) for k,v in prior.items()}
 for root in PROTECTED:sets['all_'+root.name]=set(members(root))
 sets['main_Engine']={str(p) for p in (BASE/'end_engine').rglob('*.py')}|{str(BASE/'pyproject.toml')}
 allpaths=set().union(*sets.values());print('Hashing',len(allpaths),'protected files',flush=True)
 with ThreadPoolExecutor(max_workers=16) as pool:cache=dict(pool.map(lambda n:(n,sha(n)),sorted(allpaths)))
 states={str(p):git_state(p) for p in [BASE,PROTECTED[0]/'checkout',Path('E:/END-v102-V21-Contract-Checkpoint'),Path('E:/END-Cognitive-Architectures-Fix-v102'),Path('E:/END-v102-WIP-Checkpoint-20261019')]}
 return {'maps':{k:{n:cache[n] for n in sorted(v)} for k,v in sets.items()},'git_states':states,'unique_files':len(allpaths)}
def main(mode):
 before_path=ROOT/'_control/BEFORE.json'
 if mode=='before':
  assert not before_path.exists();x=capture()
  prior=json.loads((REVIEW/'_control/BEFORE.json').read_text(encoding='utf-8'))['maps'];delta={k:[n for n,h in v.items() if x['maps'][k].get(n)!=h] for k,v in prior.items()};assert not any(delta.values()),delta
  m=json.loads((REVIEW/'_control/REVIEW_FILE_HASHES.json').read_text(encoding='utf-8'));assert all(sha(REVIEW/n)==e['sha256'] for n,e in m['files'].items())
  assert x['git_states'][str(PROTECTED[0]/'checkout')]['HEAD']=='783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e'
  save('_control/BEFORE.json',x);save('_control/BASELINE_VERIFICATION.json',{'passed':True,'prior_inventory_delta':delta,'independent_review_manifest_entries':len(m['files']),'independent_review_manifest_sha256':sha(REVIEW/'_control/REVIEW_FILE_HASHES.json'),'source_commit':x['git_states'][str(PROTECTED[0]/'checkout')]['HEAD']});print('BASELINE_VERIFIED',flush=True)
 else:
  before=json.loads(before_path.read_text(encoding='utf-8'));after=capture();changes={k:sorted(n for n in set(v)|set(after['maps'][k]) if v.get(n)!=after['maps'][k].get(n)) for k,v in before['maps'].items()};same=before['git_states']==after['git_states'];passed=not any(changes.values()) and same
  save('SOURCE_PRESERVATION.json',{'passed':passed,'unique_protected_files':after['unique_files'],'counts':{k:len(v) for k,v in before['maps'].items()},'changed':changes,'git_states_unchanged':same,'git_states':after['git_states'],'original_source_and_evidence_roots':list(map(str,PROTECTED)),'new_write_boundary':str(ROOT),'production_changes':0,'Engine_Harness_frozen_evaluator_changes':0,'old_tests_and_historical_results_edited':False,'commit_push_merge_release':False});print('PRESERVATION',passed,flush=True);assert passed
if __name__=='__main__':main(sys.argv[1])
