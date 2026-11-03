"""Execute A0-only offline vectors in new scratch; preserve every run and failure."""
import argparse,ast,hashlib,json,os,shutil,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
import probe_workers as w
import test_lock_domain_feasibility as t
E=w.CHECKOUT.parent
FILES=['README.md','probe_runner.py','probe_workers.py','test_lock_domain_feasibility.py','source_profile.json','result_schema.json']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();out=Path(args.output).resolve();assert out.is_relative_to((E/'runs').resolve()),'A0_OUTPUT_MUST_BE_NEW_LOCAL_SCRATCH';assert not out.exists(),'NEVER_OVERWRITE_AN_EXISTING_ATTEMPT'
 profile=w.read(HERE/'source_profile.json');assert all(w.sha((w.CHECKOUT/n).read_bytes())==v['sha256'] for n,v in profile['source_files'].items()),'PINNED_SOURCE_DRIFT'
 plan=Path('E:/The End Engine/v21_implementation_masterplan/FIRST_IMPLEMENTATION_SLICE.md').read_text(encoding='utf-8');requirements={}
 for line in plan.splitlines():
  if line.startswith('| A0-'):parts=line.split('|');requirements[parts[1].strip()]=parts[2].strip()
 assert set(requirements)==set(t.CASES) and len(requirements)==20
 out.mkdir(parents=True);saved=out/'executed_scaffolding';saved.mkdir()
 hashes={}
 for n in FILES:shutil.copyfile(HERE/n,saved/n);hashes[n]=w.sha((saved/n).read_bytes())
 w.write_json(out/'EXECUTED_SOURCE_RECEIPT.json',{'source_commit':profile['commit'],'new_scaffolding_files':hashes,'unchanged_implementation_sources':profile['source_files'],'source_fixture_profile':profile['template_files'],'user_scoring_clarification':profile['scoring_clarification']})
 rows={k:{'vector_id':k,'required_plan_observation':v,'status':'NOT_EXECUTED','expectation_matched':False,'observed_events':[],'authority':'X','material_blocker':False} for k,v in requirements.items()};executed=[];stop=None
 def save():
  result={'scope':'A0_SYNTHETIC_FEASIBILITY_NOT_PRODUCTION_OBSERVER_OR_CERTIFICATE','source_commit':profile['commit'],'rows':[rows[k] for k in sorted(rows)],'execution_order':executed,'stop':stop,'counts':{s:sum(r['status']==s for r in rows.values()) for s in ['PASS','FAIL','ERROR','NOT_EXECUTED']},'parent_call_tripwire_counters':dict(w.COUNTERS),'no_new_attempt_reservations':w.COUNTERS['forbidden_dispatch_or_reservation_calls']==0,'no_A_or_S_awarded':True}
  w.write_json(out/'RUN_RESULT.json',result);return result
 save()
 for vector in t.EXECUTION_ORDER:
  root=out/vector;root.mkdir();row=rows[vector];row['started_unix']=time.time();executed.append(vector);start=time.monotonic()
  try:
   value=t.CASES[vector](root);row.update(value);row['status']='PASS';row['expectation_matched']=True
  except BaseException as e:
   row.update(status='FAIL' if isinstance(e,AssertionError) else 'ERROR',expectation_matched=False,error=type(e).__name__+': '+str(e),traceback=traceback.format_exc());stop={'reason':'UNEXPECTED_FEASIBILITY_FAILURE','vector':vector}
  finally:
   cleanup=[]
   for p in w.CHILDREN:
    if not p.a0_collected:
     was_alive=p.poll() is None;cleanup.append(w.collect(p,kill=was_alive))
     if was_alive:row.update(status='FAIL',expectation_matched=False,error='UNEXPECTED_LIVE_CHILD_REQUIRED_CLEANUP');stop={'reason':'UNJOINED_WORKER','vector':vector}
   if cleanup:row['cleanup_receipts']=cleanup
   row['elapsed_seconds']=time.monotonic()-start;w.write_json(root/'VECTOR_RESULT.json',row)
  if row.get('material_blocker'):stop={'reason':'AUTHORIZED_STOP_RULE_REAL_UNENROLLED_WRITER_MUTATION','vector':vector,'detail':row.get('blocker_reason')}
  result=save();print(json.dumps({'vector':vector,'status':row['status'],'material_blocker':row.get('material_blocker',False),'elapsed_seconds':row['elapsed_seconds']}),flush=True)
  if stop:break
 print(json.dumps({'completed':True,'output':str(out),'counts':result['counts'],'stop':stop}),flush=True)
 return 0 if all(r['status']=='PASS' for r in rows.values()) else 1
if __name__=='__main__':raise SystemExit(main())
