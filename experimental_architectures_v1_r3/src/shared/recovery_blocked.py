"""Read-only F02 integrity-hold outcome; never a completed RunResult/certificate."""
import base64
import secrets
from .publication import durable
from .strict_json import sha


def blocked_recovery(error):
    pub = error.publication
    if pub is None:
        # No grounded run context: do not invent a recovery result.
        raise error
    report = error.report
    if report.get('overall') != 'BLOCKED' or not report.get('requires_integrity_hold'):
        raise error
    diagnostics = [r for r in report['attempts']
                   if r.get('status') in ('MISSING', 'CORRUPT', 'INCONSISTENT')]
    invariants = list(dict.fromkeys(r.get('detail') or r['code'] for r in diagnostics))
    if not invariants:
        raise error

    def observation(path, include_bytes=False):
        item = {'path': str(path), 'authority': 'CURRENT_OBSERVATION_NOT_PROVENANCE_CERTIFICATION'}
        try:
            raw = path.read_bytes()
        except OSError as problem:
            item['unavailable'] = type(problem).__name__
        else:
            item.update(bytes=len(raw), sha256=sha(raw))
            if include_bytes:
                item['raw_base64'] = base64.b64encode(raw).decode('ascii')
        return item

    # Preserve both the inconsistent input and independent settlement evidence.
    # Never deduplicate/reconstruct a ledger or claim an aggregate from it.
    ledger = observation(pub.ledger.path, True)
    settlements = [observation(p, True) for p in sorted((pub.meta / 'attempts').glob('*.settlement.json'))]
    evidence = [observation(p) for directory, pattern in
                ((pub.meta / 'attempts', '*.json'), (pub.directory / 'wire', '*.jsonl'))
                for p in sorted(directory.glob(pattern))]
    prior_result = observation(pub.final) if pub.final.exists() else None
    directory = pub.meta / 'recovery_holds'
    directory.mkdir(exist_ok=True)
    record = directory / (secrets.token_hex(16) + '.json')
    outcome = {
        'schema_version': 'abc-r3-blocked-recovery-v1',
        'namespace': 'MOCK_WIRING_ONLY_NOT_EMPIRICAL',
        'status': 'BLOCKED', 'is_completed_result': False,
        'request_run_id': pub.request.run_id,
        'journal_integrity': report,
        'result': {
            'run_id': pub.request.run_id, 'task_id': pub.request.task_id,
            'condition_id': pub.request.condition_id,
            'termination_reason': 'EXTERNAL_BLOCKER',
            'physical_attempts': None, 'input_tokens': None,
            'output_tokens': None, 'total_tokens': None, 'wall_time': None,
            'all_generated_candidates': None,
            'accounting_authority': 'UNRESOLVED_CORRUPT_HISTORY_NOT_ZERO',
            'diagnostic_errors': [{'code': 'F02_PROVENANCE_INTEGRITY_HOLD',
                                   'failed_attempt_identity_invariants': invariants}],
        },
        'candidate_history': {
            'status': 'RETAINED_IN_EVIDENCE_NOT_RECONSTRUCTED_OR_CERTIFIED',
            'ledger_observation': ledger,
            'independent_settlement_observations': settlements,
        },
        'evidence_observations': evidence,
        'existing_result_observation': prior_result,
        'scientific_scores': None, 'recovery_provider_calls': 0,
        'diagnostic_record': str(record),
        'publication': 'NONE_INTEGRITY_HOLD_NO_RESULT_CERTIFICATE',
    }
    # Only a new uniquely named diagnostic is written. Existing ledger, wire,
    # response anchors, closure and completed/pending results are untouched.
    durable(record, outcome, True)
    return outcome
