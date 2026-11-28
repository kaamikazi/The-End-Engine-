"""Optional TypeSafe SDK adapter. No TypeSafe type escapes this module.

Contract reviewed against official SDK 0.7.2: TypeSafeClient.system_one;
Choice/Noul/Score; response.model/usage/request_id and typed answer maps.
"""
import importlib
import os
from time import perf_counter

from .context import redact
from .providers import DecisionProvider
from .types import (BinaryDecision, ChoiceDecision, ScoreDecision, DecisionProvenance,
                    DecisionResult, DecisionStatus, validate_result)


class JevDecisionProvider(DecisionProvider):
    def __init__(self, *, requested_model=None, sdk_loader=None):
        self.requested_model = requested_model
        self._loader = sdk_loader or (lambda: importlib.import_module("typesafe_sdk"))
        self._sdk = None

    def for_run(self):
        return JevDecisionProvider(requested_model=self.requested_model, sdk_loader=self._loader)

    def availability(self):
        if not self.requested_model:
            return "unavailable", "requested_model_required"
        if not os.environ.get("TYPESAFE_API_KEY", "").strip():
            return "unavailable", "missing_api_key"
        if self._sdk is None:
            try:
                self._sdk = self._loader()
            except ModuleNotFoundError as exc:
                if exc.name != "typesafe_sdk":
                    raise  # A broken unrelated import must not be misreported as an absent optional SDK.
                return "unavailable", "missing_sdk"
        return "available", None

    def evaluate(self, request):
        start = perf_counter()
        available, reason = self.availability()
        if available != "available":
            return DecisionResult(request.question_id, request.question_type, DecisionStatus.UNAVAILABLE,
                DecisionProvenance("typesafe", request.requested_model, availability=available), failure_reason=reason)
        sdk = self._sdk
        if request.requested_model != self.requested_model:
            return DecisionResult(request.question_id, request.question_type, DecisionStatus.UNAVAILABLE,
                DecisionProvenance("typesafe", request.requested_model), failure_reason="requested_model_mismatch")
        try:
            if request.question_type == "choice":
                question = sdk.Choice(instructions=request.question, criteria={choice: None for choice in request.choices})
            elif request.question_type == "binary":
                question = sdk.Noul(instructions=request.question)
            else:
                question = sdk.Score(instructions=request.question, criteria=list(request.score_levels))
            # No SDK retry, model listing, warmup or automatic pin resolution request.
            with sdk.TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"], model=request.requested_model,
                    timeout=request.timeout_seconds, retry=sdk.RetryPolicy(max_retries=0),
                    base_url="https://api.typesafe.ai") as client:
                response = client.system_one(state=request.context, questions={request.question_id: question},
                                             model=request.requested_model)
            usage = tuple((name, getattr(response.usage, name, None)) for name in ("input_tokens", "output_tokens"))
            for _, v in usage:
                if v is not None and (type(v) is not int or v < 0): raise ValueError("Invalid usage")
            resolved = response.model
            if not isinstance(resolved, str) or not resolved.strip(): raise ValueError("Missing resolved model")
            request_id = getattr(response, "request_id", None)
            provenance = DecisionProvenance("typesafe", request.requested_model, redact(resolved)[:80],
                redact(request_id)[:128] if request_id else None, round((perf_counter()-start)*1000, 3), usage)
            if request.question_type == "choice":
                answer = response.choices[request.question_id]
                value = ChoiceDecision(redact(answer.choice), tuple((redact(label),p) for label,p in answer.probabilities.items()), answer.confidence)
            elif request.question_type == "binary":
                answer = response.nouls[request.question_id]
                value = BinaryDecision(answer.noul, answer.noul >= .5)
            else:
                answer = response.scores[request.question_id]
                value = ScoreDecision(answer.score, tuple(answer.probabilities.items()), tuple((level,redact(text)) for level,text in answer.legend.items()), answer.confidence)
            result = DecisionResult(request.question_id, request.question_type, DecisionStatus.SUCCESS, provenance, value)
            validate_result(result, request)
            return result
        except Exception as exc:
            def is_sdk(name):
                cls = getattr(sdk, name, None)
                return isinstance(cls, type) and isinstance(exc, cls)
            status = getattr(exc, "status", None)
            if isinstance(exc, TimeoutError) or is_sdk("TypeSafeAPITimeoutError"):
                state = DecisionStatus.TIMEOUT
            elif is_sdk("TypeSafeAPIResponseValidationError") or isinstance(exc, (ValueError, TypeError, KeyError, AttributeError)):
                state = DecisionStatus.MALFORMED
            elif status == 429 or is_sdk("TypeSafeRateLimitError"):
                state = DecisionStatus.RATE_LIMITED
            elif status in (401,403) or is_sdk("TypeSafeAuthenticationError"):
                state = DecisionStatus.AUTHENTICATION_FAILURE
            elif status == 404 or is_sdk("TypeSafeNotFoundError"):
                state = DecisionStatus.UNKNOWN_MODEL
            elif isinstance(exc, ConnectionError) or is_sdk("TypeSafeAPIConnectionError"):
                state = DecisionStatus.CONNECTION_FAILURE
            elif type(status) is int or is_sdk("TypeSafeAPIError"):
                state = DecisionStatus.HTTP_FAILURE
            else:
                state = DecisionStatus.PROVIDER_ERROR
            # Never persist SDK bodies, headers, raw responses, credentials or exception messages.
            return DecisionResult(request.question_id, request.question_type, state,
                DecisionProvenance("typesafe", request.requested_model, latency_ms=round((perf_counter()-start)*1000, 3),
                                   error_type=type(exc).__name__), failure_reason=state.value)
