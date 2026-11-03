"""Mechanical identity/preservation only. No author acceptance judgments."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent
V=Path('E:/END-v102-V21-Contract-Checkpoint')
D=V/'experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(r,*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(r),'-c','safe.directory='+r.as_posix(),*args],text=True).strip()
def capture():
 maps={}
 previous=json.loads(Path('E:/The End Engine/contract_closure_v21_20261020/BEFORE.json').read_text())
 for key,files in previous.items(): maps[key]={p:sha(Path(p)) for p in files}
 maps['v21_checkpoint']={str(p):sha(p) for p in V.rglob('*') if p.is_file() and '.git' not in p.relative_to(V).parts}
 maps['original_v21']={str(p):sha(p) for p in Path('E:/END-Cognitive-Architectures-Fix-v102/experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1').rglob('*') if p.is_file()}
 return maps
def identities():
 out={}
 for label,r in [('v21',V),('old_checkpoint',Path('E:/END-v102-WIP-Checkpoint-20261019')),('correction',Path('E:/END-Cognitive-Architectures-Fix-v102'))]:
  out[label]={'head':git(r,'rev-parse','HEAD'),'branch':git(r,'branch','--show-current'),'status':git(r,'status','--porcelain=v1'),'index_diff':git(r,'diff','--cached','--name-status')}
 assert out['v21']['head']=='783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e'
 assert not out['v21']['status']
 docs={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in D.iterdir() if p.is_file()};assert len(docs)==18
 for p in D.iterdir():
  if p.is_file():assert subprocess.check_output(['git','--no-optional-locks','-C',str(V),'-c','safe.directory='+V.as_posix(),'show','HEAD:'+p.relative_to(V).as_posix()])==p.read_bytes()
 out['specification_documents']=docs
 p=Path('E:/The End Engine/v2_contract_acceptance_review_20261020/V2_CONTRACT_ACCEPTANCE_REVIEW_BUNDLE.zip')
 assert sha(p)=='ad21ed22701c05c7249c4bc8ddfeda037a7d31e6bfed51b3b76adfc9193cbddf'
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  manifest=json.loads(z.read('BUNDLE_MANIFEST.json'))
  assert all(hashlib.sha256(z.read(n)).hexdigest()==v['sha256'] for n,v in manifest['files'].items())
 out['prior_review_bundle']={'sha256':sha(p),'bytes':p.stat().st_size,'zip_crc_and_all_manifest_members':'PASS'}
 out['network_verification']='NOT_PERFORMED_OFFLINE_REVIEW; commit tree verified locally, not live GitHub'
 out['coordinator_provenance']='Prior v2.1 author; mechanical checks only. Fresh agents own substantive review.'
 return out
if __name__=='__main__':
 stage=sys.argv[1]
 if stage=='before':
  assert not (H/'BEFORE.json').exists()
  maps=capture(); ident=identities()
  (H/'BEFORE.json').write_text(json.dumps(maps,indent=2)+'\n')
  (H/'IDENTITY.json').write_text(json.dumps(ident,indent=2)+'\n')
  print(json.dumps({'identity':'PASS','file_counts':{k:len(v) for k,v in maps.items()}}))
 else:
  before=json.loads((H/'BEFORE.json').read_text());now=capture()
  diff={k:[p for p in set(before[k])|set(now[k]) if before[k].get(p)!=now[k].get(p)] for k in before}
  ident=identities();old=json.loads((H/'IDENTITY.json').read_text())
  assert old==ident
  report={'passed':not any(diff.values()),'changes':diff,'counts':{k:len(v) for k,v in before.items()},'git_identity_status_index_unchanged':True,'author_conflict_disclosed':True}
  (H/'PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
  print(json.dumps(report));assert report['passed']
