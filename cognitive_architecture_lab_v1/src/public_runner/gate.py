"""Fail closed: this laboratory supplies no real generation transport."""
class IsolationBlocked(RuntimeError):pass
ISOLATION_STATUS='NOT_VERIFIED'
def require_generation_runtime():
    raise IsolationBlocked('ISOLATION_BLOCKED: no verified generation transport or restricted worker in this phase')
