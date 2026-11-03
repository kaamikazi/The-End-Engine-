# v0.3.5 Core Regression Pilot

This is a separate diagnostic: four Alpha tasks ×three conditions ×one trial =12
runs. It is not Benchmark Beta or a publication-quality comparison. Both FULL_END
conditions have max_cycles=3 and protocol_repair_attempts=1; they differ only in
candidate_generation. Jev is explicitly baseline/disabled. Cloud APIs are not used.

Frozen copies: Alpha tasks and evaluator; existing Beta providers/conditions/analysis
and evaluate_run helper. The Beta transport preserves Alpha model settings and
correctly signals v0.3.5 ModelProtocolError after structured-output failures.
No historical file or Engine source is edited. All outputs remain in this directory.

Commands from the repository root, using Python 3.11+ and PYTHONDONTWRITEBYTECODE=1:

    python -B -m unittest v035_core_regression_pilot.tests
    python -B -m v035_core_regression_pilot.run_pilot preflight
    python -B -m v035_core_regression_pilot.run_pilot live
    python -B -m v035_core_regression_pilot.run_pilot summarize

The live command launches only missing trial records, with an OS lock preventing
duplicate execution. Interrupted wire/call artifacts are archived before a missing
run is resumed. Completed trial records are saved exclusively before evaluation.
Infrastructure/evaluation defects stop the pilot rather than being silently fixed.

Transport is loopback-only, bypasses HTTP proxies, and records every observable
request/answer/usage; separate hidden-thinking fields and irrelevant token-context
arrays are omitted. No external evaluator result is sent to a model or used by END.
External task expectations stay in the offline evaluator.

The fixed runtime guard projects total duration after the first completed FULL_END
and before later runs. It uses observed FULL_END average and DIRECT average (900s
timeout upper bound until a DIRECT completes). Projection over six hours stops the
pilot. The model's per-request timeout remains 900s; no outcome-based prompt tuning.

REPORT.md/summary.json/results.csv are derived pilot-only observations. All eight
FULL_END trajectories must be read manually and reviewed in MANUAL_REVIEW.md.
Alpha is historical context and is never rescored. Higher scores do not alone
demonstrate correct mechanisms or superiority.
