"""Execute only the newly authorized A0-18 rerun, never the full A0 suite."""
import argparse,ast,difflib,hashlib,json,os,shutil,sys,time,traceback
from pathlib import Path
E=Path(__file__).resolve().parent.parent;H=E/'harness';A=Path('E:/The End Engine/v21_A0_feasibility');C=A/'checkout'
os.environ['A0_SOURCE_CHECKOUT']=str(C);sys.dont_write_bytecode=True;sys.path.insert(0,str(H))
import probe_workers as w
import test_lock_domain_feasibility as tests
FILES=['README.md','probe_runner.py','probe_workers.py','test_lock_domain_feasibility.py','source_profile.json','result_schema.json']
def defs(path):
 text=path.read_text(encoding='utf-8');tree=ast.parse(text);return {n.name:ast.get_source_segment(text,n) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();out=Path(args.output).resolve();assert out.is_relative_to((E/'runs').resolve()) and not out.exists(),'FRESH_CORRECTION_SCRATCH_ONLY'
 original=A/'runs/attempt_002/executed_scaffolding';receipt=w.read(A/'runs/attempt_002/EXECUTED_SOURCE_RECEIPT.json')
 assert all(w.sha((C/n).read_bytes())==v['sha256'] for n,v in receipt['unchanged_implementation_sources'].items())
 differences=[]
 for n in FILES:
  old=(original/n).read_text(encoding='utf-8');new=(H/n).read_text(encoding='utf-8')
  if old!=new:differences.append(n)
 assert set(differences)=={'probe_workers.py','test_lock_domain_feasibility.py'}
 for n,allowed in [('probe_workers.py',{'collect_a018_namespace'}),('test_lock_domain_feasibility.py',{'case18'})]:
  before=defs(original/n);after=defs(H/n)
  assert all(after.get(k)==v for k,v in before.items() if k not in allowed),'UNRELATED_SCAFFOLD_FUNCTION_CHANGED'
  assert set(after)-set(before)<=allowed
 assert defs(original/'test_lock_domain_feasibility.py')['recursive']==defs(H/'test_lock_domain_feasibility.py')['recursive']
 out.mkdir(parents=True);saved=out/'executed_harness';saved.mkdir();hashes={}
 for n in FILES:shutil.copyfile(H/n,saved/n);hashes[n]=w.sha((saved/n).read_bytes())
 for n in differences:(out/(n+'.diff')).write_text(''.join(difflib.unified_diff((original/n).read_text(encoding='utf-8').splitlines(True),(H/n).read_text(encoding='utf-8').splitlines(True),fromfile='original/'+n,tofile='corrected/'+n)),encoding='utf-8')
 w.write_json(out/'EXECUTED_HARNESS_RECEIPT.json',{'source_commit':'783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e','original_six_hashes':receipt['new_scaffolding_files'],'corrected_six_hashes':hashes,'changed_files':differences,'all_unrelated_original_definitions_unchanged':True,'recursive_negative_scoring_unchanged':True,'actual_requested_vector_ids':['A0-18']})
 root=out/'A0-18';root.mkdir();start=time.monotonic();result={'vector_id':'A0-18','scope':'SINGLE_A0_COLLECTOR_NEGATIVE_CONTROL_NOT_STRONG_FEASIBILITY','executed_controls':1,'status':'ERROR','expectation_matched':False,'strong_profile_supported':False,'A_or_S_awarded':False}
 try:
  value=tests.case18(root);result.update(value);result.update(status='PASS',expectation_matched=True)
 except BaseException as error:result.update(status='FAIL' if isinstance(error,AssertionError) else 'ERROR',error=type(error).__name__+': '+str(error),traceback=traceback.format_exc())
 finally:
  cleanup=[]
  for child in w.CHILDREN:
   if not child.a0_collected:
    alive=child.poll() is None;cleanup.append(w.collect(child,kill=alive))
    if alive:result.update(status='FAIL',expectation_matched=False,error='UNEXPECTED_UNJOINED_CHILD')
  if cleanup:result['emergency_cleanup']=cleanup
  result['elapsed_seconds']=time.monotonic()-start;result['parent_tripwire_counters']=dict(w.COUNTERS)
  if any(w.COUNTERS.values()):result.update(status='FAIL',expectation_matched=False,error='FORBIDDEN_CALL_ATTEMPT')
  w.write_json(out/'TARGETED_RESULT.json',result)
 print(json.dumps({'vector':'A0-18','status':result['status'],'executed_controls':1,'strong_profile_supported':False,'elapsed_seconds':result['elapsed_seconds'],'error':result.get('error')}),flush=True)
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
