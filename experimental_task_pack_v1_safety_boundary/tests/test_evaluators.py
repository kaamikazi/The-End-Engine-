import copy
import json
from pathlib import Path
import unittest
from experimental_task_pack_v1_safety_boundary.evaluators import evaluate_answer,compare_candidates
from experimental_task_pack_v1_safety_boundary.evaluators.contracts import parse_answer
from experimental_task_pack_v1_safety_boundary.public_loader import load_public_task,render_public_prompt

ROOT=Path(__file__).resolve().parents[1]
def fixtures():return [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'fixtures').rglob('*.json'))]
def good(tid):return next(f for f in fixtures() if f['fixture_id']==tid+'.01_correct')['candidate_content']

class FixtureTests(unittest.TestCase):
    def test_original_fixture_expectations_are_historical(self):
        # Safety expectations remain byte-identical R3 records, not active labels.
        for f in fixtures():
            r=evaluate_answer(f['task_id'],f['candidate_content'],**f['evaluation_options'])
            self.assertIs(r['task_success'],f['expected']['task_success'])
            for name in ('substantive_correctness','output_contract_compliance','requirement_preservation','repair_completeness','unnecessary_alterations'):
                self.assertEqual({k:r['dimensions'][name][k] for k in ('score','status')},f['expected']['dimensions'][name])
            self.assertTrue(set(f['expected']['required_contract_errors'])<=set(r['dimensions']['output_contract_compliance']['violations']))

    def test_exactly_two_public_tasks_and_complete_fixture_metadata(self):
        self.assertEqual([p.stem for p in sorted((ROOT/'tasks').glob('*.json'))],['EXP-001','EXP-002'])
        ids=[f['fixture_id'] for f in fixtures()];self.assertEqual(len(ids),len(set(ids)))
        for tid in ('EXP-001','EXP-002'):
            self.assertGreaterEqual(sum(f['task_id']==tid for f in fixtures()),12)
        for f in fixtures():
            self.assertTrue(f['rationale']);self.assertEqual(len(f['expected']['dimensions']),7)
            self.assertEqual(f['candidate_role'],'SYNTHETIC_FIXTURE_NOT_ACTUAL_GENERATED_C0')
    def test_each_substantive_output_mutation_is_detected(self):
        for tid,n,field in [('EXP-001',3,'label'),('EXP-001',3,'handling'),('EXP-002',8,'decision')]:
            obj=json.loads(good(tid));key='labels' if tid=='EXP-001' else 'table'
            for i in range(n):
                with self.subTest(task=tid,row=i,field=field):
                    bad=copy.deepcopy(obj)
                    bad[key][i][field]='HOLD' if field=='decision' and bad[key][i][field]!='HOLD' else 'FULL' if field=='decision' else 'wrong'
                    r=evaluate_answer(tid,json.dumps(bad));self.assertLess(r['substantive_score'],1);self.assertFalse(r['overall_pass'])
    def test_every_immutable_input_flag_mutation_is_detected(self):
        obj=json.loads(good('EXP-002'))
        for i in range(8):
            for field in ('consent','quarantine','destination'):
                bad=copy.deepcopy(obj);value=bad['table'][i][field]
                bad['table'][i][field]=not value if type(value) is bool else 'external' if value=='internal' else 'internal'
                r=evaluate_answer('EXP-002',json.dumps(bad));self.assertLess(r['dimensions']['requirement_preservation']['score'],1)
                self.assertFalse(r['overall_pass'])
    def test_unknown_duplicate_missing_rows_and_explanations(self):
        for tid,key in [('EXP-001','labels'),('EXP-002','table')]:
            original=json.loads(good(tid))
            for change in ('duplicate','missing','unknown'):
                bad=copy.deepcopy(original)
                if change=='duplicate':bad[key][1]=copy.deepcopy(bad[key][0])
                elif change=='missing':bad[key].pop()
                else:bad[key][0]['accession' if tid=='EXP-001' else 'row_id']='UNKNOWN'
                r=evaluate_answer(tid,json.dumps(bad));self.assertFalse(r['overall_pass']);self.assertLess(r['substantive_score'],1)
    def test_bool_is_not_integer_and_input_edits_cannot_excuse_decisions(self):
        obj=json.loads(good('EXP-002'));obj['table'][1]['quarantine']=1
        r=evaluate_answer('EXP-002',json.dumps(obj));self.assertFalse(r['overall_pass'])
        self.assertEqual(r['substantive_score'],1);self.assertLess(r['dimensions']['requirement_preservation']['score'],1)
    def test_synthetic_transitions_measure_gain_loss_and_no_change(self):
        for tid in ('EXP-001','EXP-002'):
            fs=fixtures();wrong=next(f['candidate_content'] for f in fs if f['fixture_id']==tid+'.22_fully_wrong')
            g=good(tid)
            self.assertTrue(compare_candidates(tid,wrong,g)['substantive_improvement'])
            self.assertTrue(compare_candidates(tid,g,wrong)['substantive_regression'])
            self.assertFalse(compare_candidates(tid,g,g)['substantive_improvement'])
        # Supplied broken draft is not silently inserted as an artificial C0.
        r=compare_candidates('EXP-002',good('EXP-002'),good('EXP-002'))
        self.assertEqual(r['dimension_deltas']['repair_completeness'],0)
    def test_nonapplicable_repair_is_not_perfect_score(self):
        d=evaluate_answer('EXP-001',good('EXP-001'))['dimensions']['repair_completeness']
        self.assertEqual(d['status'],'NOT_APPLICABLE');self.assertIsNone(d['score'])
    def test_complete_answer_only_no_transcript_or_multi_block_rescue(self):
        for text in ('<think>hidden</think>'+good('EXP-001'),good('EXP-001')+'\n'+good('EXP-001'),
                     '```json\n'+good('EXP-001')+'\n```\n```json\n{}\n```'):
            r=evaluate_answer('EXP-001',text);self.assertFalse(r['overall_pass']);self.assertIsNone(r['substantive_score'])
        r=evaluate_answer('EXP-001',good('EXP-001'),answer_region_status='AMBIGUOUS')
        self.assertEqual(r['error_code'],'ANSWER_REGION_REQUIRES_REVIEW')
    def test_nonfinite_bounds_and_no_execution(self):
        for text in ('{"n":NaN}','{"n":1e999}','{"n":Infinity}','x'*65537,'[1]','{"x":'+('['*18)+'0'+(']'*18)+'}'):
            self.assertFalse(evaluate_answer('EXP-001',text)['overall_pass'])
        candidate='{"labels":[],"explanation":{},"scope":"label_text_only","notes":["__import__(\\"os\\").system(\\"echo BAD\\")"]}'
        self.assertFalse(evaluate_answer('EXP-001',candidate)['overall_pass'])
    def test_missing_execution_and_withholding_not_incorrect_content(self):
        for status in ('TIMEOUT','PROVIDER_UNAVAILABLE','BUDGET_EXHAUSTED','SAFETY_WITHHELD','SCORER_ERROR'):
            r=evaluate_answer('EXP-002','',execution_status=status)
            self.assertIsNone(r['task_success']);self.assertIsNone(r['overall_pass']);self.assertIsNone(r['substantive_score'])
            self.assertEqual(r['execution_status'],status);self.assertFalse(r['delivery_success'])
        self.assertEqual(evaluate_answer('EXP-002','')['evaluation_status'],'FORMAT_FAILURE')
    def test_public_prompt_whitelist_no_fixture_or_evaluator_material(self):
        for tid in ('EXP-001','EXP-002'):
            t=load_public_task(tid);prompt=render_public_prompt(tid)
            self.assertEqual(set(t),{'task_id','title','task_statement','input','output_contract','public_reference_ids'})
            for key in ('expected_scoring','expected_dimensions','GOOD1','GOOD2','fixture_id','architecture'):
                self.assertNotIn(key,prompt)
    def test_withheld_final_does_not_erase_observed_c0(self):
        r=compare_candidates('EXP-002',good('EXP-002'),'',final_options={'execution_status':'SAFETY_WITHHELD'})
        self.assertEqual(r['c0']['substantive_score'],1);self.assertIsNone(r['final']['substantive_score'])
        self.assertIsNone(r['substantive_regression'])
    def test_budget_exhaustion_complete_return_still_scored(self):
        for tid in ('EXP-001','EXP-002'):
            r=evaluate_answer(tid,good(tid),execution_status='BUDGET_EXHAUSTED')
            self.assertEqual(r['execution_status'],'BUDGET_EXHAUSTED');self.assertTrue(r['overall_pass'])
            self.assertEqual(r['substantive_score'],1)
            bad=evaluate_answer(tid,'{',execution_status='BUDGET_EXHAUSTED')
            self.assertEqual(bad['execution_status'],'BUDGET_EXHAUSTED');self.assertEqual(bad['evaluation_status'],'FORMAT_FAILURE')
            self.assertIsNone(bad['substantive_score'])

if __name__=='__main__':unittest.main()
