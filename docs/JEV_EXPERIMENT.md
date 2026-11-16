# Experimental decision-model routing

Status: **optional, disabled by default, offline validated only**. Engine package
version remains 0.3.5. A future experimental 0.3.6 release is proposed in the report;
it has not been committed, published or empirically evaluated.

**Jev judgments are model-generated decision signals. They are not independent
evidence and do not satisfy END Engine verification requirements by themselves.**

## Boundary

The existing Engine continues to own analysis, cognition, revision, verification,
grounding, integrity, quality gates, budgets, termination and rollback. Only the
operator-family choice has an advisory integration. Escalation, revision-needed
and evidence-relevance integrations are intentionally deferred.

The adapter is behind `DecisionProvider`. END owns `DecisionRequest`, `DecisionResult`,
`ChoiceDecision`, `BinaryDecision` and `ScoreDecision`. No TypeSafe SDK object enters
the Engine. Choice retains choice probabilities and choice confidence; binary
retains the native yes-probability and an explicitly defined `>= 0.5` yes flag;
score retains expected ordered score, level probabilities, legend and score confidence.
There is no universal confidence or cross-primitive equivalence.

## Configuration

```python
from end_engine import EndEngine, EngineConfig
from end_engine.decisions import DecisionConfig

baseline = EndEngine()  # No decision SDK import, decision calls or changed routing.

config = EngineConfig(
    max_run_calls=128,
    decision=DecisionConfig(
        provider="jev",
        requested_model="jev-1.13.0",  # Example exact pin reviewed on 2026-10-04.
        max_calls_per_run=4,
        timeout_seconds=5,
        max_latency_ms=15000,
        min_choice_probability=0.65,
        min_choice_confidence=0.70,
        max_utility_loss=0.25,
        max_repetition_penalty=0.50,
    ),
)
# Configuration only. Do not run a live provider without separate authorization.
```

Use `provider="baseline"` (default), `"scripted"`, `"replay"`, or `"jev"`.
Constructor `decision_provider=` permits a provider-neutral injected implementation;
it does not enable the feature without non-baseline configuration. An explicit
existing selector or selection policy remains authoritative and skips consultation.
`RoutingConstraints` can add END-owned allowed/forbidden operators, mandatory
operator and allowed modes. FAST never reaches routing in the Engine.

## Decision flow

1. The ordinary selector computes its original baseline decision.
2. END filters actual availability, explicit constraints, repetition penalties and
   maximum acceptable utility loss. A sole eligible family needs no model call.
3. `DecisionContextBuilder` projects at most eight issue IDs/categories/severities
   and 160-character descriptions, six recent families, bounded repetition/utility
   indicators, available families and remaining budgets. It sends no task text,
   candidate answer, full claim/evidence blobs, conversation, provider metadata or
   full trajectory. Known credential values/patterns are redacted.
4. One atomic Choice question asks for one **offered family**.
5. END checks identity/type, native values, availability, probability/confidence
   thresholds, repetition, utility, latency, and policy again. It selects the best
   eligible operator within that family. The provider never executes anything.
6. Unknown, forbidden, stale, low-certainty or failed advice falls back to the
   existing baseline choice. Mandatory operations skip consultation entirely.

These routing thresholds are experimental policy thresholds, not claims of
calibrated correctness. They may reduce eligible choices substantially.

## SDK contract and optional installation

Official sources reviewed on 2026-10-04:

- [Python SDK](https://docs.typesafe.ai/sdk/python)
- [Synchronous client and retry/timeout options](https://docs.typesafe.ai/sdk/python/api/clients/sync)
- [Typed answers, native fields and request IDs](https://docs.typesafe.ai/sdk/python/api/types/responses)
- [Models and explicit pinning](https://docs.typesafe.ai/models)
- [Official SDK source/version](https://github.com/typesafe-ai/typesafe-sdk-python/blob/main/pyproject.toml)
- [Swagger API documentation](https://api.typesafe.ai/docs) (interactive page; SDK reference used for the detailed contract)

Optional extra: `typesafe-sdk==0.7.2`, isolated from normal runtime requirements.
No dependency was installed during this task. Future installation, if authorized:

```sh
python -m pip install '.[jev]'
```

`JevDecisionProvider` lazy-loads `typesafe_sdk`; credentials come only from the
`TYPESAFE_API_KEY` environment variable. It calls `TypeSafeClient.system_one`
with one typed question, explicit requested model, finite timeout and
`RetryPolicy(max_retries=0)`. It uses the official API origin; no model-listing,
warmup, discovery or inference request happens during construction/preflight.
Resolved model and request ID are recorded if returned. The adapter never records
credentials, headers, wire bodies or exception messages. Normalized native labels
are defensively redacted if a response reflects a known credential.

Missing model/key/SDK means unavailable and fallback. A missing unrelated SDK
dependency is not mislabeled as `missing_sdk`: the adapter propagates it, and the
routing boundary records an explicit provider error/fallback. Timeout, connection,
HTTP, authentication, rate limit, unknown model and malformed results have distinct
failure states. Errors never become positive binary/choice values.

## Shared budgets

`max_run_calls` is a run-wide ceiling for Engine-managed model attempts, decision
calls, non-LLM verifier operations and configured tool callbacks. Every structured
repair also consumes a slot. Decision-enabled runs use a finite global default of
128 if no explicit ceiling is supplied. Legacy disabled runs retain no new ceiling
unless `max_run_calls` is configured.

`max_calls_per_run` is a **sub-budget** of that same ceiling; it adds no free calls.
Decision routing retains four call slots for the ordinary critique/plan/revision/
verification path before consulting. Judges may need additional slots; the global
ceiling still applies and a depleted run stops as BUDGET_EXHAUSTED. Local unavailability
does not count as inference. Timeout/failed attempted calls count conservatively.
SDK retries are disabled. Other caller-supplied transports must honestly report
their own internal retry activity; the core cannot intercept private I/O.

The latency sub-budget measures routing elapsed time, narrows the next transport
timeout, rejects late signals and prevents later consultations. HTTP transport
timeouts are not a hard process wall-clock kill; a misbehaving custom synchronous
provider cannot be forcibly cancelled by this wrapper.

## Trace, serialization and replay

Existing schema 2.0/3.0 remains compatible. Enabled runs add optional `decisions`,
`decision_summary` and `run_call_budget`; historical records are not migrated.
Events include `decision.requested`, `.completed`, `.ignored`, `.rejected`,
`.fallback`, `.error` and `.budget_exhausted`. Completed records include the exact
projected question/context/options, semantic fingerprint, normalized answer,
requested/resolved models, request ID, native probability fields, usage, latency,
availability/error, disposition, END rule, thresholds, selected/fallback operator
and consumed budget. Decision calls also enter `model_calls` as `evaluate_decision`;
their provenance is always MODEL_JUDGMENT.

```python
from end_engine.decisions import ReplayDecisionProvider

recorded_provider = ReplayDecisionProvider.from_trajectory(saved_trajectory)
# Inject it with decision.provider="replay" and the same semantic inputs/config.
```

Replay matches exact question ID, type, projected context, choices, category and
requested model. It returns recorded normalized answers and original native
provenance, marked `replayed=True`. No live transport exists in the replay provider.
Absent or mismatched records explicitly produce `replay_missing` or
`replay_input_mismatch` and deterministic fallback. Replay preserves whether an
original preflight decision consumed a call slot. Usage attached to replay is
historical usage, not a claim that new tokens were consumed.

This is **decision replay**, not a new complete generative-model replay system.
For a full deterministic reproduction, other providers and inputs must also be
replayed or replaced by deterministic fixtures.

## Validation and future smoke

Offline commands (no API key/SDK/network required):

```sh
python -B validation_jev/run_offline.py
python -m unittest tests.test_decisions -v
python -m end_engine.decisions.demo --output-dir validation_jev/demo
```

The validator blocks runtime socket connections and records attempts, full-suite
results and SDK absence. No lint/type checker is configured in this repository;
the saved syntax validation is standard-library AST parsing, not a substitute for
a configured type checker.

**Prepared only; not executed:** after separate live authorization and optional
installation, set the credential through your secret environment mechanism, then:

**Current live-test blocker (2026-10-05):** the user reports zero TypeSafe account
credits and unavailable API-key creation. The live smoke is **NOT EXECUTED**, with
**0 live requests and no inference consumed**. Offline validation still passes;
live transport compatibility remains unvalidated. The following command is preserved
for future use if credits and the required environment credential become available.

```sh
python -m end_engine.decisions.demo --allow-live --model jev-1.13.0 --output-dir trajectories/jev_smoke
```

This proposed smoke uses a mock reasoning provider and allows at most one TypeSafe
routing request within an eight-slot shared budget. It is a transport/routing
contract check, not a reasoning-quality experiment. The existing quality gate is
never satisfied by this decision alone. See `JEV_AB_PLAN.md` for the separately
authorized routing-only A/B design.
