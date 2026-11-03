"""Actual bounded native workers; inputs/outputs must stay in new evidence."""
import argparse,json,os,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests_coordination_v1.support import EVIDENCE,request,save,NETWORK
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from cognitive_architecture_lab_v1.src.accounting.coordination import Coordinator
def main(spec):
 cfg=json.loads(spec.read_text(encoding='utf-8'));root=Path(cfg['root']).resolve();path=Path(cfg['path']).resolve();assert root.is_relative_to(EVIDENCE.resolve()) and path.is_relative_to(EVIDENCE.resolve());mode=cfg['mode'];kw=cfg['kwargs'];result={'pid':os.getpid(),'mode':mode};start=time.monotonic()
 try:
  if mode=='hold':
   c=Coordinator.attach(path,timeout=.5)
   with c.acquire():
    save(root/'ready.json',{'phase':'L2_HELD','pid':os.getpid()});deadline=time.monotonic()+10
    while not (root/'release').exists():
     if time.monotonic()>deadline:raise AssertionError('WORKER_RELEASE_DEADLINE')
     time.sleep(.01)
   result['operation_status']='RELEASED'
  elif mode=='source_core':
   os.environ['A0_SOURCE_CHECKOUT']=str(ROOT);h=Path('E:/The End Engine/v21_A0_independent_decision/harness');sys.path.insert(0,str(h));import probe_workers as w
   pub=w.clone_fixture(root/'copy');c=Coordinator.create(pub.ledger.path);pub.ledger._coordination=c;before=w.snapshot(pub.directory);owner=pub.owner_path.read_bytes()
   with w.ExistingLock(pub.guard),c.acquire(),w.Pins(w.data_paths(pub.directory)):
    value=pub._verify_completed()
   assert w.snapshot(pub.directory)==before and pub.owner_path.read_bytes()==owner and pub.fd is None and pub.fence is None and pub.token is None and not any(w.COUNTERS.values())
   result.update(operation_status='SOURCE_CORE_PASS',payload_sha256=value['artifact_payload_sha256'],owner_fence_token_preserved=True,source_bytes_preserved=True,source_tripwires=w.COUNTERS,lock_order='L1->L2->ordinary_L3',fixture_origin='REBASED_SYNTHETIC_ONLY')
  else:
   enrolled=kw.get('enrolled',True);c=Coordinator.attach(path,timeout=.25) if enrolled else None
   if mode=='constructor':ledger=None
   else:
    ledger=object.__new__(Ledger);ledger.path=path;ledger.limits=json.loads(path.read_text(encoding='utf-8'))['state']['limits'];ledger._coordination=c
   save(root/'attempting.json',{'phase':'ACTUAL_OPERATION_ENTRY','pid':os.getpid(),'operation':mode,'enrolled':enrolled})
   try:
    if mode=='constructor':Ledger(path,coordination=c)
    elif mode=='register':ledger.register(request(kw.get('run_id','foreign')))
    elif mode=='reserve':ledger.reserve('run','synthetic-control',10,1)
    elif mode=='finish':ledger.finish(kw['attempt_id'],state='SUCCEEDED',input_tokens=1,output_tokens=2,seconds=.01)
    elif mode=='crash_pending':
     from unittest.mock import patch
     import cognitive_architecture_lab_v1.src.accounting.ledger as lm
     def pause(source,destination):
      save(root/'ready.json',{'phase':'PENDING_FLUSHED_FSYNCED_BEFORE_REPLACE','pid':os.getpid(),'pending_path':str(source)});time.sleep(30);raise AssertionError('PARENT_DID_NOT_TERMINATE_WORKER')
     with patch.object(lm.os,'replace',pause):ledger.register(request('crash'))
    else:raise AssertionError('UNKNOWN_OPERATION')
    result['operation_status']='RETURNED'
   except BaseException as error:
    result.update(operation_status='REJECTED',exception_type=type(error).__name__,message=str(error),code=getattr(error,'code',None),errno=getattr(error,'errno',None),winerror=getattr(error,'winerror',None))
  result.update(elapsed_seconds=time.monotonic()-start,network_attempts=NETWORK);save(spec.with_suffix('.result.json'),result);print(json.dumps(result),flush=True);return 0
 except BaseException as error:
  result.update(operation_status='WORKER_ERROR',exception_type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),elapsed_seconds=time.monotonic()-start);save(spec.with_suffix('.result.json'),result);print(json.dumps(result),flush=True);return 2
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);raise SystemExit(main(p.parse_args().request))
