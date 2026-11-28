"""Copy-only independent-review archive builder and byte/hash/security validation."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import zipfile

ROOT=Path(__file__).resolve().parents[1]
WORK=Path(__file__).resolve().parent
PACK=ROOT/'experimental_task_pack_v1'
ARCHIVE=ROOT/'END_Experimental_Independent_Review_v1.zip'
PREFIX='END_Experimental_Independent_Review_v1/'

def sha(data):return hashlib.sha256(data).hexdigest()
def file_sha(path):return sha(path.read_bytes())
def save(name,data):
    (WORK/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def originals():
    return {p.relative_to(ROOT).as_posix():file_sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file()
        and not p.is_relative_to(WORK) and p!=ARCHIVE and '.git' not in p.relative_to(ROOT).parts}
def git(*args):
    return subprocess.run(['git','--no-optional-locks','-c','safe.directory=E:/The End Engine',*args],
        cwd=ROOT,capture_output=True,check=True,encoding='utf-8').stdout

START=r'''# Independent review starts here

END Experimental Task Pack v1 — Independent Evaluation of Productive Deliberation.

**Independent review PENDING. Freeze DRAFT_PENDING_REVIEW.** No independent approval, final scientific freeze, productive-deliberation result, architecture winner, deployment claim or live-experiment authorization exists. The package is for a reviewer outside the authoring coding session. Same-author validation is evidence of local consistency, not independent review.

## What is included and what is authoritative

`experimental_task_pack_v1/` is a byte-exact copy of all122 original task-pack files. It includes two public task definitions, all57 labelled fixtures (27 EXP-001,30 EXP-002), four evaluator modules, three test modules plus their package initializer, all validation attempts (including initial failures), latest RESULTS, correction history, scientific specifications, draft freeze and reviewer feedback template. Nothing in that subtree has been edited, reformatted, redacted or re-frozen for this package.

`REVIEW_START_HERE.md`, `REVIEWER_CHECKLIST.md` and `PACKAGE_MANIFEST.json` are packaging-only additions. `review_context/` contains explicitly identified, byte-exact read-only source copies for task novelty, architecture neutrality and budget inspection: original Alpha tasks/evaluator, architecture proposals/review/plan/limitations/aggregates, implementation report and selected current Engine source. This is not the entire Engine repository. Historical raw trajectories, model weights, environments, Git metadata, credentials and unrelated projects are absent.

Authoritative **public requirements**: tasks/EXP-001.json and tasks/EXP-002.json. **Scoring contract**: SCORING_CONTRACTS.md. **Executable rubric**: evaluators/contracts.py, evaluator.py and safety.py, rubric exp-pack-1.0.1-draft. **Authored expected labels**: each fixtures/*/*.json. **Latest validation**: validation/RESULTS.json (attempt7,28 methods,57 fixtures); older attempts are historical, not the active rubric. FREEZE_MANIFEST records current hashes; validation/DRAFT_FREEZE_REVISION_01.json is a preserved superseded draft. Disagreements between specification/code/fixtures must be adjudicated, not resolved by silently changing evidence.

## Read the tasks and independent-review questions

EXP-001: Museum loan-label kit. Three labels derived from loan/fragility flags, opaque IDs/order/title preservation, checkable flag explanation and label_text_only scope. Inspect public input and contracts before viewing known-good fixture01. Ask whether it is new, objectively defined, permits legitimate equivalents, detects unnecessary damage and has enough real C0 headroom.

EXP-002: Telemetry export decision-table repair. Eight normative rows, priority rules and three supplied faults, with five correct decisions/immutable features to preserve and explicit diagnosis. **TASK_INPUT is a supplied defective draft; C0 is only the first actual model-generated answer.** No model C0 or live result is present. Ask whether rules/faults are unambiguous, repairs measurable, unaffected content protected and alternate valid order accepted.

Read INDEPENDENT_REVIEW_HANDOFF, DESIGN_RATIONALE, TASK_SELECTION, SCORING_CONTRACTS, validation/ADVERSARIAL_REVIEW, BUDGET_FEASIBILITY and EXPERIMENT_PREREGISTRATION. The checklist covers freshness, difficulty, equivalence, scoring games, source/polarity safety, architecture bias, C0 deltas and fair bounded costs. Record evidence/fixture IDs for every disagreement.

## Offline reproduction without changing the evidence

Extract the ZIP. Set the working directory to the extracted `END_Experimental_Independent_Review_v1` folder (the directory containing this guide). Python3.11+ standard library only; author and packaging reproduction used Python3.12.14. No pip installation, provider credentials, model, internet, original Engine checkout or external service is required **for evaluator tests or synthetic-fixture scoring**.

PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
python -B -m unittest discover -s experimental_task_pack_v1/tests -t . -v
```

Expected recorded result:28 test methods pass, zero failures/errors/skips. One method checks all57 fixture expectations; method count and fixture count are different denominators. Tests include safe data parsing, field mutations, polarity, state/order/locale controls and synthetic gain/loss/no-change comparisons. They do not execute candidate code or model inference. Running the unittest command with -B does not rewrite the archived evidence. Write any review findings outside the copied task-pack subtree or into a separate working copy.

Evaluate a known-good synthetic fixture without writing results:

```powershell
@'
import json
from pathlib import Path
from experimental_task_pack_v1.evaluators import evaluate_answer
f = json.loads(Path('experimental_task_pack_v1/fixtures/exp-001/01_correct.json').read_text(encoding='utf-8'))
r = evaluate_answer(f['task_id'], f['candidate_content'], **f['evaluation_options'])
print(json.dumps({'expected': f['expected'], 'actual': r}, ensure_ascii=False, indent=2))
'@ | python -B -
```

To inspect all fixtures, iterate the57 JSON files and compare the returned seven dimensions, task_success, overall_pass, safety_outcome and required reason codes with expected fields. Do not label a synthetic fixture as a live generated C0. The supplied metadata records SYNTHETIC_FIXTURE_NOT_ACTUAL_GENERATED_C0.

Avoid re-running prepare_materials.py, author_docs.py, validate_evaluators.py, finalize_pack.py or research_guard.py against the evidence copy: those authoring/validation utilities can overwrite outputs or require the original repository. They are included for inspection/provenance, not needed for isolated evaluator reproduction. compute_budget.py additionally depends on the original architecture-review/Engine environment; inspect its saved BUDGET_ESTIMATES and the included context rather than installing or reconstructing an Engine. Review context Engine/legacy Alpha code is **static evidence only**; do not run it or execute untrusted candidate code.

## Outcomes, safety and missingness

Each fixture includes ID/task/content, evaluation options, explicit seven-dimension expected status/score, expected task_success/overall_pass/safety outcome, required failure/review codes and rationale. Within-dimension equal-weight atomic checks are exposed; there is no cross-dimension weighted quality number. Correctness, preservation, repair, contract, safety/citation and efficiency remain separate. EXP-001 repair is NOT_APPLICABLE/null. Malformed whole answers leave substance unassessed rather than salvaging a convenient snippet. Execution failure, budget exhaustion, format failure, internal BLOCKED and safety withholding are distinct. A complete authoritative answer returned at budget exhaustion is still scored, with exhaustion metadata retained.

Safety outcomes: PASS_WITHIN_DETECTOR_SCOPE, FAIL, INDETERMINATE_REQUIRES_REVIEW. The bounded detector distinguishes direct confirmation/execution claims, negation, source attribution and hypotheticals; unknown semantics remain review-required. Unregistered external URLs/strings are unverified, not proof of nonexistent sources. An undeclared LABEL-/POL- identifier is invalid only in that closed task registry. Model confidence/agreement/internal END judgment never supplies independent verification. Overall pass cannot conceal detected safety/reference failure; null is not a perfect score or a fabricated definite judgment.

Current same-author fixture validation:17 accepted,34 rejected,6 review-required; error counters0 against authored labels. This does not estimate independent real-model error rates. Known limitations include finite English grammar, attribution truth/implicit claims, optional prose overreview, constrained explanation style, actual-answer boundary dependence, source visibility/contamination and potentially easy/ceiling-limited tasks. No live task difficulty has been measured.

## Public/private separation, budget and review readiness

Future models receive only public_loader's whitelist of task statement/input/output contract/reference IDs. They must not receive fixtures, known-good answers, evaluator internals, private measurements or research preferences. Folder separation is not secrecy: a repository-reading coding agent can inspect everything. The reviewer intentionally has the entire measurement implementation; independent review material must not later be injected into model prompts.

The full24-run target with a three-cycle END control does not defensibly fit136 calls: conditional ordinary source path152; native historical estimate177; pooled estimate188.5; structural maximum216. Both full public prompts classify DEEP/minimum2 cycles in the current offline heuristic. The proposed12-run stage preserves three-cycle control and common36-call/run outer ceiling, estimated ~244,544 tokens/~69–76min before margin, with unchanged global136 calls/400k tokens/3h. Its published structural maximum108 is an estimate for unimplemented variants, not a demonstrated guarantee. Stage2/prototypes/live requests require separate approval. No experiment was executed.

Use REVIEWER_CHECKLIST.md as an editable review document. Return structured disagreements through a separate copy of validation/REVIEW_FEEDBACK.csv, including task/fixture/evaluator ID, original expectation, proposed correction, evidence, resolution status and reviewer identity. A reviewer can also be wrong: resolve through task-contract evidence or retain UNRESOLVED. Do not mark independent approval or final freeze merely because the ZIP exists or tests pass. The user uploads this ZIP to the independent reviewer; packaging launches no other task.
'''

CHECKLIST='''# Independent reviewer checklist — editable review copy

Reviewer identity: ____________________  Date: ____________________
Package SHA-256 checked: ____________________  Rubric: exp-pack-1.0.1-draft
Review disposition: PENDING / CHANGES_REQUESTED / APPROVED_WITH_SCOPE / UNRESOLVED
Do not infer approval from packaging or same-author tests. Leave every item unchecked until examined; write PASS/FAIL/REVIEW/NOT_APPLICABLE plus evidence where useful.

## A. EXP-001

- [ ] Is the museum-label task genuinely new? Evidence: ____________________
- [ ] Is the correct output objectively defined? Evidence: ____________________
- [ ] Are valid equivalents accepted? Evidence: ____________________
- [ ] Can preservation failures be detected? Evidence: ____________________
- [ ] Can unnecessary revisions be detected? Evidence: ____________________
- [ ] Are explanations evaluated meaningfully? Evidence: ____________________
- [ ] Is the task too easy to provide improvement headroom? Evidence: ____________________

## B. EXP-002

- [ ] Are the telemetry rules unambiguous? Evidence: ____________________
- [ ] Are all eight decisions correctly specified? Evidence: ____________________
- [ ] Are the three supplied faults genuinely repairable? Evidence: ____________________
- [ ] Are the five unaffected decisions preserved? Evidence: ____________________
- [ ] Can partial repairs receive appropriate credit? Evidence: ____________________
- [ ] Can a correct solution be distinguished from a lucky format match? Evidence: ____________________
- [ ] Is TASK_INPUT clearly separate from generated C0? Evidence: ____________________

## C. EVALUATORS

- [ ] Are there false accepts? Fixture/evidence: ____________________
- [ ] Are there false rejects? Fixture/evidence: ____________________
- [ ] Are legitimate equivalent answers penalized? Evidence: ____________________
- [ ] Is wording unfairly rewarded? Evidence: ____________________
- [ ] Are safety claims assessed within justified scope? Evidence: ____________________
- [ ] Can unsupported citations pass? Evidence: ____________________
- [ ] Can legitimate uncertainty be falsely rejected? Evidence: ____________________
- [ ] Can correct answers fail because of formatting artifacts? Evidence: ____________________
- [ ] Can incorrect answers game the rubric? Evidence: ____________________

## D. EXPERIMENT

- [ ] Do tasks unfairly favor sparse gating? Evidence: ____________________
- [ ] Do tasks unfairly favor directed repair? Evidence: ____________________
- [ ] Do tasks unfairly favor bounded alternatives? Evidence: ____________________
- [ ] Is C0 preservation measured correctly? Evidence: ____________________
- [ ] Does the rubric detect genuine candidate improvement? Evidence: ____________________
- [ ] Are correctness, safety and cost kept separate? Evidence: ____________________
- [ ] Is the proposed12-run pilot feasible? Evidence: ____________________
- [ ] Are inference ceilings scientifically fair? Evidence: ____________________

## Reproduction and disposition

- [ ] Package/byte hashes checked; no unexpected or missing files.
- [ ] Offline28-test result reproduced without changing source/labels.
- [ ] All57 expected fixture results inspected; review-required cases remain explicit.
- [ ] Independent review distinguished from author-side checks; no live experiment inferred.

Disagreements (copy one entry per issue; do not overwrite the archived evidence):

| task_id | evaluator_or_fixture_id | issue_description | original_expectation | proposed_correction | supporting_reasoning | resolution_status | reviewer_identity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | UNRESOLVED | |

Scope of any approval: ____________________
Remaining limitations/conditions: ____________________
Final immutable freeze/live experiment remain a separately authorized step.
'''

def security_scan(entries):
    findings=[]
    forbidden={'.git','.venv','venv','__pycache__','.pytest_cache','.mypy_cache','node_modules','scratch'}
    patterns=[('provider key',r'\bsk-[A-Za-z0-9_-]{20,}'),('GitHub token',r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}'),
        ('Google API key',r'\bAIza[A-Za-z0-9_-]{30,}'),('HuggingFace token',r'\bhf_[A-Za-z0-9]{20,}'),
        ('JWT/access token',r'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}'),
        ('private key',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\s]{40,}'),
        ('authentication value',r'(?i)(?:authorization|proxy-authorization)\s*["\x27]?\s*[:=]\s*["\x27]?(?:bearer|basic)\s+[A-Za-z0-9+/_.=-]{12,}'),
        ('assigned credential',r'(?i)["\x27]?(?:api[_-]?key|password|access_token|refresh_token|client_secret)["\x27]?\s*[:=]\s*["\x27]([A-Za-z0-9+/_.=-]{12,})["\x27]'),
        ('personal user path',r'(?i)C:[\\/]+Users[\\/]+(?!Public\b|Default\b)[A-Za-z0-9_. -]+[\\/]'),
        ('email/account information',r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')]
    for name,data in entries.items():
        path=Path(name)
        if any(part in forbidden for part in path.parts) or path.name.lower().startswith('.env') or path.suffix.lower() in ('.pyc','.pem','.key','.gguf','.safetensors'):
            findings.append({'file':name,'type':'forbidden sensitive/transient file path'})
        text=data.decode('utf-8',errors='replace')
        for kind,pattern in patterns:
            if re.search(pattern,text):findings.append({'file':name,'type':kind})
    return findings

def main():
    assert not ARCHIVE.exists(),'Archive already exists: refuse overwrite'
    assert ARCHIVE.resolve().parent==ROOT and WORK.resolve().parent==ROOT
    before=originals();save('originals-before.json',before)
    head=git('rev-parse','HEAD').strip();save('git-before.json',{'head':head,'status':git('status','--short')})
    freeze=json.loads((PACK/'FREEZE_MANIFEST.json').read_text(encoding='utf-8'))
    result=json.loads((PACK/'validation/RESULTS.json').read_text(encoding='utf-8'))
    assert freeze['FREEZE_STATUS']=='DRAFT_PENDING_REVIEW' and freeze['INDEPENDENT_REVIEW_STATUS']=='PENDING'
    assert result['tests_run']==28 and result['passed'] and result['fixture_count']==57
    packfiles=sorted(p for p in PACK.rglob('*') if p.is_file())
    assert len(packfiles)==122
    assert set(p.relative_to(PACK).as_posix() for p in packfiles)==set(freeze['all_pack_files_sha256'])|{'FREEZE_MANIFEST.json'}
    assert all(file_sha(PACK/name)==value for name,value in freeze['all_pack_files_sha256'].items())
    source={p.relative_to(ROOT).as_posix():file_sha(p) for p in sorted([*(ROOT/'end_engine').rglob('*.py'),ROOT/'pyproject.toml'])}
    fp=sha(json.dumps(source,sort_keys=True,separators=(',',':')).encode())
    assert fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
    assert tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']=='0.3.5.2'
    entries={PREFIX+'experimental_task_pack_v1/'+p.relative_to(PACK).as_posix():p.read_bytes() for p in packfiles}
    context=[*sorted((ROOT/'benchmark_alpha/tasks').glob('*.json')),
        ROOT/'benchmark_alpha/bench/evaluators.py',ROOT/'IMPLEMENTATION_REPORT_v0.3.5.2.md',
        *[ROOT/'architecture_review_v1'/name for name in ('REPORT.md','ARCHITECTURE_PROPOSALS.md','EXPERIMENT_PLAN.md','LIMITATIONS.md','SUMMARY.json','RUNS.json')],
        ROOT/'end_engine/core/task_analyzer.py',ROOT/'end_engine/engine.py',ROOT/'end_engine/quality/session.py']
    for p in context:
        assert p.is_file() and not p.is_symlink()
        entries[PREFIX+'review_context/'+p.relative_to(ROOT).as_posix()]=p.read_bytes()
    entries[PREFIX+'REVIEW_START_HERE.md']=START.encode('utf-8')
    entries[PREFIX+'REVIEWER_CHECKLIST.md']=CHECKLIST.encode('utf-8')
    sensitive=security_scan(entries)
    save('SECURITY_AUDIT.json',{'files_scanned':len(entries),'findings':sensitive,
        'method':'Full-text provider/token/private-key/auth-value/credential/user-path/email patterns plus forbidden-path checks; keyword matches manually reviewed as code identifiers/docs, not secret values.',
        'review':'API-key names in environment scrubbing and detector source contain no values; E:/project development paths are documented provenance, not account credentials.',
        'live_network_requests':0})
    assert not sensitive,'Possible sensitive material found; stop before creating ZIP (values not printed)'
    manifest={'package':'END Experimental Independent Review v1','date':'2026-10-12',
        'review_status':'PENDING','freeze_status':'DRAFT_PENDING_REVIEW','rubric':freeze['rubric_version'],
        'engine_version':'0.3.5.2','engine_fingerprint':fp,'task_pack_file_count':len(packfiles),'task_count':2,
        'fixture_count':57,'evaluator_modules':4,'evaluator_test_methods_recorded':28,
        'copied_sources_sha256':{name:sha(data) for name,data in entries.items() if '/experimental_task_pack_v1/' in name or '/review_context/' in name},
        'review_only_additions':['REVIEW_START_HERE.md','REVIEWER_CHECKLIST.md','PACKAGE_MANIFEST.json','review_context/'],
        'all_other_entry_sha256':{name:sha(data) for name,data in entries.items()},
        'manifest_self_hash_excluded':True,'omitted_files':[],
        'excluded_empty_directory':'experimental_task_pack_v1/validation/scratch/ (empty temporary-fixture directory; no source/fixture/evidence file omitted)',
        'dependencies':'Python3.11+ stdlib for evaluator reproduction; no Engine/model/environment required. Original authoring/baseline/budget utilities are provenance-only and reference the original repo.',
        'security_scan':'No credential/private-data findings; no source redaction or modification',
        'no_scientific_approval_or_live_authorization':True,'live_model_calls':0,'benchmark_executed':False}
    entries[PREFIX+'PACKAGE_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    temp=WORK/'archive-building.tmp'
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(name,(2026,10,12,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    inventory=[]
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        assert sorted(z.namelist())==sorted(entries)
        for name,data in entries.items():
            assert z.read(name)==data
            info=z.getinfo(name);assert info.file_size==len(data)
            inventory.append({'path':name,'bytes':info.file_size,'compressed_bytes':info.compress_size,'sha256':sha(data)})
        assert sum('/experimental_task_pack_v1/fixtures/' in n and n.endswith('.json') for n in z.namelist())==57
        assert sum('/experimental_task_pack_v1/tasks/' in n and n.endswith('.json') for n in z.namelist())==2
        assert sum('/experimental_task_pack_v1/evaluators/' in n and n.endswith('.py') for n in z.namelist())==4
        assert sum('/experimental_task_pack_v1/tests/' in n and n.endswith('.py') for n in z.namelist())==4
        assert not security_scan({name:z.read(name) for name in z.namelist()})
        extracted=WORK/'extracted';extracted.mkdir(exist_ok=False)
        for name in z.namelist():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert (extracted/name).resolve().is_relative_to(extracted.resolve())
        z.extractall(extracted)
    # Reproduce selected offline evaluator tests from the self-contained extracted copy.
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1';env.pop('PYTHONPATH',None)
    runroot=extracted/PREFIX.rstrip('/')
    proc=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','experimental_task_pack_v1/tests','-t','.','-v'],
        cwd=runroot,capture_output=True,text=True,encoding='utf-8',env=env,timeout=60)
    (WORK/'packaged-evaluator-tests.txt').write_text(proc.stdout+proc.stderr,encoding='utf-8',newline='\n')
    assert proc.returncode==0 and 'Ran 28 tests' in proc.stderr and 'OK' in proc.stderr
    # Every extracted source still matches its archive entry after testing; -B prevents caches.
    for name,data in entries.items():assert (extracted/name).read_bytes()==data
    assert not list(extracted.rglob('__pycache__'))
    assert originals()==before and git('rev-parse','HEAD').strip()==head
    os.replace(temp,ARCHIVE)
    with zipfile.ZipFile(ARCHIVE) as z:assert z.testzip() is None
    save('ARCHIVE_CONTENTS.json',sorted(inventory,key=lambda x:x['path']))
    (WORK/'ARCHIVE_CONTENTS.txt').write_text('\n'.join(x['path'] for x in sorted(inventory,key=lambda x:x['path']))+'\n',encoding='utf-8',newline='\n')
    after=originals();assert after==before;save('originals-after.json',after)
    report={'archive_absolute_path':str(ARCHIVE),'archive_bytes':ARCHIVE.stat().st_size,
        'archive_MB_decimal':ARCHIVE.stat().st_size/1_000_000,'archive_MiB':ARCHIVE.stat().st_size/1048576,
        'archive_sha256':file_sha(ARCHIVE),'archive_file_entries':len(entries),'original_task_pack_files':len(packfiles),
        'task_count':2,'fixture_count':57,'evaluator_modules':4,'evaluator_test_source_files':4,
        'packaged_offline_test_methods_passed':28,'archive_integrity':True,'byte_hash_consistency':True,
        'original_task_pack_byte_identical':True,'all_preexisting_files_byte_identical':True,
        'protected_preexisting_file_count':len(before),'engine_fingerprint':fp,'engine_source_changes':'NONE',
        'git_head_unchanged':True,'secret_scan_findings':0,'missing_or_skipped_files':[],
        'excluded_empty_transient_directory':'experimental_task_pack_v1/validation/scratch/',
        'review_status':'PENDING','freeze_status':'DRAFT_PENDING_REVIEW','live_model_calls':0,'benchmark_executed':'NO',
        'next_action':'User uploads the ZIP to the independent reviewer; no other task launched.'}
    save('VALIDATION.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
