"""Offline tests/hash validation; never updates historical pack validation records."""
import hashlib,json,os,socket,sys,tempfile,time,unittest,urllib.request
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];OUT=Path(__file__).resolve().parent;VAL=OUT/'validation'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
VAL.mkdir(exist_ok=True);scratch=VAL/'scratch';scratch.mkdir(exist_ok=True)
tempfile.tempdir=str(scratch);os.environ['TEMP']=os.environ['TMP']=str(scratch)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def suite(path,label):
    attempts=[]
    def block(*a,**kw):attempts.append('blocked');raise AssertionError('Checkpoint offline tests only')
    start=time.perf_counter()
    with (VAL/(label+'.txt')).open('w',encoding='utf-8') as stream:
        with patch.object(socket.socket,'connect',block),patch.object(socket.socket,'connect_ex',block),patch.object(socket.socket,'sendto',block),patch.object(socket,'getaddrinfo',block),patch.object(urllib.request.OpenerDirector,'open',block):
            s=unittest.defaultTestLoader.discover(str(ROOT/path),top_level_dir=str(ROOT));r=unittest.TextTestRunner(stream=stream,verbosity=2).run(s)
    return {'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'network_attempts':len(attempts),'elapsed_seconds':round(time.perf_counter()-start,3),'passed':r.wasSuccessful() and not attempts}
data={'engine':suite('tests','engine'),'active_evaluator':suite('experimental_task_pack_v1_safety_boundary/tests','evaluator')}
src={p.relative_to(ROOT).as_posix():sha(p) for p in sorted([*(ROOT/'end_engine').rglob('*.py'),ROOT/'pyproject.toml'])}
fp=hashlib.sha256(json.dumps(src,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
frozen={}
for name in ('experimental_task_pack_v1','experimental_task_pack_v1_r2','experimental_task_pack_v1_r3','experimental_task_pack_v1_safety_boundary'):
    manifest=json.loads((ROOT/name/'FREEZE_MANIFEST.json').read_text())
    # Freeze formats are versioned; generic before/after protection covers all files.
    frozen[name]={'manifest_sha256':sha(ROOT/name/'FREEZE_MANIFEST.json'),'version':manifest.get('rubric_version'),'status':manifest.get('freeze_status',manifest.get('status'))}
    if name.endswith('safety_boundary'):
        assert all(sha(ROOT/name/p)==h for p,h in manifest['sha256'].items());frozen[name]['scientific_hashes_verified']=len(manifest['sha256'])
data.update(engine_version='0.3.5.2',engine_fingerprint=fp,python=sys.version.split()[0],rubric='exp-pack-1.1.0-draft',independent_review='PENDING',frozen_manifests=frozen,model_calls=0,
    test_commands=['PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1 python -B checkpoint_20261013/validate_checkpoint.py (network-blocked unittest discovery: tests; experimental_task_pack_v1_safety_boundary/tests)'])
assert data['engine']['passed'] and data['active_evaluator']['passed']
(VAL/'TEST_RESULTS.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(data))
