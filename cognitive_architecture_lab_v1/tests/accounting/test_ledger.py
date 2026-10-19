import dataclasses,json,unittest
from pathlib import Path
from tests.helpers import request,temporary
from src.accounting.ledger import Ledger,BudgetStop
from src.public_runner.mock import MockSession
class AccountingTests(unittest.TestCase):
    def test_reservation_durable_before_dispatch(self):
        with temporary() as d:
            p=Path(d)/'l.json';l=Ledger(p);l.register(request());i=l.reserve('run','candidate',10,1);self.assertEqual(Ledger(p).state()['attempts'][0]['attempt_id'],i);self.assertEqual(Ledger(p).state()['attempts'][0]['state'],'RESERVED')
    def test_interruption_blocks_restart_budget_reset(self):
        with temporary() as d:
            p=Path(d)/'l.json';l=Ledger(p);l.register(request());l.reserve('run','candidate',10,1);l2=Ledger(p)
            with self.assertRaises(BudgetStop):l2.reserve('run','retry',10,1)
            self.assertEqual(l2.summary('run')['physical_attempts'],1)
    def test_all_physical_purposes_count(self):
        with temporary() as d:
            s=MockSession(request(),Ledger(Path(d)/'l.json'))
            for purpose in ('candidate','critique','decision','verification','alternative','protocol_repair','retry','selection','judge'):s.dispatch('x',purpose=purpose)
            for failure in ('FAILED','CANCELED','INTERRUPTED','PROTOCOL_FAILURE'):s.dispatch('',purpose='retry',failure=failure)
            r=s.result();self.assertEqual(r.physical_attempts,13);self.assertEqual(r.total_tokens,65)
    def test_per_run_attempt_cap(self):
        with temporary() as d:
            s=MockSession(request(attempt_budget=1),Ledger(Path(d)/'l.json'));s.dispatch('x')
            with self.assertRaises(BudgetStop):s.dispatch('second')
            self.assertEqual(s.ledger.summary('run')['physical_attempts'],1)
    def test_global_attempts_shared_across_runs(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json',global_attempts=1);a=MockSession(request(run_id='a'),l);b=MockSession(request(run_id='b'),l);a.dispatch('x')
            with self.assertRaises(BudgetStop):b.dispatch('x')
            self.assertEqual(len(l.state()['attempts']),1)
    def test_per_run_token_reservation_stop(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request(token_budget=9))
            with self.assertRaises(BudgetStop):l.reserve('run','candidate',10,1)
    def test_global_token_cap(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json',global_tokens=10);l.register(request());i=l.reserve('run','candidate',10,1);l.finish(i,state='SUCCEEDED',input_tokens=4,output_tokens=6,seconds=1)
            with self.assertRaises(BudgetStop):l.reserve('run','retry',1,1)
    def test_active_time_cap(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json',global_seconds=1);l.register(request());i=l.reserve('run','candidate',10,1);l.finish(i,state='SUCCEEDED',input_tokens=0,output_tokens=0,seconds=1)
            with self.assertRaises(BudgetStop):l.reserve('run','retry',1,.1)
    def test_per_run_time_cap(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request(wall_time_budget=1))
            with self.assertRaises(BudgetStop):l.reserve('run','candidate',1,2)
    def test_unknown_tokens_not_zero(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request());i=l.reserve('run','candidate',10,1);l.finish(i,state='FAILED',input_tokens=None,output_tokens=None,seconds=.5)
            s=l.summary('run');self.assertIsNone(s['total_tokens']);self.assertEqual(s['unknown_usage_attempts'],1)
            with self.assertRaises(BudgetStop):l.reserve('run','retry',1,.1)
    def test_unknown_time_blocks(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request());i=l.reserve('run','candidate',10,1);l.finish(i,state='CANCELED',input_tokens=0,output_tokens=0,seconds=None)
            with self.assertRaises(BudgetStop):l.reserve('run','retry',1,.1)
    def test_actual_usage_overrun_retained_and_halts(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request());i=l.reserve('run','candidate',1,1);l.finish(i,state='SUCCEEDED',input_tokens=1,output_tokens=2,seconds=2);self.assertEqual(l.summary('run')['total_tokens'],3);self.assertTrue(l.state()['halted'])
            with self.assertRaises(BudgetStop):l.reserve('run','retry',1,.1)
    def test_invalid_measured_times_and_tokens(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request());i=l.reserve('run','candidate',10,1)
            for x in (-1,True,float('nan'),float('inf')):
                with self.subTest(x=str(x)),self.assertRaises(ValueError):l.finish(i,state='SUCCEEDED',input_tokens=0,output_tokens=0,seconds=x)
            for x in (-1,True,1.5):
                with self.subTest(x=str(x)),self.assertRaises(ValueError):l.finish(i,state='SUCCEEDED',input_tokens=x,output_tokens=0,seconds=0)
            self.assertEqual(l.state()['attempts'][0]['state'],'RESERVED')
    def test_measured_zero_valid(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request());i=l.reserve('run','candidate',10,1);l.finish(i,state='FAILED',input_tokens=0,output_tokens=0,seconds=0);self.assertEqual(l.summary('run')['total_tokens'],0);self.assertEqual(l.summary('run')['wall_time'],0)
    def test_limits_cannot_reset_after_restart(self):
        with temporary() as d:
            p=Path(d)/'l.json';Ledger(p,global_attempts=2)
            with self.assertRaises(ValueError):Ledger(p,global_attempts=3)
    def test_run_contract_cannot_change_on_resume(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request())
            with self.assertRaises(ValueError):l.register(request(model_digest='different'))
    def test_response_and_candidate_durable(self):
        with temporary() as d:
            p=Path(d)/'l.json';s=MockSession(request(),Ledger(p));s.dispatch('raw\r\ntext');a=Ledger(p).state()['attempts'][0];self.assertEqual(a['response_text'],'raw\r\ntext');self.assertEqual(a['candidate']['candidate_id'],'c0')
    def test_response_hash_mismatch_rejects(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request());i=l.reserve('run','candidate',10,1)
            with self.assertRaises(ValueError):l.finish(i,state='SUCCEEDED',response_text='x',response_sha256='wrong')
    def test_settlement_cannot_be_overwritten(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');l.register(request());i=l.reserve('run','candidate',10,1);l.finish(i,state='FAILED',input_tokens=0,output_tokens=0,seconds=0)
            with self.assertRaises(ValueError):l.finish(i,state='SUCCEEDED',input_tokens=0,output_tokens=0,seconds=0)
    def test_corrupt_checkpoint_fail_closed(self):
        with temporary() as d:
            p=Path(d)/'l.json';l=Ledger(p);v=json.loads(p.read_text(encoding='utf-8'));v['state']['halted']=True;p.write_text(json.dumps(v),encoding='utf-8')
            with self.assertRaises(ValueError):Ledger(p)
    def test_failed_calls_not_deleted_on_new_cell(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');a=MockSession(request(run_id='a'),l);a.dispatch('',failure='FAILED');b=MockSession(request(run_id='b'),l);b.dispatch('x');self.assertEqual(len(l.state()['attempts']),2);self.assertEqual(l.summary('a')['physical_attempts'],1)
