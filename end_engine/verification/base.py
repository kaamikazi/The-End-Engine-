from typing import Protocol

from ..core.state import Candidate, VerificationResult


class Verifier(Protocol):
    def verify(self, task: str, candidate: Candidate, trajectory: dict) -> VerificationResult: ...
