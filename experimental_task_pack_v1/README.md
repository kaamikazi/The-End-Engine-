# END Experimental Task Pack v1
## Independent Evaluation of Productive Deliberation

**DRAFT_PENDING_REVIEW. Independent review: PENDING. Experiment: NOT EXECUTED.**
This is offline external measurement infrastructure, not an Engine release or a cognitive architecture. Exactly two fresh public tasks: museum loan-label preservation (EXP-001) and telemetry decision-table diagnosis/repair (EXP-002). The latter's supplied defective draft is TASK_INPUT, never an invented model C0.

Python3.11+ standard library only; validated with3.12.14. No installs, network, model, code execution or special provider credentials are needed. From repository root, with PYTHONDONTWRITEBYTECODE=1 and PYTHONUTF8=1:

```
python -B -m unittest discover -s experimental_task_pack_v1/tests -t . -v
python -B -m experimental_task_pack_v1.validate_evaluators
```

The second command preserves a numbered validation attempt and updates the local latest RESULTS.json; running it after this draft changes validation hashes and requires a new draft manifest. Do not overwrite a final freeze after model outputs exist. Do not rerun prepare_materials.py on a frozen bundle. Evaluator API:

```python
from experimental_task_pack_v1.evaluators import evaluate_answer, compare_candidates
result = evaluate_answer('EXP-001', complete_authoritative_answer_text)
transition = compare_candidates('EXP-002', actual_generated_c0, actual_final_answer)
```

The caller must supply the complete authoritative user-facing answer and its boundary status. No raw-transcript last-block rescue, arbitrary snippet, internal gate/confidence or model authority enters scoring. Bare JSON or one complete JSON fence is accepted. Non-applicable values are null/NOT_APPLICABLE, uncertain semantics are null/INDETERMINATE, not a fabricated perfect score. Pure data parsing never executes candidate code.

Read [TASK_SELECTION](TASK_SELECTION.md), [DESIGN_RATIONALE](DESIGN_RATIONALE.md), [scoring contracts](SCORING_CONTRACTS.md), [author adversarial review](validation/ADVERSARIAL_REVIEW.md), [independent reviewer handoff](INDEPENDENT_REVIEW_HANDOFF.md), [budget audit](BUDGET_FEASIBILITY.md), [draft preregistration](EXPERIMENT_PREREGISTRATION.md) and [final report](FINAL_REPORT.md). FREEZE_MANIFEST.json records task/evaluator/fixture/report hashes and pending review status.

Public tasks and public_loader.py contain only task statements/input/contracts. Evaluators, fixtures, validation and research documents are evaluation-side material. This is organizational separation, **not an enforced access boundary**: a repository-reading coding agent can see all files. Future model prompts must be constructed only through the public whitelist and independently logged/audited. No current END prompt/source/configuration is changed.
