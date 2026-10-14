"""Offline corrective-release checks; no inference or runtime networking permitted."""
import argparse
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


def protected_paths():
    return [*ROOT.glob('benchmark_*'), ROOT/'v035_core_regression_pilot',
            ROOT/'v0351_core_regression_pilot',
            *(p for p in ROOT.glob('validation_*') if p != OUT),
            *ROOT.glob('IMPLEMENTATION_REPORT*.md'), ROOT/'docs', ROOT/'tests/fixtures']


def hashes(paths):
    files = []
    for p in paths:
        files.extend(p.rglob('*') if p.is_dir() else [p])
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(files)) if p.is_file()}


def source():
    return hashes([*(ROOT/'end_engine').rglob('*.py'), ROOT/'pyproject.toml'])


def save(name, data, exclusive=False):
    with (OUT/name).open('x' if exclusive else 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def git(*args):
    return subprocess.run(['git', '--no-optional-locks', '-c',
        'safe.directory=E:/The End Engine', *args], cwd=ROOT, capture_output=True,
        encoding='utf-8', check=True).stdout


def freeze():
    files = source()
    save('source-before.json', files, True)
    save('editable-before.json', hashes([ROOT/'end_engine', ROOT/'tests',
         ROOT/'pyproject.toml', ROOT/'README.md']), True)
    save('protected-before.json', hashes(protected_paths()), True)
    (OUT/'git-status-before.txt').write_text(git('status', '--short'), encoding='utf-8')
    save('baseline.json', {'version': tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'],
         'source_sha256': hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
         'source_files': len(files), 'python': platform.python_version(),
         'git_head': git('rev-parse', 'HEAD').strip(), 'git_branch': git('branch', '--show-current').strip()}, True)


def ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from ids(item)
        else:
            yield item.id()


def tests(label, selector):
    attempts = []
    def blocked(*args, **kwargs):
        attempts.append('runtime_network_attempt')
        raise AssertionError('Runtime networking prohibited during v0352 validation')
    for name in ('TYPESAFE_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY',
                 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'):
        os.environ.pop(name, None)
    start = time.perf_counter()
    with (OUT/(label+'.txt')).open('w', encoding='utf-8') as stream:
        with patch.object(socket.socket, 'connect', blocked), patch.object(socket.socket, 'connect_ex', blocked), \
             patch.object(socket.socket, 'sendto', blocked), patch.object(socket, 'getaddrinfo', blocked), \
             patch.object(urllib.request.OpenerDirector, 'open', blocked):
            if selector == 'prior':
                suite = unittest.defaultTestLoader.loadTestsFromNames(json.loads((OUT/'prior-test-ids.json').read_text()))
            elif selector == 'new':
                suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_v0352_regressions')
            else:
                suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), top_level_dir=str(ROOT))
            if label == 'engine-tests-before':
                save('prior-test-ids.json', list(ids(suite)), True)
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    data = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
            'skipped': len(result.skipped), 'network_attempts': len(attempts), 'live_model_calls': 0,
            'selector': selector, 'success': result.wasSuccessful() and not attempts,
            'elapsed_seconds': round(time.perf_counter()-start, 3)}
    save(label+'.json', data)
    print(json.dumps(data))
    if not data['success']:
        raise SystemExit(1)


def audit():
    before = json.loads((OUT/'protected-before.json').read_text())
    after = hashes(protected_paths())
    # The new implementation report is the only new root report allowed.
    after.pop('IMPLEMENTATION_REPORT_v0.3.5.2.md', None)
    save('protected-after.json', after)
    save('history-audit.json', {'files': len(before), 'unchanged': before == after})
    if before != after:
        raise RuntimeError('Protected history changed; STOP')
    current = source(); save('source-after.json', current)
    save('identity-after.json', {'version': tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'],
        'files': len(current), 'source_sha256': hashlib.sha256(json.dumps(current, sort_keys=True, separators=(',', ':')).encode()).hexdigest()})
    original = json.loads((OUT/'editable-before.json').read_text())
    edited = hashes([ROOT/'end_engine', ROOT/'tests', ROOT/'pyproject.toml', ROOT/'README.md'])
    save('changed-files.json', sorted(k for k in set(original)|set(edited) if original.get(k) != edited.get(k)))
    (OUT/'git-status-after.txt').write_text(git('status', '--short'), encoding='utf-8')
    print(json.dumps({'protected_files': len(before), 'unchanged': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('freeze', 'tests', 'audit'))
    parser.add_argument('--label', default='engine-tests-after')
    parser.add_argument('--selector', default='all', choices=('all', 'prior', 'new'))
    args = parser.parse_args()
    if args.command == 'freeze': freeze()
    elif args.command == 'tests': tests(args.label, args.selector)
    else: audit()
