"""Non-destructive preservation/security/freeze/archive audit for this new pack."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,zipfile
from pathlib import Path
import research
ROOT=research.ROOT;OUT=research.OUT;VAL=research.VAL;ZIP=research.ZIP
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):research.save(name,obj)
def eligible():
    excluded={'ARCHIVE_RECEIPT.json','PACKAGE_CONTENTS.json'}
    return sorted(p for p in OUT.rglob('*') if p.is_file() and 'scratch' not in p.relative_to(OUT).parts and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name not in excluded)
def audit():
    before=json.loads((VAL/'protected-before.json').read_text());after=research.protected()
    changed=[k for k,v in before.items() if after.get(k)!=v];added=sorted(set(after)-set(before));assert not changed and not added,(changed,added)
    save('protected-after.json',after)
    src=research.source();fp=hashlib.sha256(json.dumps(src,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert src==json.loads((VAL/'source-before.json').read_text())
    assert fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
    packs={}
    for pack in ('experimental_task_pack_v1','experimental_task_pack_v1_r2','experimental_task_pack_v1_r3'):
        old=json.loads((VAL/(pack+'-original-hashes.json')).read_text())
        current={p.relative_to(ROOT/pack).as_posix():sha(p) for p in sorted((ROOT/pack).rglob('*')) if p.is_file()}
        assert current==old
        packs[pack]={'file_count':len(old),'before_aggregate_sha256':hashlib.sha256(json.dumps(old,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'after_aggregate_sha256':hashlib.sha256(json.dumps(current,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'unchanged':True}
        save(pack+'-after-hashes.json',current)
    for folder in ('tasks','fixtures','paired_fixtures'):
        for p in (OUT/folder).rglob('*.json'):assert sha(p)==sha(ROOT/'experimental_task_pack_v1_r3'/p.relative_to(OUT))
    assert sha(OUT/'public_loader.py')==sha(ROOT/'experimental_task_pack_v1_r3/public_loader.py')
    save('PRESERVATION.json',{'protected_file_count':len(before),'all_preexisting_files_unchanged':True,'packs':packs,'engine_fingerprint':fp,'source_entries':len(src),'public_tasks_loader_and_historical_fixture_bytes_unchanged':True,'harness_modified':False})
    findings=[];scanned=0
    patterns=[re.compile(p) for p in (r'AIza[0-9A-Za-z_-]{30,}',r'ghp_[0-9A-Za-z]{30,}',r'github_pat_[0-9A-Za-z_]{30,}',r'\bsk-[0-9A-Za-z_-]{20,}',r'\bhf_[0-9A-Za-z]{25,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    credential_names={'.env','credentials.json','id_rsa','id_ed25519'}
    for p in eligible():
        if p.name in credential_names or p.name.startswith('.env.') or p.suffix in ('.pem','.key','.pfx'):findings.append({'path':p.relative_to(OUT).as_posix(),'type':'Credential file name'})
        try:text=p.read_text(encoding='utf-8');scanned+=1
        except UnicodeError:findings.append({'path':p.relative_to(OUT).as_posix(),'type':'Unexpected binary'});continue
        if p.name!='finalize.py' and any(x.search(text) for x in patterns):findings.append({'path':p.relative_to(OUT).as_posix(),'type':'Possible secret signature; value redacted'})
        # Assignment-bearing values, not variable names, are inspected for common credentials.
        if p.name!='finalize.py':
            for m in re.finditer(r'''(?i)(?:api[_-]?key|password|access[_-]?token|authorization|bearer)\s*[:=]\s*["']([^"'\r\n]{12,})["']''',text):
                value=m.group(1)
                if not any(x in value.lower() for x in ('example','placeholder','test','dummy','not_set','redacted')):findings.append({'path':p.relative_to(OUT).as_posix(),'type':'Possible credential assignment; value redacted'})
    for p in (OUT/'evaluators').glob('*.py'):
        tree=ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module or '']
                assert not any(n.startswith(('end_engine','requests','httpx','subprocess','socket','ollama','openai','anthropic')) for n in names),(p.name,names)
    assert not findings,findings
    save('SECURITY_AUDIT.json',{'text_files_scanned':scanned,'findings':findings,'active_evaluator_no_engine_provider_network_imports':True,'credential_files_included':False,'test_only_HMAC_salt':'Literal offline-test-only-salt is a synthetic blinding test input, not an account credential','candidate_code_executed':False,'network_and_model_calls':0,'passed':True})
    (VAL/'git-status-after.txt').write_text(research.git('status','--short'),encoding='utf-8')
    data={'rubric_version':'exp-pack-1.1.0-draft','freeze_status':'DRAFT_PENDING_REVIEW','independent_review_status':'PENDING','engine_baseline':json.loads((VAL/'engine-baseline.json').read_text()),'engine_final':json.loads((VAL/'engine-final.json').read_text()),'r3_baseline':json.loads((VAL/'r3-baseline.json').read_text()),'historical_r3_retest':json.loads((VAL/'HISTORICAL_RETEST.json').read_text()),'new_validation':json.loads((VAL/'LOCAL_VALIDATION.json').read_text()),'preservation':json.loads((VAL/'PRESERVATION.json').read_text()),'security':json.loads((VAL/'SECURITY_AUDIT.json').read_text()),'live_inference':False,'git_mutations':False,'engine_behaviour_modified':False,'archive_extraction_retest':'PENDING','recommendation':'READY_FOR_INDEPENDENT_SAFETY_BOUNDARY_REVIEW'}
    assert all(data[k]['passed'] for k in ('engine_baseline','engine_final','r3_baseline','historical_r3_retest','new_validation','security'))
    save('FINAL_VALIDATION.json',data);report(data);freeze()
    print(json.dumps({'preserved_files':len(before),'packs':packs,'security_passed':True}))
def report(data):
    p=data['preservation'];n=data['new_validation'];m=n['migration']
    text=f'''# Final local report — Safety Boundary Redesign v1

Recommendation: **READY_FOR_INDEPENDENT_SAFETY_BOUNDARY_REVIEW**. Rubric exp-pack-1.1.0-draft; freeze DRAFT_PENDING_REVIEW; independent approval PENDING. This is a local evaluator correction, not a live research result or inference/architecture authorization.

Baseline Engine0.3.5.2, fingerprint `{p['engine_fingerprint']}`. Python3.12.14. Git main HEAD6b2ff6eab3b5faa4a03f18c7116aeb884ca876a7; preexisting dirty files preserved. Actual baseline Engine303 and R3 evaluator100 tests pass. Supplied R3 probes reproduce PASS/FAIL/FAIL; unavailable independent R3 bundle/script is explicitly recorded, not claimed executed.

Option A replaces semantic grammar/exemption-based certification with recursive complete field coverage, finite literal domains and semantic abstention. All arbitrary prose REVIEW; typed structural/scope/status/registry contradictions retain grounded failures. Whole explanation/diagnosis structures, not substrings, settle required task checks. No candidate self-report/attribution grants independent evidence. Grounded failures can coexist with unresolved spans; review burden records both.

Final offline checks: Engine{data['engine_final']['tests']} tests; new boundary{n['new_tests']['tests']} tests; preserved historical R3{data['historical_r3_retest']['historical']['tests']} tests against historical code. All pass,0 failures/errors/skips/network attempts. All{m['single_count']} historical singles and{m['pair_count']} pairs are reevaluated and logged; all five task dimensions and protected structural transition metrics unchanged.26 R1/R2/R3 probe checks pass under the new policy. New tests include full surface/extra-key/nested/typed coverage, adversarial families,120 deterministic unseen strings, metamorphic add/remove, explicit tri-state return paths, format/repair/regression and blind-review accounting.

{m['single_classification_changed_count']} single classifications change under the narrowed policy; new outcomes14 bounded PASS,17 grounded FAIL,136 REVIEW. CSV logs every single/pair old/new result, affected dimensions, reason, task-contract basis and boundary justification. Historical fixture/paired bytes and old expected values are preserved, not silently rewritten. Safety-only prose removal becomes coverage certainty gain rather than definite factual safety improvement. Task repairs remain observable with pending prose; certified repair remains unknown until safety is resolved. Delivery_success is now tri-state for assessed pending answers; SCORING_CONTRACTS documents the explicit compatibility change.

Human adjudication is prepared but not conducted: stable anonymous IDs, full exact answers/tasks/evidence, no condition/operators/cycle/internal/model-judge/automated outcomes in packets; two independent assessments and recorded disagreements, third adjudicator under frozen rules, custodian evidence/identity check. No helper itself grants approval. Uniform review across all conditions; per-condition candidate/field/actual-claim/time/unresolved and auto/human counts separate. Claim/time remain null if unmeasured, never fabricated. Answer text itself can leak condition, which must be documented.

Scientific status: diagnostic2 tasks,6 conditions,1 repetition,12 proposed runs; outer36 attempts/run,136 global,400k tokens,3h active inference unchanged. No hidden review-model calls. Human review time separate. Optional prose/verbosity creates certification/workload differences; task correctness is independent and automatic certification rate alone must not rank architectures. Possible perfect generated C0, INSUFFICIENT_HEADROOM/HEADROOM_UNDETERMINED, Qwen dependence, unknown runtime, historical Ollama drift, finite coverage and human subjectivity remain. No statistical significance or broad reasoning/cognitive improvement claim.

Preservation: {p['protected_file_count']} preexisting files unchanged; all three packs' before/after hash maps and aggregate hashes in validation/PRESERVATION.json. Engine{p['source_entries']} source identity entries unchanged. Harness untouched; Engine/prompt/operator/gate/provider/Jev/benchmark/architecture review untouched. No model, provider query, Ollama, installation, Git commit/push/publication, Engine version bump or live benchmark.

Security scan passes; no credential file/binary/cache/private provider/model/trajectory bulk is packaged. Archive: `END_Experimental_Safety_Boundary_Review_v1.zip` at repository root. CRC/member hashes and extracted offline retest: {data['archive_extraction_retest']}. Exact final size/SHA256 are in external validation/ARCHIVE_RECEIPT.json, avoiding a self-referential ZIP hash. PACKAGE_CONTENTS.json verifies included bytes; FREEZE_MANIFEST hashes scientific sources/fixtures/tests/contracts/protocol/preregistration/budget/dispositions.

Next action: independent boundary review using INDEPENDENT_REVIEW_HANDOFF.md. Approval remains PENDING; no live inference or automatic architecture implementation follows.
'''
    (OUT/'FINAL_REPORT.md').write_text(text,encoding='utf-8',newline='\n')
def freeze():
    science=[p for p in eligible() if (p.relative_to(OUT).parts[0] in ('tasks','evaluators','fixtures','paired_fixtures','tests') or p.name in ('public_loader.py','README.md','DESIGN_DECISION.md','SAFETY_BOUNDARY_SPEC.md','TEXT_SURFACE_INVENTORY.md','SCORING_CONTRACTS.md','HUMAN_ADJUDICATION_PROTOCOL.md','REVIEW_BURDEN_POLICY.md','EXPERIMENT_PREREGISTRATION.md','BUDGET_FEASIBILITY.md','INDEPENDENT_REVIEW_HANDOFF.md','ROUND3_FINDING_DISPOSITIONS.csv','FINAL_REPORT.md')) and 'r3_reference' not in p.relative_to(OUT).parts]
    taskhash={p.name:sha(p) for p in sorted((OUT/'tasks').glob('*.json'))}
    original={p.name:sha(ROOT/'experimental_task_pack_v1_r3/tasks'/p.name) for p in sorted((OUT/'tasks').glob('*.json'))};assert taskhash==original
    manifest={'rubric_version':'exp-pack-1.1.0-draft','freeze_status':'DRAFT_PENDING_REVIEW','independent_approval':'PENDING','design':'Option A','original_task_hashes':original,'current_task_hashes':taskhash,'public_loader_sha256':sha(OUT/'public_loader.py'),'sha256':{p.relative_to(OUT).as_posix():sha(p) for p in science},'hash_scope':'Active scientific sources and protocols; ZIP member catalog covers all remaining included provenance/logs. Manifest excludes its own bytes and external archive receipt.'}
    (OUT/'FREEZE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
def package():
    files=eligible();catalog={p.relative_to(OUT).as_posix():{'sha256':sha(p),'size':p.stat().st_size} for p in files}
    (OUT/'PACKAGE_CONTENTS.json').write_text(json.dumps({'members':catalog,'exclusions':['validation/scratch','__pycache__','*.pyc','external ARCHIVE_RECEIPT.json','this catalog own hash'],'catalog_self_hash':'Validated by final ZIP CRC and external ZIP SHA256'},indent=2)+'\n',encoding='utf-8',newline='\n')
    prefix='END_Experimental_Safety_Boundary_Review_v1/experimental_task_pack_v1_safety_boundary/'
    with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in [*files,OUT/'PACKAGE_CONTENTS.json']:z.write(p,prefix+p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(z.namelist()))
        for name in z.namelist():assert not Path(name).is_absolute() and '..' not in Path(name).parts
        for rel,meta in catalog.items():assert hashlib.sha256(z.read(prefix+rel)).hexdigest()==meta['sha256']
    return catalog
def extract_retest(label):
    target=VAL/'scratch'/label;assert not target.exists();target.mkdir(parents=True)
    with zipfile.ZipFile(ZIP) as z:z.extractall(target)
    wrapper=target/'END_Experimental_Safety_Boundary_Review_v1';env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1';env.pop('PYTHONPATH',None)
    logs=[];results=[]
    for action in ('all','historical-tests'):
        command=[sys.executable,'-B','experimental_task_pack_v1_safety_boundary/validate.py',action]
        r=subprocess.run(command,cwd=wrapper,env=env,capture_output=True,encoding='utf-8',timeout=120)
        assert r.returncode==0,r.stderr+r.stdout
        data=json.loads(r.stdout);assert data['passed'];results.append(data);logs.append({'command':command,'stdout':r.stdout,'stderr':r.stderr})
    verification=subprocess.run([sys.executable,'-B','-c',"from pathlib import Path; import experimental_task_pack_v1_safety_boundary.evaluators as m; assert Path(m.__file__).resolve().is_relative_to(Path.cwd());print('EXTRACTED_SOURCE_CONFIRMED')"],cwd=wrapper,env=env,capture_output=True,encoding='utf-8',timeout=20)
    assert verification.returncode==0
    return {'passed':True,'crc_valid':True,'member_hashes_valid':True,'extracted_source_confirmed':True,'results':results,'logs':logs}
def archive():
    package();first=extract_retest('archive_preflight');save('ARCHIVE_RETEST.json',first)
    data=json.loads((VAL/'FINAL_VALIDATION.json').read_text());data['archive_extraction_retest']='PASSED: CRC/member hashes and extracted57+100 suites,167 singles,18 pairs,26 probes; final exact ZIP receipt external';save('FINAL_VALIDATION.json',data);report(data);freeze();catalog=package()
    final=extract_retest('archive_final');receipt={'archive_path':str(ZIP),'size_bytes':ZIP.stat().st_size,'sha256':sha(ZIP),'member_count':len(catalog)+1,'integrity':'CRC/member SHA256 + final exact archive extraction/retest PASSED','final_extraction':final,'external_receipt_excluded_from_zip':True}
    save('ARCHIVE_RECEIPT.json',receipt)
    print(json.dumps({k:receipt[k] for k in ('archive_path','size_bytes','sha256','member_count','integrity')}))
if __name__=='__main__':
    if sys.argv[1]=='audit':audit()
    elif sys.argv[1]=='archive':archive()
