"""F01 publication-window controls. Synthetic offline artifacts only."""
from .common import *
import src.shared.publication as publication


class PublicationWindowTests(unittest.TestCase):
    def check_mutation(self, target, operation):
        with temporary() as d:
            q,s=partial(d);original=publication.exclusive_publish
            paths={'wire':journal(d),'settlement':s.store.meta/'attempts/000001.settlement.json',
                   'ledger':s.ledger.path,'closure':s.ledger.path.with_suffix('.closed.json'),
                   'owner':s.store.owner_path}
            def changed(pending,final):
                path=Path(pending) if target=='pending' else s.store.meta/'prepared'/(s.store.token+'.json') if target=='prepared' else paths[target]
                if operation=='write':path.write_bytes(b'changed-during-final-link')
                elif operation=='delete':path.unlink()
                else:path.rename(path.with_suffix('.preserved'))
                original(pending,final)
            with patch.object(publication,'exclusive_publish',side_effect=changed):
                with self.assertRaises(ArtifactIntegrity):s.finish('INTERRUPTED')
            self.assertFalse((Path(d)/'RESULT.json').exists())
            self.assertEqual(s.ledger.summary(q.run_id)['physical_attempts'],1)
            self.assertTrue(list(Path(d).glob('RESULT.*.pending')))

    def test_wire_write_at_link(self):self.check_mutation('wire','write')
    def test_wire_delete_at_link(self):self.check_mutation('wire','delete')
    def test_wire_rename_at_link(self):self.check_mutation('wire','rename')
    def test_settlement_write_at_link(self):self.check_mutation('settlement','write')
    def test_ledger_write_at_link(self):self.check_mutation('ledger','write')
    def test_closure_write_at_link(self):self.check_mutation('closure','write')
    def test_owner_write_at_link(self):self.check_mutation('owner','write')
    def test_prepared_write_at_link(self):self.check_mutation('prepared','write')
    def test_pending_write_at_link(self):self.check_mutation('pending','write')

    def test_change_after_initial_validation_rejected(self):
        with temporary() as d:
            q,s=partial(d);original=s.store.verify_semantics;calls=[];p=journal(d)
            def changed(data):
                r=original(data);calls.append(1)
                if len(calls)==1:p.write_bytes(p.read_bytes()+b'changed-after-initial-validation\n')
                return r
            with patch.object(s.store,'verify_semantics',side_effect=changed):
                with self.assertRaises(ArtifactIntegrity):s.finish('INTERRUPTED')
            self.assertFalse((Path(d)/'RESULT.json').exists());self.assertEqual(len(calls),1)

    def test_new_orphan_at_exclusive_link_seam_is_rejected(self):
        with temporary() as d:
            q,s=partial(d);original=publication.exclusive_publish
            def changed(pending,final):
                (Path(d)/'wire/orphan.jsonl').write_bytes(b'new-orphan-record\n')
                original(pending,final)
            with patch.object(publication,'exclusive_publish',side_effect=changed):
                with self.assertRaises(ArtifactIntegrity):s.finish('INTERRUPTED')
            self.assertFalse((Path(d)/'RESULT.json').exists());self.assertTrue((Path(d)/'wire/orphan.jsonl').exists())

    def test_native_link_hook_cannot_mutate_existing_wire(self):
        with temporary() as d:
            q,s=partial(d);original=publication.os.link;p=journal(d);before=p.read_bytes()
            def changed(source,destination,*args,**kwargs):
                if Path(destination).name=='RESULT.json':p.write_bytes(b'changed-in-native-link-hook')
                return original(source,destination,*args,**kwargs)
            with patch.object(publication.os,'link',side_effect=changed):
                with self.assertRaises(ArtifactIntegrity):s.finish('INTERRUPTED')
            self.assertFalse((Path(d)/'RESULT.json').exists());self.assertEqual(p.read_bytes(),before)

    def test_real_process_writer_denied_until_after_link(self):
        with temporary() as d:
            q,s=partial(d);original=publication.exclusive_publish;p=journal(d);before=p.read_bytes();observed=[]
            def check(pending,final):
                program="from pathlib import Path;import sys,json\ntry:Path(sys.argv[1]).write_bytes(b'child-mutation');print(json.dumps({'denied':False}))\nexcept PermissionError:print(json.dumps({'denied':True}))"
                r=subprocess.run([sys.executable,'-B','-c',program,str(p)],capture_output=True,text=True,timeout=15)
                self.assertEqual(r.returncode,0,r.stderr);self.assertTrue(json.loads(r.stdout)['denied']);observed.append(r.stdout)
                original(pending,final)
            with patch.object(publication,'exclusive_publish',side_effect=check):r=s.finish('INTERRUPTED')
            self.assertEqual(p.read_bytes(),before);self.assertEqual(r['journal_integrity']['overall'],'VERIFIED');s.store.verify_completed()
            self.assertEqual(len(observed),1)
            # Successful publication releases pins: later damage is detected,
            # without rewriting the already immutable final artifact.
            final=(Path(d)/'RESULT.json').read_bytes();p.write_bytes(before+b'later-damage\n')
            with self.assertRaises(ArtifactIntegrity):s.store.verify_completed()
            self.assertEqual((Path(d)/'RESULT.json').read_bytes(),final)
