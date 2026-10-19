"""Closed offline backend policy. No provider SDK/client/authentication import."""
from enum import Enum
class FeatureStatus(str,Enum):
    DISABLED_AND_ENFORCED='DISABLED_AND_ENFORCED'
    NOT_SUPPORTED='NOT_SUPPORTED'
    NOT_CONFIGURED='NOT_CONFIGURED'
    UNKNOWN='UNKNOWN'
FEATURES=('tools','shell','python','browser','search','retrieval','attachments','external_history','persistent_threads','workspace_ingestion','provider_memory','secondary_calls','sdk_retries')
class BoundaryError(ValueError):pass
class IntegrationPending(RuntimeError):pass

def require_empty_defaults(defaults):
    if type(defaults) is not dict or defaults:raise BoundaryError('Adapter defaults are forbidden; use reviewed explicit serialization')

def capability_inventory():
    return {'offline_reference':{f:{'status':'DISABLED_AND_ENFORCED' if f not in ('provider_memory',) else 'NOT_SUPPORTED','evidence':'Closed serializer + recording sink; no SDK/network/model. Provider memory cannot exist in canned byte recorder.'} for f in FEATURES},
            'live_backends':{f:{'status':'UNKNOWN','evidence':'No real backend selected/implemented/contacted'} for f in FEATURES},
            'live_eligibility':'INTEGRATION_PENDING','os_filesystem_isolation':'NOT_VERIFIED; not claimed for Model A'}

def require_live_backend():raise IntegrationPending('No eligible live adapter or inference authorization in this phase')
