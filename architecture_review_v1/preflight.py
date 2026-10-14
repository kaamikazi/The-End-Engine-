"""Read-only repository verification; all new outputs stay in this review directory."""
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import time
import tomllib
import unittest
from unittest.mock import patch
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def hashes(paths):
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths) if p.is_file()}


def protected():
    return hashes(p for p in ROOT.rglob('*') if p.is_file() and
                  not p.is_relative_to(OUT) and '.git' not in p.relative_to(ROOT).parts)


def source():
    return hashes([*(ROOT/'end_engine').rglob('*.py'),ROOT/'pyproject.toml'])


def save(name, value, exclusive=False):
    with (OUT/name).open('x' if exclusive else 'w',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')


def git(*args):
    return subprocess.run(['git','--no-optional-locks','-c','safe.directory=E:/The End Engine',*args],
        cwd=ROOT,capture_output=True,encoding='utf-8',check=True).stdout


def main():
    for name in ('TYPESAFE_API_KEY','GOOGLE_API_KEY','GEMINI_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY'):
        os.environ.pop(name,None)
    files=source();fingerprint=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
    assert version=='0.3.5.2' and fingerprint=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
    save('SOURCE_BEFORE.json',files,True);save('PROTECTED_BEFORE.json',protected(),True)
    (OUT/'git-status-before.txt').write_text(git('status','--short'),encoding='utf-8')
    baseline={'version':version,'source_fingerprint':fingerprint,'source_files':len(files),
              'python':platform.python_version(),'git_head':git('rev-parse','HEAD').strip(),
              'git_branch':git('branch','--show-current').strip()}
    save('BASELINE.json',baseline,True)
    # Existing tests own temporary fixture directories; keep those writes inside this review.
    scratch=OUT/'test_scratch';scratch.mkdir(exist_ok=True)
    os.environ['TEMP']=os.environ['TMP']=str(scratch)
    import tempfile
    tempfile.tempdir=str(scratch)
    attempts=[]
    def blocked(*args,**kwargs):
        attempts.append('blocked runtime networking');raise AssertionError('Review prohibits runtime networking')
    start=time.perf_counter()
    with (OUT/'offline-tests.txt').open('w',encoding='utf-8') as stream:
        with patch.object(socket.socket,'connect',blocked),patch.object(socket.socket,'connect_ex',blocked), \
             patch.object(socket.socket,'sendto',blocked),patch.object(socket,'getaddrinfo',blocked), \
             patch.object(urllib.request.OpenerDirector,'open',blocked):
            suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    tests={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
           'skipped':len(result.skipped),'network_attempts':len(attempts),'live_inference_calls':0,
           'elapsed_seconds':round(time.perf_counter()-start,3),'passed':result.wasSuccessful() and not attempts}
    save('offline-tests.json',tests,True)
    assert source()==files and protected()==json.loads((OUT/'PROTECTED_BEFORE.json').read_text())
    assert tests['passed']
    print(json.dumps({'baseline':baseline,'tests':tests}))


if __name__=='__main__':main()
