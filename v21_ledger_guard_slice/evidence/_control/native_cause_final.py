"""Retain native contention error on the exact final candidate revision."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
E=Path(__file__).resolve().parents[1];C=E.parent/'checkout';sys.path.insert(0,str(C))
from tests_coordination_v1.support import request,save,sha,NETWORK
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from cognitive_architecture_lab_v1.src.accounting.coordination import Coordinator
def main():
 out=E/'runs/native_cause_final_source';assert not out.exists();out.mkdir(parents=True);path=out/'budget.json';coord=Coordinator.create(path);Ledger(path,coordination=coord);before=sha(path);control=sha(coord.guard_path);start=time.monotonic();argv=[sys.executable,'-B',str(C/'tests_coordination_v1/record_contention_cause.py'),'--child',str(path)]
 with coord.acquire():
  child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
  try:stdout,stderr=child.communicate(timeout=5)
  except subprocess.TimeoutExpired:
   child.kill();stdout,stderr=child.communicate(timeout=3);save(out/'TIMEOUT.json',{'pid':child.pid,'exit':child.returncode,'stdout':stdout,'stderr':stderr});raise
  save(out/'COMMAND.json',{'argv':argv,'pid':child.pid,'exit':child.returncode,'stdout':stdout,'stderr':stderr});assert child.returncode==0;observed=json.loads(stdout);assert observed['domain_code']=='L2_CONTENTION_DEADLINE' and observed['native_errno']==13 and observed['native_winerror'] is None;assert not path.with_suffix('.json.pending').exists() and sha(path)==before
 assert sha(coord.guard_path)==control and not NETWORK
 save(out/'RESULT.json',{'verdict':'PASS','observed':observed,'pending_created':False,'main_unchanged':True,'guard_unchanged':True,'elapsed_seconds':time.monotonic()-start,'production_hashes':{p.relative_to(C).as_posix():sha(p) for p in (C/'cognitive_architecture_lab_v1/src/accounting').glob('*.py')},'not_in_unittest_count':True,'strong_authority_awarded':False});print('Final-source native contention receipt PASS; errno13, winerror=null; no pending.')
if __name__=='__main__':main()
