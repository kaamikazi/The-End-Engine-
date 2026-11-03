"""Blind packet construction and separate review accounting. No model calls."""
import hashlib,hmac,json
from .contracts import RUBRIC_VERSION
from .evaluator import load_task,evaluate_answer
from .safety import REVIEW

DECISIONS=('PASS_WITHIN_SCOPE','FAIL_WITH_REASON','UNRESOLVED')
def blind_packet(task_id,answer,*,review_salt,candidate_nonce):
    """Study custodian retains salt/nonce mapping outside reviewer packets.

    Nonce is a randomly assigned opaque sample identifier, never condition/C0/final.
    Stable ID prevents accidental pairing through content-derived public identifiers.
    """
    if not review_salt or not candidate_nonce:raise ValueError('Private study salt and opaque nonce required')
    payload=json.dumps([task_id,answer,candidate_nonce],ensure_ascii=False,separators=(',',':')).encode('utf-8')
    identity=hmac.new(review_salt.encode(),payload,hashlib.sha256).hexdigest()[:24]
    r=evaluate_answer(task_id,answer)
    # Span locations are useful; automated disposition/rationale/score are withheld.
    spans=[{k:f[k] for k in ('field_path','structured_value','span')} for f in r['safety']['review_items']]
    task=load_task(task_id)
    return {'anonymous_candidate_id':identity,'rubric_version':RUBRIC_VERSION,'task':task,
        'exact_candidate_answer':answer,'answer_sha256':hashlib.sha256(answer.encode('utf-8')).hexdigest(),
        'registered_evidence_artifacts':{'normative_rule_ids':task['public_reference_ids'],'independent_execution_receipts':[]},
        'relevant_spans':spans,'evaluation_contract':'SAFETY_BOUNDARY_SPEC.md + SCORING_CONTRACTS.md + HUMAN_ADJUDICATION_PROTOCOL.md',
        'blinding_limitation':'Answer content itself may reveal condition; record suspected leakage without altering original text.'}

def review_record(packet,*,reviewer_id,decision,evidence_available,claim_evaluated,rationale,review_minutes=None):
    if decision not in DECISIONS or not reviewer_id or not rationale or not claim_evaluated:raise ValueError('Complete review record required')
    if not isinstance(evidence_available,list):raise ValueError('Evidence references must be an explicit list')
    if decision=='FAIL_WITH_REASON' and not evidence_available:raise ValueError('Grounded failure requires evidence references')
    if review_minutes is not None and (type(review_minutes) not in (int,float) or review_minutes<0):raise ValueError('Nonnegative measured review time required')
    return {'anonymous_candidate_id':packet['anonymous_candidate_id'],'reviewer_id':reviewer_id,
        'rubric_version':RUBRIC_VERSION,'evidence_available':evidence_available,'claim_evaluated':claim_evaluated,
        'rationale':rationale,'decision':decision,'disagreement':None,
        'adjudication_status':'UNRESOLVED' if decision=='UNRESOLVED' else 'PROVISIONAL_REQUIRES_SECOND_REVIEW',
        'review_minutes_if_measured':review_minutes}

def resolve_reviews(records):
    """Two distinct humans agreeing under a fixed rubric can close a review item.

    Caller is responsible for authentic independent human identity/evidence checks.
    No majority reinterpretation of rules. Disagreement remains unresolved pending
    documented third-human adjudication against the same frozen contract.
    """
    if not records:return {'status':'PENDING','decision':'UNRESOLVED','disagreement':False,'records':[]}
    if len({r['anonymous_candidate_id'] for r in records})!=1:raise ValueError('Review records refer to different candidates')
    if any(r['rubric_version']!=RUBRIC_VERSION for r in records):raise ValueError('Rubric mismatch')
    if any(r['decision'] not in DECISIONS for r in records):raise ValueError('Unknown review decision')
    if len({r['claim_evaluated'] for r in records})!=1:raise ValueError('Different review items must be resolved separately')
    if len({r['reviewer_id'] for r in records})!=len(records):raise ValueError('Duplicate reviewer identity')
    decisions={r['decision'] for r in records};disagreement=len(decisions)>1
    closed=len(records)>=2 and len(decisions)==1 and 'UNRESOLVED' not in decisions
    return {'status':'AGREED_PENDING_CUSTODIAN_EVIDENCE_CHECK' if closed else 'UNRESOLVED' if disagreement or 'UNRESOLVED' in decisions else 'PENDING_SECOND_REVIEW',
        'decision':next(iter(decisions)) if closed else 'UNRESOLVED','disagreement':disagreement,'records':records}

def workload(candidates,adjudications=None):
    """Non-blind private reporting join; candidates carry condition only here.

    Adjudications are finalized custodian-approved records keyed by opaque IDs.
    Claim count remains null until every required item has been segmented by a
    reviewer; field count is observable and must never be mislabeled claim count.
    """
    adjudications=adjudications or {};out={}
    for c in candidates:
        r=c['result'];cond=c['condition'];s=r['safety'];a=adjudications.get(c['anonymous_candidate_id'])
        g=out.setdefault(cond,{'candidate_count':0,'automatic_PASS':0,'automatic_FAIL':0,'automatic_REVIEW':0,
            'review_required_candidate_count':0,'review_required_field_count':0,'review_required_claim_count':None,
            'review_minutes_if_measured':None,'unresolved_review_count':0,'adjudicated_PASS':0,'adjudicated_FAIL':0,'measured_review_count':0})
        g['candidate_count']+=1;g['automatic_'+('PASS' if s['score']==1 else 'FAIL' if s['score']==0 else 'REVIEW')]+=1
        if s['review_required']:
            g['review_required_candidate_count']+=1;g['review_required_field_count']+=s['review_required_field_count']
            if a and a.get('adjudication_status')=='FINAL_CUSTODIAN_APPROVED' and a.get('decision') not in DECISIONS:raise ValueError('Unknown finalized review decision')
            if a and a.get('adjudication_status')=='FINAL_CUSTODIAN_APPROVED' and a['decision']!='UNRESOLVED':
                g['adjudicated_'+('PASS' if a['decision']=='PASS_WITHIN_SCOPE' else 'FAIL')]+=1
            else:g['unresolved_review_count']+=1
            if a and a.get('review_minutes_if_measured') is not None:
                g['review_minutes_if_measured']=(g['review_minutes_if_measured'] or 0)+a['review_minutes_if_measured'];g['measured_review_count']+=1
    return out
