"""Mechanical read-only protection checks; no acceptance judgments."""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / '_control'
BASE = Path('E:/The End Engine')
A = BASE / 'v21_A0_feasibility'
I = BASE / 'v21_A0_blocker_investigation'
C = BASE / 'v21_A0_collector_correction'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def git_state(path):
    def run(*args):
        return subprocess.check_output(['git', '--no-optional-locks', '-C', str(path), '-c', 'safe.directory=' + path.as_posix(), *args], text=True).strip()
    return {'HEAD': run('rev-parse', 'HEAD'), 'branch': run('branch', '--show-current'), 'status': run('status', '--porcelain=v1'), 'staged': run('diff', '--cached', '--name-status')}

def members(path):
    return sorted(str(p) for p in path.rglob('*') if p.is_file() and '.git' not in p.relative_to(path).parts)

def snapshot():
    prior = json.loads((C / '_control/BEFORE.json').read_text(encoding='utf-8'))
    maps = {}
    for label, files in prior.items():
        maps[label] = {p: sha(Path(p)) for p in files}
        print(label, len(files), flush=True)
    # Capture full membership of all three supplied evidence roots, including manifest files.
    for label, path in [('A0_all', A), ('investigation_all', I), ('collector_correction_all', C)]:
        maps[label] = {p: sha(Path(p)) for p in members(path)}
    states = {str(p): git_state(p) for p in [A / 'checkout', Path('E:/END-v102-V21-Contract-Checkpoint'), Path('E:/END-Cognitive-Architectures-Fix-v102'), Path('E:/END-v102-WIP-Checkpoint-20261019')]}
    main = git_state(BASE)
    # Root status will gain the new reviewer directory only; track existing tracked files separately.
    states[str(BASE)] = {k: v for k, v in main.items() if k != 'status'}
    return {'maps': maps, 'git_states': states}

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'before':
        assert not (CONTROL / 'BEFORE.json').exists()
        before = snapshot()
        save('_control/BEFORE.json', before)
        manifests = []
        for root, name in [(A, '_control/EVIDENCE_FILE_HASHES.json'), (I, '_evidence/INVESTIGATION_FILE_HASHES.json'), (C, '_control/EVIDENCE_FILE_HASHES.json')]:
            manifest = json.loads((root / name).read_text(encoding='utf-8'))
            failures = [n for n, entry in manifest['files'].items() if sha(root / n) != entry['sha256']]
            manifests.append({'root': str(root), 'manifest': name, 'manifest_sha256': sha(root / name), 'entries': len(manifest['files']), 'failures': failures})
        save('_control/INPUT_MANIFEST_VERIFICATION.json', manifests)
        assert not any(x['failures'] for x in manifests)
        print('BASELINE_READY', flush=True)
    elif mode == 'after':
        before = json.loads((CONTROL / 'BEFORE.json').read_text(encoding='utf-8'))
        after = snapshot()
        changed = {k: sorted(p for p in set(v) | set(after['maps'][k]) if v.get(p) != after['maps'][k].get(p)) for k, v in before['maps'].items()}
        state_equal = before['git_states'] == after['git_states']
        result = {'passed': not any(changed.values()) and state_equal, 'method': 'SHA-256 of all prior preservation inventory entries plus complete file membership of supplied three evidence roots; before/after read-only Git identities/status of isolated sources; root HEAD/branch/staged only.', 'changed': changed, 'counts': {k: len(v) for k, v in before['maps'].items()}, 'git_states_unchanged': state_equal, 'git_states': after['git_states'], 'original_reports_and_tests_edited': False, 'production_changes': 0, 'provider_calls': 0, 'live_inference': False, 'benchmark_runs': 0, 'git_commit_push_merge_release': False, 'authorship': 'Mechanical preservation by prior collector author; independent acceptance judgments are separately attributed.'}
        save('PRESERVATION.json', result)
        print(json.dumps({'preservation_passed': result['passed'], 'changed_counts': {k: len(v) for k, v in changed.items()}, 'git_states_unchanged': state_equal}), flush=True)
        assert result['passed']
    else:
        raise SystemExit('before or after required')
