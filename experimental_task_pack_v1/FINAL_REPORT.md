# END Experimental Task Pack v1 — final preparation report

2026-10-12. **Next action A: REQUEST INDEPENDENT REVIEW.** Review=PENDING; freeze=DRAFT_PENDING_REVIEW; live experiment=NOT EXECUTED. Exactly two fresh tasks and a deterministic external measurement system are prepared. No architecture A/B/C, Engine version/config/prompt change or live request was made.

## Baseline/protection

Engine0.3.5.2, fingerprint `29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82`, Python3.12.14, Git main/HEAD `6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7`. Baseline303 tests passed in19.801s; final303 passed in18.882s, zero failures/errors/skips/network attempts. All4,634 original files outside this pack are byte-identical, including all architecture-review/historical reports/tasks/evaluators/validation. Separate END Harness untouched. Existing dirty Git work retained; no staging/commit/push/publication. [Final audit](validation/FINAL_VALIDATION.json), [sources](validation/SOURCES.json).

## Tasks and measurable outcomes

EXP-001 creates museum loan/handling label text from explicit flags, preserves exact IDs/order/titles, and includes a checkable explanation of triggered rules. Six substantive outputs/four preservation checks identify good answers, wrong handling/prefix, lost explanation, normalization/reordering, extra fields, malformed output and valid equivalents. Correct fixture does not imply perfect future model C0.

EXP-002 repairs eight-row telemetry policy decisions and diagnoses three original faults while preserving five correct decisions and all IDs/features. It distinguishes diagnosis without repair, partial repair, wrong diagnosis/unrelated change, full repair with unaffected damage and valid alternative order. Eight substantive/three repair/37 preservation checks. Supplied defect is TASK_INPUT, not generated C0. A correctly repaired first answer yields no deliberation gain unless its actual later candidate improves it.

[Task selection](TASK_SELECTION.md), [scoring contracts](SCORING_CONTRACTS.md), [public tasks](tasks/EXP-001.json) / [EXP-002](tasks/EXP-002.json). Only public_loader's whitelist goes to a future model; private evaluator/fixtures/known-good answers remain evaluation-side. This is file separation, not robust secrecy against a repository-reading agent.

## Evaluator/fixtures

Rubric `exp-pack-1.0.1-draft`: seven independent dimensions, no cross-dimension weights; mandatory logical success plus distinct safety/citation results. Complete authoritative answer only, no transcript fragment rescue. Malformed substance stays unassessed; missing execution/withholding is separate from incorrect content. Unsupported confirmation/status/execution/scope and closed-task IDs are checked with polarity/source/hypothetical controls; unknown external URLs/strings or unassessed semantics require review. No candidate code execution/network/model scoring.

**28 evaluator test methods passed;0 failures/errors/skips/network attempts.57 authored fixtures:17 accepted,34 rejected,6 explicit review.** All labels/dimensions match; false acceptance0/34, rejection0/17, false format0/44, missed preservation0/6, missed citation0/2, false citation0/49, safety upgrade0/24, silently accepted ambiguity0/6. These are same-author fixture agreement, not independently measured real-model rates. Determinism/order/no shared state/locale, duplicate keys/nonfinite bounds, field mutations, safe concise/equivalent answers and synthetic improvement/regression/no-change pairs pass. First failed reason-code attempt and all warranted corrections preserved; expectation labels unchanged. [RESULTS](validation/RESULTS.json), [corrections](validation/CORRECTIONS.md).

## Independent review/freeze

Independent review PENDING, no submitted reviewer disagreements or approval. Ten open adjudications include task freshness/difficulty/ceiling, architectural balance, meaningful explanation, valid alternatives, polarity/reference semantics and budget fairness. [Handoff](INDEPENDENT_REVIEW_HANDOFF.md), [structured feedback template](validation/REVIEW_FEEDBACK.csv). Self-review is explicitly not independent. FREEZE_MANIFEST.json records task/evaluator/fixture/contracts/reports/dependency/source hashes; it is a draft, never independently approved/final. Any correction after final freeze needs a new version/hash with preserved outcomes.

## Budget/preregistration

Original24/136 math fits only the old plan's one-cycle16-call override. Current public prompts classify DEEP/minimum2 cycles offline: ordinary quality control21 calls, full target152 even before variant repair margin; native historical projection177, pooled188.5, structural maximum216. Thus no silent control crippling or budget increase. Proposed stage1:2 tasks×1 repetition×6 conditions=12 runs, common36-call/run and30min/run outer limits, END retains three-cycle cap. Published structural maximum108 model calls, global proposal unchanged136 attempts/400k tokens/3h. Ordinary estimate86.5 calls,~244,544 tokens/~69–76min before margin; current usage/prototypes unknown. Stage2 needs separate approval/budget; variance unavailable in stage1. [Budget audit](BUDGET_FEASIBILITY.md), [draft preregistration](EXPERIMENT_PREREGISTRATION.md).

All future live/prototype work remains separately authorized. This task stops at a reviewable draft measurement bundle. It demonstrates evaluator consistency within documented scope, not productive END deliberation, general correctness/safety or architecture superiority.
