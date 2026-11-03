import dataclasses,json,unittest
from tests.helpers import *
from src.trusted_transport.transport import GenerationClosed,DuplicateDispatch,TransportFailure
from src.evaluation_firewall.firewall import EvaluationPlane
class RestartTests(unittest.TestCase):
    def test_interrupted_construction_before_reservation(self):
        with temporary() as d:
            e=Env(d)
            with self.assertRaises(BoundaryError):e.gateway.reserve_request({'call_id':'partial'})
            self.assertEqual(e.ledger.state()['attempts'],[])
    def test_interruption_after_reservation_survives_restart(self):
        with temporary() as d:
            e=Env(d)
            with self.assertRaises(KeyboardInterrupt):e.gateway.reserve_request(spec(),interrupt_after_reserve=True)
            g=e.restart()
            with self.assertRaises(BudgetStop):g.reserve_request(spec('c2'))
            self.assertEqual(g.ledger.summary('run')['physical_attempts'],1);self.assertEqual(g.ledger.state()['attempts'][0]['state'],'RESERVED')
    def test_no_replay_after_crash(self):
        with temporary() as d:
            e=Env(d);e.gateway.reserve_request(spec());g=e.restart()
            with self.assertRaises(DuplicateDispatch):g.reserve_request(spec())
            self.assertEqual(g.transport.sent,[])
    def test_old_seal_cannot_cross_restart(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec());g=e.restart()
            with self.assertRaises(BoundaryError):g.dispatch(s)
            self.assertEqual(g.transport.sent,[])
    def test_retry_path_revalidates(self):
        with temporary() as d:
            e=Env(d);e.send()
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec('c2',purpose='retry',instruction_id='PUBLIC_REVISION',tools=['shell']))
            self.assertEqual(e.ledger.summary('run')['physical_attempts'],1)
    def test_restart_path_revalidates(self):
        with temporary() as d:
            e=Env(d);e.send();g=e.restart()
            with self.assertRaises(BoundaryError):g.reserve_request(spec('c2',conversation_id='private'))
            self.assertEqual(g.ledger.summary('run')['physical_attempts'],1)
    def test_own_output_provenance_survives_restart(self):
        with temporary() as d:
            e=Env(d,responses=[response_bytes('first')]);a=e.send();g=e.restart();s=g.reserve_request(spec('c2',purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=[a['output_id']]));g.dispatch(s);self.assertIn('first',s.payload_bytes.decode());self.assertEqual(g.ledger.summary('run')['physical_attempts'],2)
    def test_missing_response_quarantined(self):
        with temporary() as d:
            e=Env(d,failure='MISSING')
            with self.assertRaises(BoundaryError):e.send()
            self.assertEqual(e.ledger.state()['attempts'][0]['state'],'PROTOCOL_FAILURE')
    def test_malformed_response_retained_host_only(self):
        with temporary() as d:
            e=Env(d,responses=[b'{broken'])
            with self.assertRaises(BoundaryError):e.send()
            a=e.ledger.state()['attempts'][0];self.assertEqual(a['response_text'],'{broken');self.assertIsNone(a.get('candidate'))
    def test_interrupted_exchange_counts(self):
        with temporary() as d:
            e=Env(d,failure='INTERRUPT')
            with self.assertRaises(KeyboardInterrupt):e.send()
            self.assertEqual(e.ledger.state()['attempts'][0]['state'],'INTERRUPTED')
            with self.assertRaises(BudgetStop):e.restart().reserve_request(spec('c2'))
    def test_closure_durable_prevents_new_generation(self):
        with temporary() as d:
            e=Env(d);e.send();closed=e.gateway.close_generation('run');g=e.restart()
            with self.assertRaises(GenerationClosed):g.reserve_request(spec('c2'))
            self.assertEqual(g.close_generation('run'),closed)
    def test_evaluation_requires_closed_generation(self):
        with temporary() as d:
            e=Env(d);e.send();plane=EvaluationPlane(e.gateway)
            with self.assertRaises(BoundaryError):plane.evaluate('run',{},lambda x:True)
    def test_posthoc_evaluation_cannot_feed_revision(self):
        with temporary() as d:
            e=Env(d);a=e.send();closed=e.gateway.close_generation('run');result=EvaluationPlane(e.gateway).evaluate('run',closed,lambda x:{'private_score':1})
            self.assertEqual(result.results[0][1],{'private_score':1})
            with self.assertRaises(GenerationClosed):e.gateway.reserve_request(spec('c2',purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=[a['output_id']]))
    def test_modified_closed_output_rejects(self):
        with temporary() as d:
            e=Env(d);e.send();c=e.gateway.close_generation('run');c['outputs'][0]['text']='changed'
            with self.assertRaises(BoundaryError):EvaluationPlane(e.gateway).evaluate('run',c,lambda x:True)
