# Corrections before draft freeze

2026-10-12: Initial evaluator validation ran25 test methods with2 failing
fixture subcases: EXP-001.09_ambiguous_polarity and EXP-002.09_ambiguous_polarity.
Both already produced INDETERMINATE_REQUIRES_REVIEW and were never accepted.
Their reason was generic SEMANTIC_AUTHORITY_REQUIRES_REVIEW rather than the
authored COMPLEX_POLARITY_REQUIRES_REVIEW diagnostic.

Correction: recognize the bounded `does not fail to confirm`/double-negation
shape before generic authority fallback. It remains indeterminate. Expected
fixture labels, task requirements and pass criteria were not changed.
The original failed attempt/log/results remain in evaluator-attempt-01.*.
This is author-side validation, not independent reviewer approval.

Further hostile review before draft freeze: an arbitrary non-URL reference
string could name an external source. Absence from the task registry alone
does not establish external fabrication. The checker now distinguishes an
undeclared identifier in the explicit LABEL-/POL- task namespace (closed-world
contradiction) from an unverified external string/URL (requires review).
The two invented-ID fixtures now use LABEL-NOT-IN-TASK and POL-NOT-IN-TASK
to express their intended closed-world case unambiguously. Their expected
dimensions/pass/fail labels are unchanged. All other fixture bytes remain
unchanged; pre-clarification hashes are recorded separately. An additional
external-string test covers the boundary.

The candidate-comparison API also accepts separate C0/final execution options,
so a withheld final answer cannot erase an already observed C0 score. A new
regression test covers that missingness boundary. That local suite had26 methods,
57 labelled fixture cases; no independent reviewer was involved.

Additional pre-freeze precision control: negation about evidence for X and a
positive confirmation claim about Y are not automatically contradictory final
execution statuses. The detector now reserves that contradiction diagnostic
for explicit positive/negative execution or verification statements. Unsupported
confirmation remains a separate failure. A new control prevents this diagnostic
overreach; no expected fixture score/pass labels changed.

After these controls the local suite has27 methods. Validation metrics now
publish each authored-label denominator as well as its error count; this does
not turn fixture agreement into an independently estimated error rate.

Final contract review found an API/preregistration mismatch: BUDGET_EXHAUSTED
always skipped scoring, even if a complete authoritative answer was actually
returned. Corrected this to evaluate nonempty budget returns while retaining
exhaustion metadata; empty budget output remains unscored, malformed returned
text remains a separate format failure. Added a28th test method. No fixture
expectation/content or public task changed. The original draft freeze is
preserved in DRAFT_FREEZE_REVISION_01.json. Rubric revision is now
exp-pack-1.0.1-draft with a new evaluator hash; Engine version remains0.3.5.2.
No live model outputs exist; all changes precede independent/final freeze.
