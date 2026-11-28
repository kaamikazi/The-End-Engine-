# Benchmark Beta — plan (not executed)

Status: **plan only. Nothing here has been run, and no model inference has been consumed.** Beta needs separate
authorization.

## Purpose

Measure END Engine v0.3.5 on exactly the Benchmark Alpha task set and external evaluators, so that the v0.3.4 → v0.3.5
comparison changes one thing: the Engine.

## Fixed from Alpha (do not change)

- **Task pack:** `benchmark_alpha/tasks/BA-*.json`, task-set hash `9e177f6d6be25acf82010d898e42a86c7a4d516af882eaa1725bcb5efe468ca6`.
- **External evaluators:** `benchmark_alpha/bench/evaluators.py`, version `alpha-3`. Copy them into Beta unchanged and
  check that the copy's hash matches.
- **Model:** `qwen3:4b`, local Ollama, model digest `359d7dd4bcda…`, with Alpha's settings: temperature 0.7, top_p 0.8,
  `num_predict` 4096, `num_ctx` 8192, `think: false`, one transport retry for structured output, 900 s timeout.
- **Design:** conditions, randomization procedure and analysis definitions as in Alpha. Use a new seed and record it.
- **Alpha artifacts** stay read-only. Beta writes only under `benchmark_beta/`.

## What changes

- Engine v0.3.5, fingerprint recorded in `benchmark_beta/manifest.json` at run time.
- END conditions use v0.3.5 defaults: `protocol_repair_attempts = 1`.

**Open decision before authorization:** `candidate_generation` for the END conditions. The default `"structured"` keeps
v0.3.4's generation requests, so it isolates the effect of protocol recovery and grounding. `"native"` is the v0.3.5
C0 fix. Options:

| Option | Conditions | Runs (12 tasks × 2 trials) | Rough time |
|---|---|---|---|
| (a) | FULL_END and END_LITE in native mode | 96 | ≈ 5–6 h (Alpha: 96 runs ≈ 5.5 h) |
| (b) | (a) plus FULL_END_STRUCTURED, separating "recovery + grounding" from "native generation" | 120 | ≈ 7 h |
| (c) | DIRECT and SELF_REFLECT reused from Alpha (same model, settings and tasks), only END conditions run | 48 | ≈ 3 h; weaker, because the baselines are not re-sampled in the same session |

## Measures (v0.3.4 Alpha value → v0.3.5 Beta: MEASURE)

| Measure | Alpha (v0.3.4) |
|---|---|
| FULL_END `EXTERNAL_BLOCKER` | 22/24 |
| FULL_END `MODEL_PROTOCOL_FAILURE` | n/a (did not exist) |
| Mean FULL_END END cycles | 0.33 |
| FULL_END pass rate | 8/24 |
| END_LITE pass rate | 8/24 |
| END C0 mean external score | 0.349 |
| END C0 required-structure presence | 23/48 |
| BA-002 judge misattribution (rejecting correct code by quoting task code) | present |
| BA-008 false-premise rejection | present |
| BA-009 consensus presented as confirmation | present (4/4 END answers leaned on consensus) |
| Protocol repairs attempted / succeeded / discarded elements | n/a |
| Tokens, calls, latency per condition | see Alpha `summary.json` |

Plus every Alpha section: calibration, hallucination counters, candidate progression, rollback value, operator effects,
the failure archive and a manual review set.

## Rules

- END never grades itself; deterministic external evaluators only.
- Failures are recorded, not fixed during the run.
- Do not tune v0.3.5 against the Alpha or Beta answers.
- A positive Beta result would still be one model and twelve tasks.

## Command (after authorization; the Beta harness must first be copied from Alpha's `bench/` with a native-mode option)

```
python -B -m bench.cli live . --model qwen3:4b --trials 2
```
