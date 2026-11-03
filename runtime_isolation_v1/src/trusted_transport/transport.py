"""One final byte serialization path, backed exclusively by an offline recorder.
No SDK, credential lookup, HTTP endpoint, eval/exec/plugin, shell or model callback.
"""
import json,os,secrets
from contextlib import contextmanager
from pathlib import Path
from ..sealed_requests.boundary import Compiler,SealedModelRequest,inspect_final_wire,sha
from ..capability_policy.policy import BoundaryError,require_empty_defaults
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger,BudgetStop
from cognitive_architecture_lab_v1.src.interfaces.contracts import canonical

class DuplicateDispatch(BoundaryError):pass
class GenerationClosed(BoundaryError):pass
class TransportFailure(RuntimeError):pass

@contextmanager
def dispatch_lock(path):
    # Distinct outer OS lock wraps duplicate-check/reserve/exchange/finish and closure.
    # Inner legacy ledger lock remains unchanged. Cooperating sequential writers only.
    path=Path(path)
    with path.open('a+b') as f:
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

def response_bytes(text='dummy',input_tokens=3,output_tokens=2,seconds=.01,tool_calls=None):
    return canonical({'text':text,'input_tokens':input_tokens,'output_tokens':output_tokens,'seconds':seconds,'tool_calls':[] if tool_calls is None else tool_calls})

class RecordingTransport:
    def __init__(self,responses=(),*,defaults=None,failure=None):
        self.defaults={} if defaults is None else defaults;require_empty_defaults(self.defaults)
        if failure not in (None,'BEFORE_SEND','AFTER_SEND','CANCEL','MISSING','INTERRUPT'):raise BoundaryError('Unknown canned failure')
        if any(type(r) is not bytes for r in responses):raise BoundaryError('Canned wire responses only; no callbacks')
        self.responses=list(responses);self.failure=failure;self.sent=[];self.provider_logs=[]
    def exchange(self,body):
        require_empty_defaults(self.defaults);inspect_final_wire(body)
        if self.failure=='BEFORE_SEND':raise TransportFailure('CANNED_BEFORE_SEND')
        self.sent.append(body);self.provider_logs.append({'wire_sha256':sha(body),'bytes':len(body)})
        if self.failure=='INTERRUPT':raise KeyboardInterrupt()
        if self.failure in ('AFTER_SEND','CANCEL'):raise TransportFailure('CANNED_TRANSPORT_STOP')
        if self.failure=='MISSING':return None
        return self.responses.pop(0) if self.responses else response_bytes()

def parse_response(raw):
    if type(raw) is not bytes or len(raw)>200000:raise BoundaryError('Missing/oversized provider response')
    try:
        def pairs(items):
            d={}
            for k,v in items:
                if k in d:raise BoundaryError('Duplicate response key')
                d[k]=v
            return d
        r=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(BoundaryError('Nonfinite receipt')))
    except (ValueError,UnicodeError):raise BoundaryError('Malformed provider response') from None
    if type(r) is not dict or set(r)!={'text','input_tokens','output_tokens','seconds','tool_calls'}:raise BoundaryError('Unexpected provider metadata/schema')
    if type(r['text']) is not str or r['tool_calls']!=[]:raise BoundaryError('Unexpected tool response or text')
    for k in ('input_tokens','output_tokens'):
        if r[k] is not None and (type(r[k]) is not int or r[k]<0):raise BoundaryError('Invalid token receipt')
    from cognitive_architecture_lab_v1.src.interfaces.contracts import finite
    if r['seconds'] is not None:finite(r['seconds'])
    return r

class Gateway:
    def __init__(self,compiler,ledger,transport):
        if type(compiler) is not Compiler or type(ledger) is not Ledger or type(transport) is not RecordingTransport:raise BoundaryError('Only reviewed offline components allowed; no provider object bypass')
        require_empty_defaults(transport.defaults)
        self.compiler,self.ledger,self.transport=compiler,ledger,transport
        self.guard=ledger.path.with_suffix('.boundary.lock');self.closed=ledger.path.with_suffix('.closed.json')
    def register(self,request):self.compiler.register(request);self.ledger.register(request)
    def _closed_runs(self):
        if not self.closed.exists():return {}
        r=json.loads(self.closed.read_text(encoding='utf-8'))
        if set(r)!={'closed','sha256'} or sha(canonical(r['closed']))!=r['sha256']:raise BoundaryError('Closure receipt corrupt')
        return r['closed']
    def _open(self,run_id):
        if run_id in self._closed_runs():raise GenerationClosed('Run permanently closed to generation')
    def reserve_request(self,spec,*,token_ceiling=100,seconds_ceiling=1,interrupt_after_reserve=False):
        with dispatch_lock(self.guard):
            state=self.ledger.state();intent=self.compiler.intent(spec,state);d=json.loads(intent);run_id=spec['run_id'];self._open(run_id)
            for a in state['attempts']:
                try:prior=json.loads(a['purpose'])
                except (ValueError,TypeError):raise BoundaryError('Unsealed legacy dispatch in boundary ledger') from None
                if a['run_id']==run_id and prior.get('call_id')==d['call_id']:raise DuplicateDispatch('Call already reserved; no automatic replay')
            reservation=self.ledger.reserve(run_id,intent,token_ceiling,seconds_ceiling)
            if interrupt_after_reserve:raise KeyboardInterrupt()
            return self.compiler.seal(spec,self.ledger.state(),reservation)
    def dispatch(self,sealed):
        with dispatch_lock(self.guard):
            if type(sealed) is not SealedModelRequest:raise BoundaryError('No dict, SDK object or raw-body bypass')
            self._open(sealed.run_id);state=self.ledger.state();body=self.compiler.validate(sealed,state)
            require_empty_defaults(self.transport.defaults);inspect_final_wire(body)
            i=sealed.physical_call_reservation
            try:raw=self.transport.exchange(body)
            except KeyboardInterrupt:
                self.ledger.finish(i,state='INTERRUPTED',error_code='INTERRUPTED');raise
            except Exception:
                # No exception string/details/provider metadata forwarded to logs or future prompts.
                self.ledger.finish(i,state='CANCELED' if self.transport.failure=='CANCEL' else 'FAILED',error_code='TRANSPORT_CANCELED' if self.transport.failure=='CANCEL' else 'TRANSPORT_ERROR');raise TransportFailure('TRANSPORT_ERROR_UNKNOWN_USAGE') from None
            try:r=parse_response(raw)
            except (ValueError,TypeError):
                # Raw bytes are retained HOST-ONLY for diagnosis, never admitted as generation context.
                text=raw.decode('utf-8',errors='replace') if isinstance(raw,bytes) else None
                self.ledger.finish(i,state='PROTOCOL_FAILURE',error_code='RESPONSE_REJECTED',response_text=text);raise BoundaryError('RESPONSE_REJECTED_UNKNOWN_USAGE') from None
            output_id='O_'+secrets.token_hex(12) # Opaque handle; never expose global accounting sequence
            record={'output_id':output_id,'call_id':sealed.call_id,'task_id':sealed.task_id,'wire_sha256':sha(body),'provenance_sha256':sha(sealed.provenance_bytes)}
            self.ledger.finish(i,state='SUCCEEDED',input_tokens=r['input_tokens'],output_tokens=r['output_tokens'],seconds=r['seconds'],response_text=r['text'],candidate=record)
            return {'output_id':output_id,'text':r['text'],'answer_sha256':sha(r['text'].encode('utf-8'))}
    def close_generation(self,run_id):
        with dispatch_lock(self.guard):
            self.compiler.run(run_id);closed=self._closed_runs()
            if run_id in closed:return closed[run_id]
            rows=[a for a in self.ledger.state()['attempts'] if a['run_id']==run_id]
            artifact={'schema_version':'closed-generation-v1','run_id':run_id,'task_id':self.compiler.run(run_id).task_id,'attempts_sha256':sha(canonical(rows)),
                      'outputs':[{'output_id':a['candidate']['output_id'],'text':a['response_text'],'answer_sha256':a['response_sha256']} for a in rows if a.get('candidate') and a['state']=='SUCCEEDED'],
                      'outstanding_or_unknown_cost':any(a['state']=='RESERVED' or a['total_tokens'] is None or a['seconds'] is None for a in rows)}
            closed[run_id]=artifact;envelope=canonical({'closed':closed,'sha256':sha(canonical(closed))});pending=self.closed.with_suffix('.pending')
            with pending.open('wb') as f:f.write(envelope);f.flush();os.fsync(f.fileno())
            os.replace(pending,self.closed);return artifact
