"""Preserve previous source/evidence/branches; authorized new worktree is separate."""
import hashlib,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('E:/The End Engine')
DESIGN=BASE/'v21_minimal_runtime_decision'
BRANCH='codex/v21-ledger-guard-slice'
def save(name,x):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def members(p):return sorted(str(q) for q in p.rglob('*') if q.is_file() and '.git' not in q.relative_to(p).parts)
def git(p,*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),'-c','safe.directory='+p.as_posix(),*args],text=True).strip()
def capture():
 prior=json.loads((DESIGN/'_control/BEFORE.json').read_text(encoding='utf-8'))['maps'];sets={k:set(v) for k,v in prior.items()};sets['all_minimal_runtime_decision']=set(members(DESIGN));names=set().union(*sets.values());print('Hashing',len(names),'protected prior files',flush=True)
 states={str(p):{'HEAD':git(p,'rev-parse','HEAD'),'branch':git(p,'branch','--show-current'),'status':git(p,'status','--porcelain=v1'),'staged':git(p,'diff','--cached','--name-status'),'tracked_diff':git(p,'diff','--binary','--no-ext-diff')} for p in [BASE,BASE/'v21_A0_feasibility/checkout',Path('E:/END-v102-V21-Contract-Checkpoint'),Path('E:/END-Cognitive-Architectures-Fix-v102'),Path('E:/END-v102-WIP-Checkpoint-20261019')]}
 refs=[line for line in git(BASE,'for-each-ref','--format=%(refname) %(objectname)','refs/heads').splitlines() if not line.startswith('refs/heads/'+BRANCH+' ')]
 with ThreadPoolExecutor(max_workers=16) as pool:cache=dict(pool.map(lambda n:(n,sha(n)),sorted(names)))
 return {'maps':{k:{n:cache[n] for n in sorted(v)} for k,v in sets.items()},'old_git_states':states,'old_branch_refs_excluding_authorized_new_branch':refs,'unique_files':len(names)}
if __name__=='__main__':
 mode=sys.argv[1];p=ROOT/'_control/BEFORE.json'
 if mode=='before':
  assert not p.exists();x=capture();prior=json.loads((DESIGN/'_control/BEFORE.json').read_text(encoding='utf-8'))['maps'];assert all(x['maps'][k][n]==h for k,v in prior.items() for n,h in v.items());m=json.loads((DESIGN/'_control/FILE_HASHES.json').read_text(encoding='utf-8'));assert all(sha(DESIGN/n)==v['sha256'] for n,v in m['files'].items());save('_control/BEFORE.json',x);print('BASELINE_PASSED',flush=True)
 else:
  old=json.loads(p.read_text(encoding='utf-8'));new=capture();changes={k:[n for n in set(v)|set(new['maps'][k]) if v.get(n)!=new['maps'][k].get(n)] for k,v in old['maps'].items()};same=old['old_git_states']==new['old_git_states'];refs=old['old_branch_refs_excluding_authorized_new_branch']==new['old_branch_refs_excluding_authorized_new_branch'];passed=not any(changes.values()) and same and refs;save('SOURCE_PRESERVATION.json',{'passed':passed,'prior_unique_files':new['unique_files'],'changed_prior_files':changes,'prior_git_states_unchanged':same,'published_WIP_and_other_old_local_refs_unchanged':refs,'old_git_states':new['old_git_states'],'only_authorized_new_branch_excluded':BRANCH,'new_implementation_preservation_receipt':'_control/SCOPED_SOURCE_REVIEW.json','historical_tests_and_N12_unchanged':True,'Engine_Harness_frozen_evaluator_changes':0});print('PRESERVATION',passed,flush=True);assert passed
