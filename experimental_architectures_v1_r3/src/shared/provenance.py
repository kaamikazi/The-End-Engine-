"""F02 graph reconciliation. Verification never creates historical evidence.

The ledger's checksum is local consistency only. Settlement witnesses are
exclusive files captured under the existing run lease immediately after the
unchanged gateway settles. They corroborate separately recorded dispatch and
raw-response anchors; they are not provider signatures or hostile-host security.
"""
import json
import re
from pathlib import Path
from dataclasses import asdict
from .strict_json import canonical, read, sha, loads
from .publication import durable, ArtifactIntegrity


class ProvenanceFault(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ProvenanceFault(code)


def settlement_path(pub, attempt_id):
    return pub.meta / 'attempts' / (str(attempt_id).zfill(6) + '.settlement.json')


def record_settlement(pub, attempt_id):
    """Execution-only hook; never called by restore, verification or finalization."""
    row = next(a for a in pub.ledger.state()['attempts'] if a['attempt_id'] == attempt_id)
    if row['state'] == 'RESERVED':
        return
    require(row['run_id'] == pub.request.run_id, 'SETTLEMENT_RUN_OWNERSHIP')
    # A new witness cannot claim dispatch evidence which was never recorded.
    anchor = pub.attempt_anchor(attempt_id)
    if not anchor.exists():
        return
    response = pub.response_anchor(attempt_id)
    value = {'schema_version': 'abc-r3-settlement-v1',
             'identity_sha256': pub.identity_sha, 'run_id': pub.request.run_id,
             'attempt_id': attempt_id, 'settlement': row,
             'dispatch_anchor_sha256': sha(anchor.read_bytes()),
             'response_anchor_sha256': sha(response.read_bytes()) if response.exists() else None}
    durable(settlement_path(pub, attempt_id), value, True)


def record_reservation(pub, sealed):
    row = next(a for a in pub.ledger.state()['attempts']
               if a['attempt_id'] == sealed.physical_call_reservation)
    require(row['state'] == 'RESERVED' and row['run_id'] == pub.request.run_id,
            'RESERVATION_OWNERSHIP')
    value = {'schema_version': 'abc-r3-reservation-v1', 'identity_sha256': pub.identity_sha,
             'run_id': pub.request.run_id, 'attempt_id': row['attempt_id'],
             'reservation': row}
    durable(pub.meta / 'attempts' / (str(row['attempt_id']).zfill(6) + '.reservation.json'),
            value, True)


def reconcile(pub):
    """Validate global reservation order and this run's independent graph."""
    state = pub.ledger.state()
    all_rows = state['attempts']
    require(type(all_rows) is list, 'ATTEMPT_ARRAY')
    ids = [a.get('attempt_id') for a in all_rows]
    require(all(type(i) is int for i in ids) and ids == list(range(1, len(ids) + 1)),
            'GLOBAL_RESERVATION_ORDER_OR_UNIQUENESS')
    own = [a for a in all_rows if a.get('run_id') == pub.request.run_id]
    own_ids = {a['attempt_id'] for a in own}
    require(len(own) <= pub.effective.attempt_budget, 'ATTEMPT_LIMIT')
    files = {}
    def observed(path):
        raw = path.read_bytes()
        files[path.relative_to(pub.directory).as_posix()] = sha(raw)
        return loads(raw, max_bytes=64000000, max_depth=128, max_nodes=2000000)
    # Bidirectional coverage: walking only the mutable ledger misses erased rows.
    for path in (pub.meta / 'attempts').glob('*.json'):
        match = re.fullmatch(r'(\d+)\.(?:response\.|settlement\.|reservation\.)?json', path.name)
        require(match is not None, 'UNRECOGNIZED_ATTEMPT_ANCHOR')
        require(int(match.group(1)) in own_ids, 'ORPHAN_INDEPENDENT_ATTEMPT_EVIDENCE')
    from ..adapters.gateway import StageCompiler
    compiler = StageCompiler()
    compiler.register(pub.effective)
    prior = []
    handles = {}
    stages = []
    uncovered = []
    for row in own:
        aid = row['attempt_id']
        require(row['state'] in ('RESERVED', 'SUCCEEDED', 'FAILED', 'CANCELED',
                                 'INTERRUPTED', 'PROTOCOL_FAILURE'), 'SETTLEMENT_STATE')
        dispatch = pub.attempt_anchor(aid)
        reservation = pub.meta / 'attempts' / (str(aid).zfill(6) + '.reservation.json')
        if reservation.exists():
            reserved = observed(reservation)
            require(reserved['schema_version'] == 'abc-r3-reservation-v1' and
                    reserved['identity_sha256'] == pub.identity_sha and
                    reserved['attempt_id'] == aid and reserved['run_id'] == pub.request.run_id,
                    'RESERVATION_IDENTITY')
            require(all(reserved['reservation'][k] == row[k] for k in
                        ('attempt_id', 'run_id', 'purpose', 'token_ceiling',
                         'seconds_ceiling', 'started_unix')), 'RESERVATION_REBOUND')
        witness = settlement_path(pub, aid)
        receipt = pub.response_anchor(aid)
        if not dispatch.exists():
            require(not receipt.exists() and not witness.exists(), 'RESPONSE_WITHOUT_DISPATCH')
            require(row['state'] == 'RESERVED', 'SETTLED_WITHOUT_DISPATCH')
            prior.append(row)
            continue
        anchor = observed(dispatch)
        spec = loads(anchor['spec'])
        require(anchor['run_id'] == row['run_id'] == pub.request.run_id and
                anchor['attempt_id'] == aid and anchor['identity_sha256'] == pub.identity_sha,
                'DISPATCH_OWNERSHIP')
        stage = spec['purpose']
        require(stage not in stages, 'DUPLICATE_STAGE')
        stages.append(stage)
        for handle in spec['prior_output_ids']:
            require(handle in handles, 'HANDLE_ABSENT_FOREIGN_REBOUND_OR_NOT_YET_SETTLED')
            require(handles[handle]['attempt_id'] < aid, 'HANDLE_CREATION_ORDER')
        # Pure recompilation from the original public compiler. No reservation,
        # dispatch, algorithm, selection, prompt or provider behavior is changed.
        sealed_spec, reference, provenance = compiler._compile(spec, {'attempts': prior})
        require(sha(reference) == anchor['reference_wire_sha256'] and
                sha(provenance) == anchor['provenance_sha256'] and
                loads(sealed_spec) == spec, 'SEALED_CONTROL_REQUEST_PROVENANCE')
        req, structured, seed = compiler.bindings[sha(reference)]
        require(asdict(req) == anchor['model_request'] and structured == anchor['structured']
                and seed == anchor['seed'], 'MODEL_REQUEST_REFERENCES_OR_SETTINGS')
        if row['state'] != 'RESERVED':
            if witness.exists():
                claim = observed(witness)
                require(set(claim) == {'schema_version', 'identity_sha256', 'run_id',
                                      'attempt_id', 'settlement', 'dispatch_anchor_sha256',
                                      'response_anchor_sha256'}, 'SETTLEMENT_WITNESS_SCHEMA')
                require(claim['schema_version'] == 'abc-r3-settlement-v1' and
                        claim['identity_sha256'] == pub.identity_sha and
                        claim['run_id'] == pub.request.run_id and claim['attempt_id'] == aid,
                        'SETTLEMENT_WITNESS_IDENTITY')
                if canonical(claim['settlement']) != canonical(row):
                    require(all(claim['settlement'].get(k) == row.get(k) for k in
                                ('attempt_id', 'run_id', 'purpose', 'state', 'candidate')),
                            'INDEPENDENT_SETTLEMENT_CONTRADICTS_LEDGER')
                    raise ProvenanceFault('INDEPENDENT_CONTENT_OR_ACCOUNTING_MISMATCH')
                require(claim['dispatch_anchor_sha256'] == files[dispatch.relative_to(pub.directory).as_posix()],
                        'SETTLEMENT_DISPATCH_BINDING')
                if receipt.exists():
                    observed(receipt)
                    require(claim['response_anchor_sha256'] == files[receipt.relative_to(pub.directory).as_posix()],
                            'SETTLEMENT_RESPONSE_BINDING')
                else:
                    require(claim['response_anchor_sha256'] is None, 'SETTLEMENT_RESPONSE_DISAPPEARED')
            else:
                # Old histories and the crash window after gateway settlement
                # cannot be retroactively assigned opaque handle identities.
                uncovered.append(aid)
        else:
            require(not witness.exists(), 'SETTLED_RESERVATION_REUSED')
        candidate = row.get('candidate')
        if row['state'] == 'SUCCEEDED':
            require(type(candidate) is dict and type(row.get('response_text')) is str,
                    'SUCCESS_WITHOUT_CANDIDATE')
            require(set(candidate) == {'output_id', 'call_id', 'task_id', 'wire_sha256', 'provenance_sha256'},
                    'CANDIDATE_HANDLE_SCHEMA')
            oid = candidate['output_id']
            require(type(oid) is str and re.fullmatch(r'O_[0-9a-f]{24}', oid) is not None,
                    'HANDLE_IDENTITY_FORMAT')
            require(oid not in handles, 'DUPLICATE_HANDLE')
            require(candidate['task_id'] == pub.request.task_id and
                    candidate['call_id'] == anchor['call_id'] == spec['call_id'] and
                    candidate['wire_sha256'] == sha(reference) and
                    candidate['provenance_sha256'] == sha(provenance) and
                    sha(row['response_text'].encode()) == row['response_sha256'],
                    'CANDIDATE_CONTENT_OR_ORIGIN')
            handles[oid] = row
        else:
            require(candidate is None, 'NONSUCCESS_WITH_CANDIDATE')
        prior.append(row)
    # Detect a changed version during validation without binding unrelated
    # future runs in a shared ledger to this run's immutable result.
    require(canonical(own) == canonical([a for a in pub.ledger.state()['attempts']
                                       if a['run_id'] == pub.request.run_id]), 'LEDGER_CHANGED_DURING_VERIFICATION')
    for name, digest in files.items():
        require(sha((pub.directory / name).read_bytes()) == digest,
                'ANCHOR_CHANGED_DURING_VERIFICATION')
    return {'schema_version': 'abc-r3-provenance-v1', 'revision': '1.0.2',
            'run_attempts_sha256': sha(canonical(own)), 'anchor_hashes': files,
            'ordered_attempt_ids': [a['attempt_id'] for a in own],
            'bound_output_handles': sorted(handles), 'unwitnessed_settlements': uncovered,
            'overall': 'INTERRUPTED' if uncovered else 'VERIFIED'}


class RecoveryIntegrityHold(ArtifactIntegrity):
    """Recognized F02 rejection, with its grounded verifier/run context."""
    def __init__(self, report, publication):
        from copy import deepcopy
        self.report = deepcopy(report)
        self.report['requires_integrity_hold'] = True
        self.publication = publication
        super().__init__('F02_PROVENANCE_GRAPH_INCONSISTENT_EVIDENCE_PRESERVED')


def require_recoverable(report, pub=None):
    from .certification import disposition, EvidenceDisposition
    if disposition(report) is EvidenceDisposition.BLOCKED:
        if pub is not None:
            pub.release()
        raise RecoveryIntegrityHold(report, pub)


def require_dispatchable(pub):
    from .journals import verify_journals
    report = verify_journals(pub)
    if report['overall'] != 'VERIFIED':
        pub.release()
        raise ArtifactIntegrity('F02_UNVERIFIED_HISTORY_NO_NEW_DISPATCH')


def publish_verified(pub, data):
    """F02 eligibility before normal publication and after revalidation.

    The existing run lock/lease spans construction through this verification.
    Late changed evidence leaves any exclusive final bytes preserved as suspect
    evidence, but no verified return and no overwrite/replay is permitted.
    """
    from .certification import require_certification_eligible
    # Refuse before invoking normal publication. The same independent check
    # runs inside Publication.verify_semantics at each protected revalidation.
    require_certification_eligible(pub, data)
    try:
        pub.publish(data)
        return pub.verify_completed()
    except ArtifactIntegrity as error:
        # F01 wraps semantic failures. Translate only a grounded F02 hold,
        # never generic F01 ownership/filesystem/programming failures.
        cause = error.__cause__
        if isinstance(cause, RecoveryIntegrityHold):
            raise cause
        raise
