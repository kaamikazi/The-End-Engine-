"""Public-contract checks only. No task scoring, hidden answers or evaluator imports.
We implement JSON shape/declared literal/input equality, never infer natural-language
policy answers. Passing these observations is NOT task correctness certification.
"""
import json
from cognitive_architecture_lab_v1.src.interfaces.contracts import canonical
from .strict_json import DataFault as ProtocolFault,NumericFault,loads
MISSING=object()
def parse(text):
    if type(text) is not str:raise ProtocolFault('Response type')
    try:
        if len(text.encode('utf-8'))>1000000:raise ProtocolFault('Response size')
    except UnicodeError as error:raise ProtocolFault('Response encoding') from error
    t=text.strip()
    if t.startswith('```json\n') and t.endswith('\n```'):t=t[8:-4]
    return loads(t)

def pointer(value,path):
    if path=='':return value
    if type(path) is not str or not path.startswith('/'):return MISSING
    try:
        for key in path[1:].split('/'):
            key=key.replace('~1','/').replace('~0','~');value=value[int(key)] if type(value) is list else value[key]
        return value
    except (KeyError,IndexError,TypeError,ValueError):return MISSING

def escape(s):return str(s).replace('~','~0').replace('/','~1')
def same(a,b):return a is not MISSING and b is not MISSING and canonical(a)==canonical(b)
def definitions(task):
    c=task['output_contract'];out=[{'id':'JSON_OBJECT','kind':'format','path':'','expected':{'type':'object'},'public_source':'/output_contract/format'}]
    for key in c.get('required_fields',[]):out.append({'id':'required:'+key,'kind':'required','path':'/'+escape(key),'public_source':'/output_contract/required_fields'})
    if 'required_scope' in c:out.append({'id':'public_scope','kind':'equals_literal','path':'/scope','expected':c['required_scope'],'public_source':'/output_contract/required_scope'})
    for d in c.get('public_constraints',[]):
        if set(d)-{'id','kind','path','source_path','expected'} or not {'id','kind','path'}<=set(d) or d['kind'] not in ('required','equals_input','equals_literal','type'):raise ProtocolFault('Unsupported PUBLIC constraint definition')
        if any(x['id']==d['id'] for x in out):raise ProtocolFault('Duplicate PUBLIC constraint ID')
        n=dict(d,public_source='/output_contract/public_constraints')
        if d['kind']=='equals_input':
            if not d.get('source_path','').startswith('/input/'):raise ProtocolFault('Only public input source paths allowed')
            e=pointer(task,d['source_path'])
            if e is MISSING:raise ProtocolFault('Missing public input source')
            n['expected']=e
        out.append(n)
    return out

def identifier_facts(task):
    # Only public opaque ID fields and declared copy/identifier requirements.
    text=(task['task_statement']+' '+str(task['output_contract'])).lower()
    if not any(word in text for word in ('identifier','accession','row_id','copy','immutable')):return {}
    facts={}
    def visit(v,path='/input'):
        if type(v) is dict:
            for k,x in v.items():
                if (k=='id' or k=='accession' or k.endswith('_id')) and type(x) is str:facts.setdefault(k,[]).append({'value':x,'public_source':path+'/'+escape(k)})
                visit(x,path+'/'+escape(k))
        elif type(v) is list:
            for j,x in enumerate(v):visit(x,path+'/'+str(j))
    visit(task['input']);return facts

def identifier_usage(value,facts):
    found={k:[] for k in facts}
    def visit(v):
        if type(v) is dict:
            for k,x in v.items():
                if k in facts and type(x) is str:found[k].append(x)
                visit(x)
        elif type(v) is list:
            for x in v:visit(x)
    visit(value);return found

def identifier_preservation(before,after):
    lost=[];introduced=[]
    for key,items in before['public_identifier_facts'].items():
        allowed={x['value'] for x in items};old=set(before['identifier_usage'][key]);new=set(after['identifier_usage'].get(key,[]))
        lost.extend(key+':'+v for v in sorted((old&allowed)-new));introduced.extend(key+':'+v for v in sorted((new-allowed)-(old-allowed)))
    return {'lost_public_identifiers':lost,'introduced_nonpublic_identifiers':introduced,'scope':'Public ID membership/preservation only, not row mapping or full task correctness'}

def inspect(task,text):
    defs=definitions(task)
    try:value=parse(text);object_ok=type(value) is dict
    except NumericFault:raise
    except ProtocolFault:value=None;object_ok=False
    obs=[]
    for d in defs:
        actual=pointer(value,d['path']) if object_ok else MISSING
        if d['kind']=='format':state='SATISFIED' if object_ok else 'VIOLATED'
        elif not object_ok:state='UNKNOWN'
        elif d['kind']=='required':state='VIOLATED' if actual is MISSING else 'SATISFIED'
        elif d['kind'] in ('equals_input','equals_literal'):state='SATISFIED' if same(actual,d.get('expected',MISSING)) else 'VIOLATED'
        else:
            types={'string':str,'boolean':bool,'number':(int,float),'object':dict,'array':list}
            wanted=types.get(d.get('expected'));ok=actual is not MISSING and (type(actual) in wanted if type(wanted) is tuple else type(actual) is wanted);state='SATISFIED' if ok else 'VIOLATED'
        obs.append({**d,'status':state,'actual':'<MISSING>' if actual is MISSING else actual,'origin':'LOCAL_DETERMINISTIC_CHECK','semantic_scope':'EXPLICIT_PUBLIC_CONSTRAINT_ONLY'})
    facts=identifier_facts(task);usage=identifier_usage(value,facts)
    return {'public_identifier_facts':facts,'identifier_usage':usage,'parsed':value,'format_ok':object_ok,'observations':obs,'violations':[o['id'] for o in obs if o['status']=='VIOLATED'],'unknown':[o['id'] for o in obs if o['status']=='UNKNOWN'],'semantic_correctness':'NOT_ASSESSED'}

def leaves(x,path=''):
    if type(x) is dict and x:return {p:v for k,v in x.items() for p,v in leaves(v,path+'/'+escape(k)).items()}
    if type(x) is list and x:return {p:v for i,v in enumerate(x) for p,v in leaves(v,path+'/'+str(i)).items()}
    return {path:x}
def preservation(before,after,allowed_paths):
    ids=identifier_preservation(before,after)
    if ids['lost_public_identifiers'] or ids['introduced_nonpublic_identifiers']:return {'status':'FAIL','outside_target_changes':[],'public_identifier_preservation':ids}
    if not before['format_ok']:return {'status':'UNKNOWN_UNPARSED_C0','outside_target_changes':[]}
    if not after['format_ok']:return {'status':'FAIL','outside_target_changes':['<invalid response>']}
    a,b=leaves(before['parsed']),leaves(after['parsed']);changed=[p for p in sorted(a.keys()|b.keys()) if not same(a.get(p,MISSING),b.get(p,MISSING))]
    outside=[p for p in changed if not any(t=='' or p==t or p.startswith(t+'/') for t in allowed_paths)]
    return {'status':'FAIL' if outside else 'PASS','outside_target_changes':outside,'changed_paths':changed}

def local_improvement(before,after):
    resolved=set(before['violations'])-set(after['violations'])
    new=set(after['violations'])-(set(before['violations'])|set(before['unknown']))
    ids=identifier_preservation(before,after)
    if ids['lost_public_identifiers'] or ids['introduced_nonpublic_identifiers']:new.add('PUBLIC_IDENTIFIER_PRESERVATION')
    return bool(resolved) and not new and after['format_ok'],sorted(resolved),sorted(new)
def equivalent(a,b):
    try:return same(parse(a),parse(b))
    except ProtocolFault:return a==b
