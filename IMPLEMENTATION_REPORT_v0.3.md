# END Engine v0.3 implementation report

v0.3 incrementally adds the Trajectory Quality Gate and Adversarial Judge to the
existing engine. README, both implementation reports, all package/test modules,
schema-1.0 and schema-2.0 records, provider recording, verifier separation, and
both demos were inspected. The full **75-test baseline passed before editing**.
No AGENTS.md was present. The v0.2 report is preserved in
IMPLEMENTATION_REPORT_v0.2.md; the older report and historical trajectories remain intact.

## Architecture changes

- Explicit JudgeProvider and ModelJudgeProvider, with primary, optional secondary,
  and adversarial roles recorded separately from generator calls.
- Structured Judgment: dimension score/confidence, verdict, fatal/major/minor issues,
  uncertainties, evidence references and recommended action.
- Blinded candidate judging and anonymous A/B pairwise comparison; no iteration,
  lineage, verifier score or success label is sent to candidate judges.
- Adversarial review, deterministic TrajectoryJudge, claim validation, weakness
  resolution audit, assumption audit, and heuristic VerifierGamingDetector.
- Adversarial test descriptions with honest execution status, and an explicit
  ToolVerifier callback hook for scoped EXECUTED_EVIDENCE.
- QualityGate outcomes REJECT, REVISE, BLOCKED, ACCEPT_PROVISIONALLY and ACCEPT_VERIFIED.
  Fatal issues, contradicted important claims and severe regression cannot be averaged away.
- Judge disputes are retained without averaging. Confidence is distinct from score
  and is not presented as statistical calibration.
- RevisionComparator stores preferences, dimension deltas and regression classifications.
  Added complexity without benefit counts as regression.
- Best/latest candidate tracking, rollback and candidate-state restoration. Failed
  candidates, judgments, knowledge events and transition labels remain recorded.
- Judge feedback becomes structured weaknesses/operator targets. Judges never rewrite answers.
- Complete trajectory labels, transition labels, final scorecard, and recovery annotations.

No live API, paid dependency, model training, dataset exporter, Harness-Zero,
self-modification, autonomous deployment or arbitrary generated-code execution was added.

## Created files

| Directory | Files |
| --- | --- |
| end_engine/quality/ | __init__.py, state.py, schema.py, providers.py, judges.py, comparison.py, audits.py, gate.py, mock.py, session.py |
| end_engine/verification/ | tool_verifier.py |
| end_engine/models/ | deployment_mock.py |
| end_engine/ | demo_v03.py |
| tests/ | test_quality.py |
| Root | IMPLEMENTATION_REPORT_v0.2.md |
| Artifacts | demo_v03_output/, demo_v03_compat_v01/, demo_v03_compat_v02/ |

## Modified files

| Directory | Files |
| --- | --- |
| Root | README.md, IMPLEMENTATION_REPORT.md, pyproject.toml, run-demo.ps1 |
| end_engine/ | __init__.py, config.py, engine.py |
| end_engine/core/ | state.py, weaknesses.py |
| end_engine/cognition/ | knowledge.py |
| end_engine/verification/ | __init__.py |
| end_engine/experience/ | schema.py, serializer.py |

The original 75 tests and the v0.1/v0.2 demo modules were not changed.

## Schema and compatibility

Strict evaluation is enabled by a primary judge_provider or
EngineConfig(quality_evaluation=True). Strict runs use schema **3.0**.

Schema 3.0 adds judgments, adversarial judgments, pairwise comparisons, quality
deltas, gate decisions, fatal issues, disputes, claim validations, resolution and
assumption audits, adversarial tests, evidence provenance, rollback events,
best/latest pointers, acceptance labels, transition labels and the final scorecard.
The loader accepts 1.0, 2.0 and 3.0 and returns historical records unchanged.

Existing unconfigured runs preserve the v0.2 API, schema 2.0 and stop reasons.
They explicitly report an unjudged scorecard, quality_gate=BLOCKED and
acceptance_label=INCONCLUSIVE (INCOMPLETE on error). This opt-in strict path preserves
the existing test/API contract without silently treating old self-verification as
independent acceptance. A legacy QUALITY_THRESHOLD_REACHED is not verified acceptance.

After rollback, top-level knowledge/weakness registers describe the returned candidate.
All discoveries and transitions from rejected revisions remain in ordered events.
Candidate, claim, assumption and weakness IDs are not reused after restoration.

## Test results and commands

Final suite: **115 passed, 0 failures, 0 errors** — the original 75 plus **40 new tests**.

The new tests cover all 30 requested categories: separate providers, structured
judgments, adversarial/fatal gating, disputes, confidence, scoped claim evidence,
resolution/assumption audits, execution status/provenance, pairwise preference,
quality delta, rollback/best/latest preservation, all acceptance outcomes, judge
feedback/targeting, anti-gaming, labels, three schema versions, state reset and
legacy demo compatibility. Extra cases cover false fatal flags, unknown evidence
references, model-claimed simulation, identity reuse after rollback, complexity-only
regression, fatal revisions mislabeled as good, and explicit successful recovery.

Executed full-suite command from E:\The End Engine:

    & 'C:\Users\imran\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests

Portable equivalent:

    python -m unittest discover -s tests -v

Executed all demos:

    .\run-demo.ps1 -OutputDir demo_v03_compat_v01
    .\run-demo.ps1 -V02 -OutputDir demo_v03_compat_v02
    .\run-demo.ps1 -V03

Portable v0.3 command:

    python -m end_engine.demo_v03

All three final pretty JSON files were independently loaded and compared for exact
equality with their UUID JSONL records. Every demo completed without run errors.

## v0.3 demonstration

Task: design a deployment controller that automatically rolls out a new service
version while preventing a faulty release from causing a large-scale outage.

The fixture generator supplies five proposals, including one deliberately regressing
revision. The ordinary utility policy selects ASSUMPTION, WHAT_BREAKS, EVIDENCE and
ALTERNATIVE from judged cognitive state; no operator schedule is installed.

| Candidate | Verifier / independent quality result |
| --- | --- |
| C0 | Single-probe rollout; quality gate REVISE |
| C1 | Bounded canary but incomplete recovery; quality gate REVISE |
| C2 | Apparently high verifier score 0.97; adversarial judge identifies premature retirement of healthy capacity and stale-completion/retry races; gate REVISE |
| C3 | Retains healthy pool through rollback, fences by epoch and serializes promotion/recovery; passes recorded abstract model checks; gate ACCEPT_VERIFIED |
| C4 | Clearer wording removes recovery invariants; verifier remains optimistic at 0.99, but adversarial judgment and failed checks reject it |

C3 and C4 are compared without position/score labels. Correctness, robustness and
constraint-adherence deltas are -0.50 for C4; clarity improves +0.12. The comparison
prefers C3 and classifies C4 as SEVERE_REGRESSION.

Recorded rollback:

    from_candidate: C4
    to_candidate: C3
    reason: B removes retained healthy capacity and epoch fencing

Final best_candidate_id=C3; latest_candidate_id=C4; final_candidate_id=C3.
The returned answer is exactly C3. C4 remains in candidate history with its failed
evidence, fatal finding, comparison and BAD_REVISION label.

Final gate: **ACCEPT_VERIFIED**.
Final stop reason: **ACCEPTED_VERIFIED**.
Trajectory label: **ACCEPTED_HIGH_CONFIDENCE**.

This acceptance is limited to recorded scope: the demo actually runs a small
abstract state machine across six orderings of retry, stale completion and rollback
completion. Model judgments are deterministic fixtures. The demo does not deploy
software, execute generated source, or establish production-wide safety.

The optional post_acceptance_cycles=1 is explicitly used to probe C4 after C3 passes.
It is off by default and remains within cycle/operation limits.

## Saved artifacts

Final v0.3 trajectory: cc1aff25-9b25-420d-831f-1fa13c5e9f0f.

- demo_v03_output/demo_trace.txt: full quality/rollback trace.
- demo_v03_output/cognitive_trace.txt: underlying cognitive operations.
- demo_v03_output/demo_trajectory.json: complete pretty JSON.
- demo_v03_output/cc1aff25-9b25-420d-831f-1fa13c5e9f0f.jsonl: complete single-record JSONL.
- demo_v03_output/demo_console.txt: complete console output.

Compatibility runs:

- v0.1: 92d715dd-f1b1-4c75-84c5-a3e0085eec56; 3 candidates; original quality-threshold stop.
- v0.2: 7007d0f3-0df9-46d2-a338-e07cda9bea6e; 6 candidates; original quality-threshold stop.

Compatibility results remain explicitly unjudged, not accepted by the v0.3 gate.
Earlier development records are retained; stable demo_trace.txt/demo_trajectory.json
paths identify the final runs.

## Known limitations

- Mock judgments and estimated quality deltas are not empirical model-quality benchmarks.
- ACCEPT_VERIFIED is scoped to attached checks, not universal correctness or production safety.
- Audit and gaming checks are conservative lexical/structural heuristics and can miss semantic issues or produce false positives.
- Different metadata identities do not prove genuine independence; same-model judging remains correlated.
- Evidence callbacks are trusted code and must report what actually ran. The core does not sandbox arbitrary caller callbacks.
- Blinding hides status/position metadata but cannot remove identifying clues inside candidate text.
- Judge work is bounded by candidate count; there is no separate token, cost or wall-clock cancellation budget.
- Final atomic storage is not a crash-resume journal. One engine instance is intended for sequential runs.
- Legacy mode remains available but grants no independent quality acceptance.
