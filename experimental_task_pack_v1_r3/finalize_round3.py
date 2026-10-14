"""Copy-only scientific freeze, preservation/security checks and offline R3 ZIP."""
import ast,hashlib,json,os,re,subprocess,sys,zipfile
from pathlib import Path
from experimental_task_pack_v1_r3 import research_round3 as g
ROOT,OUT,VAL,ARCHIVE=g.ROOT,g.OUT,g.VAL,g.ZIP;PREFIX='END_Experimental_Independent_Review_v1_R3/'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(b):return hashlib.sha256(b).hexdigest()
def skip(p):return any(x in ('scratch','__pycache__','.git','.venv','.pytest_cache') for x in p.relative_to(OUT).parts)
START='''# Round3 independent re-review

Active rubric exp-pack-1.0.3-draft; independent recheck PENDING; DRAFT_PENDING_REVIEW. Independent R2 verdict REVISE. All3 reported new defects reproduced before edits in extracted R2; standalone reviewer files absent, exact supplied probes used. Local correction/testing is not independent approval or live authorization.

Read ROUND3_CHANGELOG.md and ROUND2_FINDING_DISPOSITIONS.csv here, then experimental_task_pack_v1_r3/README, FINAL_REPORT, SCORING_CONTRACTS, AMBIGUITY_BOUNDARY and INDEPENDENT_REVIEW_HANDOFF. The complete5-module evaluator includes assertion_scope.py. Both public tasks/loader,83 R2 single labels/content,18 pairs, earlier attribution/criticism/required-repair metrics and12-run/36 outer/136 global/400k/3h limits remain unchanged.

After extraction, from this directory, Python3.11+ standard library (3.12.14 used):

```
python -B -m unittest discover -s experimental_task_pack_v1_r3/tests -t . -v
python -B -m experimental_task_pack_v1_r3.review_examples
```

Use PYTHONDONTWRITEBYTECODE=1/PYTHONUTF8=1. Tests reproduce100 methods and all167 single fixtures/18 pairs, without Engine/model/network installation or candidate code execution. review_examples prints exact old R1/R2 failures using verbatim round1_reference/round2_reference code/tasks, without editing original source. These are historical unapproved baselines, never active scoring authority. Research/authoring/validation/finalization utilities may write files/require the original repository: inspect, do not run against frozen evidence. Return feedback in a separate review copy.

New controls cover hypothetical/main/subordinate assertions and local polarity, quote boundaries, connecting structures, invalid reference warnings/prohibitions/positive use, ordinary negative execution, double negation/exception and unsupported attribution. Mixed asserted test claims cannot inherit an earlier hypothetical exemption. Unresolvable scope abstains rather than gaining definite authority. Citation warnings are mentions, not source support; later positive use remains active. Clear ordinary negative tests receive scoped PASS without becoming execution evidence. See ClauseAssessment spans/scope/ambiguity and final safety violation/review lists; LOCAL_SCOPE_ASSESSED is not PASS.

PASS/FAIL/REVIEW remain distinct; safety review prevents overall True while primary task outcome remains separately visible. Same-author synthetic error counts are not universal semantic accuracy. Complex nested quotation, modifiers, indirect claims, source aliases or discourse contradiction can require manual review. Future review burden is separate from inference cost. All tasks remain finite closed-world and potentially first-answer-ceiling-limited; INSUFFICIENT_HEADROOM and HEADROOM_UNDETERMINED retained, no empirical difficulty/architecture conclusions.

validation/ROUND2_REPRODUCTION_BEFORE/AFTER preserves all exact probes including contradictory status. R2_FIXTURE_REVALIDATION records every prior expectation/result/change/reason/recheck. Original finding statuses RV-001–004 are retained; new finding local resolutions never close independent rechecks. Package member hashes and scientific FREEZE_MANIFEST support byte verification. Archive SHA receipt is outside ZIP to avoid self-reference. No entire Engine repository, credential, environment, cache, weight or historical trajectory is included. Submit R3 only for independent re-review; no model/benchmark/architecture work is authorized.
'''
def main():
    before=load(VAL/'protected-before.json');assert g.protected()==before
    source=g.source();assert source==load(VAL/'source-before.json');base=load(VAL/'BASELINE.json')
    fp=digest(json.dumps(source,sort_keys=True,separators=(',',':')).encode());assert fp==base['engine_fingerprint']
    engine=load(VAL/'engine-final.json');r=load(VAL/'RESULTS.json');assert engine['passed'] and engine['tests']==303 and r['passed'] and r['tests']['tests']==100
    r2=ROOT/'experimental_task_pack_v1_r2';manifest2=load(r2/'FREEZE_MANIFEST.json')
    for pack in ('experimental_task_pack_v1','experimental_task_pack_v1_r2'):
        hashes=load(VAL/(pack+'-original-hashes.json'));assert all(g.sha(ROOT/pack/n)==h for n,h in hashes.items())
    task_hashes={p.stem:g.sha(p) for p in (OUT/'tasks').glob('*.json')};assert task_hashes==manifest2['task_hashes']
    assert g.sha(OUT/'public_loader.py')==g.sha(r2/'public_loader.py')
    assert g.sha(OUT/'evaluators/evaluator.py')==g.sha(r2/'evaluators/evaluator.py')
    assert not r['fixture_label_or_content_changes'];assert len(list((OUT/'fixtures').rglob('*.json')))==167 and len(list((OUT/'paired_fixtures').glob('*.json')))==18
    for p in (OUT/'evaluators').glob('*.py'):
        tree=ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):assert not node.module or not node.module.startswith(('end_engine','socket','subprocess','requests','urllib','typesafe'))
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in ('exec','eval','compile','__import__')
    (VAL/'git-status-after.txt').write_text(g.git('status','--short'),encoding='utf-8',newline='\n')
    assert g.git('rev-parse','HEAD').strip()==base['git_head']
    (VAL/'git-diff-stat.txt').write_text(g.git('diff','--no-ext-diff','--no-textconv','--stat'),encoding='utf-8',newline='\n')
    findings=[]
    for p in OUT.rglob('*'):
        if not p.is_file() or skip(p):continue
        text=p.read_text(encoding='utf-8',errors='replace')
        if p.name.lower().startswith('.env') or p.suffix in ('.pem','.key','.gguf','.pyc'):findings.append(str(p.relative_to(OUT)))
        if any(re.search(pattern,text) for pattern in (r'\bsk-[A-Za-z0-9_-]{20,}',r'\b(?:ghp_|github_pat_|hf_)[A-Za-z0-9_]{20,}',r'\bAIza[A-Za-z0-9_-]{30,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\s]{40,}',r'(?i)(?:authorization|password|client_secret)\s*["\x27]?\s*[:=]\s*["\x27](?:bearer |basic )?[A-Za-z0-9+/_.=-]{16,}["\x27]',r'(?i)C:[\\/]+Users[\\/]+[A-Za-z0-9_. -]+[\\/]')):findings.append(str(p.relative_to(OUT)))
    g.save('SECURITY_AUDIT.json',{'findings':findings,'secret_values_printed':False});assert not findings,'Sensitive artifact; stop without printing values'
    final={'passed':True,'engine_version':'0.3.5.2','engine_fingerprint':fp,'engine_source_unchanged':True,'original_v1_and_R2_byte_identical':True,
        'all_preexisting_files_byte_identical':True,'protected_file_count':len(before),'historical_benchmarks_architecture_review_unchanged':True,'Harness':'Separate project untouched',
        'engine_baseline':base['engine_tests'],'engine_final':engine,'prior_R2_tests':base['r2_evaluator_tests'],'R3_tests':r['tests'],
        'fixtures':167,'R2_fixtures_retained':83,'new_fixtures':84,'paired_transitions':18,'outcomes':r['outcomes'],'expectation_changes':[],
        'tasks_public_loader_repair_metric_source_unchanged':True,'all_reported_findings_reproduced_before_edit':True,
        'local_dispositions':'RESOLVED_LOCALLY','independent_recheck':'PENDING','freeze':'DRAFT_PENDING_REVIEW','rubric':'exp-pack-1.0.3-draft',
        'unresolved_ambiguity':'Bounded grammar abstains; see AMBIGUITY_BOUNDARY; no universal NLP/world-truth claim',
        'budget':{'runs':12,'outer_attempts':36,'global_attempts':136,'tokens':400000,'active_seconds':10800},
        'secrets':0,'live_model_calls':0,'network_inference_calls':0,'benchmarks':0,'commit_push_publication':False,
        'archive_digest':'External ARCHIVE_RECEIPT.json; scientific hashes and member bytes checked independently'}
    g.save('FINAL_VALIDATION.json',final)
    report=f'''# Round3 final report — exp-pack-1.0.3-draft

**Local validation passed; independent recheck PENDING; DRAFT_PENDING_REVIEW.** Independent Round2 verdict REVISE; all3 newly reported defects confirmed locally before edits on extracted R2. Standalone reviewer files absent, exact supplied probes used; no claim of executing an unavailable reviewer script. No final approval or live authorization.

Baseline Engine0.3.5.2, fingerprint `{fp}`, Python{base['python']}, Git main/HEAD `{base['git_head']}`. Engine303 baseline/final pass; prior exp-pack-1.0.2-draft58 pass despite newly reproduced faults. R3 **100 methods pass**,0 failures/errors/skips/network attempts (58 retained+42 added).

R2-NEW-001 HIGH release blocker: R2 accepted hypothetical opening plus later asserted execution/success, including not_executed contradiction. R3 local proposition scope detects those assertions; unsupported embedded/exception/conditional binding reviews. T01–T18 and cross-clause/metamorphic controls pass. This is grammatical scope/modality/quotation separation, not one added conjunction. Remaining complex discourse/indirect claims are outside supported grammar.

R2-NEW-002: citation warning falsely failed while identifier warning passed. Shared reference warning/prohibition grammar now validates registry without inventing endorsement; warning→positive 'it proves' use remains actionable. T19–T22 and noun-swap/pronoun controls pass. Ambiguous use reviews; external reference existence not asserted.

R2-NEW-003: truthful did-not-execute reviewed unnecessarily. Ordinary active/passive/did-not/have-not/performed/carried-out negatives now pass under no-execution contract, without earning verification. Double negation, later positives, external actors/verified results and exceptions cannot silently pass. T23–T25/metamorphic order controls pass.

Original R1 attribution/source/quote controls and R2 explanation/diagnosis/contract/content/safety metrics remain intact; no causal targeting invented. All18 pairs match. All167 singles match: **55 PASS,82 FAIL,30 REVIEW**.83 R2 singles retain candidate content/expected labels/outcomes (25/42/16),84 new cases added. No expectation relabelling. Synthetic error/disagreement counts0 within authored controls, not general semantic accuracy. Unresolved grammar/source review burden explicitly documented, not converted to FAIL.

Both task hashes/public-loader bytes and repair-metric source unchanged. C0 ceiling risk unmeasured; INSUFFICIENT_HEADROOM and HEADROOM_UNDETERMINED retained.12-run proposal/36 outer/136 global/400k tokens/3h unchanged, END not reduced to one cycle. No empirical model/architecture conclusions.

All{len(before):,} preexisting files remain byte-identical, including original v1/R2 packs/manifests/ZIPs, Engine/source/provider/Jev/history/architecture review. Harness untouched; Git HEAD unchanged; existing Git diff inspected and preserved. Secret scan clean. No model/network inference, live benchmark, dependency/model download, architecture implementation, commit/push/publication or Engine bump.

Complete R3 ZIP: `E:\\The End Engine\\END_Experimental_Independent_Review_v1_R3.zip`. Full active implementation, fixtures/tests/contracts/dispositions and historical baseline code for offline review included; no whole Engine, credentials, caches, weights or trajectories. CRC, member bytes/hashes and extracted100-test/probe result checked; exact bytes/size/SHA-256 in external validation/ARCHIVE_RECEIPT.json to avoid self-reference.

Next action: submit Round3 ZIP for independent re-review. Local success is not independent approval.
'''
    (OUT/'FINAL_REPORT.md').write_text(report,encoding='utf-8',newline='\n')
    scientific={p.relative_to(OUT).as_posix():g.sha(p) for p in OUT.rglob('*') if p.is_file() and not skip(p) and
        (p.relative_to(OUT).parts[0] in ('evaluators','tasks','fixtures','paired_fixtures','tests') or p.suffix=='.md' or p.name in ('public_loader.py','RESULTS.json','ROUND2_FINDING_DISPOSITIONS.csv','ROUND1_FINDING_DISPOSITIONS.csv','BUDGET_ESTIMATES.json','DRAFT_RUN_MATRIX.json'))}
    ev={p.name:g.sha(p) for p in (OUT/'evaluators').glob('*.py')}
    manifest={'rubric':'exp-pack-1.0.3-draft','FREEZE_STATUS':'DRAFT_PENDING_REVIEW','INDEPENDENT_RECHECK_STATUS':'PENDING','independently_approved':False,
        'independent_R2_verdict':'REVISE','engine_version':'0.3.5.2','engine_fingerprint':fp,'task_hashes':task_hashes,'public_loader_sha256':g.sha(OUT/'public_loader.py'),
        'evaluator_hashes':ev,'evaluator_bundle_sha256':digest(json.dumps(ev,sort_keys=True,separators=(',',':')).encode()),
        'fixture_hashes':{n:h for n,h in scientific.items() if n.startswith('fixtures/')},'paired_fixture_hashes':{n:h for n,h in scientific.items() if n.startswith('paired_fixtures/')},
        'test_hashes':{n:h for n,h in scientific.items() if n.startswith('tests/')},'scientific_artifact_hashes':scientific,
        'original_v1_manifest_sha256':g.sha(ROOT/'experimental_task_pack_v1/FREEZE_MANIFEST.json'),'R2_manifest_sha256':g.sha(r2/'FREEZE_MANIFEST.json'),
        'tasks_match_R2':True,'R2_fixture_expectation_changes':[],'dependencies':{'python':base['python'],'minimum_python':'3.11','third_party':[]},
        'no_observed_live_outputs':True,'packaging_receipts_excluded_from_scientific_hashes':True,'live_model_calls':0}
    (OUT/'FREEZE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    assert not ARCHIVE.exists(),'Refuse archive overwrite'
    entries={PREFIX+'experimental_task_pack_v1_r3/'+p.relative_to(OUT).as_posix():p.read_bytes() for p in OUT.rglob('*') if p.is_file() and not skip(p) and p.name not in ('ARCHIVE_RECEIPT.json','ARCHIVE_CONTENTS.json')}
    entries[PREFIX+'REVIEW_START_HERE.md']=START.encode()
    entries[PREFIX+'ROUND3_CHANGELOG.md']=(OUT/'ROUND3_CHANGELOG.md').read_bytes()
    entries[PREFIX+'ROUND2_FINDING_DISPOSITIONS.csv']=(VAL/'ROUND2_FINDING_DISPOSITIONS.csv').read_bytes()
    temp=VAL/'archive-building.tmp'
    def build():
        entries[PREFIX+'PACKAGE_MEMBER_HASHES.json']=(json.dumps({n:{'sha256':digest(d),'bytes':len(d)} for n,d in entries.items() if not n.endswith('PACKAGE_MEMBER_HASHES.json')},indent=2)+'\n').encode()
        with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for n,d in sorted(entries.items()):z.writestr(n,d)
    build();extract=VAL/'scratch/extracted_r3';extract.mkdir()
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        for n,d in entries.items():assert z.read(n)==d and not Path(n).is_absolute() and '..' not in Path(n).parts
        z.extractall(extract)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1';env.pop('PYTHONPATH',None);cwd=extract/PREFIX.rstrip('/')
    test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','experimental_task_pack_v1_r3/tests','-t','.','-v'],cwd=cwd,env=env,capture_output=True,encoding='utf-8',timeout=60)
    (VAL/'packaged-tests.txt').write_text(test.stdout+test.stderr,encoding='utf-8',newline='\n');assert test.returncode==0 and 'Ran 100 tests' in test.stderr
    probes=subprocess.run([sys.executable,'-B','-m','experimental_task_pack_v1_r3.review_examples'],cwd=cwd,env=env,capture_output=True,encoding='utf-8',timeout=30);assert probes.returncode==0
    (VAL/'packaged-review-probes.json').write_text(probes.stdout,encoding='utf-8',newline='\n')
    parsed=json.loads(probes.stdout);assert [x['R3_overall'] for x in parsed['results'][:8]]==[False,False,True,True,False,False,True,True]
    for n,d in entries.items():assert (extract/n).read_bytes()==d
    for name in ('packaged-tests.txt','packaged-review-probes.json'):entries[PREFIX+'experimental_task_pack_v1_r3/validation/'+name]=(VAL/name).read_bytes()
    build()
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        for n,d in entries.items():assert z.read(n)==d and z.getinfo(n).file_size==len(d)
        assert not any(any(p in ('__pycache__','.git','.venv') for p in Path(n).parts) for n in z.namelist())
    assert g.protected()==before;os.replace(temp,ARCHIVE)
    receipt={'archive_path':str(ARCHIVE),'bytes':ARCHIVE.stat().st_size,'MB_decimal':ARCHIVE.stat().st_size/1e6,'SHA256':g.sha(ARCHIVE),'members':len(entries),
        'CRC_member_hashes_valid':True,'packaged_tests_passed':100,'packaged_probes_valid':True,'fixture_singles':167,'paired_transitions':18,
        'task_hashes_unchanged':True,'originals_unchanged':g.protected()==before,'review':'R3_PENDING','freeze':'DRAFT_PENDING_REVIEW','secrets':0,'live_model_calls':0,'live_benchmarks':0}
    g.save('ARCHIVE_RECEIPT.json',receipt);g.save('ARCHIVE_CONTENTS.json',{n:{'sha256':digest(d),'bytes':len(d)} for n,d in entries.items()})
    assert g.protected()==before and g.source()==source;print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
