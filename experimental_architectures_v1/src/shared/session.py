"""Common contracts and durable execution, not a generic deliberation strategy."""
import json,os,time
from dataclasses import replace,asdict
from pathlib import Path
from cognitive_architecture_lab_v1.src.interfaces.contracts import Candidate,RunResult,RunRequest,canonical
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger,BudgetStop
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
from runtime_isolation_v1.src.trusted_transport.transport import TransportFailure
from ..adapters.gateway import StageCompiler,StageTransport,ArchitectureGateway,LIMITS,control,OUT
from ..prompts.registry import STAGES
from .observations import inspect,ProtocolFault
from native_model_integration_v1.src.provider_protocol.wire import sha
class UnknownCost(RuntimeError):pass
class Session:
    def __init__(self,request,script,directory,ledger=None):
        if type(request) is not RunRequest:raise BoundaryError('Existing RunRequest required')
        self.started=time.perf_counter();self.request=request;self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        if (self.directory/'RESULT.json').exists():raise FileExistsError('Completed run artifact immutable')
        limit=LIMITS[request.condition_id];self.effective=replace(request,attempt_budget=min(request.attempt_budget,limit))
        self.ledger=ledger if ledger is not None else Ledger(self.directory/'budget.json');compiler=StageCompiler();self.transport=StageTransport(compiler,script,self.directory/'wire');self.gateway=ArchitectureGateway(compiler,self.ledger,self.transport);self.gateway.register(self.effective)
        self.candidates=[];self.outputs={};self.events=[];self.errors=[];self.notes=[];self.checks={};self.final=None;self.repair_used=False
    def event(self,state,**data):self.events.append({'state':state,**data})
    def ensure_known(self):
        s=self.ledger.summary(self.request.run_id)
        if s['unknown_usage_attempts'] or s['outstanding_attempts'] or s['wall_time'] is None:raise UnknownCost('Unknown cost blocks continuation')
    def call(self,stage,refs=()):
        self.ensure_known();spec={'run_id':self.request.run_id,'call_id':'CALL_'+stage,'task_id':self.request.task_id,'purpose':stage,'instruction_id':stage,'prior_output_ids':[r['output_id'] for r in refs],'observation_ids':[]}
        self.event('STAGE_REQUESTED',stage=stage)
        sealed=self.gateway.reserve_request(spec,token_ceiling=16384,seconds_ceiling=900)
        self.event('ATTEMPT_RESERVED',stage=stage,attempt_id=sealed.physical_call_reservation)
        result=self.gateway.dispatch(sealed);result={**result,'stage':stage,'attempt_id':sealed.physical_call_reservation};self.outputs[stage]=result;self.event('RESPONSE_RECORDED',stage=stage,answer_sha256=result['answer_sha256']);return result
    def generate(self,stage,refs=(),parents=()):
        out=self.call(stage,refs);c=Candidate('C'+str(len(self.candidates)),out['text'],out['attempt_id'],tuple(parents),True);self.candidates.append(c);self.checks[c.candidate_id]=inspect(self.request.public_task_payload,c.answer)
        if self.final is None:self.final=c.candidate_id
        self.event('CANDIDATE_RECORDED',candidate_id=c.candidate_id,stage=stage,parents=list(parents));self.ensure_known();return c,out
    def assess(self,stage,refs):
        out=self.call(stage,refs);self.ensure_known()
        try:value=control(stage,out['text'])
        except ProtocolFault:
            if self.repair_used:raise
            self.repair_used=True;self.event('CONTROL_FORMAT_REPAIR',stage=stage)
            out=self.call(stage+'_FORMAT_REPAIR',tuple(refs)+(out,));self.ensure_known();value=control(stage,out['text'])
        return value,out
    def pick(self,candidate,reason):self.final=candidate.candidate_id;self.event('FINAL_SELECTED',candidate_id=self.final,reason=reason)
    def restore_without_dispatch(self):
        for path in sorted(self.transport.journal_dir.glob('*.jsonl')):
            lines=path.read_text(encoding='utf-8').splitlines();entries=[]
            for index,line in enumerate(lines):
                try:entries.append(json.loads(line))
                except json.JSONDecodeError:
                    if index!=len(lines)-1:raise BoundaryError('Corrupt interior journal record') from None
                    self.notes.append({'journal':path.name,'status':'TORN_FINAL_APPEND_NO_REPLAY'})
            if not entries or entries[0].get('state')!='RESERVED_WIRE_READY':
                self.notes.append({'journal':path.name,'status':'INCOMPLETE_WIRE_HEADER_NO_REPLAY'});continue
            record=dict(entries[0]['record']);record['recovered_without_dispatch']=True
            for entry in entries[1:]:
                if entry['state']=='RAW_RESPONSE_RECEIVED':record['response']=entry['response']
                elif entry['state']=='TRANSPORT_STOP':record['error_type']=entry['error_type']
            self.transport.calls.append(record)
        for a in self.ledger.state()['attempts']:
            if a['run_id']!=self.request.run_id or not a.get('candidate') or a['state']!='SUCCEEDED':continue
            stage=json.loads(a['purpose'])['purpose'];base=STAGES.get(stage,{}).get('base_stage',stage)
            if STAGES.get(base,{}).get('kind')!='candidate':continue
            parents=('C0',) if base in ('SPARSE_REVISION','REPAIR_REVISION') and self.candidates else ()
            c=Candidate('C'+str(len(self.candidates)),a['response_text'],a['attempt_id'],parents,True);self.candidates.append(c);self.checks[c.candidate_id]=inspect(self.request.public_task_payload,c.answer)
        self.final=self.candidates[0].candidate_id if self.candidates else None;self.event('RESTORED_NO_AUTOMATIC_REPLAY')
    def finish(self,termination):
        summary=self.ledger.summary(self.request.run_id);closed=self.gateway.close_generation(self.request.run_id);self.event('GENERATION_CLOSED',run_id=self.request.run_id);self.event('TERMINATED',termination_reason=termination,final_candidate=self.final,physical_attempts=summary['physical_attempts'])
        initial=self.candidates[0].candidate_id if self.candidates else None
        result=RunResult(self.request.run_id,self.request.condition_id,self.request.task_id,self.request.model_identity,
            {'adapter':'abc-stage-admission-v1','namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','provider':'ollama-generate-recording','model_digest':self.request.model_digest,'live_verified':False},initial,self.final,tuple(self.candidates),{c.candidate_id:list(c.parent_ids) for c in self.candidates},tuple(summary['attempts']),summary['physical_attempts'],summary['input_tokens'],summary['output_tokens'],summary['total_tokens'],summary['wall_time'],termination,
            {'internal_limit':LIMITS[self.request.condition_id],'effective_attempt_limit':self.effective.attempt_budget,'halted':summary['halted'],'known_token_subset':summary['known_token_subset']},
            {'outstanding_attempts':summary['outstanding_attempts'],'unknown_usage_attempts':summary['unknown_usage_attempts']},tuple(self.events)+({'uncertainty':self.notes,'public_checks':self.checks,'candidate_content_authority':'MODEL_GENERATED_UNVERIFIED_CONTENT'},),tuple(sorted({'PUBLIC_TASK:'+self.request.task_id+o['public_source'] for report in self.checks.values() for o in report['observations'] if o['status']!='UNKNOWN'})),tuple(self.errors)).validate()
        data={'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','request':asdict(self.request),'effective_ledger_request':asdict(self.effective),'result':result.data(),'C0':self.candidates[0].answer if self.candidates else None,'FINAL':next((c.answer for c in self.candidates if c.candidate_id==self.final),None),'events':self.events,'control_outputs':self.outputs,'checks':self.checks,'provider_records':self.transport.calls,'generation_closed':closed,'prompt_registry_root':json.loads((OUT/'validation/PROMPT_HASHES.json').read_text(encoding='utf-8'))['registry_root'],'scientific_scores':None}
        data['durable_journal_hashes']={p.relative_to(self.directory).as_posix():sha(p.read_bytes()) for p in sorted(self.transport.journal_dir.glob('*.jsonl'))}
        data['runner_elapsed_seconds']=time.perf_counter()-self.started;data['artifact_payload_sha256']=sha(canonical(data))
        pending=self.directory/'RESULT.pending'
        with pending.open('w',encoding='utf-8',newline='\n') as f:
            f.write(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
        os.replace(pending,self.directory/'RESULT.json');return data

def execute(request,script,directory,ledger=None):
    s=Session(request,script,directory,ledger)
    existing=[a for a in s.ledger.state()['attempts'] if a['run_id']==request.run_id]
    if existing:s.restore_without_dispatch();return s.finish('INTERRUPTED')
    try:
        if request.condition_id=='SPARSE_DELIBERATION':
            from ..architecture_a.sparse import run
        elif request.condition_id=='DIRECTED_REPAIR':
            from ..architecture_b.repair import run
        else:
            from ..architecture_c.alternatives import run
        termination=run(s)
    except BudgetStop as e:
        text=str(e);termination='TIME_EXHAUSTED' if 'TIME_EXHAUSTED' in text else 'BUDGET_EXHAUSTED' if 'BUDGET_EXHAUSTED' in text else 'EXTERNAL_BLOCKER';s.errors.append({'code':type(e).__name__,'detail':text})
    except UnknownCost:termination='EXTERNAL_BLOCKER';s.errors.append({'code':'UNKNOWN_CONSUMPTION'})
    except KeyboardInterrupt:termination='INTERRUPTED';s.errors.append({'code':'INTERRUPTED'})
    except ProtocolFault as e:termination='PROTOCOL_FAILURE';s.errors.append({'code':'CONTROL_PROTOCOL','detail':str(e)})
    except (TransportFailure,BoundaryError) as e:
        kind=s.transport.calls[-1].get('error_type') if s.transport.calls else None;termination='TIME_EXHAUSTED' if kind=='TimeoutError' else 'EXTERNAL_BLOCKER';s.errors.append({'code':type(e).__name__})
    return s.finish(termination)
