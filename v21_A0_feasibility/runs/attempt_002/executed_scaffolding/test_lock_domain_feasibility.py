"""Twenty named A0 probe contracts; no historical assertions or runtime features."""
import ast,contextlib,ctypes,os,threading,time,traceback
from pathlib import Path
import probe_workers as w

def ok(cond,message):
 if not cond:raise AssertionError(message)
def refused(action,classes=(TimeoutError,)):
 start=time.monotonic()
 try:action()
 except classes as e:return {'observed':'EXPECTED_REFUSAL','exception':type(e).__name__,'message':str(e),'elapsed_seconds':time.monotonic()-start,'winerror':getattr(e,'winerror',None)}
 raise AssertionError('REQUIRED_REFUSAL_DID_NOT_OCCUR')
def held_and_released(path):
 with w.ExistingLock(path):return {'observed':'ACQUIRED_AND_RELEASED','identity':w.identity(path)}
def result(events,authority='I',blocker=False,**extra):return {'observed_events':events,'authority':authority,'material_blocker':blocker,**extra}
def zero_worker(r):ok(r['exit_code']==0,'WORKER_FAILED:'+str(r));return r
def clean(root):root.mkdir(parents=True,exist_ok=False);return root

def case01(root):
 path=w.control(root/'L1.lock');before=path.read_bytes();parent=w.identity(path);ready=root/'ready.json';release=root/'release';p=w.spawn('lock_hold',root,guard=path,ready=ready,release=release)
 try:
  child=w.wait(ready);negative=refused(lambda:held_and_released(path));ok(negative['elapsed_seconds']<=5,'L1_WAIT_EXCEEDED_BOUND');ok(parent==child['identity'],'L1_FILE_ID_DISAGREES')
 finally:release.write_text('release');exit= w.collect(p)
 zero_worker(exit);ok(before==path.read_bytes(),'GUARD_BYTES_CHANGED');ok(str(path.resolve()) in w.publication_module._LOCAL_LOCKS,'MISSING_CANONICAL_LOCAL_LOCK')
 return result([{'parent_identity':parent,'child':child,'local_key':str(path.resolve())},negative,exit])
def case02(root):
 L2=w.control(root/'shared.L2.lock');one=w.control(root/'runA/L1.lock');two=w.control(root/'runB/L1.lock');before=w.identity(L2);ps=[w.spawn('observer',root,L1=p,L2=L2) for p in (one,two)];rs=[zero_worker(w.collect(p)) for p in ps];intervals=sorted((r['worker_result']['events'][0] for r in rs),key=lambda x:x['enter'])
 ok(intervals[0]['exit']<=intervals[1]['enter'],'COMPETING_OBSERVERS_OVERLAPPED_SHARED_L2');ok(all(x['L2_identity']==before for x in intervals),'SHARED_RESOURCE_IDENTITY_MISMATCH')
 return result([{'two_run_one_ledger_resource':before,'intervals':intervals},*rs])
def case03(root):
 pub=w.clone_fixture(root/'copy');before=w.snapshot(pub.directory)
 with w.ExistingLock(pub.guard),w.ExistingLock(pub.directory/'.a0-L2.lock'):
  state=pub.ledger.state();summary=pub.ledger.summary(pub.request.run_id)
 ok(before==w.snapshot(pub.directory),'READ_MUTATED_SOURCE');return result([{'observed':'UNCHANGED_L3_READS_COMPLETED_WITH_L1_L2_NO_L3_HELD','global_attempt_rows':len(state['attempts']),'own_attempt_rows':summary['physical_attempts']}])
def recursive(root,kind):
 pub=w.clone_fixture(root/'copy');guard=pub.ledger.path.with_suffix(pub.ledger.path.suffix+'.lock') if kind=='L3' else pub.ledger.path.with_suffix('.boundary.lock');ready=root/'ready.json';p=w.spawn('recursive',root,kind=kind,guard=guard,ledger=pub.ledger.path,ready=ready);w.wait(ready);start=time.monotonic()
 try:
  r=w.collect(p,timeout=.6);zero_worker(r);events=r['worker_result']['events'];ok(events and events[0].get('event')=='NATIVE_RECURSION_REFUSED','NATIVE_RECURSION_WAS_ADMITTED; NOT_A_SAFE_OBSERVER_ASSUMPTION')
  event={'observed':'NATIVE_RECURSION_REFUSED','expected_negative':True,'worker':r}
 except Exception as e:
  # collect() already kills on subprocess timeout. Only that exact bounded event is expected.
  if not isinstance(e,w.subprocess.TimeoutExpired):raise
  event={'observed':'EXPECTED_BOUNDED_BLOCKED_SENTINEL','expected_negative':True,'operation_status':'BLOCKED_AND_TERMINATED_NOT_SUCCESSFUL_LOCK_ACQUISITION','elapsed_seconds':time.monotonic()-start,'actual_exit_code':p.returncode,'raw_timeout_receipt':str(p.a0_request.with_suffix('.timeout.json'))}
 ok(time.monotonic()-start<3,'NEGATIVE_SENTINEL_UNBOUNDED');held_and_released(guard)
 return result([event,{'production_observer_order':'L1->L2->ordinary_L3_only; no recursive L3 or D','sentinel_is_not_runtime_deadlock_acceptance':True}])
def case04(root):return recursive(root,'L3')
def case05(root):return recursive(root,'D')
def case06(root):
 from src.shared.session import Session
 constructors={Session.__init__,w.Publication.__init__,w.Ledger.__init__};observed=[]
 def probe_preflight(constructor):
  if constructor in constructors:raise PermissionError('A0_MUTATING_CONSTRUCTOR_REFUSED_BEFORE_CALL')
  raise AssertionError('UNKNOWN_CONSTRUCTOR')
 for f in constructors:observed.append(refused(lambda f=f:probe_preflight(f),(PermissionError,)))
 source=(w.R3/'src/shared/session.py').read_text(encoding='utf-8');tree=ast.parse(source);ok('mkdir' in source and '.gateway.register(' in source,'SOURCE_SIDE_EFFECT_EVIDENCE_MISSING');ok(not any(root.iterdir()),'PREFLIGHT_CREATED_METADATA')
 return result([{'observed':'TEST_PREFLIGHT_REJECTED_MUTATING_CONSTRUCTORS','constructors_executed':0,'source_side_effects':['Session mkdir/Publication init/ledger initialization','gateway registration'],'no_observer_constructor_shortcut':True},*observed],authority='X')
def case07(root):
 p=w.control(root/'L1.lock');owned=threading.Event();release=threading.Event();fail=[]
 def hold():
  try:
   with w.ExistingLock(p):owned.set();ok(release.wait(4),'THREAD_RELEASE_MISSING')
  except BaseException as e:fail.append(str(e))
 t=threading.Thread(target=hold);t.start();ok(owned.wait(3),'THREAD_DID_NOT_ACQUIRE');start=time.monotonic()
 try:r=refused(lambda:held_and_released(p));ok(r['elapsed_seconds']<=5,'THREAD_WAIT_EXCEEDED_BOUND')
 finally:release.set();t.join(3)
 ok(not t.is_alive() and not fail,'THREAD_UNJOINED_OR_FAILED');held_and_released(p);return result([r,{'thread_joined':True,'shared_local_RLock':True,'total_seconds':time.monotonic()-start}])
def case08(root):
 pub=w.clone_fixture(root/'copy');before=w.snapshot(pub.directory);ready=root/'ready.json';release=root/'release';p=w.spawn('live_owner',root,fixture=pub.directory,ready=ready,release=release)
 try:w.wait(ready);r=refused(lambda:held_and_released(pub.guard));ok(r['elapsed_seconds']<=5,'PROCESS_WAIT_EXCEEDED_BOUND');ok(pub.fd is None,'OBSERVER_OWNS_LEASE')
 finally:release.write_text('release');exit=zero_worker(w.collect(p))
 ok(before==w.snapshot(pub.directory),'TEST_LEASE_OR_OBSERVER_CHANGED_SOURCE_OWNER');return result([r,exit,{'live_test_owner_not_stolen':True,'owner_fence_and_all_source_bytes_unchanged':True}])
def case09(root):
 path=w.control(root/'L2.lock');ready=root/'ready.json';release=root/'release';p=w.spawn('lock_hold',root,guard=path,ready=ready,release=release);events=[]
 try:
  w.wait(ready)
  for attempt in range(2):events.append({'attempt':attempt+1,**refused(lambda:held_and_released(path))})
  ok(len(events)==2 and all(x['elapsed_seconds']<=5 for x in events),'BAD_ATTEMPT_OR_WAIT_BOUND')
 finally:release.write_text('release');exit=zero_worker(w.collect(p))
 return result([*events,exit,{'coordination_unavailable':'NO_STRONG_DOMAIN; no third attempt'}])
def case10(root):
 pub=w.clone_fixture(root/'copy');r=w.protected_core(pub);ok(r['core']['passed'],'UNCHANGED_SOURCE_CORE_FAILED:'+str(r['core']));ok(r['opens'],'CORE_FILE_OPEN_AUDIT_EMPTY');return result([r,{'limitation':'Byte-consistent rebased synthetic copy only; no new execution-origin or full writer coverage established'}])
def case11(root):
 pub=w.clone_fixture(root/'corrupt');wire=next((pub.directory/'wire').glob('*.jsonl'));wire.write_bytes(wire.read_bytes()+b'{"extra":true}\n');r=w.protected_core(pub);w.write_json(root/'blocked_core.raw.json',r);ok(not r['core']['passed'] and r['core']['exception']=='RecoveryIntegrityHold','BLOCKED_DID_NOT_CAUSE_GENUINE_F02_REJECTION')
 other=w.clone_fixture(root/'missing_reservation');reservation=next((other.meta/'attempts').glob('*.reservation.json'));saved=reservation.read_bytes();reservation.rename(root/'reservation.preserved');s=w.protected_core(other)
 standalone=w.verify_journals(other);w.write_json(root/'missing_reservation_core.raw.json',s)
 ok(standalone['overall']=='VERIFIED' and standalone['provenance_graph']['overall']=='VERIFIED','STANDALONE_OPTIONAL_RESERVATION_BEHAVIOR_CHANGED')
 ok(not s['core']['passed'] and s['core']['exception']=='ArtifactIntegrity' and s['core']['message']=='PROPOSED_PROVENANCE_REPORT_NOT_CURRENT','COMPLETED_SOURCE_MUST_REJECT_CHANGED_BOUND_REPORT');ok(not reservation.exists(),'OBSERVER_REPAIRED_MISSING_RESERVATION')
 return result([r,{'missing_reservation_source_core':s,'standalone_graph_verified_is_not_completed_source_verification':True,'reservation_preserved_sha256':w.sha(saved),'new_A_forbidden':True,'prospective_S_only_if_full_domain_cut_independently_proved':True,'actual_authority_maximum':'I'}])
def case12(root):
 missing=root/'missing.lock';empty=root/'empty.lock';empty.write_bytes(b'');before=w.snapshot(root);r=[refused(lambda p=p:held_and_released(p),(FileNotFoundError,)) for p in (missing,empty)];ok(before==w.snapshot(root),'MISSING_OR_EMPTY_GUARD_INITIALIZED');return result(r,authority='X')
def case13(root):
 p=root/'data.txt';p.write_bytes(b'ORIGINAL');before=p.read_bytes()
 with w.Pins([p]) as pins:
  child=zero_worker(w.collect(w.spawn('mutate',root,target=p,operations=['write','delete'])));events=child['worker_result']['events'];ok(all(x['outcome']=='DENIED' for x in events),'NATIVE_PIN_DID_NOT_DENY_WRITE_DELETE');ok(p.read_bytes()==before,'PINNED_BYTES_CHANGED');fact=pins.facts[0]
 p.write_bytes(b'AFTER_RELEASE');ok(p.read_bytes()==b'AFTER_RELEASE','PIN_HANDLES_LEAKED');return result([child,{'pin_identity':fact['identity'],'captured_sha256':fact['sha256'],'post_release_write_succeeds':True}])
def case14(root):
 wire=root/'wire';wire.mkdir();p=wire/'registered.txt';p.write_bytes(b'PINNED');target=wire/'orphan.tmp';before={x.name for x in wire.iterdir()}
 with w.Pins([p]):r=zero_worker(w.collect(w.spawn('mutate',root,target=target,operations=['write'])));after={x.name for x in wire.iterdir()};ok(after-before=={'orphan.tmp'},'NEW_MEMBER_NOT_OBSERVED')
 oldid=w.identity(target);oldhash=w.sha(target.read_bytes());r2=zero_worker(w.collect(w.spawn('mutate',root,target=target,operations=['replace'])));newid=w.identity(target);ok(oldid['file_index']!=newid['file_index'],'REPLACEMENT_FILE_ID_NOT_DETECTED');target.rename(wire/'orphan.preserved');removed={x.name for x in wire.iterdir()};ok('orphan.tmp' not in removed,'REMOVED_NAME_NOT_DETECTED')
 return result([r,{'observed':'PINS_DO_NOT_FREEZE_NAMESPACE','added':sorted(after-before),'old_identity':oldid,'new_identity':newid,'old_hash':oldhash,'removed_registered_name':'orphan.tmp','test_had_no_claimed_cooperative_domain':True},r2],authority='U')
def case15(root):
 pub=w.clone_fixture(root/'copy');lock=pub.ledger.path.with_suffix(pub.ledger.path.suffix+'.lock');before=w.snapshot(pub.directory)
 with w.Pins([pub.ledger.path]):ordinary=pub.ledger.state()
 with w.Pins([lock]):denied=refused(pub.ledger.state,(OSError,))
 ok(w.snapshot(pub.directory)==before,'OPERATIONAL_LOCK_TEST_CHANGED_SOURCE');again=pub.ledger.state();ok(ordinary==again,'L3_NOT_REUSABLE_AFTER_PIN_RELEASE');return result([{'ordinary_L3_read_with_data_pin':'PASS','L3_control_lock_excluded_from_data_pins':True},denied])
def case16(root):
 L1=w.control(root/'L1.lock');L2=w.control(root/'L2.lock');data=root/'data.txt';data.write_bytes(b'ORIGINAL');events=[]
 for boundary in range(4):
  try:
   with contextlib.ExitStack() as stack:
    if boundary>=1:stack.enter_context(w.ExistingLock(L1))
    if boundary>=2:stack.enter_context(w.ExistingLock(L2))
    if boundary>=3:stack.enter_context(w.Pins([data]))
    raise KeyboardInterrupt('A0_INJECTED_ACQUISITION_INTERRUPTION')
  except KeyboardInterrupt:events.append({'boundary':boundary,'observed':'EXPECTED_INTERRUPTION_CLEANED_UP'})
  held_and_released(L1);held_and_released(L2);data.write_bytes(b'ORIGINAL')
 pinfailure=refused(lambda: w.Pins([data,root/'missing.data']).__enter__(),(OSError,));data.write_bytes(b'ORIGINAL')
 ready=root/'ready.json';p=w.spawn('kill_holder',root,L1=L1,L2=L2,target=data,ready=ready);w.wait(ready);dead=w.collect(p,kill=True);ok(dead['exit_code']!=0,'KILLED_CHILD_REPORTED_ZERO');held_and_released(L1);held_and_released(L2);data.write_bytes(b'AFTER_KILL');events.extend([pinfailure,dead,{'actual_killed_holder_resources_reacquired':True}]);return result(events)
def case17(root):
 gate=w.control(root/'ADMISSION.lock');L1=w.control(root/'L1.lock');L2=w.control(root/'L2.lock');target=root/'data.txt';target.write_bytes(b'BEFORE');first_ready=root/'first.ready.json';first_done=root/'first.done.json';second_ready=root/'second.ready.json';second_done=root/'second.done.json'
 first=w.spawn('admitted_writer',root,gate=gate,L1=L1,target=target,ready=first_ready,finished=first_done);w.wait(first_ready);events=[]
 with w.ExistingLock(gate):
  second_attempt=root/'second.attempting.json';second=w.spawn('admitted_writer',root,gate=gate,L1=L1,target=target,ready=second_ready,finished=second_done,attempting=second_attempt);w.wait(second_attempt);exit1=zero_worker(w.collect(first));w.wait(first_done);ok(not second_ready.exists(),'NEW_ADMISSION_NOT_EXCLUDED');events.append({'phase':'FIRST_DRAINED_FINALLY_COMPLETE_BEFORE_CAPTURE_LOCKS','pid':first.pid,'new_writer_admission_attempt_observed':True})
  with w.ExistingLock(L1),w.ExistingLock(L2),w.Pins([target]):ok(not second_ready.exists(),'NEW_WRITER_ADMITTED_DURING_TEST_CUT');events.append({'phase':'CONTROLLED_TEST_CUT_HELD','bytes_sha256':w.sha(target.read_bytes())})
  ok(not second_ready.exists(),'ADMISSION_RELEASED_BEFORE_E')
 exit2=zero_worker(w.collect(second));w.wait(second_done);events.extend([exit1,exit2,{'scope':'TWO_EXPLICITLY_COOPERATING_TEST_PARTICIPANTS_ONLY_NOT_ALL_WRITER_COVERAGE','complete_domain_proven':False}]);return result(events)
def case18(root):
 pub=w.clone_fixture(root/'copy');gate=w.control(root/'ADMISSION.lock');before=w.snapshot(pub.directory);before_rows=len(pub.ledger.state()['attempts'])
 with w.ExistingLock(gate),w.ExistingLock(pub.guard),w.ExistingLock(pub.directory/'.a0-L2.lock'),w.Pins(w.data_paths(pub.directory)):
  r=zero_worker(w.collect(w.spawn('register_bypass',root,fixture=pub.directory)));after=w.snapshot(pub.directory)
 additions=sorted(set(after)-set(before));changed=sorted(n for n in before if after.get(n)!=before[n]);event=r['worker_result']['events'][-1];ok(event['pending_created'] or event['ledger_before']!=event['ledger_after'],'UNCHANGED_DIRECT_WRITER_DID_NOT_REACH_UNENROLLED_MUTATION');ok(event['attempt_rows_after']==before_rows,'A0_RESERVED_ATTEMPT')
 return result([r,{'observed':'REAL_UNENROLLED_LEDGER_REGISTER_BYPASSES_TEST_ADMISSION_L1_L2','added_members':additions,'changed_members':changed,'pins_protect_existing_data_not_new_pending_names':True,'stop_rule_triggered':True,'strong_domain_proven':False,'supported_original_attempt_facts_retained':True}],authority='U',blocker=True,blocker_reason='Actual unchanged Ledger.register produced content or new pending membership while proposed test coordination guards were held. No complete writer enrollment/exclusion proof; A/S disabled. This is not a claim of a new F01 certification bypass or malicious-host resistance requirement.')
def case19(root):
 pub=w.clone_fixture(root/'copy');blueprint=w.read(pub.final);w.write_json(root/'blueprint.json',blueprint);saved=root/'preserved_prior_copy';saved.mkdir();pub.final.rename(saved/'RESULT.json')
 for p in (pub.meta/'prepared').glob('*.json'):p.rename(saved/p.name)
 ready=root/'ready.json';go=root/'go';entered=root/'finish.entered.json';p=w.spawn('finalize',root,fixture=pub.directory,blueprint=root/'blueprint.json',ready=ready,go=go,finish_entry=entered);w.wait(ready)
 with w.ExistingLock(pub.guard):go.write_text('go');w.wait(entered);ok(not pub.final.exists(),'FINALIZER_NOT_SERIALIZED_ON_L1')
 r=zero_worker(w.collect(p));ok(pub.final.exists(),'VALID_FINALIZER_DID_NOT_PUBLISH');ok(len(list((pub.meta/'prepared').glob('*.json')))==1,'NOT_EXACTLY_ONE_NEW_PREPARED');source_before=pub.final.read_bytes();ctx=w.context(pub.directory);observed=w.protected_core(ctx);ok(observed['core']['passed'],'OBSERVER_CORE_REJECTED_VALID_FINAL');ok(pub.final.read_bytes()==source_before,'OBSERVER_CHANGED_FINAL');ok(r['worker_result']['events'][0]['script_seen']==[],'PROVIDER_REPLAY');return result([r,observed,{'actual_valid_publication_once':True,'observer_claimed_owner':False}])
def case20(root):
 one=root/'resource.json';two=root/'alias.json';one.write_bytes(b'{}');os.link(one,two);a=w.identity(one);b=w.identity(two);ok(a==b and a['links']>=2,'ACTUAL_HARDLINK_ALIAS_NOT_DETECTED');r=zero_worker(w.collect(w.spawn('duplicate_origin',root)));dup=r['worker_result']['events'][0];ok(dup['same_file'] and dup['distinct_class_identity'] and dup['distinct_lock_maps'],'DUPLICATE_SOURCE_ORIGIN_NOT_REPRODUCED')
 actual_process=w.process_identity(os.getpid());wrong_creation=actual_process['creation_filetime']+1;ok(actual_process['creation_filetime']!=wrong_creation,'STALE_PROCESS_IDENTITY_NOT_REJECTED');epoch=root/'epoch.fixture.json';w.write_json(epoch,{'epoch':0});old=epoch.read_bytes();w.write_json(epoch,{'epoch':1});ok(old!=epoch.read_bytes(),'STALE_EPOCH_FIXTURE_NOT_DISTINGUISHED')
 return result([{'unknown_actor':'NO_STRONG_DOMAIN; lower facts if grounded','actual_alias_identity':a,'alias_paths':[str(one),str(two)],'stale_epoch':'ACTUAL_CHANGED_EPOCH_FILE_REJECTED_AS_SAME_EPOCH; no production capability issued','process_identity':actual_process,'wrong_creation_filetime_rejected':wrong_creation,'PID_reuse':'CREATION_ID_MISMATCH_NEGATIVE; actual OS PID reuse not forced or claimed','candidate_association_if_unsupported':'NONE; X, never fake zero'},r],authority='X')

CASES={f'A0-{i:02d}':globals()[f'case{i:02d}'] for i in range(1,21)}
# Run destructive real-writer fault last; stop immediately when it is observed.
EXECUTION_ORDER=[f'A0-{i:02d}' for i in range(1,18)]+['A0-19','A0-20','A0-18']
