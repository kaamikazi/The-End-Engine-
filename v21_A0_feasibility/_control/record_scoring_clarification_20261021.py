"""Administrative scoring of preserved A0 negatives only. Executes no probes."""
import ast,hashlib,json
from pathlib import Path
E=Path(__file__).resolve().parent.parent
O=E/'scoring_clarification_20261021'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old_manifest=read(E/'_control/EVIDENCE_FILE_HASHES.json')
assert all(sha(E/n)==v['sha256'] for n,v in old_manifest['files'].items()),'PREEXISTING_A0_EVIDENCE_CHANGED'
assert not O.exists(),'NEVER_OVERWRITE_SCORING_RECEIPT'
scores=[]
for attempt in ['attempt_001','attempt_002']:
 saved=E/'runs'/attempt/'executed_scaffolding'
 code=(saved/'test_lock_domain_feasibility.py').read_text(encoding='utf-8')
 ast.parse(code)
 assert 'w.collect(p,timeout=.6)' in code and "ok(time.monotonic()-start<3,'NEGATIVE_SENTINEL_UNBOUNDED');held_and_released(guard)" in code
 executed=read(E/'runs'/attempt/'EXECUTED_SOURCE_RECEIPT.json')
 assert all(sha(saved/n)==h for n,h in executed['new_scaffolding_files'].items())
 for vector,arrangement in [('A0-04','Outer unchanged Ledger.lock followed by Ledger.state reacquiring that same L3'),('A0-05','Outer unchanged dispatch_lock followed by a second acquisition of that same D guard')]:
  source=E/'runs'/attempt/vector/'VECTOR_RESULT.json';r=read(source)
  event=r['observed_events'][0];timeout=Path(event['raw_timeout_receipt']);raw=read(timeout);ready=source.parent/'ready.json';marker=read(ready)
  duration=event['elapsed_seconds'];bounded=(0<=duration<3 and r['elapsed_seconds']<3)
  sentinel=(event['observed']=='EXPECTED_BOUNDED_BLOCKED_SENTINEL' and marker['phase']=='FIRST_LOCK_HELD' and raw['exit_code']==event['actual_exit_code'] and raw['exit_code']!=0)
  cleanup=(r['status']=='PASS' and r['expectation_matched'] and sentinel)
  verdict='PASS' if bounded and sentinel and cleanup else 'FAIL'
  scores.append({'attempt':attempt,'vector_id':vector,
   'observed_event':{'arrangement':arrangement,'readiness':marker,'result':event['observed'],'lock_operation_outcome':'BLOCKED_AND_TERMINATED; no successful recursive acquisition','actual_exit_code':raw['exit_code'],'raw_timeout_receipt':str(timeout)},
   'expected_event':{'required_negative_behavior':'After FIRST_LOCK_HELD, recursive operation does not complete before the timed wait; expected watchdog records timeout, parent terminates/joins child, then the probe reacquires/releases the guard','timed_wait_threshold_seconds':0.6,'overall_sentinel_bound_seconds':3,'unexpected_timeout_wrong_sentinel_or_cleanup_failure':'FAIL'},
   'elapsed_time':duration,'elapsed_time_unit':'seconds','elapsed_time_scope':'Recorded sentinel detection plus parent termination/join; not a separate watchdog-trigger timestamp','whole_vector_elapsed_time':r['elapsed_seconds'],
   'bound_satisfied':bool(bounded),'control_verdict':verdict,
   'feasibility_implication':'The deliberately recursive arrangement exhibited the expected bounded lock hazard. This is not a successful acquisition, does not establish safe production reentrancy, and does not waive unresolved production-deadlock or writer-domain stop conditions.',
   'cleanup_evidence':'The exact saved recursive() source reacquires/releases the guard before returning; its preserved expectation-match PASS establishes that code path returned. No new cleanup experiment or separate timestamp is invented.',
   'timing_limit':'0.6s is the timed-wait threshold; the original explicit end-to-end sentinel assertion is <3s. No claim of an exactly measured 0.6s watchdog-trigger deadline is made.',
   'raw_vector_file':str(source),'raw_vector_sha256':sha(source),'raw_timeout_sha256':sha(timeout),'saved_scaffold_sha256':sha(saved/'test_lock_domain_feasibility.py'),'original_control_status_unchanged':r['status']})
blocker=read(E/'_control/BLOCKER_ANALYSIS.json');latest=read(E/'runs/attempt_002/RUN_RESULT.json');initial=read(E/'runs/attempt_001/RUN_RESULT.json')
assert blocker['verdict']=='A0_FEASIBILITY_BLOCKED' and latest['counts']=={'PASS':19,'FAIL':0,'ERROR':1,'NOT_EXECUTED':0}
assert initial['counts']=={'PASS':10,'FAIL':1,'ERROR':0,'NOT_EXECUTED':9}
report={'date':'2026-10-21','scope':'Approved scoring clarification only; retrospective administrative evidence annotation, no test or source modification','required_fields':['observed_event','expected_event','elapsed_time','bound_satisfied','control_verdict','feasibility_implication'],'records':scores,'counts':{k:sum(x['control_verdict']==k for x in scores) for k in ['PASS','FAIL']},'existing_A0_verdict':'A0_FEASIBILITY_BLOCKED','latest_run_counts_unchanged':latest['counts'],'initial_run_counts_unchanged':initial['counts'],'unwaived_stop':'Actual unenrolled Ledger.register created pending namespace membership under test coordination; A0-18 collector ERROR also remains. Recursive-lock scoring clarification does not resolve these.','new_probe_executions':0,'new_reservations_dispatch_provider_calls':0,'A1_or_production_authorization':'NONE','old_evidence_manifest_sha256':sha(E/'_control/EVIDENCE_FILE_HASHES.json'),'preexisting_evidence_hashes_verified':len(old_manifest['files'])}
O.mkdir()
(O/'A0_NEGATIVE_CONTROL_SCORING.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
lines=['# A0 negative-control scoring clarification — 2026-10-21','','Approved scoring is applied only to preserved recursive-lock negatives A0-04/A0-05 in both attempts. All four satisfy their original explicit bounded-sentinel expectation. Raw evidence, original PASS/FAIL/ERROR/NOT_EXECUTED statuses, source and probe scripts remain unchanged. These are retrospective annotations, not new test executions.','','| Attempt | Vector | Measured sentinel duration (s) | Explicit bound (s) | Control verdict |','|---|---|---|---|---|']
for x in scores:lines.append('| '+x['attempt']+' | '+x['vector_id']+' | '+str(x['elapsed_time'])+' | <3 | '+x['control_verdict']+' |')
lines+=['','The 0.6-second timed-wait threshold and three-second overall sentinel bound are separate. The recorded duration includes termination/join overhead; a separate exact watchdog-trigger timestamp was not recorded and is not invented. Every record contains observed_event, expected_event, elapsed_time, bound_satisfied, control_verdict and feasibility_implication. Expected child exit1/blocked operations remain visible and are not described as successful lock acquisition or safe production reentrancy.','','**A0_FEASIBILITY_BLOCKED remains.** Attempt_002 remains19 PASS/1 ERROR; attempt_001 remains10 PASS/1 FAIL/9 NOT_EXECUTED. The separate real-writer mutation and A0-18 collection error are unresolved. The earlier A0 stop rule for a real writer changing evidence outside the declared domain remains applicable. This scoring-only clarification does not authorize restarting probes across that stop or starting A1.','','All721 previously manifested evidence file hashes were verified unchanged. No new feasibility probes, implementation edits, reservations, dispatches, provider calls, benchmarks, commits or pushes occurred.']
(O/'A0_SCORING_CLARIFICATION.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
manifest={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in O.iterdir() if p.is_file()}
(O/'SCORING_RECEIPT.json').write_text(json.dumps({'files':manifest,'administrative_script':str(Path(__file__)),'administrative_script_sha256':sha(Path(__file__)),'preexisting_evidence_unchanged':all(sha(E/n)==v['sha256'] for n,v in old_manifest['files'].items()),'no_probe_execution':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'scoring_records':len(scores),'counts':report['counts'],'old_evidence_hashes_verified':len(old_manifest['files']),'probe_executions':0,'A0_verdict':'A0_FEASIBILITY_BLOCKED','output':str(O)}))
