"""Immutable, explicit evaluation artifacts. Scores and confidence stay separate."""
from dataclasses import dataclass
from enum import Enum

from ..core.state import to_data


class Verdict(str, Enum):
    PASS = "PASS"
    NEEDS_REVISION = "NEEDS_REVISION"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class GateDecision(str, Enum):
    REJECT = "REJECT"
    REVISE = "REVISE"
    ACCEPT_PROVISIONALLY = "ACCEPT_PROVISIONALLY"
    ACCEPT_VERIFIED = "ACCEPT_VERIFIED"
    BLOCKED = "BLOCKED"


class Provenance(str, Enum):
    """Minimal source semantics (v0.3.5). Where information came from, never how confident anyone is.
    MODEL_CONSENSUS != EXECUTED_CHECK; TASK_PROVIDED != REGISTERED_EVIDENCE; MODEL_JUDGMENT != verified fact."""
    TASK_PROVIDED = "TASK_PROVIDED"            # user instructions and claims; may contain false premises
    CANDIDATE = "CANDIDATE"                    # what the candidate actually says, proposes or computes
    ENGINE_DERIVED = "ENGINE_DERIVED"          # deterministic Engine checks (format, leakage, grounding)
    EXECUTED_CHECK = "EXECUTED_CHECK"          # EXECUTED_EVIDENCE from the trusted tool verifier
    REGISTERED_EVIDENCE = "REGISTERED_EVIDENCE"
    MODEL_JUDGMENT = "MODEL_JUDGMENT"          # a judge's interpretation
    MODEL_CONSENSUS = "MODEL_CONSENSUS"        # several model statements agreeing
    REPORTED_CONSENSUS = "REPORTED_CONSENSUS"  # people or sources reported as agreeing
    UNKNOWN = "UNKNOWN"
    TASK_INSTRUCTION = "TASK_INSTRUCTION"
    TASK_ASSERTION = "TASK_ASSERTION"
    MODEL_CRITIQUE = "MODEL_CRITIQUE"
    MODEL_REVISION_PLAN = "MODEL_REVISION_PLAN"


EVIDENCE_PROVENANCE = {"EXECUTED_EVIDENCE": Provenance.EXECUTED_CHECK, "MODEL_JUDGMENT": Provenance.MODEL_JUDGMENT}


@dataclass(frozen=True)
class DimensionJudgment:
    score: float
    confidence: float


@dataclass(frozen=True)
class JudgeIssue:
    category: str
    description: str
    target: str = "candidate"
    fatal: bool = False
    evidence: tuple[str, ...] = ()
    # v0.3.5, optional and additive. claim_type: CANDIDATE_INTERNAL | TASK_CONSTRAINT | EXTERNAL_FACT ("" = undeclared).
    claim_type: str = ""
    candidate_quote: str = ""      # verbatim candidate text the finding is about
    task_reference: str = ""       # task text the finding relies on
    grounding: str = ""            # set by the Engine, never by the judge (see quality/grounding.py)
    decisive: bool = True          # False: the finding cannot drive REJECT/REVISE, rollback or a weakness
    # v0.3.5.1: optional bounded semantic argument. Writer provenance remains MODEL_JUDGMENT.
    source_claim: str = ""
    alleged_defect: str = ""
    basis: str = ""
    textual_grounding: str = ""    # Engine annotations, distinct from semantic support
    semantic_grounding: str = ""


@dataclass(frozen=True)
class Judgment:
    judgment_id: str
    candidate_id: str
    judge_id: str
    verdict: Verdict
    dimensions: tuple[tuple[str, DimensionJudgment], ...]
    fatal_issues: tuple[JudgeIssue, ...] = ()
    major_issues: tuple[JudgeIssue, ...] = ()
    minor_issues: tuple[JudgeIssue, ...] = ()
    uncertainties: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    recommended_action: str = "REVIEW"
    adversarial: bool = False
    # Cited IDs absent from the evidence supplied to the judge. Kept as cited; never dropped, repaired or substituted.
    unresolved_evidence: tuple[str, ...] = ()
    assessment_decisive: bool = True
    assessment_requires_evidence: bool = False

    def as_dict(self):
        data = to_data(self)
        data["dimensions"] = {name: to_data(value) for name, value in self.dimensions}
        return data


@dataclass(frozen=True)
class ClaimValidationResult:
    claim_id: str
    status: str
    importance: str
    supporting_artifacts: tuple[str, ...]
    contradicting_artifacts: tuple[str, ...]
    judge_confidence: float
    out_of_scope_artifacts: tuple[str, ...] = ()  # passed checks that target the claim but do not cover it


@dataclass(frozen=True)
class ResolutionAudit:
    target_id: str
    status: str
    reason: str
    transition_step: int
    supporting_artifacts: tuple[str, ...] = ()
    kind: str = "weakness"
    transition: str = ""  # audited target status, e.g. accepted_risk
    corroborating_judgments: tuple[str, ...] = ()  # model judgments only; never executed evidence
    criteria_gaps: tuple[str, ...] = ()  # unmet risk-acceptance criteria


@dataclass(frozen=True)
class AdversarialTest:
    test_id: str
    candidate_id: str
    target: str
    scenario: str
    expected_property: str
    execution_status: str = "UNEXECUTED"


@dataclass(frozen=True)
class CheckContract:
    """What a trusted checker declares it actually checked. A PASS supports nothing broader.

    phase: "development" (a declared subset, e.g. development checks) or "final" (the task's own acceptance check).
    claims: exact statements the check establishes; empty means the verifier's targets are the whole declaration.
    artifact_sha256: SHA-256 of the exact candidate content (UTF-8) that was checked, when the checker binds it."""
    check_id: str
    phase: str = "development"
    properties: tuple[str, ...] = ()
    claims: tuple[str, ...] = ()
    artifact_sha256: str | None = None
    version: str | None = None
    bounds: str = ""


@dataclass(frozen=True)
class EvidenceArtifact:
    artifact_id: str
    candidate_id: str
    evidence_type: str
    source: str
    passed: bool
    description: str
    targets: tuple[str, ...] = ()
    test_id: str | None = None
    contract: CheckContract | None = None  # None: legacy evidence; phase undeclared (never final-task proof)


@dataclass(frozen=True)
class RevisionComparison:
    from_candidate: str
    to_candidate: str
    preferred: str | None
    dimensions: tuple[tuple[str, str], ...]
    delta: tuple[tuple[str, float], ...]
    net_assessment: str
    reason: str
    severe_dimensions: tuple[str, ...] = ()
    assessment_decisive: bool = True


@dataclass(frozen=True)
class JudgeDispute:
    candidate_id: str
    status: str
    judges: tuple[str, ...]
    disputed_dimensions: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class GateResult:
    candidate_id: str
    decision: GateDecision
    reasons: tuple[str, ...]
    required_actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrajectoryAssessment:
    substantive_progress: str
    redundancy: str
    resolution_integrity: str
    verification_independence: str
    evidence_quality: str
    trajectory_issues: tuple[str, ...] = ()
