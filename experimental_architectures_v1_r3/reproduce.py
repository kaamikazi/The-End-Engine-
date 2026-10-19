"""Offline reproduction receipt for the partial r3 correction.

Creates a fresh output directory. Does not change historical reviewer inputs.
"""
import copy
import json
import os
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(OUT), str(OUT.parent)]
sys.dont_write_bytecode = True
def offline(event, args):
    if event.startswith('socket.') and event != 'socket.__new__':
        raise PermissionError('OFFLINE_PROVENANCE_REPRODUCTION')
sys.addaudithook(offline)
from tests.corrections.common import partial, Script
from src.shared.session import execute
from src.shared.journals import verify_journals
from src.shared.strict_json import read, canonical, sha
from src.shared.publication import ArtifactIntegrity


def run(target):
    target.mkdir(parents=True, exist_ok=False)
    cases = []
    for kind in ('settlement-downgrade', 'output-handle', 'duplicate-attempt', 'reordered-attempts'):
        d = target / kind
        d.mkdir()
        q, s = partial(d)
        if kind in ('output-handle', 'reordered-attempts'):
            from src.adapters.script import gate
            s.transport.script = Script({'SPARSE_GATE': [gate()]})
            s.assess('SPARSE_GATE', (s.outputs['INITIAL'],))
        path = d / 'budget.json'
        original = path.read_bytes()
        envelope = read(path)
        snapshots = {p.relative_to(d).as_posix(): sha(p.read_bytes()) for p in d.rglob('*')
                     if p.is_file() and (p.is_relative_to(d/'wire') or p.is_relative_to(d/'publication/attempts'))}
        rows = envelope['state']['attempts']
        if kind == 'settlement-downgrade':
            rows[0].update(state='FAILED', candidate=None,
                           response_text='CHANGED_FAILED_TEXT', response_sha256=sha(b'CHANGED_FAILED_TEXT'),
                           error_code='TRANSPORT_ERROR')
        elif kind == 'output-handle':
            rows[0]['candidate']['output_id'] = 'O_UNBOUND_FRESH_REVIEW_HANDLE'
        elif kind == 'duplicate-attempt':
            rows.append(copy.deepcopy(rows[0]))
        else:
            rows.reverse()
        envelope['state_sha256'] = sha(canonical(envelope['state']))
        path.write_bytes(canonical(envelope))
        mutated = path.read_bytes()
        (d/'original_ledger.json').write_bytes(original)
        (d/'mutated_ledger.json').write_bytes(mutated)
        report = verify_journals(s.store)
        s.detach()
        script = Script({})
        try:
            result = execute(q, script, d)
            recovery = {'published': (d/'RESULT.json').exists(),
                        'journal': result['journal_integrity']['overall']}
        except ArtifactIntegrity as error:
            recovery = {'published': (d/'RESULT.json').exists(),
                        'exception': type(error).__name__, 'detail': str(error)}
        preserved = all(sha((d/name).read_bytes()) == digest for name,digest in snapshots.items())
        row = {'case': kind, 'expected': 'BLOCKED', 'observed': report['overall'],
               'pass_or_fail': 'PASS' if report['overall']=='BLOCKED' and not script.seen and preserved else 'FAIL',
               'recovery': recovery, 'original_ledger_sha256': sha(original),
               'mutated_ledger_sha256': sha(mutated), 'independent_hashes': snapshots,
               'independent_evidence_unchanged': preserved, 'new_replay_calls': len(script.seen),
               'journal_report': report, 'live_model_calls': 0, 'empirical_benchmark_runs': 0}
        (d/'case.json').write_text(json.dumps(row, indent=2)+'\n')
        cases.append(row)
    (target/'RESULTS.json').write_text(json.dumps({'cases':cases},indent=2)+'\n')
    return cases


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python -B reproduce.py <new-output-directory>')
    cases = run(Path(sys.argv[1]).resolve())
    print(json.dumps({'tests':len(cases),'passed':sum(c['pass_or_fail']=='PASS' for c in cases),
                      'live_model_calls':0,'empirical_benchmark_runs':0}))
    raise SystemExit(any(c['pass_or_fail']!='PASS' for c in cases))
