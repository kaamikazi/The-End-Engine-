import hashlib,json,os,subprocess,sys,unittest
from pathlib import Path
from tests.helpers import temporary,task,request
from src.interfaces.contracts import canonical
from src.public_runner.package import build_package,approved_path,minimal_environment
from src.public_runner.gate import require_generation_runtime,IsolationBlocked
from src.accounting.ledger import Ledger
from src.public_runner.mock import MockSession
class IsolationTests(unittest.TestCase):
    def prepare(self,root):
        p=root/'public.json';p.write_bytes(canonical(task()));return {'public.json':hashlib.sha256(p.read_bytes()).hexdigest()}
    def test_only_allowlisted_bytes(self):
        with temporary() as d:
            r=Path(d);approved=self.prepare(r);(r/'hidden.json').write_text('PRIVATE-CANARY',encoding='utf-8')
            b=build_package(r,approved);self.assertNotIn(b'PRIVATE-CANARY',b);self.assertEqual(len(json.loads(b)['files']),1)
    def test_deterministic_export(self):
        with temporary() as d:
            r=Path(d);a=self.prepare(r);self.assertEqual(build_package(r,a),build_package(r,a))
    def test_changed_approved_bytes_reject(self):
        with temporary() as d:
            r=Path(d);a=self.prepare(r);(r/'public.json').write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):build_package(r,a)
    def test_hidden_top_level_key_reject(self):
        with temporary() as d:
            r=Path(d);t=task();t['reference_answer']='private';p=r/'x.json';p.write_bytes(canonical(t))
            with self.assertRaises(ValueError):build_package(r,{'x.json':hashlib.sha256(p.read_bytes()).hexdigest()})
    def test_traversal_absolute_stream_reject(self):
        with temporary() as d:
            for p in ('../hidden','/hidden','C:/hidden','E:\\hidden','file:stream','./public.json','foo/../public.json'):
                with self.subTest(p=p),self.assertRaises(ValueError):approved_path(d,p)
    def test_symlink_export_reject(self):
        with temporary() as d:
            r=Path(d);self.prepare(r)
            try:(r/'link.json').symlink_to(r/'public.json')
            except OSError as e:self.skipTest('OS symlink creation unavailable: '+str(e.winerror))
            with self.assertRaises(ValueError):approved_path(r,'link.json')
    @unittest.skipUnless(os.name=='nt','Windows junction control')
    def test_junction_export_reject(self):
        with temporary() as d:
            r=Path(d);private=r/'private';private.mkdir();self.prepare(private);link=r/'junction'
            script="New-Item -ItemType Junction -Path '"+str(link)+"' -Target '"+str(private)+"' -ErrorAction Stop | Out-Null"
            powershell=Path(os.environ.get('SYSTEMROOT',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
            p=subprocess.run([str(powershell),'-NoProfile','-NonInteractive','-Command',script],capture_output=True,encoding='utf-8')
            if p.returncode:self.skipTest('Junction creation unavailable on test volume')
            with self.assertRaises(ValueError):approved_path(r,'junction/public.json')
    def test_child_environment_stripped(self):
        with temporary() as d:
            old=os.environ.get('LAB_TEST_SECRET');os.environ['LAB_TEST_SECRET']='CANARY-NEVER-LOGGED'
            try:
                r=subprocess.run([sys.executable,'-I','-S','-B','-c',"import os,json;print(json.dumps({'secret': 'LAB_TEST_SECRET' in os.environ,'pythonpath':'PYTHONPATH' in os.environ}))"],env=minimal_environment(d),close_fds=True,capture_output=True,encoding='utf-8',check=True)
                self.assertEqual(json.loads(r.stdout),{'secret':False,'pythonpath':False})
            finally:
                if old is None:os.environ.pop('LAB_TEST_SECRET',None)
                else:os.environ['LAB_TEST_SECRET']=old
    def test_no_tool_or_private_metadata_in_wire(self):
        r=request(run_id='PRIVATE-RUN-ID');wire=r.wire_bytes();self.assertNotIn(b'PRIVATE-RUN-ID',wire);self.assertNotIn(b'condition_id',wire);self.assertEqual(r.wire()['tools'],[]);self.assertEqual(r.wire()['history'],[])
    def test_temp_logs_have_no_hidden_canary(self):
        with temporary() as d:
            r=Path(d);(r/'private').write_text('HIDDEN-SCORING-CANARY',encoding='utf-8');ledger=Ledger(r/'ledger.json');s=MockSession(request(),ledger);s.dispatch('{"word":"blue"}')
            self.assertNotIn('HIDDEN-SCORING-CANARY',(r/'ledger.json').read_text(encoding='utf-8'));self.assertNotIn(b'HIDDEN-SCORING-CANARY',b''.join(s.visible))
    def test_no_evaluator_import_in_mock_source(self):
        import ast
        root=Path(__file__).resolve().parents[2]/'src'
        for p in root.rglob('*.py'):
            for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
                if isinstance(n,ast.Import):self.assertFalse(any('evaluator' in a.name for a in n.names))
                if isinstance(n,ast.ImportFrom):self.assertNotIn('evaluator',n.module or '')
    def test_posthoc_evaluation_order_synthetic(self):
        with temporary() as d:
            ledger=Ledger(Path(d)/'l.json');s=MockSession(request(),ledger);c=s.dispatch('{"word":"blue"}');result=s.result();events=['generation_closed']
            # Synthetic private checker AFTER result; never exported as tool/callback.
            def posthoc(text):events.append('private_evaluation');return json.loads(text)['word']=='blue'
            self.assertTrue(posthoc(c.answer));self.assertEqual(events,['generation_closed','private_evaluation']);self.assertNotIn('score',result.data())
    def test_real_runtime_gate_is_closed(self):
        with self.assertRaises(IsolationBlocked):require_generation_runtime()
    def test_unrestricted_child_CAN_read_private_canary(self):
        # Positive escape control: success means proposed cwd-only boundary FAILS.
        with temporary() as d:
            r=Path(d);public=r/'public';public.mkdir();p=r/'private.txt';p.write_text('PRIVATE-CANARY',encoding='utf-8')
            code="from pathlib import Path;print(Path("+repr(str(p))+").read_text(encoding='utf-8')=='PRIVATE-CANARY')"
            q=subprocess.run([sys.executable,'-I','-S','-B','-c',code],cwd=public,env=minimal_environment(public),close_fds=True,capture_output=True,encoding='utf-8',check=True)
            self.assertEqual(q.stdout.strip(),'True','If denied, re-audit actual enforcement; do not silently assume this control')
    def test_unrestricted_child_CAN_import_absolute_private_module(self):
        with temporary() as d:
            r=Path(d);p=r/'private_module.py';p.write_text('CANARY=True',encoding='utf-8')
            code="import importlib.util;s=importlib.util.spec_from_file_location('private_canary',"+repr(str(p))+");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.CANARY)"
            q=subprocess.run([sys.executable,'-I','-S','-B','-c',code],cwd=r,env=minimal_environment(r),close_fds=True,capture_output=True,encoding='utf-8',check=True)
            self.assertEqual(q.stdout.strip(),'True')
