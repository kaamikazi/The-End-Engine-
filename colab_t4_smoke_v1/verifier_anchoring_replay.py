"""Replay run 1's last verification request (C3, qwen3:4b) under three conditions to test score anchoring.

A: unchanged (previous_verification included)
B: previous_verification removed
C: previous_verification with every dimension set to 0.3 (a fake prior)
"""
import copy, glob, json, sys, time

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\The End Engine")
from end_engine.models.base import ModelRequest
from v0351_core_regression_pilot.bench.providers import CallLog, ModelSettings, OllamaModel, discover

RUN = sys.argv[1]
SAMPLES = int(sys.argv[2]) if len(sys.argv) > 2 else 3
t = json.loads(open(glob.glob(RUN + "/ledger/*.jsonl")[0], encoding="utf-8").read())
calls = [m for m in t["model_calls"] if m["request"].get("purpose") == "verification"]
src = calls[-1]["request"]
original_dims = calls[-1]["response"]["content"]["dimensions"]
print("replaying", calls[-1]["call_id"], "candidate", src["context"]["candidate"]["candidate_id"])
print("original response dims:", original_dims)
prev = src["context"]["previous_verification"][-1]
print("prior shown (prev dims):", prev.get("dimensions"))

def variant(kind):
    ctx = copy.deepcopy(src["context"])
    if kind == "B":
        ctx["previous_verification"] = []
    elif kind == "C":
        p = ctx["previous_verification"][-1]
        dims = p["dimensions"]
        p["dimensions"] = [[k, 0.3] for k, _ in dims] if isinstance(dims, list) else {k: 0.3 for k in dims}
        p["score"] = 0.3
    return ModelRequest("verification", src["prompt"], ctx, src["schema"])

settings = ModelSettings(model="qwen3:4b")
identity = discover(settings)
results = {}
for kind in ("A", "B", "C"):
    results[kind] = []
    for i in range(SAMPLES):
        log = CallLog()
        model = OllamaModel(settings, identity, log, trial_seed=1000 + i)
        start = time.time()
        try:
            out = model.generate_structured(variant(kind)).content
            dims = out["dimensions"]
            results[kind].append(dims)
            print(f"{kind}{i}: {round(time.time()-start)}s prompt_tokens={log.entries[-1]['input_tokens']} dims={dims}", flush=True)
        except Exception as exc:
            print(f"{kind}{i}: FAILED {type(exc).__name__}: {str(exc)[:200]}", flush=True)

def same(d):
    p = prev["dimensions"]
    p = dict(p) if isinstance(p, list) else p
    return d == p
print("\nSUMMARY (matches prior exactly):")
for kind, rows in results.items():
    print(kind, f"{sum(same(r) for r in rows)}/{len(rows)} identical to prior", "| mean scores:",
          {k: round(sum(r[k] for r in rows) / len(rows), 2) for k in rows[0]} if rows else None)
