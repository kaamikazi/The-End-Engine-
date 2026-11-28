"""Replay a Colab run's revision-plan requests with the old and the new planner prompt on local Ollama.

Usage: python planner_fix_replay.py <extracted run folder> [model] [samples]
Counts plan changes that ask for evidence a revision cannot create (studies, references, metrics, ...).
"""
import glob, json, re, sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\The End Engine")
from end_engine.models.base import ModelRequest
from end_engine.core import revision_planner
from v0351_core_regression_pilot.bench.providers import CallLog, ModelSettings, OllamaModel, discover

RUN = sys.argv[1]
MODEL = sys.argv[2] if len(sys.argv) > 2 else "qwen3:8b"
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 1
EVIDENCE = re.compile(r"\b(?:citations?|references?|empirical|stud(?:y|ies)|benchmarks?|measurements?|metrics?|"
                      r"real[- ]world (?:results?|data|implementations?|examples?|deployments?|testing)|"
                      r"performance data|case stud(?:y|ies)|experiments?|experimental|simulations?|validation)\b", re.I)

t = json.loads(open(glob.glob(RUN + "/ledger/*.jsonl")[0], encoding="utf-8").read())
calls = [m for m in t["model_calls"] if m["request"].get("purpose") == "revision_plan"]
src = open(revision_planner.__file__, encoding="utf-8").read()
added = re.search(r"prompt \+= \((' A revision cannot create evidence.*?)\)\n", src, re.S).group(1)
addition = "".join(re.findall(r"'([^']*)'", added))
old_marker = "Do not add unsupported evidence or verification authority."

settings = ModelSettings(model=MODEL, num_ctx=16384)
identity = discover(settings)
print("model", MODEL, "| plan requests", len(calls), "| added text:", addition[:80], "...")
totals = {"old": [0, 0], "new": [0, 0]}
for m in calls:
    req = m["request"]
    old_prompt = req["prompt"]
    assert old_prompt.endswith(old_marker) and "cannot create evidence" not in old_prompt
    for label, prompt in (("old", old_prompt), ("new", old_prompt + addition)):
        for i in range(SAMPLES):
            out = OllamaModel(settings, identity, CallLog(), trial_seed=3000 + i).generate_structured(
                ModelRequest("revision_plan", prompt, req["context"], req["schema"])).content
            actions = [c["action"] for c in out["changes"]]
            asks = [a for a in actions if EVIDENCE.search(a)]
            totals[label][0] += len(asks); totals[label][1] += len(actions)
            print(f"{req['context']['candidate']['candidate_id']} {label}: {len(asks)}/{len(actions)} changes ask for evidence", flush=True)
            for a in actions:
                print(f"    {'EVIDENCE ' if EVIDENCE.search(a) else ''}- {a[:170]}", flush=True)
print("\nTOTAL", {k: f"{v[0]}/{v[1]} changes ask for evidence" for k, v in totals.items()})
