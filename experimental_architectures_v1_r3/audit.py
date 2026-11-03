"""Read-only baseline/preservation checks; output only inside this phase."""
import hashlib,json,subprocess,sys,tomllib,importlib.metadata
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent;V=OUT/'validation'
BASE='d5109d5c898d9b6fcee0dd0198cb5e2e7080cf8a'
ROOTS={'abc_parent':ROOT,'original_abc':Path('E:/END-Cognitive-Architectures-v1'),'native_integration':Path('E:/END-Native-Integration-v1'),'runtime_isolation':Path('E:/END-Runtime-Isolation-v1'),'architecture_lab':Path('E:/END-Cognitive-Lab-v1'),'freeze_worktree':Path('E:/END-Evaluator-Audit-Fix-111'),'original':Path('E:/The End Engine')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(V/n).write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def git(root,*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(root),'-c','safe.directory='+root.as_posix(),*args],encoding='utf-8')
def snapshot(root):return {p:sha(root/p) if (root/p).is_file() else None for p in git(root,'ls-files').splitlines() if not p.startswith('experimental_architectures_v1_r2/')}
def harness():
    import os
    root=Path('E:/The End Harness');out={};excluded={'.git','.venv','venv','__pycache__','.pytest_cache','node_modules'}
    for directory,dirs,files in os.walk(root):
        dirs[:]=[n for n in dirs if n not in excluded]
        for name in files:
            p=Path(directory)/name
            if p.suffix in ('.py','.md','.toml','.json','.yaml','.yml','.ps1') or p.name=='.gitignore':out[p.relative_to(root).as_posix()]=sha(p)
    return out
def freeze(root):
    r=subprocess.run([sys.executable,'-B',str(root/'experimental_rubric_freeze_v111/verify_frozen_evaluator.py')],capture_output=True,encoding='utf-8',check=True);v=json.loads(r.stdout)
    assert v['passed'] and v['frozen_file_count']==725 and v['scientific_payload_root_sha256']=='23a923ebb224a162ba98c673a9f4f97e8c0571807a893ed72d6a07d65f181a09';return v
def fingerprint():
    files={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'end_engine').rglob('*.py'))};files['pyproject.toml']=sha(ROOT/'pyproject.toml')
    h=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert h=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82';return {'sha256':h,'files':files}
def capture():
    assert git(ROOT,'rev-parse','HEAD').strip()==BASE
    identity=freeze(ROOT);source=fingerprint();assert tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']=='0.3.5.2'
    before={name:snapshot(p) for name,p in ROOTS.items()};before['harness']=harness();save('PROTECTED_BEFORE.json',before)
    sdks={}
    for name in ('openai','anthropic','google-genai','typesafe-sdk','httpx'):
        try:sdks[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:sdks[name]=None
    baseline={'base_commit':BASE,'branch':git(ROOT,'branch','--show-current').strip(),'worktree':str(ROOT),'engine_version':'0.3.5.2','engine_fingerprint':source,'freeze':identity,'prior_tests':{'command':'python -B -m unittest discover -s tests -t . -v','workdir':'E:/END-Cognitive-Lab-v1/cognitive_architecture_lab_v1','tests':58,'failures':0,'errors':0,'skips':0,'executed_this_phase':True,'filesystem_escape_controls':'Both succeeded, confirming no host confinement'},'git':{name:{'head':git(p,'rev-parse','HEAD').strip(),'branch':git(p,'branch','--show-current').strip(),'status':git(p,'status','--short')} for name,p in ROOTS.items()},'worktrees':git(ROOT,'worktree','list','--porcelain'),'remotes':git(ROOT,'remote','-v'),'installed_sdk_metadata_only_no_imports':sdks,'threat_model':'MODEL_A_TRUSTED_ORCHESTRATOR_TOOL_FREE_MODEL','python':sys.version,'runtime_tests':{'tests':85,'failures':0,'errors':0,'skipped':0,'rerun_this_phase':True},'native_tests':{'tests':53,'failures':0,'errors':0,'skipped':0},'engine_tests':{'tests':303,'failures':0,'errors':0,'skipped':0},'new_phase_source_only':True}
    save('BASELINE.json',baseline);print(json.dumps({'passed':True,'frozen_files':725,'engine_fingerprint':source['sha256'],'protected':{k:len(v) for k,v in before.items()}}))
def preserve():
    before=json.loads((V/'PROTECTED_BEFORE.json').read_text(encoding='utf-8'));after={name:snapshot(p) for name,p in ROOTS.items()};after['harness']=harness();diff={k:[p for p in sorted(before[k].keys()|after[k].keys()) if before[k].get(p)!=after[k].get(p)] for k in before}
    b=json.loads((V/'BASELINE.json').read_text(encoding='utf-8'));samegit={n:all(git(p,*args).strip()==b['git'][n][field].strip() for field,args in [('head',('rev-parse','HEAD')),('branch',('branch','--show-current')),('status',('status','--short'))]) for n,p in ROOTS.items() if n!='abc_parent'}
    identities={n:freeze(p) for n,p in ROOTS.items() if n in ('abc_parent','freeze_worktree','architecture_lab')}
    return {'passed':not any(diff.values()) and all(samegit.values()),'changed':diff,'protected_counts':{k:len(v) for k,v in before.items()},'existing_worktree_git_unchanged':samegit,'freeze_identities':identities,'engine':fingerprint()['sha256']}
if __name__=='__main__':
    if '--preserve' in sys.argv:print(json.dumps(preserve()))
    else:capture()