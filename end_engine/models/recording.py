from copy import deepcopy
from time import perf_counter
import json

from .base import ModelProvider, ModelRequest, ModelResponse
from .protocol import REPAIR_EXHAUSTED, REPAIR_INSTRUCTION, SCHEMA_FAILURE, ModelProtocolError, repair_context
from .schema import validate
from .repair import repair_policy
from ..core.state import now, to_data
from ..experience.serializer import dumps


class RecordingProvider(ModelProvider):
    """Record requests, raw responses, usage and failures, including invalid output.

    Unparseable or schema-invalid structured output is a model-protocol failure (ModelProtocolError), not an external
    failure. With repair_attempts > 0 such a call gets that many targeted repair calls, each recorded; exceptions
    raised by the provider itself (transport, availability, budgets) are never retried here and stay external."""

    def __init__(self, provider, trajectory, repair_attempts=0):
        self.provider = provider
        self.trajectory = trajectory
        self.repair_attempts = repair_attempts

    def metadata(self):
        return self.provider.metadata()

    def generate(self, request):
        return self._call(request, structured=False)

    def generate_structured(self, request):
        return self._call(request, structured=True)

    def _call(self, request, *, structured):
        try:
            return self._once(request, structured=structured)
        except ModelProtocolError as error:
            if not structured or self.repair_attempts < 1 or request.context.get('protocol_repair'):
                raise
            policy = repair_policy(self.trajectory)
            if not policy.begin(request.purpose):
                raise
            failure, previous = error, error.output
            for attempt in range(1, 2):
                self.trajectory.record("protocol_event", {"stage": request.purpose, "category": failure.category,
                    "validation_error": str(failure), "action": "repair_requested", "attempt": attempt},
                    "protocol_events")
                repaired = ModelRequest(request.purpose, request.prompt + "\n\n" + REPAIR_INSTRUCTION,
                                        {**request.context, "protocol_repair": repair_context(failure, previous, attempt)},
                                        request.schema)
                try:
                    response = self._once(repaired, structured=True)
                except ModelProtocolError as again:
                    failure, previous = again, again.output
                    continue
                except Exception:
                    policy.finish(request.purpose, False)
                    raise
                # Reference-sensitive stages acknowledge only after semantic/reference validation and use.
                if request.purpose not in ('critique', 'revision_plan', 'verification', 'synthesis'):
                    policy.finish(request.purpose, True)
                    self.trajectory.record("protocol_event", {"stage": request.purpose, "category": error.category,
                        "action": "repaired", "attempt": attempt, "result": "valid"}, "protocol_events")
                return response
            policy.finish(request.purpose, False)
            self.trajectory.record("protocol_event", {"stage": request.purpose, "category": REPAIR_EXHAUSTED,
                "original_category": error.category, "validation_error": str(failure), "action": "repair_exhausted",
                "attempts": self.repair_attempts}, "protocol_events")
            raise ModelProtocolError(REPAIR_EXHAUSTED, f"{request.purpose}: {failure}", stage=request.purpose,
                                     output=previous) from failure

    def _once(self, request, *, structured):
        call = {"call_id": self.trajectory.next_call_id(), "started_at": now(),
                "model": None,
                "method": "generate_structured" if structured else "generate",
                "request": deepcopy(to_data(request)), "response": None, "error": None}
        start = perf_counter()
        try:
            self.trajectory.reserve_call("model")
            metadata = self.provider.metadata()
            dumps(metadata)
            call["model"] = deepcopy(metadata)
            # Provider mutation cannot affect either the saved request or engine state.
            response = (self.provider.generate_structured if structured else self.provider.generate)(deepcopy(request))
            if not isinstance(response, ModelResponse):
                call["response"] = {"raw_repr": repr(response)}
                raise ValueError("Provider must return ModelResponse")
            raw = to_data(response)
            try:
                dumps(raw)
                call["response"] = deepcopy(raw)
            except (TypeError, ValueError):
                call["response"] = {"raw_repr": repr(raw)}
                raise ValueError("Provider response is not finite JSON-compatible data")
            content = response.content
            if structured:
                if request.schema is None:
                    raise ValueError("Structured requests require a schema")
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except ValueError as exc:
                        raise ModelProtocolError(SCHEMA_FAILURE, f"unparseable JSON: {exc}", stage=request.purpose,
                                                 output=response.content) from exc
                try:
                    validate(content, request.schema)
                except ValueError as exc:
                    raise ModelProtocolError(SCHEMA_FAILURE, str(exc), stage=request.purpose, output=content) from exc
            elif not isinstance(content, str):
                raise ValueError("Text generation must return a string")
            for item in response.tool_calls:
                self.trajectory.record("tool_call", {"call_id": call["call_id"], "data": item}, "tool_calls")
            return ModelResponse(deepcopy(content), deepcopy(response.usage), deepcopy(response.tool_calls),
                                 deepcopy(response.answer_content))
        except Exception as exc:
            call["error"] = {"type": type(exc).__name__, "message": str(exc)}
            raise
        finally:
            call["latency_ms"] = round((perf_counter() - start) * 1000, 3)
            call["completed_at"] = now()
            self.trajectory.record("model_call", call, "model_calls")
