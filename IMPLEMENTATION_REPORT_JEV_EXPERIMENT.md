# Experimental Jev decision-provider integration — offline implementation

Date: 2026-10-04. Package version remains **0.3.5**. Proposed next release:
**0.3.6 experimental**, subject to review and explicit publication/version approval.
No commit, push, release, tag, dependency installation or live experiment was performed.
The existing current implementation report and all historical reports are unchanged.

## Current architecture found

END already has frozen candidate lineage, CognitiveState, seven operator families,
utility selection, persistent weaknesses/claims/assumptions, bounded branches,
revision planning, verifiers, independent/adversarial judging, grounding, evidence
integrity, quality gates, best-candidate restoration/final reconciliation, schema
2.0/3.0 ledger records, and v0.3.5 structured protocol repair/native output options.
It has cognitive-operation budgets but no shared provider/tool call ceiling.
Its small component interfaces and run-local trajectory recorder are reusable.
There is no general full-run replay API in the core; benchmark/replay scripts are
separate research code and were inspected but not executed.

The initial Git tree was already dirty from existing v0.3.5 development and completed
research work. Its commit was `6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7`, on main.
That state was recorded before edits in `validation_jev/git-status-before.txt`.

| Baseline | Value |
| --- | --- |
| Engine version | 0.3.5 |
| Python | 3.12.14 |
| Source fingerprint | `520d2052832eaee93f7c8931e028762c7008006ae61f2fdc7ec6589d7e4bd448` |
| Fingerprint scope | end_engine/**/*.py + pyproject.toml, 55 files |
| Offline Engine suite | 182 passed; 0 failures; 0 errors |
| TypeSafe SDK | Absent |

## Integration design and first target

Operator routing is the first target because it already has an explicit baseline,
registered options, utility/repetition signals and a replaceable selector boundary.
It can accept bounded advice without changing claims, verification, judgment,
termination, rollback, evidence integrity or user-side-effect authorization.

The Engine first computes its baseline selection. DecisionRoutingSession filters
available operators, END constraints, repetition and acceptable utility loss,
then asks one atomic question choosing an offered family. It validates the answer
again, applies native choice probability/confidence thresholds, and chooses the best
eligible operator inside that family. The provider cannot execute an action.
Mandatory operators and explicit existing custom policies skip consultation.
Single-family states also skip the unnecessary call.

Only this category is wired. Escalation, revision-needed and evidence-relevance
signals are deferred. Binary and score normalization are available for future
narrow applications, not attached to quality or termination decisions.

## New types/interfaces and TypeSafe adapter

- DecisionProvider, DeterministicDecisionProvider, ScriptedDecisionProvider and ReplayDecisionProvider.
- DecisionRequest/DecisionResult/DecisionProvenance, ChoiceDecision, BinaryDecision, ScoreDecision and DecisionStatus.
- DecisionConfig, DecisionContextBuilder, DecisionRoutingSession and RoutingConstraints.
- RunCallBudget/RunBudgetExceeded for a shared, optional ceiling.

The official SDK interface was checked against:

- [Official Python SDK](https://docs.typesafe.ai/sdk/python)
- [Client signature, timeouts and retry controls](https://docs.typesafe.ai/sdk/python/api/clients/sync)
- [Answer/native fields and request IDs](https://docs.typesafe.ai/sdk/python/api/types/responses)
- [Exception taxonomy](https://docs.typesafe.ai/sdk/python/api/exceptions)
- [Pinned-model semantics](https://docs.typesafe.ai/models)
- [Official SDK source: version 0.7.2](https://github.com/typesafe-ai/typesafe-sdk-python/blob/main/pyproject.toml)
- [Official interactive API documentation](https://api.typesafe.ai/docs)

The adapter lazy-loads typesafe_sdk, constructs one typed question, and calls
TypeSafeClient.system_one with an explicit model, finite timeout and zero SDK
retries. Construction/preflight does not list models, warm up or infer. It retains
requested/resolved model, request ID, latency and usage if returned. Exact pins or
explicit aliases are caller-configured; the Engine contains no moving model alias.

Choice preserves its distribution and choice confidence. Binary preserves native
noul_probability and explicitly maps >=0.5 to its yes flag. Score preserves the
expected ordered score, rubric, distribution and score confidence. No shared
universal confidence is fabricated or claimed to be mathematically equivalent.

SDK objects, headers and bodies stay outside the core. Credentials come only from
the environment. Exception messages and credentials are not retained. Normalized
labels/context are defensively redacted if they reflect known credential values.

## Minimal context, budgets, failure and fallback

Projection includes at most eight short issue descriptions and IDs, actual family
options, bounded utility/repetition indicators, six recent family labels and
remaining budgets. It excludes task text, full candidate/history, claim/evidence
blobs, conversation, provider metadata and unrelated trajectory events.

All Engine-managed model calls (including protocol repairs), decision calls,
non-LLM verifier operations and tool callbacks draw from max_run_calls. Enabled
decision runs have a finite default global ceiling of 128 unless configured.
Disabled legacy runs gain no new ceiling by default. A max-four decision sub-budget
adds no extra calls. Four slots are retained for the ordinary revision path before
consultation; further judge work still uses the global ceiling.

Missing model/key/SDK is local unavailability with no inference reservation. Timeout,
connection, rate limit, HTTP/authentication failure, unknown model and malformed
results are explicit failures. Failed attempted calls consume a slot conservatively;
local unavailable checks do not. No failure becomes a positive signal. Unknown,
forbidden, low-certainty, late or policy-invalid advice falls back to the existing
selector result. A broken unrelated import is not mislabeled as missing SDK; the
adapter raises it and the routing boundary records an explicit error/fallback.

## Replay, trace and provenance

Enabled runs add optional decisions, decision_summary and run_call_budget fields to
existing schemas; old records load unchanged. Events include requested, completed,
ignored, rejected, fallback, error and budget-exhausted decision interactions.
They retain projected input/question/options, semantic fingerprint, native answer,
model pin/resolution, usage, latency, availability/error, thresholds, END rule,
disposition, selected/fallback operator and consumed budget. Consulted decisions
also appear in model_calls with method evaluate_decision and MODEL_JUDGMENT provenance.

Replay consumes recorded normalized decisions by exact semantic fingerprint,
retains historical native provenance and marks replayed=True. It has no live
fallback transport. Missing or mismatched records explicitly fall back rather than
inventing historical decisions. Zero-cost unavailable decisions keep their original
reservation semantics. Replay usage is historical, not newly consumed tokens.
This is decision replay; other model/provider inputs need their own replay or mocks
for full-run deterministic reproduction.

## Safety and verification invariants

**Jev judgments are model-generated decision signals. They are not independent
evidence and do not satisfy END Engine verification requirements by themselves.**

The J1–J8 tests cover an UNVERIFIED claim despite a supported=0.99 decision,
failed verifier retention, mandatory revision, exhausted budget, forbidden
operator rejection at extremely high probability, generator/judge/Jev agreement
without evidence, outage fallback and distinct primitive confidence semantics.
Decision results have no API for claim verification, gate acceptance, side-effect
authorization or policy mutation. Verification/grounding/integrity rules were not
relaxed. QualitySession was touched only to charge configured tool callbacks to
the same optional run budget.

## Files changed by this task

| Kind | Files |
| --- | --- |
| New decision package | end_engine/decisions/__init__.py, config.py, types.py, context.py, providers.py, jev.py, routing.py, demo.py |
| New shared budget | end_engine/models/budget.py |
| Modified core boundary | end_engine/config.py, engine.py, experience/schema.py, models/recording.py, quality/session.py |
| Packaging/docs | pyproject.toml optional jev extra; README.md experimental pointer; docs/JEV_EXPERIMENT.md; docs/JEV_AB_PLAN.md; this report |
| Tests/validation | tests/test_decisions.py; validation_jev/ baseline/status/fingerprint/immutability records, socket-blocked runner, final results and offline demo |

The earlier uncommitted user changes were preserved. **All 1,800 hashed research
and prior validation files remain byte-identical**, including Alpha/Beta/Beta-Gemini
records. No separate Harness files were changed.

## Configuration and optional dependency behavior

DecisionConfig(provider="baseline") is the default. Jev requires opt-in provider
configuration and an explicit requested model. categories currently permits only
operator_routing. Timeouts, native thresholds, utility/repetition guards, decision
call/latency limits and the global call ceiling are configurable.

Normal dependencies remain empty. `.[jev]` installs pinned typesafe-sdk==0.7.2 only
if requested later. This task installed nothing. END imports and operates with no
SDK and no TYPESAFE_API_KEY; missing prerequisites yield fallback when enabled.

## Tests and final identity

| Validation | Result |
| --- | --- |
| Baseline before | 182 passed, 0 failures/errors |
| New decision/Jev tests | 44 passed |
| Final full Engine suite | **226 passed, 0 failures/errors** |
| Runtime network sentinel | **0 attempted connections** |
| SDK installed/imported in final suite | false / false |
| Syntax | Changed/new Python files parsed with standard-library AST |
| Existing lint/type tooling | None configured; no new checker installed or claimed |
| Secret signature scan | No matching credential/private-key signatures in changed files |

Development-only test issues (test syntax, decision collection initialization and
timestamp comparison) were corrected. No baseline failure remained or was hidden.

Commands executed with the bundled Python 3.12.14 and PYTHONDONTWRITEBYTECODE=1:

    python -m unittest discover -s tests -t .
    python -m unittest tests.test_decisions
    python -B validation_jev/run_offline.py
    python -m end_engine.decisions.demo --output-dir validation_jev/demo

The actual executable was:
`C:\Users\imran\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

Final source fingerprint:
`7c9ce8d2b892b70cdecce93b40c3310269d603c59101757f32983dde96a0947b`
(64 files, same fingerprint algorithm/scope). Package version remains 0.3.5.

Offline demo: one deterministic advisory decision + six mock model calls = seven
of eight shared slots. The legacy quality gate stays BLOCKED, illustrating that
decision agreement creates no verification. Complete trace is in
validation_jev/demo/decision_demo.json, with final run UUID
`a8be4a2c-ca51-48c5-b32c-778ef34a6e9a`.

## Live calls, network calls, benchmark and next experiment

### Live smoke status — 2026-10-05

**Live Jev smoke: NOT EXECUTED.** The user reports that the TypeSafe organization
has **zero available credits**, so **API-key creation is unavailable**. This is an
**external provider-account blocker for live testing only**.

- **Live requests made: 0. No inference consumed.**
- The offline implementation remains validated: **226 Engine tests, including 44
  decision/Jev tests, passed**. The separately authorized installation completed;
  SDK **0.7.2** imported successfully and the offline suite passed with it installed.
- **Live transport compatibility is NOT VALIDATED; no claim of it may be made.**
  No live result, resolved model, request ID, latency or usage is available.
- The prepared one-request smoke command remains in `docs/JEV_EXPERIMENT.md` for
  future use if credits and an environment credential become available.
- No credits were purchased, other provider attempted, credential requirement
  bypassed, Engine behavior changed, version bumped, commit/push/publication made,
  or benchmark executed because of this blocker.

Structured status: `validation_jev/live-smoke-status.json`. The smoke preflight in
`trajectories/jev_smoke/preflight.json` records the updated blocker while preserving
its earlier missing-credential status. Existing offline validation remains historical.

The implementation-stage records below remain unchanged in meaning; the subsequent
SDK installation does not establish live service compatibility. No automatic retry
or live continuation is scheduled.

**LIVE MODEL CALLS: 0.**

**NETWORK CALLS (Engine/runtime/tests): 0.** The brief also required current official
documentation inspection, which used **five read-only web-tool lookup calls**.
Thus zero runtime/inference traffic is verified; zero traffic including documentation
retrieval cannot honestly be claimed. No TypeSafe inference-endpoint, model-listing
or authenticated request was made.

**BENCHMARK: plan only, not executed.** docs/JEV_AB_PLAN.md isolates operator routing,
holds generator/judges/verifiers/tasks/settings/budgets fixed, measures independent
quality, unsupported claims, calls/cost/latency/repetition/fallbacks, and includes
confidently wrong advice. No Beta, Gemini, Alpha replay or Jev A/B run was launched.

Recommended first live experiment, only after separate authorization: one request
on public synthetic projected state using the prepared demo's --allow-live flag,
an explicit exact model pin and max_calls_per_run=1. The reasoning provider remains
mocked. Validate transport/trace/redaction first, then request authorization for
the small paired routing-only pilot. The command is documented but was not run.

## Open questions and risks

- The actual installed SDK/service was not exercised; tests use a faithful in-memory
  transport contract checked against current official sources.
- Utility thresholds, certainty thresholds and global limits are experimental;
  no empirical benefit, lower cost or improved routing is established.
- HTTP deadlines/elapsed checks cannot forcibly cancel an arbitrary blocked custom
  synchronous provider. SDK retries are disabled, but other transports must account
  for their own private retries honestly.
- Projection descriptions may still contain sensitive task information unrelated to
  known credential patterns. Users must review the projected data before live use.
- Native probabilities/confidence remain model reports and never constitute proof.
- The shared counter measures controlled call reservations, not token spending or
  every internal I/O operation in arbitrary trusted extensions.
- Full-run replay requires deterministic/replayed nondecision providers as well;
  this patch deliberately does not redesign the generative replay architecture.
