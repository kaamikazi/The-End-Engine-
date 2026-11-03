import hashlib,json,secrets,sys,tempfile
from pathlib import Path
LAB=Path(__file__).resolve().parents[1];ROOT=LAB.parent
sys.path.insert(0,str(ROOT))
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest,canonical,CONDITIONS
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger,BudgetStop
from src.sealed_requests.boundary import Compiler,sha
from src.trusted_transport.transport import Gateway,RecordingTransport,response_bytes
from src.capability_policy.policy import BoundaryError

def task(statement='Return the supplied public word as JSON.'):
    return {'task_id':'SYN-A','title':'Offline synthetic echo','task_statement':statement,'input':{'word':'blue'},'output_contract':{'word':'string'},'public_reference_ids':[]}
def public_bytes(t=None):return json.dumps(task() if t is None else t,ensure_ascii=False,allow_nan=False).encode('utf-8')
def request(run_id='run',condition='DIRECT',t=None,**kwargs):
    args=dict(task_id='SYN-A',public_task_payload=task() if t is None else t,model_identity='OFFLINE_DUMMY',model_digest='dummy-v1',generation_parameters={'temperature':.7,'top_p':.8,'think':False},seed_if_supported=11,context_window=8192,maximum_output_tokens=4096,condition_id=condition,attempt_budget=36,token_budget=30000,wall_time_budget=1800,run_id=run_id);args.update(kwargs);return RunRequest(**args)
def spec(call_id='c1',run_id='run',purpose='candidate',instruction_id='INITIAL',prior_output_ids=None,observation_ids=None,**extra):
    return dict(run_id=run_id,call_id=call_id,task_id='SYN-A',purpose=purpose,instruction_id=instruction_id,prior_output_ids=[] if prior_output_ids is None else prior_output_ids,observation_ids=[] if observation_ids is None else observation_ids,**extra)
def temporary():
    scratch=LAB/'validation/scratch';scratch.mkdir(parents=True,exist_ok=True);assert scratch.resolve().is_relative_to(LAB.resolve());return tempfile.TemporaryDirectory(dir=scratch)
class Env:
    def __init__(self,root,*,responses=(),failure=None,t=None,condition='DIRECT',run_id='run',ledger_options=None):
        self.root=Path(root);self.data=public_bytes(t);self.compiler=Compiler({'SYN-A':(self.data,sha(self.data))});self.ledger=Ledger(self.root/'ledger.json',**(ledger_options or {}));self.transport=RecordingTransport(responses,failure=failure);self.gateway=Gateway(self.compiler,self.ledger,self.transport);self.request=request(run_id,condition,t);self.gateway.register(self.request)
    def send(self,s=None):return self.gateway.dispatch(self.gateway.reserve_request(spec() if s is None else s))
    def restart(self):
        c=Compiler({'SYN-A':(self.data,sha(self.data))});g=Gateway(c,Ledger(self.ledger.path,**{'global_attempts':self.ledger.limits['attempts'],'global_tokens':self.ledger.limits['tokens'],'global_seconds':self.ledger.limits['seconds']}),RecordingTransport());g.register(self.request);return g
