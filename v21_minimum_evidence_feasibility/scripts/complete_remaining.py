"""Execute only two previously unexecuted approved controls, never retry N12."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 original=json.loads((ROOT/'_control/CONTROL_EXECUTION.json').read_text(encoding='utf-8'));assert not original['all_scheduled_commands_passed']
 assert [x['name'] for x in original['schedule'] if x['status']=='NOT_EXECUTED_AFTER_FAILURE']==['COOPERATING_POSITIVE','N01_N02']
 assert not (ROOT/'_control/REMAINING_CONTROL_EXECUTION.json').exists()
 save(ROOT/'_control/CONTINUATION_SCOPE.json',{'reason':'Owner mission requires the twelve categories. Original scheduler stopped on N12 incorrect WinError-specific assertion; its FAIL, exit1, exact code and all raw evidence stay immutable. Complete only the other two originally planned and still unexecuted controls, once each, without changing the profile or any assertion. No negative result is rerun or turned green.','N12':'FAIL_NOT_RETRIED','production_changes':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'unchanged_profile_script_sha256':hashlib.sha256((ROOT/'scripts/probe_profile.py').read_bytes()).hexdigest()})
 receipts=[]
 for case in ['COOPERATING_POSITIVE','N01_N02']:
  assert not (ROOT/'runs/native'/case).exists();argv=[sys.executable,'-B',str(ROOT/'scripts/probe_profile.py'),'--case',case];start=time.monotonic();began=datetime.datetime.now(datetime.timezone.utc).isoformat();proc=subprocess.Popen(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1','A0_SOURCE_CHECKOUT':'E:/The End Engine/v21_A0_feasibility/checkout'});timeout=False;cleanup=None
  try:out,err=proc.communicate(timeout=60)
  except subprocess.TimeoutExpired:
   timeout=True;k=subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,text=True);cleanup={'exit':k.returncode,'stdout':k.stdout,'stderr':k.stderr};out,err=proc.communicate(timeout=10)
  elapsed=time.monotonic()-start;receipt={'name':case,'argv':argv,'pid':proc.pid,'started_utc':began,'observed_exit_code':proc.returncode,'elapsed_seconds':elapsed,'watchdog_seconds':60,'bound_satisfied':not timeout and elapsed<60,'timed_out':timeout,'stdout':out,'stderr':err,'cleanup':cleanup,'execution_attempts':1,'status':'PASS' if proc.returncode==0 and not timeout and elapsed<60 else 'FAIL'};receipts.append(receipt);save(ROOT/'_control/commands'/('remaining_'+case+'.json'),receipt);print(json.dumps({k:receipt[k] for k in ('name','observed_exit_code','status','elapsed_seconds')}),flush=True)
  if receipt['status']=='FAIL':break
 save(ROOT/'_control/REMAINING_CONTROL_EXECUTION.json',{'original_schedule_preserved':True,'original_N12_remains_FAIL':True,'profile_count':1,'only_previously_unexecuted_controls':True,'receipts':receipts,'all_required_controls_green':False})
 return 0 if len(receipts)==2 and all(x['status']=='PASS' for x in receipts) else 1
if __name__=='__main__':raise SystemExit(main())
