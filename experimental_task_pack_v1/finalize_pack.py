"""Offline protection audit and draft freeze. No model/provider/benchmark execution."""
import ast
import csv
import hashlib
import json
import platform
import re
from pathlib import Path
from experimental_task_pack_v1 import research_guard as g
from experimental_task_pack_v1.evaluators.contracts import RUBRIC_VERSION

ROOT,OUT,VAL=g.ROOT,g.OUT,g.VAL
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
    base=load(VAL/'BASELINE.json');before=load(VAL/'protected-before.json');after=g.protected()
    assert before==after,'Original file-set/hash changed outside task pack'
    assert g.source()==load(VAL/'source-before.json')
    fp=hashlib.sha256(json.dumps(g.source(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert fp==base['fingerprint'];assert g.git('rev-parse','HEAD').strip()==base['git_head']
    status=g.git('status','--short');assert status==(VAL/'git-status-before.txt').read_text(encoding='utf-8')
    (VAL/'git-status-after.txt').write_text(status,encoding='utf-8',newline='\n')
    diff=g.git('diff','--no-ext-diff','--no-textconv','--stat')
    (VAL/'git-diff-stat.txt').write_text(diff,encoding='utf-8',newline='\n')
    packdiff=g.git('diff','--no-ext-diff','--no-textconv','--','experimental_task_pack_v1')
    (VAL/'git-diff-pack.txt').write_text(packdiff,encoding='utf-8',newline='\n')
    engine=load(VAL/'engine-tests-final.json');ev=load(VAL/'RESULTS.json')
    assert engine['passed'] and engine['tests']==303 and engine['network_attempts']==0
    assert ev['passed'] and ev['fixture_count']==57 and ev['network_attempts']==0
    assert not ev['fixture_label_disagreements'] and ev['independent_review_status']=='PENDING'
    fixtures=sorted((OUT/'fixtures').rglob('*.json'));assert len(fixtures)==57
    first=load(VAL/'evaluator-attempt-01.json');first_labels={r['fixture_id']:r['expected'] for r in first['fixtures']}
    for p in fixtures:
        fixture=load(p);assert fixture['expected']==first_labels[fixture['fixture_id']]
        assert len(fixture['expected']['dimensions'])==7 and fixture['rationale']
    old_fixtures=load(VAL/'fixture-hashes-before-reference-clarification.json')
    changed=[name for name,old in old_fixtures.items() if g.sha(OUT/name)!=old]
    assert sorted(changed)==['fixtures/exp-001/07_invented_registry_id.json','fixtures/exp-002/07_invented_registry_id.json']
    tasks=sorted((OUT/'tasks').glob('*.json'));assert [p.stem for p in tasks]==['EXP-001','EXP-002']
    for p in OUT.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    # Candidate evaluation modules must be data-only, without execution/network/provider imports.
    prohibited={'end_engine','subprocess','socket','requests','urllib','http','typesafe','openai','anthropic'}
    for p in (OUT/'evaluators').glob('*.py'):
        tree=ast.parse(p.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):assert all(n.name.split('.')[0] not in prohibited for n in node.names)
            if isinstance(node,ast.ImportFrom) and node.module:assert node.module.split('.')[0] not in prohibited
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in ('eval','exec','compile','__import__')
    credentials=[]
    patterns=[re.compile(r'\bsk-[A-Za-z0-9_-]{20,}'),re.compile(r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}'),
        re.compile(r'\bAIza[A-Za-z0-9_-]{30,}'),re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\s]{40,}')]
    for p in OUT.rglob('*'):
        if p.is_file():
            text=p.read_text(encoding='utf-8',errors='ignore')
            if any(x.search(text) for x in patterns):credentials.append(p.relative_to(OUT).as_posix())
    assert not credentials,'Possible secret markers; stop without printing values'
    source_docs=['architecture_review_v1/REPORT.md','architecture_review_v1/ARCHITECTURE_PROPOSALS.md',
        'architecture_review_v1/EXPERIMENT_PLAN.md','architecture_review_v1/LIMITATIONS.md',
        'architecture_review_v1/QUALITYGATE_CALIBRATION.md','architecture_review_v1/CANDIDATE_TRANSITIONS.csv',
        'architecture_review_v1/SUMMARY.json','architecture_review_v1/RUNS.json','IMPLEMENTATION_REPORT_v0.3.5.2.md',
        'end_engine/core/task_analyzer.py','end_engine/config.py','end_engine/engine.py',
        'v0351_core_regression_pilot/bench/conditions.py','v0351_core_regression_pilot/manifest.json',
        'v035_core_regression_pilot/manifest.json','benchmark_alpha/bench/evaluators.py']
    source_docs+=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'benchmark_alpha/tasks').glob('*.json'))
    controls=[]
    for pilot in ('v035_core_regression_pilot','v0351_core_regression_pilot'):
        m=load(ROOT/pilot/'manifest.json')
        for name,sha in m['task_hashes'].items():assert g.sha(ROOT/pilot/'tasks'/f'{name}.json')==sha
        p=ROOT/pilot/'bench/evaluators.py';assert g.sha(p)==m['evaluator_sha256']
        assert g.sha(ROOT/'benchmark_alpha/bench/evaluators.py')==m['evaluator_sha256']
        controls.append({'pilot':pilot,'version':m['engine']['version'],'historical_source_fingerprint':m['engine']['source_sha256'],
            'evaluator_version':'alpha-3','evaluator_sha256':m['evaluator_sha256'],'historical_task_hashes':m['task_hashes']})
    write(VAL/'SOURCES.json',{'date':'2026-10-12','documents':[{'path':n,'sha256':before[n],
        'role':'Historical/current research source; read only'} for n in source_docs],
        'historical_controls':controls,'original_protected_file_count':len(before),
        'source_fingerprint':fp,'source_entries':len(g.source()),'existing_architectures_implemented':False,
        'offline_analysis_exception':'compute_budget imports the unchanged TaskAnalyzer for provider-free heuristic classification only; external evaluators never import END.',
        'independent_review_status':'PENDING'})
    write(VAL/'protected-after.json',after)
    budget=load(VAL/'BUDGET_ESTIMATES.json')
    final={'date':'2026-10-12','passed':True,'source_fingerprint':fp,'engine_source_unchanged':True,
        'all_original_file_sets_and_hashes_unchanged':True,'protected_original_files':len(before),
        'historical_research_unchanged':True,'historical_tasks_evaluators_unchanged':True,
        'end_harness':'No access or modification to separate project','git_head_unchanged':True,'git_status_unchanged':True,
        'git_diff_inspected':'Existing diff stat recorded; new pack untracked, so its Git diff is empty and its full file inventory/hashes are reviewed separately.',
        'engine_tests':engine,'evaluator_tests':{k:v for k,v in ev.items() if k!='fixtures'},
        'fixture_expectation_labels_unchanged':True,'fixture_reference_content_changes_documented':changed,
        'known_good_accepted':17,'known_bad_rejected':34,'explicit_review_cases':6,
        'independent_review_status':'PENDING','freeze_status':'DRAFT_PENDING_REVIEW',
        'untrusted_candidate_code_executed':False,'possible_secret_findings':[],
        'live_model_calls':0,'runtime_inference_network_calls':0,'live_benchmarks_executed':False,
        'engine_architecture_changes':False,'commit_push_publish_version_bump':False,
        'budget_assessment':'24-run136-call three-cycle control plan infeasible on source/historical estimates;12-run stage proposed, not approved/executed',
        'recommended_next_action':'A. REQUEST INDEPENDENT REVIEW',
        'all_new_writes':'experimental_task_pack_v1/'}
    write(VAL/'FINAL_VALIDATION.json',final)
    report=f'''# END Experimental Task Pack v1 — final preparation report

2026-10-12. **Next action A: REQUEST INDEPENDENT REVIEW.** Review=PENDING; freeze=DRAFT_PENDING_REVIEW; live experiment=NOT EXECUTED. Exactly two fresh tasks and a deterministic external measurement system are prepared. No architecture A/B/C, Engine version/config/prompt change or live request was made.

## Baseline/protection

Engine0.3.5.2, fingerprint `{fp}`, Python{platform.python_version()}, Git main/HEAD `{base['git_head']}`. Baseline303 tests passed in{base['tests']['elapsed_seconds']}s; final303 passed in{engine['elapsed_seconds']}s, zero failures/errors/skips/network attempts. All{len(before):,} original files outside this pack are byte-identical, including all architecture-review/historical reports/tasks/evaluators/validation. Separate END Harness untouched. Existing dirty Git work retained; no staging/commit/push/publication. [Final audit](validation/FINAL_VALIDATION.json), [sources](validation/SOURCES.json).

## Tasks and measurable outcomes

EXP-001 creates museum loan/handling label text from explicit flags, preserves exact IDs/order/titles, and includes a checkable explanation of triggered rules. Six substantive outputs/four preservation checks identify good answers, wrong handling/prefix, lost explanation, normalization/reordering, extra fields, malformed output and valid equivalents. Correct fixture does not imply perfect future model C0.

EXP-002 repairs eight-row telemetry policy decisions and diagnoses three original faults while preserving five correct decisions and all IDs/features. It distinguishes diagnosis without repair, partial repair, wrong diagnosis/unrelated change, full repair with unaffected damage and valid alternative order. Eight substantive/three repair/37 preservation checks. Supplied defect is TASK_INPUT, not generated C0. A correctly repaired first answer yields no deliberation gain unless its actual later candidate improves it.

[Task selection](TASK_SELECTION.md), [scoring contracts](SCORING_CONTRACTS.md), [public tasks](tasks/EXP-001.json) / [EXP-002](tasks/EXP-002.json). Only public_loader's whitelist goes to a future model; private evaluator/fixtures/known-good answers remain evaluation-side. This is file separation, not robust secrecy against a repository-reading agent.

## Evaluator/fixtures

Rubric `{RUBRIC_VERSION}`: seven independent dimensions, no cross-dimension weights; mandatory logical success plus distinct safety/citation results. Complete authoritative answer only, no transcript fragment rescue. Malformed substance stays unassessed; missing execution/withholding is separate from incorrect content. Unsupported confirmation/status/execution/scope and closed-task IDs are checked with polarity/source/hypothetical controls; unknown external URLs/strings or unassessed semantics require review. No candidate code execution/network/model scoring.

**{ev['tests_run']} evaluator test methods passed;0 failures/errors/skips/network attempts.57 authored fixtures:17 accepted,34 rejected,6 explicit review.** All labels/dimensions match; false acceptance0/34, rejection0/17, false format0/44, missed preservation0/6, missed citation0/2, false citation0/49, safety upgrade0/24, silently accepted ambiguity0/6. These are same-author fixture agreement, not independently measured real-model rates. Determinism/order/no shared state/locale, duplicate keys/nonfinite bounds, field mutations, safe concise/equivalent answers and synthetic improvement/regression/no-change pairs pass. First failed reason-code attempt and all warranted corrections preserved; expectation labels unchanged. [RESULTS](validation/RESULTS.json), [corrections](validation/CORRECTIONS.md).

## Independent review/freeze

Independent review PENDING, no submitted reviewer disagreements or approval. Ten open adjudications include task freshness/difficulty/ceiling, architectural balance, meaningful explanation, valid alternatives, polarity/reference semantics and budget fairness. [Handoff](INDEPENDENT_REVIEW_HANDOFF.md), [structured feedback template](validation/REVIEW_FEEDBACK.csv). Self-review is explicitly not independent. FREEZE_MANIFEST.json records task/evaluator/fixture/contracts/reports/dependency/source hashes; it is a draft, never independently approved/final. Any correction after final freeze needs a new version/hash with preserved outcomes.

## Budget/preregistration

Original24/136 math fits only the old plan's one-cycle16-call override. Current public prompts classify DEEP/minimum2 cycles offline: ordinary quality control21 calls, full target152 even before variant repair margin; native historical projection177, pooled188.5, structural maximum216. Thus no silent control crippling or budget increase. Proposed stage1:2 tasks×1 repetition×6 conditions=12 runs, common36-call/run and30min/run outer limits, END retains three-cycle cap. Published structural maximum108 model calls, global proposal unchanged136 attempts/400k tokens/3h. Ordinary estimate86.5 calls,~244,544 tokens/~69–76min before margin; current usage/prototypes unknown. Stage2 needs separate approval/budget; variance unavailable in stage1. [Budget audit](BUDGET_FEASIBILITY.md), [draft preregistration](EXPERIMENT_PREREGISTRATION.md).

All future live/prototype work remains separately authorized. This task stops at a reviewable draft measurement bundle. It demonstrates evaluator consistency within documented scope, not productive END deliberation, general correctness/safety or architecture superiority.
'''
    (OUT/'FINAL_REPORT.md').write_text(report,encoding='utf-8',newline='\n')
    # Check all artifact/document links now that final outputs exist (manifest added below).
    missing=[]
    for doc in OUT.rglob('*.md'):
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
            if not (doc.parent/link.split('#')[0]).is_file():missing.append((doc.name,link))
    assert not missing,missing
    required=['README.md','DESIGN_RATIONALE.md','TASK_SELECTION.md','INDEPENDENT_REVIEW_HANDOFF.md',
        'EXPERIMENT_PREREGISTRATION.md','BUDGET_FEASIBILITY.md','FINAL_REPORT.md','validation/RESULTS.json','validation/ADVERSARIAL_REVIEW.md']
    assert all((OUT/name).is_file() for name in required)
    files={p.relative_to(OUT).as_posix():g.sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='FREEZE_MANIFEST.json'}
    evaluator_hashes={p.name:g.sha(p) for p in sorted((OUT/'evaluators').glob('*.py'))}
    bundle=hashlib.sha256(json.dumps(evaluator_hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    manifest={'FREEZE_STATUS':'DRAFT_PENDING_REVIEW','INDEPENDENT_REVIEW_STATUS':'PENDING','independently_approved':False,
        'date':'2026-10-12','rubric_version':RUBRIC_VERSION,'task_ids':['EXP-001','EXP-002'],
        'task_hashes':{p.stem:g.sha(p) for p in tasks},'evaluator_source_hashes':evaluator_hashes,'evaluator_bundle_sha256':bundle,
        'fixture_hashes':{p.relative_to(OUT).as_posix():g.sha(p) for p in fixtures},
        'contract_and_report_hashes':{name:files[name] for name in files if name.endswith('.md')},
        'dependencies':{'python':platform.python_version(),'minimum_python':'3.11','third_party':[], 'models_installed':False},
        'engine_source_fingerprint':fp,'engine_version':'0.3.5.2','git_head':base['git_head'],
        'aggregation':'Equal atomic weights within separate dimensions; no cross-dimension weighting. task_success requires all applicable task dimensions1; overall_pass additionally requires safety/citation1; unknown=null/review.',
        'scores_inapplicable':'NOT_APPLICABLE/null; never automatically1','source_manifest':'validation/SOURCES.json',
        'protected_original_snapshot':'validation/protected-before.json','protected_original_snapshot_sha256':g.sha(VAL/'protected-before.json'),
        'source_scope':'All evaluator/task/fixtures/tests/reports/source hashes below; manifest itself excluded from self-hash.',
        'all_pack_files_sha256':files,'validation':{'engine_tests':303,'evaluator_test_methods':ev['tests_run'],'fixture_count':57,
            'passed':True,'independent_review_status':'PENDING','live_calls':0},
        'future_matrix':'24 target; revised12-run stage proposed, not authorized/executed',
        'no_post_output_rewrite':'Final freeze requires future independent review and authorization; later corrections create a new immutable version/hash, never overwrite scored model artifacts.'}
    write(OUT/'FREEZE_MANIFEST.json',manifest)
    assert g.protected()==before and g.source()==load(VAL/'source-before.json')
    print(json.dumps({'baseline':base['version'],'engine_tests':engine['tests'],'evaluator_tests':ev['tests_run'],
        'fixtures':57,'protected_files_unchanged':len(before),'review':'PENDING','freeze':'DRAFT_PENDING_REVIEW',
        'task_hashes':manifest['task_hashes'],'evaluator_bundle_sha256':bundle,'live_calls':0}))
if __name__=='__main__':main()
