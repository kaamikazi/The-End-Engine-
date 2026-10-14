# Manual review set — SYNTHETIC BENCHMARK INFRASTRUCTURE TEST

Selected automatically by the rules in `bench/report.py`; inspect the referenced files.

**SYNTHETIC BENCHMARK INFRASTRUCTURE TEST** — scripted outputs, not evidence.

## BA-004.T1.END_LITE — largest END improvement over its own C0

- condition END_LITE, external passed=True score=1.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/9fa53a81-291d-4819-8509-1c22c7dc059f.jsonl`
- files: `trials/BA-004.T1.END_LITE.json`, `evaluations/BA-004.T1.END_LITE.json`
- failed checks: []
- review flags: []

## BA-012.T1.END_LITE — largest END regression from its own C0

- condition END_LITE, external passed=False score=0.5556
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/9d4b7b9d-0978-472e-88c6-e12aecf3ea8f.jsonl`
- files: `trials/BA-012.T1.END_LITE.json`, `evaluations/BA-012.T1.END_LITE.json`
- failed checks: ['unit_tests']
- review flags: []

## BA-001.T1.END_LITE — QualityGate/verifier false accept

- condition END_LITE, external passed=False score=0.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/d85102f2-53af-4182-86c1-fb57c2446b45.jsonl`
- files: `trials/BA-001.T1.END_LITE.json`, `evaluations/BA-001.T1.END_LITE.json`
- failed checks: ['values_correct']
- review flags: []

## BA-002.T1.FULL_END — rollback save

- condition FULL_END, external passed=True score=1.0
- END: gate=ACCEPT_PROVISIONALLY label=ACCEPTED_PROVISIONAL termination=ACCEPTED_PROVISIONALLY returned=C0 trajectory=`trajectories/f193aa0f-3c12-4793-ae1b-410299b39062.jsonl`
- files: `trials/BA-002.T1.FULL_END.json`, `evaluations/BA-002.T1.FULL_END.json`
- failed checks: []
- review flags: []

## BA-007.T1.FULL_END — rollback hurt

- condition FULL_END, external passed=False score=0.25
- END: gate=ACCEPT_PROVISIONALLY label=ACCEPTED_PROVISIONAL termination=ACCEPTED_PROVISIONALLY returned=C0 trajectory=`trajectories/6854df09-3e20-4b48-a928-2be19435dd2e.jsonl`
- files: `trials/BA-007.T1.FULL_END.json`, `evaluations/BA-007.T1.FULL_END.json`
- failed checks: ['prevention', 'w1_after_rejection', 'w2_retry_on_timeout']
- review flags: []

## BA-009.T1.END_LITE — correct uncertainty

- condition END_LITE, external passed=True score=1.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/3324bf0b-85fe-426b-9cf7-956f533fc51f.jsonl`
- files: `trials/BA-009.T1.END_LITE.json`, `evaluations/BA-009.T1.END_LITE.json`
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

