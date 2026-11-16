from dataclasses import dataclass, field
import math
from .decisions.config import DecisionConfig


@dataclass(frozen=True)
class EngineConfig:
    ledger_dir: str = "trajectories"
    verbose: bool = False
    llm_classification: bool = False
    llm_selection: bool = False
    quality_threshold: float = 0.90
    critical_quality_threshold: float = 0.95
    improvement_epsilon: float = 0.01
    stagnation_patience: int = 2
    repeated_critique_patience: int = 2
    max_active_branches: int = 3
    max_branch_depth: int = 2
    max_branches_per_operator: int = 3
    max_cognitive_operations: int | None = None
    enable_branching: bool = True
    meta_check_interval: int = 3
    max_reframings: int = 1
    cognitive_stagnation_patience: int = 3
    quality_evaluation: bool = False
    judge_min_confidence: float = 0.75
    post_acceptance_cycles: int = 0
    # v0.3.5. Targeted repair calls per failing structured stage (0 disables repair).
    protocol_repair_attempts: int = 1
    repair_failure_limit: int = 2
    no_progress_patience: int = 2
    # v0.3.5. "structured" (default; candidate inside the Engine JSON protocol, as before) or "native" (the
    # user-facing answer is generated as free text with the task as the prompt; Engine metadata stays separate).
    candidate_generation: str = "structured"
    decision: DecisionConfig = field(default_factory=DecisionConfig)
    # Shared provider/tool call ceiling. None preserves legacy behavior; decision-enabled
    # runs receive a finite default ceiling of 128 unless explicitly configured.
    max_run_calls: int | None = None

    def __post_init__(self):
        for name in ("quality_threshold", "critical_quality_threshold", "improvement_epsilon", "judge_min_confidence"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be a finite number in [0, 1]")
        if self.critical_quality_threshold < self.quality_threshold:
            raise ValueError("Critical quality threshold cannot be lower than the regular threshold")
        for name in ("stagnation_patience", "repeated_critique_patience"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("max_active_branches", "max_branch_depth", "max_branches_per_operator", "max_reframings", "post_acceptance_cycles"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        for name in ("meta_check_interval", "cognitive_stagnation_patience"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")
        if type(self.protocol_repair_attempts) is not int or not 0 <= self.protocol_repair_attempts <= 3:
            raise ValueError("protocol_repair_attempts must be an integer in [0, 3]")
        for name in ('repair_failure_limit', 'no_progress_patience'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 2:
                raise ValueError(f'{name} must be an integer >= 2')
        if self.candidate_generation not in ("structured", "native"):
            raise ValueError("candidate_generation must be 'structured' or 'native'")
        if self.max_cognitive_operations is not None and (type(self.max_cognitive_operations) is not int or self.max_cognitive_operations < 0):
            raise ValueError("max_cognitive_operations must be nonnegative or None")
        if not isinstance(self.decision, DecisionConfig):
            raise ValueError("decision must be DecisionConfig")
        if self.max_run_calls is not None and (type(self.max_run_calls) is not int or self.max_run_calls < 0):
            raise ValueError("max_run_calls must be nonnegative or None")
