from tests.helpers import *
from src.shared.observations import equivalent
from src.prompts.registry import STAGES
class FairnessTests(ScenarioCase):
    def test_same_initial_concrete_bytes_for_three_algorithms(self):
        records=[]
        scripts={
          'SPARSE_DELIBERATION':{'INITIAL':[complete()],'SPARSE_GATE':[gate()]},
          'DIRECTED_REPAIR':{'INITIAL':[complete()],'REPAIR_INVENTORY':[{'findings':[]}]},
          'BOUNDED_ALTERNATIVES':{'INITIAL':[complete()],'ALTERNATIVE_REQUIREMENTS':[complete()],'ALTERNATIVE_CONSTRAINTS':[complete()],'ALTERNATIVE_SELECTION':[select('C0')]}}
        for c,v in scripts.items():records.append(self.scenario(c,c,v)['provider_records'][0]['wire'])
        self.assertEqual(len(set(records)),1)
    def test_genuine_distinct_control_flow(self):
        from src.architecture_a.sparse import run as a
        from src.architecture_b.repair import run as b
        from src.architecture_c.alternatives import run as c
        self.assertEqual(len({a.__module__,b.__module__,c.__module__}),3)
        self.assertEqual(STAGES['SPARSE_GATE']['schema']['properties']['decision']['enum'],['STOP','REVISE']);self.assertIn('REPAIR_PLAN',STAGES);self.assertNotEqual(STAGES['ALTERNATIVE_REQUIREMENTS']['prompt'],STAGES['ALTERNATIVE_CONSTRAINTS']['prompt'])
    def test_canonical_repair_condition_not_renamed(self):
        with self.assertRaises(ValueError):request('EVIDENCE_DIRECTED_REPAIR')
    def test_equivalent_formatting_is_not_substantive_change(self):
        self.assertTrue(equivalent(json.dumps(complete()),'```json\n'+json.dumps(dict(reversed(list(complete().items()))),indent=2)+'\n```'))
    def test_property_complete_C0_stop_across_equivalent_encodings(self):
        variants=[json.dumps(complete()),json.dumps(complete(),indent=2),'```json\n'+json.dumps(complete())+'\n```']
        for i,text in enumerate(variants):
            r=self.scenario('encoding_'+str(i),'SPARSE_DELIBERATION',{'INITIAL':[text],'SPARSE_GATE':[gate()]});self.assertEqual(r['result']['final_candidate'],'C0');self.assertEqual(r['result']['termination_reason'],'NO_ACTIONABLE_REVISION')
    def test_property_targeted_repair_cannot_overwrite_non_target(self):
        for wrong in (0,1,8,99,-2):
            r=self.scenario('amount_'+str(wrong),'SPARSE_DELIBERATION',{'INITIAL':[complete()|{'amount':wrong}],'SPARSE_GATE':[gate(['amount_from_input'])],'SPARSE_REVISION':[complete()|{'item_id':'CHANGED'}]});self.assertEqual(r['result']['final_candidate'],'C0')

    def test_public_identifiers_recorded_without_private_rubric(self):
        r=inspect(task(),json.dumps(complete()));self.assertEqual(r['public_identifier_facts']['item_id'][0]['value'],'T-1');self.assertEqual(r['semantic_correctness'],'NOT_ASSESSED')
    def test_whole_format_repair_cannot_erase_known_public_identifier(self):
        r=self.scenario('root_preservation','SPARSE_DELIBERATION',{'INITIAL':[[{'item_id':'T-1'}]],'SPARSE_GATE':[gate(['JSON_OBJECT'])],'SPARSE_REVISION':[complete()|{'item_id':'OTHER'}]});self.assertEqual(r['result']['final_candidate'],'C0')
