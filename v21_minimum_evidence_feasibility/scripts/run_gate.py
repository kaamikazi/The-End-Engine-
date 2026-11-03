"""Finite, single-attempt subprocess schedule; no runtime or benchmark entry point."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONDITIONS=('DIRECT','SELF_REFLECT','FROZEN_CURRENT_END','SPARSE_DELIBERATION','DIRECTED_REPAIR','BOUNDED_ALTERNATIVES')
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert (ROOT/'_control/OWNER_APPROVAL.json').exists() and (ROOT/'_control/BEFORE.json').exists()
 assert not (ROOT/'_control/CONTROL_EXECUTION.json').exists()
 hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in (ROOT/'scripts',ROOT/'support/harness') for p in folder.glob('*') if p.is_file()}
 save(ROOT/'_control/EXECUTED_SCRIPT_HASHES.json',{'files':hashes,'source_checkout':'E:/The End Engine/v21_A0_feasibility/checkout','source_commit':'783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e','profile_count':1,'retries_per_command':0})
 schedule=[('SOURCE_CENSUS','inspect_sources.py',[],'INSPECTION')]
 schedule += [('POSITIVE_'+c,'check_positive.py',['--condition',c],'CONTROL') for c in CONDITIONS]
 schedule += [('N'+str(i).zfill(2),'test_evidence_faults.py',['--case','N'+str(i).zfill(2)],'CONTROL') for i in range(3,12)]
 schedule += [('N12','probe_profile.py',['--case','N12'],'CONTROL'),('COOPERATING_POSITIVE','probe_profile.py',['--case','COOPERATING_POSITIVE'],'CONTROL'),('N01_N02','probe_profile.py',['--case','N01_N02'],'CONTROL')]
 receipts=[];stopped=False
 for step,(name,script,args,role) in enumerate(schedule,1):
  if stopped:
   receipts.append({'step':step,'name':name,'role':role,'status':'NOT_EXECUTED_AFTER_FAILURE'});continue
  command=[sys.executable,'-B',str(ROOT/'scripts'/script),*args];start=time.monotonic();began=datetime.datetime.now(datetime.timezone.utc).isoformat();proc=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1','A0_SOURCE_CHECKOUT':'E:/The End Engine/v21_A0_feasibility/checkout'})
  timed_out=False;cleanup=None
  try:stdout,stderr=proc.communicate(timeout=60)
  except subprocess.TimeoutExpired:
   timed_out=True;kill=subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,text=True);cleanup={'argv':['taskkill','/PID',str(proc.pid),'/T','/F'],'exit':kill.returncode,'stdout':kill.stdout,'stderr':kill.stderr};stdout,stderr=proc.communicate(timeout=10)
  elapsed=time.monotonic()-start;record={'step':step,'name':name,'role':role,'argv':command,'pid':proc.pid,'started_utc':began,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observed_exit_code':proc.returncode,'elapsed_seconds':elapsed,'watchdog_seconds':60,'timed_out':timed_out,'bound_satisfied':not timed_out and elapsed<60,'stdout':stdout,'stderr':stderr,'cleanup':cleanup,'execution_attempts':1,'status':'PASS' if proc.returncode==0 and not timed_out and elapsed<60 else 'FAIL'}
  save(ROOT/'_control/commands'/(str(step).zfill(2)+'_'+name+'.json'),record);receipts.append(record);print(json.dumps({'step':step,'name':name,'role':role,'status':record['status'],'exit':proc.returncode,'elapsed_seconds':elapsed}),flush=True)
  if record['status']=='FAIL':stopped=True
 save(ROOT/'_control/CONTROL_EXECUTION.json',{'schedule':receipts,'all_scheduled_commands_passed':not stopped,'profile_count':1,'last_planned_fault':'N01_N02','profile_stopped_after_known_bypass':not stopped,'historical_runners_executed':0,'model_or_algorithm_generation_runs':0,'new_provider_calls':0,'new_reservations':0,'scientific_scores':None})
 return 0 if not stopped else 1
if __name__=='__main__':raise SystemExit(main())
