# ABORTED — local-Qwen Benchmark Beta attempt (not an official result)

**Do not use these records as Benchmark Beta results.** They are preserved exactly as written and are not part of any
official Beta summary.

## What ran

| | |
|---|---|
| Engine | END Engine v0.3.5, fingerprint `520d2052832eaee93f7c8931e028762c7008006ae61f2fdc7ec6589d7e4bd448` |
| Model | `qwen3:4b` (local Ollama, digest `359d7dd4bcda…`), with the Alpha settings |
| Design | 5 conditions × 12 tasks × 2 trials = 120 planned runs, seed 20261102 (`PREFLIGHT.json`, `manifest.json`) |
| Started | 2026-10-01T07:27:57Z |
| Stopped | 2026-10-01 at about 08:35Z, by the user's decision |

## Completed runs (2 of 120)

| Run | Duration | Calls | Tokens |
|---|---|---|---|
| `BA-006.T1.FULL_END_NATIVE` | 3,551 s | 66 | 280,529 |
| `BA-006.T1.DIRECT` | 281 s | 1 | 4,326 |

`BA-006.T1.FULL_END_STRUCTURED` was in progress when the process was stopped. It left no trial, evaluation or trajectory
record, because records are written only when a run completes.

## Why it was stopped

With v0.3.5 the END loop runs its full budget instead of aborting, as v0.3.4 did in Alpha. The first DEEP-mode
FULL_END run took 59 minutes, and the whole 120-run design projected to about 40 hours of local inference. The user's
laptop cannot reasonably sustain that.

## Status

- **Incomplete.** No conclusion about v0.3.5 on Qwen may be drawn from these two runs.
- **Alpha (v0.3.4) stays** the frozen historical Qwen baseline in `benchmark_alpha/`.
- **The Gemini experiment** is a separate benchmark in `benchmark_beta_gemini/`, and is never mixed with these records.

## Files

All 11 files are byte-identical to the moment the run stopped (SHA-256 checked across the move):
- `manifest.json`, `PREFLIGHT.json`;
- `trials/`, `evaluations/`, `trajectories/`;
- `preflight/` (Engine 182/182 and Beta infrastructure 20/20 test records);
- `live_progress.log`.

The only addition to `live_progress.log` is a final line recording the stop.
