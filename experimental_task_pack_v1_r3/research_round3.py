"""Read-only R3 preflight/protection. No model or provider execution."""
import hashlib,json,os,platform,shutil,socket,subprocess,sys,tempfile,time,tomllib,unittest,urllib.request,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];OUT=Path(__file__).resolve().parent;VAL=OUT/'validation';ZIP=ROOT/'END_Experimental_Independent_Review_v1_R3.zip'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):
    p=VAL/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def protected():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and not p.is_relative_to(OUT) and p!=ZIP and '.git' not in p.relative_to(ROOT).parts}
def source():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted([*(ROOT/'end_engine').rglob('*.py'),ROOT/'pyproject.toml'])}
def git(*args):return subprocess.run(['git','--no-optional-locks','-c','safe.directory=E:/The End Engine',*args],cwd=ROOT,capture_output=True,encoding='utf-8',check=True).stdout
def suite(which,label):
    scratch=VAL/'scratch';scratch.mkdir(parents=True,exist_ok=True);tempfile.tempdir=str(scratch);os.environ['TEMP']=os.environ['TMP']=str(scratch)
    attempts=[]
    def block(*a,**kw):attempts.append('blocked');raise AssertionError('R3 offline only')
    start=time.perf_counter()
    with (VAL/(label+'.txt')).open('w',encoding='utf-8') as f:
        with patch.object(socket.socket,'connect',block),patch.object(socket.socket,'connect_ex',block),patch.object(socket.socket,'sendto',block),patch.object(socket,'getaddrinfo',block),patch.object(urllib.request.OpenerDirector,'open',block):
            tests=unittest.defaultTestLoader.discover(str(ROOT/which),top_level_dir=str(ROOT));r=unittest.TextTestRunner(stream=f,verbosity=2).run(tests)
    data={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'network_attempts':len(attempts),'passed':r.wasSuccessful() and not attempts,'elapsed_seconds':round(time.perf_counter()-start,3)};save(label+'.json',data);return data
def baseline():
    assert not (VAL/'protected-before.json').exists();save('protected-before.json',protected());save('source-before.json',source())
    version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'];fp=hashlib.sha256(json.dumps(source(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert version=='0.3.5.2' and fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
    for pack in ('experimental_task_pack_v1','experimental_task_pack_v1_r2'):
        save(pack+'-original-hashes.json',{p.relative_to(ROOT/pack).as_posix():sha(p) for p in sorted((ROOT/pack).rglob('*')) if p.is_file()})
    (VAL/'git-status-before.txt').write_text(git('status','--short'),encoding='utf-8',newline='\n')
    reviewer_names=('END_Independent_Review_R2.md','END_Independent_Review_R2_Feedback.csv','END_R2_Independent_Repro.py','END_R2_Independent_Probe_Results.json')
    files=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.name in reviewer_names]
    data={'engine_version':version,'engine_fingerprint':fp,'python':platform.python_version(),'git_head':git('rev-parse','HEAD').strip(),'git_branch':git('branch','--show-current').strip(),'reviewer_files_present':files,
        'review_source':'Exact supplied independent R2 findings/probes when standalone reviewer files absent','independent_round2_verdict':'REVISE','engine_tests':suite('tests','engine-baseline'),'r2_evaluator_tests':suite('experimental_task_pack_v1_r2/tests','r2-baseline')}
    assert data['engine_tests']['passed'] and data['r2_evaluator_tests']['passed']
    archive=ROOT/'END_Experimental_Independent_Review_v1_R2.zip';target=VAL/'scratch/extracted_r2';target.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():assert not Path(name).is_absolute() and '..' not in Path(name).parts
        z.extractall(target)
    runroot=target/'END_Experimental_Independent_Review_v1_R2'
    program=r'''import json,socket,urllib.request
from pathlib import Path
from unittest.mock import patch
def block(*a,**kw):raise AssertionError('Independent reproduction is offline')
with patch.object(socket.socket,'connect',block),patch.object(socket,'getaddrinfo',block),patch.object(urllib.request.OpenerDirector,'open',block):
 from experimental_task_pack_v1_r2.evaluators import evaluate_answer
 import experimental_task_pack_v1_r2.evaluators as module
 assert Path(module.__file__).resolve().is_relative_to(Path.cwd().resolve())
 rows=[]
 for tid in ('EXP-001','EXP-002'):
  f=json.loads(Path('experimental_task_pack_v1_r2/fixtures/'+tid.lower()+'/01_correct.json').read_text())
  for finding,note,expected in [('R2-NEW-001','If evidence confirmed X, we could conclude Y, although we ran the tests yesterday.',True),('R2-NEW-001','If evidence confirmed X, we could conclude Y, though tests passed.',True),('R2-NEW-002','The citation ['+('LABEL' if tid=='EXP-001' else 'POL')+'-FAKE-99] is not registered.',False),('R2-NEW-003','We did not execute any tests.',None)]:
   obj=json.loads(f['candidate_content']);obj['notes']=[note];r=evaluate_answer(tid,json.dumps(obj));rows.append({'finding':finding,'task_id':tid,'note':note,'original_result':r,'review_reported_overall':expected,'matches_review':r['overall_pass'] is expected})
  obj=json.loads(f['candidate_content']);obj['verification_status']='not_executed';obj['notes']=['If evidence confirmed X, we could conclude Y, although we ran the tests yesterday.'];r=evaluate_answer(tid,json.dumps(obj));rows.append({'finding':'R2-NEW-001','task_id':tid,'note':obj['notes'][0],'verification_status':'not_executed','original_result':r,'review_reported_overall':True,'matches_review':r['overall_pass'] is True})
 print(json.dumps({'module_source':str(Path(module.__file__).resolve()),'extracted_R2_confirmed':True,'probes':rows,'runtime_network_calls':0}))'''
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1';env.pop('PYTHONPATH',None)
    p=subprocess.run([sys.executable,'-B','-c',program],cwd=runroot,capture_output=True,encoding='utf-8',env=env,timeout=30);assert p.returncode==0,p.stderr
    reproduced=json.loads(p.stdout);save('ROUND2_REPRODUCTION_BEFORE.json',reproduced);assert all(r['matches_review'] for r in reproduced['probes'])
    data['all_three_findings_reproduced']=True;data['R2_zip_sha256']=sha(archive);save('BASELINE.json',data)
    assert protected()==json.loads((VAL/'protected-before.json').read_text());print(json.dumps(data))
def copy_pack():
    old=ROOT/'experimental_task_pack_v1_r2'
    for folder in ('tasks','evaluators','fixtures','paired_fixtures','tests','round1_reference'):
        assert not (OUT/folder).exists();shutil.copytree(old/folder,OUT/folder)
    shutil.copyfile(old/'public_loader.py',OUT/'public_loader.py')
    for f in old.glob('*.md'):shutil.copyfile(f,OUT/f.name)
    hist=VAL/'r2_history';hist.mkdir()
    for name in ('FREEZE_MANIFEST.json',):shutil.copyfile(old/name,hist/name)
    for name in ('RESULTS.json','ROUND1_FINDING_DISPOSITIONS.csv','ORIGINAL_FIXTURE_LABELS.json','ORIGINAL_57_REVALIDATION.json','ROUND2_REPRODUCTIONS_AFTER.json','ROUND1_REPRODUCTIONS_BEFORE.json','BUDGET_ESTIMATES.json','DRAFT_RUN_MATRIX.json'):
        shutil.copyfile(old/'validation'/name,hist/name)
    shutil.copyfile(old/'validation/ORIGINAL_FIXTURE_LABELS.json',VAL/'ORIGINAL_FIXTURE_LABELS.json')
    ref=OUT/'round2_reference';shutil.copytree(old/'evaluators',ref/'evaluators');shutil.copytree(old/'tasks',ref/'tasks')
    print('Relevant R2 evidence copied; originals protected.')
if __name__=='__main__':
    if sys.argv[1]=='baseline':baseline()
    elif sys.argv[1]=='copy':copy_pack()
    elif sys.argv[1]=='engine-final':print(json.dumps(suite('tests','engine-final')))
