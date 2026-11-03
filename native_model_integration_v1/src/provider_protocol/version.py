"""Future externally supplied identity lock; never queries a server."""
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
class VersionLock:
    def __init__(self):self.observed=None
    def observe(self,identity):
        required={'provider_version','model','model_digest'}
        if type(identity) is not dict or set(identity)!=required or any(type(v) is not str or not v for v in identity.values()):raise BoundaryError('Complete external identity evidence required')
        if identity['model']!='qwen3:4b':raise BoundaryError('Model substitution')
        if self.observed is not None and self.observed!=identity:raise BoundaryError('PROVIDER_OR_MODEL_DRIFT')
        self.observed=dict(identity);return dict(identity)
    def require_live(self):raise BoundaryError('Live integration/authentication/inference not authorized or verified')
