"""Estimate future budget solely from saved historical costs; never execute a runner."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from end_engine.core.task_analyzer import TaskAnalyzer
from experimental_task_pack_v1.public_loader import render_public_prompt
def main():
    s=json.loads((ROOT/'architecture_review_v1/SUMMARY.json').read_text());runs=json.loads((ROOT/'architecture_review_v1/RUNS.json').read_text())
    native=[r for r in runs if r['condition']=='FULL_END_NATIVE'];recent=[r for r in native if r['version']=='0.3.5.1']
    # Two tasks, one repetition: all non-END ordinary structures, not measured variants.
    nonend={'initial_generation':14,'operator_critique':6,'revision_generation':6,'revision_planning':2,'candidate_comparison':6}
    estimated_nonend={metric:sum(n*s['purpose_costs'][purpose][metric]/s['purpose_costs'][purpose]['calls'] for purpose,n in nonend.items())
        for metric in ('tokens','provider_latency_seconds')}
    record={'date':'2026-10-12','estimate_only':True,'live_inference_for_estimation':False,
        'historical_all_full_end':{'runs':16,'calls':466,'mean_calls':466/16},
        'historical_native':{'runs':len(native),'calls':sum(r['calls'] for r in native),
            'mean_calls':sum(r['calls'] for r in native)/len(native),'max_calls':max(r['calls'] for r in native),
            'mean_tokens':sum(r['tokens'] for r in native)/len(native),'mean_run_wall_seconds':sum(r['wall_seconds'] for r in native)/len(native)},
        'original_24_three_cycle_estimate':{'native_control_calls':4*sum(r['calls'] for r in native)/len(native),
            'nonend_structural_max_calls':4*(1+3+4+5+5),'total_native_based':4*sum(r['calls'] for r in native)/len(native)+72,
            'total_pooled_based':4*(466/16)+72,'hard_structural_all_cells_max':4*(1+3+36+4+5+5)},
        'revised_stage1':{'runs':12,'repetitions':1,'tasks':2,'conditions':6,'ordinary_nonend_calls':sum(nonend.values()),
            'ordinary_native_based_calls':2*sum(r['calls'] for r in native)/len(native)+sum(nonend.values()),
            'published_cell_max_calls':2*(1+3+36+4+5+5),'outer_equal_per_run_call_limit':36,
            'unchanged_global_authorization_proposal':{'calls':136,'tokens':400000,'active_wall_seconds':10800},
            'estimated_tokens':2*sum(r['tokens'] for r in native)/len(native)+estimated_nonend['tokens'],
            'estimated_wall_seconds_native_pooled':2*sum(r['wall_seconds'] for r in native)/len(native)+estimated_nonend['provider_latency_seconds'],
            'estimated_wall_seconds_latest_native':2*sum(r['wall_seconds'] for r in recent)/len(recent)+estimated_nonend['provider_latency_seconds'],
            'nonend_purpose_estimates':estimated_nonend,'ordinary_nonend_purpose_counts':nonend,
            'reserve_to_published_cell_caps':2*(1+3+36+4+5+5)-(2*sum(r['calls'] for r in native)/len(native)+sum(nonend.values()))},
        'decision':'Original136 arithmetic fits a one-cycle16-call END override, not a historically comparable three-cycle control. Propose12-run stage1; stage2 needs separate approval. No budget increase or live execution.',
        'limitations':['Current v0.3.5.2 native usage unmeasured','A/B/C unimplemented structural estimates',
            'Historical wall/provider latency partly mixed; orchestration overhead unknown','New task prompt/output lengths differ',
            'Server drift/load/repair/sampling uncertainty','36-call ceiling can still truncate rare/new control runs; disclose and stop rather than claim fair completed superiority']}
    analyses={}
    for tid in ('EXP-001','EXP-002'):
        prompt=render_public_prompt(tid)
        result=TaskAnalyzer().analyze(prompt,use_llm=False,mode=None,max_cycles=3)
        analyses[tid]={'prompt_characters':len(prompt),'complexity':result.complexity.value,
            'minimum_cycles':result.reasoning_budget.min_cycles,'maximum_cycles':result.reasoning_budget.max_cycles,
            'rationale':result.rationale,'analysis_only_no_provider':True}
    record['current_offline_task_classification']=analyses
    record['source_structural_no_repair_no_branch_control']={'pre_cycle_calls':5,'calls_per_cycle':8,
        'two_cycle_calls':21,'three_cycle_calls':29,
        'full24_two_cycle_control_plus_other_ordinary_calls':4*21+4*(1+3+4+5+4),
        'full24_two_cycle_control_plus_other_max_calls':4*21+72,
        'one_cycle16_call_control_cannot_normally_complete_current_minimum':all(x['minimum_cycles']>1 for x in analyses.values()),
        'caveat':'Conditional structure count, not observed usage. Protocol failure/budget interruption can stop without completed cycles; additional best comparisons/repair/branches increase calls.'}
    (OUT/'validation/BUDGET_ESTIMATES.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(record['revised_stage1']))
if __name__=='__main__':main()
