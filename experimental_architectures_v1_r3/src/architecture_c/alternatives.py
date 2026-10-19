"""C: independent candidate set -> bounded comparison -> non-consensus selection."""
from ..shared.observations import local_improvement,equivalent

def run(s):
    c0,o0=s.generate('INITIAL');s.event('INDEPENDENT_ALTERNATIVES_BEGIN')
    c1,o1=s.generate('ALTERNATIVE_REQUIREMENTS');c2,o2=s.generate('ALTERNATIVE_CONSTRAINTS')
    s.event('ALTERNATIVE_DIVERSITY_RECORDED',byte_distinct=len({c.answer for c in s.candidates}),json_equivalent_pairs=[[a.candidate_id,b.candidate_id] for i,a in enumerate(s.candidates) for b in s.candidates[i+1:] if equivalent(a.answer,b.answer)],interpretation='STRUCTURAL_DIFFERENCE_NOT_PROOF_OF_REASONING_DIVERSITY')
    selection,so=s.assess('ALTERNATIVE_SELECTION',(o0,o1,o2));s.event('ALTERNATIVE_COMPARISON',model_proposal=selection,authority='ADVISORY_NOT_EXTERNAL_VERIFICATION')
    byid={c.candidate_id:c for c in s.candidates};preferred=byid.get(selection['preferred_id'])
    if selection['decision']!='SELECT' or preferred is None:
        s.pick(c0,'TIE_UNCERTAINTY_OR_INVALID_SELECTOR_ID');return 'UNRESOLVED'
    if preferred.candidate_id==c0.candidate_id:s.pick(c0,'SELECTOR_RETAINED_C0');return 'COMPLETED' if not s.checks['C0']['violations'] else 'UNRESOLVED'
    p=s.checks[preferred.candidate_id];improved,resolved,new=local_improvement(s.checks['C0'],p)
    supported=set(selection['support_observation_ids'])
    better_exists=any(local_improvement(p,s.checks[c.candidate_id])[0] for c in s.candidates if c!=preferred)
    if improved and supported and supported<=set(resolved) and not better_exists:
        s.pick(preferred,'STRICT_PUBLIC_LOCAL_ADVANTAGE_NOT_LENGTH_CONFIDENCE_OR_CONSENSUS');return 'UNRESOLVED' if p['violations'] else 'COMPLETED'
    s.pick(c0,'UNSUPPORTED_RANKING_OR_NO_STRICT_LOCAL_ADVANTAGE');s.notes.append('Model preference/agreement does not establish correctness');return 'UNRESOLVED'
