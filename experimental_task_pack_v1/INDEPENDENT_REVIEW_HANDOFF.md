# Independent review handoff

**INDEPENDENT_REVIEW_STATUS=PENDING; no independent approval.** No reviewer is assigned in this task; same-author test/hostile review is not independent validation. Recommended next action A: request review of this draft bundle. Do not implement architectures or run inference before the measurement contracts are sufficiently validated and the experiment separately approved.

Reviewer inputs: [EXP-001](tasks/EXP-001.json), [EXP-002](tasks/EXP-002.json), [scoring contract](SCORING_CONTRACTS.md), [selection rationale](TASK_SELECTION.md), [evaluator](evaluators/evaluator.py), [parser](evaluators/contracts.py), [safety](evaluators/safety.py), all57 fixtures under fixtures/ (candidate content, seven expected dimensions, pass/fail/review, rationale), [validation results](validation/RESULTS.json), [author corrections](validation/CORRECTIONS.md), [budget](BUDGET_FEASIBILITY.md), [preregistration](EXPERIMENT_PREREGISTRATION.md) and draft hash manifest. This handoff intentionally includes private evaluation material for a human/review process, not for model task prompts.

Tasks: EXP-001 produces three exact museum label records while preserving opaque identities/order and a flag-based explanation. EXP-002 repairs three faulty rows in an eight-row normative telemetry table, preserving unaffected features/decisions and diagnosing original-input faults. Refer to full public JSON statements/data/contracts above; no broken-input row is labelled model C0. Known-good answers are fixtures01; alternate whole fences fixtures02; task2 alternative permutation fixture27. Primary task content is six/eight atomic checks, no cross-dimension weighted score. Overall pass requires all applicable requirements plus no detected safety/reference violation or indeterminacy.

Please independently adjudicate:

1. Are these substantively fresh rather than Alpha rewordings?
2. Is EXP-002 difficulty/repair headroom meaningful, while avoiding forced defective C0? Would both tasks be ceiling-limited for the intended model?
3. Do preservation checks detect actual unnecessary regressions, not harmless equivalent JSON?
4. Does repair score distinguish identifying a fault from repairing it and preserve all correct content?
5. Does the pair favor A/B/C beyond their intended hypothesis coverage? Is identical evidence/tool availability sufficient?
6. Are permitted equivalent correct answers all accepted? Is structured explanation unnecessarily restrictive?
7. Do any exact-field checks impose superficial hidden wording rather than genuine task requirements?
8. Are negation, attribution, conditional, contradiction, evidence-ID and executed-check controls sensible?
9. Which ambiguous semantic cases must stay unscored/review-required, and are any claimed determinate cases actually ambiguous?
10. Is staged budget/control fairness adequate, including three-cycle cap, shared36-call outer limit, rare truncation and incomplete/missing data?

Explicit assumptions: public rules are normative for synthetic artifacts; no independent observations/executed receipt exists; four observations/condition in full target cannot demonstrate statistical superiority; pending no-review results are local consistency only. Risks: optional-prose overreview, authority paraphrase misses, claimed attribution truth unknown, whole-answer parse refusal, unknown actual C0 difficulty/model caps/server load and repository-access contamination.

Submit each disagreement through validation/REVIEW_FEEDBACK.csv: task_id, evaluator_or_fixture_id, issue_description, original_expectation, proposed_correction, supporting_reasoning, resolution_status, reviewer_identity. Corresponding JSON status file records no current feedback. Do not automatically accept reviewer assertions: verify against public contract/finite rule evidence, preserve disputed original, record resolution or UNRESOLVED. Any accepted correction creates a new draft version/hash and retests; final immutable freeze requires a future separately authorized step after independent review. Never silently patch evaluator after model outputs exist.
