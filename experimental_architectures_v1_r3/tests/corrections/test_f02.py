from .common import *
import base64,shutil
from src.shared.journals import entry
class JournalIntegrityTests(unittest.TestCase):
    def check_damage(self,name,mutate):
        with temporary() as d:
            q,s=partial(d);p=journal(d);mutate(Path(d),p,s);snap={x.relative_to(d).as_posix():x.read_bytes() for x in (Path(d)/'wire').iterdir() if x.is_file()};s.detach();script=Script({});r=execute(q,script,d)
            self.assertEqual(script.seen,[]);self.assertEqual(r['result']['physical_attempts'],1);self.assertEqual(r['journal_integrity']['overall'],'BLOCKED');self.assertTrue(r['result']['diagnostic_errors']);self.assertNotEqual(r['result']['termination_reason'],'COMPLETED')
            self.assertEqual(snap,{x.relative_to(d).as_posix():x.read_bytes() for x in (Path(d)/'wire').iterdir() if x.is_file()});evidence(self,'F02',mutation=name,statuses=r['journal_integrity']['attempts'],raw_bytes_preserved=True,new_calls=0)
    def test_valid_settled_evidence_is_verified(self):
        with temporary() as d:
            q,s=partial(d);report=verify_journals(s.store);self.assertEqual(report['overall'],'VERIFIED');self.assertEqual(len(report['trusted_hashes']),1);s.finish('INTERRUPTED');evidence(self,'F02',status=report['overall'])
    def test_swapped_journal_between_runs_is_not_trusted(self):
        with temporary() as d:
            one=Path(d)/'one';two=Path(d)/'two';q,a=partial(one);other=replace(q,run_id='other_run');b=Session(other,Script({'INITIAL':[complete()]}),two);b.generate('INITIAL')
            # Swap actual evidence from a distinct run, with identical public task/settings.
            pa=journal(one);pb=journal(two);pa.write_bytes(pb.read_bytes());a.detach();b.detach();r=execute(q,Script({}),one);self.assertEqual(r['journal_integrity']['overall'],'BLOCKED')
    def test_final_hash_mutation_is_rejected_without_overwriting_result(self):
        with temporary() as d:
            q,r=finish_good(d);before=(Path(d)/'RESULT.json').read_bytes();p=journal(d);p.write_bytes(p.read_bytes()+b'changed\n')
            with self.assertRaises(ArtifactIntegrity):Session(q,Script({}),d)
            self.assertEqual((Path(d)/'RESULT.json').read_bytes(),before)
    def test_unknown_pre_dispatch_reservation_is_not_verified(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({}),d);spec={'run_id':q.run_id,'call_id':'CALL_INITIAL','task_id':q.task_id,'purpose':'INITIAL','instruction_id':'INITIAL','prior_output_ids':[],'observation_ids':[]};s.gateway.reserve_request(spec);report=verify_journals(s.store);self.assertEqual(report['overall'],'INTERRUPTED');self.assertEqual(report['attempts'][0]['status'],'UNKNOWN');s.finish('INTERRUPTED')
    def test_header_only_inflight_append_remains_unknown(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[complete()]}),d)
            # Suppress settlement by interrupting immediately after a durable wire header.
            from src.shared.journals import finish_entry
            with patch('src.shared.journals.finish_entry',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):s.generate('INITIAL')
            report=verify_journals(s.store);self.assertNotEqual(report['overall'],'VERIFIED');s.finish('INTERRUPTED')

def mutate_row(p,index,fn):
    r=lines(p);fn(r[index]);write_lines(p,r)
def duplicate_file(d,p,s):shutil.copyfile(p,p.with_name('duplicate.jsonl'))
def missing(d,p,s):p.rename(p.with_suffix('.preserved-missing'))
def duplicate_record(d,p,s):
    r=lines(p);r.append(dict(r[-1]));write_lines(p,r)
def reorder(d,p,s):write_lines(p,list(reversed(lines(p))))
def ledger_disagree(d,p,s):
    file=Path(d)/'budget.json';env=read(file);env['state']['attempts'][0]['response_text']='changed accepted text';env['state']['attempts'][0]['response_sha256']=sha(b'changed accepted text');env['state_sha256']=sha(canonical(env['state']));file.write_bytes(canonical(env))
def recomputed_header(d,p,s):
    r=lines(p);r[0]['record']['wire']='{}';r[0]['record']['wire_sha256']=sha(b'{}');r[0].pop('record_sha256');r[0]['record_sha256']=sha(canonical(r[0]));r[1]['previous_sha256']=r[0]['record_sha256'];r[1].pop('record_sha256');r[1]['record_sha256']=sha(canonical(r[1]));write_lines(p,r)
MUTATIONS={
 'changed_wire':lambda d,p,s:mutate_row(p,0,lambda r:r['record'].__setitem__('wire','different wire')),
 'changed_wire_digest':lambda d,p,s:mutate_row(p,0,lambda r:r['record'].__setitem__('wire_sha256','0'*64)),
 'changed_decoded_response':lambda d,p,s:mutate_row(p,1,lambda r:r.__setitem__('response','wrong response')),
 'invalid_base64':lambda d,p,s:mutate_row(p,1,lambda r:r.__setitem__('raw_response_base64','!!!!')),
 'changed_response_digest':lambda d,p,s:mutate_row(p,1,lambda r:r.__setitem__('raw_response_sha256','0'*64)),
 'missing_settled_journal':missing,
 'duplicate_attempt_file':duplicate_file,
 'duplicate_response_record':duplicate_record,
 'wrong_stage':lambda d,p,s:mutate_row(p,0,lambda r:r.__setitem__('stage','REPAIR_PLAN')),
 'wrong_run':lambda d,p,s:mutate_row(p,0,lambda r:r.__setitem__('run_id','OTHER_RUN')),
 'wrong_attempt':lambda d,p,s:mutate_row(p,0,lambda r:r.__setitem__('attempt_id',999)),
 'incorrect_record_order':reorder,
 'settled_torn_tail':lambda d,p,s:p.write_bytes(p.read_bytes()+b'{"state":'),
 'ledger_disagreement':ledger_disagree,
 'recomputed_hashes_still_fail_anchor':recomputed_header,
 'missing_response_anchor':lambda d,p,s:s.store.response_anchor(1).rename(s.store.response_anchor(1).with_suffix('.preserved')),
}
for name,fn in MUTATIONS.items():
    def test(self,label=name,mutator=fn):self.check_damage(label,mutator)
    setattr(JournalIntegrityTests,'test_'+name,test)
