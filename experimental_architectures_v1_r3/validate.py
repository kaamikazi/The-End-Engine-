"""Offline r2 validation. Outputs are a new checkpoint; no existing wiring overwrite."""
import ast,io,json,os,shutil,socket,subprocess,sys,unittest,urllib.request
from collections import Counter
from pathlib import Path
from unittest.mock import patch
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent;INPUTS=OUT/'validation';V=INPUTS
if '--output-dir' in sys.argv:
    V=Path(sys.argv[sys.argv.index('--output-dir')+1]).resolve()
    if not V.is_relative_to((OUT/'validation/scratch').resolve()):raise ValueError('Additional checkpoints must stay inside r2 validation/scratch')
sys.path[0:0]=[str(OUT),str(ROOT)]
from audit import preserve,sha
from src.shared.session import execute
from src.shared.wiring import baseline,wiring_script
from src.adapters.gateway import LIMITS,ArchitectureGateway,StageCompiler
from src.shared.publication import Publication
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest,CONDITIONS,canonical
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from runtime_isolation_v1.src.trusted_transport.transport import Gateway
from runtime_isolation_v1.src.sealed_requests.boundary import Compiler

def save(name,value):(V/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
class ObservedResult(unittest.TextTestResult):
    def __init__(self,*a,**k):super().__init__(*a,**k);self.records=[]
    def addSuccess(self,t):super().addSuccess(t);self.records.append({'id':t.id(),'status':'PASS'})
    def addFailure(self,t,e):super().addFailure(t,e);self.records.append({'id':t.id(),'status':'FAIL'})
    def addError(self,t,e):super().addError(t,e);self.records.append({'id':t.id(),'status':'ERROR'})
    def addSkip(self,t,r):super().addSkip(t,r);self.records.append({'id':t.id(),'status':'SKIP','reason':r})

def new_tests():
    previous=Path.cwd();os.chdir(OUT);stream=io.StringIO()
    try:r=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=ObservedResult).run(unittest.defaultTestLoader.discover('tests',top_level_dir='.'))
    finally:os.chdir(previous)
    (V/'NEW_TESTS.txt').write_text(stream.getvalue(),encoding='utf-8',newline='\n')
    totals={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)};save('TEST_RESULTS.json',{'r2_suite':totals,'test_results':r.records,'command':'python -B -m unittest discover -s tests -t . -v','cwd':'experimental_architectures_v1_r2','offline':True});assert r.wasSuccessful(),stream.getvalue()[-12000:]
    from tests.corrections.common import EVIDENCE
    for group,name in [('F01','CONCURRENCY_RESULTS.json'),('F02','JOURNAL_INTEGRITY_RESULTS.json'),('F03','BASELINE_CONTRACT_RESULTS.json'),('F04','NUMERIC_SAFETY_RESULTS.json'),('INTERACTIONS','CROSS_DEFECT_RESULTS.json')]:
        marker='test_'+group.lower() if group!='INTERACTIONS' else 'test_interactions'
        ids=[x for x in r.records if '.'+marker+'.' in x['id']];save(name,{'tests':len(ids),'results':ids,'evidence':[x for x in EVIDENCE if x['group']==group],'failures':sum(x['status']!='PASS' for x in ids)})
    from tests.helpers import SCENARIOS
    save('LEGACY_SCENARIO_SUMMARIES.json',{'count':len(SCENARIOS),'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','scope':'Raw unit fixtures and expectations in unchanged/ported test source; temporary detailed receipts recreated by rerun','scenarios':[{'id':x['scenario_id'],'expected':x['expected'],'actual_stages':[a['stage'] for a in x['actual']['provider_records']],'termination':x['actual']['result']['termination_reason'],'final_candidate':x['actual']['result']['final_candidate'],'physical_attempts':x['actual']['result']['physical_attempts'],'artifact_payload_sha256':x['actual']['artifact_payload_sha256']} for x in SCENARIOS]})
    return totals

def reviewer():
    target=V/'REVIEWER_PROBES_R2.json'
    if target.exists():
        backup=V/'scratch'/('development-reviewer-'+sha(target)[:12]+'.json')
        if not backup.exists():backup.write_bytes(target.read_bytes())
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'}
    if V!=INPUTS:env['END_ABC_R2_REVIEW_OUTPUT']=str(V)
    r=subprocess.run([sys.executable,'-B',str(INPUTS/'reviewer_probes_r2.py')],cwd=ROOT,env=env,capture_output=True,encoding='utf-8',timeout=180)
    (V/'REVIEWER_RUN.txt').write_text(r.stdout+r.stderr,encoding='utf-8',newline='\n');assert r.returncode==0,r.stderr[-5000:]
    p=json.loads(target.read_text(encoding='utf-8'));assert p['count']==49 and p['passed']==49 and p['failed']==p['harness_errors']==0,p
    # Retain raw, current counterexample evidence; other synthetic development scratch remains local.
    evidence=V/'reviewer_evidence'
    if evidence.exists():raise FileExistsError('New reviewer evidence checkpoint needed')
    evidence.mkdir();paths=set()
    def visit(x):
        if isinstance(x,str) and str(V/'scratch/reviewer_runs') in x:
            q=Path(x)
            if q.is_file():q=q.parent
            if q.is_dir():
                while q.parent!=(V/'scratch/reviewer_runs') and q.is_relative_to(V/'scratch/reviewer_runs'):q=q.parent
                if q.parent==V/'scratch/reviewer_runs':paths.add(q)
        elif isinstance(x,dict):
            for v in x.values():visit(v)
        elif isinstance(x,list):
            for v in x:visit(v)
    if V!=INPUTS:
        return {'tests':p['count'],'passed':p['passed'],'failures':p['failed'],'harness_errors':p['harness_errors'],'previously_failing_checks':sum(bool(x.get('finding_id')) for x in p['probes']),'raw_evidence_directories':'Retained in portable output runs'}
    for x in p['probes']:
        if x.get('finding_id') in ('F01','F02','F03','F04'):visit(x)
    for path in sorted(paths):shutil.copytree(path,evidence/path.name,ignore=shutil.ignore_patterns('*.lock'))
    return {'tests':p['count'],'passed':p['passed'],'failures':p['failed'],'harness_errors':p['harness_errors'],'previously_failing_checks':sum(bool(x.get('finding_id')) for x in p['probes']),'raw_evidence_directories':len(paths)}

def regression_inputs():
    manifest=INPUTS/'REGRESSION_INPUTS.json'
    if manifest.exists():files=json.loads(manifest.read_text(encoding='utf-8'))['files']
    else:
        files=json.loads((INPUTS/'BASELINE_INPUT_HASHES.json').read_text(encoding='utf-8'))['reused_files']
        demo='demo_output/7744de05-e9ac-4e42-bd65-18a1889026ba.jsonl';schema='demo_v02_output/966fc233-7d0e-4c68-85f9-15b424858d80.jsonl';legacy=next((ROOT/'v035_core_regression_pilot/trajectories').glob('*.jsonl')).relative_to(ROOT).as_posix()
        files={n:h for n,h in files.items() if not n.startswith('demo_output/') or n==demo}
        files={n:h for n,h in files.items() if not n.startswith('v035_core_regression_pilot/trajectories/') or n==legacy};files[schema]=sha(ROOT/schema)
        save('REGRESSION_INPUTS.json',{'source_commit':'d5109d5c898d9b6fcee0dd0198cb5e2e7080cf8a','files':files,'historical_trajectory_scope':'Three exact legacy schema compatibility fixtures only, no historical trajectory bulk'})
    destination=V/'r'
    if destination.exists():raise FileExistsError('New regression source checkpoint needed')
    destination.mkdir()
    for n,h in files.items():
        p=ROOT/n;assert sha(p)==h,n;q=destination/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
    return destination,files

def old_suites():
    copied,files=regression_inputs();results={}
    for name,rel in [('original_architectures','experimental_architectures_v1'),('native','native_model_integration_v1'),('runtime','runtime_isolation_v1'),('laboratory','cognitive_architecture_lab_v1'),('engine','')]:
        cwd=copied/rel;program="import sys,socket,urllib.request,unittest,tempfile,os,json;from unittest.mock import patch;sys.path[0:0]=["+repr(str(cwd))+","+repr(str(copied))+"];sys.dont_write_bytecode=True\ndef deny(*a,**k):raise AssertionError('Offline unchanged regression')\nwith tempfile.TemporaryDirectory(prefix='regression-',dir="+repr(str(V/'scratch'))+") as d:\n os.environ['TEMP']=os.environ['TMP']=d;tempfile.tempdir=d\n with patch.object(socket.socket,'connect',deny),patch.object(socket,'getaddrinfo',deny),patch.object(urllib.request.OpenerDirector,'open',deny):\n  r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests',top_level_dir='.'))\n print(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),'passed':r.wasSuccessful()}))\n sys.exit(not r.wasSuccessful())"
        r=subprocess.run([sys.executable,'-B','-c',program],cwd=cwd,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'},capture_output=True,encoding='utf-8',timeout=180);(V/('previous-'+name+'.txt')).write_text(r.stdout+r.stderr,encoding='utf-8',newline='\n');assert r.returncode==0,r.stderr[-6000:];results[name]=json.loads(r.stdout.strip().splitlines()[-1])
    for n,h in files.items():assert sha(copied/n)==h,n
    save('PREVIOUS_REGRESSIONS.json',results);return results

def wiring():
    directory=V/'mock_wiring'
    if directory.exists():raise FileExistsError('Completed wiring checkpoint must not overwrite')
    directory.mkdir();ledger=Ledger(directory/'GLOBAL_BUDGET.json');cells=[];wires={}
    for tid in ('EXP-001','EXP-002'):
        t=json.loads((OUT/'public_inputs'/(tid+'.json')).read_text(encoding='utf-8'));initial=[]
        for c in CONDITIONS:
            rid='MOCK_'+tid+'_'+c;q=RunRequest(tid,t,'qwen3:4b','UNOBSERVED_NO_MODEL_QUERIED',{'temperature':.7,'top_p':.8,'think':False},None,8192,4096,c,36,400000,1800,rid);d=directory/rid
            r=execute(q,wiring_script(t),d,ledger) if c in LIMITS else baseline(q,d,ledger);first=r['provider_records'][0]['wire'].encode();initial.append(first);raw=(d/('RESULT.json' if c in LIMITS else 'COMMON_RESULT.json')).read_bytes();store=Publication(d,q,__import__('dataclasses').replace(q,attempt_budget=min(q.attempt_budget,LIMITS[c])) if c in LIMITS else q,ledger,result_name='RESULT.json' if c in LIMITS else 'COMMON_RESULT.json',mode='ARCHITECTURE' if c in LIMITS else 'NATIVE_BASELINE');verified=store.verify_completed();assert verified['artifact_payload_sha256']==r['artifact_payload_sha256'];assert raw==(d/('RESULT.json' if c in LIMITS else 'COMMON_RESULT.json')).read_bytes()
            assert r['generation_closed'] and r['scientific_scores'] is None
            cells.append({'run_id':rid,'task_id':tid,'condition':c,'physical_attempts':r['result']['physical_attempts'],'initial_wire_sha256':sha_bytes(first),'artifact_payload_sha256':r['artifact_payload_sha256'],'result_file_sha256':sha_bytes(raw),'final_candidate':r['result']['final_candidate'],'termination':r['result']['termination_reason'],'journal_integrity':r['journal_integrity']['overall'],'immutable_verified':True,'generation_closed':True,'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','native_iterations':json.loads((d/'MOCK_REPLAY.json').read_text(encoding='utf-8'))['iterations'] if c=='FROZEN_CURRENT_END' else None})
        assert len(set(initial))==1;wires[tid]=sha_bytes(initial[0])
    report={'cells':cells,'cells_count':len(cells),'actual_physical_attempts':len(ledger.state()['attempts']),'initial_bytes_identical':wires,'global_limits':ledger.limits,'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','actual_model_calls':0,'empirical_benchmarks':0};save('SIX_CONDITION_WIRING.json',report);return report

def sha_bytes(value):
    import hashlib
    return hashlib.sha256(value).hexdigest()
def architecture_preservation():
    old=ROOT/'experimental_architectures_v1';exact={}
    for name in ('src/architecture_a/sparse.py','src/architecture_b/repair.py','src/architecture_c/alternatives.py','src/prompts/registry.py','src/shared/evidence.py','src/adapters/script.py','validation/PROMPT_HASHES.json','public_inputs/ABC-PUBLIC-001.json','public_inputs/EXP-001.json','public_inputs/EXP-002.json'):
        assert (OUT/name).read_bytes()==(old/name).read_bytes();exact[name]=sha(OUT/name)
    def functions(p):
        source=p.read_text(encoding='utf-8');tree=ast.parse(source);return {n.name:ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
    a,b=functions(old/'src/shared/observations.py'),functions(OUT/'src/shared/observations.py');unchanged=[n for n in a if n not in ('parse','inspect')];assert all(a[n]==b[n] for n in unchanged)
    inherited={n:getattr(ArchitectureGateway,n) is getattr(Gateway,n) for n in ('reserve_request','dispatch','close_generation')};sealed={n:getattr(StageCompiler,n) is getattr(Compiler,n) for n in ('seal','validate','intent','run')};assert all(inherited.values()) and all(sealed.values())
    result={'exact_original_files':exact,'unchanged_public_constraint_functions':unchanged,'gateway_methods_identical':inherited,'compiler_seal_methods_identical':sealed,'intrinsic_caps':LIMITS,'independent_approval':'PENDING'};save('ARCHITECTURE_PRESERVATION.json',result);return result

def main():
    V.mkdir(exist_ok=True);(V/'scratch').mkdir(exist_ok=True);network=[]
    def deny(*a,**kw):network.append(1);raise AssertionError('No model/provider network')
    with patch.object(socket.socket,'connect',deny),patch.object(socket.socket,'connect_ex',deny),patch.object(socket.socket,'sendto',deny),patch.object(socket,'getaddrinfo',deny),patch.object(urllib.request.OpenerDirector,'open',deny):
        tests=new_tests();print(json.dumps({'stage':'new_tests','result':tests}),flush=True)
        probes=reviewer();print(json.dumps({'stage':'reviewer','result':probes}),flush=True)
        previous=old_suites();print(json.dumps({'stage':'previous_suites','result':previous}),flush=True)
        cells=wiring();arch=architecture_preservation()
        if '--portable' in sys.argv:
            preservation={'passed':None,'scope':'External Git/frozen-payload preservation not repeated in standalone archive; compare the supplied original local receipt'}
        else:
            preservation=preserve();assert preservation['passed']
        save('SOURCE_PRESERVATION.json',preservation)
    assert not network
    final={'verdict':'PORTABLE_OFFLINE_RETEST_PASS' if '--portable' in sys.argv else 'READY_FOR_INDEPENDENT_REVIEW','implementation':'1.0.1','r2_tests':tests,'reviewer_probes':probes,'previous_suites':previous,'mock_wiring_cells':cells['cells_count'],'mock_physical_attempts':cells['actual_physical_attempts'],'architecture_preservation':'PASS','source_preservation':'NOT_REPEATED_PORTABLE_SCOPE' if '--portable' in sys.argv else 'PASS','findings':{f:'RESOLVED_LOCALLY' for f in ('F01','F02','F03','F04')},'independent_status':'PENDING','provider_compatibility':'PENDING','human_adjudication':'PENDING','contamination':'PENDING_EXTERNAL_DECISION','live_model_calls':0,'empirical_benchmark_runs':0,'network_attempts':len(network)};save('FINAL_VALIDATION.json',final);print(json.dumps(final))
if __name__=='__main__':main()
