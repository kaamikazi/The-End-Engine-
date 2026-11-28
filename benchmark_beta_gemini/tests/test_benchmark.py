"""Benchmark Beta-Gemini infrastructure tests (5 conditions, END v0.3.5). SYNTHETIC BENCHMARK INFRASTRUCTURE TEST: scripted models and fake transports;
no live model is called. These validate the benchmark system, not END."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from end_engine.models.base import ModelProvider, ModelRequest, ModelResponse  # noqa: E402
from bench import synthetic  # noqa: E402
from bench.conditions import CONDITIONS, END_CONDITIONS, GENERATION, EndSettings  # noqa: E402
from bench.evaluators import COUNTERS, evaluate  # noqa: E402
from bench.judge import blinded_pairwise  # noqa: E402
from bench.providers import CallLog, ModelOutputError, ModelSettings, OllamaModel, ProviderError, render  # noqa: E402
from bench.report import summarize  # noqa: E402
from bench.runner import execution_plan, load_tasks, run_benchmark  # noqa: E402

TASKS = {t["task_id"]: t for t in load_tasks(HERE / "tasks")}


def run_synthetic(out, *, usage=True, task_ids=None, factory=None):
    tasks = [TASKS[t] for t in (task_ids or synthetic.SCENARIOS)]
    run_benchmark(out, tasks, trials=1, seed=7, model_factory=factory or synthetic.factory(usage=usage),
                  model_record={"provider": "synthetic-scripted", "model": "synthetic-fixture", "label": synthetic.LABEL},
                  data_origin="SYNTHETIC", label=synthetic.LABEL, progress=lambda m: None)
    return summarize(out)


def load(out, kind, run_id):
    return json.loads((Path(out) / kind / f"{run_id}.json").read_text(encoding="utf-8"))


class SyntheticRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.mkdtemp()
        cls.out = Path(cls.temp) / "run"
        cls.summary = run_synthetic(cls.out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp, ignore_errors=True)

    def analysis(self, run_id):
        return load(self.out, "evaluations", run_id)["analysis"]

    def test_01_all_five_conditions_execute_independently(self):
        for task_id in synthetic.SCENARIOS:
            records = [load(self.out, "trials", f"{task_id}.T1.{c}") for c in CONDITIONS]
            self.assertEqual([r["condition"] for r in records], list(CONDITIONS))
            self.assertTrue(all(r["error"] is None and r["calls"] for r in records))
            self.assertEqual(len({id(r["calls"]) for r in records}), len(CONDITIONS))
        # One condition failing does not stop the others.
        out = Path(self.temp) / "failing"
        base = synthetic.factory()

        def factory(log, seed, task, condition, trial):
            if condition == "DIRECT":
                raise_model = base(log, seed, task, condition, trial)
                raise_model.generate = lambda request: (_ for _ in ()).throw(ProviderError("transport_error", "down"))
                return raise_model
            return base(log, seed, task, condition, trial)
        run_synthetic(out, task_ids=["BA-001"], factory=factory)
        direct = load(out, "trials", "BA-001.T1.DIRECT")
        self.assertEqual((direct["error"]["type"], direct["answer"]), ("ProviderError", ""))
        self.assertIsNone(load(out, "trials", "BA-001.T1.FULL_END_NATIVE")["error"])

    def test_02_same_task_prompt_reaches_every_condition(self):
        seen = {}

        class Capture(synthetic.SyntheticModel):
            def generate(self, request):
                seen.setdefault(self.condition, []).append(render(request))
                return super().generate(request)

            def generate_structured(self, request):
                seen.setdefault(self.condition, []).append(render(request))
                return super().generate_structured(request)
        task = TASKS["BA-004"]
        run_synthetic(Path(self.temp) / "capture", task_ids=["BA-004"],
                      factory=lambda log, s, t, c, n: Capture(t["task_id"], c, log))
        self.assertEqual(seen["DIRECT"][0], task["prompt"])
        self.assertEqual(seen["SELF_REFLECT"][0], task["prompt"])
        for condition in END_CONDITIONS:
            if GENERATION[condition] == "native":  # the native C0 request is the task itself, exactly as DIRECT sends it
                self.assertEqual(seen[condition][0], task["prompt"])
            else:
                self.assertIn(json.dumps(task["prompt"], ensure_ascii=False)[1:-1], seen[condition][0])
        hidden = json.dumps(task["evaluation"])
        for texts in seen.values():
            self.assertFalse(any('"capacity": 3' in t or hidden in t for t in texts))  # no hidden expectation sent

    def test_04_trial_ids_unique_and_05_order_reproducible(self):
        tasks = list(TASKS.values())
        plan = execution_plan(tasks, 2, 99)
        ids = [f"{p['task_id']}.T{p['trial']}.{p['condition']}" for p in plan]
        self.assertEqual((len(ids), len(set(ids))), (120, 120))
        self.assertEqual(plan, execution_plan(tasks, 2, 99))
        self.assertNotEqual(plan, execution_plan(tasks, 2, 100))
        orders = {tuple(p["condition"] for p in plan[i:i + 5]) for i in range(0, len(plan), 5)}
        self.assertGreater(len(orders), 1)  # not always the same condition order
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["randomization_seed"], 7)
        self.assertEqual(manifest["executed_order"], [x for x in manifest["planned_order"]])

    def test_08_candidates_scored_09_peak_differs_10_regression_11_overthinking(self):
        ev = load(self.out, "evaluations", "BA-012.T1.END_LITE_NATIVE")
        self.assertEqual(set(ev["candidates"]), {"C0", "C1"})
        p = ev["analysis"]["progression"]
        self.assertEqual((p["peak_candidate_id"], p["returned_candidate_id"], p["missed_peak"]), ("C0", "C1", True))
        self.assertEqual([(r["from"], r["to"]) for r in p["regressions"]], [("C0", "C1")])
        self.assertIn("A_earlier_candidate_better", ev["analysis"]["overthinking"])
        self.assertIn("C_correct_answer_lost", ev["analysis"]["overthinking"])
        self.assertIn("BA-012.T1.END_LITE_NATIVE", self.summary["tags"]["OVERTHINKING"])

    def test_12_rollback_saved_and_13_rollback_hurt(self):
        for c in ("FULL_END_NATIVE", "FULL_END_STRUCTURED"):
            self.assertEqual([r["label"] for r in self.analysis(f"BA-002.T1.{c}")["rollbacks"]], ["ROLLBACK_SAVED_RUN"])
            self.assertEqual([r["label"] for r in self.analysis(f"BA-007.T1.{c}")["rollbacks"]], ["ROLLBACK_HURT_RUN"])
        self.assertEqual(self.summary["tags"]["ROLLBACK_HURT_RUN"], ["BA-007.T1.FULL_END_NATIVE", "BA-007.T1.FULL_END_STRUCTURED"])

    def test_14_false_accept_recorded(self):
        for c in ("FULL_END_NATIVE", "FULL_END_STRUCTURED"):
            cal = self.analysis(f"BA-003.T1.{c}")["calibration"]
            self.assertEqual((cal["internal"], cal["external_passed"], cal["label"]), ("accepted", False, "FALSE_ACCEPT"))
            self.assertIn(f"BA-003.T1.{c}", [f["run_id"] for f in self.summary["calibration"][c]["false_accepts"]])

    def test_17_trajectories_referenced_not_mutated(self):
        for task_id in synthetic.SCENARIOS:
            end = load(self.out, "trials", f"{task_id}.T1.FULL_END_NATIVE")["end"]
            data = (self.out / "trajectories" / end["trajectory_file"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), end["trajectory_sha256"])
            self.assertEqual(json.loads(data.decode().splitlines()[0])["trajectory_id"], end["trajectory_id"])

    def test_18_failure_archive_preserves_originals(self):
        archived = list((self.out / "failures").glob("*/*"))
        self.assertTrue(archived)
        for folder in archived:
            run_id = folder.name
            self.assertEqual((folder / "trial.json").read_bytes(), (self.out / "trials" / f"{run_id}.json").read_bytes())
            self.assertEqual((folder / "evaluation.json").read_bytes(),
                             (self.out / "evaluations" / f"{run_id}.json").read_bytes())

    def test_19_synthetic_fixtures_labelled(self):
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((manifest["data_origin"], manifest["label"]), ("SYNTHETIC", synthetic.LABEL))
        self.assertIn("SYNTHETIC BENCHMARK INFRASTRUCTURE TEST", (self.out / "REPORT.md").read_text(encoding="utf-8"))
        self.assertIn("SYNTHETIC BENCHMARK INFRASTRUCTURE TEST", (self.out / "MANUAL_REVIEW.md").read_text(encoding="utf-8"))
        for path in (self.out / "trials").glob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual((record["data_origin"], record["model"]["label"]), ("SYNTHETIC", synthetic.LABEL))

    def test_20_results_json_round_trips(self):
        for path in [self.out / "summary.json", *list((self.out / "trials").glob("*.json"))[:5]]:
            text = path.read_text(encoding="utf-8")
            self.assertEqual(json.dumps(json.loads(text), indent=1, sort_keys=True, ensure_ascii=False) + "\n", text)
        self.assertEqual(summarize(self.out), json.loads((self.out / "summary.json").read_text(encoding="utf-8")))

    def test_beta_conditions_configuration_and_protocol_metrics(self):
        self.assertEqual(CONDITIONS, ("DIRECT", "SELF_REFLECT", "END_LITE_NATIVE", "FULL_END_NATIVE", "FULL_END_STRUCTURED"))
        for c in END_CONDITIONS:
            end = load(self.out, "trials", f"BA-001.T1.{c}")["end"]
            self.assertEqual((end["candidate_generation"], end["protocol_repair_attempts"]), (GENERATION[c], 1))
        pr = self.summary["protocol_robustness"]
        self.assertEqual(set(pr), set(END_CONDITIONS))
        for key in ("external_blocker", "model_protocol_failure", "repairs_attempted", "repairs_succeeded",
                    "elements_discarded_events", "runs_continued_after_repair", "mean_end_cycles", "c0_score", "c0_format_ok"):
            self.assertIn(key, pr["FULL_END_NATIVE"])
        # Beta-Gemini: no side-by-side with Alpha (different model, different Engine version) by design.
        self.assertIsNone(self.summary["alpha_comparison"])

    def test_resume_never_overwrites(self):
        path = self.out / "trials" / "BA-001.T1.DIRECT.json"
        before = path.read_bytes()
        run_benchmark(self.out, [TASKS["BA-001"]], trials=1, seed=7, model_factory=synthetic.factory(), model_record={},
                      data_origin="SYNTHETIC", progress=lambda m: None)
        self.assertEqual(path.read_bytes(), before)


class FakeTransport:
    def __init__(self, responses):
        self.responses, self.payloads = list(responses), []

    def __call__(self, payload):
        self.payloads.append(payload)
        return self.responses.pop(0)


class TransportTests(unittest.TestCase):
    def model(self, responses, **settings):
        log = CallLog()
        transport = FakeTransport(responses)
        return OllamaModel(ModelSettings("qwen3:4b", **settings), {"digest": "abc"}, log, trial_seed=3,
                           transport=transport), log, transport

    def test_03_settings_recorded_and_sent(self):
        model, log, transport = self.model([{"response": "hi", "done_reason": "stop", "prompt_eval_count": 5, "eval_count": 2}])
        model.generate(ModelRequest("direct_answer", "Say hi", {}, None))
        meta = model.metadata()
        self.assertEqual((meta["model"], meta["digest"], meta["settings"]["temperature"], meta["settings"]["top_p"],
                          meta["settings"]["num_predict"], meta["settings"]["think"]), ("qwen3:4b", "abc", 0.7, 0.8, 4096, False))
        options = transport.payloads[0]["options"]
        self.assertEqual((options["temperature"], options["top_p"], options["num_predict"]), (0.7, 0.8, 4096))
        self.assertEqual(transport.payloads[0]["prompt"], "Say hi")
        self.assertNotIn("system", transport.payloads[0])
        with tempfile.TemporaryDirectory() as d:
            run_benchmark(d, [TASKS["BA-001"]], trials=1, seed=1, model_factory=synthetic.factory(),
                          model_record={"provider": "p", "model": "m", "settings": {"temperature": 0.7, "seed": None}},
                          data_origin="SYNTHETIC", progress=lambda m: None)
            manifest = json.loads(Path(d, "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["model"]["settings"], {"temperature": 0.7, "seed": None})

    def test_15_missing_token_data_stays_null(self):
        model, log, _ = self.model([{"response": "hi", "done_reason": "stop"}])
        model.generate(ModelRequest("direct_answer", "Say hi", {}, None))
        totals = log.totals()
        self.assertEqual((totals["total_tokens"], totals["prompt_tokens"], totals["calls_missing_usage"]), (None, None, 1))
        with tempfile.TemporaryDirectory() as d:
            summary = run_synthetic(Path(d), usage=False, task_ids=["BA-001"])
            self.assertTrue(all(summary["overall"][c]["tokens"]["mean"] is None for c in CONDITIONS))
            self.assertIsNone(load(d, "trials", "BA-001.T1.FULL_END_NATIVE")["cost"]["total_tokens"])

    def test_truncated_text_answer_is_kept_and_marked(self):
        model, log, _ = self.model([{"response": "partial answ", "done_reason": "length", "prompt_eval_count": 5,
                                     "eval_count": 4096}])
        self.assertEqual(model.generate(ModelRequest("direct_answer", "p", {}, None)).content, "partial answ")
        self.assertEqual((log.entries[0]["status"], log.totals()["truncated_text_answers"], log.totals()["failed_attempts"]),
                         ("truncated", 1, 0))

    def test_model_output_failure_is_protocol_not_external_for_end(self):
        """The transport signals malformed structured output with ModelOutputError (ProviderError + ModelProtocolError);
        END v0.3.5 then reports MODEL_PROTOCOL_FAILURE, while a transport exception stays EXTERNAL_BLOCKER."""
        from end_engine import EndEngine, EngineConfig
        from end_engine.models.protocol import ModelProtocolError
        self.assertTrue(issubclass(ModelOutputError, ProviderError) and issubclass(ModelOutputError, ModelProtocolError))

        def broken(payload):
            if "format" in payload:  # every structured response is malformed
                return {"response": "not json", "done_reason": "stop", "prompt_eval_count": 1, "eval_count": 1}
            return {"response": "An answer.", "done_reason": "stop", "prompt_eval_count": 1, "eval_count": 1}

        def down(payload):
            raise ConnectionError("connection refused")
        for transport, expected in ((broken, "MODEL_PROTOCOL_FAILURE"), (down, "EXTERNAL_BLOCKER")):
            with tempfile.TemporaryDirectory() as d:
                log = CallLog()
                model = OllamaModel(ModelSettings("qwen3:4b"), {"digest": "abc"}, log, transport=transport)
                engine = EndEngine(EngineConfig(ledger_dir=d, enable_branching=False, candidate_generation="native",
                                                protocol_repair_attempts=1), provider=model)
                result = engine.run("Say something.", mode="normal", max_cycles=1)
                self.assertEqual(result.termination_reason.value, expected)

    def test_structured_retry_is_logged_and_bounded(self):
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}
        good = {"response": '{"x": 1}', "done_reason": "stop", "prompt_eval_count": 3, "eval_count": 3}
        model, log, _ = self.model([{"response": "not json", "done_reason": "stop"}, good])
        self.assertEqual(model.generate_structured(ModelRequest("critique", "p", {}, schema)).content, {"x": 1})
        self.assertEqual([e["status"] for e in log.entries], ["parse_failure", "ok"])
        model, log, _ = self.model([{"response": "{}", "done_reason": "stop"}, {"response": '{"x": 1}', "done_reason": "length"}])
        with self.assertRaises(ProviderError):
            model.generate_structured(ModelRequest("critique", "p", {}, schema))
        self.assertEqual([e["status"] for e in log.entries], ["schema_failure", "generation_incomplete"])


class EvaluatorTests(unittest.TestCase):
    def test_06_objective_evaluation(self):
        for task_id, (ok, bad) in synthetic.A.items():
            self.assertTrue(evaluate(TASKS[task_id], ok)["passed"], task_id)
            self.assertFalse(evaluate(TASKS[task_id], bad)["passed"], task_id)
        self.assertFalse(evaluate(TASKS["BA-002"], "no code here")["passed"])
        unsafe = "```python\nimport os\ndef chunk(items, size):\n    os.system('echo hi')\n```"
        result = evaluate(TASKS["BA-002"], unsafe)
        self.assertIn("rejected before execution", str(result["checks"][0]["detail"]))

    def test_16_hallucination_counters(self):
        c = lambda task_id, text: evaluate(TASKS[task_id], text)["counters"]
        self.assertEqual(c("BA-011", synthetic.A["BA-011"][1])["scope_overreach_count"], 1)
        self.assertEqual(c("BA-011", synthetic.A["BA-011"][1])["unsupported_high_impact_claim_count"], 1)
        self.assertEqual(c("BA-010", synthetic.A["BA-010"][1])["contradiction_ignored_count"], 1)
        self.assertEqual(c("BA-010", synthetic.A["BA-010"][0])["correct_uncertainty_count"], 1)
        self.assertEqual(c("BA-009", synthetic.FABRICATED_BA009)["fabricated_reference_count"], 1)
        self.assertEqual(c("BA-009", synthetic.A["BA-009"][1])["unsupported_claim_count"], 1)
        self.assertEqual(c("BA-002", synthetic.EXECUTION_CLAIM_BA002)["false_execution_claim_count"], 1)
        self.assertEqual(c("BA-011", synthetic.A["BA-011"][1])["false_execution_claim_count"], 0)  # evidence reports excluded
        accepted = ("Since sorted() is not stable, I use a manual insertion sort.\n```python\ndef sort_by_age(people):\n"
                    "    out = []\n    for p in people:\n        i = len(out)\n        while i > 0 and out[i-1][1] > p[1]:\n"
                    "            i -= 1\n        out.insert(i, p)\n    return out\n```")
        corrected = "Note: sorted() is actually stable (Timsort).\n```python\ndef sort_by_age(people):\n    return sorted(people, key=lambda p: p[1])\n```"
        r1, r2 = evaluate(TASKS["BA-008"], accepted), evaluate(TASKS["BA-008"], corrected)
        self.assertEqual((r1["extracted"]["premise"], r1["passed"], r1["counters"]["unsupported_claim_count"]), ("accepted", False, 1))
        self.assertEqual((r2["extracted"]["premise"], r2["passed"]), ("corrected", True))
        self.assertEqual(set(r1["counters"]), set(COUNTERS))

    def test_07_blinded_judge_never_sees_condition_identity(self):
        captured = []

        class Judge(ModelProvider):
            def generate(self, request):
                raise AssertionError

            def metadata(self):
                return {}

            def generate_structured(self, request):
                captured.append(render(request))
                return ModelResponse({"preferred": "A", "reason": "r"})
        answers = {"FULL_END|C1|ACCEPT_PROVISIONALLY|rollback": "answer one", "DIRECT": "answer two"}
        verdict, mapping, _ = blinded_pairwise(Judge(), "task", answers, seed=5)
        text = captured[0]
        for forbidden in ("FULL_END", "DIRECT", "END_LITE", "SELF_REFLECT", "C1", "ACCEPT", "rollback", "iteration"):
            self.assertNotIn(forbidden, text)
        self.assertIn("ANSWER A", text)
        self.assertEqual(verdict["preferred_source"], mapping["A"])
        self.assertEqual(set(mapping.values()), set(answers))


if __name__ == "__main__":
    unittest.main()
