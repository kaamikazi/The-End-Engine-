from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math

from ..core.state import to_data


class DecisionStatus(str, Enum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    MALFORMED = "malformed"
    TIMEOUT = "timeout"
    HTTP_FAILURE = "http_failure"
    RATE_LIMITED = "rate_limited"
    CONNECTION_FAILURE = "connection_failure"
    UNKNOWN_MODEL = "unknown_model"
    AUTHENTICATION_FAILURE = "authentication_failure"
    EXHAUSTED = "exhausted"
    PROVIDER_ERROR = "provider_error"


@dataclass(frozen=True)
class DecisionRequest:
    question_id: str
    question_type: str
    question: str
    context_json: str
    choices: tuple[str, ...] = ()
    score_levels: tuple[str, ...] = ()
    requested_model: str | None = None
    category: str = "operator_routing"
    timeout_seconds: float = 5

    def __post_init__(self):
        if self.question_type not in ("choice", "binary", "score") or not self.question_id or not self.question.strip():
            raise ValueError("Expected one named, typed, atomic question")
        if len(self.question) > 1000 or len(self.context_json.encode()) > 8192:
            raise ValueError("Decision question/context exceeds its bounded size")
        context = json.loads(self.context_json)
        if not isinstance(context, dict):
            raise ValueError("Decision context must be a projected object")
        if self.question_type == "choice" and (not 1 <= len(self.choices) <= 17 or len(set(self.choices)) != len(self.choices)):
            raise ValueError("Choice questions require 1–17 distinct choices")
        if self.question_type == "score" and not 2 <= len(self.score_levels) <= 8:
            raise ValueError("Score requires 2–8 ordered levels")
        if type(self.timeout_seconds) not in (int, float) or not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("Timeout must be finite and positive")

    @property
    def context(self):
        return json.loads(self.context_json)

    @property
    def fingerprint(self):
        # Transport deadline can shrink on replay; semantic inputs and pinning cannot.
        data = to_data(self)
        data.pop("timeout_seconds")
        return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class DecisionProvenance:
    provider: str
    requested_model: str | None = None
    resolved_model: str | None = None
    request_id: str | None = None
    latency_ms: float | None = None
    usage: tuple[tuple[str, int | None], ...] = ()
    availability: str = "available"
    error_type: str | None = None
    replayed: bool = False
    evidence_type: str = "MODEL_JUDGMENT"


@dataclass(frozen=True)
class ChoiceDecision:
    selected_choice: str
    choice_probabilities: tuple[tuple[str, float], ...]
    choice_confidence: float | None = None


@dataclass(frozen=True)
class BinaryDecision:
    noul_probability: float
    # Explicit decision convention: >= 0.5 means yes. No confidence is synthesized.
    positive: bool


@dataclass(frozen=True)
class ScoreDecision:
    ordered_score: float
    score_probabilities: tuple[tuple[int, float], ...]
    score_legend: tuple[tuple[int, str], ...]
    score_confidence: float | None = None


@dataclass(frozen=True)
class DecisionResult:
    question_id: str
    question_type: str
    status: DecisionStatus
    provenance: DecisionProvenance
    value: ChoiceDecision | BinaryDecision | ScoreDecision | None = None
    failure_reason: str | None = None

    def as_dict(self):
        return to_data(self)


def result_from_data(data):
    provenance = dict(data["provenance"])
    provenance["usage"] = tuple(tuple(pair) for pair in provenance.get("usage", []))
    raw = data.get("value")
    value = None
    if raw is not None:
        raw = dict(raw)
        kind = data["question_type"]
        if kind == "choice":
            raw["choice_probabilities"] = tuple(tuple(pair) for pair in raw["choice_probabilities"])
            value = ChoiceDecision(**raw)
        elif kind == "binary":
            value = BinaryDecision(**raw)
        elif kind == "score":
            for key in ("score_probabilities", "score_legend"):
                raw[key] = tuple(tuple(pair) for pair in raw[key])
            value = ScoreDecision(**raw)
        else:
            raise ValueError("Unknown recorded decision type")
    return DecisionResult(data["question_id"], data["question_type"], DecisionStatus(data["status"]),
                          DecisionProvenance(**provenance), value, data.get("failure_reason"))


def validate_result(result, request):
    if not isinstance(result, DecisionResult) or (result.question_id, result.question_type) != (request.question_id, request.question_type):
        raise ValueError("Decision identity/type mismatch")
    if result.provenance.evidence_type != "MODEL_JUDGMENT":
        raise ValueError("Decision signals cannot carry evidence authority")
    if result.status is not DecisionStatus.SUCCESS:
        if result.value is not None:
            raise ValueError("Failed decision must not contain a positive value")
        return
    def unit(v):
        if type(v) not in (int,float) or not math.isfinite(v) or not 0 <= v <= 1:
            raise ValueError("Invalid provider-native probability/confidence")
    value = result.value
    if request.question_type == "choice":
        if not isinstance(value, ChoiceDecision) or not isinstance(value.selected_choice, str):
            raise ValueError("Expected a choice signal")
        probabilities = dict(value.choice_probabilities)
        if not probabilities or len(probabilities) != len(value.choice_probabilities):
            raise ValueError("Missing or duplicate choice probabilities")
        for p in probabilities.values(): unit(p)
        if abs(sum(probabilities.values())-1) > .02:
            raise ValueError("Choice probabilities do not sum approximately to one")
        if value.choice_confidence is not None: unit(value.choice_confidence)
    elif request.question_type == "binary":
        if not isinstance(value, BinaryDecision): raise ValueError("Expected binary signal")
        unit(value.noul_probability)
        if type(value.positive) is not bool or value.positive != (value.noul_probability >= .5):
            raise ValueError("Invalid binary mapping")
    else:
        if not isinstance(value, ScoreDecision) or type(value.ordered_score) not in (int,float) or not math.isfinite(value.ordered_score):
            raise ValueError("Expected a finite ordered score")
        if not 0 <= value.ordered_score <= len(request.score_levels)-1: raise ValueError("Score outside rubric")
        if (len(dict(value.score_probabilities)) != len(value.score_probabilities) or
                any(type(k) is not int for k,_ in value.score_probabilities) or
                set(dict(value.score_probabilities)) != set(range(len(request.score_levels)))): raise ValueError("Invalid score levels")
        for p in dict(value.score_probabilities).values(): unit(p)
        if abs(sum(p for _,p in value.score_probabilities)-1) > .02: raise ValueError("Score probabilities do not sum to one")
        if (set(dict(value.score_legend)) != set(range(len(request.score_levels))) or
                len(dict(value.score_legend)) != len(value.score_legend) or
                tuple(v for _,v in sorted(value.score_legend)) != request.score_levels): raise ValueError("Wrong score rubric")
        if value.score_confidence is not None: unit(value.score_confidence)
