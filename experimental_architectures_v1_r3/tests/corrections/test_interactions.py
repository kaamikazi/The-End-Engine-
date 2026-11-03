from .common import *
from src.shared.session import UnknownCost
class CrossDefectTests(unittest.TestCase):
    def test_corrupt_journal_then_stale_finalization_cannot_replace_blocked_record(self):
        with temporary() as d:
            q,s=partial(d);p=journal(d);p.write_bytes(p.read_bytes()+b'{"bad":true}\n');stale=Session(q,Script({}),d);r=s.finish('INTERRUPTED');before=(Path(d)/'RESULT.json').read_bytes();again=stale.finish('COMPLETED');self.assertEqual(r['journal_integrity']['overall'],'BLOCKED');self.assertEqual(before,(Path(d)/'RESULT.json').read_bytes());self.assertEqual(again['result']['termination_reason'],'EXTERNAL_BLOCKER');evidence(self,'INTERACTIONS',journal_blocker_preserved=True,result_immutable=True)
    def test_simultaneous_finalizers_with_missing_journal_keep_failure_explicit(self):
        with temporary() as d:
            q,s=partial(d);journal(d).rename(journal(d).with_suffix('.missing'));s.detach();a=worker('finalize',d,'a','INTERRUPTED');b=worker('finalize',d,'b','COMPLETED');wait(Path(d)/'a.ready');wait(Path(d)/'b.ready');(Path(d)/'go').write_text('go');ra=collect(a);rb=collect(b);self.assertEqual(ra['exit_code'],0,ra);self.assertEqual(rb['exit_code'],0,rb);r=read(Path(d)/'RESULT.json');self.assertEqual(r['journal_integrity']['overall'],'BLOCKED');self.assertEqual(r['result']['termination_reason'],'EXTERNAL_BLOCKER');self.assertEqual(len(list((Path(d)/'publication/prepared').glob('*.json'))),1);evidence(self,'INTERACTIONS',processes=[ra,rb],overall='BLOCKED',one_terminal_record=True)
    def test_unknown_usage_survives_interrupted_recovery(self):
        from tests.helpers import unknown
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[unknown(complete())]}),d)
            with self.assertRaises(UnknownCost):s.generate('INITIAL')
            s.detach();script=Script({});r=execute(q,script,d);self.assertEqual(script.seen,[]);self.assertIsNone(r['result']['total_tokens']);self.assertEqual(r['result']['physical_attempts'],1);self.assertTrue(r['generation_closed']['outstanding_or_unknown_cost'])
    def test_malformed_receipt_and_duplicate_recovery_keep_unknown_cost(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');r=execute(q,Script({'INITIAL':[b'{"model":"qwen3:4b","response":']}),d);before=(Path(d)/'RESULT.json').read_bytes();self.assertIsNone(r['result']['total_tokens'])
            with self.assertRaises(FileExistsError):Session(q,Script({}),d)
            self.assertEqual(before,(Path(d)/'RESULT.json').read_bytes())
    def test_completed_result_ignores_late_error_without_rewriting(self):
        with temporary() as d:
            q,s=partial(d);r=s.finish('INTERRUPTED');before=(Path(d)/'RESULT.json').read_bytes();s.errors.append({'code':'LATE_PROVIDER_ERROR'});again=s.finish('EXTERNAL_BLOCKER');self.assertEqual(before,(Path(d)/'RESULT.json').read_bytes());self.assertEqual(r['artifact_payload_sha256'],again['artifact_payload_sha256'])
    def test_serializer_fallback_does_not_conceal_journal_failure(self):
        with temporary() as d:
            q,s=partial(d);p=journal(d);p.write_bytes(p.read_bytes()+b'corruption\n');s.notes.append(float('nan'));r=s.finish('INTERRUPTED');self.assertEqual(r['result']['termination_reason'],'PROTOCOL_FAILURE');self.assertEqual(r['journal_integrity']['overall'],'BLOCKED');self.assertIn('JOURNAL_INTEGRITY_BLOCKER',json.dumps(r['result']['diagnostic_errors']));canonical(r)
    def test_completed_result_and_corrupt_closure_fail_closed(self):
        with temporary() as d:
            q,r=finish_good(d);before=(Path(d)/'RESULT.json').read_bytes();file=Path(d)/'budget.closed.json';env=read(file);env['sha256']='0'*64;file.write_text(json.dumps(env),encoding='utf-8')
            with self.assertRaises(ArtifactIntegrity):Session(q,Script({}),d)
            self.assertEqual(before,(Path(d)/'RESULT.json').read_bytes())
    def test_rehashed_result_cannot_replace_independent_prepared_anchor(self):
        with temporary() as d:
            q,r=finish_good(d);path=Path(d)/'RESULT.json';data=read(path);data['result']['termination_reason']='INTERRUPTED';data.pop('artifact_payload_sha256');data['artifact_payload_sha256']=sha(canonical(data));path.write_text(json.dumps(data),encoding='utf-8');damaged=path.read_bytes()
            with self.assertRaises(ArtifactIntegrity):Session(q,Script({}),d)
            self.assertEqual(path.read_bytes(),damaged)
