"""Injected provider bridge. Engine and historical Ollama implementation are unchanged.
This additive consumer reuses SealedModelRequest and Ledger, not the old closed
OFFLINE_DUMMY Compiler/Gateway (which cannot encode native Engine context).
"""
import contextlib,hashlib,hmac,inspect,json,secrets,time
from dataclasses import asdict
from pathlib import Path
from end_engine.models.base import ModelRequest
from end_engine.core.state import to_data
from v0351_core_regression_pilot.bench.providers import OllamaModel,CallLog,ProviderError
from runtime_isolation_v1.src.sealed_requests.boundary import SealedModelRequest
from runtime_isolation_v1.src.trusted_transport.transport import Gateway,dispatch_lock
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest,canonical
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger,BudgetStop
from end_engine.models.budget import RunBudgetExceeded
from ..provider_protocol.wire import SETTINGS,expected,validate_wire,sha,ADAPTER_VERSION
from ..response_decoder.decode import decode
ROOT=Path(__file__).resolve().parents[3]
PURPOSES={'initial_candidate','revision','critique','revision_plan','verification','branch_generation','branch_evaluation','synthesis','judgment','adversarial_judgment','adversarial_tests','comparison','direct_answer','self_reflect_initial','self_reflect_critique','self_reflect_revision'}
FORBIDDEN_CONTEXT={'evaluator','fixture_answer','external_scores','reviewer_feedback','conversation_id','thread_id','api_key','tools','attachments','private_evaluation'}

def verify_sources():
    manifest=json.loads((ROOT/'native_model_integration_v1/validation/TRUSTED_SOURCE_HASHES.json').read_text(encoding='utf-8'))
    if any(sha((ROOT/p).read_bytes())!=h for p,h in manifest.items()):raise BoundaryError('Trusted Engine/provider source drift')
    return manifest

def approved_prompt(task):
    from cognitive_architecture_lab_v1.src.public_runner.render import render_public_prompt
    manifest=json.loads((ROOT/'native_model_integration_v1/validation/APPROVED_PUBLIC_INPUTS.json').read_text(encoding='utf-8'))
    name=task['task_id']+'.json'
    if name not in manifest:raise BoundaryError('Task not approved')
    path=ROOT/'native_model_integration_v1/public_inputs'/name
    if sha(path.read_bytes())!=manifest[name] or json.dumps(task,ensure_ascii=False)!=json.dumps(json.loads(path.read_text(encoding='utf-8')),ensure_ascii=False):raise BoundaryError('Approved public bytes/order mismatch')
    return render_public_prompt(task)

def origin():
    # Diagnostics + pinned trusted-origin admission; not an OS stack security claim.
    for f in inspect.stack():
        p=Path(f.filename).resolve()
        if p.is_relative_to(ROOT/'end_engine') and p.relative_to(ROOT/'end_engine').as_posix() not in ('models/base.py','models/recording.py','quality/providers.py'):
            return {'path':p.relative_to(ROOT).as_posix(),'function':f.function,'line':f.lineno}
        if p==ROOT/'v0351_core_regression_pilot/bench/conditions.py' and f.function in ('run_direct','run_self_reflect'):
            return {'path':p.relative_to(ROOT).as_posix(),'function':f.function,'line':f.lineno}
    raise BoundaryError('Request did not originate in admitted unchanged Engine/baseline source')

class NativeCompiler:
    def __init__(self,run_request):
        self.request=run_request;self.key=secrets.token_bytes(32);self.prompt=approved_prompt(run_request.public_task_payload);self.identity=sha(run_request.wire_bytes())
    def run(self,runid):
        if runid!=self.request.run_id:raise BoundaryError('Foreign run')
        if sha(self.request.wire_bytes())!=self.identity:raise BoundaryError('Common request changed')
        return self.request
    def seal(self,request,structured,seed,reservation,wire,source):
        generic=json.dumps(to_data(request),ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8');spec=canonical({'run_id':self.request.run_id,'task_id':self.request.task_id,'purpose':request.purpose,'structured':structured,'seed':seed,'wire_sha256':sha(wire)})
        provenance=canonical({'source':source,'native_model_request_sha256':sha(generic),'wire_sha256':sha(wire),'adapter':ADAPTER_VERSION,'execution':'MOCK_WIRING_ONLY'})
        signature=hmac.digest(self.key,canonical(reservation)+spec+generic+provenance,'sha256')
        return SealedModelRequest(self.request.run_id,'P'+str(reservation),self.request.task_id,request.purpose,reservation,spec,generic,provenance,signature)
    def validate(self,sealed,state,wire):
        if type(sealed) is not SealedModelRequest or sealed.run_id!=self.request.run_id or sealed.task_id!=self.request.task_id:raise BoundaryError('Sealed request required')
        signature=hmac.digest(self.key,canonical(sealed.physical_call_reservation)+sealed.spec_bytes+sealed.payload_bytes+sealed.provenance_bytes,'sha256')
        if not hmac.compare_digest(sealed.signature,signature):raise BoundaryError('Seal mismatch')
        s=json.loads(sealed.spec_bytes);request=ModelRequest(**json.loads(sealed.payload_bytes));validate_wire(json.loads(wire),request,s['structured'],s['seed'])
        if sha(wire)!=s['wire_sha256']:raise BoundaryError('Provider wire changed')
        row=state['attempts'][sealed.physical_call_reservation-1]
        if row['state']!='RESERVED' or row['run_id']!=sealed.run_id or row['purpose']!=sealed.spec_bytes.decode('utf-8'):raise BoundaryError('Stale/foreign physical reservation')
        return request

class RecordingTransport:
    def __init__(self,script):self.script=script;self.calls=[];self.defaults={}
    def exchange(self,wire,request,structured):
        if self.defaults:raise BoundaryError('Inherited provider defaults forbidden')
        if type(wire) is not bytes:raise BoundaryError('Raw provider bytes required')
        record={'method':'POST','path':'/api/generate','headers':{'Content-Type':'application/json'},'wire':wire.decode('utf-8'),'wire_sha256':sha(wire),'purpose':request.purpose,'structured':structured,'response':None,'namespace':'MOCK_WIRING_ONLY'};self.calls.append(record)
        raw=self.script.reply(request,structured,len(self.calls));record['response']=raw.decode('utf-8',errors='replace') if isinstance(raw,bytes) else None;return raw

class NativeGateway(Gateway):
    def __init__(self,run_request,ledger,transport):
        if type(run_request) is not RunRequest or type(ledger) is not Ledger or type(transport) is not RecordingTransport:raise BoundaryError('Reviewed native components required')
        if run_request.model_identity!=SETTINGS.model or run_request.generation_parameters!={'temperature':SETTINGS.temperature,'top_p':SETTINGS.top_p,'think':SETTINGS.think} or run_request.context_window!=SETTINGS.num_ctx or run_request.maximum_output_tokens!=SETTINGS.num_predict:raise BoundaryError('Common settings/provider configuration mismatch')
        self.compiler=NativeCompiler(run_request);self.ledger=ledger;self.transport=transport;self.guard=ledger.path.with_suffix('.boundary.lock');self.closed=ledger.path.with_suffix('.closed.json');ledger.register(run_request);self.seals=[];self.last_budget_stop=None
    def attempt(self,request,structured,seed,payload,source):
        if source!=origin():raise BoundaryError('Native source admission mismatch')
        if self.transport.defaults:raise BoundaryError('Inherited tools/defaults forbidden')
        if type(request) is not ModelRequest or request.purpose not in PURPOSES or FORBIDDEN_CONTEXT&set(request.context):raise BoundaryError('Unapproved ModelRequest')
        self.compiler.run(self.compiler.request.run_id)
        if request.context.get('task')!=self.compiler.prompt and self.compiler.prompt not in request.prompt:raise BoundaryError('Request not bound to approved task')
        wire=validate_wire(payload,request,structured,seed);runid=self.compiler.request.run_id
        with dispatch_lock(self.guard):
            self._open(runid)
            spec=canonical({'run_id':runid,'task_id':self.compiler.request.task_id,'purpose':request.purpose,'structured':structured,'seed':seed,'wire_sha256':sha(wire)})
            # Real conservative tokenizer/time reservations require later backend validation.
            try:i=self.ledger.reserve(runid,spec.decode(),16384,900)
            except BudgetStop as e:
                self.last_budget_stop=str(e);raise
            sealed=self.compiler.seal(request,structured,seed,i,wire,source);self.compiler.validate(sealed,self.ledger.state(),wire);self.last_sealed=sealed;self.seals.append({'reservation':i,'wire_sha256':sha(wire),'request_sha256':sha(sealed.payload_bytes),'provenance':json.loads(sealed.provenance_bytes),'purpose':request.purpose,'structured':structured,'protocol_repair':bool(request.context.get('protocol_repair') or 'Repair the previous structured output' in request.prompt)})
            start=time.perf_counter();raw=None
            try:
                raw=self.transport.exchange(wire,request,structured);r=decode(raw,SETTINGS.model)
            except BaseException as error:
                elapsed=time.perf_counter()-start;state='INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'FAILED'
                self.ledger.finish(i,state=state,seconds=elapsed,error_code='RECEIPT_OR_TRANSPORT_FAILURE',response_text=raw.decode('utf-8',errors='replace') if isinstance(raw,bytes) else None)
                if isinstance(error,KeyboardInterrupt):raise
                raise ProviderError('transport_or_receipt_failure','Raw evidence kept host-only; usage unknown') from None
            record={'output_id':'O_'+secrets.token_hex(12),'task_id':self.compiler.request.task_id,'wire_sha256':sha(wire),'raw_provider_response':raw.decode('utf-8'),'server_durations_ns':{k:v for k,v in r.items() if k.endswith('_duration')}}
            self.ledger.finish(i,state='SUCCEEDED',input_tokens=r.get('prompt_eval_count'),output_tokens=r.get('eval_count'),seconds=time.perf_counter()-start,response_text=r['response'],candidate=record)
            return r

class NativeBridge(OllamaModel):
    def __init__(self,gateway):
        verify_sources();self.gateway=gateway;self.active=None;self.authorized=False
        super().__init__(SETTINGS,{'digest':None,'server_version':None},CallLog(),trial_seed=11,transport=self._sealed_transport)
    def _http(self,payload):raise BoundaryError('Real HTTP transport unavailable in this offline integration')
    def metadata(self):
        return {'provider':'ollama-generate-offline-recording','model':SETTINGS.model,'digest':None,'server_version':None,'settings':asdict(SETTINGS),'adapter_version':ADAPTER_VERSION,'data_origin':'MOCK_WIRING_ONLY','live_verified':False}
    @contextlib.contextmanager
    def run_scope(self):
        if self.authorized:raise BoundaryError('Nested/shared run scope')
        verify_sources();self.authorized=True
        try:yield
        finally:self.authorized=False
    def _call(self,request,*,structured):
        if not self.authorized:raise BoundaryError('No approved baseline run scope')
        if self.transport!=self._sealed_transport:raise BoundaryError('Transport bypass refused')
        if self.settings!=SETTINGS:raise BoundaryError('Frozen model/settings drift')
        source=origin();previous=self.active;self.active=(request,structured,source)
        try:return super()._call(request,structured=structured) # exact historical retry/parse/schema semantics
        except ProviderError:
            if self.gateway.last_budget_stop and ('BUDGET_EXHAUSTED' in self.gateway.last_budget_stop or 'TIME_EXHAUSTED' in self.gateway.last_budget_stop):raise RunBudgetExceeded(self.gateway.last_budget_stop) from None
            raise
        finally:self.active=previous
    def _sealed_transport(self,payload):
        if not self.authorized or self.active is None:raise BoundaryError('No active native request')
        request,structured,source=self.active
        return self.gateway.attempt(request,structured,self._seed(),payload,source)
