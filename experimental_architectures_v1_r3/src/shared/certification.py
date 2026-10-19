"""F02-owned dispositions and independently recomputed certification eligibility."""
from enum import Enum


class EvidenceDisposition(Enum):
    VERIFIED = 'VERIFIED'
    UNCERTAIN = 'UNCERTAIN'
    BLOCKED = 'BLOCKED'


UNCERTAIN_TERMINATIONS = frozenset({
    'INTERRUPTED', 'EXTERNAL_BLOCKER', 'TIME_EXHAUSTED', 'BUDGET_EXHAUSTED',
    'PROTOCOL_FAILURE', 'INVALID_RESPONSE', 'UNRESOLVED',
})


def disposition(report):
    status = report['overall']
    if status == 'VERIFIED':
        return EvidenceDisposition.VERIFIED
    if status == 'BLOCKED':
        return EvidenceDisposition.BLOCKED
    if status in ('INTERRUPTED', 'UNKNOWN'):
        return EvidenceDisposition.UNCERTAIN
    # An unrecognized internal report is not silently treated as success.
    raise ValueError('UNRECOGNIZED_JOURNAL_DISPOSITION:' + str(status))


def require_certification_eligible(pub, data):
    """Do not trust the proposed report or its requires_integrity_hold flag.

    This hook is also invoked by the normal protected semantic verifier, so
    calling the underlying publisher/verifier cannot bypass F02 eligibility.
    """
    from .journals import verify_journals, verify_native_records
    from .provenance import require_recoverable
    from .publication import ArtifactIntegrity
    from .strict_json import canonical
    current = (verify_journals(pub) if pub.mode == 'ARCHITECTURE'
               else verify_native_records(pub, data['provider_records']))
    state = disposition(current)
    if state is EvidenceDisposition.BLOCKED:
        require_recoverable(current, pub)
    if canonical(current) != canonical(data['journal_integrity']):
        raise ArtifactIntegrity('PROPOSED_PROVENANCE_REPORT_NOT_CURRENT')
    if state is EvidenceDisposition.UNCERTAIN:
        if data['result']['termination_reason'] not in UNCERTAIN_TERMINATIONS:
            raise ArtifactIntegrity('UNCERTAIN_PROVENANCE_CANNOT_CERTIFY_SUCCESS')
    return state
