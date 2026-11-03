"""Additive stage admission; core reservation/dispatch/closure APIs stay inherited.
Internal alias OLLAMA_QWEN3_4B is a reviewed routing symbol, not a model substitution.
Final provider bytes are the existing concrete qwen3:4b mapping.
"""
import base64,hashlib,json,os,time
from pathlib import Path
from end_engine.models.base import ModelRequest
from end_engine.models.schema import validate
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest,canonical,digest
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from runtime_isolation_v1.src.sealed_requests.boundary import Compiler,exact,identifier,SPEC_KEYS,sha
from runtime_isolation_v1.src.trusted_transport.transport import Gateway
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError,require_empty_defaults
from native_model_integration_v1.src.provider_protocol.wire import SETTINGS,expected,validate_wire
from native_model_integration_v1.src.response_decoder.decode import decode
from ..prompts.registry import STAGES
from ..shared.observations import inspect,parse,ProtocolFault
from ..shared.evidence import gate_targets,supported_inventory,checked_plan
OUT=Path(__file__).resolve().parents[2]
LIMITS={'SPARSE_DELIBERATION':4,'DIRECTED_REPAIR':5,'BOUNDED_ALTERNATIVES':5}
ROLES={'INITIAL':[],'SPARSE_GATE':['INITIAL'],'SPARSE_REVISION':['INITIAL','SPARSE_GATE'],'REPAIR_INVENTORY':['INITIAL'],'REPAIR_PLAN':['INITIAL','REPAIR_INVENTORY'],'REPAIR_REVISION':['INITIAL','REPAIR_INVENTORY','REPAIR_PLAN'],'ALTERNATIVE_REQUIREMENTS':[],'ALTERNATIVE_CONSTRAINTS':[],'ALTERNATIVE_SELECTION':['INITIAL','ALTERNATIVE_REQUIREMENTS','ALTERNATIVE_CONSTRAINTS']}

def catalog():
    manifest=json.loads((OUT/'validation/APPROVED_PUBLIC_INPUTS.json').read_text(encoding='utf-8'))
    tasks={}
    for name,h in manifest.items():
        p=OUT/'public_inputs'/name;b=p.read_bytes()
        if sha(b)!=h:raise BoundaryError('Public snapshot drift')
        tasks[json.loads(b)['task_id']]=(b,h)
    return tasks

def control(stage,text):
    value=parse(text)
    try:validate(value,STAGES[stage]['schema'])
    except (ValueError,TypeError,KeyError):raise ProtocolFault('Control schema rejected') from None
    return value

class StageCompiler(Compiler):
    def __init__(self):
        super().__init__(catalog());self.bindings={}
        self.stages=json.loads(canonical(STAGES));expected_hashes=json.loads((OUT/'validation/PROMPT_HASHES.json').read_text(encoding='utf-8'))['stages']
        if {k:sha(canonical(v)) for k,v in self.stages.items()}!=expected_hashes:raise BoundaryError('Versioned stage registry drift')
    def register(self,r):
        if type(r) is not RunRequest or r.condition_id not in LIMITS:raise BoundaryError('Canonical architecture RunRequest required')
        identifier(r.run_id)
        if r.task_id not in self._tasks or json.dumps(r.public_task_payload,ensure_ascii=False)!=json.dumps(json.loads(self._tasks[r.task_id][0]),ensure_ascii=False):raise BoundaryError('Unapproved task bytes/order')
        if r.model_digest!='UNOBSERVED_NO_MODEL_QUERIED' or r.model_identity!=SETTINGS.model or r.generation_parameters!={'temperature':.7,'top_p':.8,'think':False} or r.context_window!=8192 or r.maximum_output_tokens!=4096 or r.seed_if_supported is not None:raise BoundaryError('Frozen provider/settings mismatch')
        identity=sha(canonical({'private':r.private_metadata(),'public_wire':r.wire()}))
        if r.run_id in self._runs and self._runs[r.run_id][1]!=identity:raise BoundaryError('Run resume identity drift')
        self._runs[r.run_id]=(r,identity)
    def _compile(self,spec,state):
        s=exact(spec,SPEC_KEYS)
        for k in ('run_id','call_id','task_id','purpose','instruction_id'):identifier(s[k])
        r=self.run(s['run_id']);stage=s['instruction_id']
        if stage not in self.stages or s['purpose']!=stage or s['task_id']!=r.task_id or s['observation_ids']!=[]:raise BoundaryError('Unknown/private stage or observation input')
        d=self.stages[stage];base=d.get('base_stage',stage)
        if d['condition'] not in ('*',r.condition_id):raise BoundaryError('Cross-condition stage')
        if type(s['prior_output_ids']) is not list or len(s['prior_output_ids'])!=d['refs'] or any(type(x) is not str for x in s['prior_output_ids']) or len(set(s['prior_output_ids']))!=len(s['prior_output_ids']):raise BoundaryError('Exact stage references required')
        own=[a for a in state['attempts'] if a['run_id']==r.run_id and a['state']!='RESERVED']
        history=[json.loads(a['purpose']).get('purpose') for a in own]
        if stage in history:raise BoundaryError('Stage already attempted; no extra deliberation')
        if stage!='INITIAL' and 'INITIAL' not in history:raise BoundaryError('No generated C0')
        if stage=='ALTERNATIVE_CONSTRAINTS' and 'ALTERNATIVE_REQUIREMENTS' not in history:raise BoundaryError('Alternative sequence not admitted')
        if 'base_stage' in d and any(str(x).endswith('_FORMAT_REPAIR') for x in history):raise BoundaryError('One total protocol repair per run')
        lookup={a['candidate']['output_id']:a for a in state['attempts'] if a.get('candidate')}
        refs=[]
        roles=ROLES[base]+([base] if 'base_stage' in d else [])
        for oid,role in zip(s['prior_output_ids'],roles):
            a=lookup.get(oid)
            if a is None or a['run_id']!=r.run_id or a['state']!='SUCCEEDED' or a['candidate']['task_id']!=r.task_id:raise BoundaryError('Foreign/private output handle')
            raw_stage=json.loads(a['purpose'])['purpose'];normalized=self.stages.get(raw_stage,{}).get('base_stage',raw_stage)
            if normalized!=role or sha(a['response_text'].encode('utf-8'))!=a['response_sha256']:raise BoundaryError('Wrong stage/changed output provenance')
            refs.append({'output_id':oid,'text':a['response_text'],'role':role})
        if sum(len(x['text'].encode()) for x in refs)>self.max_prior_bytes:raise BoundaryError('Prior context bound')
        public=self._tasks[r.task_id][2];ctx={};structured=d['schema'] is not None
        if base=='INITIAL':request=ModelRequest(stage,public,{},None)
        else:
            ctx={'task':public,'quoted_current_run_outputs':refs,'external_trusted_evidence':[]}
            report=inspect(r.public_task_payload,refs[0]['text']) if refs and base not in ('ALTERNATIVE_REQUIREMENTS','ALTERNATIVE_CONSTRAINTS') else None
            if report:ctx['public_local_observations']=report['observations']
            if base=='SPARSE_REVISION':
                targets=gate_targets(control('SPARSE_GATE',refs[1]['text']),report)
                if not targets:raise BoundaryError('No supported sparse revision target')
                ctx['validated_targets']=targets
            if base in ('REPAIR_PLAN','REPAIR_REVISION'):
                accepted,rejected=supported_inventory(control('REPAIR_INVENTORY',refs[1]['text']),report)
                if not accepted:raise BoundaryError('No supported repair inventory')
                ctx['supported_findings']=accepted
                if base=='REPAIR_REVISION':
                    actions=checked_plan(control('REPAIR_PLAN',refs[2]['text']),accepted)
                    if not actions:raise BoundaryError('Empty repair plan')
                    ctx['validated_plan']=actions
            if base=='ALTERNATIVE_SELECTION':ctx['candidate_observations']=[{'candidate_id':'C'+str(i),'observations':inspect(r.public_task_payload,x['text'])['observations']} for i,x in enumerate(refs[:3])]
            if 'base_stage' in d:
                try:control(base,refs[-1]['text'])
                except ProtocolFault:pass
                else:raise BoundaryError('Unnecessary format repair denied')
                ctx['failed_control_output']=refs[-1]['text']
            request=ModelRequest(stage,d['prompt'],ctx,d['schema'])
        from v0351_core_regression_pilot.bench.providers import render
        sequence=sum(a['run_id']==r.run_id for a in state['attempts'] if a['state']!='RESERVED')
        seed=int(hashlib.sha256(f'{SETTINGS.base_seed}:11:{sequence}'.encode()).hexdigest()[:8],16)
        rendered=render(request)
        wire={'wire_version':'tool-free-recording-json-v1','model':'OLLAMA_QWEN3_4B','parameters':{**r.generation_parameters,'seed':seed,'context_window':r.context_window,'maximum_output_tokens':r.maximum_output_tokens},'messages':[{'role':'user','content':rendered}],'tools':[],'tool_choice':'none','stream':False,'stateless':True}
        body=canonical(wire)
        if len(body)>self.max_wire_bytes:raise BoundaryError('Wire size bound')
        self.bindings[sha(body)]=(request,structured,seed)
        provenance=canonical({'run_id':r.run_id,'task_id':r.task_id,'stage':stage,'public_sha256':self._tasks[r.task_id][1],'prompt_sha256':sha(canonical(d)),'prior_output_ids':s['prior_output_ids'],'wire_sha256':sha(body),'trust':'REVIEWED_STAGE_PUBLIC_SOURCE_GRAPH'})
        return canonical(s),body,provenance

class StageTransport:
    def __init__(self,compiler,script,journal_dir,publication):
        from .script import Script
        if type(script) is not Script:raise BoundaryError('Only deterministic synthetic Script admitted')
        self.compiler=compiler;self.script=script;self.defaults={};self.failure=None;self.calls=[];self.journal_dir=Path(journal_dir);self.journal_dir.mkdir(parents=True,exist_ok=True);self.publication=publication;self.dispatch_context=None
    @staticmethod
    def append_journal(path,value,mode='a'):
        with path.open(mode,encoding='utf-8',newline='\n') as f:
            f.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def exchange(self,reference_bytes):
        require_empty_defaults(self.defaults)
        from runtime_isolation_v1.src.sealed_requests.boundary import inspect_final_wire
        ref=inspect_final_wire(reference_bytes)
        if sha(reference_bytes) not in self.compiler.bindings:raise BoundaryError('Unsealed adapter body')
        req,structured,seed=self.compiler.bindings[sha(reference_bytes)]
        from v0351_core_regression_pilot.bench.providers import render
        if ref['model']!='OLLAMA_QWEN3_4B' or ref['messages'][0]['content']!=render(req):raise BoundaryError('Reference/provider mapping drift')
        payload=expected(req,structured,seed);raw_body=validate_wire(payload,req,structured,seed)
        record={'stage':req.purpose,'method':'POST','path':'/api/generate','wire':raw_body.decode(),'wire_sha256':sha(raw_body),'response':None,'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL'};self.calls.append(record);start=time.perf_counter()
        from ..shared.journals import prepare,finish_entry
        context,journal,header=prepare(self,reference_bytes,req,structured,seed,raw_body,record)
        self.dispatch_context=None
        try:raw=self.script.reply(req.purpose)
        except BaseException as error:
            record['error_type']=type(error).__name__
            finish_entry(self,context,journal,header,'TRANSPORT_STOP',error_type=record['error_type'])
            if type(error).__name__=='Canceled':self.failure='CANCEL'
            raise
        record['response']=raw.decode('utf-8',errors='replace') if type(raw) is bytes else None
        finish_entry(self,context,journal,header,'RAW_RESPONSE_RECEIVED',response=record['response'],raw_response_base64=base64.b64encode(raw).decode() if type(raw) is bytes else None,raw_response_sha256=sha(raw) if type(raw) is bytes else None)
        r=decode(raw,SETTINGS.model)
        return canonical({'text':r['response'],'input_tokens':r.get('prompt_eval_count'),'output_tokens':r.get('eval_count'),'seconds':time.perf_counter()-start,'tool_calls':[]})

class ArchitectureGateway(Gateway):
    # Deliberately no overrides of reserve_request, dispatch, close_generation or locks.
    def __init__(self,compiler,ledger,transport):
        if type(compiler) is not StageCompiler or type(ledger) is not Ledger or type(transport) is not StageTransport:raise BoundaryError('Reviewed additive stage components required')
        require_empty_defaults(transport.defaults);self.compiler,self.ledger,self.transport=compiler,ledger,transport;self.guard=ledger.path.with_suffix('.boundary.lock');self.closed=ledger.path.with_suffix('.closed.json')
