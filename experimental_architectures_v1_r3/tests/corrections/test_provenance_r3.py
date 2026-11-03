"""Fresh deterministic F02 graph controls; no scientific answers changed."""
from .common import *
from src.shared.provenance import settlement_path
from src.shared.strict_json import loads
import copy

class ProvenanceGraphTests(unittest.TestCase):
    def mutated(self, name, mutate, second=False):
        with temporary() as d:
            q,s=partial(d)
            if second:
                s.transport.script=Script({'SPARSE_GATE':[gate()]})
                s.assess('SPARSE_GATE',(s.outputs['INITIAL'],))
            path=Path(d)/'budget.json';envelope=read(path)
            independent={p.relative_to(d).as_posix():p.read_bytes()
                         for p in Path(d).rglob('*') if p.is_file() and
                         (p.is_relative_to(Path(d)/'wire') or p.is_relative_to(Path(d)/'publication/attempts'))}
            mutate(envelope['state']['attempts'],s)
            envelope['state_sha256']=sha(canonical(envelope['state']))
            path.write_bytes(canonical(envelope))
            report=verify_journals(s.store)
            self.assertNotEqual(report['overall'],'VERIFIED',name)
            s.detach();script=Script({})
            try:
                result=execute(q,script,d)
            except (ArtifactIntegrity,ValueError):
                result=None
            if result is not None:
                self.assertEqual(result['journal_integrity']['overall'],'BLOCKED')
            self.assertEqual(script.seen,[])
            self.assertTrue(all((Path(d)/n).read_bytes()==b for n,b in independent.items()
                                if (Path(d)/n).exists()))

    def test_A_success_downgraded_failed(self):
        self.mutated('AR01',lambda a,s:a[0].update(state='FAILED',candidate=None))

    def test_B_candidate_removed(self):
        self.mutated('candidate removed',lambda a,s:a[0].update(candidate=None))

    def test_C_success_changed_interrupted(self):
        self.mutated('interrupted',lambda a,s:a[0].update(state='INTERRUPTED',candidate=None))

    def test_D_changed_handle(self):
        self.mutated('AR02',lambda a,s:a[0]['candidate'].update(output_id='O_'+'a'*24))

    def test_E_changed_content_same_handle(self):
        self.mutated('content',lambda a,s:a[0].update(response_text='changed',response_sha256=sha(b'changed')))

    def test_F_later_request_quotes_old_handle(self):
        self.mutated('old reference',lambda a,s:a[0]['candidate'].update(output_id='O_'+'b'*24),True)

    def test_G_duplicate_handle(self):
        self.mutated('duplicate handle',lambda a,s:a[1]['candidate'].update(output_id=a[0]['candidate']['output_id']),True)

    def test_H_handle_reassigned_attempt(self):
        self.mutated('attempt binding',lambda a,s:a[0].update(attempt_id=2))

    def test_I_foreign_run_identity(self):
        self.mutated('foreign run',lambda a,s:a[0].update(run_id='foreign_run'))

    def test_J_duplicate_attempt(self):
        self.mutated('AR03 duplicate',lambda a,s:a.append(copy.deepcopy(a[0])))

    def test_K_reordered_attempts(self):
        self.mutated('AR03 order',lambda a,s:a.reverse(),True)

    def test_L_duplicate_ordinal(self):
        self.mutated('ordinal',lambda a,s:a[1].update(attempt_id=1),True)

    def test_M_changed_stage(self):
        def change(a,s):
            value=loads(a[0]['purpose']);value['purpose']='SPARSE_GATE';a[0]['purpose']=canonical(value).decode()
        self.mutated('stage',change)

    def test_N_swapped_response_anchor(self):
        with temporary() as d:
            q,s=partial(d);s.transport.script=Script({'SPARSE_GATE':[gate()]});s.assess('SPARSE_GATE',(s.outputs['INITIAL'],))
            p=s.store.response_anchor(1);p.write_bytes(s.store.response_anchor(2).read_bytes())
            self.assertEqual(verify_journals(s.store)['overall'],'BLOCKED')

    def test_O_missing_dispatch_evidence(self):
        with temporary() as d:
            q,s=partial(d);s.store.attempt_anchor(1).rename(Path(d)/'preserved-dispatch.json')
            self.assertEqual(verify_journals(s.store)['overall'],'BLOCKED')

    def test_P_missing_response_evidence(self):
        with temporary() as d:
            q,s=partial(d);s.store.response_anchor(1).rename(Path(d)/'preserved-response.json')
            self.assertEqual(verify_journals(s.store)['overall'],'BLOCKED')

    def test_Q_refreshed_ledger_checksum_is_insufficient(self):
        self.mutated('checksum',lambda a,s:a[0].update(state='FAILED',candidate=None,total_tokens=None))

    def test_R_erased_attempt_leaves_orphan_anchor(self):
        self.mutated('erased',lambda a,s:a.clear())

    def test_S_interrupted_attempt_remains_uncertain(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[KeyboardInterrupt()]}),d)
            with self.assertRaises(KeyboardInterrupt):s.generate('INITIAL')
            r=s.finish('INTERRUPTED');self.assertIsNone(r['result']['total_tokens'])
            self.assertNotEqual(r['journal_integrity']['overall'],'BLOCKED')

    def test_T_transport_failure_retained(self):
        with temporary() as d:
            r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[TimeoutError()]}),d)
            self.assertEqual(r['result']['physical_attempts'],1)
            self.assertEqual(r['result']['model_invocations'][0]['state'],'FAILED')

    def test_U_rejected_raw_provider_response_retained(self):
        with temporary() as d:
            r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[b'not JSON']}),d)
            self.assertEqual(r['result']['model_invocations'][0]['state'],'FAILED')
            self.assertTrue(list((Path(d)/'wire').glob('*.jsonl')))

    def test_V_unknown_usage_stays_unknown(self):
        from tests.helpers import unknown
        with temporary() as d:
            r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[unknown(complete())]}),d)
            self.assertIsNone(r['result']['total_tokens'])

    def test_W_torn_journal_remains_diagnosable(self):
        with temporary() as d:
            q,s=partial(d);p=journal(d);p.write_bytes(p.read_bytes()+b'{"state":')
            before=p.read_bytes();r=s.finish('INTERRUPTED')
            self.assertEqual(r['journal_integrity']['overall'],'BLOCKED');self.assertEqual(p.read_bytes(),before)

    def test_X_completed_result_immutable(self):
        with temporary() as d:
            q,r=finish_good(d);before=(Path(d)/'RESULT.json').read_bytes()
            holder=Publication(d,q,replace(q,attempt_budget=4),Ledger(Path(d)/'budget.json'))
            holder.verify_completed();self.assertEqual((Path(d)/'RESULT.json').read_bytes(),before)

    def test_Y_journal_changes_at_publication_is_not_returned_verified(self):
        import src.shared.publication as publication
        with temporary() as d:
            q,s=partial(d);original=publication.exclusive_publish;p=journal(d)
            def changed(pending,final):
                p.write_bytes(p.read_bytes()+b'changed-during-publication\n')
                original(pending,final)
            with patch('src.shared.publication.exclusive_publish',side_effect=changed):
                with self.assertRaises(ArtifactIntegrity):s.finish('INTERRUPTED')
            # Authorized F01 correction strengthens this former post-link-only
            # check: the attempted evidence mutation must prevent publication.
            self.assertFalse((Path(d)/'RESULT.json').exists())

    def test_Z_valid_recorded_history_passes(self):
        with temporary() as d:
            q,s=partial(d);report=verify_journals(s.store)
            self.assertEqual(report['overall'],'VERIFIED')
            self.assertEqual(report['provenance_graph']['unwitnessed_settlements'],[])
            s.detach();script=Script({});r=execute(q,script,d)
            self.assertEqual(r['journal_integrity']['overall'],'VERIFIED');self.assertEqual(script.seen,[])

    def test_missing_historical_witness_is_not_fabricated(self):
        with temporary() as d:
            q,s=partial(d);p=settlement_path(s.store,1);p.rename(Path(d)/'preserved-settlement.json')
            report=verify_journals(s.store);self.assertNotEqual(report['overall'],'VERIFIED')
            self.assertFalse(p.exists())

    def test_unwitnessed_handle_cannot_trigger_a_new_call(self):
        with temporary() as d:
            q,s=partial(d);settlement_path(s.store,1).rename(Path(d)/'preserved-settlement.json')
            script=Script({'SPARSE_GATE':[gate()]});s.transport.script=script
            with self.assertRaises(ArtifactIntegrity):s.assess('SPARSE_GATE',(s.outputs['INITIAL'],))
            self.assertEqual(script.seen,[])
            self.assertEqual(s.ledger.summary(q.run_id)['physical_attempts'],1)

    def test_publication_window_never_leaves_a_verified_certificate(self):
        import src.shared.publication as publication
        with temporary() as d:
            q,s=partial(d);original=publication.exclusive_publish;p=journal(d)
            def changed(pending,final):
                p.write_bytes(p.read_bytes()+b'changed-in-final-publication-window\n')
                original(pending,final)
            with patch('src.shared.publication.exclusive_publish',side_effect=changed):
                with self.assertRaises(ArtifactIntegrity):s.finish('INTERRUPTED')
            final=Path(d)/'RESULT.json'
            if final.exists():
                self.assertNotEqual(read(final)['journal_integrity']['overall'],'VERIFIED',
                                    'A rejected API return cannot retract a published VERIFIED certificate')
