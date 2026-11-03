"""A0 test scaffolding only. Not an observer, adapter, or writer enrollment API."""
import argparse,base64,contextlib,ctypes,hashlib,importlib,json,msvcrt,os,shutil,subprocess,sys,threading,time,traceback
from ctypes import wintypes as wt
from pathlib import Path
from dataclasses import replace
HERE=Path(__file__).resolve().parent;CHECKOUT=Path(os.environ.get('A0_SOURCE_CHECKOUT',str(HERE.parents[1]))).resolve();R3=CHECKOUT/'experimental_architectures_v1_r3'
sys.dont_write_bytecode=True;sys.path[0:0]=[str(R3),str(CHECKOUT)]
from src.shared import publication as publication_module
from src.shared.publication import Publication
from src.shared.strict_json import canonical,read,sha
from src.shared.journals import verify_journals
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest
from runtime_isolation_v1.src.trusted_transport.transport import dispatch_lock,Gateway

COUNTERS={'forbidden_network_events':0,'forbidden_dispatch_or_reservation_calls':0}
CHILDREN=[]
CORE_AUDIT=None
FINISH_ENTRY_MARKER=None
def audit(event,args):
 if event in {'socket.connect','socket.connect_ex','socket.getaddrinfo','socket.sendto','urllib.Request','http.client.connect'}:
  COUNTERS['forbidden_network_events']+=1;raise AssertionError('A0_NETWORK_FORBIDDEN:'+event)
 if event=='open' and CORE_AUDIT is not None and not isinstance(args[0],int):
  p=Path(os.fsdecode(args[0])).resolve();mode=args[1];flags=args[2]
  if p.is_relative_to(CORE_AUDIT['root']):
   key=str(p)
   if key not in CORE_AUDIT['pinned'] and key not in CORE_AUDIT['controls']:raise AssertionError('CORE_OPEN_UNPINNED_RUN_INPUT:'+str(p))
   CORE_AUDIT['opens'].append({'path':key,'mode':mode,'flags':flags,'kind':'EXISTING_CONTROL' if key in CORE_AUDIT['controls'] else 'PINNED_DATA'})
sys.addaudithook(audit)
from src.adapters.gateway import StageTransport
from native_model_integration_v1.src.native_end_bridge.bridge import NativeGateway,RecordingTransport as NativeRecording
forbidden_codes={f.__code__ for f in [Ledger.reserve,Gateway.reserve_request,Gateway.dispatch,StageTransport.exchange,NativeGateway.attempt,NativeRecording.exchange]}
def call_guard(frame,event,arg):
 if event=='call' and frame.f_code in forbidden_codes:
  COUNTERS['forbidden_dispatch_or_reservation_calls']+=1;raise AssertionError('A0_DISPATCH_OR_RESERVATION_FORBIDDEN:'+frame.f_code.co_name)
 if event=='call' and FINISH_ENTRY_MARKER is not None and frame.f_code.co_name=='finish' and frame.f_code.co_filename.replace('\\','/').endswith('/src/shared/session.py'):
  write_json(FINISH_ENTRY_MARKER,{'phase':'UNCHANGED_SESSION_FINISH_ENTERED','pid':os.getpid()})
sys.setprofile(call_guard);threading.setprofile(call_guard)

K=ctypes.WinDLL('kernel32',use_last_error=True)
class INFO(ctypes.Structure):
 _fields_=[('attributes',wt.DWORD),('creation',wt.FILETIME),('access',wt.FILETIME),('write',wt.FILETIME),('volume',wt.DWORD),('size_hi',wt.DWORD),('size_lo',wt.DWORD),('links',wt.DWORD),('index_hi',wt.DWORD),('index_lo',wt.DWORD)]
K.CreateFileW.argtypes=[wt.LPCWSTR,wt.DWORD,wt.DWORD,wt.LPVOID,wt.DWORD,wt.DWORD,wt.HANDLE];K.CreateFileW.restype=wt.HANDLE
K.CloseHandle.argtypes=[wt.HANDLE];K.CloseHandle.restype=wt.BOOL
K.GetFileInformationByHandle.argtypes=[wt.HANDLE,ctypes.POINTER(INFO)];K.GetFileInformationByHandle.restype=wt.BOOL
K.ReadFile.argtypes=[wt.HANDLE,wt.LPVOID,wt.DWORD,ctypes.POINTER(wt.DWORD),wt.LPVOID];K.ReadFile.restype=wt.BOOL
K.GetFileSizeEx.argtypes=[wt.HANDLE,ctypes.POINTER(ctypes.c_longlong)];K.GetFileSizeEx.restype=wt.BOOL
def write_json(p,value):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def snapshot(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}

def collect_a018_namespace(root, known_controls, active_controls=None):
    """A0-18 evidence collection only; no strong snapshot/authority claim.

    Never infer operational status from a filename suffix. Every entry remains
    visible. Known active controls use their actual owned descriptors, not a
    blind second-handle read of a byte-locked region. All other read failures
    retain the exact path/operation and make collection incomplete.
    """
    import stat
    root=Path(root).resolve()
    known={str(Path(p).resolve()):role for p,role in known_controls.items()}
    active={str(Path(p).resolve()):guard for p,guard in (active_controls or {}).items()}
    expected_fixture_files=set(read(HERE/'source_profile.json')['template_files'])
    entries=[];errors=[];external=[]
    def role(path):
        key=str(path.resolve());rel=path.relative_to(root).as_posix()
        if key in known:return 'A_OPERATIONAL_CONTROL',known[key]
        if path.name.endswith(('.pending','.tmp','.temporary')):return 'C_PENDING_TEMPORARY_EVIDENCE','Pending/temporary evidence retained; never excluded'
        historical_role=(rel in {'budget.json','budget.closed.json','RESULT.json','publication/IDENTITY.json','publication/owner.json'} or (len(path.relative_to(root).parts)>1 and path.relative_to(root).parts[0] in {'wire','publication','budget.json.r2_bindings'}))
        if rel in expected_fixture_files and historical_role:
            return 'B_HISTORICAL_FIXTURE_EVIDENCE','Known fixture evidence namespace; no origin or certification assertion'
        return 'D_UNKNOWN_UNEXPECTED_MEMBER','No declared control/evidence role; retained without trusting its name'
    def unavailable(entry,operation,error):
        detail={'path':entry['path'],'operation':operation,'exception':type(error).__name__,'errno':getattr(error,'errno',None),'winerror':getattr(error,'winerror',None),'message':str(error)}
        entry.update(read_status='READ_FAILED',sha256=None,raw_base64=None,error=detail)
        errors.append(detail)
    def control_descriptor(entry,guard):
        if entry['path'] not in known or guard.fd is None or not guard.local_owned or str(guard.path.resolve())!=entry['path']:
            raise ValueError('A0_ACTIVE_CONTROL_NOT_AN_OWNED_DECLARED_GUARD:'+entry['path'])
        entry.update(active=True,identity=file_info(msvcrt.get_osfhandle(guard.fd)),read_status='NOT_READ_ACTIVE_LOCK_CONTROL',sha256=None,raw_base64=None,content_reason='Owned native byte-lock control: identity/metadata recorded without a second-handle byte read. No fabricated hash or observed read error.',descriptor_is_owned=True)
    def visit(directory):
        # scandir/lstat preserve unknown/dot/temporary entries and never traverse
        # reparse points. No .pending, dotfile or *.lock exclusion is applied.
        with os.scandir(directory) as scan:names=sorted(list(scan),key=lambda x:x.name.casefold())
        for item in names:
            path=Path(item.path);category,reason=role(path)
            entry={'path':str(path.resolve()),'relative_path':path.relative_to(root).as_posix(),'category':category,'classification_reason':reason,'active':False,'sha256':None,'raw_base64':None}
            metadata_operation='lstat'
            try:
                st=item.stat(follow_symlinks=False);entry['metadata']={'bytes':st.st_size,'mode':st.st_mode,'mtime_ns':st.st_mtime_ns,'file_attributes':getattr(st,'st_file_attributes',None)}
                reparse=bool(getattr(st,'st_file_attributes',0)&0x400)
                if stat.S_ISLNK(st.st_mode) or reparse:
                    entry.update(type='LINK_OR_REPARSE',read_status='NOT_FOLLOWED');errors.append({'path':str(path),'operation':'classify/follow','exception':'UnsupportedLink','message':'A0 evidence capture cannot safely read this member'})
                elif stat.S_ISDIR(st.st_mode):entry.update(type='DIRECTORY',read_status='NOT_APPLICABLE_DIRECTORY')
                elif stat.S_ISREG(st.st_mode):
                    entry['type']='FILE'
                    if entry['path'] in active:
                        metadata_operation='GetFileInformationByHandle(owned_control_fd)';control_descriptor(entry,active[entry['path']])
                    else:
                        operation='GetFileInformationByHandle(read-only metadata handle)'
                        try:
                            entry['identity']=identity(path);operation='open(rb)'
                            with path.open('rb') as stream:operation='read';raw=stream.read()
                            entry.update(read_status='BYTES_CAPTURED',sha256=sha(raw),raw_base64=base64.b64encode(raw).decode(),captured_bytes=len(raw))
                        except OSError as error:unavailable(entry,operation,error)
                else:
                    entry.update(type='UNSUPPORTED_ENTRY',read_status='NOT_READ');errors.append({'path':str(path),'operation':'classify','exception':'UnsupportedEntry','message':'Unknown entry type remains evidence, not a successful capture'})
            except OSError as error:unavailable(entry,metadata_operation,error)
            entries.append(entry)
            if entry.get('type')=='DIRECTORY':visit(path)
    visit(root)
    for path,guard in active.items():
        if not Path(path).is_relative_to(root):
            entry={'path':path,'type':'FILE','category':'A_OPERATIONAL_CONTROL','classification_reason':known.get(path),'metadata':{'bytes':os.fstat(guard.fd).st_size}}
            try:control_descriptor(entry,guard)
            except OSError as error:unavailable(entry,'GetFileInformationByHandle(owned_external_control_fd)',error)
            external.append(entry)
    return {'scope':'A0_18_EVIDENCE_INVENTORY_NOT_A_PRODUCTION_SNAPSHOT','root':str(root),'entries':entries,'external_active_controls':external,'required_read_failures':errors,'collection_complete_for_declared_A0_policy':not errors,'active_control_bytes_not_claimed':True,'A_or_S_authority_awarded':False,'all_namespace_categories_retained':True}
def ensure_inside(path,root):
 path=Path(path).resolve();assert path.is_relative_to(Path(root).resolve()),str(path);return path
def file_info(handle):
 i=INFO()
 if not K.GetFileInformationByHandle(handle,ctypes.byref(i)):raise ctypes.WinError(ctypes.get_last_error())
 return {'volume_serial':format(i.volume,'08x'),'file_index':format((i.index_hi<<32)|i.index_lo,'016x'),'links':i.links,'bytes':(i.size_hi<<32)|i.size_lo}
class Pins:
 def __init__(self,paths):self.paths=list(paths);self.handles=[];self.facts=[]
 def __enter__(self):
  try:
   for path in self.paths:
    h=K.CreateFileW(str(Path(path).resolve()),0x80000000,1,None,3,0x80,None)
    if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    self.handles.append(h);i=file_info(h);size=ctypes.c_longlong()
    if not K.GetFileSizeEx(h,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
    if size.value>64000000:raise ValueError('A0_FIXTURE_SIZE_BOUND')
    buf=ctypes.create_string_buffer(size.value or 1);n=wt.DWORD()
    if size.value and not K.ReadFile(h,buf,size.value,ctypes.byref(n),None):raise ctypes.WinError(ctypes.get_last_error())
    raw=buf.raw[:n.value];assert len(raw)==size.value
    self.facts.append({'path':str(Path(path).resolve()),'identity':i,'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode()})
   return self
  except BaseException:self.__exit__(None,None,None);raise
 def __exit__(self,*args):
  problems=[]
  for h in reversed(self.handles):
   if not K.CloseHandle(h):problems.append(ctypes.get_last_error())
  self.handles.clear()
  if problems:raise OSError('A0_HANDLE_CLOSE_FAILED:'+str(problems))
def identity(path):
 h=K.CreateFileW(str(Path(path).resolve()),0x80000000,7,None,3,0x80,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 try:return file_info(h)
 finally:K.CloseHandle(h)
def process_identity(pid):
 K.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD];K.OpenProcess.restype=wt.HANDLE
 K.GetProcessTimes.argtypes=[wt.HANDLE,ctypes.POINTER(wt.FILETIME),ctypes.POINTER(wt.FILETIME),ctypes.POINTER(wt.FILETIME),ctypes.POINTER(wt.FILETIME)];K.GetProcessTimes.restype=wt.BOOL
 h=K.OpenProcess(0x1000,False,pid)
 if not h:raise ctypes.WinError(ctypes.get_last_error())
 try:
  creation,exit,kernel,user=wt.FILETIME(),wt.FILETIME(),wt.FILETIME(),wt.FILETIME()
  if not K.GetProcessTimes(h,ctypes.byref(creation),ctypes.byref(exit),ctypes.byref(kernel),ctypes.byref(user)):raise ctypes.WinError(ctypes.get_last_error())
  return {'pid':pid,'creation_filetime':(creation.dwHighDateTime<<32)|creation.dwLowDateTime}
 finally:K.CloseHandle(h)
class ExistingLock:
 def __init__(self,path,timeout=.4,local=True):self.path=Path(path).resolve();self.timeout=min(timeout,5);self.fd=None;self.local=publication_module._LOCAL_LOCKS.setdefault(str(self.path),threading.RLock()) if local else None;self.local_owned=False
 def __enter__(self):
  start=time.monotonic();self.deadline=start+self.timeout
  if not self.path.is_file() or self.path.stat().st_size<1:raise FileNotFoundError('A0_EXISTING_NONEMPTY_GUARD_REQUIRED:'+str(self.path))
  if self.local is not None:
   if not self.local.acquire(timeout=max(0,self.deadline-time.monotonic())):raise TimeoutError('A0_LOCAL_GUARD_DEADLINE')
   self.local_owned=True
  try:
   self.fd=os.open(self.path,os.O_RDWR|os.O_BINARY)
   while True:
    try:os.lseek(self.fd,0,0);msvcrt.locking(self.fd,msvcrt.LK_NBLCK,1);break
    except OSError:
     if time.monotonic()>=self.deadline:raise TimeoutError('A0_NATIVE_GUARD_DEADLINE')
     time.sleep(min(.01,max(0,self.deadline-time.monotonic())))
   self.elapsed=time.monotonic()-start;return self
  except BaseException:
   if self.fd is not None:os.close(self.fd);self.fd=None
   if self.local_owned:self.local.release();self.local_owned=False
   raise
 def __exit__(self,*args):
  try:
   if self.fd is not None:os.lseek(self.fd,0,0);msvcrt.locking(self.fd,msvcrt.LK_UNLCK,1)
  finally:
   if self.fd is not None:os.close(self.fd);self.fd=None
   if self.local_owned:self.local.release();self.local_owned=False
def control(path):path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'0');return path
def wait(path,seconds=8):
 deadline=time.monotonic()+seconds
 while not Path(path).exists():
  if time.monotonic()>deadline:raise TimeoutError('A0_RENDEZVOUS_TIMEOUT:'+str(path))
  time.sleep(.01)
 return read(Path(path)) if Path(path).suffix=='.json' else Path(path).read_text(encoding='utf-8')
def spawn(mode,root,**kwargs):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);request=root/(mode+'-'+str(time.time_ns())+'.request.json');write_json(request,{'mode':mode,'root':str(root),'kwargs':{k:str(v) if isinstance(v,Path) else v for k,v in kwargs.items()}})
 p=subprocess.Popen([sys.executable,'-B',str(HERE/'probe_workers.py'),'--request',str(request)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'})
 p.a0_request=request;p.a0_collected=False;CHILDREN.append(p);return p
def collect(p,timeout=10,kill=False):
 if kill:p.kill()
 try:stdout,stderr=p.communicate(timeout=timeout)
 except subprocess.TimeoutExpired:
  p.kill();stdout,stderr=p.communicate();p.a0_collected=True;write_json(p.a0_request.with_suffix('.timeout.json'),{'pid':p.pid,'exit_code':p.returncode,'stdout':stdout,'stderr':stderr});raise
 receipt={'pid':p.pid,'exit_code':p.returncode,'stdout':stdout,'stderr':stderr,'request':str(p.a0_request),'killed_by_parent':kill}
 result=p.a0_request.with_suffix('.result.json')
 if result.exists():receipt['worker_result']=read(result)
 p.a0_collected=True;write_json(p.a0_request.with_suffix('.exit.json'),receipt);return receipt

def context(root,blueprint=None):
 root=Path(root).resolve();data=blueprint if blueprint is not None else read(root/'RESULT.json');ident=read(root/'publication/IDENTITY.json');ledger=object.__new__(Ledger);ledger.path=root/'budget.json';ledger.limits=read(ledger.path)['state']['limits']
 pub=object.__new__(Publication);pub.directory=root;pub.meta=root/'publication';pub.ledger=ledger;pub.identity=ident;pub.identity_sha=sha(canonical(ident));pub.request=RunRequest(**data['request']);pub.effective=RunRequest(**data['effective_ledger_request']);pub.mode=ident['mode'];pub.final=root/'RESULT.json';pub.guard=root/'.publication.lock';pub.owner_path=pub.meta/'owner.json';pub.lease_path=pub.meta/'owner.lock';pub.fd=None;pub.fence=None;pub.token=None;pub.detached=False;pub.context=None
 assert ident['output_directory']==str(root) and ident['ledger_path']==str(ledger.path.resolve())
 return pub
def clone_fixture(target):
 target=Path(target).resolve();assert not target.exists();profile=read(HERE/'source_profile.json');source=Path(profile['template'])
 assert all(sha((source/n).read_bytes())==v['sha256'] for n,v in profile['template_files'].items())
 shutil.copytree(source,target);data=read(target/'RESULT.json');ident=read(target/'publication/IDENTITY.json');ident.update(output_directory=str(target),ledger_path=str(target/'budget.json'));newhash=sha(canonical(ident));(target/'publication/IDENTITY.json').write_bytes(canonical(ident))
 for p in (target/'budget.json.r2_bindings').glob('*.json'):
  x=read(p)
  if x.get('run_id')==ident['run_id']:p.write_bytes(canonical(ident))
 owner=read(target/'publication/owner.json');owner['identity_sha256']=newhash;(target/'publication/owner.json').write_bytes(canonical(owner))
 for p in (target/'publication/attempts').glob('*.json'):
  x=read(p)
  if 'identity_sha256' in x:x['identity_sha256']=newhash;p.write_bytes(canonical(x))
 for p in (target/'publication/attempts').glob('*.settlement.json'):
  x=read(p);aid=str(x['attempt_id']).zfill(6);x['dispatch_anchor_sha256']=sha((p.parent/(aid+'.json')).read_bytes());response=p.parent/(aid+'.response.json');x['response_anchor_sha256']=sha(response.read_bytes()) if response.exists() else None;p.write_bytes(canonical(x))
 pub=context(target,data);report=verify_journals(pub);assert report['overall']=='VERIFIED',report
 data['publication_identity_sha256']=newhash;data['journal_integrity']=report;data['durable_journal_hashes']=report['trusted_hashes'];data.pop('artifact_payload_sha256',None);data['artifact_payload_sha256']=sha(canonical(data));raw=(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode();(target/'RESULT.json').write_bytes(raw)
 anchor=target/'publication/prepared'/(data['publication']['token']+'.json');a=read(anchor);a.update(identity_sha256=newhash,payload_sha256=data['artifact_payload_sha256'],result_file_sha256=sha(raw));anchor.write_bytes(canonical(a))
 # This is synthetic relocation/checksum construction, NOT historical witness creation.
 pub._verify_completed();control(target/'.a0-L2.lock')
 write_json(target.parent/(target.name+'.clone_receipt.json'),{'template':str(source),'template_file_hashes':profile['template_files'],'purpose':'A0_SYNTHETIC_REBASED_COPY_NOT_PROVIDER_EXECUTION_OR_ORIGIN_ATTESTATION','new_root':str(target),'identity_sha256':newhash,'new_attempts_reserved':0,'model_dispatches':0,'source_core_setup_check':'PASS_NOT_CAPTURE_TEST'})
 return pub
def data_paths(root):return [p for p in Path(root).rglob('*') if p.is_file() and not p.name.endswith('.lock')]
def protected_core(pub):
 global CORE_AUDIT
 paths=data_paths(pub.directory);static=list((R3/'public_inputs').rglob('*.json'))+[R3/'validation/APPROVED_PUBLIC_INPUTS.json',R3/'validation/PROMPT_HASHES.json']
 before=snapshot(pub.directory);events=[]
 with ExistingLock(pub.guard),ExistingLock(pub.directory/'.a0-L2.lock'),Pins(paths+static) as pins:
  pinned={x['path'] for x in pins.facts};controls={str(p.resolve()) for p in pub.directory.rglob('*.lock')};CORE_AUDIT={'root':pub.directory,'pinned':pinned,'controls':controls,'opens':events}
  try:
   value=pub._verify_completed();status={'passed':True,'payload_sha256':value['artifact_payload_sha256'],'provenance':value['journal_integrity']['overall']}
  except BaseException as e:status={'passed':False,'exception':type(e).__name__,'message':str(e),'cause':type(e.__cause__).__name__ if e.__cause__ else None,'traceback':traceback.format_exc()}
  finally:CORE_AUDIT=None
  buffers=[{'path':x['path'],'identity':x['identity'],'sha256':x['sha256']} for x in pins.facts]
 after=snapshot(pub.directory);assert before==after,'NONOWNING_CORE_MUTATED_SOURCE';assert pub.fd is None and pub.fence is None and pub.token is None
 return {'core':status,'source_bytes_unchanged':True,'opens':events,'pinned_buffers':buffers,'no_owner_fd_fence_or_token':True}

def perform(req):
 global FINISH_ENTRY_MARKER
 mode=req['mode'];root=Path(req['root']).resolve();k=req['kwargs'];events=[]
 def path(name):return ensure_inside(k[name],root.parent if name in ['target','guard','L1','L2','gate','ready','release','go','fixture'] else root)
 if mode=='lock_hold':
  with ExistingLock(path('guard'),2):
   write_json(path('ready'),{'pid':os.getpid(),'phase':'LOCK_HELD','identity':identity(path('guard'))});wait(path('release'),10)
 elif mode=='recursive':
  guard=path('guard');ledger=None
  if k['kind']=='L3':ledger=object.__new__(Ledger);ledger.path=Path(k['ledger']);ledger.limits=read(ledger.path)['state']['limits'];cm=ledger.lock()
  else:cm=dispatch_lock(guard)
  with cm:
   write_json(path('ready'),{'phase':'FIRST_LOCK_HELD','pid':os.getpid()})
   try:
    if ledger is not None:ledger.state()
    else:
     with dispatch_lock(guard):events.append('RECURSION_ADMITTED_NOT_USED_BY_OBSERVER')
   except BaseException as e:events.append({'event':'NATIVE_RECURSION_REFUSED','exception':type(e).__name__,'message':str(e),'winerror':getattr(e,'winerror',None)})
 elif mode=='mutate':
  target=path('target')
  for op in k.get('operations',['write']):
   try:
    if op=='write':target.write_bytes(b'A0_CHILD_WRITE')
    elif op=='delete':target.unlink()
    elif op=='replace':q=target.with_suffix('.replacement');q.write_bytes(b'A0_REPLACEMENT');os.replace(q,target)
    events.append({'operation':op,'outcome':'MUTATED'})
   except OSError as e:events.append({'operation':op,'outcome':'DENIED','exception':type(e).__name__,'errno':e.errno,'winerror':getattr(e,'winerror',None),'message':str(e)})
 elif mode=='observer':
  with ExistingLock(path('L1'),3),ExistingLock(path('L2'),3):
   start=time.monotonic();time.sleep(.04);events.append({'enter':start,'exit':time.monotonic(),'L2_identity':identity(path('L2')),'pid':os.getpid()})
 elif mode=='kill_holder':
  with ExistingLock(path('L1')),ExistingLock(path('L2')),Pins([path('target')]):
   write_json(path('ready'),{'phase':'ALL_TEST_RESOURCES_HELD','pid':os.getpid()});time.sleep(60)
 elif mode=='admitted_writer':
  if k.get('attempting'):write_json(Path(k['attempting']),{'phase':'COOPERATING_ADMISSION_ATTEMPT','pid':os.getpid()})
  with ExistingLock(path('gate'),3):write_json(path('ready'),{'phase':'ADMITTED','pid':os.getpid()})
  try:
   with ExistingLock(path('L1'),3):time.sleep(.08);path('target').write_bytes(b'WRITER_FINISHED')
  finally:write_json(Path(k['finished']),{'phase':'FINALLY_LOG_COMPLETE','pid':os.getpid()})
 elif mode=='register_bypass':
  pub=context(path('fixture'));q=replace(pub.request,run_id='A0_UNENROLLED_REGISTER');before=sha(pub.ledger.path.read_bytes());pending=pub.ledger.path.with_suffix(pub.ledger.path.suffix+'.pending')
  try:pub.ledger.register(q);events.append({'operation':'UNCHANGED_LEDGER_REGISTER','outcome':'RETURNED'})
  except BaseException as e:events.append({'operation':'UNCHANGED_LEDGER_REGISTER','outcome':'RAISED','exception':type(e).__name__,'winerror':getattr(e,'winerror',None),'message':str(e)})
  events.append({'ledger_before':before,'ledger_after':sha(pub.ledger.path.read_bytes()),'pending_created':pending.exists(),'pending_sha256':sha(pending.read_bytes()) if pending.exists() else None,'attempt_rows_after':len(pub.ledger.state()['attempts'])})
 elif mode=='finalize':
  fixture=path('fixture');blueprint=read(Path(k['blueprint']));q=RunRequest(**blueprint['request']);ledger=Ledger(fixture/'budget.json');from src.shared.session import Session;from src.adapters.script import Script
  script=Script({});s=Session(q,script,fixture,ledger);s.restore_without_dispatch();write_json(path('ready'),{'phase':'ADMITTED_RESTORED_NO_DISPATCH','pid':os.getpid()});wait(path('go'));FINISH_ENTRY_MARKER=k.get('finish_entry');r=s.finish('INTERRUPTED');FINISH_ENTRY_MARKER=None;events.append({'outcome':'ACTUAL_FINAL_PUBLISHED','payload_sha256':r['artifact_payload_sha256'],'file_sha256':sha((fixture/'RESULT.json').read_bytes()),'script_seen':script.seen,'attempt_rows':len(ledger.state()['attempts'])})
 elif mode=='duplicate_origin':
  first=publication_module;second=importlib.import_module('experimental_architectures_v1_r3.src.shared.publication');events.append({'same_file':Path(first.__file__).resolve()==Path(second.__file__).resolve(),'distinct_class_identity':first.Publication is not second.Publication,'distinct_lock_maps':first._LOCAL_LOCKS is not second._LOCAL_LOCKS,'decision':'REJECT_DUPLICATE_MODULE_ORIGIN_NO_STRONG_DOMAIN'})
 elif mode=='live_owner':
  pub=context(path('fixture'));pub._take_lease()
  try:
   with ExistingLock(pub.guard,2):write_json(path('ready'),{'phase':'TEST_OWNER_LEASE_AND_L1_HELD','pid':os.getpid()});wait(path('release'))
  finally:pub.release()
 else:raise AssertionError('UNKNOWN_A0_WORKER_MODE:'+mode)
 return {'events':events,'counters':dict(COUNTERS)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);args=ap.parse_args();request=Path(args.request);req=read(request)
 try:out=perform(req);out['worker_operation_completed']=True;code=0
 except BaseException as e:out={'worker_operation_completed':False,'exception':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'counters':dict(COUNTERS)};code=1
 write_json(request.with_suffix('.result.json'),out);print(json.dumps(out));raise SystemExit(code)
