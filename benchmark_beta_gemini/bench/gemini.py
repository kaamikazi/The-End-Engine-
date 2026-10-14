"""Gemini Developer API transport for Benchmark Beta-Gemini (stdlib only).

The same ModelProvider contract, call log, request rendering and failure semantics as the Ollama transport:
* plain model inference only: no `tools`, no Google Search grounding, no code execution, no system instruction;
* the API key is read from the GEMINI_API_KEY environment variable at request time and sent only in the
  `x-goog-api-key` header. It never appears in URLs, metadata, call logs, errors, prompts or artifacts;
* malformed structured output (unparseable, schema-invalid, cut at the output cap) raises ModelOutputError, which END
  v0.3.5 classifies as a model-protocol failure; transport/availability failures stay ProviderError (external);
* HTTP 429/500/503 are retried with bounded backoff (honouring the server's retryDelay); every wait is logged.
Unknown token counts stay None. Thinking tokens are recorded separately and counted as output (they bill as output)."""
from dataclasses import asdict, dataclass
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

from end_engine.models.base import ModelProvider, ModelResponse
from end_engine.models.schema import validate

from .providers import JUDGE_PURPOSES, CallLog, ModelOutputError, ProviderError, render

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
KEY_ENV = "GEMINI_API_KEY"
UNSUPPORTED_SCHEMA_KEYS = ("minLength", "maxLength")  # enforced by END's own validation after the response


@dataclass(frozen=True)
class GeminiSettings:
    model: str = "gemini-3.8-flash"
    provider: str = "google-gemini-api"
    temperature: float = 0.7
    top_p: float = 0.8
    max_output_tokens: int = 4096
    thinking_level: str = "low"          # cannot be disabled on gemini-3.8-flash; "low" is the minimum
    timeout_seconds: float = 300.0
    structured_retries: int = 1          # same transport policy as Alpha/Beta-Qwen
    schema_field: str = "responseJsonSchema"
    rate_limit_waits: int = 6            # bounded backoff on 429/500/503
    max_wait_seconds: float = 120.0
    min_interval_seconds: float = 0.0    # optional client-side pacing between requests
    seed: None = None                    # not sent: no per-call seed is used for this provider
    system: str | None = None


def _gemini_schema(schema):
    """JSON Schema for Gemini structured output; keywords the API does not accept are dropped (END re-validates)."""
    if isinstance(schema, dict):
        return {k: _gemini_schema(v) for k, v in schema.items() if k not in UNSUPPORTED_SCHEMA_KEYS}
    if isinstance(schema, list):
        return [_gemini_schema(v) for v in schema]
    return schema


def _scrub(text):
    key = os.environ.get(KEY_ENV)
    text = str(text)
    return text.replace(key, "<redacted>") if key else text


def _retry_delay(body):
    for detail in (body.get("error") or {}).get("details", []) if isinstance(body, dict) else []:
        delay = detail.get("retryDelay")
        if isinstance(delay, str) and delay.endswith("s"):
            try:
                return float(delay[:-1])
            except ValueError:
                pass
    return None


class GeminiModel(ModelProvider):
    def __init__(self, settings: GeminiSettings, log: CallLog, *, trial_seed=0, transport=None, sleep=time.sleep):
        self.settings, self.log, self.trial_seed = settings, log, trial_seed
        self.transport = transport or self._http
        self.sleep = sleep
        self.model_version = None
        self._last = 0.0

    def metadata(self):
        return {"provider": self.settings.provider, "model": self.settings.model, "model_version": self.model_version,
                "settings": asdict(self.settings), "data_origin": "LIVE_GEMINI_API"}

    def generate(self, request):
        return self._call(request, structured=False)

    def generate_structured(self, request):
        return self._call(request, structured=True)

    def payload(self, request, structured):
        s = self.settings
        config = {"temperature": s.temperature, "topP": s.top_p, "maxOutputTokens": s.max_output_tokens,
                  "thinkingConfig": {"thinkingLevel": s.thinking_level}}
        if structured:
            config["responseMimeType"] = "application/json"
            config[s.schema_field] = _gemini_schema(request.schema)
        body = {"contents": [{"role": "user", "parts": [{"text": render(request)}]}], "generationConfig": config}
        if s.system is not None:
            body["systemInstruction"] = {"parts": [{"text": s.system}]}
        return body

    def _http(self, body):
        key = os.environ.get(KEY_ENV)
        if not key:
            raise ProviderError("missing_api_key", f"{KEY_ENV} is not set")
        req = urllib.request.Request(API.format(model=self.settings.model), data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=self.settings.timeout_seconds) as response:
                return 200, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, json.loads(exc.read().decode("utf-8"))
            except ValueError:
                return exc.code, {"error": {"message": _scrub(exc)}}

    def _send(self, body, entry):
        """POST with bounded backoff on 429/500/503. Returns the parsed JSON body or raises ProviderError."""
        waits = 0
        while True:
            if self.settings.min_interval_seconds:
                gap = self.settings.min_interval_seconds - (time.monotonic() - self._last)
                if gap > 0:
                    self.sleep(gap)
            self._last = time.monotonic()
            try:
                status, data = self.transport(body)
            except ProviderError:
                raise
            except Exception as exc:  # connection, timeout: external
                raise ProviderError("transport_error", _scrub(f"{type(exc).__name__}: {exc}")) from exc
            if status == 200:
                return data
            message = _scrub(((data or {}).get("error") or {}).get("message", ""))[:300]
            if status in (429, 500, 503) and waits < self.settings.rate_limit_waits:
                delay = min(self.settings.max_wait_seconds, _retry_delay(data) or 2 ** (waits + 2))
                entry.setdefault("rate_limit_waits", []).append({"http_status": status, "wait_seconds": delay,
                                                                 "message": message})
                waits += 1
                self.sleep(delay)
                continue
            raise ProviderError("rate_limited" if status == 429 else f"http_{status}", message)

    def _call(self, request, *, structured):
        s = self.settings
        attempts = 1 + (s.structured_retries if structured else 0)
        for attempt in range(1, attempts + 1):
            role = JUDGE_PURPOSES.get(request.purpose, "generator")
            entry = {"role": role, "purpose": request.purpose, "structured": structured, "attempt": attempt,
                     "seed": None, "input_tokens": None, "output_tokens": None, "thought_tokens": None,
                     "status": "transport_error", "done_reason": None, "prompt_chars": len(render(request))}
            start = time.perf_counter()
            try:
                data = self._send(self.payload(request, structured), entry)
            except ProviderError as exc:
                entry.update(latency_ms=round((time.perf_counter() - start) * 1000, 3), status=exc.category,
                             error=_scrub(exc)[:300])
                self.log.add(**entry)
                raise
            entry["latency_ms"] = round((time.perf_counter() - start) * 1000, 3)
            usage = data.get("usageMetadata") or {}
            thoughts = usage.get("thoughtsTokenCount")
            entry["input_tokens"] = usage.get("promptTokenCount") if type(usage.get("promptTokenCount")) is int else None
            out = usage.get("candidatesTokenCount")
            if type(out) is int:
                entry["output_tokens"] = out + (thoughts if type(thoughts) is int else 0)
            elif type(thoughts) is int:
                entry["output_tokens"] = thoughts  # thinking only, no visible output
            entry["thought_tokens"] = thoughts if type(thoughts) is int else None
            self.model_version = data.get("modelVersion") or self.model_version
            entry["model_version"] = data.get("modelVersion")
            candidates = data.get("candidates") or []
            reason = candidates[0].get("finishReason") if candidates else (data.get("promptFeedback") or {}).get("blockReason")
            entry["done_reason"] = reason
            parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            try:
                if not candidates or reason not in ("STOP", "MAX_TOKENS"):
                    raise ProviderError("response_blocked_or_empty", str(reason))
                if reason == "MAX_TOKENS" and structured:
                    raise ModelOutputError("generation_incomplete", "MAX_TOKENS", text)
                content = text
                if structured:
                    try:
                        content = json.loads(text)
                    except ValueError as exc:
                        raise ModelOutputError("parse_failure", str(exc), text) from exc
                    try:
                        validate(content, request.schema)
                    except ValueError as exc:
                        raise ModelOutputError("schema_failure", str(exc), content) from exc
            except ProviderError as exc:
                category = getattr(exc, "transport_category", exc.category)
                entry.update(status=category, error=_scrub(exc)[:300], raw_output=text[:2000])
                self.log.add(**entry)
                if attempt < attempts and isinstance(exc, ModelOutputError):
                    continue
                raise
            entry["status"] = "truncated" if reason == "MAX_TOKENS" else "ok"
            self.log.add(**entry)
            reported = {k: entry[k] for k in ("input_tokens", "output_tokens") if entry[k] is not None} or None
            return ModelResponse(content, reported)


def probe(settings: GeminiSettings, transport=None):
    """ONE tiny structured request: connectivity, model identity (modelVersion), structured-output support, usage."""
    log = CallLog()
    model = GeminiModel(settings, log, transport=transport, sleep=lambda s: None)
    from end_engine.models.base import ModelRequest
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}
    result = {"request_count": 1, "model_requested": settings.model}
    s = settings
    tiny = GeminiSettings(**{**asdict(s), "structured_retries": 0, "rate_limit_waits": 0})
    model.settings = tiny
    try:
        response = model.generate_structured(ModelRequest("connectivity_probe", 'Return {"ok": true}.', {}, schema))
        result.update(status="ok", content=response.content)
    except ProviderError as exc:
        result.update(status="failed", category=exc.category, message=_scrub(exc)[:300])
    entry = log.entries[0] if log.entries else {}
    result.update(model_version=model.model_version, http_attempts=1 + len(entry.get("rate_limit_waits", [])),
                  finish_reason=entry.get("done_reason"), latency_ms=entry.get("latency_ms"),
                  usage={k: entry.get(k) for k in ("input_tokens", "output_tokens", "thought_tokens")})
    return result
