"""Design-task administrative hashing only; never imports project runtime code."""
import hashlib,json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('E:/The End Engine')
PREVIOUS=BASE/'v21_minimum_evidence_feasibility'
def save(path,x):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def members(path):return sorted(str(p) for p in path.rglob('*') if p.is_file() and '.git' not in p.relative_to(path).parts)
def state(path):
 def g(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(path),'-c','safe.directory='+path.as_posix(),*a],text=True).strip()
 return {k:g(*a) for k,a in [('HEAD',('rev-parse','HEAD')),('branch',('branch','--show-current')),('status',('status','--porcelain=v1')),('staged',('diff','--cached','--name-status')),('tracked_diff',('diff','--binary','--no-ext-diff'))]}
def capture():
 prior=json.loads((PREVIOUS/'_control/BEFORE.json').read_text(encoding='utf-8'))['maps'];sets={k:set(v) for k,v in prior.items()}
 sets['all_latest_feasibility_evidence']=set(members(PREVIOUS));paths=set().union(*sets.values());print('Reading SHA-256 for',len(paths),'protected files',flush=True)
 with ThreadPoolExecutor(max_workers=16) as pool:cache=dict(pool.map(lambda name:(name,sha(name)),sorted(paths)))
 git={str(p):state(p) for p in [BASE,BASE/'v21_A0_feasibility/checkout',Path('E:/END-v102-V21-Contract-Checkpoint'),Path('E:/END-Cognitive-Architectures-Fix-v102'),Path('E:/END-v102-WIP-Checkpoint-20261019')]}
 return {'maps':{k:{n:cache[n] for n in sorted(v)} for k,v in sets.items()},'git_states':git,'unique_files':len(paths)}
if __name__=='__main__':
 mode=sys.argv[1];path=ROOT/'_control/BEFORE.json'
 if mode=='before':
  assert not path.exists();x=capture();prior=json.loads((PREVIOUS/'_control/BEFORE.json').read_text(encoding='utf-8'))['maps'];changes={k:[n for n,h in v.items() if x['maps'][k].get(n)!=h] for k,v in prior.items()};assert not any(changes.values()),changes
  m=json.loads((PREVIOUS/'_control/FILE_HASHES.json').read_text(encoding='utf-8'));assert all(sha(PREVIOUS/n)==v['sha256'] for n,v in m['files'].items());save(path,x);save(ROOT/'_control/INPUT_INTEGRITY.json',{'passed':True,'previous_feasibility_manifest_entries':len(m['files']),'previous_manifest_sha256':sha(PREVIOUS/'_control/FILE_HASHES.json'),'prior_inventory_delta':changes});print('BEFORE_VERIFIED',flush=True)
 else:
  old=json.loads(path.read_text(encoding='utf-8'));new=capture();changes={k:sorted(n for n in set(v)|set(new['maps'][k]) if v.get(n)!=new['maps'][k].get(n)) for k,v in old['maps'].items()};same=old['git_states']==new['git_states'];passed=not any(changes.values()) and same;save(ROOT/'SOURCE_PRESERVATION.json',{'passed':passed,'unique_protected_files':new['unique_files'],'counts':{k:len(v) for k,v in new['maps'].items()},'changed':changes,'git_states_unchanged':same,'git_states':new['git_states'],'method':'Full byte SHA-256 plus complete prior evidence membership; read-only Git identities/status/diffs before and after design analysis','production_imports_or_experiments_executed':False,'tests_executed':0,'provider_calls':0,'protected_source_changes':0,'historical_result_changes':0,'git_commit_push_merge_release':False,'new_output_boundary':str(ROOT)});print('PRESERVATION',passed,flush=True);assert passed
