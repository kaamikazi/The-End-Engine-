# Manual review set — SYNTHETIC BENCHMARK INFRASTRUCTURE TEST

Selected automatically by the rules in `bench/report.py`; inspect the referenced files.

**SYNTHETIC BENCHMARK INFRASTRUCTURE TEST** — scripted outputs, not evidence.

## BA-004.T1.END_LITE_NATIVE — largest END improvement over its own C0

- condition END_LITE_NATIVE, external passed=True score=1.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/0774750e-ad1a-45da-afc4-59b91660c1e2.jsonl`
- files: `trials/BA-004.T1.END_LITE_NATIVE.json`, `evaluations/BA-004.T1.END_LITE_NATIVE.json`
- failed checks: []
- review flags: []

## BA-012.T1.END_LITE_NATIVE — largest END regression from its own C0

- condition END_LITE_NATIVE, external passed=False score=0.5556
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/6a34c6f6-facc-48b4-8685-8039191765c7.jsonl`
- files: `trials/BA-012.T1.END_LITE_NATIVE.json`, `evaluations/BA-012.T1.END_LITE_NATIVE.json`
- failed checks: ['unit_tests']
- review flags: []

## BA-001.T1.END_LITE_NATIVE — QualityGate/verifier false accept

- condition END_LITE_NATIVE, external passed=False score=0.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/31de1102-ceef-4024-a816-d9adf22836e2.jsonl`
- files: `trials/BA-001.T1.END_LITE_NATIVE.json`, `evaluations/BA-001.T1.END_LITE_NATIVE.json`
- failed checks: ['values_correct']
- review flags: []

## BA-002.T1.FULL_END_NATIVE — rollback save

- condition FULL_END_NATIVE, external passed=True score=1.0
- END: gate=ACCEPT_PROVISIONALLY label=ACCEPTED_PROVISIONAL termination=ACCEPTED_PROVISIONALLY returned=C0 trajectory=`trajectories/fdf87cc0-92f2-4473-a867-2e1cc5a7594c.jsonl`
- files: `trials/BA-002.T1.FULL_END_NATIVE.json`, `evaluations/BA-002.T1.FULL_END_NATIVE.json`
- failed checks: []
- review flags: []

## BA-007.T1.FULL_END_NATIVE — rollback hurt

- condition FULL_END_NATIVE, external passed=False score=0.25
- END: gate=ACCEPT_PROVISIONALLY label=ACCEPTED_PROVISIONAL termination=ACCEPTED_PROVISIONALLY returned=C0 trajectory=`trajectories/a130f1c0-2095-44ad-abec-82b95a1867cb.jsonl`
- files: `trials/BA-007.T1.FULL_END_NATIVE.json`, `evaluations/BA-007.T1.FULL_END_NATIVE.json`
- failed checks: ['prevention', 'w1_after_rejection', 'w2_retry_on_timeout']
- review flags: []

## BA-009.T1.END_LITE_NATIVE — correct uncertainty

- condition END_LITE_NATIVE, external passed=True score=1.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/ccaa2680-a4da-4e94-b2e9-897bc840b9d4.jsonl`
- files: `trials/BA-009.T1.END_LITE_NATIVE.json`, `evaluations/BA-009.T1.END_LITE_NATIVE.json`
- failed checks: []
- review flags: []

## BA-011.T1.DIRECT — scope overreach

- condition DIRECT, external passed=False score=0.5
- no END trajectory
- files: `trials/BA-011.T1.DIRECT.json`, `evaluations/BA-011.T1.DIRECT.json`
- failed checks: ['names_missing_evidence', 'no_guarantee_from_narrow_test']
- review flags: []

## BA-009.T1.SELF_REFLECT — fabricated evidence

- condition SELF_REFLECT, external passed=False score=0.75
- no END trajectory
- files: `trials/BA-009.T1.SELF_REFLECT.json`, `evaluations/BA-009.T1.SELF_REFLECT.json`
- failed checks: ['cited_ids_exist']
- review flags: []

