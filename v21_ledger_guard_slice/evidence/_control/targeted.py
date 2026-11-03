"""Author targeted controls, not independent acceptance or runtime readiness."""
import hashlib,json,os,sys,time,unittest
from pathlib import Path
E=Path(__file__).resolve().parents[1];C=E.parent/'checkout';sys.path.insert(0,str(C))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 attempt=sys.argv[1] if len(sys.argv)>1 else 'attempt_001';assert attempt in ('attempt_001','attempt_002','attempt_003','attempt_004')
 output=E/'runs/targeted'/attempt;assert not output.exists();output.mkdir(parents=True);os.environ['LEDGER_TEST_OUTPUT']=str(output)
 files=[C/'cognitive_architecture_lab_v1/src/accounting/ledger.py',C/'cognitive_architecture_lab_v1/src/accounting/coordination.py',*(C/'tests_coordination_v1').glob('*.py')];save(output/'EXECUTED_SOURCE.json',{'files':{p.relative_to(C).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'python':sys.version,'source_commit_base':'783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e','author_testing_only':True})
 records={}
 class Result(unittest.TextTestResult):
  def startTest(self,test):records[test.id()]={'id':test.id(),'status':'PASS','start':time.monotonic()};super().startTest(test)
  def stopTest(self,test):records[test.id()]['elapsed_seconds']=time.monotonic()-records[test.id()].pop('start');super().stopTest(test)
  def addFailure(self,test,err):records[test.id()].update(status='FAIL',message=str(err[1]),exception_type=err[0].__name__);super().addFailure(test,err)
  def addError(self,test,err):records[test.id()].update(status='ERROR',message=str(err[1]),exception_type=err[0].__name__);super().addError(test,err)
  def addSkip(self,test,reason):records[test.id()].update(status='SKIP',reason=reason);super().addSkip(test,reason)
 start=time.monotonic()
 with (output/'unittest.log').open('w',encoding='utf-8') as log:
  suite=unittest.defaultTestLoader.loadTestsFromName('tests_coordination_v1.test_coordination');result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Result).run(suite)
 report={'attempt':attempt,'testsRun':result.testsRun,'PASS':sum(x['status']=='PASS' for x in records.values()),'FAIL':len(result.failures),'ERROR':len(result.errors),'SKIP':len(result.skipped),'all_passed':result.wasSuccessful(),'test_outcomes':list(records.values()),'raw_failures':[{'id':t.id(),'traceback':tb} for t,tb in result.failures],'raw_errors':[{'id':t.id(),'traceback':tb} for t,tb in result.errors],'elapsed_seconds':time.monotonic()-start,'strong_authority_awarded':False,'independent_acceptance':False,'retained_previous_results':[str(p.relative_to(E)) for p in (E/'runs/targeted').glob('*/RESULT.json')]};save(output/'RESULT.json',report);save(E/'TARGETED_TEST_RESULTS.json',report);print(json.dumps({k:report[k] for k in ('testsRun','PASS','FAIL','ERROR','SKIP','all_passed','elapsed_seconds')}),flush=True);return 0 if result.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
