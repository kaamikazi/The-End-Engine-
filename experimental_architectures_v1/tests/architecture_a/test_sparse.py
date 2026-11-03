from tests.helpers import *
A='SPARSE_DELIBERATION'
class SparseTests(ScenarioCase):
    def test_complete_C0_stops_without_revision(self):
        r=self.scenario('complete',A,{'INITIAL':[complete()],'SPARSE_GATE':[gate()]});self.assertEqual(r['result']['termination_reason'],'NO_ACTIONABLE_REVISION');self.assertEqual(r['result']['physical_attempts'],2);self.assertEqual(r['result']['final_candidate'],'C0')
    def test_missing_mandatory_section_repaired(self):
        bad=complete();bad.pop('status');r=self.scenario('missing',A,{'INITIAL':[bad],'SPARSE_GATE':[gate(['required:status','status_from_input'])],'SPARSE_REVISION':[complete()]});self.assertEqual(r['result']['final_candidate'],'C1')
    def test_malformed_initial_format_repaired(self):
        r=self.scenario('malformed',A,{'INITIAL':['{bad'],'SPARSE_GATE':[gate(['JSON_OBJECT'])],'SPARSE_REVISION':[complete()]});self.assertEqual(r['result']['final_candidate'],'C1');self.assertTrue(r['result']['provenance_records'])
    def test_public_contradiction_targeted(self):
        r=self.scenario('contradiction',A,{'INITIAL':[complete()|{'amount':8}],'SPARSE_GATE':[gate(['amount_from_input'])],'SPARSE_REVISION':[complete()]});self.assertEqual(r['result']['physical_attempts'],3);self.assertEqual(r['result']['termination_reason'],'COMPLETED')
    def test_vague_unsupported_criticism_cannot_trigger_rewrite(self):
        g=gate(['invented_target']);r=self.scenario('unsupported',A,{'INITIAL':[complete()],'SPARSE_GATE':[g]});self.assertEqual(r['result']['final_candidate'],'C0');self.assertEqual(r['result']['physical_attempts'],2)
    def test_generic_uncertainty_only_stops(self):
        g=gate();g['uncertainty']=['Maybe this could be better'];r=self.scenario('uncertainty',A,{'INITIAL':[complete()],'SPARSE_GATE':[g]});self.assertEqual(r['result']['termination_reason'],'NO_ACTIONABLE_REVISION')
    def test_repair_damaging_unaffected_content_retains_C0(self):
        r=self.scenario('preservation',A,{'INITIAL':[complete()|{'amount':8}],'SPARSE_GATE':[gate(['amount_from_input'])],'SPARSE_REVISION':[complete()|{'item_id':'DAMAGED'}]});self.assertEqual(r['result']['final_candidate'],'C0');self.assertEqual(len(r['result']['all_generated_candidates']),2)
    def test_no_progress_revision_retained(self):
        bad=complete()|{'amount':8};r=self.scenario('no_progress',A,{'INITIAL':[bad],'SPARSE_GATE':[gate(['amount_from_input'])],'SPARSE_REVISION':[bad]});self.assertEqual(r['result']['termination_reason'],'NO_PROGRESS')
    def test_provider_failure_preserves_C0(self):
        r=self.scenario('failure',A,{'INITIAL':[complete()],'SPARSE_GATE':[RuntimeError('synthetic provider failure')]});self.assertEqual(r['result']['final_candidate'],'C0');self.assertIsNone(r['result']['total_tokens'])
    def test_budget_stops_before_revision(self):
        r=self.scenario('budget',A,{'INITIAL':[complete()|{'amount':8}],'SPARSE_GATE':[gate(['amount_from_input'])]},attempt_budget=2);self.assertEqual(r['result']['termination_reason'],'BUDGET_EXHAUSTED');self.assertEqual(r['result']['physical_attempts'],2)
    def test_unknown_usage_no_gate_call(self):
        r=self.scenario('unknown',A,{'INITIAL':[unknown(complete())]});self.assertEqual(r['result']['physical_attempts'],1);self.assertEqual(r['result']['final_candidate'],'C0');self.assertIsNone(r['result']['total_tokens'])
    def test_interrupted_gate_preserves_C0(self):
        r=self.scenario('interrupted',A,{'INITIAL':[complete()],'SPARSE_GATE':[KeyboardInterrupt()]});self.assertEqual(r['result']['termination_reason'],'INTERRUPTED')
    def test_one_control_format_repair_counts_four_total(self):
        r=self.scenario('format_retry',A,{'INITIAL':[complete()|{'amount':8}],'SPARSE_GATE':['bad control'],'SPARSE_GATE_FORMAT_REPAIR':[gate(['amount_from_input'])],'SPARSE_REVISION':[complete()]});self.assertEqual(r['result']['physical_attempts'],4);self.assertEqual(r['result']['final_candidate'],'C1')
    def test_second_malformed_gate_does_not_loop(self):
        r=self.scenario('invalid_twice',A,{'INITIAL':[complete()],'SPARSE_GATE':['bad'],'SPARSE_GATE_FORMAT_REPAIR':['still bad']});self.assertEqual(r['result']['physical_attempts'],3);self.assertEqual(r['result']['termination_reason'],'PROTOCOL_FAILURE')
