import unittest
from tests.helpers import *
COMPONENT_RECORDS=[]
class NativeEngineTests(unittest.TestCase):
    def test_actual_three_cycle_engine_not_simplified(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d,mode='three_cycles');self.assertIsNone(r['error']);self.assertEqual(r['iterations'],3);self.assertEqual(r['engine_trajectory']['configuration']['overrides']['max_cycles'],3)
    def test_all_actual_attempts_intercepted(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d);self.assertEqual(r['physical_attempts'],len(r['provider_records']));self.assertEqual(r['physical_attempts'],len(r['sealed_requests']));self.assertEqual(r['physical_attempts'],len(r['historical_adapter_call_log']));self.assertTrue(all(a['state']=='SUCCEEDED' for a in r['accounting']['attempts']))
    def test_primary_adversarial_verifier_and_revision_all_bridge(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d);self.assertTrue({'initial_candidate','critique','revision_plan','revision','judgment','adversarial_judgment','adversarial_tests','comparison','verification'}<={a['purpose'] for a in r['provider_records']})
    def test_two_provider_failures_then_engine_protocol_repair(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d,mode='repair');self.assertTrue(any(a['protocol_repair'] for a in r['sealed_requests']));rows=[a for a in r['provider_records'] if a['purpose']=='critique'];self.assertEqual(json.loads(rows[0]['response'])['response'],'not valid JSON');self.assertEqual(json.loads(rows[1]['response'])['response'],'not valid JSON');self.assertGreaterEqual(len(rows),3)
    def test_no_progress_real_engine_stop(self):
        with temporary() as d:
            r=run_baseline(task('Inspect a bounded architecture proposal. No execution occurred.'),'FROZEN_CURRENT_END',d,mode='no_progress');self.assertEqual(r['termination_reason'],'NO_PROGRESS')
    def test_native_c0_is_generated_not_task_input(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d);self.assertIsNotNone(r['C0']);self.assertIn('synthetic_wiring_only',r['C0']);self.assertNotEqual(r['C0'],r['complete_public_request'])
    def test_source_manifest_is_verified(self):self.assertGreater(len(verify_sources()),70)
    def test_standalone_call_without_approved_scope_rejects(self):
        with temporary() as d:
            b,g=environment(d)
            with self.assertRaises(BoundaryError):b.generate(ModelRequest('initial_candidate','private',{},None))
    def test_call_from_untrusted_origin_inside_scope_rejects(self):
        with temporary() as d:
            b,g=environment(d)
            with b.run_scope(),self.assertRaises(BoundaryError):b.generate(ModelRequest('initial_candidate','private',{},None))
    def test_legacy_http_fallback_cannot_be_selected(self):
        with temporary() as d:
            b,g=environment(d);self.assertEqual(b.transport,b._sealed_transport);self.assertEqual(b.metadata()['data_origin'],'MOCK_WIRING_ONLY');self.assertIsNone(b.metadata()['digest']);self.assertIsNone(b.metadata()['server_version'])
            with self.assertRaises(BoundaryError):b._http({})

    def test_invalid_reference_repair_reaches_gateway(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d,mode='invalid_reference');self.assertTrue(any(s['protocol_repair'] for s in r['sealed_requests']))
    def test_existing_branch_components_use_injected_provider(self):
        from end_engine import EngineConfig
        from end_engine.experience import Trajectory
        from end_engine.core.task_analyzer import TaskAnalyzer
        from end_engine.cognition.session import CognitiveSession
        from end_engine.cognition.branches import BranchController
        from end_engine.operators import default_operators
        from end_engine.core.state import Candidate,to_data
        from cognitive_architecture_lab_v1.src.public_runner.render import render_public_prompt
        t=json.loads((OUT/'public_inputs/EXP-001.json').read_text(encoding='utf-8'));prompt=render_public_prompt(t)
        with temporary() as d:
            b,g=environment(d,t=t);config=EngineConfig(candidate_generation='native',quality_evaluation=True,max_run_calls=36);analysis=TaskAnalyzer().analyze(prompt,max_cycles=3);trace=Trajectory(prompt,{},b.metadata());trace.set('analysis',to_data(analysis));session=CognitiveSession(analysis,config,trace);controller=BranchController(config,trace,session)
            with b.run_scope():controller.explore(prompt,Candidate('C0',None,0,'SYNTHETIC COMPONENT', ''),default_operators()['ALTERNATIVE'],None,analysis.dimensions,b)
            COMPONENT_RECORDS.extend(g.seals);purposes={x['purpose'] for x in g.transport.calls};self.assertTrue({'branch_generation','branch_evaluation','synthesis'}<=purposes)
    def test_all_six_initial_public_wires_equal_without_variant_loops(self):
        from cognitive_architecture_lab_v1.src.interfaces.contracts import CONDITIONS
        from cognitive_architecture_lab_v1.src.public_runner.render import render_public_prompt
        from v0351_core_regression_pilot.bench.conditions import run_direct
        for tid in ('EXP-001','EXP-002'):
            t=json.loads((OUT/'public_inputs'/(tid+'.json')).read_text(encoding='utf-8'));wires=[]
            with temporary() as d:
                for c in CONDITIONS:
                    b,g=environment(Path(d)/c,t=t,condition=c)
                    with b.run_scope():run_direct({'prompt':render_public_prompt(t)},b)
                    wires.append(g.transport.calls[0]['wire'])
            self.assertEqual(len(set(wires)),1)
