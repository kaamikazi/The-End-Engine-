# Round2 local correction record

The original28 tests and all concrete review probes were run BEFORE any
Round2 evaluator edits; originals/results are preserved. Original Engine303
tests passed under network blocking. RV-001/002/003 reproduced exactly.

R2 changes only the copied evaluator/tests/fixtures/docs. Two existing
attribution fixture expectations change from definite PASS to review-required
because the public tasks contain no such alleged statements. Content is
unchanged. All other original57 expectations remain unchanged; the complete
original/new content, expected dimensions, result, contract rationale and
pending reviewer status are in ORIGINAL_57_REVALIDATION.json and CSV.

Claim-context controls distinguish criticizing a confirmation proposition
from falsely claiming a registered ID is absent. Ambiguous quoted/hypothetical
unknown-ID use is reviewed rather than treated as definite positive support;
every occurrence still has its actual registry state recorded.

During added named-source/nested-task-report testing, a greedy source pattern
consumed a later reporting verb and failed to recognize an actual provided
attribution. Revised-attempt-01.* preserves this1 failing new test (58 methods,
0 errors). The bounded source parser now selects the earliest reporting verb,
and the unchanged test checks the valid task-provided statement without
promoting its proposition to independent verification. No expected fixture
label was changed to resolve this defect.

No model output has been observed in this correction task. Rubric identity is
exp-pack-1.0.2-draft; original exp-pack-1.0.1-draft and original ZIP are preserved.
All independent rechecks remain PENDING.
