"""Post-stop evidence copying and consistency checks only, not probe execution."""
import csv,hashlib,json,shutil
from pathlib import Path
H=Path(__file__).resolve().parent;E=H.parent;C=E/'checkout';F=C/'experimental_architectures_v1_r3/feasibility_v21'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
profile=read(F/'source_profile.json');source=Path(profile['template']);target=E/'inputs/original_synthetic_template';assert not target.exists();target.mkdir(parents=True)
for n,v in profile['template_files'].items():
 original=source/n;assert sha(original)==v['sha256'];out=target/n;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,out);assert sha(out)==v['sha256']
(H/'COPIED_TEMPLATE_RECEIPT.json').write_text(json.dumps({'original':str(source),'copy':str(target),'files':profile['template_files'],'exact_byte_copies':True,'post_stop_action':'administrative preservation only; no copied fixture executed'},indent=2)+'\n',encoding='utf-8')
doc='''# A0 offline reproduction

The actual verdict is A0_FEASIBILITY_BLOCKED. Reproduction is not authorization to start A1 or modify production source. Use a new synthetic output path; existing attempts must never be overwritten. The current scaffold intentionally retains the A0-18 collection error, and its actual raw writer operation also produces pending membership outside the test coordination domain. Its expected overall process exit is1, not a green acceptance run.

Exact second-attempt reproduction on this Windows/NTFS machine:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
$env:A0_SOURCE_CHECKOUT='E:\\The End Engine\\v21_A0_feasibility\\checkout'
& 'C:\\Users\\imran\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -B 'E:\\The End Engine\\v21_A0_feasibility\\runs\\attempt_002\\executed_scaffolding\\probe_runner.py' --output 'E:\\The End Engine\\v21_A0_feasibility\\runs\\independent_reproduction_001'
```

The new output must be inside v21_A0_feasibility/runs and not exist. Native Windows permissions are required for real NTFS share/hard-link/byte-lock behavior; sandbox denial is not a successful native test. This command was NOT executed after the stop. No install/network/model request is needed or permitted. Every parent/child has reservation/dispatch/network tripwires.

For the first preserved failed probe, substitute runs/attempt_001/executed_scaffolding/probe_runner.py and another fresh output path. That exact version retains its incorrect supplemental A0-11 assertion, so it should not be silently called a corrected pass. Its read-only diagnosis is in _control/ATTEMPT_001_DIAGNOSIS.json.

The pinned implementation must remain at783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e and match all246 source manifest entries. Saved source_profile.json identifies the original27-file public/synthetic template and exact hashes. Exact raw copies are also included under inputs/original_synthetic_template with _control/COPIED_TEMPLATE_RECEIPT.json. For a separately relocated independent environment, preserve the pinned checkout and record an explicit profile-only path adaptation to that copied template in the reviewer's own scaffold copy; all original template and implementation hashes must still match. That path adaptation is not falsely described as byte-identical executed profile provenance.

No original research directory should be created/overwritten to emulate an old path. Synthetic setup rebases ONLY new copies and recomputes their path-bound identities/anchors; this is not original recording authentication or a new inference event. All execution source versions, initial failures, child exit/timeout receipts and raw result files remain preserved. No expected rejection is a successful source capture or complete writer-domain proof.
'''
(E/'A0_REPRODUCTION.md').write_text(doc,encoding='utf-8')
required=['A0_FEASIBILITY_REPORT.md','A0_WRITER_COVERAGE.csv','A0_LOCK_ORDER_RESULTS.json','A0_NATIVE_NTFS_RESULTS.json','A0_NONOWNING_READER_RESULTS.json','A0_SOURCE_VERIFIER_RESULTS.json','A0_VECTOR_RESULTS.json','A0_AUTHORITY_DOWNGRADE_MATRIX.csv','A0_SOURCE_PRESERVATION.json','A0_OPEN_BLOCKERS.md','A0_NEXT_SCOPE_DECISION.md']
checks=[]
def check(name,value):checks.append({'check':name,'passed':bool(value)});assert value,name
check('all11 requested deliverables present',all((E/n).is_file() for n in required))
v=read(E/'A0_VECTOR_RESULTS.json');latest=v['latest_rows_VERBATIM'];check('exact20 IDs and raw statuses retained',len(latest)==20 and {r['vector_id'] for r in latest}=={f'A0-{i:02d}' for i in range(1,21)} and v['latest_counts_VERBATIM']=={'PASS':19,'FAIL':0,'ERROR':1,'NOT_EXECUTED':0})
check('original first failure and9 not-executed preserved',read(E/'runs/attempt_001/RUN_RESULT.json')['counts']=={'PASS':10,'FAIL':1,'ERROR':0,'NOT_EXECUTED':9})
check('material pending writer evidence verified',read(H/'BLOCKER_ANALYSIS.json')['pending_sha256']==sha(E/'runs/attempt_002/A0-18/copy/budget.json.pending'))
check('protected source/Git preservation passes',read(E/'A0_SOURCE_PRESERVATION.json')['passed'])
check('new checkout only six authorized files',len(read(E/'A0_SOURCE_PRESERVATION.json')['new_checkout_untracked'].splitlines())==6 and read(E/'A0_SOURCE_PRESERVATION.json')['new_checkout_diff']=='')
executed=read(E/'runs/attempt_002/EXECUTED_SOURCE_RECEIPT.json')['new_scaffolding_files'];check('all6 current scaffold files equal exact second execution version',all(sha(F/n)==h for n,h in executed.items()))
coverage=list(csv.DictReader((E/'A0_WRITER_COVERAGE.csv').open(encoding='utf-8',newline='')));check('40 actual source entries plus unknown actor no false strong coverage',len(coverage)==41 and all(r['strong_domain_proven'].startswith('NO') for r in coverage))
matrix=list(csv.DictReader((E/'A0_AUTHORITY_DOWNGRADE_MATRIX.csv').open(encoding='utf-8',newline='')));check('authority matrix20 onlyIUX noA/S',len(matrix)==20 and all(r['post_stop_R1_feasibility_classification'] in ['I','U','X'] and r['A_or_S_awarded']=='NO' for r in matrix))
child=read(H/'ALL_CHILD_EXIT_RECEIPTS.json');check('23 actual child exits retained including five planned nonzero',child['children_with_recorded_exits']==23 and child['zero_exit']==18 and child['nonzero_exit']==5)
for run in ['attempt_001','attempt_002']:
 result=read(E/'runs'/run/'RUN_RESULT.json');check(run+' parent tripwires zero',all(x==0 for x in result['parent_call_tripwire_counters'].values()))
 for p in (E/'runs'/run).rglob('*.request.result.json'):
  result=read(p);check(run+' child tripwires zero '+p.name,all(x==0 for x in result['counters'].values()))
result={'scope':'POST_STOP_ADMINISTRATIVE_EVIDENCE_CONSISTENCY_ONLY_NOT_PROBE_OR_ACCEPTANCE','passed':True,'checks':checks,'feasibility_verdict':'A0_FEASIBILITY_BLOCKED','control_error_not_reclassified':True,'experiments_after_stop':0,'provider_calls':0,'live_model_calls':0,'new_budget_reservations':0,'benchmarks':0,'no_A1_or_production_implementation':True}
(H/'EVIDENCE_CONSISTENCY.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
paths=[p for p in E.rglob('*') if p.is_file() and not p.is_relative_to(C)] + [F/n for n in executed]
manifest={p.relative_to(E).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths if p.name!='EVIDENCE_FILE_HASHES.json'}
(H/'EVIDENCE_FILE_HASHES.json').write_text(json.dumps({'files':manifest,'purpose':'Local A0 evidence identities; no publication','manifest_excludes_itself':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'required_reports':len(required),'administrative_checks':len(checks),'manifest_files':len(manifest),'manifest_sha256':sha(H/'EVIDENCE_FILE_HASHES.json'),'feasibility_verdict':'A0_FEASIBILITY_BLOCKED'}))
