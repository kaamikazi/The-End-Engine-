"""Explicit opt-in evidence hook. This module never runs shell/model-generated code."""
from dataclasses import dataclass
from typing import Protocol

from ..quality.state import CheckContract, EvidenceArtifact


@dataclass(frozen=True)
class ToolCheck:
    passed: bool
    description: str
    targets: tuple[str, ...] = ()
    test_id: str | None = None
    contract: CheckContract | None = None  # optional declared scope; see CheckContract


class ToolVerifier(Protocol):
    def collect(self, task, candidate, tests, claims) -> tuple[EvidenceArtifact, ...]: ...


class CallableToolVerifier:
    """Invoke a caller-supplied trusted callback; no arbitrary command execution API."""
    def __init__(self, callback, *, name="trusted_callback"):
        self.callback, self.name = callback, name

    def collect(self, task, candidate, tests, claims):
        checks = tuple(self.callback(task, candidate, tests, claims))
        if any(not isinstance(c, ToolCheck) or type(c.passed) is not bool or not c.description.strip() for c in checks):
            raise ValueError("Tool callbacks must return valid ToolCheck records")
        test_ids = {t.test_id for t in tests}
        if any(c.test_id is not None and c.test_id not in test_ids for c in checks):
            raise ValueError("Tool evidence references an unknown adversarial test")
        if any(c.contract is not None and (not isinstance(c.contract, CheckContract) or not c.contract.check_id.strip()
                                           or c.contract.phase not in ("development", "final")) for c in checks):
            raise ValueError("Tool check contracts need a check ID and a development or final phase")
        return tuple(EvidenceArtifact(f"E-{candidate.candidate_id}-{i+1}", candidate.candidate_id,
                     "EXECUTED_EVIDENCE", self.name, c.passed, c.description, tuple(c.targets), c.test_id, c.contract)
                     for i,c in enumerate(checks))
