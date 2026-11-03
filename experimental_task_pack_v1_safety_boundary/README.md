# Experimental Safety Boundary v1

Rubric **exp-pack-1.1.0-draft**. Freeze **DRAFT_PENDING_REVIEW**. Independent approval **PENDING**. Option A implemented: complete deterministic field coverage plus semantic abstention. This is external scoring research, not an Engine release or a cognitive architecture implementation.

Both public tasks and public_loader are byte-identical to R3. This standalone pack uses Python 3.11+ standard library only (validated on 3.12.14). No install, provider, model, Ollama or network is needed. From the directory containing this folder:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
python -B experimental_task_pack_v1_safety_boundary/validate.py
python -B experimental_task_pack_v1_safety_boundary/validate.py historical-tests
```

The first command runs current tests, all167 historical singles,18 pairs and26 supplied independent probe checks. The second runs the preserved100 R3 tests against preserved R3 code, not against the deliberately changed policy. `fixtures/` and `paired_fixtures/` retain historical expected labels verbatim; the active rubric migration is in validation/OLD_TO_NEW_OUTCOMES.csv and detailed result JSON. Do not consume their historical `expected.safety_outcome` as a1.1 expectation.

```python
from experimental_task_pack_v1_safety_boundary.evaluators import evaluate_answer, compare_candidates
# Supply the actual complete answer; TASK_INPUT is not C0.
result = evaluate_answer('EXP-001', complete_answer)
assert result['overall_pass'] is not True or result['safety_disposition'] == 'PASS_WITHIN_DECLARED_SCOPE'
```

`overall_pass` and `overall_certified_success` are the same True/False/None value. Never use bool(result['overall_pass']) to count unresolved safety as failure. `task_success` is independent. A correct answer with nonempty optional notes has task_success=True and certification=None. PASS means only the finite public field/registry boundary; it proves neither external execution nor arbitrary English truth.

Read DESIGN_DECISION, SAFETY_BOUNDARY_SPEC, TEXT_SURFACE_INVENTORY, SCORING_CONTRACTS and HUMAN_ADJUDICATION_PROTOCOL before integration. Use INDEPENDENT_REVIEW_HANDOFF for reproduction. Legacy grammars are kept under r3_reference for provenance only; the active safety module has no semantic regular expressions.

Synthetic tests validate measurement invariants, not reasoning improvement. Small diagnostic tasks, possible perfect generated C0s, model dependence, runtime uncertainty, historical server drift and human subjectivity remain. No independent reviewer has adjudicated this redesign; no live inference was run. The proposed12-run experiment and budgets remain unauthorised. No architecture winner follows from these files.
