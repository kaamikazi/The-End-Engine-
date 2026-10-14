"""Gemini transport tests (SYNTHETIC: fake transports; no network, no real key)."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from end_engine.models.base import ModelRequest  # noqa: E402
from end_engine.models.protocol import ModelProtocolError  # noqa: E402
from bench import gemini  # noqa: E402
from bench.gemini import GeminiModel, GeminiSettings, probe  # noqa: E402
from bench.providers import CallLog, ModelOutputError, ProviderError  # noqa: E402

FAKE_KEY = "FAKE-KEY-0123456789-not-real"
SCHEMA = {"type": "object", "properties": {"x": {"type": "string", "minLength": 1}}, "required": ["x"],
          "additionalProperties": False}


def reply(text, reason="STOP", prompt=10, out=5, thoughts=3, version="gemini-3.8-flash-001"):
    return 200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": reason}],
                 "usageMetadata": {"promptTokenCount": prompt, "candidatesTokenCount": out, "thoughtsTokenCount": thoughts},
                 "modelVersion": version}


class Fake:
    def __init__(self, *responses):
        self.responses, self.bodies = list(responses), []

    def __call__(self, body):
        self.bodies.append(body)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def model(fake, **settings):
    log = CallLog()
    return GeminiModel(GeminiSettings(**settings), log, transport=fake, sleep=lambda s: None), log


@mock.patch.dict(os.environ, {"GEMINI_API_KEY": FAKE_KEY})
class GeminiTransportTests(unittest.TestCase):
    def test_plain_inference_payload_no_tools_thinking_low(self):
        fake = Fake(reply("hello"), reply('{"x": "y"}'))
        m, log = model(fake)
        self.assertEqual(m.generate(ModelRequest("direct_answer", "Say hi", {}, None)).content, "hello")
        self.assertEqual(m.generate_structured(ModelRequest("critique", "p", {"a": 1}, SCHEMA)).content, {"x": "y"})
        text_body, json_body = fake.bodies
        for body in fake.bodies:
            self.assertNotIn("tools", body)
            self.assertNotIn("toolConfig", body)
            self.assertNotIn("systemInstruction", body)
            config = body["generationConfig"]
            self.assertEqual((config["temperature"], config["topP"], config["maxOutputTokens"],
                              config["thinkingConfig"]), (0.7, 0.8, 4096, {"thinkingLevel": "low"}))
        self.assertEqual(text_body["contents"][0]["parts"][0]["text"], "Say hi")  # the task verbatim, like Ollama
        self.assertEqual(json_body["generationConfig"]["responseMimeType"], "application/json")
        self.assertNotIn("minLength", json.dumps(json_body["generationConfig"]["responseJsonSchema"]))

    def test_api_key_only_in_header_never_in_url_logs_or_metadata(self):
        captured = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps(reply("ok")[1]).encode()

        def urlopen(request, timeout):
            captured.append(request)
            return Response()
        log = CallLog()
        m = GeminiModel(GeminiSettings(), log)
        with mock.patch("urllib.request.urlopen", urlopen):
            m.generate(ModelRequest("direct_answer", "Say hi", {}, None))
        request = captured[0]
        self.assertNotIn(FAKE_KEY, request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), FAKE_KEY)
        self.assertNotIn(FAKE_KEY, request.data.decode())
        self.assertNotIn(FAKE_KEY, json.dumps(log.entries) + json.dumps(m.metadata()))

    def test_missing_key_is_external_and_not_leaked(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            m, log = model(GeminiModel(GeminiSettings(), CallLog())._http)
            with self.assertRaises(ProviderError) as ctx:
                m.generate(ModelRequest("direct_answer", "x", {}, None))
            self.assertEqual(ctx.exception.category, "missing_api_key")
            self.assertNotIsInstance(ctx.exception, ModelProtocolError)

    def test_rate_limit_backoff_is_bounded_and_logged(self):
        limited = (429, {"error": {"message": "quota", "details": [{"retryDelay": "7s"}]}})
        m, log = model(Fake(limited, limited, reply("ok")))
        self.assertEqual(m.generate(ModelRequest("direct_answer", "x", {}, None)).content, "ok")
        self.assertEqual([w["wait_seconds"] for w in log.entries[0]["rate_limit_waits"]], [7.0, 7.0])
        m, log = model(Fake(*[limited] * 3), rate_limit_waits=2)
        with self.assertRaises(ProviderError) as ctx:
            m.generate(ModelRequest("direct_answer", "x", {}, None))
        self.assertEqual(ctx.exception.category, "rate_limited")  # external, not a protocol failure
        self.assertNotIsInstance(ctx.exception, ModelProtocolError)

    def test_model_output_failures_are_protocol_errors_and_tokens_include_thinking(self):
        m, log = model(Fake(reply("not json"), reply("still not json")))
        with self.assertRaises(ModelOutputError) as ctx:
            m.generate_structured(ModelRequest("critique", "p", {}, SCHEMA))
        self.assertIsInstance(ctx.exception, ModelProtocolError)
        self.assertEqual([e["status"] for e in log.entries], ["parse_failure", "parse_failure"])
        m, log = model(Fake(reply('{"x": "y"}', reason="MAX_TOKENS"), reply('{"x": "y"}')))
        self.assertEqual(m.generate_structured(ModelRequest("critique", "p", {}, SCHEMA)).content, {"x": "y"})
        self.assertEqual(log.entries[0]["status"], "generation_incomplete")
        self.assertEqual((log.entries[1]["input_tokens"], log.entries[1]["output_tokens"], log.entries[1]["thought_tokens"]),
                         (10, 8, 3))
        m, log = model(Fake(reply("partial", reason="MAX_TOKENS")))
        self.assertEqual(m.generate(ModelRequest("direct_answer", "p", {}, None)).content, "partial")
        self.assertEqual(log.entries[0]["status"], "truncated")
        m, log = model(Fake((200, {"promptFeedback": {"blockReason": "SAFETY"}})))
        with self.assertRaises(ProviderError) as ctx:
            m.generate(ModelRequest("direct_answer", "p", {}, None))
        self.assertNotIsInstance(ctx.exception, ModelProtocolError)

    def test_connection_failure_is_external(self):
        m, log = model(Fake(ConnectionError("refused")))
        with self.assertRaises(ProviderError) as ctx:
            m.generate(ModelRequest("direct_answer", "p", {}, None))
        self.assertEqual(ctx.exception.category, "transport_error")

    def test_probe_sends_exactly_one_request(self):
        fake = Fake(reply('{"ok": true}'), reply('{"ok": true}'))
        result = probe(GeminiSettings(), transport=fake)
        self.assertEqual((len(fake.bodies), result["status"], result["model_version"]), (1, "ok", "gemini-3.8-flash-001"))
        fake = Fake((429, {"error": {"message": "quota"}}), reply('{"ok": true}'))
        result = probe(GeminiSettings(), transport=fake)
        self.assertEqual((len(fake.bodies), result["status"], result["category"]), (1, "failed", "rate_limited"))


if __name__ == "__main__":
    unittest.main()
