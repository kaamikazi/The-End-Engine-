"""Run original unittest suites in isolated processes; retain baseline failures."""
import datetime,json,os,subprocess,sys,time,traceback,unittest
from pathlib import Path
E=Path(__file__).resolve().parents[1];C=E.parent/'checkout'
SUITES={'engine':C,'lab':C/'cognitive_architecture_lab_v1','isolation':C/'runtime_isolation_v1','native':C/'native_model_integration_v1','r3':C/'experimental_architectures_v1_r3'}
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def child(stage,name):
 root=SUITES[name];out=E/'regressions'/stage/name;out.mkdir(parents=True,exist_ok=True);net=[]
 def audit(event,args):
  if event in {'socket.connect','socket.connect_ex','socket.getaddrinfo','socket.sendto'}:net.append(event);raise PermissionError('OFFLINE_REGRESSION_NETWORK_DENIED')
 sys.addaudithook(audit);sys.path[:0]=[str(root),str(C)];records={};subs=[]
 class Result(unittest.TextTestResult):
  def startTest(self,test):records[test.id()]={'id':test.id(),'status':'PASS'};super().startTest(test)
  def addFailure(self,test,err):records.setdefault(test.id(),{'id':test.id()}).update(status='FAIL',exception_type=err[0].__name__,message=str(err[1]));super().addFailure(test,err)
  def addError(self,test,err):records.setdefault(test.id(),{'id':test.id()}).update(status='ERROR',exception_type=err[0].__name__,message=str(err[1]));super().addError(test,err)
  def addSkip(self,test,reason):records.setdefault(test.id(),{'id':test.id()}).update(status='SKIP',reason=reason);super().addSkip(test,reason)
  def addExpectedFailure(self,test,err):records[test.id()]['status']='EXPECTED_FAILURE';super().addExpectedFailure(test,err)
  def addUnexpectedSuccess(self,test):records[test.id()]['status']='UNEXPECTED_SUCCESS';super().addUnexpectedSuccess(test)
  def addSubTest(self,test,subtest,err):
   row={'parent':test.id(),'id':subtest.id(),'status':'PASS' if err is None else 'FAIL' if issubclass(err[0],test.failureException) else 'ERROR'}
   if err:row.update(exception_type=err[0].__name__,message=str(err[1]));records[test.id()]['status']=row['status']
   subs.append(row);super().addSubTest(test,subtest,err)
 start=time.monotonic()
 with (out/'unittest.log').open('w',encoding='utf-8') as log:
  suite=unittest.defaultTestLoader.discover(str(root/'tests'),top_level_dir=str(root));result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Result).run(suite)
 report={'stage':stage,'suite':name,'python':sys.version,'testsRun':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'expected_failures':len(result.expectedFailures),'unexpected_successes':len(result.unexpectedSuccesses),'successful':result.wasSuccessful(),'test_outcomes':list(records.values()),'subtest_outcomes':subs,'raw_failures':[{'id':t.id(),'traceback':tb} for t,tb in result.failures],'raw_errors':[{'id':t.id(),'traceback':tb} for t,tb in result.errors],'network_attempts_denied':net,'elapsed_seconds':time.monotonic()-start};save(out/'RESULT.json',report);print(json.dumps({k:report[k] for k in ('stage','suite','testsRun','failures','errors','skipped','successful','elapsed_seconds')}),flush=True);return 0 if result.wasSuccessful() else 1
def main(stage):
 receipts=[];tmp=E/'regressions'/stage/'tmp';tmp.mkdir(parents=True,exist_ok=True)
 for name in SUITES:
  out=E/'regressions'/stage/name;assert not (out/'RESULT.json').exists();argv=[sys.executable,'-B',str(Path(__file__).resolve()),stage,name];start=time.monotonic();p=subprocess.Popen(argv,cwd=SUITES[name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1','TEMP':str(tmp),'TMP':str(tmp)});timeout=False
  try:stdout,stderr=p.communicate(timeout=240)
  except subprocess.TimeoutExpired:
   timeout=True;subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True);stdout,stderr=p.communicate(timeout=10)
  receipt={'suite':name,'argv':argv,'pid':p.pid,'exit_code':p.returncode,'stdout':stdout,'stderr':stderr,'timed_out':timeout,'elapsed_seconds':time.monotonic()-start};save(out/'COMMAND.json',receipt);receipts.append(receipt);print(stdout.strip() or json.dumps(receipt),flush=True)
  if timeout:break
 save(E/'regressions'/stage/'COMMANDS.json',receipts)
 return 0 if len(receipts)==len(SUITES) and not any(x['timed_out'] for x in receipts) else 1
if __name__=='__main__':raise SystemExit(child(sys.argv[1],sys.argv[2]) if len(sys.argv)>2 else main(sys.argv[1]))
