import dataclasses,importlib.util,json,os,sys,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
from tests_coordination_v1.support import EVIDENCE,NETWORK,request,save,sha,spawn,collect,wait,pin
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger,BudgetStop
from cognitive_architecture_lab_v1.src.accounting.coordination import Coordinator,CoordinationError,CoordinationBusy
import cognitive_architecture_lab_v1.src.accounting.ledger as lm
import cognitive_architecture_lab_v1.src.accounting.coordination as cm

class GuardTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(os.environ['LEDGER_TEST_OUTPUT'])/self._testMethodName;self.root.mkdir(parents=True,exist_ok=False);self.details={};self.children=[]
 def tearDown(self):
  unexpected=[]
  for child in self.children:
   if not child.collected:unexpected.append(collect(child,kill=child.poll() is None))
  save(self.root/'DETAILS.json',{'observations':self.details,'unexpected_child_cleanup':unexpected,'network_attempts':NETWORK});self.assertFalse(unexpected);self.assertFalse(NETWORK)
 def make(self,name='budget.json',**limits):
  p=self.root/name;c=Coordinator.create(p,timeout=.2);l=Ledger(p,coordination=c,**limits);return p,c,l
 def child(self,mode,path,**kw):
  p=spawn(self.root,mode,path,**kw);self.children.append(p);return p
 def test_01_constructor_and_existing_attachment(self):
  p,c,l=self.make();self.assertEqual(l.state()['attempts'],[]);self.assertEqual(c.guard_identity,Coordinator.attach(p).guard_identity);self.assertFalse(p.with_suffix('.json.pending').exists());self.details={'domain_id':c.domain_id,'parent_identity':c.parent_identity,'guard_identity':c.guard_identity,'existing_parent_required':True}
 def test_02_missing_parent_has_no_pre_guard_creation(self):
  missing=self.root/'absent'/'budget.json'
  with self.assertRaisesRegex(CoordinationError,'PARENT_MUST_ALREADY_EXIST'):Coordinator.create(missing)
  self.assertFalse(missing.parent.exists())
 def test_03_wrong_resource_rejected_before_initialization(self):
  p,c,l=self.make();other=self.root/'other.json'
  with self.assertRaisesRegex(CoordinationError,'LEDGER_RESOURCE_MISMATCH'):Ledger(other,coordination=c)
  self.assertFalse(other.exists());self.assertFalse(other.with_suffix('.json.lock').exists())
 def test_04_register_reserve_finish_and_usage_unchanged(self):
  p,c,l=self.make();l.register(request());i=l.reserve('run','synthetic',10,1);self.assertEqual(i,1);self.assertEqual(l.state()['attempts'][0]['state'],'RESERVED');l.finish(i,state='SUCCEEDED',input_tokens=2,output_tokens=3,seconds=.01,response_text='blue',candidate={'candidate_id':'c0'});s=l.summary('run');self.assertEqual((s['physical_attempts'],s['input_tokens'],s['output_tokens'],s['total_tokens']),(1,2,3,5));self.details=s
 def test_05_unknown_usage_still_blocks_next_reservation(self):
  p,c,l=self.make();l.register(request());i=l.reserve('run','synthetic',10,1);l.finish(i,state='FAILED',seconds=.01)
  self.assertIsNone(l.summary('run')['total_tokens'])
  with self.assertRaises(BudgetStop):l.reserve('run','not-replayed',10,1)
 def test_06_global_ceiling_and_shared_runs(self):
  p,c,l=self.make(global_attempts=1);l.register(request('one'));l.register(request('two'));i=l.reserve('one','synthetic',10,1);l.finish(i,state='SUCCEEDED',input_tokens=1,output_tokens=1,seconds=.01)
  with self.assertRaises(BudgetStop):l.reserve('two','synthetic',10,1)
  self.assertEqual(len(l.state()['attempts']),1)
 def test_07_logical_reentry_across_explicit_instances(self):
  p,c,l=self.make();other=Coordinator.attach(p,timeout=.2)
  with c.acquire(),other.acquire():
   another=Ledger(p,coordination=other);another.register(request());self.assertEqual(another.summary('run')['physical_attempts'],0)
  with c.acquire():pass
 def test_08_nonowning_reader_explicitly_enrolled(self):
  p,c,l=self.make();r=object.__new__(Ledger);r.path=p;r.limits=l.limits;r._coordination=Coordinator.attach(p)
  with c.acquire():self.assertEqual(r.state(),l.state())
 def test_09_recursive_l3_rejected_before_native_reacquire(self):
  p,c,l=self.make();start=time.monotonic()
  with l.lock():
   with self.assertRaisesRegex(CoordinationError,'RECURSIVE_OR_REVERSED_L3_ENTRY'):l.state()
  self.assertLess(time.monotonic()-start,1);self.assertEqual(l.state()['attempts'],[])
 def test_10_first_l2_under_legacy_l3_rejected(self):
  p,c,l=self.make();legacy=Ledger(p)
  with legacy.lock():
   with self.assertRaisesRegex(CoordinationError,'LOCK_ORDER_L3_TO_L2_REJECTED'):
    with c.acquire():pass
  with c.acquire():pass
 def test_11_write_cannot_acquire_l2_from_inside_private_helper(self):
  p,c,l=self.make();state=l.state();before=p.read_bytes()
  with self.assertRaisesRegex(CoordinationError,'L2_NOT_OWNED'):l._write(state)
  with c.acquire():
   with self.assertRaisesRegex(CoordinationError,'L3_NOT_OWNED'):l._write(state)
  self.assertEqual(p.read_bytes(),before);self.assertFalse(p.with_suffix('.json.pending').exists())
 def test_12_other_thread_cannot_borrow_ownership(self):
  p,c,l=self.make();state=l.state();observed=[]
  def wrong():
   try:l._write(state)
   except CoordinationError as e:observed.append(e.code)
  with c.acquire():
   t=threading.Thread(target=wrong);t.start();t.join(2);self.assertFalse(t.is_alive())
  self.assertEqual(observed,['L2_NOT_OWNED_BY_CURRENT_THREAD'])
 def test_13_thread_contention_is_bounded(self):
  p,c,l=self.make();observed=[]
  def blocked():
   try:Ledger(p,coordination=Coordinator.attach(p,timeout=.15))
   except CoordinationBusy as e:observed.append(e.code)
  with c.acquire():
   t=threading.Thread(target=blocked);start=time.monotonic();t.start();t.join(2);self.assertFalse(t.is_alive());self.assertLess(time.monotonic()-start,2)
  self.assertEqual(observed,['L2_CONTENTION_DEADLINE']);self.assertEqual(l.state()['runs'],{})
 def test_14_threads_share_domain_and_no_lost_registrations(self):
  p,c,l=self.make();errors=[];barrier=threading.Barrier(5)
  def writer(index):
   try:
    actor=Ledger(p,coordination=Coordinator.attach(p,timeout=3));barrier.wait(3);actor.register(request('thread_'+str(index)))
   except BaseException as e:errors.append(repr(e))
  threads=[threading.Thread(target=writer,args=(i,)) for i in range(4)]
  for t in threads:t.start()
  barrier.wait(3)
  for t in threads:t.join(5)
  self.assertFalse(any(t.is_alive() for t in threads));self.assertFalse(errors);self.assertEqual(len(l.state()['runs']),4);self.details={'registered_threads':4,'errors':errors}
 def contested(self,operation,*,constructor=False,attempt_id=None):
  p=self.root/'budget.json';c=Coordinator.create(p,timeout=.2)
  if not constructor:
   l=Ledger(p,coordination=c);l.register(request())
   if operation=='finish':attempt_id=l.reserve('run','synthetic',10,1)
  before={x.name:sha(x) for x in self.root.iterdir() if x.is_file()};pending=p.with_suffix('.json.pending')
  with c.acquire():
   child=self.child(operation,p,attempt_id=attempt_id);phase=wait(self.root/'attempting.json',child);receipt=collect(child);self.assertEqual(receipt['exit_code'],0);self.assertEqual(receipt['result']['operation_status'],'REJECTED');self.assertEqual(receipt['result']['code'],'L2_CONTENTION_DEADLINE');self.assertFalse(pending.exists())
   for name,digest in before.items():
    if os.path.normcase(str(self.root/name))==os.path.normcase(str(c.guard_path)):
     import hashlib
     owned=c._owned().fd;os.lseek(owned,0,os.SEEK_SET);raw=os.read(owned,os.fstat(owned).st_size);self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
    else:self.assertEqual(sha(self.root/name),digest)
   if constructor:self.assertFalse(p.exists());self.assertFalse(p.with_suffix('.json.lock').exists())
  for name,digest in before.items():self.assertEqual(sha(self.root/name),digest)
  if not constructor:Ledger(p,coordination=c).state()
  self.details={'operation':operation,'attempt_phase':phase,'receipt':receipt,'no_pending_created_while_L2_held':True,'constructor':constructor}
 def test_15_cross_process_constructor_waits_before_l3_or_data(self):self.contested('constructor',constructor=True)
 def test_16_cross_process_register_no_pending_while_excluded(self):self.contested('register')
 def test_17_cross_process_reserve_no_pending_while_excluded(self):self.contested('reserve')
 def test_18_cross_process_finish_no_pending_while_excluded(self):self.contested('finish')
 def test_19_enrolled_process_writes_after_release(self):
  p,c,l=self.make();child=self.child('register',p,run_id='child');receipt=collect(child);self.assertEqual(receipt['exit_code'],0);self.assertEqual(receipt['result']['operation_status'],'RETURNED');self.assertIn('child',l.state()['runs']);self.details=receipt
 def test_20_unenrolled_process_bypasses_domain_and_creates_pending(self):
  p,c,l=self.make();before=p.read_bytes()
  with c.acquire(),pin(p):
   child=self.child('register',p,enrolled=False,run_id='unenrolled');receipt=collect(child);pending=p.with_suffix('.json.pending');self.assertEqual(receipt['exit_code'],0);self.assertEqual(receipt['result']['exception_type'],'PermissionError');self.assertTrue(pending.exists());self.assertIn('unenrolled',json.loads(pending.read_text(encoding='utf-8'))['state']['runs']);self.assertEqual(p.read_bytes(),before)
  self.details={'receipt':receipt,'pending_sha256':sha(pending),'main_sha256':sha(p),'scope':'UNENROLLED_OUTSIDE_GUARANTEE_NO_A_S'}
 def test_21_write_fsync_and_replace_stay_inside_l2_l3(self):
  p,c,l=self.make();pending=p.with_suffix('.json.pending');events=[];real_fsync=lm.os.fsync;real_replace=lm.os.replace
  def sync(fd):c.assert_write(p);self.assertTrue(pending.exists());events.append('PENDING_FLUSHED_WITH_L2_L3');return real_fsync(fd)
  def replace(a,b):c.assert_write(p);self.assertTrue(pending.exists());events.append('REPLACE_WITH_L2_L3');return real_replace(a,b)
  with patch.object(lm.os,'fsync',sync),patch.object(lm.os,'replace',replace):l.register(request())
  self.assertEqual(events,['PENDING_FLUSHED_WITH_L2_L3','REPLACE_WITH_L2_L3']);self.details={'phases':events}
 def test_22_exception_at_fsync_preserves_pending_and_releases(self):
  p,c,l=self.make();before=p.read_bytes()
  with patch.object(lm.os,'fsync',side_effect=OSError('INJECTED_FSYNC_FAILURE')):
   with self.assertRaisesRegex(OSError,'INJECTED_FSYNC_FAILURE'):l.register(request())
  self.assertEqual(p.read_bytes(),before);pending=p.with_suffix('.json.pending');self.assertTrue(pending.exists());self.details={'pending_sha256':sha(pending),'main_unchanged':True}
  with Coordinator.attach(p).acquire():self.assertEqual(l.state()['runs'],{})
 def test_23_replace_failure_preserves_both_files_and_releases(self):
  p,c,l=self.make();before=p.read_bytes()
  with patch.object(lm.os,'replace',side_effect=PermissionError('INJECTED_REPLACE_FAILURE')):
   with self.assertRaisesRegex(PermissionError,'INJECTED_REPLACE_FAILURE'):l.register(request())
  pending=p.with_suffix('.json.pending');saved=pending.read_bytes();self.assertEqual(p.read_bytes(),before)
  with self.assertRaises(FileExistsError):l.register(request('again'))
  self.assertEqual(pending.read_bytes(),saved);self.assertEqual(l.state()['runs'],{});self.details={'pending_sha256':sha(pending),'stale_pending_not_overwritten':True}
 def test_24_stale_pending_blocks_new_optin_write(self):
  p,c,l=self.make();pending=p.with_suffix('.json.pending');pending.write_bytes(b'PRESERVED_STALE_EVIDENCE')
  with self.assertRaises(FileExistsError):l.register(request())
  self.assertEqual(pending.read_bytes(),b'PRESERVED_STALE_EVIDENCE');self.assertEqual(l.state()['runs'],{})
 def test_25_interruption_releases_owned_guards(self):
  p,c,l=self.make()
  with self.assertRaises(KeyboardInterrupt):
   with l.lock():raise KeyboardInterrupt('SYNTHETIC_INTERRUPT')
  l.register(request());self.assertIn('run',l.state()['runs'])
 def test_26_process_termination_releases_l2(self):
  p,c,l=self.make();child=self.child('hold',p);wait(self.root/'ready.json',child);receipt=collect(child,kill=True);self.assertNotEqual(receipt['exit_code'],0)
  with Coordinator.attach(p).acquire():self.assertEqual(l.state()['runs'],{})
  self.details={'terminated_holder':receipt,'guard_reacquired':True}
 def test_27_crash_after_pending_keeps_evidence_and_no_replay(self):
  p,c,l=self.make();before=p.read_bytes();child=self.child('crash_pending',p);phase=wait(self.root/'ready.json',child);receipt=collect(child,kill=True);self.assertNotEqual(receipt['exit_code'],0);pending=p.with_suffix('.json.pending');raw=pending.read_bytes();self.assertEqual(p.read_bytes(),before)
  with Coordinator.attach(p).acquire():self.assertEqual(l.state()['runs'],{})
  with self.assertRaises(FileExistsError):l.register(request('not-replayed'))
  self.assertEqual(pending.read_bytes(),raw);self.details={'phase':phase,'terminated_writer':receipt,'pending_sha256':sha(pending),'main_unchanged':True,'automatic_repair_or_replay':False}
 def test_28_control_missing_is_not_recreated(self):
  p,c,l=self.make();preserved=c.guard_path.with_suffix('.preserved');c.guard_path.rename(preserved)
  with self.assertRaises(FileNotFoundError):l.register(request())
  self.assertFalse(c.guard_path.exists());self.assertTrue(preserved.exists())
 def test_29_empty_control_fails_without_repair(self):
  p=self.root/'budget.json';guard=p.with_name(p.name+'.coordination-v1.lock');guard.write_bytes(b'')
  with self.assertRaisesRegex(CoordinationError,'INVALID_CONTROL_FILE'):Coordinator.attach(p)
  self.assertEqual(guard.read_bytes(),b'');self.assertFalse(p.exists())
 def test_30_control_copy_cannot_rebind_identity(self):
  p,c,l=self.make();other=self.root/'other.json';wrong=other.with_name(other.name+'.coordination-v1.lock');wrong.write_bytes(c.guard_path.read_bytes())
  with self.assertRaises(CoordinationError):Coordinator.attach(other)
  self.assertFalse(other.exists())
 def test_31_actual_hardlink_alias_rejected(self):
  p,c,l=self.make();alias=self.root/'alias.json';os.link(p,alias)
  with self.assertRaisesRegex(CoordinationError,'LEDGER_ALIAS_OR_TYPE_UNSUPPORTED'):Coordinator.create(alias)
  with self.assertRaisesRegex(CoordinationError,'LEDGER_ALIAS_OR_TYPE_UNSUPPORTED'):l.state()
  self.details={'actual_links':p.stat().st_nlink,'file_identity':[p.stat().st_dev,p.stat().st_ino]}
 def test_32_case_alias_uses_same_domain(self):
  p,c,l=self.make();upper=Path(str(p).upper());other=Coordinator.attach(upper);self.assertEqual(c.guard_identity,other.guard_identity)
  with c.acquire():Ledger(upper,coordination=other).register(request())
  self.assertIn('run',l.state()['runs'])
 def test_33_invalid_configuration_has_no_effects(self):
  for value in (True,0,6,float('nan'),float('inf')):
   p=self.root/('invalid_'+str(value)+'.json')
   with self.assertRaises(CoordinationError):Coordinator.create(p,timeout=value)
   self.assertFalse(p.with_name(p.name+'.coordination-v1.lock').exists())
  with self.assertRaises(TypeError):Ledger(self.root/'fake.json',coordination=True)
  self.assertFalse((self.root/'fake.json').exists())
 def test_34_d_then_l2_then_l3_without_recursive_d(self):
  from runtime_isolation_v1.src.trusted_transport.transport import dispatch_lock
  p,c,l=self.make();d=self.root/'D.lock';d.write_bytes(b'0')
  with dispatch_lock(d),c.acquire():l.register(request());self.assertEqual(l.summary('run')['physical_attempts'],0)
  self.details={'actual_order':'D->L2->ordinary_L3','D_primitive_unchanged':True}
 def test_35_legacy_api_and_default_stale_pending_semantics(self):
  p=self.root/'legacy'/'budget.json';l=Ledger(p);self.assertFalse(p.with_name(p.name+'.coordination-v1.lock').exists());pending=p.with_suffix('.json.pending');pending.write_bytes(b'OLD_LEGACY_PENDING');l.register(request());self.assertFalse(pending.exists());self.assertIn('run',l.state()['runs'])
 def test_36_default_does_not_silently_enroll(self):
  p,c,l=self.make()
  with c.acquire(),patch.dict(os.environ,{'END_LEDGER_COORDINATION':'1'}):Ledger(p).register(request('unenrolled'))
  self.assertIn('unenrolled',l.state()['runs']);self.details={'explicit_opt_out_outside_guarantee':True}
 def test_37_legacy_differential_against_pinned_source(self):
  source=Path('E:/The End Engine/v21_A0_feasibility/checkout/cognitive_architecture_lab_v1/src/accounting/ledger.py');name='cognitive_architecture_lab_v1.src.accounting._baseline_reference';spec=importlib.util.spec_from_file_location(name,source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);states=[];errors=[]
  for typ,label in [(module.Ledger,'pinned'),(Ledger,'candidate')]:
   actor=typ(self.root/(label+'.json'));actor.register(request())
   with patch.object(lm.time,'time',return_value=12345):i=actor.reserve('run','fixed',10,1)
   actor.finish(i,state='SUCCEEDED',input_tokens=2,output_tokens=3,seconds=.01,response_text='same',candidate={'candidate_id':'C0'});states.append(actor.state())
   try:actor.register(dataclasses.replace(request(),model_digest='changed'))
   except Exception as e:errors.append((type(e).__name__,str(e)))
  self.assertEqual(states[0],states[1]);self.assertEqual(errors[0],errors[1]);self.details={'exact_state_equality':True,'exception_equality':errors,'baseline_source_sha256':sha(source)}
 def test_38_duplicate_module_origin_rejected(self):
  name='_ledger_guard_duplicate_origin';spec=importlib.util.spec_from_file_location(name,Path(cm.__file__));module=importlib.util.module_from_spec(spec);sys.modules[name]=module
  try:
   spec.loader.exec_module(module)
   with self.assertRaisesRegex(CoordinationError,'DUPLICATE_COORDINATION_MODULE_ORIGIN'):Coordinator.create(self.root/'budget.json')
  finally:sys.modules.pop(name,None)
 def test_39_source_core_l1_l2_l3_and_owner_preserved(self):
  child=self.child('source_core',self.root/'placeholder.json');receipt=collect(child,timeout=15);self.assertEqual(receipt['exit_code'],0,receipt);self.assertEqual(receipt['result']['operation_status'],'SOURCE_CORE_PASS');self.assertTrue(receipt['result']['owner_fence_token_preserved']);self.details=receipt
 def test_40_guard_bootstrap_never_overwrites_existing_control(self):
  p,c,l=self.make();raw=c.guard_path.read_bytes()
  with self.assertRaises(FileExistsError):Coordinator.create(p)
  self.assertEqual(c.guard_path.read_bytes(),raw)
 def test_41_stream_trailing_and_device_names_fail_before_creation(self):
  before={p.name for p in self.root.iterdir()}
  for name in ('budget.json:stream','budget.json ','budget.json.','NUL','CON.json'):
   with self.assertRaisesRegex(CoordinationError,'NONCANONICAL_LEDGER_NAME_UNSUPPORTED'):Coordinator.create(self.root/name)
  self.assertEqual({p.name for p in self.root.iterdir()},before)
