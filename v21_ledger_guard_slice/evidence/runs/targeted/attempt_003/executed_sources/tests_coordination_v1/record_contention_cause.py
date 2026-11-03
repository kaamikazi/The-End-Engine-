"""Focused reproduction retaining the native cause behind domain contention."""
import errno,hashlib,json,os,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests_coordination_v1.support import EVIDENCE,NETWORK,request,save,sha
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from cognitive_architecture_lab_v1.src.accounting.coordination import Coordinator,CoordinationBusy
def child(path):
 actor=object.__new__(Ledger);actor.path=path;actor.limits=json.loads(path.read_text(encoding='utf-8'))['state']['limits'];actor._coordination=Coordinator.attach(path,timeout=.15)
 try:actor.register(request('blocked'))
 except CoordinationBusy as error:
  cause=error.__cause__;print(json.dumps({'domain_code':error.code,'native_cause_type':type(cause).__name__,'native_errno':getattr(cause,'errno',None),'native_winerror':getattr(cause,'winerror',None),'native_message':str(cause),'traceback':traceback.format_exc(),'network_attempts':NETWORK}),flush=True);return 0
 raise AssertionError('ENROLLED_REGISTER_NOT_EXCLUDED')
def main(final=False):
 output=EVIDENCE/('runs/native_contention_cause_final' if final else 'runs/native_contention_cause');assert not output.exists();output.mkdir(parents=True);path=output/'budget.json';c=Coordinator.create(path);Ledger(path,coordination=c);before=sha(path);guard_before=sha(c.guard_path);start=time.monotonic()
 argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(path)]
 with c.acquire():
  p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW);out,err=p.communicate(timeout=5);save(output/'COMMAND.json',{'argv':argv,'pid':p.pid,'exit_code':p.returncode,'stdout':out,'stderr':err});assert p.returncode==0;observed=json.loads(out);assert observed['domain_code']=='L2_CONTENTION_DEADLINE' and observed['native_errno'] in (errno.EACCES,errno.EAGAIN);assert not path.with_suffix('.json.pending').exists() and sha(path)==before
 assert sha(c.guard_path)==guard_before
 report={'control_verdict':'PASS','observed_native_contention':observed,'pending_created':False,'main_unchanged':True,'control_unchanged':True,'elapsed_seconds':time.monotonic()-start,'strong_authority_awarded':False,'supplemental_control_not_added_to_unittest_count':True,'script_sha256':sha(Path(__file__)),'production_hashes':{n:sha(ROOT/n) for n in ['cognitive_architecture_lab_v1/src/accounting/ledger.py','cognitive_architecture_lab_v1/src/accounting/coordination.py']}};save(output/'RESULT.json',report);print(json.dumps({k:report[k] for k in ('control_verdict','pending_created','main_unchanged','elapsed_seconds')}),flush=True)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='--child':raise SystemExit(child(Path(sys.argv[2])))
 main(final=len(sys.argv)>1 and sys.argv[1]=='--final')
