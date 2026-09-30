"""Immutable public state and JSON conversion helpers."""
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_data(value: Any) -> Any:
    if is_dataclass(value):
        return {f.name: to_data(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: to_data(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_data(v) for v in value]
    return value


class Complexity(str, Enum):
    FAST = "fast"
    NORMAL = "normal"
    DEEP = "deep"
    CRITICAL = "critical"


class WeaknessStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    ACCEPTED_RISK = "accepted_risk"
    INVALIDATED = "invalidated"


class StopReason(str, Enum):
    QUALITY_THRESHOLD_REACHED = "QUALITY_THRESHOLD_REACHED"
    NO_MATERIAL_IMPROVEMENT = "NO_MATERIAL_IMPROVEMENT"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    VERIFIER_PASSED = "VERIFIER_PASSED"
    REPEATED_CRITIQUE = "REPEATED_CRITIQUE"
    FAST_PATH = "FAST_PATH"
    EXTERNAL_BLOCKER = "EXTERNAL_BLOCKER"
    ACCEPTED_VERIFIED = "ACCEPTED_VERIFIED"
    ACCEPTED_PROVISIONALLY = "ACCEPTED_PROVISIONALLY"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class ReasoningBudget:
    min_cycles: int
    target_cycles: int
    max_cycles: int

    def __post_init__(self):
        values = (self.min_cycles, self.target_cycles, self.max_cycles)
        if any(type(v) is not int for v in values) or not 0 <= values[0] <= values[1] <= values[2]:
            raise ValueError("Expected 0 <= min_cycles <= target_cycles <= max_cycles")


@dataclass(frozen=True)
class TaskAnalysis:
    complexity: Complexity
    confidence: float
    reasoning_budget: ReasoningBudget
    dimensions: tuple[str, ...]
    rationale: str
    source: str = "heuristic"


@dataclass(frozen=True)
class Weakness:
    id: str
    type: str
    severity: str
    description: str
    evidence: str
    status: WeaknessStatus = WeaknessStatus.OPEN
    first_seen_iteration: int = 0
    last_seen_iteration: int = 0
    occurrences: int = 1
    status_reason: str = ""
    target_id: str | None = None


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    parent_candidate_id: str | None
    iteration: int
    content: str
    created_at: str
    known_strengths: tuple[str, ...] = ()
    known_weaknesses: tuple[Weakness, ...] = ()
    confidence: float | None = None


@dataclass(frozen=True)
class Selection:
    operator: str
    reason: str
    priority: float


@dataclass(frozen=True)
class Critique:
    candidate_id: str
    operator: str
    summary: str
    findings: tuple[Weakness, ...]


@dataclass(frozen=True)
class Change:
    targets: tuple[str, ...]
    action: str
    expected_effect: str


@dataclass(frozen=True)
class RevisionPlan:
    candidate_id: str
    changes: tuple[Change, ...]


@dataclass(frozen=True)
class WeaknessUpdate:
    id: str
    status: WeaknessStatus
    reason: str


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    score: float
    dimensions: tuple[tuple[str, float], ...]
    remaining_issues: tuple[str, ...]
    weakness_updates: tuple[WeaknessUpdate, ...] = ()
    verifier: str = "unknown"

    def as_dict(self) -> dict:
        result = to_data(self)
        result["dimensions"] = dict(self.dimensions)
        return result


@dataclass(frozen=True)
class EngineResult:
    answer: str
    trajectory_id: str
    iterations: int
    verification: VerificationResult | None
    termination_reason: StopReason
    trajectory_path: str
    best_candidate_id: str | None = None
    latest_candidate_id: str | None = None
    quality_gate: str | None = None
    acceptance_label: str | None = None

    def as_dict(self) -> dict:
        result = to_data(self)
        result["verification"] = self.verification.as_dict() if self.verification else None
        return result
