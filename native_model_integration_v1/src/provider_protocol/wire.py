"""Existing Ollama /api/generate mapping, never a network transport."""
import hashlib,json
from dataclasses import asdict
from v0351_core_regression_pilot.bench.providers import ModelSettings,render
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
SETTINGS=ModelSettings(model='qwen3:4b')
ADAPTER_VERSION='native-model-integration-v1'
PROTOCOL_TARGET='repository Ollama generate contract; observed server version UNKNOWN'
def body(payload):return json.dumps(payload,allow_nan=False).encode('utf-8') # exactly historical _http encoding

def expected(request,structured,seed):
    s=SETTINGS
    p={'model':s.model,'stream':False,'think':s.think,'prompt':render(request),'options':{'temperature':s.temperature,'top_p':s.top_p,'num_predict':s.num_predict,'num_ctx':s.num_ctx,'seed':seed}}
    if structured:p['format']=request.schema
    return p

def validate_wire(payload,request,structured,seed):
    if type(payload) is not dict or payload!=expected(request,structured,seed) or body(payload)!=body(expected(request,structured,seed)):raise BoundaryError('Provider payload differs from exact approved mapping')
    if type(seed) is not int or not 0<=seed<2**32:raise BoundaryError('Invalid derived seed')
    if structured and type(request.schema) is not dict:raise BoundaryError('Structured output requires Engine schema')
    return body(payload)

def sha(b):return hashlib.sha256(b).hexdigest()
