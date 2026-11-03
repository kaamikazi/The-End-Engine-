import json,unittest
from tests.helpers import *
from src.trusted_transport.transport import DuplicateDispatch,TransportFailure
class AccountingTests(unittest.TestCase):
    def test_reserved_before_transport_captures_any_bytes(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec());a=e.ledger.state()['attempts'][0];self.assertEqual(a['state'],'RESERVED');self.assertEqual(e.transport.sent,[]);self.assertEqual(s.physical_call_reservation,a['attempt_id']);self.assertEqual(json.loads(a['purpose'])['wire_sha256'],sha(s.payload_bytes))
    def test_every_call_purpose_uses_same_boundary_and_counts(self):
        pairs=(('candidate','INITIAL'),('critique','PUBLIC_REVIEW'),('revision','PUBLIC_REVISION'),('alternative','PUBLIC_ALTERNATIVE'),('selection','PUBLIC_SELECTION'),('judge','PUBLIC_REVIEW'),('verification','PUBLIC_REVIEW'),('decision','PUBLIC_SELECTION'),('protocol_repair','PUBLIC_REVISION'),('retry','PUBLIC_REVISION'))
        with temporary() as d:
            e=Env(d)
            for i,(purpose,instruction) in enumerate(pairs):e.send(spec('c'+str(i),purpose=purpose,instruction_id=instruction))
            self.assertEqual(e.ledger.summary('run')['physical_attempts'],10);self.assertEqual(e.ledger.summary('run')['total_tokens'],50);self.assertEqual(len(e.transport.sent),10)
    def test_known_tokens_and_time_preserved(self):
        with temporary() as d:
            e=Env(d,responses=[response_bytes('x',7,11,.2)]);e.send();s=e.ledger.summary('run');self.assertEqual(s['total_tokens'],18);self.assertEqual(s['wall_time'],.2)
    def test_unknown_tokens_remain_unknown_and_block(self):
        with temporary() as d:
            e=Env(d,responses=[response_bytes('x',None,None,.01)]);e.send();self.assertIsNone(e.ledger.summary('run')['total_tokens'])
            with self.assertRaises(BudgetStop):e.gateway.reserve_request(spec('c2'))
    def test_unknown_active_time_blocks(self):
        with temporary() as d:
            e=Env(d,responses=[response_bytes('x',3,2,None)]);e.send()
            with self.assertRaises(BudgetStop):e.gateway.reserve_request(spec('c2'))
    def test_no_free_retry_after_known_success(self):
        with temporary() as d:
            e=Env(d);e.send();e.send(spec('c2',purpose='retry',instruction_id='PUBLIC_REVISION'));self.assertEqual(e.ledger.summary('run')['physical_attempts'],2)
    def test_global_cap_shared(self):
        with temporary() as d:
            e=Env(d,ledger_options={'global_attempts':1});e.gateway.register(request('other'));e.send()
            with self.assertRaises(BudgetStop):e.gateway.reserve_request(spec(run_id='other'))
    def test_per_run_cap(self):
        with temporary() as d:
            e=Env(d);limited=request('limited',attempt_budget=1);e.gateway.register(limited);e.send(spec(run_id='limited'))
            with self.assertRaises(BudgetStop):e.gateway.reserve_request(spec('c2',run_id='limited'))
    def test_token_reservation_refused_before_send(self):
        with temporary() as d:
            e=Env(d,ledger_options={'global_tokens':50})
            with self.assertRaises(BudgetStop):e.gateway.reserve_request(spec(),token_ceiling=100)
            self.assertEqual(e.transport.sent,[])
    def test_time_reservation_refused(self):
        with temporary() as d:
            e=Env(d,ledger_options={'global_seconds':.5})
            with self.assertRaises(BudgetStop):e.gateway.reserve_request(spec(),seconds_ceiling=1)
    def test_overrun_recorded_and_halts(self):
        with temporary() as d:
            e=Env(d,responses=[response_bytes('x',60,50,2)]);e.send();self.assertEqual(e.ledger.summary('run')['total_tokens'],110);self.assertTrue(e.ledger.state()['halted'])
            with self.assertRaises(BudgetStop):e.gateway.reserve_request(spec('c2'))
    def test_transport_failure_before_send_counts(self):
        with temporary() as d:
            e=Env(d,failure='BEFORE_SEND')
            with self.assertRaises(TransportFailure):e.send()
            self.assertEqual(e.ledger.summary('run')['physical_attempts'],1);self.assertEqual(e.transport.sent,[]);self.assertIsNone(e.ledger.summary('run')['total_tokens'])
    def test_after_send_failure_counts_and_retains_unknown(self):
        with temporary() as d:
            e=Env(d,failure='AFTER_SEND')
            with self.assertRaises(TransportFailure):e.send()
            self.assertEqual(len(e.transport.sent),1);self.assertEqual(e.ledger.summary('run')['physical_attempts'],1);self.assertIsNone(e.ledger.summary('run')['total_tokens'])
    def test_canceled_response_counts(self):
        with temporary() as d:
            e=Env(d,failure='CANCEL')
            with self.assertRaises(TransportFailure):e.send()
            self.assertEqual(e.ledger.state()['attempts'][0]['state'],'CANCELED')
    def test_duplicate_dispatch_rejected(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec());e.gateway.dispatch(s)
            with self.assertRaises(BoundaryError):e.gateway.dispatch(s)
            with self.assertRaises(DuplicateDispatch):e.gateway.reserve_request(spec())
            self.assertEqual(len(e.transport.sent),1);self.assertEqual(e.ledger.summary('run')['physical_attempts'],1)

    def test_concurrent_duplicate_reservations_are_serialized(self):
        import threading
        with temporary() as d:
            e=Env(d);barrier=threading.Barrier(2);out=[]
            def go():
                barrier.wait()
                try:e.gateway.dispatch(e.gateway.reserve_request(spec()));out.append('sent')
                except DuplicateDispatch:out.append('duplicate')
            threads=[threading.Thread(target=go) for i in range(2)]
            for t in threads:t.start()
            for t in threads:t.join(5)
            self.assertFalse(any(t.is_alive() for t in threads));self.assertEqual(sorted(out),['duplicate','sent']);self.assertEqual(len(e.transport.sent),1)
