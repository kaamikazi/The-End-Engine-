"""Read-only source/record preservation and native environment inventory for A0."""
import ast,ctypes,csv,hashlib,json,platform,subprocess,sys,zipfile
from ctypes import wintypes
from pathlib import Path
H=Path(__file__).resolve().parent;E=H.parent;C=E/'checkout';P=Path('E:/The End Engine/v21_implementation_masterplan');R=Path('E:/END-Cognitive-Architectures-Fix-v102');W=Path('E:/END-v102-V21-Contract-Checkpoint')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(root),'-c','safe.directory='+root.as_posix(),*a],text=True).strip()
def volume(path):
 k=ctypes.WinDLL('kernel32',use_last_error=True);v=ctypes.create_unicode_buffer(1024);name=ctypes.create_unicode_buffer(1024);fs=ctypes.create_unicode_buffer(128);serial=wintypes.DWORD();maxc=wintypes.DWORD();flags=wintypes.DWORD()
 if not k.GetVolumePathNameW(str(path.resolve()),v,len(v)):raise ctypes.WinError(ctypes.get_last_error())
 if not k.GetVolumeInformationW(v.value,name,len(name),ctypes.byref(serial),ctypes.byref(maxc),ctypes.byref(flags),fs,len(fs)):raise ctypes.WinError(ctypes.get_last_error())
 return {'volume_root':v.value,'volume_label':name.value,'serial_hex':format(serial.value,'08x'),'filesystem':fs.value,'flags':flags.value}
def identity():
 out={}
 for label,root in [('approved',W),('correction',R),('earlier_WIP',Path('E:/END-v102-WIP-Checkpoint-20261019'))]:out[label]={'root':str(root),'HEAD':git(root,'rev-parse','HEAD'),'branch':git(root,'branch','--show-current'),'status':git(root,'status','--porcelain=v1'),'staged':git(root,'diff','--cached','--name-status')}
 assert out['approved']['HEAD']=='783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e' and not out['approved']['status'];assert out['correction']['HEAD']=='bc9bcbad8e9cb051d54c3b270e2e03d460858986'
 assert git(C,'rev-parse','HEAD')==out['approved']['HEAD']
 out['checkout_HEAD']=git(C,'rev-parse','HEAD');out['checkout_branch']=git(C,'branch','--show-current')
 for root in (W,R,C):
  m={p.relative_to(root).as_posix():sha(p) for p in (root/'end_engine').rglob('*.py')};m['pyproject.toml']=sha(root/'pyproject.toml');fp=hashlib.sha256(json.dumps(m,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
 out['engine_fingerprint']=fp
 manifest=json.loads((C/'experimental_architectures_v1_r3/validation/WIP_SOURCE_MANIFEST.json').read_text(encoding='utf-8'));assert all(sha(C/n)==x['sha256']==sha(R/n) for n,x in manifest['files'].items());out['manifest_entries']=len(manifest['files'])
 plan=json.loads((P/'_evidence/PLAN_FILE_HASHES.json').read_text(encoding='utf-8'));assert all(sha(P/n)==x['sha256'] for n,x in plan['files'].items());out['plan_files_verified']=len(plan['files'])
 d=C/'experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1';out['contract_files']={p.name:sha(p) for p in d.iterdir() if p.is_file()};assert len(out['contract_files'])==18
 review=Path('E:/The End Engine/v21_contract_acceptance_review/V21_CONTRACT_ACCEPTANCE_REVIEW_BUNDLE.zip');assert sha(review)=='fa988f05f5d8620aeff46878542d2ef083f09e5b255b7bb5581b3c3b55ec6671'
 with zipfile.ZipFile(review) as z:
  assert z.testzip() is None;mf=json.loads(z.read('BUNDLE_MANIFEST.json'));assert all(hashlib.sha256(z.read(n)).hexdigest()==x['sha256'] for n,x in mf['files'].items())
 out['review_zip_sha256']=sha(review);out['frozen']=json.loads(subprocess.check_output([sys.executable,'-B',str(R/'experimental_rubric_freeze_v111/verify_frozen_evaluator.py')],text=True));assert out['frozen']['passed']
 return out
def capture():
 old=json.loads((P/'_evidence/BEFORE.json').read_text(encoding='utf-8'));maps={}
 for label,files in old.items():maps[label]={p:sha(Path(p)) for p in files};print(label+': '+str(len(files)),flush=True)
 for label,root in [('masterplan',P),('source_fixture',Path('E:/The End Engine/ca102/own/RACE_2_valid'))]:maps[label]={str(p):sha(p) for p in root.rglob('*') if p.is_file()}
 names=subprocess.check_output(['git','--no-optional-locks','-C',str(C),'-c','safe.directory='+C.as_posix(),'ls-files','-z']).decode().split('\0');maps['checkout_tracked']={str(C/n):sha(C/n) for n in names if n}
 return maps
if __name__=='__main__':
 if sys.argv[1]=='before':
  assert not (H/'BEFORE.json').exists();i=identity();(H/'IDENTITY.json').write_text(json.dumps(i,indent=2)+'\n',encoding='utf-8')
  env={'python':sys.version,'executable':sys.executable,'windows':platform.platform(),'volume':volume(E),'native_api_exports':{n:hasattr(ctypes.WinDLL('kernel32'),n) for n in ['CreateFileW','CloseHandle','ReadFile','GetFileInformationByHandle','LockFileEx','GetVolumeInformationW','GetProcessTimes']},'source_dependencies':'246 unchanged manifest entries; stdlib test scaffolding, no installs','baseline_tests':'existing r3 tests available; NOT executed by preflight'};assert env['volume']['filesystem']=='NTFS';(H/'ENVIRONMENT.json').write_text(json.dumps(env,indent=2)+'\n',encoding='utf-8');print(json.dumps(env),flush=True)
  m=capture();(H/'BEFORE.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8');print('Full before inventory complete',flush=True)
 else:
  i=identity();assert i==json.loads((H/'IDENTITY.json').read_text(encoding='utf-8'));before=json.loads((H/'BEFORE.json').read_text(encoding='utf-8'));after=capture();diff={k:[p for p in set(v)|set(after[k]) if v.get(p)!=after[k].get(p)] for k,v in before.items()};assert not any(diff.values()),diff
  result={'passed':True,'changed':diff,'counts':{k:len(v) for k,v in before.items()},'protected_Git_states_unchanged':True,'new_checkout_HEAD':i['checkout_HEAD'],'new_checkout_branch':i['checkout_branch'],'new_checkout_diff':git(C,'diff','--name-status'),'new_checkout_untracked':git(C,'ls-files','--others','--exclude-standard'),'engine_fingerprint':i['engine_fingerprint'],'frozen':i['frozen'],'no_commit_push_merge_tag_or_release':True}
  (E/'A0_SOURCE_PRESERVATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
