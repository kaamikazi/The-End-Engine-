import unittest
from tests.helpers import *
class AccountingTests(unittest.TestCase):
    def test_direct_one_and_self_reflection_three(self):
        with temporary() as d:
            for condition,count in (('DIRECT',1),('SELF_REFLECT',3)):
                r=run_baseline(task(),condition,Path(d)/condition);self.assertEqual(r['physical_attempts'],count)
    def test_physical_retries_count_toward_36(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d,mode='all_repairs');self.assertEqual(r['physical_attempts'],36);self.assertEqual(r['termination_reason'],'BUDGET_EXHAUSTED');self.assertEqual(len(r['provider_records']),36)
    def test_failure_counted_unknown_usage(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d,mode='failure');self.assertEqual(r['physical_attempts'],1);self.assertEqual(r['termination_reason'],'EXTERNAL_BLOCKER');self.assertIsNone(r['accounting']['total_tokens'])
    def test_missing_usage_stops_before_second_request(self):
        with temporary() as d:
            r=run_baseline(task(),'SELF_REFLECT',d,mode='unknown_usage');self.assertEqual(r['physical_attempts'],1);self.assertIsNone(r['accounting']['total_tokens']);self.assertIsNotNone(r['C0'])
    def test_known_usage_totals_every_physical_attempt(self):
        with temporary() as d:
            r=run_baseline(task(),'FROZEN_CURRENT_END',d,mode='repair');self.assertEqual(r['accounting']['total_tokens'],15*r['physical_attempts'])
    def test_reservations_bound_to_actual_wire(self):
        with temporary() as d:
            r=run_baseline(task(),'SELF_REFLECT',d)
            for row,wire in zip(r['accounting']['attempts'],r['provider_records']):self.assertEqual(json.loads(row['purpose'])['wire_sha256'],wire['wire_sha256'])
    def test_restart_preserves_closure_and_counters(self):
        with temporary() as d:
            r=run_baseline(task(),'DIRECT',d);l=Ledger(Path(d)/'budget.json');self.assertEqual(len(l.state()['attempts']),1)
            with self.assertRaises(FileExistsError):run_baseline(task(),'DIRECT',d)
    def test_global_cap_not_only_native_engine_cap(self):
        with temporary() as d:
            r=run_baseline(task(),'SELF_REFLECT',d,global_attempts=1);self.assertEqual(r['physical_attempts'],1);self.assertEqual(r['termination_reason'],'BUDGET_EXHAUSTED')

    def test_shared_global_ledger_spans_baseline_conditions(self):
        with temporary() as d:
            l=Ledger(Path(d)/'shared.json',global_attempts=2);a=run_baseline(task(),'DIRECT',Path(d)/'a',run_id='a',shared_ledger=l);b=run_baseline(task(),'SELF_REFLECT',Path(d)/'b',run_id='b',shared_ledger=l)
            self.assertEqual(len(l.state()['attempts']),2);self.assertEqual(b['physical_attempts'],1);self.assertEqual(b['termination_reason'],'BUDGET_EXHAUSTED');self.assertIn('synthetic_wiring_only',b['C0'])
