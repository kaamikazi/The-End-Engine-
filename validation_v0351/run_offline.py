"""Offline release validation. Blocks runtime network access; never loads live adapters."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import unittest
from unittest.mock import patch
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
PROTECTED = ('v035_core_regression_pilot', 'benchmark_alpha', 'benchmark_beta',
             'benchmark_beta_gemini', 'validation_jev')


def hashes(paths):
    files = []
    for path in paths:
        files.extend(sorted(path.rglob('*')) if path.is_dir() else [path])
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files if p.is_file()}


def source():
    return hashes([*sorted((ROOT / 'end_engine').rglob('*.py')), ROOT / 'pyproject.toml'])


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def freeze():
    if (OUT / 'protected-before.json').exists():
        raise RuntimeError('Baseline already frozen; never overwrite it')
    files = source()
    git = lambda *args: subprocess.run(['git', '-c', 'safe.directory=E:/The End Engine', *args],
                                      cwd=ROOT, check=True, capture_output=True, encoding='utf-8').stdout
    save('source-before.json', files)
    save('protected-before.json', hashes([ROOT / name for name in PROTECTED]))
    (OUT / 'git-status-before.txt').write_text(git('status', '--short'), encoding='utf-8')
    save('baseline.json', {'version': '0.3.5', 'python': platform.python_version(),
         'source_sha256': hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
         'git_commit': git('rev-parse', 'HEAD').strip(), 'decision_provider_default': 'baseline'})


def tests(label, module=None):
    attempts = []
    def blocked(*args, **kwargs):
        attempts.append('runtime_network_attempt')
        raise AssertionError('Runtime networking is disabled for release validation')
    for name in ('TYPESAFE_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'):
        os.environ.pop(name, None)
    with (OUT / f'{label}.txt').open('w', encoding='utf-8') as stream:
        with patch.object(socket.socket, 'connect', blocked), patch.object(socket.socket, 'connect_ex', blocked), \
             patch.object(socket, 'getaddrinfo', blocked), patch.object(socket.socket, 'sendto', blocked), \
             patch.object(urllib.request.OpenerDirector, 'open', blocked):
            suite = (unittest.defaultTestLoader.loadTestsFromName(module) if module else
                     unittest.defaultTestLoader.discover(str(ROOT / 'tests'), top_level_dir=str(ROOT)))
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    data = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
            'skipped': len(result.skipped), 'network_attempts': len(attempts), 'live_model_calls': 0,
            'success': result.wasSuccessful() and not attempts, 'module': module or 'tests discovery'}
    save(f'{label}.json', data)
    print(json.dumps(data))
    if not data['success']:
        raise SystemExit(1)


def audit():
    before = json.loads((OUT / 'protected-before.json').read_text(encoding='utf-8'))
    after = hashes([ROOT / name for name in PROTECTED])
    changed = [name for name in before if after.get(name) != before[name]]
    added = sorted(set(after) - set(before))
    save('protected-after.json', after)
    save('history-audit.json', {'checked_files': len(before), 'changed_or_missing': changed,
                              'added': added, 'success': not changed and not added})
    if changed or added:
        raise RuntimeError('Protected historical evidence changed')
    files = source()
    save('source-after.json', files)
    save('identity-after.json', {'python': platform.python_version(), 'files': len(files),
         'source_sha256': hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()})
    print(json.dumps({'protected_files': len(before), 'unchanged': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('freeze', 'tests', 'audit'))
    parser.add_argument('--label', default='engine-tests-after')
    parser.add_argument('--module')
    args = parser.parse_args()
    if args.command == 'freeze': freeze()
    elif args.command == 'audit': audit()
    else: tests(args.label, args.module)
