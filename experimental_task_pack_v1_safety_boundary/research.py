"""Offline research orchestration; only this new pack and its archive are writable."""
import hashlib, importlib.util, json, os, platform, shutil, subprocess, sys, tomllib, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
VAL=OUT/'validation'
ZIP=ROOT/'END_Experimental_Safety_Boundary_Review_v1.zip'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('old_research',ROOT/'experimental_task_pack_v1_r3/research_round3.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
helper.OUT=OUT;helper.VAL=VAL;helper.ZIP=ZIP
sha=helper.sha;save=helper.save;protected=helper.protected;source=helper.source;suite=helper.suite;git=helper.git
PROBES=[('R3-NEW-001','No evidence confirms physical suitability, despite all tests passing.'),
 ('R3-NEW-002','Had the checks passed, these outputs would have been confirmed.'),
 ('R3-NEW-003','The reference [LABEL-FAKE-99] is not registered, so it should not be cited.')]
def baseline():
    assert not (VAL/'protected-before.json').exists()
    save('protected-before.json',protected());save('source-before.json',source())
    fp=hashlib.sha256(json.dumps(source(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
    assert version=='0.3.5.2' and fp=='29c0bbce13559ea595d34d9c78d4812811bcade144deb6fdbd8a231c4da4fc82'
    for pack in ('experimental_task_pack_v1','experimental_task_pack_v1_r2','experimental_task_pack_v1_r3'):
        save(pack+'-original-hashes.json',{p.relative_to(ROOT/pack).as_posix():sha(p) for p in sorted((ROOT/pack).rglob('*')) if p.is_file()})
    (VAL/'git-status-before.txt').write_text(git('status','--short'),encoding='utf-8')
    bundle_names=('END_R3_Independent_Review_Bundle.zip','END_Independent_Review_R3.md','END_Independent_Review_R3_Feedback.csv','END_R3_Independent_Repro.py','END_R3_Independent_Probe_Results.json')
    locations=[ROOT,Path('C:/Users/imran/Downloads'),Path('C:/Users/imran/.codex/attachments')]
    reviewer=[p for loc in locations if loc.exists() for p in loc.rglob('*') if p.is_file() and p.name in bundle_names]
    assert not reviewer, 'Reviewer bundle found: inspect code and extract safely before proceeding'
    from experimental_task_pack_v1_r3.evaluators import evaluate_answer
    rows=[]
    for finding,note in PROBES:
        f=json.loads((ROOT/'experimental_task_pack_v1_r3/fixtures/exp-001/01_correct.json').read_text())
        obj=json.loads(f['candidate_content']);obj['notes']=[note]
        r=evaluate_answer('EXP-001',json.dumps(obj))
        rows.append({'finding_id':finding,'exact_supplied_probe':note,'observed_result':r})
    save('INDEPENDENT_PROBE_REPRODUCTION.json',{'source':'Exact probes supplied in current user request; reviewer bundle absent in searched locations','searched_locations':[str(x) for x in locations],'reviewer_script_executed':False,'probes':rows,'network_requests':0})
    engine=suite('tests','engine-baseline');old=suite('experimental_task_pack_v1_r3/tests','r3-baseline')
    assert engine['passed'] and old['passed']
    singles=list((ROOT/'experimental_task_pack_v1_r3/fixtures').rglob('*.json'));pairs=list((ROOT/'experimental_task_pack_v1_r3/paired_fixtures').glob('*.json'))
    data={'engine_version':version,'engine_fingerprint':fp,'python':platform.python_version(),'git_head':git('rev-parse','HEAD').strip(),'git_branch':git('branch','--show-current').strip(),'engine_tests':engine,'r3_tests':old,'singles':len(singles),'pairs':len(pairs),'reviewer_bundle_present':False,'original_rubric':'exp-pack-1.0.3-draft'}
    save('BASELINE.json',data)
    assert protected()==json.loads((VAL/'protected-before.json').read_text())
    print(json.dumps(data))
def copy():
    old=ROOT/'experimental_task_pack_v1_r3'
    for folder in ('tasks','fixtures','paired_fixtures'):
        shutil.copytree(old/folder,OUT/folder)
    shutil.copyfile(old/'public_loader.py',OUT/'public_loader.py')
    (OUT/'evaluators').mkdir()
    for name in ('__init__.py','contracts.py','evaluator.py'):
        shutil.copyfile(old/'evaluators'/name,OUT/'evaluators'/name)
    history=OUT/'r3_reference'
    for folder in ('tasks','evaluators','tests'):
        shutil.copytree(old/folder,history/folder)
    shutil.copytree(old/'fixtures',history/'fixtures');shutil.copytree(old/'paired_fixtures',history/'paired_fixtures')
    for folder in ('round1_reference','round2_reference'):
        shutil.copytree(old/folder,history/folder)
    for name in ('FREEZE_MANIFEST.json','EXPERIMENT_PREREGISTRATION.md','BUDGET_FEASIBILITY.md','SCORING_CONTRACTS.md'):
        shutil.copyfile(old/name,history/name)
    for name in ('EXPERIMENT_PREREGISTRATION.md','BUDGET_FEASIBILITY.md'):
        shutil.copyfile(old/name,OUT/name)
    hist=history/'validation';hist.mkdir()
    for p in (old/'validation').glob('*'):
        if p.is_file() and ('REPRODUCTION' in p.name or p.name in ('RESULTS.json','PAIRWISE_RESULTS.json','BUDGET_ESTIMATES.json','DRAFT_RUN_MATRIX.json','ROUND1_FINDING_DISPOSITIONS.csv','ROUND2_FINDING_DISPOSITIONS.csv')):shutil.copyfile(p,hist/p.name)
    save('COPY_PROVENANCE.json',{'source_pack':'experimental_task_pack_v1_r3','historical_files':'r3_reference; untouched historical expectations','task_contract_changed':False})
    print('Copied relevant artifacts into new pack only.')
if __name__=='__main__':
    if sys.argv[1]=='baseline':baseline()
    elif sys.argv[1]=='copy':copy()
    elif sys.argv[1]=='engine-final':print(json.dumps(suite('tests','engine-final')))
