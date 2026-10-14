"""Offline fixture/pair reconciliation and preserved validation attempts."""
import csv
import json
from collections import Counter
from pathlib import Path
import sys
from experimental_task_pack_v1_r2.evaluators import evaluate_answer,compare_candidates
from experimental_task_pack_v1_r2 import evaluators
from experimental_task_pack_v1_r2.research_round2 import suite,save,reproductions

OUT=Path(__file__).resolve().parent;VAL=OUT/'validation'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    number=len(list(VAL.glob('revised-attempt-*.json')))+1
    tests=suite('experimental_task_pack_v1_r2/tests',f'revised-attempt-{number:02d}')
    prior=load(VAL/'ORIGINAL_FIXTURE_LABELS.json');rows=[];mismatches=[];original_rows=[]
    for path in sorted((OUT/'fixtures').rglob('*.json')):
        f=load(path);r=evaluate_answer(f['task_id'],f['candidate_content'],**f.get('evaluation_options',{}));e=f['expected'];bad=[]
        for key in ('overall_pass','task_success'):
            if r[key]!=e[key]:bad.append(key)
        if r['safety']['outcome']!=e['safety_outcome']:bad.append('safety_outcome')
        for name,expected in e['dimensions'].items():
            for key in ('status','score'):
                if r['dimensions'][name][key]!=expected[key]:bad.append(name+'.'+key)
        for key,actual in [('required_contract_errors',r['dimensions']['output_contract_compliance']['violations']),
            ('required_safety_violations',r['safety']['violations']),('required_review_reasons',r['safety']['review_reasons'])]:
            if not set(e.get(key,[]))<=set(actual):bad.append(key)
        if bad:mismatches.append({'fixture_id':f['fixture_id'],'fields':bad})
        row={'fixture_id':f['fixture_id'],'expected':e,'actual':r,'matches':not bad,'rationale':f['rationale']};rows.append(row)
        if f['fixture_id'] in prior:
            old=prior[f['fixture_id']];changed=old['expected']!=e
            original_rows.append({'fixture_id':f['fixture_id'],'original_content':old['candidate_content'],
                'round2_content':f['candidate_content'],'original_expectation':old['expected'],'new_expectation':e,
                'round2_result':r,'expectation_changed':changed,'content_changed':old['candidate_content']!=f['candidate_content'],
                'reason':'RV-001: alleged user/source statement does not occur in either original task' if changed else 'Prior contract expectation retained and reproduced',
                'contract_basis':'Public task input/statement contains no such reported attribution; nonendorsement alone cannot certify source occurrence' if changed else 'Unchanged public task and prior authored expectation',
                'independent_recheck_status':'PENDING'})
    pairs=[];pair_failures=[]
    for path in sorted((OUT/'paired_fixtures').glob('*.json')):
        p=load(path);r=compare_candidates(p['task_id'],p['c0_content'],p['final_content']);bad=[k for k,v in p['expected_transition_fields'].items() if r[k]!=v]
        pairs.append({'pair_id':p['pair_id'],'expected':p['expected_transition_fields'],'actual':r,'matches':not bad})
        if bad:pair_failures.append({'pair_id':p['pair_id'],'fields':bad})
    counts=dict(Counter('PASS' if r['actual']['overall_pass'] is True else 'FAIL' if r['actual']['overall_pass'] is False else 'REQUIRES_REVIEW' for r in rows))
    def error(e_pred,r_pred):return sum(e_pred(row['expected']) and r_pred(row['actual']) for row in rows)
    metrics={'false_accepts':error(lambda e:e['overall_pass'] is not True,lambda r:r['overall_pass'] is True),
        'false_rejects':error(lambda e:e['overall_pass'] is True,lambda r:r['overall_pass'] is False),
        'false_format_failures':error(lambda e:e['dimensions']['output_contract_compliance']['score']==1,lambda r:r['dimensions']['output_contract_compliance']['score']==0),
        'missed_citations':error(lambda e:e['dimensions']['unsupported_citation_evidence']['score']==0,lambda r:r['dimensions']['unsupported_citation_evidence']['score']!=0),
        'incorrect_attribution_approvals':error(lambda e:'UNSUPPORTED_ATTRIBUTION_REQUIRES_REVIEW' in e.get('required_review_reasons',[]),lambda r:r['safety']['score']==1),
        'incorrect_confirmation_allegations':sum(row['expected']['overall_pass'] is True and 'UNSUPPORTED_INDEPENDENT_CONFIRMATION' in row['actual']['safety']['violations'] for row in rows)}
    save('ORIGINAL_57_REVALIDATION.json',original_rows)
    with (VAL/'ORIGINAL_57_REVALIDATION.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['fixture_id','expectation_changed','content_changed','original_overall_pass','round2_overall_pass','reason','contract_basis','independent_recheck_status']);w.writeheader()
        for r in original_rows:w.writerow({k:r[k] for k in ('fixture_id','expectation_changed','content_changed','reason','contract_basis','independent_recheck_status')}|{'original_overall_pass':r['original_expectation']['overall_pass'],'round2_overall_pass':r['round2_result']['overall_pass']})
    save('PAIRWISE_RESULTS.json',pairs);save('FIXTURE_LABEL_CHANGES.json',[r for r in original_rows if r['expectation_changed']])
    reproductions(evaluators,'ROUND2_REPRODUCTIONS_AFTER')
    report={'rubric_version':'exp-pack-1.0.2-draft','tests':tests,'original_evaluator_test_methods':28,
        'additional_test_methods':tests['tests']-28,'single_fixture_count':len(rows),'original_fixture_count':len(original_rows),
        'paired_fixture_count':len(pairs),'fixture_outcome_counts':counts,
        'original_57_outcome_counts':dict(Counter('PASS' if r['round2_result']['overall_pass'] is True else 'FAIL' if r['round2_result']['overall_pass'] is False else 'REQUIRES_REVIEW' for r in original_rows)),
        'expectation_changes':[r['fixture_id'] for r in original_rows if r['expectation_changed']],
        'fixture_failures':mismatches,'pair_failures':pair_failures,'synthetic_error_counts':metrics,
        'passed':tests['passed'] and not mismatches and not pair_failures,'fixtures':rows,
        'round1_review_status':'REVISE','round2_review_status':'PREPARED_FOR_RE_REVIEW','independent_recheck_status':'PENDING',
        'freeze_status':'DRAFT_PENDING_REVIEW','live_model_calls':0,'benchmark_runs':0,
        'scope':'Same-author offline tests against explicit synthetic expectations; not real-world error rates or independent approval.'}
    save('RESULTS.json',report);print(json.dumps({k:v for k,v in report.items() if k!='fixtures'}))
    return report['passed']
if __name__=='__main__':sys.exit(0 if main() else 1)
