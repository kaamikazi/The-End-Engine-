"""Canned bytes only. Scripts supply observations, never choose algorithm branches."""
import json
from copy import deepcopy
from native_model_integration_v1.src.provider_protocol.canned import completion
class Canceled(RuntimeError):pass
class Script:
    def __init__(self,responses):self.responses={k:list(v) for k,v in deepcopy(responses).items()};self.seen=[]
    def reply(self,stage):
        self.seen.append(stage)
        if stage not in self.responses or not self.responses[stage]:raise RuntimeError('Synthetic stage response unavailable')
        value=self.responses[stage].pop(0)
        if isinstance(value,BaseException):raise value
        if type(value) is bytes:return value
        text=value if type(value) is str else json.dumps(value,ensure_ascii=False)
        return completion(text)

def complete():return {'item_id':'T-1','amount':7,'status':'draft'}
def gate(targets=(),decision=None):return {'decision':decision or ('REVISE' if targets else 'STOP'),'targets':list(targets),'rationale':'Synthetic public observation proposal','uncertainty':[]}
def finding(fid='F1',observation='amount_from_input',path='/amount',category='TASK_DATA_CONTRADICTION',priority=2,evidence='LOCAL_DETERMINISTIC_CHECK'):
    return {'id':fid,'category':category,'observation_id':observation,'target_path':path,'proposal':'Synthetic targeted public correction','evidence_class':evidence,'priority':priority}
def plan(target='F1',path='/amount',value=7):return {'actions':[{'target_id':target,'path':path,'suggested_value_json':json.dumps(value)}]}
def select(preferred=None,support=(),decision=None):return {'decision':decision or ('SELECT' if preferred else 'TIE'),'preferred_id':preferred,'rationale':'Synthetic comparison proposal, not verification','support_observation_ids':list(support)}
