"""Round2 baseline, reproductions and immutable protection; writes only R2 outputs."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from unittest.mock import patch
import urllib.request

ROOT=Path(__file__).resolve().parents[1];OUT=Path(__file__).resolve().parent;VAL=OUT/'validation'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
ZIP=ROOT/'END_Experimental_Independent_Review_v1_R2.zip'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
    p=VAL/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def protected():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and not p.is_relative_to(OUT) and p!=ZIP and '.git' not in p.relative_to(ROOT).parts}
def source():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted([*(ROOT/'end_engine').rglob('*.py'),ROOT/'pyproject.toml'])}
def git(*args):return subprocess.run(['git','--no-optional-locks','-c','safe.directory=E:/The End Engine',*args],cwd=ROOT,capture_output=True,check=True,encoding='utf-8').stdout
def suite(which,label):
    scratch=VAL/'scratch';scratch.mkdir(exist_ok=True);os.environ['TEMP']=os.environ['TMP']=str(scratch);tempfile.tempdir=str(scratch)
    attempts=[]
    def blocked(*args,**kwargs):attempts.append('blocked');raise AssertionError('Round2 prohibits runtime networking')
    start=time.perf_counter()
    with (VAL/f'{label}.txt').open('w',encoding='utf-8') as stream:
        with patch.object(socket.socket,'connect',blocked),patch.object(socket.socket,'connect_ex',blocked),patch.object(socket.socket,'sendto',blocked),patch.object(socket,'getaddrinfo',blocked),patch.object(urllib.request.OpenerDirector,'open',blocked):
            tests=unittest.defaultTestLoader.discover(str(ROOT/which),top_level_dir=str(ROOT))
            r=unittest.TextTestRunner(stream=stream,verbosity=2).run(tests)
    data={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),
        'network_attempts':len(attempts),'elapsed_seconds':round(time.perf_counter()-start,3),
        'passed':r.wasSuccessful() and not attempts,'command':f'python -B -m unittest discover -s {which} -t . (network guarded)'}
    save(label+'.json',data);return data
def reproductions(module,label):
    evaluate=module.evaluate_answer;compare=module.compare_candidates
    original=ROOT/'experimental_task_pack_v1';rows=[]
    f=json.loads((original/'fixtures/exp-001/01_correct.json').read_text());base=json.loads(f['candidate_content'])
    notes=['The user claims evidence confirms physical suitability.','According to the source, tests passed.',
        'The user claims [LABEL-FAKE-99] confirms physical suitability.',
        'According to source https://example.invalid/report, tests passed.',
        'The statement "Evidence confirms physical suitability" is unsupported.']
    for i,note in enumerate(notes):
        obj=json.loads(json.dumps(base));obj['notes']=[note];result=evaluate('EXP-001',json.dumps(obj))
        rows.append({'finding_id':'RV-001' if i<4 else 'RV-002','probe':note,'result':result,
            'reviewer_reported_original_overall':True if i<4 else False,'candidate_role':'SYNTHETIC_REPRODUCTION'})
    for tid,filename in [('EXP-001','24_missing_explanation.json'),('EXP-002','25_missing_diagnosis.json')]:
        a=json.loads((original/'fixtures'/tid.lower()/filename).read_text())['candidate_content']
        b=json.loads((original/'fixtures'/tid.lower()/'01_correct.json').read_text())['candidate_content']
        rows.append({'finding_id':'RV-003','task_id':tid,'probe':'missing mandatory explanation/diagnosis to correct',
            'result':compare(tid,a,b),'candidate_role':'SYNTHETIC_PAIR_NOT_LIVE_C0'})
    save(label+'.json',rows);return rows
def baseline():
    assert not (VAL/'protected-before.json').exists()
    before=protected();save('protected-before.json',before);save('source-before.json',source())
    fp=hashlib.sha256(json.dumps(source(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
    version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'];assert version=='0.3.5.2'
    original=ROOT/'experimental_task_pack_v1';hashes={p.relative_to(original).as_posix():sha(p) for p in sorted(original.rglob('*')) if p.is_file()}
    save('original-pack-hashes.json',hashes)
    status=git('status','--short');(VAL/'git-status-before.txt').write_text(status,encoding='utf-8',newline='\n')
    data={'engine_version':version,'engine_fingerprint':fp,'python':platform.python_version(),'git_head':git('rev-parse','HEAD').strip(),
        'git_branch':git('branch','--show-current').strip(),'original_rubric':json.loads((original/'FREEZE_MANIFEST.json').read_text())['rubric_version'],
        'original_pack_files':len(hashes),'original_fixture_count':len(list((original/'fixtures').rglob('*.json'))),
        'reviewer_files_present':[p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.name in ('END_Independent_Review_v1.md','END_Independent_Review_Feedback_v1.csv')],
        'review_source':'Supplied user review/reproductions; reviewer files not locally found unless listed above',
        'round1_review_status':'REVISE','reviewer':'ChatGPT in a separate authoring session, as supplied by user',
        'review_scope':'Targeted code/fixture review; not comprehensive human research audit',
        'engine_tests':suite('tests','engine-baseline'),'original_evaluator_tests':suite('experimental_task_pack_v1/tests','original-evaluator-baseline')}
    assert data['engine_tests']['passed'] and data['original_evaluator_tests']['passed']
    from experimental_task_pack_v1 import evaluators
    probes=reproductions(evaluators,'ROUND1_REPRODUCTIONS_BEFORE')
    assert all(x['result']['overall_pass']==x['reviewer_reported_original_overall'] for x in probes if x['finding_id']!='RV-003')
    assert all(x['result']['meaningful_targeted_repair'] is False and x['result']['final']['task_success'] and not x['result']['c0']['task_success'] for x in probes if x['finding_id']=='RV-003')
    data['all_concrete_review_defects_reproduced']=True;save('BASELINE.json',data)
    assert protected()==before
    print(json.dumps(data))
def copy_pack():
    original=ROOT/'experimental_task_pack_v1'
    for folder in ('tasks','evaluators','fixtures','tests'):
        assert not (OUT/folder).exists();shutil.copytree(original/folder,OUT/folder)
    shutil.copyfile(original/'public_loader.py',OUT/'public_loader.py')
    for p in original.glob('*.md'):shutil.copyfile(p,OUT/p.name)
    archive=VAL/'round1_author_validation';archive.mkdir(exist_ok=True)
    for name in ('RESULTS.json','CORRECTIONS.md','ADVERSARIAL_REVIEW.md','FINAL_VALIDATION.json','REVIEW_STATUS.json','BUDGET_ESTIMATES.json','DRAFT_RUN_MATRIX.json'):
        shutil.copyfile(original/'validation'/name,archive/name)
    shutil.copyfile(original/'FREEZE_MANIFEST.json',VAL/'ORIGINAL_FREEZE_MANIFEST.json')
    print('Copied relevant v1 source/data/docs; original pack untouched; R2 copy not yet corrected.')
if __name__=='__main__':
    if sys.argv[1]=='baseline':baseline()
    elif sys.argv[1]=='copy':copy_pack()
    elif sys.argv[1]=='engine-final':print(json.dumps(suite('tests','engine-final')))
