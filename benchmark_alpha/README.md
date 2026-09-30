# END Engine — Benchmark Alpha

A small, inspectable first benchmark of END Engine **v0.3.4 as it exists**. It does not modify the cognitive core:
all benchmark code lives here, outside `end_engine/` and `tests/`, and outside the Engine fingerprint scope.

## Layout

| Path | Contents |
|---|---|
| `ENGINE_BASELINE.json` | Frozen Engine identity, recorded before benchmark work: version, fingerprint, Python, 164/164 tests |
| `tasks/BA-*.json` | The 12-task pack. Only `prompt` is sent to a model; `evaluation` holds the hidden expectations. |
| `bench/` | Code: `providers.py` (transport and call log), `conditions.py` (the four conditions), `evaluators.py` (external evaluation and hallucination counters), `analysis.py`, `runner.py`, `report.py`, `judge.py`, `synthetic.py`, `cli.py`, `make_tasks.py` |
| `tests/test_benchmark.py` | Infrastructure tests (SYNTHETIC) |
| `synthetic/` | SYNTHETIC BENCHMARK INFRASTRUCTURE TEST output: scripted models, not evidence |
| `manifest.json`, `trials/`, `evaluations/`, `trajectories/`, `failures/`, `summary.json`, `results.csv`, `REPORT.md`, `MANUAL_REVIEW.md` | The live run |
| `live_progress.log` | Progress log of the live run |

END trajectories are written to `trajectories/` through the Engine's own ledger. They are never written to the
Engine's normal ledger directory, and the benchmark only reads them. Each trial record stores the trajectory ID and the
file's SHA-256.

## Commands

Run from `benchmark_alpha/` with Python ≥ 3.11:

```
python -B -m unittest discover -s tests -t .
python -B -m bench.cli synthetic synthetic
python -B -m bench.cli live . --model qwen3:4b --trials 3
python -B -m bench.cli summarize .
```

`live` needs a local Ollama server on `127.0.0.1:11434` with the model already installed. Nothing is downloaded, and
no credentials exist or are sent. Runs are resumable: an existing `trials/<run_id>.json` is never overwritten.

## Rules this benchmark keeps

- END never grades itself. Internal gates and verifiers are recorded and compared with external results; they are never
  used as ground truth.
- Failures are recorded, not fixed. There are no run-level retries. Structured model calls get one transport-level
  retry after a parse/schema/length failure, and it is logged.
- No monetary cost is estimated (no pricing configured). Unknown token counts stay `null`.
