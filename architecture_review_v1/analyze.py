"""Historical-only extraction. No Engine imports, evaluator execution or inference."""
import ast
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
PILOTS=('v035_core_regression_pilot','v0351_core_regression_pilot')


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def dump(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def packed(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def csvfile(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def old_region(text):
    # Historical presentation rule, deliberately not current v0352 extraction.
    boundary=0
    for m in re.finditer(r'(?m)^[ \t]*</think>[ \t]*$',text):
        if text[:m.start()].count('```')%2==0:boundary=m.end()
    return text[boundary:].lstrip('\r\n') if boundary else text


def norm(text):return ' '.join(re.findall(r'\w+|[-+<>=]',text.lower()))
def polarity(text):return bool(re.search(r'\b(?:not|never|cannot|fails?)\b',text,re.I))
def jaccard(a,b):
    a,b=set(norm(a).split()),set(norm(b).split())
    return len(a&b)/len(a|b) if a|b else 1


def content_class(before,after):
    if before==after:return 'IDENTICAL_RAW'
    a,b=old_region(before),old_region(after)
    if a==b:return 'IDENTICAL_HISTORICAL_ANSWER_REGION'
    if norm(a)==norm(b):return 'FORMAT_OR_WORDING_ONLY'
    def objects(x):
        result=[]
        for lang,block in re.findall(r'```(json|python)\s*\n(.*?)```',x,re.S|re.I):
            try:result.append((lang.lower(),json.loads(block) if lang.lower()=='json' else ast.dump(ast.parse(block),include_attributes=False)))
            except (ValueError,SyntaxError,RecursionError):return None
        return result or None
    x,y=objects(a),objects(b)
    if x and x==y:return 'SAME_PARSED_CODE_OR_JSON;PROSE_MAY_DIFFER'
    return 'CONTENT_CHANGED;SEMANTIC_EFFECT_REQUIRES_REVIEW'


def issue_assessment(task,mode,target,critique,incoming,external_score):
    """Conservative human-review rules for the limited frozen tasks; research only."""
    text=target.get('text','');kind=target.get('target_type','')
    if norm(text)=='therefore i will go with':
        return 'UNSUPPORTED','Extraction filler is not a substantive claim or repair objective.'
    if kind=='COMPONENT':
        return 'UNKNOWN','Generic dimension target, not a demonstrated defect.'
    if task=='BA-009':
        return 'DETERMINISTICALLY_GROUNDED','Provided evidence explicitly lacks causal measurements; recognized status/format gaps are observable. Root cause remains unknown.'
    if task=='BA-008':
        return 'UNSUPPORTED','Task factual premise is used as an assumption/yardstick without independent support; no scoped external artifact exists.'
    if task=='BA-001' and external_score==1 and kind=='WEAKNESS':
        return 'CONTRADICTED_BY_AVAILABLE_EVIDENCE','Claimed conversion/completeness defect conflicts with frozen encoded numeric checks; does not certify every format nuance.'
    if task=='BA-002' and kind=='WEAKNESS' and re.search(r'empty|zero|negative|larger|oversiz',text,re.I):
        return 'CONTRADICTED_BY_AVAILABLE_EVIDENCE','Frozen passing checks include these inputs; validity outside that coverage remains unknown.'
    return 'PLAUSIBLE_BUT_UNVERIFIED','Requirement/claim merits checking, but selected topic is not itself proof of a defect.'


def main():
    cycles=[];transitions=[];candidates=[];runs=[];calls=[];issues=[];sources={};all_trials=[]
    for pilot in PILOTS:
        for p in sorted((ROOT/pilot/'trials').glob('*.json')):
            r=load(p);all_trials.append(r)
            sources[p.relative_to(ROOT).as_posix()]=sha(p)
            if not r.get('end'):continue
            tp=ROOT/pilot/'trajectories'/r['end']['trajectory_file'];ep=ROOT/pilot/'evaluations'/p.name
            t,ev=load(tp),load(ep);sources[tp.relative_to(ROOT).as_posix()]=sha(tp);sources[ep.relative_to(ROOT).as_posix()]=sha(ep)
            version='0.3.5.1' if pilot.startswith('v0351') else '0.3.5'
            steps=t['steps']; selections=[s for s in steps if s['type']=='operator_selection']
            cm={c['candidate_id']:c for c in t['candidates']};scores=ev['candidates'];gates={g['candidate_id']:g for g in t['quality_gate_decisions']}
            verifications={v['candidate_id']:v for v in t['verification']}
            model_steps=[s for s in steps if s['type']=='model_call']
            assert len(model_steps)==len(r['calls'])==r['cost']['calls']
            for ms,c in zip(model_steps,r['calls']):assert ms['data']['request']['purpose']==c['purpose']
            run={'version':version,'pilot':pilot,'run_id':r['run_id'],'task':r['task_id'],'condition':r['condition'],
                 'cycles':r['end']['iterations'],'candidate_count':len(cm),'calls':r['cost']['calls'],'tokens':r['cost']['total_tokens'],
                 'wall_seconds':r['cost']['wall_ms']/1000,'c0_score':scores['C0']['score'],'final_score':ev['final']['score'],
                 'final_pass':ev['final']['passed'],'returned':r['end']['returned_candidate_id'],'gate':r['end']['quality_gate'],
                 'stop':r['end']['termination'],'rollback_count':len(t['rollback_events']),
                 'repairs':sum(c['protocol_repair_call'] for c in r['calls']),'new_executed_evidence':len(t['verifier_evidence']),
                 'trajectory':tp.relative_to(ROOT).as_posix(),'evaluation':ep.relative_to(ROOT).as_posix()}
            runs.append(run);previous_issue={};previous_texts=[]
            for c in t['candidates']:
                cid=c['candidate_id'];e=scores.get(cid)
                assert e is not None,'Missing candidate evaluation: '+r['run_id']+' '+cid
                js=[j for j in (*t['judgments'],*t['adversarial_judgments']) if j['candidate_id']==cid]
                candidates.append({'version':version,'run_id':r['run_id'],'task':r['task_id'],'condition':r['condition'],
                    'candidate_id':cid,'parent':c['parent_candidate_id'],'external_score':e['score'],'external_pass':e['passed'],
                    'external_format_ok':e['format_ok'],'internal_gate':gates[cid]['decision'],
                    'model_verifier_pass':verifications[cid]['passed'],'model_verifier_score':verifications[cid]['score'],
                    'judge_verdicts':packed([j['verdict'] for j in js]),
                    'judge_mean_score':statistics.mean(v['score'] for j in js for v in j['dimensions'].values()),
                    'judge_mean_confidence':statistics.mean(v['confidence'] for j in js for v in j['dimensions'].values()),
                    'raw_chars':len(c['content']),'historical_region_chars':len(old_region(c['content'])),
                    'selected_final':cid==r['end']['returned_candidate_id'],'source_trajectory':run['trajectory'],
                    'source_json_path':f'$.candidates[?candidate_id={cid}]','source_evaluation':run['evaluation']})
            assert len(selections)==run['cycles']
            boundaries=[s['step'] for s in selections]+[10**9]
            for cycle,sel in enumerate(selections,1):
                start,end=boundaries[cycle-1],boundaries[cycle]
                segment=[s for s in steps if start<=s['step']<end]
                before_states=[s['data'] for s in steps if s['step']<start and s['type']=='cognitive_state']
                incoming=before_states[-1]['current_candidate_id']
                outgoing_steps=[s for s in segment if s['type']=='candidate'];assert len(outgoing_steps)==1
                outgoing=outgoing_steps[0]['data']['candidate_id'];child=cm[outgoing];assert child['parent_candidate_id']==incoming
                critique=next(s['data'] for s in segment if s['type']=='critique')
                plan=next(s['data'] for s in segment if s['type']=='revision_plan')
                question=next(s['data'] for s in segment if s['type']=='question')
                initial_outcome=next(s['data'] for s in segment if s['type']=='operator_outcome')
                enriched=[s['data']['after'] for s in segment if s['type']=='operator_outcome_enriched']
                outcome=enriched[-1] if enriched else initial_outcome
                rolled=[s['data'] for s in segment if s['type']=='candidate_rollback']
                effective=rolled[-1]['to_candidate'] if rolled else outgoing
                call_pairs=[(ms,c) for ms,c in zip(model_steps,r['calls']) if start<=ms['step']<end]
                target=sel['data']['target'];assessment,why=issue_assessment(r['task_id'],r['condition'],target,critique,
                    cm[incoming],scores[incoming]['score'])
                for w in critique['findings']:
                    wid=w['id'];txt=w['description'];prior=previous_issue.get(wid)
                    if prior is not None:
                        identity='REPEATED' if norm(prior)==norm(txt) else 'REFORMULATED' if polarity(prior)==polarity(txt) and jaccard(prior,txt)>=.72 else 'UNKNOWN'
                    else:
                        match=next((x for x in previous_texts if polarity(x)==polarity(txt) and jaccard(x,txt)>=.72),None)
                        identity='REFORMULATED' if match else 'DISTINCT_LEXICAL_PROPOSAL'
                    issues.append({'version':version,'run_id':r['run_id'],'cycle':cycle,'operator':sel['data']['operator'],
                        'issue_id':wid,'description':txt,'severity':w['severity'],'status':w['status'],
                        'identity_class':identity,'jaccard_to_prior_same_id':jaccard(prior,txt) if prior is not None else None,
                        'provenance':'MODEL_CRITIQUE','equivalence_is_semantic_proof':False,'source_trajectory':run['trajectory']})
                    previous_issue[wid]=txt;previous_texts.append(txt)
                cg=scores[outgoing]['score']-scores[incoming]['score'];cc=content_class(cm[incoming]['content'],child['content'])
                classes=['SUBSTANTIVE IMPROVEMENT'] if cg>0 else ['SUBSTANTIVE REGRESSION'] if cg<0 else ['NEUTRAL CHANGE']
                if cc=='FORMAT_OR_WORDING_ONLY':classes.append('FORMAT-ONLY CHANGE')
                safety='UNKNOWN'
                if version=='0.3.5.1' and r['task_id']=='BA-009' and r['condition']=='FULL_END_NATIVE' and cycle==2:
                    classes.append('EPISTEMIC SAFETY IMPROVEMENT');safety='established→likely; also adds nonexistent evidence ID'
                if version=='0.3.5.1' and r['task_id']=='BA-009' and r['condition']=='FULL_END_STRUCTURED' and cycle==1:
                    safety='REGRESSION: unsupported evidence-confirms assertion added'
                if version=='0.3.5' and r['task_id']=='BA-008' and r['condition']=='FULL_END_NATIVE' and cycle==1:
                    classes.append('SUBSTANTIVE REGRESSION');safety='explanation lost; frozen regex hides qualitative regression'
                progress=next((s['data'] for s in segment if s['type']=='cycle_progress'),None)
                term=[s['data'] for s in segment if s['type']=='termination_decision']
                diagnostic='INSUFFICIENT EVIDENCE'
                if assessment in ('UNSUPPORTED','CONTRADICTED_BY_AVAILABLE_EVIDENCE'):diagnostic='BAD ISSUE'
                elif r['task_id']=='BA-009':
                    diagnostic='GOOD ISSUE, BAD PLAN' if any(re.search(r'add.*(?:metrics|evidence_used)',c['action'],re.I) for c in plan['changes']) else 'GOOD PLAN, BAD GENERATION'
                if cc.startswith('IDENTICAL') and cg==0 and diagnostic=='INSUFFICIENT EVIDENCE':diagnostic='NEUTRAL REVISION'
                row={'experiment_version':version,'task_id':r['task_id'],'condition':r['condition'],'trial':r['trial'],
                    'run_id':r['run_id'],'cycle_index':cycle,'incoming_candidate_id':incoming,
                    'incoming_external_score':scores[incoming]['score'],'selected_operator':sel['data']['operator'],
                    'operator_family':outcome['family'],'selected_issue_id':target['target_id'],'selected_issue':target['text'],
                    'issue_provenance':'CANDIDATE_DERIVED_TOPIC' if target['target_type'] in ('CLAIM','EVIDENCE_GAP') else 'MODEL_OR_DIMENSION_TARGET',
                    'issue_severity':next((w['severity'] for w in before_states[-1]['open_weaknesses'] if w['id']==target['target_id']),None),
                    'selected_issue_assessment':assessment,'assessment_basis':why,'internal_information_gain':packed(outcome['information_gain']),
                    'internal_information_gain_before_branch':packed(initial_outcome['information_gain']),
                    'evidence_available':packed([e for e in t['verifier_evidence'] if e['candidate_id']==incoming]),
                    'critique':packed(critique),'revision_plan':packed(plan),'outgoing_candidate_id':outgoing,
                    'outgoing_external_score':scores[outgoing]['score'],'score_delta':cg,'candidate_content_change':cc,
                    'verification':packed(verifications[outgoing]),'judge_outcomes':packed([j for j in (*t['judgments'],*t['adversarial_judgments']) if j['candidate_id']==outgoing]),
                    'quality_gate':gates[outgoing]['decision'],'quality_gate_reasons':packed(gates[outgoing]['reasons']),
                    'rollback':packed(rolled),'effective_candidate_id':effective,'effective_external_score':scores[effective]['score'],
                    'termination_decisions':packed(term),'reported_progress':packed(progress) if progress else None,
                    'diagnostic_failure_chain':diagnostic,'safety_change':safety,'model_calls':len(call_pairs),
                    'tokens':sum(c['input_tokens']+c['output_tokens'] for _,c in call_pairs),
                    'provider_latency_seconds':sum(c['latency_ms'] for _,c in call_pairs)/1000,
                    'source_trajectory':run['trajectory'],'source_step_start':start,'source_step_end_exclusive':None if end==10**9 else end,
                    'source_evaluation':run['evaluation'],'retrospective_evaluation':False}
                cycles.append(row)
                transitions.append({k:row[k] for k in ('experiment_version','task_id','condition','trial','run_id','cycle_index',
                    'incoming_candidate_id','outgoing_candidate_id','incoming_external_score','outgoing_external_score','score_delta',
                    'candidate_content_change','quality_gate','effective_candidate_id','effective_external_score','safety_change','source_trajectory','source_evaluation')}
                    |{'classification':';'.join(classes),'lineage_parent':child['parent_candidate_id'],
                      'outgoing_raw_chars':len(child['content']),'outgoing_historical_region_chars':len(old_region(child['content']))})
            for ms,c in zip(model_steps,r['calls']):
                cycle=next((i+1 for i in range(len(selections)) if boundaries[i]<=ms['step']<boundaries[i+1]),0)
                category={'initial_candidate':'initial_generation','revision':'revision_generation','revision_plan':'revision_planning',
                    'critique':'operator_critique','judgment':'primary_judging','adversarial_judgment':'adversarial_judging',
                    'comparison':'candidate_comparison','verification':'model_verification','adversarial_tests':'adversarial_test_generation',
                    'branch_generation':'branch_activity','branch_evaluation':'branch_activity','synthesis':'branch_activity'}.get(c['purpose'],'other')
                calls.append({'version':version,'run_id':r['run_id'],'cycle':cycle,'seq':c['seq'],'purpose':c['purpose'],
                    'category':category,'protocol_repair':c['protocol_repair_call'],'tokens':c['input_tokens']+c['output_tokens'],
                    'input_tokens':c['input_tokens'],'output_tokens':c['output_tokens'],'latency_seconds':c['latency_ms']/1000,
                    'source_wire':str(Path(pilot)/c['wire_file']),'source_trajectory':run['trajectory'],'source_step':ms['step']})
    assert len(runs)==16 and len(cycles)==44 and len(transitions)==44 and len(candidates)==60
    assert len(calls)==466 and sum(c['tokens'] for c in calls)==1140074
    assert sum(c['model_calls'] for c in cycles)+sum(c['cycle']==0 for c in calls)==len(calls)
    csvfile('CYCLE_AUDIT.csv',cycles);csvfile('CANDIDATE_TRANSITIONS.csv',transitions);csvfile('CANDIDATE_CALIBRATION.csv',candidates)
    csvfile('CALL_AUDIT.csv',calls);csvfile('ISSUE_EQUIVALENCE.csv',issues)
    dump('RUNS.json',runs);dump('CYCLES.json',cycles);dump('CANDIDATES.json',candidates)
    dump('SOURCE_RECORD_HASHES.json',sources)
    stats={'full_end_runs':len(runs),'cycles':len(cycles),'candidates':len(candidates),'transitions':len(transitions),
        'model_calls':len(calls),'tokens':sum(c['tokens'] for c in calls),'run_wall_seconds':sum(r['wall_seconds'] for r in runs),
        'pre_cycle_calls':sum(c['cycle']==0 for c in calls),'cycle_calls':sum(c['cycle']>0 for c in calls),
        'external_transition_improvements':sum(t['score_delta']>0 for t in transitions),
        'external_transition_regressions':sum(t['score_delta']<0 for t in transitions),
        'external_transition_neutral':sum(t['score_delta']==0 for t in transitions),
        'final_improvements_over_c0':sum(r['final_score']>r['c0_score'] for r in runs),
        'final_regressions_over_c0':sum(r['final_score']<r['c0_score'] for r in runs),
        'c0_perfect_score_runs':sum(r['c0_score']==1 for r in runs),
        'new_executed_evidence':sum(r['new_executed_evidence'] for r in runs),'rollback_events':sum(r['rollback_count'] for r in runs),
        'repairs':sum(r['repairs'] for r in runs),'issue_occurrences':len(issues),
        'issue_identity_classes':dict(Counter(i['identity_class'] for i in issues)),
        'selected_issue_assessments':dict(Counter(c['selected_issue_assessment'] for c in cycles)),
        'content_change_classes':dict(Counter(c['candidate_content_change'] for c in cycles)),
        'gate_by_external_pass':dict(Counter(c['internal_gate']+'/'+str(c['external_pass']) for c in candidates)),
        'purpose_costs':{},'operator_costs':{},'counterfactuals':[]}
    for category in sorted({c['category'] for c in calls}):
        group=[c for c in calls if c['category']==category]
        stats['purpose_costs'][category]={'calls':len(group),'tokens':sum(c['tokens'] for c in group),
            'provider_latency_seconds':sum(c['latency_seconds'] for c in group)}
    for operator in sorted({c['selected_operator'] for c in cycles}):
        group=[c for c in cycles if c['selected_operator']==operator]
        stats['operator_costs'][operator]={'activations':len(group),'family':group[0]['operator_family'],
            'associated_cycle_calls':sum(c['model_calls'] for c in group),'associated_cycle_tokens':sum(c['tokens'] for c in group),
            'positive_external_transitions':sum(c['score_delta']>0 for c in group),'negative_external_transitions':sum(c['score_delta']<0 for c in group),
            'internal_gain_levels':dict(Counter(json.loads(c['internal_information_gain'])['level'] for c in group))}
    for r in runs:
        group=[c for c in candidates if c['version']==r['version'] and c['run_id']==r['run_id']]
        first=next(c for c in cycles if c['experiment_version']==r['version'] and c['run_id']==r['run_id'] and c['cycle_index']==1)
        best=max(group,key=lambda c:(c['external_score'],c['candidate_id']=='C0'))
        stats['counterfactuals'].append({'version':r['version'],'run_id':r['run_id'],'actual_final_score':r['final_score'],
            'A_c0_score':r['c0_score'],'B_oracle_score':best['external_score'],'B_candidate':best['candidate_id'],
            'C_after_first_cycle_effective_id':first['effective_candidate_id'],'C_after_first_cycle_score':first['effective_external_score'],
            'D_status':'PARTIALLY RECONSTRUCTABLE','E_status':'PARTIALLY RECONSTRUCTABLE',
            'A_status':'OBSERVABLE FROM RECORDED ARTIFACTS; cost of changed policy not observed',
            'B_status':'RETROSPECTIVE ORACLE UPPER BOUND; unavailable at runtime',
            'C_status':'OBSERVABLE STATE SCORE; final reconciliation/safety after early stop only partially reconstructable'})
    dump('SUMMARY.json',stats)
    print(packed({k:v for k,v in stats.items() if k not in ('operator_costs','purpose_costs','counterfactuals')}))


if __name__=='__main__':main()
