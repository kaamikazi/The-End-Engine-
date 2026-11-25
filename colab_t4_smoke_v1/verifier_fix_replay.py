"""Replay every verification of a Colab run as the fixed LLMVerifier sends it (no previous_verification).

Usage: python verifier_fix_replay.py <extracted run folder> [samples]
Prints the original (anchored) scores next to the replayed ones for each candidate.
"""
import copy, glob, json, sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\The End Engine")
from end_engine.models.base import ModelRequest
from v0351_core_regression_pilot.bench.providers import CallLog, ModelSettings, OllamaModel, discover

RUN, SAMPLES = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2
t = json.loads(open(glob.glob(RUN + "/ledger/*.jsonl")[0], encoding="utf-8").read())
calls = [m for m in t["model_calls"] if m["request"].get("purpose") == "verification"]
model_name = calls[0]["model"]["model"]
settings = ModelSettings(model=model_name)
identity = discover(settings)
print("model", model_name)

def mean(d):
    return round(sum(d.values()) / len(d), 3)

for m in calls:
    req = m["request"]
    ctx = copy.deepcopy(req["context"])
    ctx.pop("previous_verification", None)
    cand = ctx["candidate"]["candidate_id"]
    orig = m["response"]["content"]["dimensions"]
    print(f"\n{cand}: original mean {mean(orig)} {orig}", flush=True)
    for i in range(SAMPLES):
        log = CallLog()
        out = OllamaModel(settings, identity, log, trial_seed=2000 + i).generate_structured(
            ModelRequest("verification", req["prompt"], ctx, req["schema"])).content
        print(f"  replay {i}: mean {mean(out['dimensions'])} {out['dimensions']} issues={len(out['remaining_issues'])}", flush=True)
