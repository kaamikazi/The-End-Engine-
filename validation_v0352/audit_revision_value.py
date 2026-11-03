"""Read frozen trajectories/evaluations. Never run or rescore a benchmark."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
NOTES = {
 ('BA-001','FULL_END_NATIVE'): ('Correct fenced temperature array.', 'A low finding restates correct conversions; not a demonstrated defect.',
  'No new facts; same correct array after one revision. C0 is returned.',
  ['ISSUE-IDENTIFICATION FAILURE','TERMINATION / COST FAILURE']),
 ('BA-001','FULL_END_STRUCTURED'): ('Correct fenced temperature array.', 'False critical completeness/misassignment allegations; verifier falsely disputes correct values.',
  'Arrays are identical or whitespace variants. Verifier/issue wording churn resets progress.',
  ['MODEL FAILURE','ISSUE-IDENTIFICATION FAILURE','JUDGE FAILURE','TERMINATION / COST FAILURE']),
 ('BA-002','FULL_END_NATIVE'): ('Correct size/type guard and full chunk loop, plus explanation.', 'False missing-guard/original-code attribution; later all-case testing is a plausible uncertainty.',
  'The corrected function remains unchanged. New low findings and in-band claim churn supply opinions, not checks.',
  ['ISSUE-IDENTIFICATION FAILURE','JUDGE FAILURE','TERMINATION / COST FAILURE','EXTERNAL EVALUATOR LIMITATION']),
 ('BA-002','FULL_END_STRUCTURED'): ('Passing chunk function with size<=0 guard; type/comment gaps outside the rubric.', 'Verifier falsely alleges empty/single/oversized failures; low critiques describe supported claims.',
  'All candidate texts are identical. The real untested type/comment issues are not repaired.',
  ['ISSUE-IDENTIFICATION FAILURE','JUDGE FAILURE','TERMINATION / COST FAILURE','EXTERNAL EVALUATOR LIMITATION']),
 ('BA-008','FULL_END_NATIVE'): ('Passing stable-sort function with explicit false-premise correction and explanation.', 'False task premise becomes authority in verifier/critique; selected high assumption has no independent support.',
  'The first revision removes the requested explanation, scores 0.5 instead of 1, and is retained. Comparisons miss the loss.',
  ['ISSUE-IDENTIFICATION FAILURE','REVISION-PLANNING FAILURE','REVISION-GENERATION FAILURE','JUDGE FAILURE','QUALITYGATE FAILURE','TERMINATION / COST FAILURE']),
 ('BA-008','FULL_END_STRUCTURED'): ('Passing stable-sort function with verbose/partly false prose.', 'False-premise evidence/assumption concerns; no executed check supports them.',
  'First revision trims prose/adds an illustrative test; later answers are identical. False list.sort commentary remains.',
  ['ISSUE-IDENTIFICATION FAILURE','REVISION-GENERATION FAILURE','JUDGE FAILURE','TERMINATION / COST FAILURE','EXTERNAL EVALUATOR LIMITATION']),
 ('BA-009','FULL_END_NATIVE'): ('JSON: established cause, E2 alone, no additional evidence requested.', 'Real missing-evidence/status concern; Engine detects established. Subsequent plan wrongly adds an evidence-ID string.',
  'Second revision reduces certainty to likely but fabricates database_metrics_unavailable; third repeats it. No new evidence enters.',
  ['REVISION-PLANNING FAILURE','REVISION-GENERATION FAILURE','JUDGE FAILURE','QUALITYGATE FAILURE','TERMINATION / COST FAILURE']),
 ('BA-009','FULL_END_STRUCTURED'): ('Unformatted prose favoring a database/deployment cause while admitting missing metrics.', 'Real format/evidence gaps mixed with excessive demands for unavailable query specifics.',
  'Revisions add unsupported evidence-confirms wording. Branches generate cache/payment hypotheses, not observations; JSON stays missing.',
  ['REVISION-PLANNING FAILURE','REVISION-GENERATION FAILURE','JUDGE FAILURE','QUALITYGATE FAILURE','TERMINATION / COST FAILURE','EXTERNAL EVALUATOR LIMITATION']),
}


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def state_before(steps, end):
    states = [s['data'] for s in steps if s['step'] < end and s['type']=='cognitive_state']
    return states[-1] if states else {}


def progress_rows(pilot, record, t):
    steps = t['steps']; output = []
    initial = next(s['step'] for s in steps if s['type']=='termination_decision')
    before = state_before(steps, initial); start = initial
    events = [s for s in steps if s['type']=='cycle_progress']
    if not events:
        # v0.3.5 predates this observer; report actual candidate transitions but
        # do not invent a no-progress counter or reset reason.
        events = [{'step':s['step'],'data':{'cycle':c['iteration'],'reasons':None,'no_progress_cycles':None,'blockers':None}}
                  for c in t['candidates'] if c['iteration']>0
                  for s in steps if s['type']=='termination_decision' and
                  s['step']>next(x['step'] for x in steps if x['type']=='candidate' and x['data']['candidate_id']==c['candidate_id'])][:record['end']['iterations']]
        # Select the first decision after each revision independently.
        events = []
        for c in t['candidates'][1:]:
            created = next(x['step'] for x in steps if x['type']=='candidate' and x['data']['candidate_id']==c['candidate_id'])
            decision = next(s for s in steps if s['type']=='termination_decision' and s['step']>created)
            events.append({'step':decision['step'],'data':{'cycle':c['iteration'],'reasons':None,
                          'no_progress_cycles':None,'blockers':None}})
    for event in events:
        after = state_before(steps,event['step'])
        b = before.get('current_candidate_id'); a = after.get('current_candidate_id')
        candidates = {c['candidate_id']:c for c in t['candidates']}
        issues_before = {w['id']:w for w in before.get('open_weaknesses',[])}
        issues_after = {w['id']:w for w in after.get('open_weaknesses',[])}
        segment = [s for s in steps if start < s['step'] <= event['step']]
        reasons = event['data']['reasons']; cycle=event['data']['cycle']
        task=record['task_id'];mode=record['condition'];kind='UNKNOWN';value='no observed substantive gain'
        if pilot=='v0351_core_regression_pilot':
            if task=='BA-008' and mode=='FULL_END_NATIVE' and cycle==1:
                kind='SUBSTANTIVE';value='harmful: explanation removed, external score 1→0.5'
            elif task=='BA-009' and mode=='FULL_END_NATIVE' and cycle==2:
                kind='SUBSTANTIVE';value='mixed: lower status, newly fabricated citation, score unchanged'
            elif task=='BA-009' and mode=='FULL_END_STRUCTURED' and cycle==1:
                kind='SUBSTANTIVE';value='harmful: unsupported confirmation added, score unchanged'
            elif reasons:
                kind='WORDING_ONLY' if reasons==['candidate_content'] else 'ADMINISTRATIVE / BOOKKEEPING'
                value='model-state/wording change, no independently acquired evidence or score improvement'
        row={'pilot':pilot,'run_id':record['run_id'],'cycle':cycle,'candidate_before':b,'candidate_after':a,
             'raw_candidate_changed':bool(a and b and candidates[a]['content']!=candidates[b]['content']),
             'issue_creation':sorted(set(issues_after)-set(issues_before)),
             'issues_no_longer_open':sorted(set(issues_before)-set(issues_after)),
             'status_transition_events':[s['data'] for s in segment if s['type']=='weakness_status_change'],
             'grounded_issue_annotations':[s['data'] for s in segment if s['type']=='judge_grounding'],
             'claim_support_events':[s['data'] for s in segment if s['type'] in ('claim_status_change','claim_validation')],
             'evidence_events':[s['data'] for s in segment if s['type']=='verifier_evidence'],
             'verifier_events':[s['data'] for s in segment if s['type']=='verification'],
             'quality_gate_events':[s['data'] for s in segment if s['type']=='quality_gate'],
             'branch_events':[s['data'] for s in segment if s['type'] in ('branch_created','branch_status_change','synthesis_plan')],
             'rollback_events':[s['data'] for s in segment if s['type']=='candidate_rollback'],
             'reported_progress_reasons':reasons,'reported_no_progress_counter':event['data']['no_progress_cycles'],
             'reported_reset':event['data']['no_progress_cycles']==0 if reasons is not None else None,
             'reported_mandatory_overrides':event['data']['blockers'],'diagnostic_classification':kind,
             'diagnostic_value':value,'limitation':'Classification is diagnostic, not a changed historical correctness/Engine label; absent reset data stays unknown.'}
        output.append(row);before=after;start=event['step']
    return output


def main():
    runs=[];cycles=[]
    for pilot in ('v035_core_regression_pilot','v0351_core_regression_pilot'):
        for path in sorted((ROOT/pilot/'trials').glob('*.json')):
            r=load(path)
            if not r.get('end'):continue
            t=load(ROOT/pilot/'trajectories'/r['end']['trajectory_file'])
            cycles.extend(progress_rows(pilot,r,t))
            if pilot!='v0351_core_regression_pilot':continue
            ev=load(ROOT/pilot/'evaluations'/path.name)
            purposes=Counter(c['purpose'] for c in r['calls']);note=NOTES[(r['task_id'],r['condition'])]
            runs.append({'run_id':r['run_id'],'trajectory':r['end']['trajectory_file'],'c0':note[0],
                'issue_diagnosis':note[1],'revision_diagnosis':note[2],'failure_categories':note[3],
                'operator_sequence':[x['operator'] for x in t['critiques']],
                'selected_targets':[q['target'] for q in t['questions']],
                'plans':t['revision_plans'],'comparisons':t['pairwise_comparisons'],
                'gate_decisions':t['quality_gate_decisions'],'rollback':t['rollback_events'],
                'c0_score':ev['candidates']['C0']['score'],'final_score':ev['final']['score'],
                'candidate_scores':{k:v['score'] for k,v in ev['candidates'].items()},
                'calls':r['cost']['calls'],'tokens':r['cost']['total_tokens'],'wall_seconds':r['cost']['wall_ms']/1000,
                'stage_calls':dict(purposes),'repair_calls':sum(c['protocol_repair_call'] for c in r['calls']),
                'cycles':r['end']['iterations'],'returned_candidate':r['end']['returned_candidate_id'],
                'new_executed_evidence':len(t['verifier_evidence']),
                'c0_preservation_score_equal_or_better':ev['candidates']['C0']['score']>=ev['final']['score']})
    assert len(runs)==8 and sum(r['cycles'] for r in runs)==22
    assert len([c for c in cycles if c['pilot']=='v0351_core_regression_pilot'])==22
    (OUT/'revision-value-data.json').write_text(json.dumps(runs,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (OUT/'progress-attribution.json').write_text(json.dumps(cycles,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    lines=['# Revision-value audit for v0.3.5.2','',
       'Read-only investigation dated 2026-10-09. Frozen v0.3.5.1 trajectories and external evaluations are the evidence; nothing is rescored or relabelled in the historical directories.',
       'The server drifted from Ollama 0.35.1 to 0.40.0 at an unknown time. Four tasks/one trial, same-model judging, frozen rubric gaps and raw-region ambiguity limit causal/general conclusions.',
       '', '## Finding','',
       'The dominant observed chain is additional model opinions → more issues/plans/judgments → similar or worse answers. Zero of eight final scores improve, seven are neutral and one regresses. No executed external evidence is acquired in any run. Native BA-009 does make a useful status downgrade, but introduces a false citation; the score stays unchanged.',
       'These are structural revision/assessment problems that the integrity patch cannot make a generator or comparison model solve. Operator selection follows the supplied concern state; these traces do not isolate intrinsic ranking failure from poisoned issue inputs. More cycles are not presumed beneficial.',
       '', '## Per-run frozen costs and outcomes','',
       '| Run | C0 → final | Revisions | Calls | Tokens | Judge / critique / verification / repair calls | C0 preservation |',
       '|---|---|---:|---:|---:|---|---|']
    for r in runs:
        p=r['stage_calls'];judge=sum(p.get(k,0) for k in ('judgment','adversarial_judgment','adversarial_tests','comparison'))
        lines.append(f"| {r['run_id']} | {r['c0_score']} → {r['final_score']} | {r['cycles']} | {r['calls']} | {r['tokens']:,} | {judge} / {p.get('critique',0)} / {p.get('verification',0)} / {r['repair_calls']} | equal or better by score |")
    for r in runs:
        lines+=['', '## '+r['run_id'], '',
          '1. C0: '+r['c0'], '2. Selected concerns: '+r['issue_diagnosis'],
          '3. Real/plausible/unsupported/false distinction: '+r['issue_diagnosis'],
          '4. Operators: '+' → '.join(r['operator_sequence'])+'.',
          '5. New information: model proposals only; zero newly executed evidence artifacts.',
          '6. Requested revisions: '+ '; '.join(ch['action'] for p in r['plans'] for ch in p['changes'])+'.',
          '7. Response to selected issue: '+r['revision_diagnosis'],
          '8. New defects/lost requirements: '+r['revision_diagnosis'],
          '9. Frozen progression: '+json.dumps(r['candidate_scores'])+'; actual returned score '+str(r['final_score'])+'.',
          '10. Replacement/regression: '+('passing C0 replaced with worse C1; explanation lost.' if r['final_score']<r['c0_score'] else 'no measured final-score regression; qualitative defects are not ruled out.'),
          '11. QualityGate: '+ '; '.join(g['candidate_id']+'='+g['decision'] for g in r['gate_decisions'])+'. Model comparisons often prefer changes without justified gains; no gate verifies independent world truth.',
          '12. Rollback: '+str(len(r['rollback']))+'; no rollback protects the lost BA-008 native explanation.',
          f"13. Cost to final: {r['calls']} calls, {r['tokens']:,} tokens, {r['wall_seconds']:.3f}s.",
          '14. Preserving C0 scores equally or better. This is a saved-output comparison, not an executed alternative. Preserving an unsupported established answer is not necessarily safer.',
          '15. Evidence acquisition: none. Useful questions/status correction do not supply new measurements or trusted receipts.',
          '', 'Overlapping failure categories: '+', '.join(r['failure_categories'])+'. Operator-selection failure remains unisolated rather than asserted.',
          f"Frozen source: `v0351_core_regression_pilot/trajectories/{r['trajectory']}`. Exact targets/plans/comparisons are copied into `validation_v0352/revision-value-data.json`."]
    lines+=['', '## Progress attribution','',
      'Every one of the 22 v0.3.5.1 cycles is listed below. `validation_v0352/progress-attribution.json` also covers 22 older v0.3.5 cycles (44 total); old no-progress counters/reasons were not recorded and stay unknown. Data includes before/after candidate, issue creation/closure, grounding, claim/evidence/verifier/gate changes, branch/rollback events and actual reset/blocker fields.',
      'SUBSTANTIVE describes a meaningful content change, not guaranteed improvement. ADMINISTRATIVE / BOOKKEEPING covers opinions/identities/support records without new evidence. WORDING_ONLY identifies unchanged propositions with presentation changes. UNKNOWN is used for absent/no-reset data and unestablished semantic effects.',
      '', '| Run / cycle | Original reported reasons | Counter | Diagnostic classification | Interpretation |',
      '|---|---|---:|---|---|']
    for c in cycles:
        if c['pilot']=='v0351_core_regression_pilot':
            lines.append(f"| {c['run_id']} / {c['cycle']} | {', '.join(c['reported_progress_reasons']) or 'none'} | {c['reported_no_progress_counter']} | {c['diagnostic_classification']} | {c['diagnostic_value']} |")
    lines+=['', '## Cost interpretation and architectural implications','',
      'The eight FULL_END runs consume 233 calls and 574,138 tokens over 22 cycles; all four-task completed trials total 237 calls/583,933 tokens. Judge/verification loops repeatedly revisit unchanged or externally neutral candidates. Repairs fix protocol structure, not substantive truth. BA-008 native damages an already passing answer; BA-009 plans manufacture authority rather than acquire evidence. The historical absence of NO_PROGRESS stops alone is not proof of a detector defect: cap timing and mandatory assumptions also explain continuation.',
      'The patch only removes concrete invalid progress signals: advisory issue creation, unverified claim churn, and unvalidated model-verifier opinion changes. It retains authoritative issue resolution, registered executed checks, candidate content, gate/contradiction changes and mandatory-action protection. No external scores enter production. There is no measured saving estimate, no counterfactual inference, and no revision architecture rebuild.',
      'Recommendation after integrity validation: **B. RECONSIDER REVISION ARCHITECTURE BEFORE MORE INFERENCE.** The observed loop cannot reliably select a real correctable issue, plan a valid correction, preserve requirements, or compare resulting answers. Integrity tests can constrain authority; they cannot demonstrate useful revision ability. Future design investigation should distinguish evidence acquisition and constraint preservation from additional opinions before authorizing more inference.']
    (ROOT/'REVISION_VALUE_AUDIT_v0352.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'runs':len(runs),'historical_cycles':len(cycles),'model_inference':0,'rescored_results':0}))


if __name__=='__main__':
    main()
