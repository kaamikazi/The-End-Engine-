"""A: one need gate, optional single targeted revision, conservative retention."""
from ..shared.evidence import gate_targets
from ..shared.observations import preservation,local_improvement,equivalent,ProtocolFault

def run(s):
    c0,o0=s.generate('INITIAL');before=s.checks[c0.candidate_id];s.event('SPARSE_NEED_ASSESSMENT')
    gate,go=s.assess('SPARSE_GATE',(o0,))
    try:targets=gate_targets(gate,before)
    except ProtocolFault as error:
        s.event('SPARSE_UNSUPPORTED_CRITICISM',reason=str(error));s.pick(c0,'UNSUPPORTED_GATE_TARGET');return 'UNRESOLVED' if before['violations'] else 'NO_ACTIONABLE_REVISION'
    s.event('SPARSE_GATE_DECISION',model_decision=gate['decision'],supported_targets=[o['id'] for o in targets],rationale=gate['rationale'])
    if not targets:
        s.notes.extend(gate['uncertainty']);s.pick(c0,'NO_SUPPORTED_ACTIONABLE_TARGET')
        return 'UNRESOLVED' if before['violations'] else 'NO_ACTIONABLE_REVISION'
    revised,ro=s.generate('SPARSE_REVISION',(o0,go),parents=(c0.candidate_id,));after=s.checks[revised.candidate_id]
    preserve=preservation(before,after,[o['path'] for o in targets]);improved,resolved,new=local_improvement(before,after)
    s.event('SPARSE_LOCAL_VALIDATION',preservation=preserve,resolved_public_observations=resolved,new_public_violations=new,semantic_correctness='NOT_ASSESSED')
    if improved and preserve['status']!='FAIL':
        s.pick(revised,'SUPPORTED_LOCAL_DEFECT_RESOLVED_NO_KNOWN_PRESERVATION_LOSS')
        if preserve['status']!='PASS':s.notes.append('Preservation of unparsed C0 unknown')
        return 'UNRESOLVED' if after['violations'] else 'COMPLETED'
    s.pick(c0,'REVISION_NOT_JUSTIFIED_OR_PRESERVATION_FAILED')
    return 'NO_PROGRESS' if equivalent(c0.answer,revised.answer) or not resolved else 'UNRESOLVED'
