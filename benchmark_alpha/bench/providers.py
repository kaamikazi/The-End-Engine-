"""Model transports for Benchmark Alpha. Every condition uses the same transport class and the same settings.

OllamaModel talks to a local Ollama server over loopback HTTP (stdlib only; no credentials exist or are sent).
Every attempt, including failed and retried ones, is appended to a CallLog so cost accounting is uniform across
conditions. Unknown token counts stay None; nothing is estimated."""
from dataclasses import asdict, dataclass, field
import hashlib
import json
import time
import urllib.request

from end_engine.models.base import ModelProvider, ModelResponse
from end_engine.models.schema import validate

JUDGE_PURPOSES = {"judgment": "judge", "comparison": "judge", "adversarial_judgment": "adversarial_judge",
                  "adversarial_tests": "adversarial_judge", "blinded_external_judgment": "external_judge"}


class ProviderError(RuntimeError):
    def __init__(self, category, detail=""):
        super().__init__(f"{category}: {detail}"[:500])
        self.category = category


@dataclass(frozen=True)
class ModelSettings:
    model: str
    provider: str = "ollama-local"
    endpoint: str = "http://127.0.0.1:11434"
    temperature: float = 0.7
    top_p: float = 0.8
    num_predict: int = 4096          # maximum output tokens per call (qwen3 reasons in-band; 2048 truncated answers)
    num_ctx: int = 8192              # context window requested from the server
    base_seed: int = 20260930        # per-call seed = f(base_seed, trial, call sequence)
    think: bool = False              # qwen3 thinking mode disabled for every condition
    timeout_seconds: float = 900.0     # above worst-case time for num_predict tokens (~14 tok/s at 4096)
    structured_retries: int = 1      # one retry after a parse/schema/length failure, same for every condition
    system: str | None = None        # no system instruction in any condition


@dataclass
class CallLog:
    entries: list = field(default_factory=list)

    def add(self, **entry):
        entry["seq"] = len(self.entries) + 1
        self.entries.append(entry)
        return entry

    def totals(self):
        """Tokens are None when any attempt lacks a reported count; the known partial sum is kept separately."""
        def total(key):
            values = [e.get(key) for e in self.entries]
            known = sum(v for v in values if isinstance(v, int))
            return (None if any(v is None for v in values) else known), known
        prompt, prompt_known = total("input_tokens")
        completion, completion_known = total("output_tokens")
        roles = {}
        for e in self.entries:
            roles[e["role"]] = roles.get(e["role"], 0) + 1
        return {"calls": len(self.entries), "calls_by_role": roles,
                "failed_attempts": sum(e["status"] not in ("ok", "truncated") for e in self.entries),
                "truncated_text_answers": sum(e["status"] == "truncated" for e in self.entries),
                "prompt_tokens": prompt, "completion_tokens": completion,
                "total_tokens": None if prompt is None or completion is None else prompt + completion,
                "known_partial_tokens": prompt_known + completion_known,
                "calls_missing_usage": sum(e.get("input_tokens") is None or e.get("output_tokens") is None
                                           for e in self.entries),
                "model_latency_ms": round(sum(e.get("latency_ms") or 0 for e in self.entries), 3)}


def render(request):
    """The text a model sees for an Engine request: instruction, context and output schema, nothing else."""
    parts = [request.prompt]
    if request.context:
        parts.append("INPUT (JSON):\n" + json.dumps(request.context, ensure_ascii=False, sort_keys=True))
    if request.schema is not None:
        parts.append("Respond with only one JSON object that satisfies this JSON Schema:\n"
                     + json.dumps(request.schema, sort_keys=True))
    return "\n\n".join(parts)


class OllamaModel(ModelProvider):
    def __init__(self, settings: ModelSettings, identity: dict, log: CallLog, *, trial_seed=0, transport=None):
        self.settings, self.identity, self.log, self.trial_seed = settings, identity, log, trial_seed
        self.transport = transport or self._http

    def metadata(self):
        return {"provider": self.settings.provider, "model": self.settings.model,
                "digest": self.identity.get("digest"), "settings": asdict(self.settings),
                "data_origin": "LIVE_LOCAL_MODEL"}

    def generate(self, request):
        return self._call(request, structured=False)

    def generate_structured(self, request):
        return self._call(request, structured=True)

    def _seed(self):
        digest = hashlib.sha256(f"{self.settings.base_seed}:{self.trial_seed}:{len(self.log.entries)}".encode()).hexdigest()
        return int(digest[:8], 16)

    def _http(self, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.settings.endpoint + "/api/generate", data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.settings.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def _call(self, request, *, structured):
        s = self.settings
        attempts = 1 + (s.structured_retries if structured else 0)
        last = None
        for attempt in range(1, attempts + 1):
            seed = self._seed()
            payload = {"model": s.model, "stream": False, "think": s.think, "prompt": render(request),
                       "options": {"temperature": s.temperature, "top_p": s.top_p, "num_predict": s.num_predict,
                                   "num_ctx": s.num_ctx, "seed": seed}}
            if s.system is not None:
                payload["system"] = s.system
            if structured:
                payload["format"] = request.schema
            role = JUDGE_PURPOSES.get(request.purpose, "generator")
            start = time.perf_counter()
            entry = {"role": role, "purpose": request.purpose, "structured": structured, "attempt": attempt,
                     "seed": seed, "input_tokens": None, "output_tokens": None, "status": "transport_error",
                     "done_reason": None, "prompt_chars": len(payload["prompt"])}
            try:
                data = self.transport(payload)
            except Exception as exc:  # transport failure: recorded, not retried (not a model-output problem)
                entry.update(latency_ms=round((time.perf_counter() - start) * 1000, 3), error=f"{type(exc).__name__}: {exc}"[:300])
                self.log.add(**entry)
                raise ProviderError("transport_error", str(exc)) from exc
            entry["latency_ms"] = round((time.perf_counter() - start) * 1000, 3)
            for source, target in (("prompt_eval_count", "input_tokens"), ("eval_count", "output_tokens")):
                if type(data.get(source)) is int:
                    entry[target] = data[source]
            entry["done_reason"] = data.get("done_reason")
            entry["context_near_limit"] = isinstance(entry["input_tokens"], int) and entry["input_tokens"] >= 0.95 * s.num_ctx
            text = data.get("response")
            try:
                if not isinstance(text, str) or data.get("error"):
                    raise ProviderError("protocol_failure", str(data.get("error")))
                if data.get("done_reason") != "stop" and structured:
                    raise ProviderError("generation_incomplete", str(data.get("done_reason")))
                if data.get("done_reason") != "stop":
                    # A text answer cut at the output cap is still the model's answer: returned as-is, marked.
                    entry.update(status="truncated", latency_ms=entry["latency_ms"])
                    self.log.add(**entry)
                    usage = {k: entry[k] for k in ("input_tokens", "output_tokens") if entry[k] is not None} or None
                    return ModelResponse(text, usage)
                content = text
                if structured:
                    try:
                        content = json.loads(text)
                    except ValueError as exc:
                        raise ProviderError("parse_failure", str(exc)) from exc
                    try:
                        validate(content, request.schema)
                    except ValueError as exc:
                        raise ProviderError("schema_failure", str(exc)) from exc
            except ProviderError as exc:
                entry.update(status=exc.category, error=str(exc)[:300], raw_output=(text or "")[:2000])
                self.log.add(**entry)
                last = exc
                if attempt < attempts and exc.category != "protocol_failure":
                    continue
                raise
            entry["status"] = "ok"
            self.log.add(**entry)
            usage = {k: entry[k] for k in ("input_tokens", "output_tokens") if entry[k] is not None} or None
            return ModelResponse(content, usage)
        raise last  # pragma: no cover


def discover(settings: ModelSettings, transport=None):
    """Identity of the installed model (name, digest, details) from the local server; no pull, no remote model."""
    with urllib.request.urlopen(settings.endpoint + "/api/tags", timeout=10) as response:
        models = json.loads(response.read().decode("utf-8"))["models"]
    model = next((m for m in models if m.get("name") == settings.model), None)
    if model is None or not model.get("digest") or "cloud" in settings.model:
        raise ValueError(f"Model {settings.model!r} is not installed locally; no automatic pull is performed")
    with urllib.request.urlopen(settings.endpoint + "/api/version", timeout=10) as response:
        version = json.loads(response.read().decode("utf-8")).get("version")
    return {"name": model["name"], "digest": model["digest"], "details": model.get("details"),
            "server_version": version, "context_length": (model.get("details") or {}).get("context_length")}
