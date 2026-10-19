"""Single durable global ledger. OS advisory lock serializes cooperating writers.
Not tamper-proof storage or a defense against malicious trusted orchestration.
Unknown usage/outstanding reservations stop new dispatch, including after restart.
"""
import copy,hashlib,json,os,time
from contextlib import contextmanager
from pathlib import Path
from ..interfaces.contracts import canonical,finite,positive_int,digest
class BudgetStop(RuntimeError):pass
class Ledger:
    def __init__(self,path,*,global_attempts=136,global_tokens=400000,global_seconds=10800):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.limits={'attempts':positive_int(global_attempts),'tokens':positive_int(global_tokens),'seconds':finite(global_seconds,True)}
        if global_attempts>136 or global_tokens>400000 or global_seconds>10800:raise ValueError('Frozen global ceilings exceeded')
        with self.lock():
            if self.path.exists():self._read()
            else:self._write({'schema_version':'lab-ledger-v1','limits':self.limits,'runs':{},'attempts':[],'halted':False})
    @contextmanager
    def lock(self):
        lockpath=self.path.with_suffix(self.path.suffix+'.lock')
        with lockpath.open('a+b') as f:
            f.seek(0,2)
            if f.tell()==0:f.write(b'0');f.flush()
            f.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(f.fileno(),msvcrt.LK_LOCK,1)
            else:
                import fcntl
                fcntl.flock(f,fcntl.LOCK_EX)
            try:yield
            finally:
                f.seek(0)
                if os.name=='nt':msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
                else:fcntl.flock(f,fcntl.LOCK_UN)
    def _read(self):
        envelope=json.loads(self.path.read_text(encoding='utf-8'))
        s=envelope['state']
        if envelope['state_sha256']!=digest(s) or s['schema_version']!='lab-ledger-v1' or s['limits']!=self.limits:raise ValueError('Ledger integrity/identity mismatch')
        return s
    def _write(self,s):
        raw=canonical({'state':s,'state_sha256':digest(s)})
        staging=self.path.with_suffix(self.path.suffix+'.pending')
        with staging.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(staging,self.path)
    def state(self):
        with self.lock():return copy.deepcopy(self._read())
    def register(self,request):
        with self.lock():
            s=self._read();contract={'identity':digest(request.private_metadata()|{'wire':request.wire()}),'attempts':request.attempt_budget,'tokens':request.token_budget,'seconds':request.wall_time_budget}
            if request.run_id in s['runs'] and s['runs'][request.run_id]!=contract:raise ValueError('Resume changed run contract')
            s['runs'][request.run_id]=contract;self._write(s)
    def reserve(self,run_id,purpose,token_ceiling,seconds_ceiling):
        positive_int(token_ceiling);finite(seconds_ceiling,True)
        if not isinstance(purpose,str) or not purpose:raise ValueError('Missing attempt purpose')
        with self.lock():
            s=self._read();all_a=s['attempts'];r=s['runs'][run_id];own=[a for a in all_a if a['run_id']==run_id]
            if s['halted'] or any(a['state']=='RESERVED' or a['total_tokens'] is None or a['seconds'] is None for a in all_a):raise BudgetStop('Unknown or outstanding consumption; reconcile externally before any new dispatch')
            if len(all_a)>=self.limits['attempts'] or len(own)>=r['attempts']:raise BudgetStop('BUDGET_EXHAUSTED: attempts')
            for rows,limits in ((all_a,self.limits),(own,r)):
                if sum(a['total_tokens'] for a in rows)+token_ceiling>limits['tokens']:raise BudgetStop('BUDGET_EXHAUSTED: tokens')
                if sum(a['seconds'] for a in rows)+seconds_ceiling>limits['seconds']:raise BudgetStop('TIME_EXHAUSTED')
            a={'attempt_id':len(all_a)+1,'run_id':run_id,'purpose':purpose,'state':'RESERVED','token_ceiling':token_ceiling,'seconds_ceiling':seconds_ceiling,'input_tokens':None,'output_tokens':None,'total_tokens':None,'seconds':None,'started_unix':time.time(),'error_code':None,'response_sha256':None}
            all_a.append(a);self._write(s);return a['attempt_id']
    def finish(self,attempt_id,*,state,input_tokens=None,output_tokens=None,seconds=None,error_code=None,response_sha256=None,response_text=None,candidate=None):
        if response_text is not None and not isinstance(response_text,str):raise ValueError('Invalid response text')
        if response_text is not None:
            h=hashlib.sha256(response_text.encode('utf-8')).hexdigest()
            if response_sha256 is not None and response_sha256!=h:raise ValueError('Response digest mismatch')
            response_sha256=h
        canonical(candidate)
        if state not in ('SUCCEEDED','FAILED','CANCELED','INTERRUPTED','PROTOCOL_FAILURE'):raise ValueError('Unknown attempt state')
        for x in (input_tokens,output_tokens):
            if x is not None and (type(x) is not int or x<0):raise ValueError('Invalid usage')
        if seconds is not None:finite(seconds)
        with self.lock():
            s=self._read();a=s['attempts'][attempt_id-1]
            if a['attempt_id']!=attempt_id or a['state']!='RESERVED':raise ValueError('Attempt already settled or absent')
            total=input_tokens+output_tokens if input_tokens is not None and output_tokens is not None else None
            if total is not None and total>a['token_ceiling'] or seconds is not None and seconds>a['seconds_ceiling']:s['halted']=True
            a.update(state=state,input_tokens=input_tokens,output_tokens=output_tokens,total_tokens=total,seconds=seconds,error_code=error_code,response_sha256=response_sha256,response_text=response_text,candidate=copy.deepcopy(candidate))
            self._write(s)
    def summary(self,run_id):
        s=self.state();rows=[a for a in s['attempts'] if a['run_id']==run_id]
        def measured(k):return sum(a[k] for a in rows) if all(a[k] is not None for a in rows) else None
        return {'physical_attempts':len(rows),'input_tokens':measured('input_tokens'),'output_tokens':measured('output_tokens'),'total_tokens':measured('total_tokens'),'wall_time':measured('seconds'),'known_token_subset':sum(a['total_tokens'] or 0 for a in rows),'unknown_usage_attempts':sum(a['total_tokens'] is None for a in rows),'outstanding_attempts':sum(a['state']=='RESERVED' for a in rows),'attempts':rows,'halted':s['halted']}
