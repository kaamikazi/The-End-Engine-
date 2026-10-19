import unittest
from tests.helpers import *
from src.capability_policy.contamination import ExposureCategory,ContaminationDecision,validate_external_decision,automatic_scientific_signoff
from src.evaluation_firewall.firewall import PrivateEvaluation
class ContaminationTests(unittest.TestCase):
    def record(self):return {'decision':'ACCEPT_WITH_LIMITATIONS','custodian':'SYNTHETIC_ONLY','reviewer_identity':'SYNTHETIC_REVIEWER_NOT_A_PERSON','basis':'Test-only sample, not real approval','exposure_ledger_sha256':'a'*64,'scope':'SYNTHETIC_TEST','signed_record_reference':'SYNTHETIC_NO_REAL_SIGNATURE'}
    def validate(self,v,auth):return validate_external_decision(v,authenticate=auth,expected_exposure_sha256='a'*64,expected_scope='SYNTHETIC_TEST')
    def test_stable_correctly_spelled_exposure_enums(self):self.assertEqual({x.value for x in ExposureCategory},{'HISTORICAL_EXPOSURE','CURRENT_RUNTIME_LEAKAGE','FUTURE_MODEL_PRIOR_CONTAMINATION'})
    def test_no_automatic_scientific_signoff(self):
        with self.assertRaises(BoundaryError):automatic_scientific_signoff()
    def test_unverified_custodian_rejected(self):
        with self.assertRaises(BoundaryError):self.validate(self.record(),lambda x:False)
    def test_plain_status_is_not_signature(self):
        with self.assertRaises(BoundaryError):self.validate({'decision':'ACCEPT_WITH_LIMITATIONS'},lambda x:True)
    def test_decision_binds_exact_exposure_and_scope(self):
        for changed in ({'exposure_ledger_sha256':'b'*64},{'scope':'other'}):
            with self.subTest(changed=changed),self.assertRaises(BoundaryError):self.validate(self.record()|changed,lambda x:True)
    def test_accept_and_block_are_both_explicit_external_choices(self):
        for d in ContaminationDecision:
            # Test authenticator is a deterministic stub, never claimed actual identity verification.
            self.assertEqual(self.validate(self.record()|{'decision':d.value},lambda x:True),d)
    def test_scientific_decision_metadata_not_generation_input(self):
        with temporary() as d:
            e=Env(d)
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(contamination_decision=self.record()))
            self.assertEqual(e.transport.sent,[])
    def test_private_evaluation_object_rejects_as_prior_output(self):
        with temporary() as d:
            e=Env(d)
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=[PrivateEvaluation('run',(('x',1),))]))
