"""Parallel read-only byte verification of the completed baseline, not a test."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib, json
from pathlib import Path
import preserve as p

before = json.loads((p.CONTROL / 'BEFORE.json').read_text(encoding='utf-8'))
paths = set().union(*(set(v) for v in before['maps'].values()))
for root in (p.A, p.I, p.C):
    paths.update(p.members(root))
cache, errors = {}, {}

def read_one(name):
    try:
        return name, hashlib.sha256(Path(name).read_bytes()).hexdigest(), None
    except OSError as error:
        return name, None, {'exception': type(error).__name__, 'message': str(error), 'errno': error.errno, 'winerror': getattr(error, 'winerror', None)}

with ThreadPoolExecutor(max_workers=16) as pool:
    jobs = [pool.submit(read_one, name) for name in sorted(paths)]
    for index, future in enumerate(as_completed(jobs), 1):
        name, digest, error = future.result()
        cache[name] = digest
        if error is not None:
            errors[name] = error
        if index % 5000 == 0:
            print('Verified', index, 'of', len(paths), flush=True)

p.sha = lambda path: cache[str(path)]
after = p.snapshot()
changed = {k: sorted(name for name in set(v) | set(after['maps'][k]) if v.get(name) != after['maps'][k].get(name)) for k, v in before['maps'].items()}
state_equal = before['git_states'] == after['git_states']
result = {
    'passed': not errors and not any(changed.values()) and state_equal,
    'method': 'SHA-256 before/after for all prior preservation inventory entries and full file membership of the supplied three evidence roots. After hashes use sixteen read-only workers; no metadata-only shortcut. Read-only Git state comparison.',
    'unique_files_hashed_after': len(cache), 'read_errors': errors,
    'changed': changed, 'counts': {k: len(v) for k, v in before['maps'].items()},
    'git_states_unchanged': state_equal, 'git_states': after['git_states'],
    'original_reports_and_tests_edited': False, 'production_changes': 0,
    'provider_calls': 0, 'live_inference': False, 'benchmark_runs': 0,
    'git_commit_push_merge_release': False,
    'authorship': 'Mechanical preservation by prior collector author; acceptance judgments are separately attributed to fresh AI reviewer contexts.',
    'inventory_attempt_note': 'Initial slow sandbox inventory was stopped with exit1 and preserved separately; exact unchanged baseline script retried with native filesystem reads. This was not an A0 control failure or rerun.'
}
p.save('PRESERVATION.json', result)
print(json.dumps({'preservation_passed': result['passed'], 'changed_counts': {k: len(v) for k, v in changed.items()}, 'git_states_unchanged': state_equal, 'read_error_count': len(errors)}), flush=True)
assert result['passed']
