import dataclasses,json,unittest
from pathlib import Path
from tests.helpers import request,task,temporary
from src.interfaces.contracts import CONDITIONS,ALIASES,TERMINATIONS,RunRequest,public_task,Candidate,RunResult
from src.public_runner.mock import MockSession
from src.accounting.ledger import Ledger
class InterfaceTests(unittest.TestCase):
    def test_all_six_identical_initial_public_bytes(self):
        self.assertEqual(len({request(c).wire_bytes() for c in CONDITIONS}),1)
    def test_explicit_alias_not_silent_relabel(self):
        self.assertEqual(ALIASES['EVIDENCE_DIRECTED_REPAIR'],'DIRECTED_REPAIR')
        with self.assertRaises(ValueError):request('EVIDENCE_DIRECTED_REPAIR')
    def test_required_request_fields(self):
        fields={f.name for f in dataclasses.fields(RunRequest)}
        self.assertEqual(fields,set('task_id public_task_payload model_identity model_digest generation_parameters seed_if_supported context_window maximum_output_tokens condition_id attempt_budget token_budget wall_time_budget run_id'.split()))
    def test_invalid_request_numbers(self):
        for kw in ({'attempt_budget':37},{'attempt_budget':True},{'token_budget':0},{'wall_time_budget':float('nan')},{'context_window':0},{'maximum_output_tokens':9000},{'seed_if_supported':False}):
            with self.subTest(kw=str(kw)),self.assertRaises(ValueError):request(**kw)
    def test_model_settings_reject_unknown_secret(self):
        with self.assertRaises(ValueError):request(generation_parameters={'temperature':.7,'top_p':.8,'think':False,'api_key':'SYNTHETIC-NOT-A-KEY'})
    def test_input_detached_from_external_mutation(self):
        t=task();r=request(public_task_payload=t);t['input']['word']='mutated';self.assertEqual(r.public_task_payload['input']['word'],'blue')
    def test_nonfinite_public_json_reject(self):
        t=task();t['input']['x']=float('inf')
        with self.assertRaises(ValueError):public_task(t)
    def test_task_identity_mismatch(self):
        with self.assertRaises(ValueError):request(task_id='different')
    def test_C0_final_lineage_separate(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'));c0=s.dispatch('initial');c1=s.dispatch('final',parents=(c0.candidate_id,));r=s.result(final=c1.candidate_id)
            self.assertEqual(r.initial_candidate,'c0');self.assertEqual(r.final_candidate,'c1');self.assertEqual(r.candidate_lineage,{'c0':[],'c1':['c0']});self.assertNotEqual(r.initial_candidate,'TASK_INPUT')
    def test_final_can_retain_C0(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'));s.dispatch('first');s.dispatch('alternative',purpose='alternative');self.assertEqual(s.result(final='c0').final_candidate,'c0')
    def test_critique_not_generated_candidate(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'));s.dispatch('first');s.dispatch('opinion',purpose='critique');r=s.result();self.assertEqual(len(r.all_generated_candidates),1);self.assertEqual(r.physical_attempts,2)
    def test_unknown_parent_reject_before_dispatch(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');s=MockSession(request(),l)
            with self.assertRaises(ValueError):s.dispatch('x',parents=('missing',))
            self.assertEqual(l.summary('run')['physical_attempts'],0)
    def test_TASK_INPUT_candidate_reject(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'));s.dispatch('x');r=s.result();bad=dataclasses.replace(r,all_generated_candidates=(Candidate('TASK_INPUT','x',1),))
            with self.assertRaises(ValueError):bad.validate()
    def test_partial_output_retained_and_not_complete(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'));s.dispatch('truncated {',failure='INTERRUPTED',input_tokens=None,output_tokens=None,seconds=None);r=s.result('INTERRUPTED');self.assertFalse(r.all_generated_candidates[0].complete);self.assertIsNone(r.total_tokens);self.assertEqual(r.diagnostic_errors[0]['retained_output'],'truncated {')
    def test_failed_without_output_null_C0(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'));s.dispatch('',failure='FAILED');r=s.result('EXTERNAL_BLOCKER');self.assertIsNone(r.initial_candidate);self.assertEqual(r.physical_attempts,1)
    def test_every_termination_code(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'));s.dispatch('x')
            for code in TERMINATIONS:self.assertEqual(s.result(code).termination_reason,code)
            with self.assertRaises(ValueError):s.result('fake')
    def test_durable_candidate_resume(self):
        with temporary() as d:
            p=Path(d)/'l.json';s=MockSession(request(),Ledger(p));s.dispatch('exact\r\nbytes');s2=MockSession(request(),Ledger(p));self.assertEqual(s2.result().all_generated_candidates[0].answer,'exact\r\nbytes');self.assertEqual(s2.result().initial_candidate,'c0')
    def test_replay_deterministic_except_attempt_time(self):
        rows=[]
        for unused in range(2):
            with temporary() as d:
                s=MockSession(request(),Ledger(Path(d)/'l.json'));s.dispatch('x');r=s.result().data()
                for a in r['model_invocations']:a.pop('started_unix')
                rows.append(r)
        self.assertEqual(rows[0],rows[1])
    def test_cross_run_invocations_rejected(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'));s.dispatch('x');r=s.result();rows=[dict(r.model_invocations[0],run_id='wrong')]
            with self.assertRaises(ValueError):dataclasses.replace(r,model_invocations=tuple(rows)).validate()

    def test_nested_request_mutation_detected_before_dispatch(self):
        with temporary() as d:
            r=request();l=Ledger(Path(d)/'l.json');s=MockSession(r,l);r.public_task_payload['input']['word']='changed'
            with self.assertRaises(ValueError):s.dispatch('x')
            self.assertEqual(l.summary('run')['physical_attempts'],0)
    def test_candidate_attempt_identity_global_across_cells(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');a=MockSession(request(run_id='a'),l);b=MockSession(request(run_id='b'),l);a.dispatch('a');b.dispatch('b')
            self.assertEqual(b.result().all_generated_candidates[0].attempt_id,2)

    def test_approved_input_display_order_preserved(self):
        from src.public_runner.render import render_public_prompt
        t=task();t['input']={'z_first':1,'a_second':2};r=request(public_task_payload=t);prompt=render_public_prompt(r.public_task_payload)
        self.assertLess(prompt.index('z_first'),prompt.index('a_second'))
