"""Package an explicitly non-accepted correction candidate and reproduce its gate.

No provider APIs, source rewrites, Git history changes or evaluator bulk copies.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
V=OUT/'validation'
CHECKPOINT=V/'scratch/full-validation-02'
VERDICT='FURTHER_PROVENANCE_CORRECTION_REQUIRED'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf8'))
def save(name,value):
    path=V/name
    with path.open('x',encoding='utf8') as stream:json.dump(value,stream,indent=2);stream.write('\n')

def main():
    protected=load(V/'PROTECTED_BEFORE.json')
    changed=[name for name,digest in protected.items() if not (ROOT/name).is_file() or sha(ROOT/name)!=digest]
    if changed:raise RuntimeError('Protected source changed: '+repr(changed))
    exact={}
    for name in ('src/architecture_a/sparse.py','src/architecture_b/repair.py',
                 'src/architecture_c/alternatives.py','src/prompts/registry.py',
                 'src/adapters/gateway.py','src/shared/publication.py',
                 'src/shared/baseline_contract.py','src/shared/strict_json.py',
                 'src/shared/wiring.py','src/shared/evidence.py'):
        exact[name]=sha(OUT/name)==sha(ROOT/'experimental_architectures_v1_r2'/name)
    assert all(exact.values())
    freeze=subprocess.run([sys.executable,'-B',str(ROOT/'experimental_rubric_freeze_v111/verify_frozen_evaluator.py')],capture_output=True,text=True,check=True)
    frozen=json.loads(freeze.stdout)
    assert frozen['passed'] and frozen['frozen_file_count']==725
    assert frozen['scientific_payload_root_sha256']=='23a923ebb224a162ba98c673a9f4f97e8c0571807a893ed72d6a07d65f181a09'
    save('SOURCE_PRESERVATION.json',{'protected_files_checked':len(protected),'changed':changed,
        'protected_r3_copies_byte_identical':exact,'frozen_evaluator':frozen,
        'engine_fingerprint':load(V/'BASELINE_IDENTITY.json')['engine_fingerprint'],
        'scope':'All tracked files in the isolated baseline tree; original source worktrees not executed or edited'})
    regression=V/'regression';regression.mkdir()
    for p in CHECKPOINT.iterdir():
        if p.is_file():
            name='LEGACY_HELPER_SUMMARY.json' if p.name=='FINAL_VALIDATION.json' else p.name
            shutil.copy2(p,regression/name)
    shutil.copytree(CHECKPOINT/'runs',V/'prior_controls')
    summary=load(CHECKPOINT/'FINAL_VALIDATION.json')
    wiring=load(CHECKPOINT/'SIX_CONDITION_WIRING.json');save('SIX_CONDITION_WIRING.json',wiring)
    before=load(V/'BASELINE_REPRODUCTIONS.json')['cases']
    after=load(V/'reproductions_after/RESULTS.json')['cases']
    for label,names in [('AR01',('settlement-downgrade',)),('AR02',('output-handle',)),
                        ('AR03',('duplicate-attempt','reordered-attempts'))]:
        save(label+'_RESULTS.json',{'finding':label,'before':[r for r in before if r['case'] in names],
            'after':[r for r in after if r['case'] in names],
            'status':'LEDGER_MUTATIONS_REJECTED_LOCALLY','remaining_acceptance_blocker':'Y_PUBLICATION_CERTIFICATE_WINDOW'})
    new=load(V/'NEW_CONTROLS.json')
    save('NEGATIVE_CONTROLS.json',{'new_control_summary':new,'log':'NEW_CONTROLS_RUN.txt',
        'unresolved':load(V/'TOCTOU_BLOCKER.json'),'do_not_relabel_failure':True})
    units=load(CHECKPOINT/'TEST_RESULTS.json')['test_results']
    positive=[r for r in units if any(term in r['id'] for term in
        ('complete_C0','correct_missing','A2_better','C0_best','format_repair',
         'provider_failure','unknown_usage','interrupted','repeated_finish','valid_recorded_history'))]
    save('POSITIVE_CONTROLS.json',{'results':positive,'all_passed':all(r['status']=='PASS' for r in positive),
        'actual_synthetic_wiring_cells':wiring['cells_count'],'physical_attempts':wiring['actual_physical_attempts'],
        'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL'})
    save('RECOVERY_RESULTS.json',{'cases':after,'zero_replay':all(r['new_replay_calls']==0 for r in after),
        'bytes_preserved':all(r['independent_evidence_unchanged'] for r in after),
        'publication_blocker':load(V/'TOCTOU_BLOCKER.json')})
    save('F01_F03_F04_REGRESSIONS.json',{name:load(CHECKPOINT/file) for name,file in
        [('F01','CONCURRENCY_RESULTS.json'),('F03','BASELINE_CONTRACT_RESULTS.json'),('F04','NUMERIC_SAFETY_RESULTS.json')]})
    nodes=[{'id':n,'independent_record':ind} for n,ind in
        [('RUN_IDENTITY',True),('PUBLIC_TASK',True),('SEALED_REQUEST',True),('RESERVATION',True),
         ('DISPATCH_ANCHOR',True),('WIRE_JOURNAL',True),('RESPONSE_ANCHOR',True),
         ('SETTLEMENT_WITNESS',True),('MUTABLE_LEDGER',False),('OUTPUT_HANDLE',False),
         ('DERIVED_CANDIDATE_LINEAGE',False),('LATER_CONTROL',True),('GENERATION_CLOSURE',False),('RESULT',True)]]
    edges=[{'from':a,'to':b,'binding':c} for a,b,c in
        [('RUN_IDENTITY','RESERVATION','run/attempt and identity hash'),
         ('RESERVATION','DISPATCH_ANCHOR','attempt identity and sealed purpose'),
         ('SEALED_REQUEST','DISPATCH_ANCHOR','spec/reference-wire/provenance hash'),
         ('DISPATCH_ANCHOR','WIRE_JOURNAL','header digest and wire digest'),
         ('WIRE_JOURNAL','RESPONSE_ANCHOR','tail/raw response digest'),
         ('SETTLEMENT_WITNESS','MUTABLE_LEDGER','exact settlement comparison, not checksum authority'),
         ('RESPONSE_ANCHOR','SETTLEMENT_WITNESS','response anchor digest when available'),
         ('SETTLEMENT_WITNESS','OUTPUT_HANDLE','original candidate/run/task/call/content identity'),
         ('OUTPUT_HANDLE','LATER_CONTROL','prior settled handle and exact compiler reconstruction'),
         ('MUTABLE_LEDGER','DERIVED_CANDIDATE_LINEAGE','unchanged stage kinds and candidate ordering'),
         ('MUTABLE_LEDGER','GENERATION_CLOSURE','derived summary only'),
         ('DERIVED_CANDIDATE_LINEAGE','RESULT','unchanged F01 semantic checks')]]
    save('PROVENANCE_GRAPH.json',{'nodes':nodes,'edges':edges,
        'authority_limit':'Execution witnesses are derived at transaction time, separately stored; not hostile-host proof or provider signatures',
        'publication_window_closed':False})
    primary=load(V/'after/fresh/fresh_results.json')['counts']
    supplemental=load(V/'after/fresh/supplemental_results.json')['counts']
    final={'verdict':VERDICT,'implementation':'1.0.2-candidate','source_commit':load(V/'BASELINE_IDENTITY.json')['commit'],
        'branch':'fix/cognitive-architectures-v102-f02','new_commit':None,'commit_withheld_reason':'Overall acceptance gate fails; protected F01 scope needs authorization',
        'inherited_and_initial_new_unit_run':summary['r2_tests'],
        'final_fresh_controls':new,'previous_49':summary['reviewer_probes'],
        'supplied_acceptance_probes':{'total':primary['total']+supplemental['total'],
            'passed':primary['pass']+supplemental['pass'],'failed':primary['fail']+supplemental['fail'],
            'failure':'JOURNAL_ledger-duplicate-attempt: BLOCKED graph followed by unhandled ArtifactIntegrity; retained as FAIL',
            'scope':'Isolated r3 candidate snapshot; source hashes retained. Final additional wire/admission guard tested in current controls.'},
        'previous_suites':summary['previous_suites'],'mock_wiring_cells':wiring['cells_count'],
        'mock_physical_attempts':wiring['actual_physical_attempts'],
        'protected_source_unchanged':not changed and all(exact.values()),'independent_acceptance':'NOT_PERFORMED',
        'remaining_blocker':'F01 final-link window can leave a VERIFIED certificate although API/later verification reject',
        'live_model_calls':0,'empirical_benchmark_runs':0,'push':False,'merge':False}
    save('FINAL_VALIDATION.json',final)
    report='''# END Cognitive Architectures v1.0.2 Candidate Report

Verdict: **FURTHER_PROVENANCE_CORRECTION_REQUIRED**.

## Baseline And Preservation

Source: 3934971a755db010d6f3e8741bc44cc241040fc9, original algorithms:
d5109d5c898d9b6fcee0dd0198cb5e2e7080cf8a. Engine 0.3.5.2 fingerprint:
29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82.
Evaluator: exp-pack-1.1.1-frozen, 725 files, root
23a923ebb224a162ba98c673a9f4f97e8c0571807a893ed72d6a07d65f181a09.
Prompt registry root: 443ef6ea04bf0fef2b3c74b6f7499dc8e85db6c247a96b91b6fdb9abbbf96683.
Both supplied archive hashes matched. All 5461 tracked baseline paths retain
their starting bytes. Original v1/r2, algorithms, prompts, Engine, Harness and
evaluator were not modified; F01 publication, F03 admission, F04 numeric and
provider/runtime code remain byte-identical in r3 copies.

## Reproduction And Candidate Correction

All three findings were reproduced before implementation. AR01 published a
VERIFIED artifact after losing the sole candidate. AR02 accepted a rebound
handle despite an older sealed request. AR03 falsely verified duplicate and
reordered attempts, before RunResult rejected them. Wire/response anchors were
unchanged. Four final-source reproduction cases now report BLOCKED, preserve
independent evidence and make zero replay calls.

r3 adds execution-time reservation/settlement witnesses and bidirectional graph
checks. It preserves legitimate transport/decoder/protocol failures and unknown
usage. Missing legacy witnesses are never invented. Candidate IDs are derived
under unchanged algorithms; opaque handles are checked against witnesses and
exact later control requests. See the provenance and trust-boundary documents.

## Unresolved Publication Gate And Required Authorization

At the last F01 link, a journal change can leave immutable RESULT.json carrying
VERIFIED, although r3 rejects the API return and later verification. This is an
actual remaining acceptance failure, not a passed negative control. Its exact
artifact and hashes are in validation/TOCTOU_BLOCKER.json. A post-link check
cannot retract an already published certificate without violating F01
immutability. Implementation stopped before changing the protected F01 code.

Requested next scope: authorize a narrowly bounded F01 publication integration
which binds coherent provenance evidence through exclusive publication while
preserving run ownership, fencing, immutable final bytes and zero replay.

## Executed Validation

- Supplied v1.0.1 probes: 154 run, 147 PASS, 7 FAIL, three root causes.
- r3 candidate supplied harness: 154 run, 153 PASS, 1 FAIL. The remaining
  duplicate-ledger harness case now sees BLOCKED, then fails because it assumes
  recovery returns an object rather than raising the integrity hold. It remains
  a recorded FAIL; no scientific assertions were rewritten to force PASS.
- Current new controls: 29 run, 28 PASS, 1 FAIL, no errors/skips. The failing
  assertion is the published-certificate window described above.
- Inherited 170 plus initial 28 additions: 198 PASS; 49 prior controls PASS.
- Unchanged original architecture/native/runtime/laboratory/Engine suites:
  86/53/85/58/303 tests PASS, no failures/errors/skips.
- Synthetic wiring: 12 cells, 82 attempts, identical initial bytes per task
  across all six conditions; native END retains three cycles.
- Frozen preflight and protected-source hashes PASS.

The first native copy-regression launcher inherited an original-root import
path and failed the unchanged origin guard. A clean offline path corrected the
launcher; source/guard/expected outputs were not modified. Earlier trial logs
and the superseded helper summary are retained where available. The copied
legacy validator's PASS/1.0.1 labels are not this report's acceptance verdict.

## Git And Archive

Dedicated branch: fix/cognitive-architectures-v102-f02. HEAD remains the baseline
commit. No correction commit is created while the overall gate is failing.
No staging outside r3, history rewrite, merge or push occurred. The ZIP and
external receipt live under dist/. Receipt records size, SHA-256, member/CRC
validation and actual extracted portable-test outcomes, including failures.

Live model calls: **0**. Empirical benchmark runs: **0**.
MOCK_WIRING_ONLY_NOT_EMPIRICAL. No independent approval is claimed.
'''
    with (OUT/'FINAL_REPORT.md').open('x',encoding='utf8') as stream:stream.write(report)
    # Package only explicit revision material and pinned regression dependencies.
    chosen={}
    excluded={'__pycache__','.git','.venv','node_modules','dist','scratch'}
    for p in OUT.rglob('*'):
        rel=p.relative_to(OUT)
        if not p.is_file() or any(part in excluded for part in rel.parts):continue
        if p.suffix in ('.pyc','.pyo') or p.name.startswith('.env'):continue
        if p.is_symlink():raise RuntimeError('Symlink not admitted')
        chosen['experimental_architectures_v1_r3/'+rel.as_posix()]=p
    dependencies=load(V/'REGRESSION_INPUTS.json')['files']
    for name,digest in dependencies.items():
        p=ROOT/name
        if sha(p)!=digest:raise RuntimeError('Dependency changed: '+name)
        chosen[name]=p
    manifest={name:sha(p) for name,p in sorted(chosen.items())}
    if len({n.casefold() for n in manifest})!=len(manifest):raise RuntimeError('Case collision')
    dist=OUT/'dist';dist.mkdir(exist_ok=True)
    archive=dist/'END_ABC_F02_Provenance_Fixes_v102.zip'
    if archive.exists():raise FileExistsError(archive)
    prefix='END_ABC_F02_v102/'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,p in sorted(chosen.items()):z.write(p,prefix+name)
        z.writestr(prefix+'MEMBER_SHA256.json',json.dumps(manifest,indent=2)+'\n')
    extract=dist/'x'
    extract.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==digest
        z.extractall(extract)
    portable=extract/'END_ABC_F02_v102/experimental_architectures_v1_r3'
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(portable/'validation/offline_guard'))
    runs=[]
    for label,args in [('mutations',['reproduce.py','validation/scratch/extracted-repro']),
                       ('fresh_controls',['-m','unittest','tests.corrections.test_provenance_r3','-v'])]:
        r=subprocess.run([sys.executable,'-B',*args],cwd=portable,env=env,capture_output=True,text=True)
        (dist/('EXTRACTED_'+label+'.txt')).write_text(r.stdout+r.stderr,encoding='utf8')
        runs.append({'suite':label,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    receipt={'verdict':VERDICT,'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),
        'members':len(manifest)+1,'crc':'PASS','member_hashes':'PASS','extracted':str(extract),
        'portable_retests':runs,'live_model_calls':0,'empirical_benchmark_runs':0,
        'note':'Expected known certificate failure remains FAIL; no independent approval'}
    with (dist/'END_ABC_F02_Provenance_Fixes_v102_RECEIPT.json').open('x',encoding='utf8') as stream:
        json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='portable_retests'},indent=2))

if __name__=='__main__':main()
