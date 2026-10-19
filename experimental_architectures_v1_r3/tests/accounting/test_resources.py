from tests.helpers import *
from src.adapters.gateway import ArchitectureGateway
from runtime_isolation_v1.src.trusted_transport.transport import Gateway
from runtime_isolation_v1.src.sealed_requests.boundary import Compiler
class ResourceTests(ScenarioCase):
    def test_existing_gateway_methods_and_seals_are_inherited_unchanged(self):
        for name in ('reserve_request','dispatch','close_generation'):self.assertIs(getattr(ArchitectureGateway,name),getattr(Gateway,name))
        for name in ('seal','validate','intent','run'):self.assertIs(getattr(StageCompiler,name),getattr(Compiler,name))
    def test_known_usage_counts_all_model_stages(self):
        r=self.scenario('usage','DIRECTED_REPAIR',{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[finding()]}],'REPAIR_PLAN':[plan()],'REPAIR_REVISION':[complete()]});self.assertEqual(r['result']['total_tokens'],60)
    def test_shared_global_cap_across_conditions(self):
        with temporary() as d:
            l=Ledger(Path(d)/'shared.json',global_attempts=2);a=execute(request('SPARSE_DELIBERATION','a'),Script({'INITIAL':[complete()],'SPARSE_GATE':[gate()]}),Path(d)/'a',l);b=execute(request('DIRECTED_REPAIR','b'),Script({}),Path(d)/'b',l);self.assertEqual(b['result']['physical_attempts'],0);self.assertEqual(b['result']['termination_reason'],'BUDGET_EXHAUSTED');self.assertEqual(len(l.state()['attempts']),2)
    def test_global_tokens_block_before_initial_without_fake_zero_usage(self):
        with temporary() as d:
            l=Ledger(Path(d)/'shared.json',global_tokens=10);r=execute(request('SPARSE_DELIBERATION'),Script({}),Path(d)/'run',l);self.assertEqual(r['result']['physical_attempts'],0);self.assertIsNone(r['C0']);self.assertEqual(r['result']['termination_reason'],'BUDGET_EXHAUSTED')
    def test_global_time_limit_recorded(self):
        with temporary() as d:
            l=Ledger(Path(d)/'shared.json',global_seconds=1);r=execute(request('SPARSE_DELIBERATION'),Script({}),Path(d)/'run',l);self.assertEqual(r['result']['termination_reason'],'TIME_EXHAUSTED')
    def test_timeout_is_counted_unknown_preserving_C0(self):
        r=self.scenario('timeout','SPARSE_DELIBERATION',{'INITIAL':[complete()],'SPARSE_GATE':[TimeoutError()]});self.assertEqual(r['result']['termination_reason'],'TIME_EXHAUSTED');self.assertIsNone(r['result']['total_tokens'])
    def test_canceled_attempt_not_refunded(self):
        r=self.scenario('cancel','SPARSE_DELIBERATION',{'INITIAL':[complete()],'SPARSE_GATE':[Canceled('synthetic')]});self.assertEqual(r['result']['model_invocations'][-1]['state'],'CANCELED');self.assertEqual(r['result']['physical_attempts'],2)
    def test_outstanding_reservation_restart_no_new_dispatch(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({}),d);spec={'run_id':q.run_id,'call_id':'CALL_INITIAL','task_id':q.task_id,'purpose':'INITIAL','instruction_id':'INITIAL','prior_output_ids':[],'observation_ids':[]}
            with self.assertRaises(KeyboardInterrupt):s.gateway.reserve_request(spec,interrupt_after_reserve=True)
            r=execute(q,Script({'INITIAL':[complete()]}),d,s.ledger);self.assertEqual(r['result']['termination_reason'],'INTERRUPTED');self.assertEqual(r['result']['physical_attempts'],1);self.assertEqual(r['provider_records'],[]);self.assertIsNone(r['result']['total_tokens'])
    def test_partial_response_restart_recovers_C0_without_budget_reset(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[complete()]}),d);s.generate('INITIAL');s.detach();r=execute(q,Script({}),d,s.ledger);self.assertEqual(r['result']['final_candidate'],'C0');self.assertEqual(r['result']['physical_attempts'],1);self.assertEqual(len(r['provider_records']),1);self.assertTrue(r['provider_records'][0]['recovered_without_dispatch'])
    def test_completed_artifact_never_overwritten(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');execute(q,Script({'INITIAL':[complete()],'SPARSE_GATE':[gate()]}),d)
            with self.assertRaises(FileExistsError):execute(q,Script({}),d)
    def test_no_dispatch_after_generation_closure(self):
        with temporary() as d:
            s=Session(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()]}),d);s.gateway.close_generation(s.request.run_id)
            with self.assertRaises(BoundaryError):s.call('INITIAL')
            self.assertEqual(s.ledger.summary(s.request.run_id)['physical_attempts'],0)
    def test_duplicate_call_rejected_before_second_dispatch(self):
        with temporary() as d:
            s=Session(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()]}),d);s.generate('INITIAL')
            with self.assertRaises(BoundaryError):s.call('INITIAL')
            self.assertEqual(s.ledger.summary(s.request.run_id)['physical_attempts'],1)

    def test_wire_and_response_journal_precedes_final_result(self):
        with temporary() as d:
            s=Session(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()]}),d);s.generate('INITIAL')
            paths=list((Path(d)/'wire').glob('*.jsonl'));self.assertEqual(len(paths),1)
            lines=[json.loads(x) for x in paths[0].read_text(encoding='utf-8').splitlines()]
            self.assertEqual([x['state'] for x in lines],['RESERVED_WIRE_READY','RAW_RESPONSE_RECEIVED']);self.assertTrue(lines[1]['raw_response_base64']);self.assertFalse((Path(d)/'RESULT.json').exists())
    def test_atomic_final_publication_binds_journal_hashes(self):
        with temporary() as d:
            r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()],'SPARSE_GATE':[gate()]}),d)
            self.assertFalse((Path(d)/'RESULT.pending').exists());self.assertEqual(len(r['durable_journal_hashes']),2)
            for rel,h in r['durable_journal_hashes'].items():self.assertEqual(sha((Path(d)/rel).read_bytes()),h)
            self.assertEqual(canonical(json.loads((Path(d)/'RESULT.json').read_text(encoding='utf-8'))),canonical(r))
    def test_torn_final_journal_append_recovers_without_dispatch(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[complete()]}),d);s.generate('INITIAL');path=next((Path(d)/'wire').glob('*.jsonl'))
            with path.open('a',encoding='utf-8') as f:f.write('{"state":')
            s.detach();script=Script({});r=execute(q,script,d,s.ledger);self.assertEqual(script.seen,[]);self.assertEqual(r['result']['final_candidate'],'C0');self.assertEqual(r['result']['physical_attempts'],1);self.assertIn('TORN_FINAL_APPEND',json.dumps(r))
