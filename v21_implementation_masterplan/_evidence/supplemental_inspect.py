import ast,csv,hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;W=Path('E:/END-v102-V21-Contract-Checkpoint');R=Path('E:/END-Cognitive-Architectures-Fix-v102')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((W/'experimental_architectures_v1_r3/validation/WIP_SOURCE_MANIFEST.json').read_text(encoding='utf-8'));assert all(sha(W/n)==v['sha256'] and sha(R/n)==v['sha256'] for n,v in m['files'].items())
rows=[];errors=[]
for p in sorted((R/'experimental_architectures_v1_r3').rglob('*.py')):
 try:text=p.read_text(encoding='utf-8-sig');tree=ast.parse(text)
 except (UnicodeError,SyntaxError) as e:errors.append({'path':str(p),'error':str(e)});continue
 for n in ast.walk(tree):
  if isinstance(n,ast.Call):
   target=ast.unparse(n.func)
   if target.rsplit('.',1)[-1] in {'execute','finish','blocked_recovery','publish','verify_semantics','verify_completed'}:
    rel=p.relative_to(R).as_posix();rows.append({'path':rel,'line':n.lineno,'call':target,'role':'RETAINED_RESEARCH_OR_COPY_NOT_ENROLLED' if '/validation/' in rel else 'CURRENT_RUNTIME_OR_TEST','expression':ast.get_source_segment(text,n)})
with (H/'ORIGINAL_WORKTREE_CALL_SITES.csv').open('w',encoding='utf-8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=['path','line','call','role','expression']);writer.writeheader();writer.writerows(rows)
t=json.loads(Path('E:/The End Engine/v2_contract_acceptance_review_20261020/probes/V2_ADVERSARIAL_RESULTS.json').read_text(encoding='utf-8'));times=[]
def walk(x,path=''):
 if isinstance(x,dict):
  for k,v in x.items():
   if k=='elapsed_seconds':times.append({'json_path':path+'.'+k,'seconds':v})
   walk(v,path+'.'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'['+str(i)+']')
walk(t)
result={'manifest_entries_verified_in_both_states':len(m['files']),'source_root_from_manifest':m.get('root_sha256',m.get('source_root_sha256')),'original_worktree_call_sites':len(rows),'original_call_scan_parse_errors':errors,'timing_source':'E:/The End Engine/v2_contract_acceptance_review_20261020/probes/V2_ADVERSARIAL_RESULTS.json','timing_observations':times,'timing_limits':'Prior bounded probe measurements only; not measurements of future v2.1 capture, adapter, full CR2 or end-to-end validation. No tests executed in planning task.'}
(H/'DEPENDENCY_AND_TIMING_INSPECTION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='timing_observations'}));print(json.dumps({'elapsed_observations':len(times),'minimum':min([x['seconds'] for x in times],default=None),'maximum':max([x['seconds'] for x in times],default=None)}))
