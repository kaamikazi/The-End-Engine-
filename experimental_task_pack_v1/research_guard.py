"""Offline baseline/final protection. Every write is local to this task pack."""
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from unittest.mock import patch
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
VAL=OUT/'validation'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,data):
    path=VAL/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def protected():
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file()
        and not p.is_relative_to(OUT) and '.git' not in p.relative_to(ROOT).parts}
def source():
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted([*(ROOT/'end_engine').rglob('*.py'),ROOT/'pyproject.toml'])}
def git(*args):
    return subprocess.run(['git','--no-optional-locks','-c','safe.directory=E:/The End Engine',*args],cwd=ROOT,
        capture_output=True,check=True,encoding='utf-8').stdout
def engine_tests(label):
    for key in ('TYPESAFE_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY','ANTHROPIC_API_KEY'):
        os.environ.pop(key,None)
    os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
    scratch=VAL/'scratch';scratch.mkdir(exist_ok=True)
    os.environ['TEMP']=os.environ['TMP']=str(scratch);tempfile.tempdir=str(scratch)
    attempts=[]
    def blocked(*args,**kwargs):attempts.append('blocked');raise AssertionError('Offline task-pack work prohibits networking')
    start=time.perf_counter()
    with (VAL/f'engine-tests-{label}.txt').open('w',encoding='utf-8') as stream:
        with patch.object(socket.socket,'connect',blocked),patch.object(socket.socket,'connect_ex',blocked), \
            patch.object(socket.socket,'sendto',blocked),patch.object(socket,'getaddrinfo',blocked), \
            patch.object(urllib.request.OpenerDirector,'open',blocked):
            suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    record={'command':'Python3.12 -B guarded unittest discover -s tests -t .','tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'network_attempts':len(attempts),'passed':result.wasSuccessful() and not attempts,
        'elapsed_seconds':round(time.perf_counter()-start,3),'live_model_calls':0}
    save(f'engine-tests-{label}.json',record);assert record['passed'];return record
def baseline():
    assert not (VAL/'protected-before.json').exists(),'Baseline must never overwrite its earlier snapshot'
    files=source();fp=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
    assert version=='0.3.5.2' and fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
    save('protected-before.json',protected());save('source-before.json',files)
    status=git('status','--short');(VAL/'git-status-before.txt').write_text(status,encoding='utf-8',newline='\n')
    record={'date':'2026-10-12','version':version,'fingerprint':fp,'python':platform.python_version(),
        'git_head':git('rev-parse','HEAD').strip(),'git_branch':git('branch','--show-current').strip(),
        'source_entries':len(files),'protected_files':len(protected()),'new_architectures_implemented':False}
    record['tests']=engine_tests('baseline');save('BASELINE.json',record)
    assert protected()==json.loads((VAL/'protected-before.json').read_text(encoding='utf-8'))
    print(json.dumps(record))
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='baseline':baseline()
    elif len(sys.argv)>1 and sys.argv[1]=='tests':print(json.dumps(engine_tests('final')))
    else:raise SystemExit('Use baseline once; tests for final offline suite')
