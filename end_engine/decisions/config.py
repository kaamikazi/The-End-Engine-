from dataclasses import dataclass
import math
import re


@dataclass(frozen=True)
class DecisionConfig:
    """Off by default. No key or endpoint override belongs in recorded configuration."""
    provider: str = "baseline"
    requested_model: str | None = None
    categories: tuple[str, ...] = ("operator_routing",)
    timeout_seconds: float = 5.0
    max_calls_per_run: int = 4
    max_latency_ms: float = 15000.0
    min_choice_probability: float = 0.65
    min_choice_confidence: float = 0.70
    max_utility_loss: float = 0.25
    max_repetition_penalty: float = 0.50

    def __post_init__(self):
        if self.provider not in ("baseline", "jev", "scripted", "replay"):
            raise ValueError("Unknown decision provider")
        if self.requested_model is not None and (not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", self.requested_model)
                or self.requested_model.startswith(("sk-", "ghp_", "github_pat_", "AIza"))):
            raise ValueError("requested_model must be a model identifier, never a credential")
        if not isinstance(self.categories, tuple) or set(self.categories) - {"operator_routing"}:
            raise ValueError("Only experimental operator_routing is supported")
        for name in ("timeout_seconds", "max_latency_ms", "max_utility_loss", "max_repetition_penalty"):
            v = getattr(self, name)
            if type(v) not in (int, float) or not math.isfinite(v) or v <= 0:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("min_choice_probability", "min_choice_confidence"):
            v = getattr(self, name)
            if type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1:
                raise ValueError(f"{name} must lie in [0, 1]")
        if type(self.max_calls_per_run) is not int or self.max_calls_per_run < 0:
            raise ValueError("max_calls_per_run must be a nonnegative integer")
