import unittest
from tests.helpers import *
class ReplayTests(unittest.TestCase):
    def test_synthetic_namespace_no_scoring(self):
        with temporary() as d:
            r=run_baseline(task(),'DIRECT',d);self.assertEqual(r['namespace'],'MOCK_WIRING_ONLY_NOT_EMPIRICAL');self.assertTrue(r['no_scoring_performed']);self.assertTrue(r['generation_closed'])
    def test_same_canned_control_flow_replayed_without_changing_engine_time(self):
        with temporary() as d:
            a=run_baseline(task(),'FROZEN_CURRENT_END',Path(d)/'a');b=run_baseline(task(),'FROZEN_CURRENT_END',Path(d)/'b');self.assertEqual([c['purpose'] for c in a['provider_records']],[c['purpose'] for c in b['provider_records']]);self.assertEqual(a['C0'],b['C0']);self.assertEqual(a['FINAL'],b['FINAL'])
    def test_stored_wire_bytes_hash_exact_replay(self):
        with temporary() as d:
            r=run_baseline(task(),'SELF_REFLECT',d)
            for c in r['provider_records']:self.assertEqual(sha(c['wire'].encode()),c['wire_sha256'])
