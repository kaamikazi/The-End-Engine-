"""IR101 eligibility controls; no reviewer assertions or scientific fixtures altered."""
from .common import *
import copy
from src.shared.provenance import RecoveryIntegrityHold,publish_verified
from src.shared.certification import disposition,EvidenceDisposition,require_certification_eligible


def mutate_ledger(d,change):
    p=Path(d)/'budget.json';v=read(p);change(v['state']['attempts']);v['state_sha256']=sha(canonical(v['state']));p.write_bytes(canonical(v));return p.read_bytes()


class CertificationTests(unittest.TestCase):
    def blocked(self,change):
        with temporary() as d:
            d=Path(d);q,s=partial(d);s.detach();before=mutate_ledger(d,change)
            independent={p:p.read_bytes() for p in (d/'publication/attempts').glob('*')};independent.update({p:p.read_bytes() for p in (d/'wire').glob('*')})
            script=Script({})
            with patch.object(Publication,'publish',side_effect=AssertionError('BLOCKED must not invoke normal publication')):
                r=execute(q,script,d)
            self.assertEqual(r['status'],'BLOCKED');self.assertFalse(r['is_completed_result']);self.assertEqual(r['journal_integrity']['overall'],'BLOCKED')
            self.assertTrue(r['journal_integrity']['requires_integrity_hold']);self.assertEqual(r['result']['termination_reason'],'EXTERNAL_BLOCKER')
            self.assertTrue(r['result']['diagnostic_errors'][0]['failed_attempt_identity_invariants']);self.assertEqual(script.seen,[])
            self.assertFalse((d/'RESULT.json').exists());self.assertEqual((d/'budget.json').read_bytes(),before);self.assertTrue(all(p.read_bytes()==b for p,b in independent.items()))

    def test_response_text_only(self):self.blocked(lambda rows:rows[0].update(response_text='changed external response'))
    def test_output_count_mismatch(self):self.blocked(lambda rows:rows[0].update(output_tokens=6))
    def test_total_count_mismatch(self):self.blocked(lambda rows:rows[0].update(total_tokens=16))
    def test_settlement_state_mismatch(self):self.blocked(lambda rows:rows[0].update(state='FAILED',candidate=None))
    def test_candidate_mismatch(self):self.blocked(lambda rows:rows[0]['candidate'].update(output_id='O_'+'b'*24))
    def test_duplicate(self):self.blocked(lambda rows:rows.append(copy.deepcopy(rows[0])))
    def test_missing_attempt(self):self.blocked(lambda rows:rows.clear())

    def test_direct_semantic_verifier_rejects_independently_blocked_data(self):
        with temporary() as d:
            q,s=partial(d);mutate_ledger(d,lambda rows:rows[0].update(response_text='changed'))
            with self.assertRaises(RecoveryIntegrityHold) as error:
                s.store.verify_semantics({'journal_integrity':{'overall':'VERIFIED'},'result':{'termination_reason':'COMPLETED'}})
            self.assertEqual(error.exception.report['overall'],'BLOCKED');self.assertIn('INDEPENDENT_CONTENT_OR_ACCOUNTING_MISMATCH',str(error.exception.report))
            self.assertFalse((Path(d)/'RESULT.json').exists())

    def test_direct_normal_publisher_cannot_bypass_F02(self):
        with temporary() as d:
            q,s=partial(d);mutate_ledger(d,lambda rows:rows[0].update(response_text='changed'))
            report=verify_journals(s.store);data={'journal_integrity':report,'result':{'termination_reason':'EXTERNAL_BLOCKER'}}
            with self.assertRaises(ArtifactIntegrity):s.store.publish(data)
            self.assertFalse((Path(d)/'RESULT.json').exists())

    def test_invalid_proposed_report_is_rejected(self):
        with temporary() as d:
            q,s=partial(d);report=verify_journals(s.store);data=s._build('INTERRUPTED',report);data['journal_integrity']=copy.deepcopy(report);data['journal_integrity']['overall']='BLOCKED'
            with self.assertRaises(ArtifactIntegrity):s.store.verify_semantics(data)
            self.assertFalse((Path(d)/'RESULT.json').exists())

    def test_unknown_report_is_not_success(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({}),d)
            spec={'run_id':q.run_id,'call_id':'CALL_INITIAL','task_id':q.task_id,'purpose':'INITIAL','instruction_id':'INITIAL','prior_output_ids':[],'observation_ids':[]};s.gateway.reserve_request(spec)
            report=verify_journals(s.store);self.assertEqual(disposition(report),EvidenceDisposition.UNCERTAIN)
            data=s._build('COMPLETED',report)
            with self.assertRaises(ArtifactIntegrity):s.store.publish(data)
            self.assertFalse((Path(d)/'RESULT.json').exists())

    def test_valid_unknown_interrupted_publication(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({}),d);spec={'run_id':q.run_id,'call_id':'CALL_INITIAL','task_id':q.task_id,'purpose':'INITIAL','instruction_id':'INITIAL','prior_output_ids':[],'observation_ids':[]};s.gateway.reserve_request(spec)
            r=s.finish('INTERRUPTED');self.assertEqual(r['journal_integrity']['overall'],'INTERRUPTED');self.assertIsNone(r['result']['total_tokens']);self.assertEqual(r['result']['termination_reason'],'INTERRUPTED');s.store.verify_completed()

    def test_valid_failed_and_rejected_receipts_still_publish(self):
        for value in (TimeoutError(),b'not valid provider JSON'):
            with self.subTest(value=type(value).__name__),temporary() as d:
                r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[value]}),d)
                self.assertEqual(r['journal_integrity']['overall'],'VERIFIED');self.assertEqual(r['result']['physical_attempts'],1);self.assertIsNone(r['result']['total_tokens']);self.assertTrue((Path(d)/'RESULT.json').exists())

    def test_valid_completed_result_idempotent(self):
        with temporary() as d:
            q,s=partial(d);r=s.finish('INTERRUPTED');before=(Path(d)/'RESULT.json').read_bytes();again=s.finish('INTERRUPTED');self.assertEqual(r['artifact_payload_sha256'],again['artifact_payload_sha256']);s.store.verify_completed();self.assertEqual((Path(d)/'RESULT.json').read_bytes(),before)

    def test_unsupported_disposition_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'UNRECOGNIZED_JOURNAL_DISPOSITION'):disposition({'overall':'UNSUPPORTED'})

    def test_four_concurrent_blocked_recoveries_do_not_publish(self):
        with temporary() as d:
            d=Path(d);q,s=partial(d);s.detach();before=mutate_ledger(d,lambda rows:rows[0].update(response_text='changed'))
            code="import sys,time,json;from pathlib import Path;sys.path[:0]=[sys.argv[1],sys.argv[2]];from tests.corrections.common import request,Script;from src.shared.session import execute;d=Path(sys.argv[3]);s=Script({});r=execute(request('SPARSE_DELIBERATION'),s,d);assert not s.seen;assert r['status']=='BLOCKED' and not r['is_completed_result'];(d/(sys.argv[4]+'.out.json')).write_text(json.dumps({'status':r['status'],'calls':len(s.seen)}))"
            children=[subprocess.Popen([sys.executable,'-B','-c',code,str(OUT),str(ROOT),str(d),str(i)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for i in range(4)]
            outputs=[collect(p) for p in children];self.assertTrue(all(x['exit_code']==0 for x in outputs),outputs)
            self.assertFalse((d/'RESULT.json').exists());self.assertEqual((d/'budget.json').read_bytes(),before);self.assertEqual(len(list((d/'publication/recovery_holds').glob('*.json'))),4)

    def test_genuine_programming_defects_remain_visible(self):
        with temporary() as d:
            q,s=partial(d)
            with patch('src.shared.journals.verify_journals',side_effect=RuntimeError('implementation defect')):
                with self.assertRaisesRegex(RuntimeError,'implementation defect'):require_certification_eligible(s.store,{'journal_integrity':{},'result':{}})
