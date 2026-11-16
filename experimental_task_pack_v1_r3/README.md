# Independent Review Corrections — Round3

Active rubric **exp-pack-1.0.3-draft**, independent recheck **PENDING**, freeze **DRAFT_PENDING_REVIEW**. Independent R2 verdict REVISE; all3 newly confirmed defects reproduced before edits in the correct extracted R2 ZIP. Reviewer standalone files not locally present; exact user-supplied findings/probes used. Local success is not independent approval.

Engine0.3.5.2 and original v1/R2/tasks remain unchanged. 100 offline methods pass (58 retained+42 added),0 failures/errors/skips/network attempts. All167 single fixtures:55 PASS,82 FAIL,30 REVIEW; all18 paired transitions match. All83 R2 content/expectations retained, with complete per-fixture observation/rationale/recheck records. No broad expectation weakening.

Python3.11+ stdlib, validated on3.12.14. From the directory containing this pack, with PYTHONDONTWRITEBYTECODE=1/PYTHONUTF8=1:

```
python -B -m unittest discover -s experimental_task_pack_v1_r3/tests -t . -v
python -B -m experimental_task_pack_v1_r3.review_examples
```

The examples compare verbatim historical evaluators with R3; no source edits, provider/Engine install, network or candidate-code execution needed. Baseline/authoring/validation/freeze utilities write artifacts and may need the original checkout; do not run them on the preserved evidence copy. round1_reference/round2_reference are historical evidence, never active scoring authority.

Read SCORING_CONTRACTS, AMBIGUITY_BOUNDARY, ROUND3_CHANGELOG, validation/ROUND2_FINDING_DISPOSITIONS, validation/RESULTS and INDEPENDENT_REVIEW_HANDOFF. Public task/loader bytes and2-task×1-repetition×6-condition12-run proposal/budgets unchanged. Headroom risk remains unmeasured. No live inference, experiment, architecture implementation, commit/push/publication or Engine bump. Next action: submit R3 ZIP for independent re-review.
