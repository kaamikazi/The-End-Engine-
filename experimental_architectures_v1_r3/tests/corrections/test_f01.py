from .common import *
class ResultPublicationTests(unittest.TestCase):
    def test_repeated_finish_is_verified_byte_identical_and_logs_conflict(self):
        with temporary() as d:
            q,s=partial(d);r=s.finish('INTERRUPTED');before=(Path(d)/'RESULT.json').read_bytes();again=s.finish('EXTERNAL_BLOCKER');self.assertEqual((Path(d)/'RESULT.json').read_bytes(),before);self.assertEqual(r['artifact_payload_sha256'],again['artifact_payload_sha256']);self.assertIn('CONFLICTING_FINALIZATION_RECORDED',''.join(p.read_text() for p in (Path(d)/'publication/events').glob('*.json')));evidence(self,'F01',result_sha256=sha(before),immutable=True)
    def test_stale_admitted_session_cannot_erase_candidate_lineage(self):
        with temporary() as d:
            stale=Session(request('SPARSE_DELIBERATION'),Script({}),d);q,r=finish_good(d);before=(Path(d)/'RESULT.json').read_bytes();returned=stale.finish('INTERRUPTED');self.assertEqual(before,(Path(d)/'RESULT.json').read_bytes());self.assertEqual(canonical(r['result']['candidate_lineage']),canonical(returned['result']['candidate_lineage']))
    def test_unrestored_session_cannot_publish_empty_history(self):
        with temporary() as d:
            q,s=partial(d);s.detach();stale=Session(q,Script({}),d)
            with self.assertRaises(ArtifactIntegrity):stale.finish('INTERRUPTED')
            self.assertFalse((Path(d)/'RESULT.json').exists())
    def test_active_owner_is_not_stolen_in_same_process(self):
        with temporary() as d:
            q,s=partial(d);other=Session(q,Script({}),d)
            with self.assertRaises(RunBusy):other.restore_without_dispatch()
            s.finish('INTERRUPTED')
    def test_stale_fencing_token_cannot_publish(self):
        with temporary() as d:
            q,s=partial(d);s.store.fence-=1
            with self.assertRaises(StaleOwner):s.finish('INTERRUPTED')
            self.assertFalse((Path(d)/'RESULT.json').exists())
    def test_two_independent_finalizers_publish_one_immutable_result(self):
        with temporary() as d:
            q,s=partial(d);s.detach();a=worker('finalize',d,'a','INTERRUPTED');b=worker('finalize',d,'b','EXTERNAL_BLOCKER');wait(Path(d)/'a.ready');wait(Path(d)/'b.ready');(Path(d)/'go').write_text('go');ra=collect(a);rb=collect(b);self.assertEqual(ra['exit_code'],0,ra);self.assertEqual(rb['exit_code'],0,rb);answers=[read(Path(d)/(n+'.result.json')) for n in ('a','b')];done=[r for r in answers if r['status']=='VERIFIED_TERMINAL'];self.assertTrue(done);self.assertEqual(len({r['result_sha256'] for r in done}),1);self.assertEqual(len(list((Path(d)/'publication/prepared').glob('*.json'))),1);final=read(Path(d)/'RESULT.json');self.assertEqual(len(final['result']['all_generated_candidates']),1);self.assertEqual(final['result']['physical_attempts'],1);evidence(self,'F01',processes=[ra,rb],outcomes=answers,result_sha256=sha((Path(d)/'RESULT.json').read_bytes()),exclusive_prepared_payloads=1)
    def test_active_other_process_rejected_then_recovers_after_death(self):
        with temporary() as d:
            p=worker('hold_owner',d);wait(Path(d)/'one.ready')
            with self.assertRaises(RunBusy):execute(request('SPARSE_DELIBERATION'),Script({}),d)
            (Path(d)/'crash_now').write_text('crash');r=collect(p);self.assertEqual(r['exit_code'],73,r);script=Script({});out=execute(request('SPARSE_DELIBERATION'),script,d);self.assertEqual(script.seen,[]);self.assertEqual(out['result']['physical_attempts'],1);evidence(self,'F01',process=r,recovered_physical_attempts=1,new_dispatches=0)
    def test_publication_lock_released_by_process_exit(self):
        with temporary() as d:
            p=worker('lock_crash',d);r=collect(p);self.assertEqual(r['exit_code'],73,r);q,result=finish_good(d);self.assertEqual(result['result']['physical_attempts'],2);evidence(self,'F01',process=r,recovered=True)
    def test_crash_after_exclusive_link_preserves_completed_bytes(self):
        with temporary() as d:
            p=worker('after_link',d);r=collect(p);self.assertEqual(r['exit_code'],73,r);before=(Path(d)/'RESULT.json').read_bytes()
            with self.assertRaises(FileExistsError):Session(request('SPARSE_DELIBERATION'),Script({}),d)
            self.assertEqual(before,(Path(d)/'RESULT.json').read_bytes());self.assertTrue(list(Path(d).glob('RESULT.*.pending')));evidence(self,'F01',process=r,result_sha256=sha(before),orphan_pending_preserved=True)
    def test_corrupt_existing_result_fails_integrity_before_admission(self):
        with temporary() as d:
            q,r=finish_good(d);path=Path(d)/'RESULT.json';path.write_bytes(path.read_bytes()+b'corrupt');before=path.read_bytes()
            with self.assertRaises(ArtifactIntegrity):Session(q,Script({}),d)
            self.assertEqual(path.read_bytes(),before)
    def test_exclusive_link_failure_leaves_diagnostic_and_no_success(self):
        with temporary() as d:
            q,s=partial(d)
            with patch('src.shared.publication.exclusive_publish',side_effect=OSError('synthetic publication failure')):
                with self.assertRaises(PublicationFailure):s.finish('INTERRUPTED')
            self.assertFalse((Path(d)/'RESULT.json').exists());self.assertIn('EXCLUSIVE_PUBLICATION_FAILED',''.join(p.read_text() for p in (Path(d)/'publication/events').glob('*.json')));r=execute(q,Script({}),d);self.assertEqual(r['result']['physical_attempts'],1)
    def test_permission_denied_does_not_claim_publication(self):
        with temporary() as d:
            q,s=partial(d)
            with patch('src.shared.publication.exclusive_publish',side_effect=PermissionError('synthetic permission denial')):
                with self.assertRaises(PublicationFailure):s.finish('INTERRUPTED')
            self.assertFalse((Path(d)/'RESULT.json').exists());self.assertTrue(list(Path(d).glob('RESULT.*.pending')))
    def test_unique_pending_collision_preserves_suspect_bytes(self):
        with temporary() as d:
            q,s=partial(d);path=Path(d)/('RESULT.'+s.store.token+'.pending');path.write_bytes(b'KEEP_COLLIDING_PENDING')
            with self.assertRaises(FileExistsError):s.finish('INTERRUPTED')
            self.assertEqual(path.read_bytes(),b'KEEP_COLLIDING_PENDING');self.assertFalse((Path(d)/'RESULT.json').exists())
    def test_completed_unknown_reservation_remains_unknown(self):
        with temporary() as d:
            q= request('SPARSE_DELIBERATION');s=Session(q,Script({}),d);spec={'run_id':q.run_id,'call_id':'CALL_INITIAL','task_id':q.task_id,'purpose':'INITIAL','instruction_id':'INITIAL','prior_output_ids':[],'observation_ids':[]};s.gateway.reserve_request(spec);r=s.finish('INTERRUPTED');verified=s.store.verify_completed();self.assertIsNone(verified['result']['total_tokens']);self.assertEqual(verified['result']['physical_attempts'],1);self.assertTrue(verified['generation_closed']['outstanding_or_unknown_cost'])
    def test_deleted_bound_ledger_cannot_reset_budget(self):
        with temporary() as d:
            q,s=partial(d);s.detach();path=Path(d)/'budget.json';path.rename(Path(d)/'budget.preserved.json')
            with self.assertRaises(ArtifactIntegrity):Session(q,Script({}),d)
            self.assertFalse(path.exists())
    def test_same_run_cannot_rebind_to_different_output_directory(self):
        with temporary() as d:
            one=Path(d)/'one';two=Path(d)/'two';l=Ledger(Path(d)/'shared.json');q=request('SPARSE_DELIBERATION');s=Session(q,Script({}),one,l)
            with self.assertRaises(ArtifactIntegrity):Session(q,Script({}),two,l)

    def test_optimized_interpreter_fails_before_admission(self):
        r=subprocess.run([sys.executable,'-O','-B','-c','import sys;sys.path.insert(0,'+repr(str(ROOT))+');import src.shared.session'],cwd=OUT,capture_output=True,encoding='utf-8')
        self.assertNotEqual(r.returncode,0);self.assertIn('ABC_R2_OPTIMIZED_PYTHON_UNSUPPORTED',r.stderr)

    def test_corrupt_owner_fence_rejected_before_generation(self):
        with temporary() as d:
            q,s=partial(d);s.detach();owner=Path(d)/'publication/owner.json';value=read(owner);value['fence']='invalid';owner.write_text(json.dumps(value),encoding='utf-8');other=Session(q,Script({}),d)
            with self.assertRaises(ArtifactIntegrity):other.restore_without_dispatch()
            self.assertFalse((Path(d)/'RESULT.json').exists());self.assertEqual(other.ledger.summary(q.run_id)['physical_attempts'],1)
    def test_missing_previous_owner_metadata_cannot_reset_fence(self):
        with temporary() as d:
            q,s=partial(d);s.detach();owner=Path(d)/'publication/owner.json';owner.rename(owner.with_suffix('.preserved'));other=Session(q,Script({}),d)
            with self.assertRaises(ArtifactIntegrity):other.restore_without_dispatch()
            self.assertFalse((Path(d)/'RESULT.json').exists())
