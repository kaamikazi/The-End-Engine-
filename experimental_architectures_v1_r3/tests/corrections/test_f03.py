from .common import *
class BaselineAdmissionTests(unittest.TestCase):
    def q(self,c):
        t=json.loads((OUT/'public_inputs/EXP-001.json').read_text(encoding='utf-8'));return replace(request(c),task_id=t['task_id'],public_task_payload=t)
    def check_rejected(self,changes):
        with temporary() as d:
            for condition in ('DIRECT','SELF_REFLECT','FROZEN_CURRENT_END'):
                p=Path(d)/condition;l=Ledger(Path(d)/(condition+'.budget.json'));q=replace(self.q(condition),**changes)
                with self.assertRaises(ContractAdmissionError):baseline(q,p,l)
                self.assertEqual(l.state()['attempts'],[]);self.assertEqual(l.state()['runs'],{});self.assertFalse(p.exists());evidence(self,'F03',condition=condition,requested_changes=changes,reservations=0,output_directory_created=False)
    def test_exact_defaults_execute_all_original_baselines(self):
        with temporary() as d:
            counts={}
            for c in ('DIRECT','SELF_REFLECT','FROZEN_CURRENT_END'):
                q=self.q(c);l=Ledger(Path(d)/(c+'.budget.json'));r=baseline(q,Path(d)/c,l);counts[c]=r['result']['physical_attempts'];self.assertEqual(r['baseline_contract']['requested_sha256'],r['baseline_contract']['admitted_effective_sha256']);self.assertEqual(r['request'],r['effective_ledger_request'])
            self.assertEqual(counts,{'DIRECT':1,'SELF_REFLECT':3,'FROZEN_CURRENT_END':29});evidence(self,'F03',supported_counts=counts)
    def test_dictionary_or_unknown_required_field_rejected(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');q=asdict(self.q('DIRECT'));q['unknown_required_field']='tools'
            with self.assertRaises(ContractAdmissionError):baseline(q,Path(d)/'cell',l)
            self.assertFalse(l.state()['attempts'])
    def test_mutated_public_contract_rejected_before_reservation(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');q=self.q('DIRECT');q.public_task_payload['output_contract']['extra']='NEW_CONTRACT'
            with self.assertRaises(ContractAdmissionError):baseline(q,Path(d)/'cell',l)
            self.assertEqual(l.state()['attempts'],[])
    def test_partial_native_cell_never_replays(self):
        from src.shared.wiring import BaselineRecoveryBlocked
        with temporary() as d:
            q=self.q('DIRECT');l=Ledger(Path(d)/'l.json');l.register(q);l.reserve(q.run_id,'synthetic interrupted original reservation',1,1)
            with self.assertRaises(BaselineRecoveryBlocked):baseline(q,Path(d)/'cell',l)
            self.assertEqual(len(l.state()['attempts']),1)
    def test_request_mutation_after_dispatch_cannot_be_echoed_as_effective(self):
        import src.shared.wiring as wiring
        original=wiring.run_baseline
        with temporary() as d:
            q=self.q('DIRECT');ledger=Ledger(Path(d)/'l.json')
            def mutate(*args,**kw):
                result=original(*args,**kw);q.generation_parameters['temperature']=.4;return result
            with patch.object(wiring,'run_baseline',side_effect=mutate):
                with self.assertRaises(ArtifactIntegrity):baseline(q,Path(d)/'cell',ledger)
            self.assertFalse((Path(d)/'cell/COMMON_RESULT.json').exists());self.assertEqual(len(ledger.state()['attempts']),1)
CHANGES={
 'model':{'model_identity':'unsupported-model'},'digest':{'model_digest':'unobserved-different-digest'},'seed':{'seed_if_supported':11},
 'temperature':{'generation_parameters':{'temperature':.6,'top_p':.8,'think':False}},'top_p':{'generation_parameters':{'temperature':.7,'top_p':.7,'think':False}},'thinking':{'generation_parameters':{'temperature':.7,'top_p':.8,'think':True}},
 'context':{'context_window':4096},'output_cap':{'maximum_output_tokens':2048},'attempts':{'attempt_budget':1},'tokens':{'token_budget':1},'active_time':{'wall_time_budget':1}}
for name,values in CHANGES.items():
    def test(self,changes=values):self.check_rejected(changes)
    setattr(BaselineAdmissionTests,'test_reject_'+name,test)
