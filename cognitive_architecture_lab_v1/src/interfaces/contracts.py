"""Public request/result contracts. No architecture algorithms or evaluator imports."""
from dataclasses import dataclass, asdict
import hashlib,json,math
CONDITIONS=('DIRECT','SELF_REFLECT','FROZEN_CURRENT_END','SPARSE_DELIBERATION','DIRECTED_REPAIR','BOUNDED_ALTERNATIVES')
ALIASES={'EVIDENCE_DIRECTED_REPAIR':'DIRECTED_REPAIR'}
TERMINATIONS=('COMPLETED','NO_ACTIONABLE_REVISION','NO_PROGRESS','BUDGET_EXHAUSTED','TIME_EXHAUSTED','INVALID_RESPONSE','EXTERNAL_BLOCKER','INTERRUPTED','PROTOCOL_FAILURE','UNRESOLVED')
PUBLIC_KEYS=('task_id','title','task_statement','input','output_contract','public_reference_ids')
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def finite(v,positive=False):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or (v<=0 if positive else v<0):raise ValueError('Expected finite nonnegative number')
    return v
def positive_int(v):
    if type(v) is not int or v<=0:raise ValueError('Expected positive integer')
    return v
def public_task(value):
    value=json.loads(json.dumps(value,ensure_ascii=False,allow_nan=False)) # detached strict copy, preserves approved display order
    if not isinstance(value,dict) or set(value)!=set(PUBLIC_KEYS):raise ValueError('Public task allowlist mismatch')
    for key in ('task_id','title','task_statement'):
        if not isinstance(value[key],str) or not value[key]:raise ValueError('Missing public task text')
    if not isinstance(value['input'],dict) or not isinstance(value['output_contract'],dict):raise ValueError('Task data/schema must be objects')
    if not isinstance(value['public_reference_ids'],list) or not all(isinstance(x,str) for x in value['public_reference_ids']):raise ValueError('Invalid public references')
    return value
@dataclass(frozen=True)
class RunRequest:
    task_id:str
    public_task_payload:dict
    model_identity:str
    model_digest:str
    generation_parameters:dict
    seed_if_supported:int|None
    context_window:int
    maximum_output_tokens:int
    condition_id:str
    attempt_budget:int
    token_budget:int
    wall_time_budget:float
    run_id:str
    def __post_init__(self):
        t=public_task(self.public_task_payload)
        if t['task_id']!=self.task_id:raise ValueError('Task identity mismatch')
        object.__setattr__(self,'public_task_payload',t)
        if self.condition_id not in CONDITIONS:raise ValueError('Use frozen condition ID; resolve documented alias explicitly')
        if not all(isinstance(x,str) and x for x in (self.run_id,self.model_identity,self.model_digest)):raise ValueError('Missing identity')
        for v in (self.context_window,self.maximum_output_tokens,self.attempt_budget,self.token_budget):positive_int(v)
        if self.maximum_output_tokens>self.context_window:raise ValueError('Output cap exceeds context')
        if self.attempt_budget>36 or self.wall_time_budget>1800:raise ValueError('Frozen per-run ceiling exceeded')
        finite(self.wall_time_budget,True)
        if self.seed_if_supported is not None and type(self.seed_if_supported) is not int:raise ValueError('Invalid seed')
        p=json.loads(canonical(self.generation_parameters))
        if set(p)!={'temperature','top_p','think'}:raise ValueError('Unapproved generation parameter')
        finite(p['temperature']);finite(p['top_p'])
        if not 0<p['top_p']<=1 or type(p['think']) is not bool:raise ValueError('Invalid generation parameters')
        object.__setattr__(self,'generation_parameters',p)
        object.__setattr__(self,'_public_serialized',json.dumps(t,ensure_ascii=False,allow_nan=False))
        object.__setattr__(self,'_settings_digest',digest(p))
    def wire(self):
        from ..public_runner.render import render_public_prompt
        if json.dumps(self.public_task_payload,ensure_ascii=False,allow_nan=False)!=self._public_serialized or digest(self.generation_parameters)!=self._settings_digest:raise ValueError('Request mutated after binding')
        # No run, condition, scores, prior chat, provider credentials or tools in initial request.
        return {'schema_version':'public-model-request-v1','task':public_task(self.public_task_payload),'prompt':render_public_prompt(self.public_task_payload),
                'model':{'identity':self.model_identity,'digest':self.model_digest},
                'settings':{**self.generation_parameters,'seed':self.seed_if_supported,'context_window':self.context_window,'maximum_output_tokens':self.maximum_output_tokens},
                'limits':{'physical_attempts':self.attempt_budget,'tokens':self.token_budget,'wall_time_seconds':self.wall_time_budget},
                'tools':[],'history':[]}
    def wire_bytes(self):return canonical(self.wire())
    def private_metadata(self):return {'run_id':self.run_id,'condition_id':self.condition_id,'task_id':self.task_id,'request_sha256':hashlib.sha256(self.wire_bytes()).hexdigest()}
@dataclass(frozen=True)
class Candidate:
    candidate_id:str
    answer:str
    attempt_id:int
    parent_ids:tuple[str,...]=()
    complete:bool=True
    def __post_init__(self):
        if not self.candidate_id or not isinstance(self.answer,str) or type(self.attempt_id) is not int or self.attempt_id<1 or type(self.complete) is not bool:raise ValueError('Invalid candidate')
    def data(self):return {**asdict(self),'answer_sha256':hashlib.sha256(self.answer.encode('utf-8')).hexdigest()}
@dataclass(frozen=True)
class RunResult:
    run_id:str
    condition_id:str
    task_id:str
    model_identity:str
    runtime_identity:dict
    initial_candidate:str|None
    final_candidate:str|None
    all_generated_candidates:tuple[Candidate,...]
    candidate_lineage:dict
    model_invocations:tuple[dict,...]
    physical_attempts:int
    input_tokens:int|None
    output_tokens:int|None
    total_tokens:int|None
    wall_time:float|None
    termination_reason:str
    budget_exhaustion:dict
    interruption_state:dict
    provenance_records:tuple[dict,...]
    public_evidence_used:tuple[str,...]
    diagnostic_errors:tuple[dict,...]
    def validate(self):
        if self.condition_id not in CONDITIONS or self.termination_reason not in TERMINATIONS:raise ValueError('Invalid run category')
        if not self.run_id or not self.task_id or not self.model_identity or not self.runtime_identity:raise ValueError('Missing result identity')
        candidates=self.all_generated_candidates;seen=set()
        for c in candidates:
            if c.candidate_id=='TASK_INPUT' or c.candidate_id in seen or any(p not in seen for p in c.parent_ids):raise ValueError('Invalid generated lineage')
            if c.attempt_id not in {a.get('attempt_id') for a in self.model_invocations}:raise ValueError('Candidate lacks physical attempt')
            seen.add(c.candidate_id)
        if self.initial_candidate!=(candidates[0].candidate_id if candidates else None):raise ValueError('C0 must be first actual generated candidate')
        if self.final_candidate is not None and self.final_candidate not in seen:raise ValueError('Final must reference recorded output')
        expected={c.candidate_id:list(c.parent_ids) for c in candidates}
        if self.candidate_lineage!=expected:raise ValueError('Lineage mismatch')
        if type(self.physical_attempts) is not int or self.physical_attempts<0 or len(self.model_invocations)!=self.physical_attempts:raise ValueError('Every attempt must be present')
        ids=[a.get('attempt_id') for a in self.model_invocations]
        if ids!=sorted(set(ids)) or any(a.get('run_id')!=self.run_id for a in self.model_invocations):raise ValueError('Invocation binding mismatch')
        for x in (self.input_tokens,self.output_tokens,self.total_tokens):
            if x is not None and (type(x) is not int or x<0):raise ValueError('Invalid token count')
        if self.total_tokens is not None and (self.input_tokens is None or self.output_tokens is None or self.total_tokens!=self.input_tokens+self.output_tokens):raise ValueError('Inconsistent usage')
        if self.wall_time is not None:finite(self.wall_time)
        canonical(asdict(self));return self
    def data(self):
        self.validate();d=asdict(self);d['all_generated_candidates']=[c.data() for c in self.all_generated_candidates];return d
