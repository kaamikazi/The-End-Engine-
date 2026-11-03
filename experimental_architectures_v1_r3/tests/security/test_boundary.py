import ast,secrets,os
from unittest.mock import patch
from tests.helpers import *
from src.prompts.registry import STAGES
from runtime_isolation_v1.src.evaluation_firewall.firewall import EvaluationPlane
class SecurityTests(ScenarioCase):
    def test_new_stage_unknown_fields_tools_and_private_messages_reject(self):
        with temporary() as d:
            s=Session(request('SPARSE_DELIBERATION'),Script({}),d);base={'run_id':'unit','call_id':'CALL_INITIAL','task_id':task()['task_id'],'purpose':'INITIAL','instruction_id':'INITIAL','prior_output_ids':[],'observation_ids':[]}
            for key in ('messages','tools','attachments','evaluator_result','thread_id','metadata'):
                with self.subTest(key=key),self.assertRaises(BoundaryError):s.gateway.reserve_request(base|{key:'PRIVATE'})
            self.assertEqual(s.ledger.summary('unit')['physical_attempts'],0)
    def test_foreign_output_handle_cannot_enter_gate(self):
        with temporary() as d:
            l=Ledger(Path(d)/'l.json');a=Session(request('SPARSE_DELIBERATION','a'),Script({'INITIAL':[complete()]}),Path(d)/'a',l);_,out=a.generate('INITIAL');b=Session(request('SPARSE_DELIBERATION','b'),Script({'INITIAL':[complete()]}),Path(d)/'b',l);b.generate('INITIAL')
            with self.assertRaises(BoundaryError):b.call('SPARSE_GATE',(out,))
    def test_alternatives_cannot_receive_sibling_or_C0_content(self):
        with temporary() as d:
            s=Session(request('BOUNDED_ALTERNATIVES'),Script({'INITIAL':[complete()]}),d);_,out=s.generate('INITIAL')
            with self.assertRaises(BoundaryError):s.call('ALTERNATIVE_REQUIREMENTS',(out,))
    def test_stage_for_another_condition_cannot_be_called(self):
        with temporary() as d:
            s=Session(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()]}),d);s.generate('INITIAL')
            with self.assertRaises(BoundaryError):s.call('ALTERNATIVE_REQUIREMENTS')
    def test_private_environment_file_and_encoded_canaries_not_forwarded(self):
        marker=secrets.token_hex(24)
        with temporary() as d:
            (Path(d)/'private_fixture').write_text(marker,encoding='utf-8');os.environ['ABC_PRIVATE_TEST_CANARY']=marker
            try:
                r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()],'SPARSE_GATE':[gate()]}),Path(d)/'run');wire=''.join(c['wire'] for c in r['provider_records']);self.assertNotIn(marker,wire);self.assertNotIn(marker.encode().hex(),wire);self.assertNotIn(str(Path(d)),wire)
            finally:os.environ.pop('ABC_PRIVATE_TEST_CANARY',None)
    def test_model_code_is_inert_no_execution_callback(self):
        with temporary() as d:
            target=Path(d)/'executed';text="__import__('pathlib').Path("+repr(str(target))+").write_text('bad')"
            with patch('builtins.eval',side_effect=AssertionError('eval forbidden')):r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[text],'SPARSE_GATE':[gate()]}),Path(d)/'run')
            self.assertFalse(target.exists());self.assertEqual(r['C0'],text)
    def test_unexpected_provider_tools_reject_unknown_consumption(self):
        raw=completion('x',tools=[{'name':'shell'}]);r=self.scenario('provider_tools','SPARSE_DELIBERATION',{'INITIAL':[raw]});self.assertEqual(r['result']['physical_attempts'],1);self.assertIsNone(r['C0']);self.assertIsNone(r['result']['total_tokens'])
    def test_unapproved_prompt_mutation_rejects(self):
        before=STAGES['SPARSE_GATE']['prompt'];STAGES['SPARSE_GATE']['prompt']='PRIVATE PROMPT'
        try:
            with self.assertRaises(BoundaryError):StageCompiler()
        finally:STAGES['SPARSE_GATE']['prompt']=before
    def test_no_evaluator_import_or_dynamic_execution_in_generation(self):
        for p in (OUT/'src').rglob('*.py'):
            for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
                if isinstance(n,ast.ImportFrom):self.assertNotIn('evaluator',n.module or '')
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('eval','exec','__import__'))
    def test_external_evaluation_requires_closed_generation(self):
        with temporary() as d:
            s=Session(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()]}),d);s.generate('INITIAL');plane=EvaluationPlane(s.gateway)
            with self.assertRaises(BoundaryError):plane.evaluate('unit',{},lambda x:True)
            c=s.gateway.close_generation('unit');r=plane.evaluate('unit',c,lambda x:{'PRIVATE_SCORE':1});self.assertTrue(r.results)
            with self.assertRaises(BoundaryError):s.call('SPARSE_GATE',(s.outputs['INITIAL'],))
    def test_invalid_observation_category_cannot_be_laundered(self):
        f=finding(category='FORMAT_CONTRACT');r=self.scenario('category','DIRECTED_REPAIR',{'INITIAL':[complete()|{'amount':8}],'REPAIR_INVENTORY':[{'findings':[f]}]});self.assertEqual(r['result']['final_candidate'],'C0')
    def test_no_arbitrary_provider_object_bypass(self):
        with temporary() as d:
            s=Session(request('SPARSE_DELIBERATION'),Script({}),d)
            with self.assertRaises(BoundaryError):s.gateway.dispatch({'prompt':'private'})
