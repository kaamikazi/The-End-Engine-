"""Bounded whole-answer JSON parsing. Never choose a convenient transcript fragment."""
import json
import re
import math

RUBRIC_VERSION='exp-pack-1.0.2-draft'
MAX_CHARS=65536
MAX_NODES=2048
MAX_DEPTH=12

class ContractError(ValueError):
    def __init__(self,code):self.code=code;super().__init__(code)

def _unique(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ContractError('DUPLICATE_JSON_KEY')
        out[key]=value
    return out

def parse_answer(text,answer_region_status='AUTHORITATIVE'):
    if answer_region_status!='AUTHORITATIVE':raise ContractError('ANSWER_REGION_REQUIRES_REVIEW')
    if not isinstance(text,str):raise ContractError('ANSWER_NOT_TEXT')
    if not text.strip():raise ContractError('EMPTY_ANSWER')
    if len(text)>MAX_CHARS:raise ContractError('ANSWER_TOO_LARGE')
    if re.search(r'</?think\b',text,re.I):raise ContractError('TRANSCRIPT_BOUNDARY_REQUIRES_REVIEW')
    body=text.strip()
    if body.startswith('```'):
        match=re.fullmatch(r'```json[ \t]*\r?\n(.*?)\r?\n```',body,re.S|re.I)
        if not match:raise ContractError('WHOLE_ANSWER_FORMAT')
        body=match[1]
    def nonfinite(value):raise ContractError('NONFINITE_JSON_NUMBER')
    try:obj=json.loads(body,object_pairs_hook=_unique,parse_constant=nonfinite)
    except ContractError:raise
    except (ValueError,RecursionError):raise ContractError('INVALID_JSON')
    if not isinstance(obj,dict):raise ContractError('ROOT_NOT_OBJECT')
    stack=[(obj,0)];nodes=0
    while stack:
        value,depth=stack.pop();nodes+=1
        if depth>MAX_DEPTH or nodes>MAX_NODES:raise ContractError('JSON_COMPLEXITY_LIMIT')
        if isinstance(value,dict):stack.extend((x,depth+1) for x in value.values())
        elif isinstance(value,list):stack.extend((x,depth+1) for x in value)
        elif isinstance(value,float) and not math.isfinite(value):raise ContractError('NONFINITE_JSON_NUMBER')
    return obj

def dimension(score=None,*,status='SCORED',violations=()):
    return {'status':status,'score':None if score is None else round(score,6),'violations':list(violations)}

def check_fields(obj,required,optional=()):
    errors=[]
    if not isinstance(obj,dict):return ['OBJECT_REQUIRED']
    errors.extend('MISSING_FIELD:'+key for key in sorted(set(required)-set(obj)))
    errors.extend('UNREQUESTED_FIELD:'+key for key in sorted(set(obj)-set(required)-set(optional)))
    return errors
