"""Host-only posthoc plane. Not registered in any model capability surface."""
from dataclasses import dataclass
from ..capability_policy.policy import BoundaryError
from ..sealed_requests.boundary import sha
@dataclass(frozen=True)
class PrivateEvaluation:
    run_id:str
    results:tuple
class EvaluationPlane:
    def __init__(self,gateway):self.gateway=gateway
    def evaluate(self,run_id,closed_artifact,scorer):
        # Scorer is a trusted custodian callable. It is never passed to generation/transport.
        expected=self.gateway._closed_runs().get(run_id)
        if expected is None or expected!=closed_artifact:raise BoundaryError('Evaluation requires exact durable closed-generation artifact')
        out=[]
        for c in expected['outputs']:
            if sha(c['text'].encode('utf-8'))!=c['answer_sha256']:raise BoundaryError('Frozen output hash drift')
            out.append((c['output_id'],scorer(c['text'])))
        return PrivateEvaluation(run_id,tuple(out))
