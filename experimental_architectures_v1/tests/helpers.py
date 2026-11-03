import json,sys,tempfile,unittest
from pathlib import Path
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parent;sys.path[0:0]=[str(OUT),str(ROOT)]
from src.shared.session import execute,Session
from src.adapters.script import Script,complete,gate,finding,plan,select,Canceled
from src.shared.observations import inspect,ProtocolFault,parse
from src.adapters.gateway import ArchitectureGateway,StageCompiler,StageTransport,LIMITS,catalog
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest,canonical,CONDITIONS
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from native_model_integration_v1.src.provider_protocol.canned import completion
from native_model_integration_v1.src.provider_protocol.wire import sha
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
SCENARIOS=[]
def task():return json.loads((OUT/'public_inputs/ABC-PUBLIC-001.json').read_text(encoding='utf-8'))
def request(condition,run_id='unit',attempt_budget=36,token_budget=400000):return RunRequest(task()['task_id'],task(),'qwen3:4b','UNOBSERVED_NO_MODEL_QUERIED',{'temperature':.7,'top_p':.8,'think':False},None,8192,4096,condition,attempt_budget,token_budget,1800,run_id)
def temporary():
    p=OUT/'validation/scratch';p.mkdir(parents=True,exist_ok=True);assert p.resolve().is_relative_to(OUT.resolve());return tempfile.TemporaryDirectory(dir=p)
def unknown(text):
    d=json.loads(completion(json.dumps(text)));d.pop('prompt_eval_count');return json.dumps(d).encode()
class ScenarioCase(unittest.TestCase):
    def scenario(self,name,condition,values,**kwargs):
        with temporary() as d:
            r=execute(request(condition,**kwargs),Script(values),d)
            self.assertEqual([x['stage'] for x in r['provider_records']],list(values),'Unexpected dispatched stage or hidden extra call');self.assertEqual(r['events'][-1]['state'],'TERMINATED');self.assertEqual(r['events'][-2]['state'],'GENERATION_CLOSED');self.assertEqual(r['namespace'],'MOCK_WIRING_ONLY_NOT_EMPIRICAL');result=r['result'];ids=[c['candidate_id'] for c in result['all_generated_candidates']];self.assertEqual(len(ids),len(set(ids)));self.assertTrue(result['final_candidate'] in ids or result['final_candidate'] is None);self.assertEqual(result['physical_attempts'],len(result['model_invocations']));self.assertLessEqual(result['physical_attempts'],LIMITS[condition]);self.assertTrue(r['generation_closed']);self.assertIsNone(r['scientific_scores']);copy=dict(r);h=copy.pop('artifact_payload_sha256');self.assertEqual(sha(canonical(copy)),h)
            SCENARIOS.append({'scenario_id':self.id()+':'+name,'synthetic_input':task(),'scripted_responses':{k:[str(x) if isinstance(x,BaseException) else x.decode(errors='replace') if isinstance(x,bytes) else x for x in vals] for k,vals in values.items()},'expected':{'dispatched_stage_order':list(values),'internal_physical_limit':LIMITS[condition],'terminal_state_order':['GENERATION_CLOSED','TERMINATED'],'assertion_source':self.id()},'actual':r,'journal_evidence':{p.relative_to(d).as_posix():p.read_text(encoding='utf-8') for p in sorted(Path(d).rglob('*.jsonl'))},'not_empirical':True})
            return r
