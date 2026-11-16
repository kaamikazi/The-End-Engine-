# Task selection and freshness

## EXP-001 — Museum loan-label kit

Generate labels for three museum records from explicit loan/fragility flags: literal loan prefix, exact title, handling text, preserved opaque accession and input order. A structured explanation lists which IDs triggered each transformation. Required scope is label_text_only; no physical inspection is implied. Two independent flags make unnecessary normalization, reordering, invented certificates, title embellishment, new fields or changed handling measurable. Six substantive outputs and four preservation checks are separate from format/explanation/safety.

Known-good synthetic answer is straightforward; actual model C0 is not guaranteed correct. A wrong initial handling/prefix can improve, while a correct C0 can regress or stay unchanged. The evaluator detects missing explanation, changed IDs/order, extra unsupported fields, format errors and authority/citation claims. Permitted equivalents are object key order, whitespace, JSON escaping and whole-fence versus bare JSON. Array order and identifiers are genuinely normative, not hidden scoring tricks.

## EXP-002 — Telemetry export decision-table repair

Eight combinations of destination, consent and quarantine have draft decisions. Three supplied decisions conflict with a priority policy; quarantine overrides other flags, external/no-consent without quarantine requires MINIMAL, otherwise FULL. Repair all three decisions, preserve five already-correct decisions and all row identifiers/features, and diagnose exactly the erroneous input rows with their governing rule and expected decision. Required scope is paper_policy_only; nothing certifies actual privacy/legal/deployment safety.

The draft is explicitly TASK_INPUT. The first actual generated candidate may already repair it perfectly. Repair completeness against TASK_INPUT is therefore not evidence of deliberation gain; C0→final uses two actually generated answers. Correct diagnosis without repair, partial repair, wrong diagnosis/unrelated change, full repair with damaged correct content, valid-shape wrong decisions and equivalent reordered tables are separately measurable. Eight decisions, three input repairs and37 preservation checks require coherent localization; this is not a correct-keyword test. Difficulty is a design hypothesis, not a measured model property. A strong model may still have a ceiling; review this before final freeze.

## Historical non-reuse audit

Read all12 Alpha task definitions, relevant alpha-3 evaluator parsing/scoring, both pilot manifests/evaluator hashes and the architecture review. BA-001 used temperature conversion/numeric tolerance; BA-002 used Python chunk-function execution; BA-008 used a false sorted premise; BA-009 used incomplete incident evidence/root cause. These tasks reuse none of their answers, numbers, code, hidden premise or regex trick. They also avoid Alpha's scheduling, timestamp normalization, payment webhook, fencing, palindrome and incident report domains. Any similarity is the legitimate general research goal of correctness/preservation/repair, not a disguised old task.

Selection did not inspect fresh model outcomes, choose architecture winners, or simulate a live C0. All six future conditions get identical public material. A preservation task may naturally exercise sparse gating and a repair task directed repair; this is intentional hypothesis coverage, **not independent proof of neutrality**. Bounded alternatives and direct/reflection/current END can all solve either task. No privileged correctness feedback, independent facts or hidden evaluator is supplied to any arm. Reviewer must adjudicate task balance and likely difficulty; no claimed independent approval.

Exact motivating documents, historical task/evaluator hashes and all original protection hashes are recorded in validation/SOURCES.json and FREEZE_MANIFEST. Current production source fingerprint matches0.3.5.2; A/B/C remain proposals, with no production implementation or configuration changes.
