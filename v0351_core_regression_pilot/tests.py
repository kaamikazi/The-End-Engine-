"""Small infrastructure checks, using mocks only; not pilot observations."""
from dataclasses import asdict
import unittest

from end_engine.models.base import ModelRequest
from .bench.conditions import EndSettings
from .bench.evaluators import evaluate
from .bench.providers import ModelSettings,render
from .run_pilot import execution_plan,projection,TASKS,CONDITIONS,OUT,load


class PilotInfrastructureTests(unittest.TestCase):
    def test_order_is_exact_historical_order(self):
        self.assertEqual(execution_plan(),load(OUT/'historical_v035_manifest.json')['plan'])

    def test_no_candidate_error_has_scoreable_empty_output(self):
        from .run_pilot import evaluate_record
        task=load(OUT/'tasks/BA-001.json')
        result=evaluate_record(task,{'run_id':'fixture','answer':'','stages':{},
            'end':{'candidates':[],'returned_candidate_id':None}},OUT)
        self.assertEqual(result['final']['score'],0)
        self.assertEqual(result['candidates'],{})

    def test_local_transport_rejects_undeclared_endpoint_without_request(self):
        from .run_pilot import local_json,InfrastructureDefect
        with self.assertRaises(InfrastructureDefect):local_json('/api/pull')

    def test_withheld_output_is_distinct_from_selected_candidate_score(self):
        from .report_pilot import metrics
        record={'run_id':'fixture','task_id':'BA-009','condition':'FULL_END_NATIVE','answer':'','calls':[],
            'end':{'returned_candidate_id':'C0','iterations':2,'termination':'BUDGET_EXHAUSTED','quality_gate':'BLOCKED'},
            'cost':{'wall_ms':0,'calls':0,'total_tokens':0,'prompt_tokens':0,'completion_tokens':0,'truncated_text_answers':0}}
        score=lambda n:{'score':n,'passed':False,'format_ok':False,'answer_chars':0,'counters':{'unsupported_claim_count':0}}
        row=metrics(record,{'final':score(0),'candidates':{'C0':score(.5)}},
                    {'output_integrity':{'blocked':True},'candidates':[{'candidate_id':'C0','content':'x'}]})
        self.assertEqual((row['external_score'],row['selected_candidate_score'],row['revision_value'],row['output_withheld']),
                         (0,.5,'REGRESSED',True))

    def test_exact_unique_matrix_and_recorded_order(self):
        plan=execution_plan()
        self.assertEqual(len(plan),12)
        self.assertEqual(len({p['run_id'] for p in plan}),12)
        self.assertEqual({p['task_id'] for p in plan},set(TASKS))
        self.assertTrue(all(p['trial']==1 for p in plan))
        for task in TASKS:self.assertEqual({p['condition'] for p in plan if p['task_id']==task},set(CONDITIONS))
        self.assertEqual(plan,execution_plan())

    def test_full_conditions_differ_only_by_candidate_generation(self):
        settings=EndSettings(full_max_cycles=3)
        a=asdict(settings.full_config(OUT/'trajectories','structured'))
        b=asdict(settings.full_config(OUT/'trajectories','native'))
        self.assertEqual(a.pop('candidate_generation'),'structured');self.assertEqual(b.pop('candidate_generation'),'native')
        self.assertEqual(a,b);self.assertEqual(settings.full_max_cycles,3)
        self.assertEqual(a['decision']['provider'],'baseline');self.assertEqual(a['protocol_repair_attempts'],1)

    def test_generation_settings_frozen(self):
        s=ModelSettings('qwen3:4b')
        self.assertEqual((s.temperature,s.top_p,s.num_predict,s.num_ctx,s.think,s.timeout_seconds),(.7,.8,4096,8192,False,900))

    def test_direct_native_initial_render_matches_task_prompt(self):
        task=load(OUT/'tasks/BA-001.json')
        a=render(ModelRequest('direct_answer',task['prompt'],{},None))
        b=render(ModelRequest('initial_candidate',task['prompt'],{},None))
        self.assertEqual(a,task['prompt']);self.assertEqual(a,b)

    def test_runtime_projection_stops_expensive_followups(self):
        plan=execution_plan();first=next(p for p in plan if p['condition'].startswith('FULL_END'))
        estimate=projection([{**first,'cost':{'wall_ms':3600*1000}}],plan)
        self.assertTrue(estimate['threshold_exceeded']);self.assertGreater(estimate['projected_total_hours'],6)

    def test_runtime_projection_uses_observed_direct(self):
        plan=execution_plan();full=next(p for p in plan if p['condition'].startswith('FULL_END'));direct=next(p for p in plan if p['condition']=='DIRECT')
        result=projection([{**full,'cost':{'wall_ms':100000}},{**direct,'cost':{'wall_ms':10000}}],plan)
        self.assertEqual(result['DIRECT_estimate_seconds'],10);self.assertAlmostEqual(result['projected_total_seconds'],840)

    def test_frozen_numeric_evaluator_checks_correct_values(self):
        task=load(OUT/'tasks/BA-001.json')
        self.assertTrue(evaluate(task,'```json\n[-40,32,97.9,212,70.7]\n```')['passed'])
        self.assertFalse(evaluate(task,'```json\n[-40,32,67.9,212,70.7]\n```')['passed'])

    def test_frozen_code_evaluator_executes_safe_unit_tests(self):
        task=load(OUT/'tasks/BA-002.json')
        answer='```python\ndef chunk(items,size):\n    if not isinstance(size,int) or size<=0: raise ValueError()\n    return [items[i:i+size] for i in range(0,len(items),size)]\n```'
        self.assertTrue(evaluate(task,answer)['passed'])

    def test_diagnostics_preserve_actual_engine_leakage_fields(self):
        from .report_pilot import metrics
        record={'run_id':'fixture','task_id':'BA-001','condition':'DIRECT','answer':'','calls':[],
                'cost':{'wall_ms':0,'calls':0,'total_tokens':0,'prompt_tokens':0,'completion_tokens':0,'truncated_text_answers':0}}
        evaluation={'final':{'score':0,'passed':False,'format_ok':False,'answer_chars':0,
                            'counters':{'unsupported_claim_count':0}},'candidates':{}}
        result=metrics(record,evaluation,{'engine_checks':[{'internal_leakage':['weakness ID W001']} ]})
        self.assertEqual(result['internal_leakage'],1)


if __name__=='__main__':unittest.main()
