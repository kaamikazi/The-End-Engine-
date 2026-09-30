from copy import deepcopy
from time import perf_counter
import json

from .base import ModelProvider, ModelResponse
from .schema import validate
from ..core.state import now, to_data
from ..experience.serializer import dumps


class RecordingProvider(ModelProvider):
    """Record requests, raw responses, usage and failures, including invalid output."""

    def __init__(self, provider, trajectory):
        self.provider = provider
        self.trajectory = trajectory

    def metadata(self):
        return self.provider.metadata()

    def generate(self, request):
        return self._call(request, structured=False)

    def generate_structured(self, request):
        return self._call(request, structured=True)

    def _call(self, request, *, structured):
        call = {"call_id": self.trajectory.next_call_id(), "started_at": now(),
                "model": None,
                "method": "generate_structured" if structured else "generate",
                "request": deepcopy(to_data(request)), "response": None, "error": None}
        start = perf_counter()
        try:
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
                    content = json.loads(content)
                validate(content, request.schema)
            elif not isinstance(content, str):
                raise ValueError("Text generation must return a string")
            for item in response.tool_calls:
                self.trajectory.record("tool_call", {"call_id": call["call_id"], "data": item}, "tool_calls")
            return ModelResponse(deepcopy(content), deepcopy(response.usage), deepcopy(response.tool_calls))
        except Exception as exc:
            call["error"] = {"type": type(exc).__name__, "message": str(exc)}
            raise
        finally:
            call["latency_ms"] = round((perf_counter() - start) * 1000, 3)
            call["completed_at"] = now()
            self.trajectory.record("model_call", call, "model_calls")
