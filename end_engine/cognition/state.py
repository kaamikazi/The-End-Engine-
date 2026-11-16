from dataclasses import dataclass
from enum import Enum

from ..core.state import Selection, Weakness


class EvidenceStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AssumptionStatus(str, Enum):
    UNTESTED = "UNTESTED"
    SUPPORTED = "SUPPORTED"
    WEAKENED = "WEAKENED"
    INVALIDATED = "INVALIDATED"
    ACCEPTED_RISK = "ACCEPTED_RISK"


class TargetType(str, Enum):
    WHOLE_CANDIDATE = "WHOLE_CANDIDATE"
    CLAIM = "CLAIM"
    ASSUMPTION = "ASSUMPTION"
    WEAKNESS = "WEAKNESS"
    COMPONENT = "COMPONENT"
    CONSTRAINT = "CONSTRAINT"
    BRANCH = "BRANCH"
    EVIDENCE_GAP = "EVIDENCE_GAP"


class CoverageLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    type: str
    source_candidate: str
    confidence: float | None = None
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED
    evidence: str = ""
    source_origin: str = 'CANDIDATE'


@dataclass(frozen=True)
class Assumption:
    assumption_id: str
    statement: str
    introduced_at: str
    risk: str = "HIGH"
    status: AssumptionStatus = AssumptionStatus.UNTESTED
    evidence: str = ""
    source_origin: str = 'UNKNOWN'
    decisive: bool = True


@dataclass(frozen=True)
class QuestionTarget:
    target_type: TargetType
    target_id: str
    text: str
    dimension: str


@dataclass(frozen=True)
class QuestionInstance:
    question_id: str
    operator: str
    target: QuestionTarget
    question: str
    expected_information: str
    parent_step: int
    intent: str


@dataclass(frozen=True)
class InformationGain:
    level: str
    new_findings: int = 0
    duplicates: int = 0
    knowledge_changes: int = 0
    viable_alternatives: int = 0
    changed_candidate_direction: bool = False


@dataclass(frozen=True)
class OperatorOutcome:
    operator: str
    family: str
    target_id: str
    intent: str
    question_id: str
    findings: tuple[str, ...]
    information_gain: InformationGain


@dataclass(frozen=True)
class OutcomeStats:
    uses: int = 0
    high_gain: int = 0
    medium_gain: int = 0
    low_gain: int = 0
    zero_gain: int = 0


@dataclass(frozen=True)
class CognitiveState:
    current_candidate_id: str
    iteration: int
    complexity: str
    resolved_dimensions: tuple[str, ...] = ()
    uncertain_dimensions: tuple[str, ...] = ()
    open_weaknesses: tuple[Weakness, ...] = ()
    high_severity_weaknesses: tuple[str, ...] = ()
    claims_without_evidence: tuple[Claim, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    alternatives_considered: tuple[str, ...] = ()
    operators_used: tuple[tuple[str, int], ...] = ()
    operator_statistics: tuple[tuple[str, OutcomeStats], ...] = ()
    family_statistics: tuple[tuple[str, OutcomeStats], ...] = ()
    recent_outcomes: tuple[OperatorOutcome, ...] = ()
    recent_improvement: float = 0
    stagnation: int = 0
    remaining_budget: tuple[tuple[str, int], ...] = ()
    coverage: tuple[tuple[str, CoverageLevel], ...] = ()
    priority_adjustments: tuple[tuple[str, float], ...] = ()
    active_branches: tuple[str, ...] = ()


@dataclass(frozen=True)
class UtilityFactors:
    relevance: float
    information_gain: float
    issue_value: float
    novelty: float
    task_importance: float
    repetition_penalty: float
    cost_penalty: float
    meta_adjustment: float = 0


@dataclass(frozen=True)
class OperatorUtility:
    operator: str
    utility: float
    scores: UtilityFactors
    target: QuestionTarget
    rationale: str


@dataclass(frozen=True)
class UtilitySelection(Selection):
    utility: float
    scores: UtilityFactors
    targets: tuple[str, ...]
    target: QuestionTarget
    ranking: tuple[OperatorUtility, ...]
