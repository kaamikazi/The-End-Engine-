"""Research annotations and reconciliation. No Engine import or evaluator execution.

The per-task annotations are manual judgments for these saved artifacts only.
They are not a general issue classifier, runtime policy, or new benchmark labels.
"""
import csv
import json
import hashlib
from collections import Counter
from pathlib import Path
import analyze as a

ROOT, OUT = a.ROOT, a.OUT

def readcsv(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def finding_grounding(f):
    """Manual, occurrence-level scope labels; not independent world-truth labels."""
    task=f['run_id'][:6];old=f['version']=='0.3.5';native=f['run_id'].endswith('NATIVE');i=int(f['cycle']);text=f['description']
    if task=='BA-001':
        return ('GROUNDED_SCOPED_OBSERVATION','Positive already-satisfied rounding/conversion observation; not a new defect') if native else ('CONTRADICTED_WITHIN_SCOPE','Ordering/completeness allegation conflicts with saved positions/values; old wrong numeric value is separate')
    if task=='BA-002':
        if old:
            return ('GROUNDED_SCOPED_OBSERVATION','Already-repaired loop/consistent explanation observation; not a new defect') if native and i==3 else ('CONTRADICTED_WITHIN_SCOPE','Original versus corrected loop or absent-guard allegation conflicts with saved repaired function')
        if native:return ('GROUNDED_SCOPED_OBSERVATION','Docstring requirement is present; already-satisfied topic, not a demonstrated defect')
        if 'range function' in text:return ('GROUNDED_SCOPED_OBSERVATION','Full range is literally present and finite frozen checks pass')
        return ('PLAUSIBLE_BUT_UNVERIFIED','Positive-integer claim is broader than observed nonpositive guard/seven tests; full type semantics not proven')
    if task=='BA-008':
        if native:
            if 'solution correctly implements' in text.lower():return ('GROUNDED_SCOPED_OBSERVATION','Frozen sorting checks support this narrow behavior; positive observation, not a defect')
            return ('UNSUPPORTED_CANDIDATE_DEFECT','Task factual conflict/normative goal does not itself demonstrate candidate failure; unsupported is not false')
        if text.startswith('The assumption'):return ('UNSUPPORTED_CANDIDATE_DEFECT','Requested sorting goal is not an externally falsified high-risk assumption')
        return ('UNKNOWN','Request for a falsifiable check may be legitimate uncertainty; illustrative check presence does not establish universal verification')
    if task=='BA-009':
        if native:
            if '100%' in text:return ('PLAUSIBLE_BUT_UNVERIFIED','Overstated paraphrase; established status is observed, literal100% inference is not')
            if 'Unsupported epistemic status established' in text:return ('UNKNOWN','Previously valid status concern may be stale after current enum becomes likely; actual-answer scope matters')
            return ('GROUNDED_SCOPED_OBSERVATION','Explicit missing observations/status support gap; no conclusion about true database cause')
        return ('PLAUSIBLE_BUT_UNVERIFIED','Missing-data caution is reasonable; exact definitely/causal-acceptance attribution is broader than the candidate and may be ambiguous')
    return ('UNKNOWN','No case-specific adjudication')

def review_cycle(row):
    version,task,mode,i=row['experiment_version'],row['task_id'],row['condition'],row['cycle_index']
    old=version=='0.3.5'; native=mode.endswith('NATIVE')
    plan=json.loads(row['revision_plan']); actions=' | '.join(c['action'] for c in plan['changes'])
    result={'target_actionable_as_defect':'UNKNOWN','critique_defect_assessment':'UNKNOWN',
        'plan_describes_issue':'UNKNOWN','plan_relevance':'UNKNOWN','plan_specificity':'UNKNOWN',
        'preservation_requested':True,'preservation_observed':'UNKNOWN',
        'issue_addressed':'UNKNOWN','unrelated_changes':'UNKNOWN','new_authority_or_citation':'NONE OBSERVED',
        'output_contract_preserved':'UNKNOWN','revision_failure_categories':[],
        'manual_review_rationale':'','grounding_uncertainty':'Scoped saved-output review; not universal semantic adjudication.'}
    if task=='BA-001':
        if native:
            row['selected_issue_assessment']='PLAUSIBLE_BUT_UNVERIFIED'
            row['assessment_basis']='One-decimal requirement is a valid topic, already satisfied in the displayed C0; not evidence of a defect.'
            result.update(target_actionable_as_defect='NO: requirement already satisfied',critique_defect_assessment='NO DEFECT PROPOSED: positive finding',
                plan_describes_issue='NO remaining encoded error',plan_relevance='Redundant formatting/rounding request',plan_specificity='SPECIFIC but already satisfied',
                preservation_observed='YES within frozen checks',issue_addressed='ALREADY SATISFIED',unrelated_changes='No displayed-answer change',
                output_contract_preserved='YES',revision_failure_categories=['NEUTRAL REVISION'],
                manual_review_rationale='Displayed JSON is unchanged and scores 1→1; critique says conversions/rounding are supported.')
        else:
            if i>1 and not old:
                row['selected_issue_assessment']='CONTRADICTED_BY_AVAILABLE_EVIDENCE'
                row['assessment_basis']='All five values and positions are present and satisfy the frozen numeric evaluator; completeness/misassignment allegation conflicts with those scoped checks.'
            result.update(target_actionable_as_defect='NO demonstrated ordering/completeness defect',
                critique_defect_assessment='CONTRADICTED_BY_AVAILABLE_EVIDENCE within encoded ordering/completeness checks',
                plan_describes_issue='NO: misordering/completeness diagnosis',plan_relevance='Misses 74.7→70.7 numeric error' if old else 'Asks to repair already correct values',
                plan_specificity='Mechanism proposed but no correct targeted numeric delta',
                preservation_observed='NO: C2 malformed partial array' if old and i==2 else 'YES within encoded original requirements',
                issue_addressed='NO demonstrated defect repaired',unrelated_changes='C2 changes values and loses JSON' if old and i==2 else 'No useful numeric change',
                output_contract_preserved='NO' if old and i==2 else 'YES',revision_failure_categories=['BAD ISSUE'],
                manual_review_rationale='Critique invents ordering errors. Old J002 detects the real numeric error, but model plans focus on ordering; no candidate corrects 74.7. New C0 is already correct.')
    elif task=='BA-002':
        row['selected_issue_assessment']='PLAUSIBLE_BUT_UNVERIFIED'
        row['assessment_basis']='Positive-integer/last-chunk requirement is a valid check topic; selecting it does not demonstrate failure. Type handling outside frozen inputs remains incompletely covered.'
        result.update(target_actionable_as_defect='NO demonstrated targeted guard/range failure; structured non-integer gap is separate',
            critique_defect_assessment='CONTRADICTED/MISATTRIBUTED allegation about existing guard or original loop' if old else 'NO DEFECT PROPOSED or inadequate positive support',
            plan_describes_issue='PARTIAL: repeats original bug instead of current repaired code',
            plan_relevance='Redundant guard/range repair; no measurable missing type-check repair',plan_specificity='SPECIFIC guard/range text; incorrect current-code premise',
            preservation_observed='YES within seven frozen checks',issue_addressed='No encoded defect remains; structured type gap not fixed',
            unrelated_changes='Native prose/analysis shortened in first newer revision; code requirements retained' if native and not old and i==1 else 'No substantive code change',
            output_contract_preserved='YES within recorded format',revision_failure_categories=['BAD ISSUE'] if old else ['NEUTRAL REVISION'],
            manual_review_rationale='Saved code already has full range and positive-size guard. Native also has integer guard. Structured lacks full non-integer handling, which seven frozen tests do not cover. Claims of absent existing guards are not that legitimate coverage gap.')
    elif task=='BA-008':
        # A correct sorting requirement/assumption must not be confused with a defective critique.
        if old and not native:
            row['selected_issue_assessment']='UNSUPPORTED'
            row['assessment_basis']='Candidate speculation about list.sort is untested in this run; no independent support or scoped test establishes it.'
        elif not old and not native and i==3:
            row['selected_issue_assessment']='UNSUPPORTED'
            row['assessment_basis']='A high-risk allegation that the requested stable-sort goal is untested conflates a normative requirement with the task factual assertion.'
        else:
            row['selected_issue_assessment']='PLAUSIBLE_BUT_UNVERIFIED'
            row['assessment_basis']='Stable-sort requirement/premise-check is a legitimate topic, not a demonstrated defect. Critique authority is assessed separately.'
        loss=native and i==1
        result.update(target_actionable_as_defect='NO demonstrated sorting failure; explanation loss becomes actionable after C1',
            critique_defect_assessment='UNSUPPORTED task-premise elevation; some positive observations coexist',
            plan_describes_issue='PARTIAL: usually correct clarification despite defective critique premise',
            plan_relevance='Relevant explanation preservation/clarification' if native else 'Illustrative stability check; does not acquire execution evidence',
            plan_specificity='Explicit requested explanation; generator must retain it' if native else ('EMPTY after protocol salvage' if old else 'Specific test/comment proposal'),
            preservation_observed='NO: explanation removed' if loss else 'NO: missing explanation persists' if native else 'YES within coarse frozen checks; prose limitations remain',
            issue_addressed='NO: explanation not supplied' if native else 'Unverified test added once; no independent result' if not old else 'No meaningful rewrite',
            unrelated_changes='Required explanation removed' if loss else 'Repeated code only' if native else 'Prose reduced and illustrative test added' if not old and i==1 else 'No useful content change',
            output_contract_preserved='NO: explanation requirement, although coarse Python-fence format passes' if native else 'YES on encoded format',
            revision_failure_categories=['GOOD PLAN, BAD GENERATION','BAD ISSUE'] if native else ['BAD ISSUE','NEUTRAL REVISION'],
            manual_review_rationale='Factual task premise is not a normative command to produce a false assertion. Native plans ask to explain the correction, but C1 and later answers are code only. Old score regex misses C0 explanation; newer score records 1→0.5. Structured illustrative tests are not executed evidence.')
    elif task=='BA-009':
        generic='candidate\'s' in row['selected_issue'].lower()
        filler=a.norm(row['selected_issue'])=='therefore i will go with'
        if filler:
            row['selected_issue_assessment']='UNSUPPORTED';row['assessment_basis']='Extraction filler is not a meaningful proposition; useful critique is a separate downstream observation.'
        elif generic:
            row['selected_issue_assessment']='UNKNOWN';row['assessment_basis']='Generic dimension target is not a demonstrated defect; real format/status/evidence gaps are considered at the critique/plan stage.'
        else:
            row['selected_issue_assessment']='DETERMINISTICALLY_GROUNDED';row['assessment_basis']='Explicit established status lacks candidate-bound support; missing observations are stipulated in the task. This grounds a status/evidence gap, not database causation.'
        if old:
            result.update(target_actionable_as_defect='NO for filler/generic target; YES for bounded certainty/JSON gap downstream',
                critique_defect_assessment='PARTLY GROUNDED missing evidence/status; some paraphrases overstate certainty',
                plan_describes_issue='NO usable change survives',plan_relevance='EMPTY after invalid-ID plan salvage',plan_specificity='NONE',
                preservation_observed='Original text retained; original failures remain',issue_addressed='NO',unrelated_changes='No displayed-answer change',
                output_contract_preserved='YES JSON' if native else 'NO JSON before or after',
                revision_failure_categories=['GOOD ISSUE, BAD PLAN']+(['BAD ISSUE'] if filler else []),
                manual_review_rationale='Critique can recognize missing evidence, but all plan changes are discarded after failed protocol repairs. Generic rewrite fallback leaves established native JSON or malformed structured prose unchanged; no valid plan is available to blame generation alone.')
        elif native:
            if i==1:
                categories=['GOOD PLAN, BAD GENERATION'];rationale='Engine-authored qualify/remove instruction is valid and format preserving; C1 keeps established and empty additional_evidence_needed.'
            else:
                categories=['GOOD ISSUE, BAD PLAN'];rationale='Model plan inserts a missing-metrics statement into evidence_used. C2 invents database_metrics_unavailable; certainty becomes likely. C3 repeats it. Plan-origin error and ignored additional-evidence requirement coexist.'
            result.update(target_actionable_as_defect='YES bounded status/evidence-ID failure; generic cycle-3 topic itself unknown',
                critique_defect_assessment='GROUNDED evidence gap; cycle-3 established finding may be stale',
                plan_describes_issue='PARTIAL: recognizes evidence absence',plan_relevance='Valid status qualification' if i==1 else 'INVALID: missing metric is not a declared evidence ID',
                plan_specificity='SPECIFIC',preservation_observed='JSON shape retained; authority boundary violated' if i>=2 else 'JSON shape retained',
                issue_addressed='NO' if i==1 else 'PARTIAL: lower certainty; citation violation remains',
                unrelated_changes='No displayed-answer change' if i==1 else 'Nonexistent citation added' if i==2 else 'No displayed-answer change',
                new_authority_or_citation='ADDED UNKNOWN EVIDENCE ID' if i==2 else 'INHERITED UNKNOWN EVIDENCE ID' if i==3 else 'INHERITED established assertion',
                output_contract_preserved='YES shape; NO declared-ID/missing-evidence semantics' if i>=2 else 'YES shape; NO certainty/missing-evidence semantics',
                revision_failure_categories=categories,manual_review_rationale=rationale)
        else:
            result.update(target_actionable_as_defect='YES actual JSON/evidence limitations; selected dimension remains generic',
                critique_defect_assessment='PLAUSIBLE evidence gap; quoted definitely attribution is ambiguous',
                plan_describes_issue='PARTIAL',plan_relevance='INVALID: requests quantitative observations absent from available evidence',
                plan_specificity='Specific unavailable metric/time interval; no acquisition method',preservation_observed='NO: required JSON never produced',
                issue_addressed='NO: absent metrics remain; causal authority increases',unrelated_changes='Confirmation assertion added' if i==1 else 'Paraphrase/defensive qualification of same unsupported conclusion',
                new_authority_or_citation='ADDED UNSUPPORTED CONFIRMATION' if i==1 else 'INHERITED UNSUPPORTED CONFIRMATION',
                output_contract_preserved='NO JSON',revision_failure_categories=['GOOD ISSUE, BAD PLAN','GOOD PLAN, BAD GENERATION'],
                manual_review_rationale='Metrics are unavailable by task stipulation; requesting insertion cannot acquire them. Required JSON is independently actionable but never repaired. C1 adds evidence-confirms assertion, preserved through C3; branches supply hypotheses, not observations.')
    row.update(result)
    row['revision_failure_categories']=a.packed(result['revision_failure_categories'])
    row['diagnostic_failure_chain']=result['revision_failure_categories'][0]
    return row

def main():
    a.main()
    cycles=a.load(OUT/'CYCLES.json');runs=a.load(OUT/'RUNS.json');trans=readcsv('CANDIDATE_TRANSITIONS.csv')
    findings=readcsv('ISSUE_EQUIVALENCE.csv');calls=readcsv('CALL_AUDIT.csv')
    cache={};seen_targets={};selected_counts=Counter()
    for row in cycles:
        review_cycle(row)
        key=(row['experiment_version'],row['run_id']);t=cache.setdefault(key,a.load(ROOT/row['source_trajectory']))
        start=row['source_step_start'];end=row['source_step_end_exclusive'] or 10**9
        sel=next(s for s in t['steps'] if s['step']==start)['data']['target']
        states=[s['data'] for s in t['steps'] if s['step']<start and s['type']=='cognitive_state'];state=states[-1]
        prior=seen_targets.get((key,sel['target_id']))
        row['issue_novelty']='FIRST_SELECTED_TARGET; novelty/validity unproven' if prior is None else 'REPEATED_TARGET_SAME_TEXT' if a.norm(prior)==a.norm(sel['text']) else 'SAME_TARGET_REWORDED; semantic equivalence unknown'
        seen_targets[(key,sel['target_id'])]=sel['text']
        target=next((w for w in state['open_weaknesses'] if w['id']==sel['target_id']),None)
        if target:
            row['issue_status']=target['status'];row['issue_provenance']=target.get('source_origin','MODEL_OR_ENGINE_FEEDBACK; legacy source field absent')
            row['issue_severity']=target['severity']
        else:
            claim=next((c for c in state['claims_without_evidence'] if c['claim_id']==sel['target_id']),None)
            assumption=next((c for c in state['assumptions'] if c['assumption_id']==sel['target_id']),None)
            row['issue_status']=claim['evidence_status'] if claim else assumption['status'] if assumption else 'NOT APPLICABLE: dimension topic'
            row['issue_provenance']=claim.get('source_origin','CANDIDATE_DERIVED; legacy origin absent') if claim else assumption.get('source_origin','CANDIDATE_OR_MODEL; legacy origin absent') if assumption else 'ENGINE_DIMENSION_TOPIC'
        row['provided_evidence_context']='Task-declared E1/E2/E3 and explicit absence of DB metrics/traces/logs; user-provided, not executed' if row['task_id']=='BA-009' else 'Task requirements/example buggy code plus candidate text; no independently executed runtime evidence'
        rev=next(s for s in t['steps'] if start<=s['step']<end and s['type']=='model_call' and s['data']['request']['purpose']=='revision')
        row['revision_prompt_source_step']=rev['step']
        row['revision_prompt_source_json_path']=f"$.steps[?step={rev['step']}].data.request"
        wire=next(c for c in calls if c['version']==row['experiment_version'] and c['run_id']==row['run_id'] and int(c['source_step'])==rev['step'])
        row['revision_wire_file']=wire['source_wire']
        row['critique_issue_identity_classes']=a.packed([f['identity_class'] for f in findings if f['version']==row['experiment_version'] and f['run_id']==row['run_id'] and int(f['cycle'])==row['cycle_index']])
        selected_counts[row['selected_issue_assessment']]+=1
        tr=next(x for x in trans if x['experiment_version']==row['experiment_version'] and x['run_id']==row['run_id'] and int(x['cycle_index'])==row['cycle_index'])
        classes=tr['classification'].split(';')
        if row['task_id']=='BA-001' and row['experiment_version']=='0.3.5' and row['condition'].endswith('STRUCTURED') and row['cycle_index']==2:
            classes+=['SUBSTANTIVE REGRESSION','FORMAT REGRESSION'];tr['safety_change']='UNKNOWN: malformed partial answer loses required content'
        if row['task_id']=='BA-009' and row['experiment_version']=='0.3.5.1' and row['condition'].endswith('STRUCTURED') and row['cycle_index']==1:classes+=['EPISTEMIC SAFETY REGRESSION']
        if row['task_id']=='BA-009' and row['experiment_version']=='0.3.5.1' and row['condition'].endswith('NATIVE') and row['cycle_index']==2:classes+=['EPISTEMIC SAFETY REGRESSION']
        if row['candidate_content_change'].startswith('CONTENT_CHANGED') and not any('IMPROVEMENT' in x or 'REGRESSION' in x for x in classes):classes+=['UNKNOWN: unmeasured semantic quality']
        tr['classification']=';'.join(dict.fromkeys(classes));tr['manual_review_rationale']=row['manual_review_rationale']
        tr['score_classification']='IMPROVED' if row['score_delta']>0 else 'REGRESSED' if row['score_delta']<0 else 'UNCHANGED_FROZEN_SCORE'
        tr['classification_basis']='Base NEUTRAL CHANGE means unchanged frozen score only; overlapping manual semantic/format/safety dimensions may differ.'
        tr['output_contract_preserved']=row['output_contract_preserved'];tr['revision_failure_categories']=row['revision_failure_categories']
    for f in findings:
        row=next(c for c in cycles if c['experiment_version']==f['version'] and c['run_id']==f['run_id'] and c['cycle_index']==int(f['cycle']))
        f['grounding_research_assessment']=row['critique_defect_assessment']
        f['grounding_note']='Cycle-level contextual review; each occurrence remains a model proposal. Mixed positive and negative findings must be read individually.'
        f['occurrence_grounding'],f['occurrence_grounding_basis']=finding_grounding(f)
    a.csvfile('CYCLE_AUDIT.csv',cycles);a.csvfile('CANDIDATE_TRANSITIONS.csv',trans);a.csvfile('ISSUE_EQUIVALENCE.csv',findings);a.dump('CYCLES.json',cycles)
    stats=a.load(OUT/'SUMMARY.json');stats['selected_issue_assessments']=dict(selected_counts)
    stats['primary_revision_diagnoses']=dict(Counter(c['diagnostic_failure_chain'] for c in cycles))
    stats['selected_target_novelty']=dict(Counter(c['issue_novelty'] for c in cycles))
    stats['finding_occurrence_grounding']=dict(Counter(f['occurrence_grounding'] for f in findings))
    stats['c0_mean_score']=sum(r['c0_score'] for r in runs)/len(runs);stats['final_mean_score']=sum(r['final_score'] for r in runs)/len(runs)
    stats['repair_cost']={'calls':sum(c['protocol_repair']=='True' for c in calls),
        'tokens':sum(int(c['tokens']) for c in calls if c['protocol_repair']=='True'),
        'latency_seconds':sum(float(c['latency_seconds']) for c in calls if c['protocol_repair']=='True')}
    a.dump('SUMMARY.json',stats)
    print(a.packed({k:stats[k] for k in ('selected_issue_assessments','primary_revision_diagnoses','selected_target_novelty','c0_mean_score','final_mean_score','repair_cost')}))

if __name__=='__main__':main()
