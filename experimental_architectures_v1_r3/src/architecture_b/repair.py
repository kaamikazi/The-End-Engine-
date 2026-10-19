"""B: proposal inventory -> grounded targets -> explicit plan -> one repair."""
from ..shared.evidence import supported_inventory,checked_plan
from ..shared.observations import preservation,local_improvement,ProtocolFault,equivalent

def run(s):
    c0,o0=s.generate('INITIAL');before=s.checks[c0.candidate_id];s.event('REPAIR_INVENTORY_REQUESTED')
    inventory,io=s.assess('REPAIR_INVENTORY',(o0,));accepted,rejected=supported_inventory(inventory,before)
    s.event('REPAIR_FINDINGS_CLASSIFIED',supported=accepted,rejected=rejected)
    if not accepted:
        s.pick(c0,'NO_SUPPORTED_DEFECT');s.notes.extend(r['reason'] for r in rejected)
        return 'UNRESOLVED' if before['violations'] else 'NO_ACTIONABLE_REVISION'
    plan,po=s.assess('REPAIR_PLAN',(o0,io))
    try:actions=checked_plan(plan,accepted)
    except ProtocolFault as error:s.event('REPAIR_PLAN_REJECTED',reason=str(error));s.pick(c0,'INVALID_TARGETED_PLAN');return 'UNRESOLVED'
    if not actions:s.pick(c0,'EMPTY_REPAIR_PLAN');return 'NO_ACTIONABLE_REVISION'
    s.event('REPAIR_TARGETED_PLAN',actions=actions,origin='MODEL_PLAN_NOT_EXECUTED_EVIDENCE')
    revised,ro=s.generate('REPAIR_REVISION',(o0,io,po),parents=(c0.candidate_id,));after=s.checks[revised.candidate_id]
    preserve=preservation(before,after,[a['path'] for a in actions]);improved,resolved,new=local_improvement(before,after)
    s.event('REPAIR_LOCAL_PRESERVATION_CHECK',preservation=preserve,resolved_public_observations=resolved,unresolved_public_observations=after['violations'],new_public_violations=new)
    if improved and preserve['status']!='FAIL':
        s.pick(revised,'RECORDED_PUBLIC_TARGET_REPAIRED')
        return 'UNRESOLVED' if after['violations'] else 'COMPLETED'
    s.pick(c0,'NO_PROVEN_LOCAL_REPAIR_OR_UNAFFECTED_CONTENT_DAMAGED')
    return 'NO_PROGRESS' if equivalent(c0.answer,revised.answer) or not resolved else 'UNRESOLVED'
