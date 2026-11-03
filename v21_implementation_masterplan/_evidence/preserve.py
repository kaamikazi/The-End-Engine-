"""Planning-only, read-only source/record inventory; writes only plan evidence."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent
P=H.parent
R=Path('E:/END-Cognitive-Architectures-Fix-v102')
W=Path('E:/END-v102-V21-Contract-Checkpoint')
V=Path('E:/The End Engine/v21_contract_acceptance_review')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(root),'-c','safe.directory='+root.as_posix(),*a],text=True).strip()
def inventory():
 previous=json.loads((V/'coordinator/BEFORE.json').read_text(encoding='utf-8'))
 maps={}
 for k,files in previous.items():
  maps[k]={p:sha(Path(p)) for p in files}
  print('Inventoried '+k+': '+str(len(files)),flush=True)
 maps['approved_review']={str(p):sha(p) for p in V.rglob('*') if p.is_file()}
 return maps
def identities():
 result={}
 for label,root in [('approved_checkpoint',W),('original_correction',R),('prior_WIP',Path('E:/END-v102-WIP-Checkpoint-20261019'))]:
  result[label]={'root':str(root),'HEAD':git(root,'rev-parse','HEAD'),'branch':git(root,'branch','--show-current'),'status':git(root,'status','--porcelain=v1'),'staged':git(root,'diff','--cached','--name-status')}
 assert result['approved_checkpoint']['HEAD']=='783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e' and not result['approved_checkpoint']['status']
 assert result['original_correction']['HEAD']=='bc9bcbad8e9cb051d54c3b270e2e03d460858986' and not result['original_correction']['staged']
 fingerprints={}
 for root in (W,R):
  files={p.relative_to(root).as_posix():sha(p) for p in (root/'end_engine').rglob('*.py')};files['pyproject.toml']=sha(root/'pyproject.toml')
  fingerprint=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  assert fingerprint=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
  fingerprints[str(root)]=fingerprint
 result['engine_fingerprints']=fingerprints
 d=W/'experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1'
 result['contract_files']={p.name:sha(p) for p in d.iterdir() if p.is_file()};assert len(result['contract_files'])==18
 for p in d.iterdir():
  if p.is_file():assert p.read_bytes()==subprocess.check_output(['git','--no-optional-locks','-C',str(W),'-c','safe.directory='+W.as_posix(),'show','HEAD:'+p.relative_to(W).as_posix()])
 archive=V/'V21_CONTRACT_ACCEPTANCE_REVIEW_BUNDLE.zip';assert sha(archive)=='fa988f05f5d8620aeff46878542d2ef083f09e5b255b7bb5581b3c3b55ec6671'
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  manifest=json.loads(z.read('BUNDLE_MANIFEST.json'))
  assert all(hashlib.sha256(z.read(n)).hexdigest()==item['sha256'] for n,item in manifest['files'].items())
  assert z.read('FINAL_VERDICT.json')==(V/'FINAL_VERDICT.json').read_bytes()
 result['approved_archive']={'sha256':sha(archive),'bytes':archive.stat().st_size,'crc_and_all_manifest_members':'PASS'}
 result['frozen']=json.loads(subprocess.check_output([sys.executable,'-B',str(R/'experimental_rubric_freeze_v111/verify_frozen_evaluator.py')],text=True))
 assert result['frozen']['passed'] and result['frozen']['scientific_payload_root_sha256']=='23a923ebb224a162ba98c673a9f4f97e8c0571807a893ed72d6a07d65f181a09'
 manifest=json.loads((W/'experimental_architectures_v1_r3/validation/WIP_SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
 result['source_manifest_structure']=list(manifest)
 return result
if __name__=='__main__':
 stage=sys.argv[1]
 if stage=='before':
  assert not (H/'BEFORE.json').exists()
  ident=identities();(H/'IDENTITY.json').write_text(json.dumps(ident,indent=2)+'\n');print('Identity PASS',flush=True)
  maps=inventory();(H/'BEFORE.json').write_text(json.dumps(maps,indent=2)+'\n')
  print(json.dumps({'baseline_counts':{k:len(v) for k,v in maps.items()}}),flush=True)
 else:
  before=json.loads((H/'BEFORE.json').read_text(encoding='utf-8'));ident=identities();assert ident==json.loads((H/'IDENTITY.json').read_text(encoding='utf-8'))
  after=inventory();changed={k:[p for p in set(v)|set(after[k]) if v.get(p)!=after[k].get(p)] for k,v in before.items()}
  # Re-enumerate complete worktree inventories to catch new/deleted unexpected files.
  for key,root in [('v21_checkpoint',W),('original_v21',R/'experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1')]:
   actual={str(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts};assert actual==set(before[key]),key
  report={'passed':not any(changed.values()),'changed':changed,'counts':{k:len(v) for k,v in before.items()},'git_HEAD_branch_index_and_original_dirty_state_unchanged':True,'baseline_identity':'_evidence/IDENTITY.json','engine_fingerprint':ident['engine_fingerprints'][str(W)],'frozen':ident['frozen'],'implementation_changes':0,'test_migrations':0,'Git_mutations':0,'live_inference':0,'empirical_benchmarks':0,'scientific_performance_claims':'NONE','planning_only':True}
  (P/'SOURCE_PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['passed']
