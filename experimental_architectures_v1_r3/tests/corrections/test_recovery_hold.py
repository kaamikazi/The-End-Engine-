"""F02 blocked-response contract. All corrupt inputs remain untouched."""
from .common import *
import base64,copy


class RecoveryHoldTests(unittest.TestCase):
    def mutate(self, name, mutation, second=False, interrupted=False, completed=False):
        with temporary() as d:
            d=Path(d)
            if interrupted:
                q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[KeyboardInterrupt()]}),d)
                with self.assertRaises(KeyboardInterrupt):s.generate('INITIAL')
            else:q,s=partial(d)
            if second:
                s.transport.script=Script({'SPARSE_GATE':[gate()]});s.assess('SPARSE_GATE',(s.outputs['INITIAL'],))
            if completed:s.finish('INTERRUPTED')
            else:s.detach()
            original_settlements={p.name:p.read_bytes() for p in (d/'publication/attempts').glob('*.settlement.json')}
            p=d/'budget.json';v=read(p);mutation(v['state']['attempts'],s);v['state_sha256']=sha(canonical(v['state']));p.write_bytes(canonical(v))
            preserved={p:p.read_bytes() for p in d.rglob('*') if p.is_file() and
                       (p in (d/'budget.json',d/'budget.closed.json',d/'RESULT.json') or
                        p.is_relative_to(d/'wire') or p.is_relative_to(d/'publication/attempts'))}
            script=Script({});r=execute(q,script,d)
            self.assertEqual(r['journal_integrity']['overall'],'BLOCKED',name);self.assertEqual(script.seen,[])
            self.assertEqual(r['result']['termination_reason'],'EXTERNAL_BLOCKER')
            if r.get('is_completed_result') is False:
                self.assertEqual(r['status'],'BLOCKED');self.assertIsNone(r['result']['physical_attempts']);self.assertIsNone(r['result']['total_tokens'])
                self.assertTrue(r['result']['diagnostic_errors'][0]['failed_attempt_identity_invariants'])
                self.assertEqual(base64.b64decode(r['candidate_history']['ledger_observation']['raw_base64']),p.read_bytes())
                witness={Path(x['path']).name:base64.b64decode(x['raw_base64']) for x in r['candidate_history']['independent_settlement_observations']}
                self.assertEqual(witness,original_settlements)
                self.assertTrue(Path(r['diagnostic_record']).is_file())
            self.assertTrue(all(p.read_bytes()==b for p,b in preserved.items()))
            if not completed and r.get('is_completed_result') is False:self.assertFalse((d/'RESULT.json').exists())
            if completed:
                self.assertEqual((d/'RESULT.json').read_bytes(),preserved[d/'RESULT.json'])
                with self.assertRaises(ArtifactIntegrity):s.store.verify_completed()
            return r

    def test_one_duplicate(self):self.mutate('duplicate',lambda rows,s:rows.append(copy.deepcopy(rows[0])))
    def test_duplicate_different_settlement(self):
        def change(rows,s):
            v=copy.deepcopy(rows[0]);v.update(state='FAILED',candidate=None);rows.append(v)
        self.mutate('conflicting duplicate',change)
    def test_duplicated_reservation(self):
        def change(rows,s):
            v=copy.deepcopy(rows[0]);v.update(state='RESERVED',candidate=None,total_tokens=None);rows.append(v)
        self.mutate('reservation',change)
    def test_reordered_sequence(self):self.mutate('order',lambda rows,s:rows.reverse(),second=True)
    def test_missing_attempt(self):self.mutate('missing',lambda rows,s:rows.clear())
    def test_conflicting_response_anchor(self):
        def change(rows,s):
            p=s.store.response_anchor(1);v=read(p);v['last_sha256']='0'*64;p.write_bytes(canonical(v))
        self.mutate('response',change)
    def test_refreshed_ledger_checksum_not_authority(self):self.mutate('checksum',lambda rows,s:rows.append(copy.deepcopy(rows[0])))
    def test_duplicate_after_interruption(self):self.mutate('interrupted',lambda rows,s:rows.append(copy.deepcopy(rows[0])),interrupted=True)
    def test_completed_result_is_never_replaced(self):self.mutate('completed',lambda rows,s:rows.append(copy.deepcopy(rows[0])),completed=True)
    def test_duplicate_inserted_at_recovery_entry(self):
        original=Session.restore_without_dispatch
        with temporary() as d:
            q,s=partial(d);s.detach();script=Script({})
            def changed(session):
                p=session.ledger.path;v=read(p);v['state']['attempts'].append(copy.deepcopy(v['state']['attempts'][0]));v['state_sha256']=sha(canonical(v['state']));p.write_bytes(canonical(v));return original(session)
            with patch.object(Session,'restore_without_dispatch',changed):r=execute(q,script,d)
            self.assertEqual(r['journal_integrity']['overall'],'BLOCKED');self.assertEqual(script.seen,[]);self.assertFalse((Path(d)/'RESULT.json').exists())
    def test_valid_interrupted_is_not_converted(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[KeyboardInterrupt()]}),d)
            with self.assertRaises(KeyboardInterrupt):s.generate('INITIAL')
            s.detach();script=Script({});r=execute(q,script,d)
            self.assertNotEqual(r['journal_integrity']['overall'],'BLOCKED');self.assertNotIn('is_completed_result',r);self.assertEqual(script.seen,[])
    def test_valid_failed_is_not_converted(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[TimeoutError()]}),d)
            from runtime_isolation_v1.src.trusted_transport.transport import TransportFailure
            with self.assertRaises(TransportFailure):s.generate('INITIAL')
            s.detach();script=Script({});r=execute(q,script,d)
            self.assertNotIn('is_completed_result',r);self.assertEqual(script.seen,[]);self.assertEqual(r['result']['physical_attempts'],1)
    def test_corrupt_journal_finalization_remains_blocked(self):
        with temporary() as d:
            q,s=partial(d);p=journal(d);p.write_bytes(p.read_bytes()+b'corrupt\n');before=p.read_bytes();r=s.finish('INTERRUPTED')
            self.assertEqual(r['journal_integrity']['overall'],'BLOCKED');self.assertEqual(p.read_bytes(),before)
    def test_unrelated_programming_defect_propagates(self):
        with temporary() as d:
            with patch('src.shared.session.verify_journals',side_effect=RuntimeError('unrelated programming defect')):
                with self.assertRaisesRegex(RuntimeError,'unrelated programming defect'):execute(request('SPARSE_DELIBERATION'),Script({}),d)
    def test_generic_integrity_error_not_swallowed(self):
        with temporary() as d:
            with patch('src.shared.session.Session',side_effect=ArtifactIntegrity('F01 synthetic failure')):
                with self.assertRaisesRegex(ArtifactIntegrity,'F01 synthetic failure'):execute(request('SPARSE_DELIBERATION'),Script({}),d)
