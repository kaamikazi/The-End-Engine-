"""Preservation/security audit, new draft freeze and self-contained Round2 ZIP."""
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from experimental_task_pack_v1_r2 import research_round2 as g

ROOT,OUT,VAL=g.ROOT,g.OUT,g.VAL;ARCHIVE=g.ZIP
PREFIX='END_Experimental_Independent_Review_v1_R2/'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(data):return hashlib.sha256(data).hexdigest()
def save(name,data):g.save(name,data)
def excluded(p):
    return any(part in ('scratch','__pycache__','.git','.venv','.pytest_cache') for part in p.relative_to(OUT).parts)

START='''# Round2 independent re-review starts here

Round1: REVISE; supplied targeted separate-session ChatGPT code/fixture review, not comprehensive human research audit. Round2: PREPARED FOR RE-REVIEW; independent recheck PENDING. Freeze DRAFT_PENDING_REVIEW. Live inference and architecture work NOT AUTHORIZED.

The active pack is experimental_task_pack_v1_r2, rubric exp-pack-1.0.2-draft. Read its README, SCORING_CONTRACTS, ROUND2_CHANGELOG, HEADROOM_AUDIT, INDEPENDENT_REVIEW_HANDOFF and validation/ROUND1_FINDING_DISPOSITIONS.csv. Public tasks are unchanged. All57 original fixtures are retained with unchanged candidate text; only two unsupported-attribution labels change, with complete original/new reasoning and pending recheck. There are26 additional single fixtures and18 directional pairs.

After extracting, use this root as working directory. Python3.11+ standard library only;3.12.14 used locally. No model/provider/Engine installation or network required:

```
python -B -m unittest discover -s experimental_task_pack_v1_r2/tests -t . -v
python -B -m experimental_task_pack_v1_r2.review_examples
```

The first command reproduces58 test methods, including all83 single labels/18 pairs; -B prevents bytecode writes. The second prints the exact original-vs-R2 probes using verbatim round1_reference evaluators/tasks. round1_reference is historical evidence, never active scoring authority. Do not rerun research/fixture-authoring/validation/finalization utilities on the frozen evidence copy; some require the original repository and write artifacts. Independent findings should be written in a separate review copy/feedback file.

Review priorities: fabricated attribution versus actual task occurrence; reference checking in every context and criticism versus supportive citation; quote/polarity/endorsement boundaries; genuine explanation/diagnosis repair versus narrow content gain; new fault/safety/citation losses; missing semantic assessment; no inferred targeted intent; independently unmeasured C0 ceiling/architecture neutrality and preserved budget fairness. Same-author passing tests are not independent approval.

Task correctness, contract repair, narrow substantive delta, preservation, epistemic safety, ambiguity and cost stay separate. Safety has PASS_WITHIN_DETECTOR_SCOPE/FAIL/INDETERMINATE_REQUIRES_REVIEW; null never becomes PASS. Quoted criticism is not endorsement. Actual task-provided report is occurrence validation, not world truth/verification. Unknown URL existence is not decided offline. Whole authoritative answers only; candidate code never runs. Actual generated C0 is never the supplied defective TASK_INPUT.

The static headroom choice is A retain both tasks for limited feasibility/preservation, not empirical disproval. INSUFFICIENT_HEADROOM and HEADROOM_UNDETERMINED are preregistered before any inference; no selective output-dependent reruns/task edits.12-run proposed stage, common36 attempts/run, global136 attempts/400k tokens/3h unchanged, not executed. A/B/C remain unimplemented. No source/privacy credentials/caches/historical trajectories or unrelated repository files included. Public/evaluation-side file separation is not secrecy against a coding agent with repository access.

Use validation/REVIEW_FEEDBACK.csv and finding IDs RV-001–004. All independent rechecks remain PENDING. Submit review evidence, do not silently rewrite labels or relabel local resolution as approval. No live experiment/production deployment follows from this ZIP.
'''

def main():
    before=load(VAL/'protected-before.json');assert g.protected()==before
    source=g.source();assert source==load(VAL/'source-before.json')
    fp=sha(json.dumps(source,sort_keys=True,separators=(',',':')).encode())
    base=load(VAL/'BASELINE.json');assert fp==base['engine_fingerprint']
    assert g.git('rev-parse','HEAD').strip()==base['git_head']
    tests=load(VAL/'engine-final.json');results=load(VAL/'RESULTS.json')
    assert tests['passed'] and tests['tests']==303 and tests['network_attempts']==0
    assert results['passed'] and results['tests']['tests']==58 and results['single_fixture_count']==83 and results['paired_fixture_count']==18
    original_hashes=load(VAL/'original-pack-hashes.json')
    assert all(g.sha(ROOT/'experimental_task_pack_v1'/name)==value for name,value in original_hashes.items())
    original_freeze=load(VAL/'ORIGINAL_FREEZE_MANIFEST.json')
    task_hashes={p.stem:g.sha(p) for p in sorted((OUT/'tasks').glob('*.json'))};assert task_hashes==original_freeze['task_hashes']
    for name,digest in original_freeze['evaluator_source_hashes'].items():assert g.sha(OUT/'round1_reference/evaluators'/name)==digest
    records=load(VAL/'ORIGINAL_57_REVALIDATION.json');assert len(records)==57 and not any(r['content_changed'] for r in records)
    assert sorted(r['fixture_id'] for r in records if r['expectation_changed'])==['EXP-001.04_attribution','EXP-002.04_attribution']
    for p in (OUT/'evaluators').glob('*.py'):
        tree=ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):assert not node.module or not node.module.startswith(('end_engine','subprocess','socket','requests','urllib','typesafe'))
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in ('eval','exec','compile','__import__')
    payloads={p.relative_to(OUT).as_posix():p.read_bytes() for p in OUT.rglob('*') if p.is_file() and not excluded(p)}
    patterns=[('provider credential',r'\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[A-Za-z0-9_-]{30,}|hf_[A-Za-z0-9_]{20,})'),
        ('private key',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\s]{40,}'),
        ('authentication value',r'(?i)(?:authorization|password|client_secret)\s*["\x27]?\s*[:=]\s*["\x27](?:bearer |basic )?[A-Za-z0-9+/_.=-]{16,}["\x27]'),
        ('unnecessary personal path',r'(?i)C:[\\/]+Users[\\/]+(?!Public\b|Default\b)[A-Za-z0-9_. -]+[\\/]')]
    findings=[]
    for name,data in payloads.items():
        if Path(name).name.lower().startswith('.env') or Path(name).suffix.lower() in ('.pyc','.gguf','.pem','.key'):findings.append({'file':name,'type':'forbidden artifact'})
        text=data.decode('utf-8',errors='replace')
        for kind,pattern in patterns:
            if re.search(pattern,text):findings.append({'file':name,'type':kind})
    save('SECURITY_AUDIT.json',{'files_scanned':len(payloads),'findings':findings,'secret_values_printed':False,'runtime_network_calls':0})
    assert not findings,'Possible sensitive artifact; stop without exposing values'
    final={'passed':True,'engine_version':'0.3.5.2','engine_fingerprint':fp,'engine_source_unchanged':True,
        'original_pack_byte_identical':True,'original_pack_files':len(original_hashes),'original_manifest_unchanged':True,
        'all_preexisting_files_byte_identical':True,'protected_preexisting_files':len(before),
        'historical_benchmarks_architecture_review_unchanged':True,'original_review_archive_unchanged':True,
        'reviewer_files':'Not locally supplied; original instructions preserved; no reviewer file overwritten',
        'end_harness':'Separate project not accessed or modified','git_head_unchanged':True,
        'engine_tests':tests,'original_evaluator_tests':base['original_evaluator_tests'],'revised_test_methods':58,
        'single_fixtures':83,'paired_fixtures':18,'fixture_outcomes':results['fixture_outcome_counts'],
        'original_57_outcomes':results['original_57_outcome_counts'],'label_changes':results['expectation_changes'],
        'synthetic_error_counts':results['synthetic_error_counts'],'reproductions_before_and_after_preserved':True,
        'original_task_hashes_preserved':True,'round1_status':'REVISE','round2_status':'PREPARED_FOR_RE_REVIEW',
        'independent_recheck_status':'PENDING','freeze_status':'DRAFT_PENDING_REVIEW','rubric_version':'exp-pack-1.0.2-draft',
        'headroom_decision':'A retain both unchanged for narrow diagnostic only; risk unmeasured',
        'budget':{'planned_runs':12,'outer_attempts_per_run':36,'global_attempts':136,'tokens':400000,'wall_seconds':10800},
        'secrets_found':0,'untrusted_candidate_code_execution':False,'live_model_calls':0,'network_inference_calls':0,
        'benchmarks_executed':0,'commit_push_tag_publication':False,
        'archive_checks':'Final ZIP copy/CRC/hashes and extracted tests are independently checked by this packaging script; digest in external archive receipt to avoid self-hash cycle.'}
    save('FINAL_VALIDATION.json',final)
    report=f'''# Independent Review Corrections — Round2 final report

**PREPARED FOR RE-REVIEW; independent recheck PENDING; DRAFT_PENDING_REVIEW.** Round1 separate-session ChatGPT targeted code/fixture review: REVISE, not comprehensive human audit. Reviewer files absent locally; supplied findings/probes used, fully reproduced before edits. No independent closure/approval or live authorization.

Baseline Engine0.3.5.2, fingerprint `{fp}`, Python{base['python']}, Git main/HEAD `{base['git_head']}`. Engine baseline303/final303 pass; original rubric exp-pack-1.0.1-draft28 tests pass despite reproduced defects. R2 **exp-pack-1.0.2-draft**:58 methods pass (28 prior+30 added),0 failures/errors/skips/network attempts. One new source-parser failure preserved and corrected without expectation relaxation.

RV-001 reproduced4 definite false accepts. Attribution now checked against actual public source/claim occurrence; registered-reference checks run in every context with use/criticism/ambiguity annotated. First two probes now review; unknown attributed task ID fails; unknown URL/source reviews. Actual reports do not earn independent verification. Remaining risks: bounded grammar/literal occurrence, complex paraphrase/alias/implicit endorsement and external source truth. RESOLVED_LOCALLY, independent PENDING.

RV-002 exact quoted criticism reproduced as false positive confirmation. Quote-aware clause/criticism handling now permits it, retaining direct/tail overclaim failures and ambiguous review. Generic grammar, not probe lookup. Complex quotation/discourse remains limited. RESOLVED_LOCALLY, independent PENDING.

RV-003 both mandatory-justification pairs reproduce old meaningful flagFalse with taskFalse→True/content1→1. Independent task-success/explanation/diagnosis/contract/preservation/safety metrics now record clean observable repair, mixed/new-fault cases and partial repair. Narrow content remains unchanged; target intent staysnull pending actual trace adjudication.18 directional pairs all match. RESOLVED_LOCALLY, independent PENDING.

RV-004 static12-question audit: **A retain both unchanged**, for feasibility/preservation only. Shallow finite transformations may produce perfect first generated C0; this is unmeasured. Explicit INSUFFICIENT_HEADROOM/HEADROOM_UNDETERMINED rules prevent unsupported strategy-failure claims, selective reruns or same-freeze task tuning. Sparse/directed/branch discrimination remains limited. RISK_ACCEPTED_FOR_DIAGNOSTIC, independent PENDING. No task harder/trick/forced defective C0 was introduced.

All83 single fixtures match:25 PASS,42 FAIL,16 REQUIRES_REVIEW; all18 pairs match. Original57:15 PASS,34 FAIL,8 REVIEW. Only EXP-001/002.04_attribution expectations change PASS→REVIEW, because their alleged statements are absent from task input; candidate text unchanged. All other old expectations/content retained. Full old/new expectations/result/rationale/recheck state recorded; synthetic false accepts/rejects/format failures/missed citations/incorrect attribution approvals/incorrect confirmation allegations all0, not real-world rates.

Budget/fairness unchanged: proposed12 runs, common36 attempts/run, global136 attempts/400k tokens/3h; no one-cycle-only END reduction. Task hashes/public prompt bytes unchanged, so original offline ~244,544-token/~69–76min projection is retained as an estimate, not actual usage. No model calibration, cognitive implementation, evaluator-in-runtime authority or privileged evidence access.

Original122 pack files, original manifest/ZIP, all{len(before):,} preexisting files, Engine70 source entries and historical/architecture research remain byte-identical. END Harness untouched; Git HEAD unchanged. No secrets detected. No live model/network inference, benchmark, commit/push/tag/publication or Engine version bump.

New FREEZE_MANIFEST records tasks/evaluator/83 fixtures/18 pairs/tests/contracts/preregistration/budget/dispositions/dependencies/current Engine/review identity. The R2 ZIP is `E:\\The End Engine\\END_Experimental_Independent_Review_v1_R2.zip`, containing complete revised pack, historical before/after reference implementation and reproduction guide. Archive integrity/member bytes/extracted58-test result and SHA-256 are recorded in repository-side validation/ARCHIVE_RECEIPT.json; receipt is outside ZIP to avoid a circular archive hash. No archive digest is fabricated inside its own content.

Next action: submit R2 ZIP for independent re-review. Do not implement architectures or run inference until the measurement system is approved and live work separately authorized.
'''
    (OUT/'FINAL_REPORT.md').write_text(report,encoding='utf-8',newline='\n')
    scientific_files={p.relative_to(OUT).as_posix():g.sha(p) for p in OUT.rglob('*') if p.is_file() and not excluded(p)
        and (p.relative_to(OUT).parts[0] in ('evaluators','tasks','fixtures','paired_fixtures','tests') or p.suffix=='.md' or p.name in ('RESULTS.json','ROUND1_FINDING_DISPOSITIONS.csv','BUDGET_ESTIMATES.json','DRAFT_RUN_MATRIX.json','ORIGINAL_FREEZE_MANIFEST.json','public_loader.py'))}
    evaluator_hashes={p.name:g.sha(p) for p in (OUT/'evaluators').glob('*.py')}
    manifest={'rubric_version':'exp-pack-1.0.2-draft','FREEZE_STATUS':'DRAFT_PENDING_REVIEW','round1_review':'REVISE',
        'round1_review_scope':base['review_scope'],'round2_review':'PREPARED_FOR_RE_REVIEW','INDEPENDENT_RECHECK_STATUS':'PENDING',
        'independently_approved':False,'engine_version':'0.3.5.2','engine_source_fingerprint':fp,'task_hashes':task_hashes,
        'original_task_hashes_preserved':True,'original_rubric':'exp-pack-1.0.1-draft','original_manifest_sha256':g.sha(ROOT/'experimental_task_pack_v1/FREEZE_MANIFEST.json'),
        'original_source_fixture_hashes':original_freeze['evaluator_source_hashes']|{'original_fixture_hashes':original_freeze['fixture_hashes']},
        'evaluator_source_hashes':evaluator_hashes,'evaluator_bundle_sha256':sha(json.dumps(evaluator_hashes,sort_keys=True,separators=(',',':')).encode()),
        'fixture_hashes':{n:h for n,h in scientific_files.items() if n.startswith('fixtures/')},
        'paired_fixture_hashes':{n:h for n,h in scientific_files.items() if n.startswith('paired_fixtures/')},
        'test_hashes':{n:h for n,h in scientific_files.items() if n.startswith('tests/')},
        'scientific_artifact_hashes':scientific_files,'dispositions_hash':g.sha(VAL/'ROUND1_FINDING_DISPOSITIONS.csv'),
        'scoring_contract_hash':g.sha(OUT/'SCORING_CONTRACTS.md'),'preregistration_hash':g.sha(OUT/'EXPERIMENT_PREREGISTRATION.md'),
        'budget_document_hash':g.sha(OUT/'BUDGET_FEASIBILITY.md'),'dependencies':{'python':base['python'],'minimum_python':'3.11','third_party':[]},
        'review_status':'ROUND2_PENDING','independent_targeting_provenance':'Not present in synthetic pairs; separate trace adjudication required',
        'live_model_calls':0,'benchmark_runs':0,'notes':['Scientific hashes exclude packaging receipts to avoid self-referential archive hash. All ZIP member bytes are separately inventoried/verified.','No source/evaluator/task correction after observed model output; no live outputs exist.']}
    (OUT/'FREEZE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    assert not ARCHIVE.exists(),'Refuse to overwrite an existing R2 archive'
    entries={PREFIX+'experimental_task_pack_v1_r2/'+p.relative_to(OUT).as_posix():p.read_bytes() for p in OUT.rglob('*') if p.is_file() and not excluded(p)
        and p.name not in ('ARCHIVE_RECEIPT.json','ARCHIVE_CONTENTS.json')}
    entries[PREFIX+'REVIEW_START_HERE.md']=START.encode('utf-8')
    inventory={name:{'sha256':sha(data),'bytes':len(data)} for name,data in entries.items()}
    entries[PREFIX+'PACKAGE_CONTENT_HASHES.json']=(json.dumps(inventory,indent=2)+'\n').encode('utf-8')
    def build(path):
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name,data in sorted(entries.items()):z.writestr(name,data)
    temp=VAL/'r2-archive-building.tmp';build(temp)
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None and set(z.namelist())==set(entries)
        for name,data in entries.items():assert z.read(name)==data and z.getinfo(name).file_size==len(data)
        assert not any(any(part in ('__pycache__','.git','.venv') for part in Path(n).parts) for n in z.namelist())
    # Separate transient verification copy is not inside scientific evidence/ZIP.
    extracted=VAL/'scratch'/'zip_reproduction';assert not extracted.exists();extracted.mkdir(parents=True)
    with zipfile.ZipFile(temp) as z:
        for name in z.namelist():assert not Path(name).is_absolute() and '..' not in Path(name).parts and (extracted/name).resolve().is_relative_to(extracted.resolve())
        z.extractall(extracted)
    runroot=extracted/PREFIX.rstrip('/')
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1';env.pop('PYTHONPATH',None)
    proc=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','experimental_task_pack_v1_r2/tests','-t','.','-v'],cwd=runroot,capture_output=True,encoding='utf-8',env=env,timeout=60)
    (VAL/'packaged-tests.txt').write_text(proc.stdout+proc.stderr,encoding='utf-8',newline='\n')
    assert proc.returncode==0 and 'Ran 58 tests' in proc.stderr
    probes=subprocess.run([sys.executable,'-B','-m','experimental_task_pack_v1_r2.review_examples'],cwd=runroot,capture_output=True,encoding='utf-8',env=env,timeout=30)
    assert probes.returncode==0;example=json.loads(probes.stdout)
    assert [r['new_overall'] for r in example['results'][:5]]==[None,None,False,None,True]
    assert all(r['new_observable_required_repair'] is True for r in example['results'][5:])
    (VAL/'packaged-review-examples.json').write_text(probes.stdout,encoding='utf-8',newline='\n')
    for name,data in entries.items():assert (extracted/name).read_bytes()==data
    assert not list(extracted.rglob('__pycache__'));assert g.protected()==before
    # Include final verification logs, rebuild and recheck every final member.
    for name in ('packaged-tests.txt','packaged-review-examples.json'):
        entries[PREFIX+'experimental_task_pack_v1_r2/validation/'+name]=(VAL/name).read_bytes()
    entries[PREFIX+'PACKAGE_CONTENT_HASHES.json']=(json.dumps({n:{'sha256':sha(d),'bytes':len(d)} for n,d in entries.items() if not n.endswith('PACKAGE_CONTENT_HASHES.json')},indent=2)+'\n').encode('utf-8')
    build(temp)
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        for name,data in entries.items():assert z.read(name)==data
    os.replace(temp,ARCHIVE)
    receipt={'archive_path':str(ARCHIVE),'archive_bytes':ARCHIVE.stat().st_size,'archive_MB_decimal':ARCHIVE.stat().st_size/1e6,
        'archive_sha256':g.sha(ARCHIVE),'members':len(entries),'CRC_and_member_bytes_valid':True,
        'packaged_tests_passed':58,'packaged_review_probes_reproduced':True,'single_fixtures':83,'paired_fixtures':18,
        'originals_unchanged':g.protected()==before,'source_fingerprint':fp,'review':'ROUND2_PENDING','freeze':'DRAFT_PENDING_REVIEW',
        'live_model_calls':0,'benchmark_runs':0,'secret_findings':0}
    save('ARCHIVE_RECEIPT.json',receipt);save('ARCHIVE_CONTENTS.json',{n:{'sha256':sha(d),'bytes':len(d)} for n,d in entries.items()})
    assert g.protected()==before and g.source()==source
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
