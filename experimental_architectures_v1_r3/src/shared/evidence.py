"""Model critique/plan proposals gain no external evidential authority."""
from .observations import ProtocolFault,parse,same
CATEGORIES=('MISSING_PUBLIC_REQUIREMENT','TASK_DATA_CONTRADICTION','UNSUPPORTED_ASSERTION','FORMAT_CONTRACT','PRESERVATION_RISK','UNRESOLVED_UNCERTAINTY')
EVIDENCE_CLASSES=('PUBLIC_TASK_FACT','MODEL_GENERATED_OBSERVATION','LOCAL_DETERMINISTIC_CHECK','UNVERIFIED_INFERENCE','EXTERNAL_TRUSTED_EVIDENCE')
def violated(report):return {o['id']:o for o in report['observations'] if o['status']=='VIOLATED'}
def gate_targets(gate,report):
    known=violated(report)
    if gate['decision']!='REVISE':return []
    if len(set(gate['targets']))!=len(gate['targets']) or any(t not in known for t in gate['targets']):raise ProtocolFault('Gate target is not an actual public violation')
    return [known[t] for t in gate['targets']]
def supported_inventory(inventory,report):
    known=violated(report);accepted=[];rejected=[];seen=set()
    for f in inventory['findings']:
        o=known.get(f['observation_id']);reason=None
        if f['id'] in seen:reason='DUPLICATE_FINDING_ID'
        seen.add(f['id'])
        if f['category'] in ('UNSUPPORTED_ASSERTION','UNRESOLVED_UNCERTAINTY'):reason='UNVERIFIED_INFERENCE_NOT_ACTIONABLE'
        if f['evidence_class']=='EXTERNAL_TRUSTED_EVIDENCE':reason='NO_EXTERNAL_EXECUTION_EVIDENCE_AUTHORIZED'
        if o is None or f['target_path']!=o['path']:reason='NO_BOUND_LOCAL_PUBLIC_OBSERVATION'
        allowed={'format':{'FORMAT_CONTRACT'},'required':{'MISSING_PUBLIC_REQUIREMENT'},'equals_input':{'TASK_DATA_CONTRADICTION','PRESERVATION_RISK'},'equals_literal':{'TASK_DATA_CONTRADICTION','PRESERVATION_RISK'},'type':{'FORMAT_CONTRACT'}}
        if o is not None and f['category'] not in allowed.get(o['kind'],set()):reason=reason or 'CATEGORY_NOT_SUPPORTED_BY_OBSERVATION'
        if reason:rejected.append({'finding':f,'reason':reason,'origin':'MODEL_GENERATED_OBSERVATION'})
        else:accepted.append({'finding':f,'observation':o,'origin':'LOCAL_DETERMINISTIC_CHECK','external_verification':False})
    accepted.sort(key=lambda a:(-a['finding']['priority'],a['finding']['id']))
    return accepted,rejected

def checked_plan(plan,accepted):
    known={a['finding']['id']:a for a in accepted};actions=[];paths={};ids=set()
    for action in plan['actions']:
        fid=action['target_id']
        if fid not in known or fid in ids:raise ProtocolFault('Invented/duplicate plan target')
        ids.add(fid);o=known[fid]['observation']
        if action['path']!=o['path']:raise ProtocolFault('Plan changes an unbound path')
        value=parse(action['suggested_value_json'])
        if o['kind'] in ('equals_input','equals_literal') and not same(value,o['expected']):raise ProtocolFault('Plan contradicts explicit public requirement')
        if action['path'] in paths and not same(value,paths[action['path']]):raise ProtocolFault('Contradictory repair proposals')
        paths[action['path']]=value;actions.append({'target_id':fid,'observation_id':o['id'],'path':o['path'],'suggested_value':value,'status':'MODEL_PLAN_NOT_EXECUTED_EVIDENCE'})
    return actions
