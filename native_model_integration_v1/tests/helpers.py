import json,sys,tempfile
from pathlib import Path
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parent
sys.path[0:0]=[str(OUT),str(ROOT)]
from src.baseline_adapters.run import run_baseline
from src.provider_protocol.wire import SETTINGS,expected,validate_wire,body,sha
from src.provider_protocol.canned import completion,CannedScript
from src.response_decoder.decode import decode,ReceiptError
from src.native_end_bridge.bridge import NativeBridge,NativeGateway,RecordingTransport,verify_sources
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest,canonical
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
from end_engine.models import ModelRequest

def task(statement='Design a bounded memory architecture with failure recovery. No execution occurred.'):
    return {'task_id':'SYN-NATIVE' if statement.startswith('Design a bounded memory') else 'SYN-NO-PROGRESS','title':'Synthetic wiring only','task_statement':statement,'input':{'limit':'256 MiB'},'output_contract':{'format':'JSON'},'public_reference_ids':[]}
def temporary():
    p=OUT/'validation/scratch';p.mkdir(parents=True,exist_ok=True);assert p.resolve().is_relative_to(OUT.resolve());return tempfile.TemporaryDirectory(dir=p)
def environment(root,mode='progress',t=None,condition='FROZEN_CURRENT_END'):
    t=task() if t is None else t
    r=RunRequest(t['task_id'],t,SETTINGS.model,'UNOBSERVED',{'temperature':.7,'top_p':.8,'think':False},None,8192,4096,condition,36,400000,1800,'mock_unit')
    l=Ledger(Path(root)/'ledger.json');g=NativeGateway(r,l,RecordingTransport(CannedScript(mode)));return NativeBridge(g),g
