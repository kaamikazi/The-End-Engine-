"""Unchanged nonowning completed-core checks on six derived mock fixtures."""
import argparse,json,time,traceback
from inspect_sources import ROOT,MOCK,CONDITIONS,w,read,save,relocate
def main(condition):
 root=ROOT/'runs/positive'/condition;assert not root.exists();root.mkdir(parents=True);start=time.monotonic();r={'condition':condition,'control_verdict':'FAIL','scope':'DERIVED_MOCK_LEGACY_CORE_ELIGIBILITY_NOT_NEW_V21_CERTIFICATION','source_authority':'I_MAXIMUM_NO_COMMON_CUT','certified_complete_totals':None,'provider_calls':0}
 try:
  pub=relocate(MOCK/('MOCK_EXP-001_'+condition),root/'copy',MOCK/'GLOBAL_BUDGET.json');before=w.snapshot(pub.directory);core=w.protected_core(pub);save(root/'UNCHANGED_CORE.json',core);assert core['core']['passed'],core['core'];assert w.snapshot(pub.directory)==before;assert pub.fd is None and pub.fence is None and pub.token is None;assert not any(w.COUNTERS.values());r.update(control_verdict='PASS',core=core['core'],owner_lease_never_claimed=True,derived_bytes_unchanged_during_core=True)
 except BaseException as e:r['error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
 r['elapsed_time']=time.monotonic()-start;r['bound_satisfied']=r['elapsed_time']<60;r['tripwires']=dict(w.COUNTERS)
 if not r['bound_satisfied']:r['control_verdict']='FAIL'
 save(root/'CONTROL_RESULT.json',r);print(json.dumps(r),flush=True);return 0 if r['control_verdict']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--condition',choices=CONDITIONS,required=True);raise SystemExit(main(p.parse_args().condition))
