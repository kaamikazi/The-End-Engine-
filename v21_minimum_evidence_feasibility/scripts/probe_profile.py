"""Only the bounded native controls approved for this one profile."""
import argparse,json,time,traceback
from pathlib import Path
from inspect_sources import ROOT,w,save,read
import test_lock_domain_feasibility as old_cases
def main(case):
 root=ROOT/'runs/native'/case;assert not root.exists();root.mkdir(parents=True);start=time.monotonic();r={'case_id':case,'control_verdict':'FAIL','strong_profile_supported':False,'A_or_S_awarded':False}
 try:
  if case=='COOPERATING_POSITIVE':
   r['expected_event']='Two explicitly cooperating actors show attempted admission, first finally drain before capture, second admission after release; no extrapolation to all writers.';r['observed_event']=old_cases.case17(root);r['feasibility_implication']='Enforced admission for these two actors only; external and bypass actors remain unproved.'
  elif case=='N12':
   r['expected_event']='Actual concurrent overwrite of pinned existing journal denied with native WinError5; original bytes remain; child joins; pin closes and permits access after release.'
   pub=w.clone_fixture(root/'copy');wire=next((pub.directory/'wire').glob('*.jsonl'));raw=wire.read_bytes()
   with w.Pins([wire]) as pins:
    child=w.collect(w.spawn('mutate',root,target=wire,operations=['write']));save(root/'CHILD_COLLECTION_RECEIPT.json',child);assert child['exit_code']==0;events=child['worker_result']['events'];assert len(events)==1 and events[0]['outcome']=='DENIED' and events[0]['winerror']==5;assert wire.read_bytes()==raw
   assert not pins.handles
   handle=w.K.CreateFileW(str(wire.resolve()),0xC0010000,7,None,3,0x80,None)
   if handle==w.ctypes.c_void_p(-1).value:raise w.ctypes.WinError(w.ctypes.get_last_error())
   assert bool(w.K.CloseHandle(handle));assert wire.read_bytes()==raw
   core=w.protected_core(pub);assert core['core']['passed'];r['observed_event']={'child':child,'unchanged_journal_sha256':w.sha(raw),'pin_handles_closed':True,'post_release_access_open_closed':True,'unchanged_core':core};r['feasibility_implication']='Existing pinned file overwrite is excluded for this attempted operation. This does not freeze new namespace membership or prove all-writer exclusion.'
  elif case=='N01_N02':
   r['expected_event']='Exact unchanged Ledger.register bypasses test admission/L1/L2, writes foreign budget.json.pending, target replacement is denied WinError5, original ledger/attempts unchanged, handles released.'
   r['observed_event']=old_cases.case18(root);assert r['observed_event']['material_blocker'];r['feasibility_implication']='Demonstrated writer-exclusion blocker in this one arrangement; no A/S; stop profile after this planned last control.'
  assert not any(w.COUNTERS.values());r['control_verdict']='PASS'
 except BaseException as e:r['error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
 finally:
  leftover=[]
  for child in w.CHILDREN:
   if not child.a0_collected:leftover.append(w.collect(child,kill=child.poll() is None));r['control_verdict']='FAIL'
  r['emergency_cleanup']=leftover;r['elapsed_time']=time.monotonic()-start;r['bound_seconds']=60;r['bound_satisfied']=r['elapsed_time']<60;r['tripwires']=dict(w.COUNTERS)
  if not r['bound_satisfied']:r['control_verdict']='FAIL'
  save(root/'CONTROL_RESULT.json',r)
 print(json.dumps({'case':case,'verdict':r['control_verdict'],'seconds':r['elapsed_time'],'error':r.get('error')}),flush=True)
 return 0 if r['control_verdict']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',choices=['COOPERATING_POSITIVE','N12','N01_N02'],required=True);raise SystemExit(main(p.parse_args().case))
