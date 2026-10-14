# v0.3.5.1 Core Regression Pilot Replay

Fresh local inference only: the exact historical 12-run plan, four Alpha tasks,
three conditions, one trial and max_cycles=3 for both FULL_END modes. No task contract
metadata is added. Decisions remain baseline; repair failure limit and no-progress
patience use untouched v0.3.5.1 defaults of two. This is not Benchmark Beta.

Copied tasks, evaluator, providers, conditions, analysis and upstream evaluation
helper are byte-identical to the old pilot. Engine behavior is not patched here.
Only the new runner/reporting records v0.3.5.1 observations. The no-candidate scoring
wrapper avoids an undefined candidate progression while retaining frozen empty-answer
scores. Safety withholding is recorded separately from raw candidate quality.

Use Python 3.11+, PYTHONDONTWRITEBYTECODE=1, from repository root:

    python -B -m v0351_core_regression_pilot.prepare
    python -B -m unittest v0351_core_regression_pilot.tests
    python -B -m v0351_core_regression_pilot.run_pilot preflight
    python -B -m v0351_core_regression_pilot.run_pilot live

Preflight source/tests/history snapshots are exclusive; do not rerun prepare over
them. Live execution uses an OS lock, skips completed trials and archives interrupted
partial attempts before resuming missing runs. Actual local requests/responses and
usage are persisted. Only loopback Ollama endpoints are used; HTTP proxies are
bypassed and cloud credential variables removed in the process. Nothing is pulled
or installed. Separate hidden-thinking/token-context fields are omitted, while
observable in-band text is retained as research evidence.

The original runtime projection formula and six-hour guard are retained. Every
completed trial is saved before external evaluation. No historical result is
rescored and no evaluator result enters the Engine. Tasks, evaluator, prompts,
Engine and runner controls are frozen before inference; an invalid infrastructure
condition stops rather than being repaired during the experiment.

All eight FULL_END trajectories require manual review. Same order and exposed
generation seeds do not eliminate sampling noise or justify a general superiority
claim. Report task quality, mechanism correctness, epistemic safety and cost separately.
