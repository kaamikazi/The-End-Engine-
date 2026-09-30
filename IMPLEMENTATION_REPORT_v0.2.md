# END Engine v0.2 implementation report

The existing repository, README, implementation report, schemas, engine, operators,
tests and demo were inspected before editing. All **39 baseline tests passed**.
No AGENTS.md was present. Development was incremental; candidate lineage, provider
recording, existing verifier interfaces, error preservation and atomic storage were
retained. The original report is preserved in IMPLEMENTATION_REPORT_v0.1.md.

## Architecture delivered

- Introspectable metadata for 17 operators in seven families.
- Immutable CognitiveState and concrete questions with explicit target type/ID,
  expected information, intent, and parent event.
- Replaceable utility policy with relevance, expected information gain, issue
  value, novelty, importance, repetition/cost penalties, and meta-priority factors.
- Run-local operator/family outcome memory, lexical finding deduplication, and
  target/intent-aware repetition control.
- Bounded claim extraction and explicit claim/assumption status transitions.
- Separate scrutiny coverage and provisional verifier-derived resolved dimensions.
- Bounded branch creation, dimensional evaluation, retained rejected hypotheses,
  multi-source synthesis, and normal revision planning that consumes synthesis.
- Shared operation budget, active-count/per-operator limits, and depth/ancestry checks.
- Sparse meta-checks and bounded advisory reframing that preserves the original task.
- Critical termination guards for missing major scrutiny, evidence gaps, severe
  assumptions, active branches, diminishing information gain, and budget exhaustion.
- Offline fixtures and full trace/trajectory demonstrations.

No training, Harness-Zero, learned cross-run policy, self-modification, deployment,
UI, live API dependency, embeddings, or vector database was added.

## Files created

| Directory | Files |
| --- | --- |
| end_engine/cognition/ | __init__.py, state.py, knowledge.py, questions.py, policy.py, session.py, deduplication.py, branches.py |
| end_engine/operators/ | metadata.py |
| end_engine/models/ | production_mock.py |
| end_engine/ | demo_v02.py |
| tests/ | test_cognitive_brain.py |
| Root | IMPLEMENTATION_REPORT_v0.1.md |
| Artifacts | demo_v02_output/ and demo_v01_compat_output/ traces, JSON, JSONL and console records |

## Files modified

| Directory | Files |
| --- | --- |
| Root | README.md, IMPLEMENTATION_REPORT.md, pyproject.toml, run-demo.ps1 |
| end_engine/ | __init__.py, config.py, engine.py |
| end_engine/core/ | state.py, question_selector.py, weaknesses.py, revision_planner.py, termination.py |
| end_engine/operators/ | __init__.py, base.py |
| end_engine/models/ | schema.py, mock.py |
| end_engine/experience/ | schema.py, serializer.py |

The original 39 tests and original demo module were not edited.

## Schema and backward compatibility

New records use schema **2.0**, retaining the v0.1 fields and adding cognitive
states, utility rankings, questions/targets, claims, assumptions, outcomes/statistics,
branches/evaluations, synthesis, coverage, meta-checks, and reframings.
New critique fields are optional, preserving existing structured provider responses.
Weaknesses gain optional target identity; SelectionContext gains cognitive state.

The loader accepts 1.0 and 2.0 and preserves loaded objects unchanged. There is no
destructive migration or automatic insertion of v0.2 fields into v0.1 records.
The historical schema-1.0 memory demo is retained as a compatibility fixture.
Legacy selectors and termination controllers remain usable. Custom planners using
branch/reframing features accept optional synthesis and reframing keyword arguments.

## Tests and exact commands

Final result: **75 tests passed, 0 failures, 0 errors** — the original 39 plus
**36 new tests**. New tests cover all 25 requested categories, plus malformed branch
batches, synthesis failure cleanup, disallowed branch adoption, generic mock
branching, and preventing repeated duplicates from manufacturing HIGH coverage.

Exact test command executed in PowerShell from E:\The End Engine:

    & 'C:\Users\imran\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests

Portable commands with Python 3.11+ on PATH:

    python -m unittest discover -s tests -v
    python -m end_engine.demo
    python -m end_engine.demo_v02

Both demos were executed successfully:

    .\run-demo.ps1 -OutputDir demo_v01_compat_output
    .\run-demo.ps1 -V02

The saved v0.2 pretty JSON was independently loaded and compared for exact equality
with its JSONL record. The sequence, utility factors, questions, knowledge transitions,
dimensional branch evaluations, synthesis, coverage, reframing, termination, and
empty errors collection were inspected.

## Demonstration result

The task is to design an autonomous production-code modification agent that
minimizes regression risk. The fixture supplies operator-dependent responses;
the normal utility policy selects the sequence without an installed schedule.

| Investigation | Target and result |
| --- | --- |
| ASSUMPTION | A001: invalidates the premise that green tests adequately represent production behavior; discovers W001 |
| WHAT_BREAKS | W001: maps concrete failures, discovers workflow uncertainty W002, records rollback assumption A002, proposes reframing |
| ALTERNATIVE | W002: creates competing workflows and identifies downstream incentive issue W003 |
| Branch evaluation | B1 direct editing REJECTED; B2 isolated worktree and B3 staged/shadow validation PROMISING |
| Synthesis | Combines B2 isolation/review with B3 shadow scenarios, holdouts, canary and rollback checks; both MERGED |
| SECOND_ORDER_EFFECT | W003: addresses test gaming, invalidates unconditional rollback, identifies acceptance-check gap W004 |
| VERIFY | W004: specifies auditable acceptance checks and records support for the proposal's review requirement |

The run produces **6 candidates, 5 investigations, 3 branches, 27 model calls, and
8 shared cognitive-operation units**. Synthetic scores:
**0.53 → 0.62 → 0.71 → 0.80 → 0.89 → 0.98**.

Termination: **QUALITY_THRESHOLD_REACHED**, CRITICAL mode, after five revisions.
No open severe weaknesses, severe untested assumptions, active evidence gaps, or
missing major scrutiny dimensions remain. Presentation-only clarity/completeness
coverage remains NONE.

Final trajectory ID: 966fc233-7d0e-4c68-85f9-15b424858d80.
Artifacts: demo_v02_output/demo_trace.txt, demo_trajectory.json, demo_console.txt,
and 966fc233-7d0e-4c68-85f9-15b424858d80.jsonl in that directory.

Compatibility demo: two revisions, synthetic score 0.94, QUALITY_THRESHOLD_REACHED;
trajectory f140ac76-3152-4345-b793-47be68693746 in demo_v01_compat_output/.

Earlier development JSONL records remain available. The stable demo_trace.txt and
demo_trajectory.json paths identify the final run.

## Known limitations

- Mock scores/evidence are synthetic judgments, not empirical reasoning improvement
  or executed production checks.
- Utility, information gain, and coverage are transparent heuristics rather than
  calibrated estimates or learned policies.
- Claim extraction, question generation, and finding similarity are lexical/template
  based; implicit claims and semantic duplicates can be missed.
- The default engine explores one flat branch batch per run. Nested depth/ancestry
  is supported and checked by the controller, but no recursive search policy is installed.
- The latest main candidate is returned without automatic rollback of regressions.
- Budgets bound cycles, operations and branches, not tokens or wall-clock time.
  Real adapters need finite transport timeouts.
- Atomic final storage is not a crash-resume journal. Default cognitive state resets
  per run; one engine instance is intended for sequential use.
- Custom components are trusted extension code. Their private I/O is not automatically
  observable; custom termination policies can replace cognitive guards while remaining
  subject to engine cycle/operation ceilings.
