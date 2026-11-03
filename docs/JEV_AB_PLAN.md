# Jev-assisted operator routing A/B — plan only

Status: **not executed**. Live inference, Benchmark Beta, Beta-Gemini, Alpha replay
and Jev A/B execution require separate authorization. Do not alter historical
benchmark records or tune routing against their recorded answers.

## One variable

Control: current END operator selection with DecisionConfig(provider="baseline").
Experiment: identical END settings and **operator-routing-only** Jev advice.

Hold fixed the task/prompt pack, generator model/version/settings, primary and
adversarial judge configuration, verifier/tool checks, output mode, protocol repair
limit, cycle/branch/cognitive limits, run call ceiling, seeds and external evaluation.
No escalation, revision-needed or evidence-relevance integration is enabled.
Pin Jev's exact model and SDK; record requested and resolved models for every result.

Proposed shared ceiling: 128 provider/tool slots in each arm, max four decision calls
inside that same ceiling in the experiment. The control has no decision calls; the
experiment's decisions reduce the slots remaining for other work. Equal ceilings
do not imply equal realized cost, latency, token use or generative-call allocation.
Those differences are measured rather than hidden.

## Stages, after authorization

1. One-request transport smoke using public synthetic projected state and mock
   reasoning. Check typed response, model pin, usage, deadline, trace and redaction.
2. Small paired pilot: two independently selected tasks, two seeds/trials per arm,
   randomized paired order. Pre-register operator constraints/thresholds and all
   external success criteria before inference. Use no recorded Alpha answer to steer
   either arm. Record run manifests and immutable source/task/config fingerprints.
3. Only if the transport/invariants hold, propose a larger paired task pack and cost
   cap for approval. Do not silently expand the pilot.

Maximum pilot operations under the proposed eight runs ×128 shared slots: 1,024
slots, including at most sixteen Jev decisions (four experimental runs ×four).
This is a request bound, not a monetary estimate. Price/provider availability and
cost authorization must be checked at the time of a live run.

## Measures

- External final-task quality and deterministic verifier outcomes; internal judge
  agreement is not ground truth.
- Unsupported-claim rate, scoped verified/provisional labels and false acceptance.
- Cycles, generative/judge/verifier/decision calls and total model/operation counts.
- Operator/family distribution, same-target repetition and information-gain levels.
- Latency, actual token usage, and monetary cost only where pricing and usage are
  known. Unknown values remain unknown.
- Decision fallback, rejection, unavailability and budget-exhaustion rates.
- Routing false positives/negatives adjudicated against pre-registered useful
  operations or blinded external review; do not infer ground truth from Jev's own
  probability/confidence.
- Pairwise task quality, regression/rollback outcomes and variance across seeds.

Include confidently wrong/forbidden advice, missing SDK/key, rate limits, timeouts,
exhausted global budget, required revision despite optimistic advice, and model
consensus without evidence. Preserve failures rather than repairing benchmark data.
Use offline scripted stress cases before deciding to spend live inference on them.

No claim of better reasoning, lower cost, better accuracy, superior routing or
improved verification is supported by this implementation alone.
