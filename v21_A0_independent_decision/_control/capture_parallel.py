"""Read-only baseline capture with concurrent byte reads, never a test runner."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib, json
from pathlib import Path
import preserve as p

assert not (p.CONTROL / 'BEFORE.json').exists()
prior = json.loads((p.C / '_control/BEFORE.json').read_text(encoding='utf-8'))
paths = set().union(*(set(v) for v in prior.values()))
for root in (p.A, p.I, p.C):
    paths.update(p.members(root))
cache = {}
def read_one(name):
    return name, hashlib.sha256(Path(name).read_bytes()).hexdigest()
with ThreadPoolExecutor(max_workers=16) as pool:
    jobs = [pool.submit(read_one, name) for name in sorted(paths)]
    for index, future in enumerate(as_completed(jobs), 1):
        name, digest = future.result()
        cache[name] = digest
        if index % 5000 == 0:
            print('Captured', index, 'of', len(paths), flush=True)
p.sha = lambda path: cache[str(path)]
before = p.snapshot()
p.save('_control/BEFORE.json', before)
# Compare every inherited protected entry with its earlier signed-by-hash inventory,
# in addition to the before/after comparison. This baseline is captured after the
# independent scratch execution; those supplied roots were used read only.
prior_delta = {k: sorted(name for name, digest in files.items() if cache[name] != digest) for k, files in prior.items()}
p.save('_control/PRIOR_INVENTORY_COMPARISON.json', {'prior': str(p.C / '_control/BEFORE.json'), 'changed': prior_delta, 'passed': not any(prior_delta.values()), 'capture_timing': 'After independent synthetic scratch run; original supplied roots were read only. Independently compare each inherited original hash and each supplied evidence manifest.'})
manifests = []
for root, name in [(p.A, '_control/EVIDENCE_FILE_HASHES.json'), (p.I, '_evidence/INVESTIGATION_FILE_HASHES.json'), (p.C, '_control/EVIDENCE_FILE_HASHES.json')]:
    manifest = json.loads((root / name).read_text(encoding='utf-8'))
    failures = [n for n, entry in manifest['files'].items() if p.sha(root / n) != entry['sha256']]
    manifests.append({'root': str(root), 'manifest': name, 'manifest_sha256': p.sha(root / name), 'entries': len(manifest['files']), 'failures': failures})
p.save('_control/INPUT_MANIFEST_VERIFICATION.json', manifests)
assert not any(prior_delta.values())
assert not any(x['failures'] for x in manifests)
print('BASELINE_READY', flush=True)
