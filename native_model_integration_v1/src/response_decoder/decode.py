"""Strict nonstreaming Ollama receipt; raw bytes stay host-only."""
import json,math
from v0351_core_regression_pilot.bench.providers import ProviderError
FIELDS={'model','created_at','response','thinking','done','done_reason','context','total_duration','load_duration','prompt_eval_count','prompt_eval_cached_count','prompt_eval_duration','eval_count','eval_duration'}
DURATIONS=('total_duration','load_duration','prompt_eval_duration','eval_duration')
COUNTS=('prompt_eval_count','prompt_eval_cached_count','eval_count')
class ReceiptError(ProviderError):
    def __init__(self,reason):super().__init__('provider_receipt_rejected',reason)

def decode(raw,model):
    if type(raw) is not bytes or len(raw)>2000000:raise ReceiptError('Missing or oversized raw completion')
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ReceiptError('Duplicate receipt key')
            d[k]=v
        return d
    try:r=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ReceiptError('Nonfinite receipt')))
    except (UnicodeError,ValueError):raise ReceiptError('Malformed response JSON') from None
    if type(r) is not dict:raise ReceiptError('Receipt object required')
    if set(r)=={'error'} and type(r['error']) is str:raise ReceiptError('Provider error; raw details retained privately')
    if set(r)-FIELDS or not {'model','response','done','done_reason'}<=set(r):raise ReceiptError('Missing fields or unexpected provider metadata/tools')
    if r['model']!=model:raise ReceiptError('MODEL_IDENTITY_DRIFT')
    if type(r['response']) is not str or type(r['done']) is not bool or type(r['done_reason']) is not str:raise ReceiptError('Invalid completion fields')
    if not r['done']:raise ReceiptError('Incomplete/interrupted nonstreaming receipt')
    if r['done_reason'] not in ('stop','length'):raise ReceiptError('Unknown stop reason needs compatibility review')
    for k in (*DURATIONS,*COUNTS):
        if k in r and (type(r[k]) is not int or r[k]<0):raise ReceiptError('Invalid numeric metrics')
    if 'created_at' in r and type(r['created_at']) is not str:raise ReceiptError('Invalid timestamp')
    if 'thinking' in r and type(r['thinking']) is not str:raise ReceiptError('Invalid thinking metadata')
    if 'context' in r and (type(r['context']) is not list or len(r['context'])>100000 or any(type(x) is not int or x<0 for x in r['context'])):raise ReceiptError('Invalid deprecated context metadata')
    if 'total_duration' in r and any(r.get(k,0)>r['total_duration'] for k in DURATIONS[1:]):raise ReceiptError('Inconsistent duration totals')
    if r.get('prompt_eval_cached_count',0)>r.get('prompt_eval_count',float('inf')):raise ReceiptError('Inconsistent cached token count')
    normalized=dict(r)
    if r.get('prompt_eval_cached_count',0):normalized.pop('prompt_eval_count',None) # inclusion semantics not verified; no guessed total
    return normalized
