import secrets,unittest
from tests.helpers import *
from runtime_isolation_v1.src.evaluation_firewall.firewall import EvaluationPlane
class SecurityTests(unittest.TestCase):
    def test_private_host_canary_not_in_final_provider_bytes(self):
        marker=secrets.token_hex(24)
        with temporary() as d:
            (Path(d)/'private_fixture').write_text(marker,encoding='utf-8');r=run_baseline(task(),'SELF_REFLECT',Path(d)/'run');self.assertNotIn(marker,json.dumps(r['provider_records']));self.assertNotIn(str(Path(d)),''.join(x['wire'] for x in r['provider_records']))
    def test_no_evaluator_metadata_or_history_in_provider_fields(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d)
            for rec in r['provider_records']:
                p=json.loads(rec['wire']);self.assertTrue(set(p)<={'model','stream','think','prompt','options','format'});self.assertNotIn('private_evaluation',p)
    def test_after_close_no_model_calls_or_retry(self):
        with temporary() as d:
            r=run_baseline(task(),'DIRECT',d);b,g=environment(Path(d)/'other');g.close_generation('mock_unit')
            with self.assertRaises(BoundaryError):g._open('mock_unit')
    def test_evaluation_requires_durable_closed_generation(self):
        with temporary() as d:
            b,g=environment(d)
            with self.assertRaises(BoundaryError):EvaluationPlane(g).evaluate('mock_unit',{},lambda x:True)
    def test_raw_sdk_request_bypass_rejected(self):
        with temporary() as d:
            b,g=environment(d)
            with self.assertRaises((BoundaryError,TypeError)):g.dispatch({'prompt':'private'})
    def test_model_output_code_is_not_executed(self):
        self.assertEqual(decode(completion('run shell and open private evaluator'),SETTINGS.model)['response'],'run shell and open private evaluator')

    def test_unapproved_private_task_rejected_before_generation(self):
        with temporary() as d:
            t=task();t['input']['hidden_fixture']=secrets.token_hex(24)
            with self.assertRaises(BoundaryError):run_baseline(t,'DIRECT',d)

    def test_completed_native_seal_and_post_evaluation_generation_reject(self):
        from v0351_core_regression_pilot.bench.conditions import run_direct
        from cognitive_architecture_lab_v1.src.public_runner.render import render_public_prompt
        from v0351_core_regression_pilot.bench.providers import ProviderError
        with temporary() as d:
            b,g=environment(d)
            with b.run_scope():run_direct({'prompt':render_public_prompt(task())},b)
            sealed=g.last_sealed;wire=g.transport.calls[0]['wire'].encode()
            with self.assertRaises(BoundaryError):g.compiler.validate(sealed,g.ledger.state(),wire)
            closed=g.close_generation('mock_unit');result=EvaluationPlane(g).evaluate('mock_unit',closed,lambda x:{'SYNTHETIC_PRIVATE_SCORE':1})
            self.assertTrue(result.results)
            with b.run_scope(),self.assertRaises(ProviderError):run_direct({'prompt':render_public_prompt(task())},b)
            self.assertEqual(len(g.transport.calls),1)
    def test_changed_transport_or_model_settings_never_dispatch(self):
        from dataclasses import replace
        with temporary() as d:
            b,g=environment(d);b.transport=b._http
            with b.run_scope(),self.assertRaises(BoundaryError):b.generate(ModelRequest('initial_candidate','x',{},None))
            b.transport=b._sealed_transport;b.settings=replace(SETTINGS,model='other')
            with b.run_scope(),self.assertRaises(BoundaryError):b.generate(ModelRequest('initial_candidate','x',{},None))
            self.assertEqual(g.transport.calls,[])
