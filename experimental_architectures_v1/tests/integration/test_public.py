from tests.helpers import *
from src.shared.wiring import baseline,wiring_script
class IntegrationTests(ScenarioCase):
    def test_frozen_public_task_snapshots_exact(self):
        for tid in ('EXP-001','EXP-002'):self.assertEqual((OUT/'public_inputs'/(tid+'.json')).read_bytes(),(ROOT/'native_model_integration_v1/public_inputs'/(tid+'.json')).read_bytes())
    def test_actual_baseline_common_contract_without_behavior_change(self):
        from dataclasses import replace
        t=json.loads((OUT/'public_inputs/EXP-001.json').read_text(encoding='utf-8'))
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');q=RunRequest(t['task_id'],t,'qwen3:4b','UNOBSERVED_NO_MODEL_QUERIED',{'temperature':.7,'top_p':.8,'think':False},None,8192,4096,'FROZEN_CURRENT_END',36,400000,1800,'native_unit');r=baseline(q,Path(d)/'native',l);self.assertEqual(r['result']['physical_attempts'],29);self.assertEqual(len(r['result']['all_generated_candidates']),4);self.assertEqual(r['result']['candidate_lineage']['C1'],['C0'])
    def test_same_mock_inputs_repeat_logical_outcome(self):
        values={'INITIAL':[complete()|{'amount':8}],'SPARSE_GATE':[gate(['amount_from_input'])],'SPARSE_REVISION':[complete()]};a=self.scenario('repeat_a','SPARSE_DELIBERATION',values);b=self.scenario('repeat_b','SPARSE_DELIBERATION',values);self.assertEqual(a['FINAL'],b['FINAL']);self.assertEqual(a['result']['termination_reason'],b['result']['termination_reason']);self.assertEqual(a['result']['candidate_lineage'],b['result']['candidate_lineage'])
    def test_input_defect_object_not_substituted_for_C0(self):
        r=self.scenario('C0','SPARSE_DELIBERATION',{'INITIAL':[complete()],'SPARSE_GATE':[gate()]});self.assertNotEqual(r['C0'],json.dumps(task()['input']));self.assertEqual(r['result']['all_generated_candidates'][0]['attempt_id'],r['result']['model_invocations'][0]['attempt_id'])
