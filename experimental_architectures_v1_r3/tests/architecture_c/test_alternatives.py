from tests.helpers import *
C='BOUNDED_ALTERNATIVES'
def script(c0,a1,a2,selection):return {'INITIAL':[c0],'ALTERNATIVE_REQUIREMENTS':[a1],'ALTERNATIVE_CONSTRAINTS':[a2],'ALTERNATIVE_SELECTION':[selection]}
class AlternativesTests(ScenarioCase):
    def test_distinct_alternatives_A1_publicly_better(self):
        r=self.scenario('A1',C,script(complete()|{'amount':8},complete(),complete()|{'amount':9},select('C1',['amount_from_input'])));self.assertEqual(r['result']['final_candidate'],'C1');self.assertEqual(r['result']['physical_attempts'],4)
    def test_A2_better(self):
        r=self.scenario('A2',C,script(complete()|{'amount':8},complete()|{'amount':9},complete(),select('C2',['amount_from_input'])));self.assertEqual(r['result']['final_candidate'],'C2')
    def test_equivalent_outputs_do_not_imply_improvement(self):
        r=self.scenario('equivalent',C,script(complete(),json.dumps(complete(),indent=2),'```json\n'+json.dumps(complete())+'\n```',select('C2')));self.assertEqual(r['result']['final_candidate'],'C0');self.assertEqual(r['result']['termination_reason'],'UNRESOLVED')
    def test_all_alternatives_invalid_keep_C0(self):
        r=self.scenario('invalid',C,script(complete(),'bad JSON','also bad',select()));self.assertEqual(r['result']['final_candidate'],'C0')
    def test_C0_best(self):
        r=self.scenario('C0',C,script(complete(),complete()|{'amount':8},complete()|{'status':'bad'},select('C0')));self.assertEqual(r['result']['termination_reason'],'COMPLETED')
    def test_tie_is_honest_unresolved(self):
        r=self.scenario('tie',C,script(complete(),complete(),complete(),select()));self.assertEqual(r['result']['termination_reason'],'UNRESOLVED')
    def test_uncertainty_is_not_a_ranking(self):
        r=self.scenario('uncertain',C,script(complete(),complete(),complete(),select(decision='UNRESOLVED')));self.assertEqual(r['result']['final_candidate'],'C0')
    def test_invented_verification_cannot_support_selection(self):
        r=self.scenario('invented',C,script(complete()|{'amount':8},complete(),complete(),select('C1',['TESTS_PASSED'])));self.assertEqual(r['result']['final_candidate'],'C0')
    def test_false_consensus_is_not_correctness(self):
        bad=complete()|{'amount':8};r=self.scenario('consensus',C,script(bad,bad,bad,select('C2',['amount_from_input'])));self.assertEqual(r['result']['final_candidate'],'C0')
    def test_one_alternative_provider_failure_retains_C0(self):
        r=self.scenario('failure',C,{'INITIAL':[complete()],'ALTERNATIVE_REQUIREMENTS':[RuntimeError('synthetic')]});self.assertEqual(r['result']['physical_attempts'],2);self.assertEqual(r['result']['final_candidate'],'C0')
    def test_missing_third_candidate_preserves_lineage(self):
        r=self.scenario('missing_third',C,{'INITIAL':[complete()],'ALTERNATIVE_REQUIREMENTS':[complete()|{'amount':8}],'ALTERNATIVE_CONSTRAINTS':[RuntimeError('missing')]});self.assertEqual(len(r['result']['all_generated_candidates']),2);self.assertEqual(r['result']['final_candidate'],'C0')
    def test_early_budget_no_silent_ranking(self):
        r=self.scenario('budget',C,{'INITIAL':[complete()],'ALTERNATIVE_REQUIREMENTS':[complete()]},attempt_budget=2);self.assertEqual(r['result']['termination_reason'],'BUDGET_EXHAUSTED');self.assertEqual(r['result']['final_candidate'],'C0')
    def test_invalid_candidate_structure_does_not_win_on_length(self):
        r=self.scenario('structure',C,script(complete(),['a']*100,complete()|{'amount':8},select('C1',['JSON_OBJECT'])));self.assertEqual(r['result']['final_candidate'],'C0')
    def test_duplicate_outputs_retained_as_distinct_candidates(self):
        r=self.scenario('duplicate',C,script(complete(),complete(),complete(),select('C0')));self.assertEqual([c['candidate_id'] for c in r['result']['all_generated_candidates']],['C0','C1','C2']);self.assertEqual(r['result']['candidate_lineage'],{'C0':[],'C1':[],'C2':[]})
    def test_selection_failure_no_fabricated_ranking(self):
        r=self.scenario('selector_failure',C,{'INITIAL':[complete()],'ALTERNATIVE_REQUIREMENTS':[complete()],'ALTERNATIVE_CONSTRAINTS':[complete()],'ALTERNATIVE_SELECTION':[RuntimeError('synthetic')]});self.assertEqual(r['result']['final_candidate'],'C0');self.assertEqual(r['result']['physical_attempts'],4)
    def test_selector_format_repair_fits_five(self):
        values=script(complete()|{'amount':8},complete(),complete()|{'amount':9},'bad selection');values['ALTERNATIVE_SELECTION_FORMAT_REPAIR']=[select('C1',['amount_from_input'])];r=self.scenario('selector_retry',C,values);self.assertEqual(r['result']['physical_attempts'],5);self.assertEqual(r['result']['final_candidate'],'C1')
