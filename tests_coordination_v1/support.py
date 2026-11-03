import ctypes,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from contextlib import contextmanager
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT.parent/'evidence'
NETWORK=[]
def audit(event,args):
 if event in {'socket.connect','socket.connect_ex','socket.getaddrinfo','socket.sendto'}:NETWORK.append(event);raise AssertionError('NO_NETWORK_IN_LEDGER_TEST')
sys.addaudithook(audit)
def request(run_id='run'):
 task={'task_id':'SYN-ONLY','title':'Synthetic echo','task_statement':'Return public word','input':{'word':'blue'},'output_contract':{'word':'string'},'public_reference_ids':[]}
 return RunRequest('SYN-ONLY',task,'dummy-no-model','dummy-v1',{'temperature':.7,'top_p':.8,'think':False},11,8192,4096,'DIRECT',36,30000,1800,run_id)
def save(p,data):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def spawn(root,mode,path,**kwargs):
 spec=Path(root)/(mode+'.request.json');save(spec,{'mode':mode,'path':str(path),'root':str(root),'kwargs':kwargs});p=subprocess.Popen([sys.executable,'-B',str(ROOT/'tests_coordination_v1/worker.py'),'--request',str(spec)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'});p.spec=spec;p.collected=False;return p
def collect(p,*,kill=False,timeout=5):
 if kill and p.poll() is None:p.kill()
 timed=False
 try:out,err=p.communicate(timeout=timeout)
 except subprocess.TimeoutExpired:
  timed=True;p.kill();out,err=p.communicate(timeout=3)
 p.collected=True;x={'pid':p.pid,'exit_code':p.returncode,'stdout':out,'stderr':err,'killed':kill,'unexpected_timeout':timed};result=p.spec.with_suffix('.result.json')
 if result.exists():x['result']=json.loads(result.read_text(encoding='utf-8'))
 save(p.spec.with_suffix('.exit.json'),x)
 if timed:raise AssertionError('UNEXPECTED_CHILD_TIMEOUT:'+str(p.spec))
 return x
def wait(path,p,seconds=5):
 deadline=time.monotonic()+seconds
 while not Path(path).exists():
  if p.poll() is not None:raise AssertionError('CHILD_EXITED_BEFORE_PHASE:'+str(path))
  if time.monotonic()>=deadline:raise AssertionError('MISSING_PHASE_DEADLINE:'+str(path))
  time.sleep(.01)
 return json.loads(Path(path).read_text(encoding='utf-8'))
@contextmanager
def pin(path):
 from ctypes import wintypes as wt
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);create=kernel.CreateFileW;create.argtypes=[wt.LPCWSTR,wt.DWORD,wt.DWORD,wt.LPVOID,wt.DWORD,wt.DWORD,wt.HANDLE];create.restype=wt.HANDLE;close=kernel.CloseHandle;close.argtypes=[wt.HANDLE];close.restype=wt.BOOL;h=create(str(Path(path).resolve()),0x80000000,1,None,3,0x80,None)
 if h==wt.HANDLE(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 try:yield
 finally:
  if not close(h):raise ctypes.WinError(ctypes.get_last_error())
