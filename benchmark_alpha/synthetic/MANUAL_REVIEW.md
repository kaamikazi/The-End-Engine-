# Manual review set — SYNTHETIC BENCHMARK INFRASTRUCTURE TEST

Selected automatically by the rules in `bench/report.py`; inspect the referenced files.

**SYNTHETIC BENCHMARK INFRASTRUCTURE TEST** — scripted outputs, not evidence.

## BA-004.T1.END_LITE — largest END improvement over its own C0

- condition END_LITE, external passed=True score=1.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/c626d30c-87e5-4814-8693-06f5aa00b51c.jsonl`
- files: `trials/BA-004.T1.END_LITE.json`, `evaluations/BA-004.T1.END_LITE.json`
- failed checks: []
- review flags: []

## BA-012.T1.END_LITE — largest END regression from its own C0

- condition END_LITE, external passed=False score=0.5556
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/2f6f601f-f95b-4a5b-a41d-5cc47905077f.jsonl`
- files: `trials/BA-012.T1.END_LITE.json`, `evaluations/BA-012.T1.END_LITE.json`
- failed checks: ['unit_tests']
- review flags: []

## BA-001.T1.END_LITE — QualityGate/verifier false accept

- condition END_LITE, external passed=False score=0.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/1f30f083-0994-4ae3-976a-021db28b9a51.jsonl`
- files: `trials/BA-001.T1.END_LITE.json`, `evaluations/BA-001.T1.END_LITE.json`
- failed checks: ['values_correct']
- review flags: []

## BA-002.T1.FULL_END — rollback save

- condition FULL_END, external passed=True score=1.0
- END: gate=ACCEPT_PROVISIONALLY label=ACCEPTED_PROVISIONAL termination=ACCEPTED_PROVISIONALLY returned=C0 trajectory=`trajectories/80cd7a96-4ff2-4fe0-9aa1-56dd4eb32ded.jsonl`
- files: `trials/BA-002.T1.FULL_END.json`, `evaluations/BA-002.T1.FULL_END.json`
- failed checks: []
- review flags: []

## BA-007.T1.FULL_END — rollback hurt

- condition FULL_END, external passed=False score=0.25
- END: gate=ACCEPT_PROVISIONALLY label=ACCEPTED_PROVISIONAL termination=ACCEPTED_PROVISIONALLY returned=C0 trajectory=`trajectories/6163878a-8120-4f50-b6a0-473f3753dfdc.jsonl`
- files: `trials/BA-007.T1.FULL_END.json`, `evaluations/BA-007.T1.FULL_END.json`
- failed checks: ['prevention', 'w1_after_rejection', 'w2_retry_on_timeout']
- review flags: []

## BA-009.T1.END_LITE — correct uncertainty

- condition END_LITE, external passed=True score=1.0
- END: gate=BLOCKED label=INCONCLUSIVE termination=QUALITY_THRESHOLD_REACHED returned=C1 trajectory=`trajectories/d99d0437-4a07-41fb-a409-cdd3cff34c92.jsonl`
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

