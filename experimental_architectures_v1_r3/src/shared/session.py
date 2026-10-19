"""Versioned F01/F02/F04 session boundary; A/B/C algorithms remain unchanged."""
import json,math,time
from dataclasses import replace,asdict
from pathlib import Path
from cognitive_architecture_lab_v1.src.interfaces.contracts import Candidate,RunResult,RunRequest,canonical
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger,BudgetStop
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
from runtime_isolation_v1.src.trusted_transport.transport import TransportFailure
from ..adapters.gateway import StageCompiler,StageTransport,ArchitectureGateway,LIMITS,control,OUT
from ..prompts.registry import STAGES
from .observations import inspect,ProtocolFault
from .strict_json import NumericFault,sha
from .publication import Publication,ArtifactIntegrity,PublicationFailure,durable
from .journals import verify_journals
from .provenance import record_settlement, record_reservation, require_recoverable, require_dispatchable, publish_verified
class UnknownCost(RuntimeError):pass
class Session:
    def __init__(self,request,script,directory,ledger=None):
        if type(request) is not RunRequest:raise BoundaryError('Existing RunRequest required')
        self.started=time.perf_counter();self.request=request;self.directory=Path(directory).resolve();self.directory.mkdir(parents=True,exist_ok=True)
        self.effective=replace(request,attempt_budget=min(request.attempt_budget,LIMITS[request.condition_id]))
        path=ledger.path if ledger is not None else self.directory/'budget.json'
        if (self.directory/'publication/IDENTITY.json').exists() and not path.exists():
            durable(self.directory/'MISSING_LEDGER_FAILURE.json',{'code':'EXISTING_RUN_LEDGER_MISSING','no_budget_reset':True});raise ArtifactIntegrity('EXISTING_RUN_LEDGER_MISSING')
        self.ledger=ledger if ledger is not None else Ledger(path);self.store=Publication(self.directory,request,self.effective,self.ledger)
        # An erased/foreign-relabelled ledger row is still an existing run when
        # independent attempt evidence remains. Reject before any new reservation.
        require_recoverable(verify_journals(self.store),self.store)
        compiler=StageCompiler();self.transport=StageTransport(compiler,script,self.directory/'wire',self.store);self.gateway=ArchitectureGateway(compiler,self.ledger,self.transport);self.gateway.register(self.effective)
        self.candidates=[];self.outputs={};self.events=[];self.errors=[];self.notes=[];self.checks={};self.final=None;self.repair_used=False
        with self.store.lock():
            if self.store.final.exists():self.store.verify_completed();raise FileExistsError('Verified completed run; no new session admitted')
    def event(self,state,**data):self.events.append({'state':state,**data})
    def detach(self):
        """Explicit abandonment: release ownership without replay or a fresh budget."""
        self.store.detach()
    def ensure_known(self):
        s=self.ledger.summary(self.request.run_id)
        if s['unknown_usage_attempts'] or s['outstanding_attempts'] or s['wall_time'] is None:raise UnknownCost('Unknown cost blocks continuation')
    def call(self,stage,refs=()):
        with self.store.lock():
            self.store.before_dispatch();self.ensure_known();require_dispatchable(self.store);spec={'run_id':self.request.run_id,'call_id':'CALL_'+stage,'task_id':self.request.task_id,'purpose':stage,'instruction_id':stage,'prior_output_ids':[r['output_id'] for r in refs],'observation_ids':[]}
            self.event('STAGE_REQUESTED',stage=stage)
            sealed=self.gateway.reserve_request(spec,token_ceiling=16384,seconds_ceiling=900)
            record_reservation(self.store,sealed)
            self.transport.dispatch_context=sealed;self.event('ATTEMPT_RESERVED',stage=stage,attempt_id=sealed.physical_call_reservation)
            try:result=self.gateway.dispatch(sealed)
            finally:record_settlement(self.store,sealed.physical_call_reservation)
            result={**result,'stage':stage,'attempt_id':sealed.physical_call_reservation};self.outputs[stage]=result;self.event('RESPONSE_RECORDED',stage=stage,answer_sha256=result['answer_sha256']);return result
    def generate(self,stage,refs=(),parents=()):
        out=self.call(stage,refs);c=Candidate('C'+str(len(self.candidates)),out['text'],out['attempt_id'],tuple(parents),True);self.candidates.append(c)
        try:self.checks[c.candidate_id]=inspect(self.request.public_task_payload,c.answer)
        except NumericFault:
            self.event('NUMERIC_RESPONSE_REJECTED',candidate_id=c.candidate_id);self.notes.append('Raw numeric-invalid output retained; not eligible for final selection');raise
        if self.final is None:self.final=c.candidate_id
        self.event('CANDIDATE_RECORDED',candidate_id=c.candidate_id,stage=stage,parents=list(parents));self.ensure_known();return c,out
    def assess(self,stage,refs):
        out=self.call(stage,refs);self.ensure_known()
        try:value=control(stage,out['text'])
        except NumericFault:raise
        except ProtocolFault:
            if self.repair_used:raise
            self.repair_used=True;self.event('CONTROL_FORMAT_REPAIR',stage=stage)
            out=self.call(stage+'_FORMAT_REPAIR',tuple(refs)+(out,));self.ensure_known();value=control(stage,out['text'])
        return value,out
    def pick(self,candidate,reason):self.final=candidate.candidate_id;self.event('FINAL_SELECTED',candidate_id=self.final,reason=reason)
    def restore_without_dispatch(self):
        with self.store.lock():
            if self.store.final.exists():self.store.verify_completed();return
            self.store.claim();report=verify_journals(self.store);require_recoverable(report,self.store);self.transport.calls=report['verified_provider_records']
            if report['overall']!='VERIFIED':self.notes.extend('JOURNAL_'+r['status']+':'+r['code'] for r in report['attempts'] if r['status']!='VERIFIED')
            for a in self.ledger.state()['attempts']:
                if a['run_id']!=self.request.run_id or not a.get('candidate') or a['state']!='SUCCEEDED':continue
                stage=json.loads(a['purpose'])['purpose'];base=STAGES.get(stage,{}).get('base_stage',stage)
                if STAGES.get(base,{}).get('kind')!='candidate':continue
                parents=('C0',) if base in ('SPARSE_REVISION','REPAIR_REVISION') and self.candidates else ()
                c=Candidate('C'+str(len(self.candidates)),a['response_text'],a['attempt_id'],parents,True);self.candidates.append(c)
                try:self.checks[c.candidate_id]=inspect(self.request.public_task_payload,c.answer)
                except NumericFault:self.notes.append('Numeric-invalid ledger candidate retained as raw evidence only');continue
                if self.final is None:self.final=c.candidate_id
            self.event('RESTORED_NO_AUTOMATIC_REPLAY',journal_status=report['overall'])
    def _build(self,termination,report):
        summary=self.ledger.summary(self.request.run_id);closed=self.gateway.close_generation(self.request.run_id);self.event('GENERATION_CLOSED',run_id=self.request.run_id);self.event('TERMINATED',termination_reason=termination,final_candidate=self.final,physical_attempts=summary['physical_attempts'])
        initial=self.candidates[0].candidate_id if self.candidates else None
        result=RunResult(self.request.run_id,self.request.condition_id,self.request.task_id,self.request.model_identity,
            {'adapter':'abc-stage-admission-r2-1.0.1','namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','provider':'ollama-generate-recording','model_digest':self.request.model_digest,'live_verified':False},initial,self.final,tuple(self.candidates),{c.candidate_id:list(c.parent_ids) for c in self.candidates},tuple(summary['attempts']),summary['physical_attempts'],summary['input_tokens'],summary['output_tokens'],summary['total_tokens'],summary['wall_time'],termination,
            {'internal_limit':LIMITS[self.request.condition_id],'effective_attempt_limit':self.effective.attempt_budget,'halted':summary['halted'],'known_token_subset':summary['known_token_subset']},
            {'outstanding_attempts':summary['outstanding_attempts'],'unknown_usage_attempts':summary['unknown_usage_attempts']},tuple(self.events)+({'uncertainty':self.notes,'public_checks':self.checks,'candidate_content_authority':'MODEL_GENERATED_UNVERIFIED_CONTENT'},),tuple(sorted({'PUBLIC_TASK:'+self.request.task_id+o['public_source'] for report in self.checks.values() for o in report['observations'] if o['status']!='UNKNOWN'})),tuple(self.errors)).validate()
        data={'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','request':asdict(self.request),'effective_ledger_request':asdict(self.effective),'result':result.data(),'C0':self.candidates[0].answer if self.candidates else None,'FINAL':next((c.answer for c in self.candidates if c.candidate_id==self.final),None),'events':self.events,'control_outputs':self.outputs,'checks':self.checks,'provider_records':self.transport.calls,'generation_closed':closed,'prompt_registry_root':json.loads((OUT/'validation/PROMPT_HASHES.json').read_text(encoding='utf-8'))['registry_root'],'scientific_scores':None}
        data['journal_integrity']=report;data['durable_journal_hashes']=report['trusted_hashes']
        elapsed=time.perf_counter()-self.started;data['runner_elapsed_seconds']=elapsed if math.isfinite(elapsed) and elapsed>=0 else None
        return data
    def finish(self,termination):
        try:
            with self.store.lock():
                if self.store.final.exists():
                    result=self.store.verify_completed();code='IDEMPOTENT_FINALIZATION' if result['result']['termination_reason']==termination else 'CONFLICTING_FINALIZATION_RECORDED'
                    self.store.event(code,requested_termination=termination,existing_termination=result['result']['termination_reason'],caller_candidate_count=len(self.candidates));return result
                self.store.claim();report=verify_journals(self.store)
                require_recoverable(report,self.store)
                if report['overall']=='BLOCKED':
                    termination='EXTERNAL_BLOCKER';self.errors.append({'code':'JOURNAL_INTEGRITY_BLOCKER','diagnostics':report['attempts']});self.notes.append('UNTRUSTED_JOURNAL_EVIDENCE_NOT_CERTIFIED')
                elif report['overall']=='INTERRUPTED':
                    termination='INTERRUPTED';self.notes.append('TRUNCATED_OR_UNKNOWN_JOURNAL_NO_REPLAY')
                try:data=self._build(termination,report);return publish_verified(self.store,data)
                except ArtifactIntegrity:raise
                except (ValueError,TypeError,OverflowError) as error:
                    self.store.event('TERMINAL_SERIALIZATION_REJECTED',exception_type=type(error).__name__)
                    prior_errors=[]
                    for diagnostic in self.errors:
                        try:canonical(diagnostic);prior_errors.append(diagnostic)
                        except (ValueError,TypeError):pass
                    self.events=[{'state':'TERMINAL_SERIALIZATION_REJECTED','replaced_local_fields':['events','notes','checks','control_outputs']}];self.notes=['Unsafe local structured metadata excluded; raw ledger/journal evidence retained'];self.checks={};self.outputs={};self.errors=prior_errors+[{'code':'TERMINAL_SERIALIZATION_REJECTED','exception_type':type(error).__name__}]
                    data=self._build('PROTOCOL_FAILURE',report)
                    try:return publish_verified(self.store,data)
                    except ArtifactIntegrity:raise
                    except (ValueError,TypeError,OverflowError) as final_error:
                        self.store.event('TERMINAL_WRITE_FAILED',exception_type=type(final_error).__name__);raise PublicationFailure('NO_TERMINAL_SUCCESS_CLAIMED') from final_error
        except BaseException as error:
            try:self.store.event('FINALIZATION_FAILED',exception_type=type(error).__name__)
            except OSError:pass
            raise
        finally:self.store.release()

def execute(request,script,directory,ledger=None):
    # Translate only a recognized F02 hold at the orchestration boundary.
    # Programming errors and F01/other integrity exceptions still propagate.
    from .provenance import RecoveryIntegrityHold
    from .recovery_blocked import blocked_recovery
    try:return _execute(request,script,directory,ledger)
    except RecoveryIntegrityHold as error:return blocked_recovery(error)


def _execute(request,script,directory,ledger=None):
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
    except NumericFault as e:termination='INVALID_RESPONSE';s.errors.append({'code':'NUMERIC_RESPONSE_REJECTED','detail':str(e)})
    except ProtocolFault as e:termination='PROTOCOL_FAILURE';s.errors.append({'code':'CONTROL_PROTOCOL','detail':str(e)})
    except (TransportFailure,BoundaryError) as e:
        kind=s.transport.calls[-1].get('error_type') if s.transport.calls else None;termination='TIME_EXHAUSTED' if kind=='TimeoutError' else 'EXTERNAL_BLOCKER';s.errors.append({'code':type(e).__name__})
    return s.finish(termination)
