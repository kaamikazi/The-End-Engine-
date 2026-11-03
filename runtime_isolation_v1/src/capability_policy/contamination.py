"""Scientific decisions require an accountable external sign-off; never auto-issued."""
from enum import Enum
from .policy import BoundaryError
class ExposureCategory(str,Enum):
    HISTORICAL_EXPOSURE='HISTORICAL_EXPOSURE'
    CURRENT_RUNTIME_LEAKAGE='CURRENT_RUNTIME_LEAKAGE'
    FUTURE_MODEL_PRIOR_CONTAMINATION='FUTURE_MODEL_PRIOR_CONTAMINATION'
class ContaminationDecision(str,Enum):
    ACCEPT_WITH_LIMITATIONS='ACCEPT_WITH_LIMITATIONS'
    BLOCK_FOR_CONTAMINATION='BLOCK_FOR_CONTAMINATION'

def validate_external_decision(record,*,authenticate,expected_exposure_sha256,expected_scope):
    keys={'decision','custodian','reviewer_identity','basis','exposure_ledger_sha256','scope','signed_record_reference'}
    if type(record) is not dict or set(record)!=keys or any(type(record[k]) is not str or not record[k].strip() for k in keys):raise BoundaryError('Incomplete external scientific decision')
    try:d=ContaminationDecision(record['decision'])
    except ValueError:raise BoundaryError('Unknown decision') from None
    if record['exposure_ledger_sha256']!=expected_exposure_sha256 or record['scope']!=expected_scope:raise BoundaryError('Scientific decision does not bind current exposure/scope')
    if authenticate(record) is not True:raise BoundaryError('External identity/sign-off not authenticated')
    return d

def automatic_scientific_signoff():raise BoundaryError('Scientific sign-off must not be issued by implementation')
