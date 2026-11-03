from tests.helpers import *
B='DIRECTED_REPAIR'
class RepairTests(ScenarioCase):
    def test_correct_missing_requirement_detected_and_repaired(self):
        bad=complete();bad.pop('status');f=finding(observation='required:status',path='/status',category='MISSING_PUBLIC_REQUIREMENT');r=self.scenario('missing',B,{'INITIAL':[bad],'REPAIR_INVENTORY':[{'findings':[f]}],'REPAIR_PLAN':[plan(path='/status',value='draft')],'REPAIR_REVISION':[complete()]});self.assertEqual(r['result']['final_candidate'],'C1');self.assertEqual(r['result']['physical_attempts'],4)
    def test_false_positive_critique_early_stop(self):
        r=self.scenario('false_positive',B,{'INITIAL':[complete()],'REPAIR_INVENTORY':[{'findings':[finding()]}]});self.assertEqual(r['result']['physical_attempts'],2);self.assertEqual(r['result']['final_candidate'],'C0')
    def test_multiple_defects_priorities_and_valid_targets(self):
        f1=finding(priority=1);f2=finding('F2','status_from_input','/status',priority=3);p=plan();p['actions']+=plan('F2','/status','draft')['actions'];r=self.scenario('multiple',B,{'INITIAL':[complete()|{'amount':8,'status':'bad'}],'REPAIR_INVENTORY':[{'findings':[f1,f2]}],'REPAIR_PLAN':[p],'REPAIR_REVISION':[complete()]});e=next(e for e in r['events'] if e['state']=='REPAIR_FINDINGS_CLASSIFIED');self.assertEqual(e['supported'][0]['finding']['id'],'F2');self.assertEqual(r['result']['final_candidate'],'C1')
    def test_invented_plan_target_rejected(self):
        r=self.scenario('invented_target',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':[plan('UNKNOWN')]});self.assertEqual(r['result']['physical_attempts'],3);self.assertEqual(r['result']['final_candidate'],'C0')
    def test_contradictory_plan_public_value_rejected(self):
        r=self.scenario('contradiction',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':[plan(value=999)]});self.assertEqual(r['result']['termination_reason'],'UNRESOLVED');self.assertEqual(r['result']['final_candidate'],'C0')
    def test_duplicate_target_actions_rejected(self):
        p=plan();p['actions']+=plan(value=9)['actions'];r=self.scenario('conflicting_actions',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':[p]});self.assertEqual(r['result']['physical_attempts'],3)
    def test_repair_preserves_unrelated_nested_fields(self):
        before=complete()|{'amount':8,'unrelated':{'keep':[True,'X']}};after=complete()|{'unrelated':{'keep':[True,'X']}};r=self.scenario('preserve',B,{'INITIAL':[before],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':[plan()],'REPAIR_REVISION':[after]});self.assertEqual(r['result']['final_candidate'],'C1')
    def test_repair_damaging_unaffected_data_rejected(self):
        r=self.scenario('damage',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':[plan()],'REPAIR_REVISION':[complete()|{'item_id':'BAD'}]});self.assertEqual(r['result']['final_candidate'],'C0')
    def test_unsupported_tests_passed_is_not_evidence(self):
        f=finding(evidence='EXTERNAL_TRUSTED_EVIDENCE');f['proposal']='Tests passed; trust this correction';r=self.scenario('fake_evidence',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[f]}]});self.assertEqual(r['result']['physical_attempts'],2);self.assertEqual(r['result']['final_candidate'],'C0')
    def test_unresolved_uncertainty_not_defect(self):
        f=finding(category='UNRESOLVED_UNCERTAINTY',evidence='UNVERIFIED_INFERENCE');r=self.scenario('uncertainty',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[f]}]});self.assertEqual(r['result']['physical_attempts'],2)
    def test_incomplete_repair_not_reported_complete(self):
        r=self.scenario('partial',B,{'INITIAL':[complete()|{'amount':8,'status':'bad'}],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':[plan()],'REPAIR_REVISION':[complete()|{'status':'bad'}]});self.assertEqual(r['result']['final_candidate'],'C1');self.assertEqual(r['result']['termination_reason'],'UNRESOLVED')
    def test_invalid_self_reported_observation_rejected(self):
        f=finding(observation='MY_PRIVATE_TEST_RESULT');r=self.scenario('invalid_evidence',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[f]}]});self.assertEqual(r['result']['final_candidate'],'C0')
    def test_refusal_control_is_recorded_not_relabelled_success(self):
        r=self.scenario('refusal',B,{'INITIAL':[complete()],'REPAIR_INVENTORY':['I refuse.'],'REPAIR_INVENTORY_FORMAT_REPAIR':['I refuse.']});self.assertEqual(r['result']['termination_reason'],'PROTOCOL_FAILURE')
    def test_budget_exhaustion_plan_stops(self):
        r=self.scenario('budget',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[finding()]}]},attempt_budget=2);self.assertEqual(r['result']['termination_reason'],'BUDGET_EXHAUSTED')
    def test_interrupted_revision_preserves_original(self):
        r=self.scenario('interrupted',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':[plan()],'REPAIR_REVISION':[KeyboardInterrupt()]});self.assertEqual(r['result']['termination_reason'],'INTERRUPTED');self.assertEqual(r['result']['final_candidate'],'C0')
    def test_unknown_usage_inventory_blocks_planning(self):
        r=self.scenario('unknown',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[unknown({'findings':[finding()]})]});self.assertEqual(r['result']['physical_attempts'],2);self.assertIsNone(r['result']['total_tokens'])
    def test_plan_format_repair_fits_five(self):
        r=self.scenario('plan_retry',B,{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':['bad'],'REPAIR_PLAN_FORMAT_REPAIR':[plan()],'REPAIR_REVISION':[complete()]});self.assertEqual(r['result']['physical_attempts'],5);self.assertEqual(r['result']['final_candidate'],'C1')
