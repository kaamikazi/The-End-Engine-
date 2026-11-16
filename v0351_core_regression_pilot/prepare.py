"""Read-only repository preflight; all new records stay in this replay directory."""
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

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
PROTECTED=('v035_core_regression_pilot','benchmark_alpha','benchmark_beta',
           'benchmark_beta_gemini','validation_jev','validation_v0351')


def hashes(paths):
    files=[]
    for path in paths:files.extend(sorted(path.rglob('*')) if path.is_dir() else [path])
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}


def source():return hashes([*sorted((ROOT/'end_engine').rglob('*.py')),ROOT/'pyproject.toml'])


def save(name,data):
    path=OUT/'preflight'/name
    if path.exists():raise RuntimeError('Preflight record already exists; never overwrite the baseline')
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def main():
    for name in ('TYPESAFE_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY'):
        os.environ.pop(name,None)
    files=source();save('engine-source-before.json',files)
    save('protected-before.json',hashes([ROOT/n for n in PROTECTED]+list(ROOT.glob('IMPLEMENTATION_REPORT*.md'))+[ROOT/'README.md']))
    git=lambda *args:subprocess.run(['git','-c','safe.directory=E:/The End Engine',*args],cwd=ROOT,
                                   capture_output=True,check=True,encoding='utf-8').stdout
    (OUT/'preflight/git-status-before.txt').write_text(git('status','--short'),encoding='utf-8')
    attempts=[]
    def blocked(*args,**kwargs):
        attempts.append('blocked runtime networking')
        raise AssertionError('Preflight offline suite cannot use networking')
    start=time.perf_counter()
    with (OUT/'preflight/engine-tests.txt').open('w',encoding='utf-8') as stream:
        with patch.object(socket.socket,'connect',blocked),patch.object(socket.socket,'connect_ex',blocked), \
             patch.object(socket.socket,'sendto',blocked),patch.object(socket,'getaddrinfo',blocked), \
             patch.object(urllib.request.OpenerDirector,'open',blocked):
            suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    tests={'command':'python -m unittest discover -s tests -t . (network-blocked unittest API)',
           'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
           'skipped':len(result.skipped),'network_attempts':len(attempts),
           'elapsed_seconds':round(time.perf_counter()-start,3)}
    assert files==source(),'Source changed during preflight'
    from end_engine import EngineConfig
    identity={'version':tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version'],
        'source_sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'fingerprint_scope':'end_engine/**/*.py and pyproject.toml','files':len(files),
        'python':platform.python_version(),'git_commit':git('rev-parse','HEAD').strip(),
        'offline_tests':tests,'decision_provider':EngineConfig().decision.provider}
    save('engine-identity.json',identity)
    expected=json.loads((ROOT/'validation_v0351/source-after.json').read_text(encoding='utf-8'))
    if (identity['version']!='0.3.5.1' or files!=expected or not result.wasSuccessful() or attempts
            or identity['decision_provider']!='baseline'):
        raise SystemExit('Actual version/source/offline/default-provider preflight failed; no inference authorized by this preflight')
    print(json.dumps(identity,indent=2))


if __name__=='__main__':main()
