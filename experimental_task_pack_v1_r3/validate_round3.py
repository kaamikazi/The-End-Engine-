"""Preserved offline attempts and every R2/new fixture and transition observation."""
import csv,json,sys
from collections import Counter
from pathlib import Path
from experimental_task_pack_v1_r3.research_round3 import suite,save
from experimental_task_pack_v1_r3.evaluators import evaluate_answer,compare_candidates
OUT=Path(__file__).resolve().parent;VAL=OUT/'validation'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    number=len(list(VAL.glob('r3-attempt-*.json')))+1;tests=suite('experimental_task_pack_v1_r3/tests',f'r3-attempt-{number:02d}')
    old=OUT.parent/'experimental_task_pack_v1_r2';old_labels={load(p)['fixture_id']:load(p) for p in (old/'fixtures').rglob('*.json')}
    rows=[];prior_rows=[];bad=[]
    for p in sorted((OUT/'fixtures').rglob('*.json')):
        f=load(p);e=f['expected'];r=evaluate_answer(f['task_id'],f['candidate_content'],**f.get('evaluation_options',{}));errors=[]
        for k in ('overall_pass','task_success'):
            if r[k]!=e[k]:errors.append(k)
        if r['safety']['outcome']!=e['safety_outcome']:errors.append('safety_outcome')
        for k,w in e['dimensions'].items():
            if any(r['dimensions'][k][x]!=w[x] for x in ('status','score')):errors.append(k)
        for key,actual in [('required_contract_errors',r['dimensions']['output_contract_compliance']['violations']),('required_safety_violations',r['safety']['violations']),('required_review_reasons',r['safety']['review_reasons'])]:
            if not set(e.get(key,[]))<=set(actual):errors.append(key)
        row={'fixture_id':f['fixture_id'],'expected':e,'actual':r,'matches':not errors};rows.append(row)
        if errors:bad.append({'fixture_id':f['fixture_id'],'fields':errors})
        if f['fixture_id'] in old_labels:
            prior=old_labels[f['fixture_id']];prior_rows.append({'fixture_id':f['fixture_id'],'r2_expectation':prior['expected'],'r3_observation':r,
                'expectation_changed':e!=prior['expected'],'candidate_content_changed':f['candidate_content']!=prior['candidate_content'],
                'outcome_changed':r['overall_pass'] is not prior['expected']['overall_pass'],
                'reason':'R2 expected numeric/tri-state labels retained; per-proposition diagnostics expanded',
                'contract_justification':'Task/evidence contract unchanged; scoped safety correction preserves prior accepted/rejected/review cases',
                'independent_recheck_status':'PENDING'})
    pairs=[];pair_bad=[]
    for p in sorted((OUT/'paired_fixtures').glob('*.json')):
        f=load(p);r=compare_candidates(f['task_id'],f['c0_content'],f['final_content']);errors=[k for k,v in f['expected_transition_fields'].items() if r[k]!=v]
        pairs.append({'pair_id':f['pair_id'],'expected':f['expected_transition_fields'],'actual':r,'matches':not errors})
        if errors:pair_bad.append({'pair_id':f['pair_id'],'fields':errors})
    save('R2_FIXTURE_REVALIDATION.json',prior_rows);save('PAIRWISE_RESULTS.json',pairs)
    with (VAL/'R2_FIXTURE_REVALIDATION.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['fixture_id','expectation_changed','candidate_content_changed','r2_overall','r3_overall','reason','contract_justification','independent_recheck_status']);w.writeheader()
        for r in prior_rows:w.writerow({k:r[k] for k in ('fixture_id','expectation_changed','candidate_content_changed','reason','contract_justification','independent_recheck_status')}|{'r2_overall':r['r2_expectation']['overall_pass'],'r3_overall':r['r3_observation']['overall_pass']})
    def counts(group):return dict(Counter('PASS' if x['actual']['overall_pass'] is True else 'FAIL' if x['actual']['overall_pass'] is False else 'REVIEW' for x in group))
    metrics={'false_acceptance':sum(x['expected']['overall_pass'] is not True and x['actual']['overall_pass'] is True for x in rows),
        'false_rejection':sum(x['expected']['overall_pass'] is True and x['actual']['overall_pass'] is False for x in rows),
        'review_disagreements':sum(x['expected']['overall_pass'] is None and x['actual']['overall_pass'] is not None for x in rows),
        'missed_unknown_reference':sum(x['expected']['dimensions']['unsupported_citation_evidence']['score']==0 and x['actual']['dimensions']['unsupported_citation_evidence']['score']!=0 for x in rows)}
    after=[]
    for x in load(VAL/'ROUND2_REPRODUCTION_BEFORE.json')['probes']:
        tid=x['task_id'];good=old_labels[tid+'.01_correct']['candidate_content'];o=json.loads(good);o['notes']=[x['note']]
        if x.get('verification_status'):o['verification_status']=x['verification_status']
        r=evaluate_answer(tid,json.dumps(o));after.append({'finding':x['finding'],'task':tid,'note':x['note'],'R2_overall':x['original_result']['overall_pass'],'R3_result':r})
    save('ROUND2_REPRODUCTION_AFTER.json',after)
    result={'rubric':'exp-pack-1.0.3-draft','tests':tests,'prior_test_methods':58,'new_test_methods':tests['tests']-58,
        'single_fixture_count':len(rows),'prior_r2_single_count':len(prior_rows),'new_single_count':len(rows)-len(prior_rows),'paired_fixture_count':len(pairs),
        'outcomes':counts(rows),'r2_outcomes':counts([x for x in rows if x['fixture_id'] in old_labels]),
        'fixture_label_or_content_changes':[x['fixture_id'] for x in prior_rows if x['expectation_changed'] or x['candidate_content_changed']],
        'fixture_errors':bad,'pair_errors':pair_bad,'synthetic_error_counts':metrics,'fixtures':rows,
        'passed':tests['passed'] and not bad and not pair_bad,'independent_recheck':'PENDING','freeze':'DRAFT_PENDING_REVIEW','live_model_calls':0}
    save('RESULTS.json',result);print(json.dumps({k:v for k,v in result.items() if k!='fixtures'}));return result['passed']
if __name__=='__main__':sys.exit(0 if main() else 1)
