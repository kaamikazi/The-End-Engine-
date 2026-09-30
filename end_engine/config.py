from dataclasses import dataclass
import math


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
        if self.max_cognitive_operations is not None and (type(self.max_cognitive_operations) is not int or self.max_cognitive_operations < 0):
            raise ValueError("max_cognitive_operations must be nonnegative or None")
