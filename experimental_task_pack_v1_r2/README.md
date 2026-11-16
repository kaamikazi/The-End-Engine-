# END Experimental Task Pack v1 — Round2 corrections

Rubric **exp-pack-1.0.2-draft**. Round1 targeted independent code/fixture review by separate-session ChatGPT: **REVISE** (supplied by user; standalone reviewer files not present). Round2: **PREPARED FOR RE-REVIEW**, independent recheck **PENDING**, freeze **DRAFT_PENDING_REVIEW**. No approval or live authorization.

Original experimental_task_pack_v1 and original review ZIP remain byte-identical. Corrected source/data/docs live only here. Public task definitions/hashes unchanged. Two attribution fixture expectations are explicitly corrected; all original57 retained, plus26 new single fixtures and18 directional pairs. Latest local suite: **58 methods** (30 added),0 failures/errors/skips/network attempts. All83 single labels and18 pair expectations match; same-author validation is not independent recheck.

Python3.11+ standard library only, validated on3.12.14. From the directory containing experimental_task_pack_v1_r2:

```
python -B -m unittest discover -s experimental_task_pack_v1_r2/tests -t . -v
```

Use PYTHONDONTWRITEBYTECODE=1/PYTHONUTF8=1. Core external evaluators never import END or execute candidate code. Research baseline/validation authoring utilities can write outputs and require the original repository; inspect rather than run them against frozen evidence. Current and historical before/after probes can be inspected under validation; round1_reference supplies verbatim old evaluator/tasks for offline contrast, never the active scoring authority.

Read SCORING_CONTRACTS, ROUND2_CHANGELOG, HEADROOM_AUDIT, EXPERIMENT_PREREGISTRATION, BUDGET_FEASIBILITY, INDEPENDENT_REVIEW_HANDOFF and validation/ROUND1_FINDING_DISPOSITIONS.csv. Expected labels/rationales are in fixtures and paired_fixtures; full original/new migration record in validation/ORIGINAL_57_REVALIDATION.json. No model-generated C0 is fabricated from TASK_INPUT. Task correctness, contract/safety repair and cost stay separate.

Only public_loader's task whitelist goes to future models. Evaluator/fixture/review material is evaluation-side; a repository-reading agent can still see it. File separation is not an access boundary. Next action is independent re-review of the R2 ZIP, not architecture implementation/inference.
