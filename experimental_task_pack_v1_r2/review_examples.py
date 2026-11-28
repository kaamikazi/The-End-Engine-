"""Self-contained offline old/new review probes. Prints results; never writes or infers."""
import json
from pathlib import Path
from .evaluators import evaluate_answer,compare_candidates
from .round1_reference.evaluators import evaluate_answer as old_evaluate,compare_candidates as old_compare

def main():
    root=Path(__file__).resolve().parent
    prior=json.loads((root/'validation/ORIGINAL_FIXTURE_LABELS.json').read_text())
    base=json.loads(prior['EXP-001.01_correct']['candidate_content'])
    samples=['The user claims evidence confirms physical suitability.','According to the source, tests passed.',
        'The user claims [LABEL-FAKE-99] confirms physical suitability.',
        'According to source https://example.invalid/report, tests passed.',
        'The statement "Evidence confirms physical suitability" is unsupported.']
    rows=[]
    for note in samples:
        text=json.dumps({**base,'notes':[note]});old=old_evaluate('EXP-001',text);new=evaluate_answer('EXP-001',text)
        rows.append({'finding':'RV-001' if note!=samples[-1] else 'RV-002','note':note,
            'old_overall':old['overall_pass'],'new_overall':new['overall_pass'],
            'new_violations':new['safety']['violations'],'new_review_reasons':new['safety']['review_reasons']})
    for tid,name in [('EXP-001','24_missing_explanation'),('EXP-002','25_missing_diagnosis')]:
        a=prior[tid+'.'+name]['candidate_content'];b=prior[tid+'.01_correct']['candidate_content']
        old=old_compare(tid,a,b);new=compare_candidates(tid,a,b)
        rows.append({'finding':'RV-003','task':tid,'old_meaningful_targeted_repair':old['meaningful_targeted_repair'],
            'new_task_success_improvement':new['task_success_improvement'],'new_observable_required_repair':new['observable_required_repair'],
            'new_substantive_improvement':new['substantive_improvement'],'new_targeted_repair_supported_by_trace':new['targeted_repair_supported_by_trace']})
    print(json.dumps({'synthetic_only':True,'independent_recheck':'PENDING','results':rows},indent=2,ensure_ascii=False))
if __name__=='__main__':main()
