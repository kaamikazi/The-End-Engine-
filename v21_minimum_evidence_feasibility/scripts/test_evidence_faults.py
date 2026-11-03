"""Nine specified data faults; unchanged F02/core verification on new mock copies."""
import argparse,base64,copy,json,shutil,time,traceback
from pathlib import Path
from inspect_sources import ROOT,w,read,save,digest
from native_model_integration_v1.src.response_decoder.decode import decode,ReceiptError
from native_model_integration_v1.src.provider_protocol.wire import SETTINGS
EXPECTED={
 'N03':('BLOCKED','RecoveryIntegrityHold','F02_PROVENANCE_GRAPH_INCONSISTENT_EVIDENCE_PRESERVED'),
 'N04':('INTERRUPTED','ArtifactIntegrity','PROPOSED_PROVENANCE_REPORT_NOT_CURRENT'),
 'N05':('BLOCKED','RecoveryIntegrityHold','F02_PROVENANCE_GRAPH_INCONSISTENT_EVIDENCE_PRESERVED'),
 'N06':('BLOCKED','RecoveryIntegrityHold','F02_PROVENANCE_GRAPH_INCONSISTENT_EVIDENCE_PRESERVED'),
 'N07':('BLOCKED','RecoveryIntegrityHold','F02_PROVENANCE_GRAPH_INCONSISTENT_EVIDENCE_PRESERVED'),
 'N08':('BLOCKED','RecoveryIntegrityHold','F02_PROVENANCE_GRAPH_INCONSISTENT_EVIDENCE_PRESERVED'),
 'N09':('INTERRUPTED','ArtifactIntegrity','PROPOSED_PROVENANCE_REPORT_NOT_CURRENT'),
 'N10':('BLOCKED','RecoveryIntegrityHold','F02_PROVENANCE_GRAPH_INCONSISTENT_EVIDENCE_PRESERVED'),
 'N11':('BLOCKED','RecoveryIntegrityHold','F02_PROVENANCE_GRAPH_INCONSISTENT_EVIDENCE_PRESERVED'),
}
NAMES={'N03':'Missing dispatch receipt','N04':'Missing settlement witness','N05':'Duplicated attempt','N06':'Changed response content','N07':'Unknown token usage','N08':'Incomplete provider-format mock response','N09':'Interrupted outstanding attempt','N10':'Corrupt journal','N11':'Missing candidate binding'}
def write_ledger(pub,envelope):
 envelope['state_sha256']=w.sha(w.canonical(envelope['state']));pub.ledger.path.write_bytes(w.canonical(envelope))
def replace_raw_receipt(pub,wire,mutator):
 items=[json.loads(x) for x in wire.read_bytes().splitlines()];tail=items[-1];raw=json.loads(base64.b64decode(tail['raw_response_base64']));mutator(raw);raw_bytes=w.canonical(raw);tail['response']=raw_bytes.decode();tail['raw_response_base64']=base64.b64encode(raw_bytes).decode();tail['raw_response_sha256']=w.sha(raw_bytes);tail.pop('record_sha256');tail['record_sha256']=w.sha(w.canonical(tail));wire.write_bytes(b'\n'.join(w.canonical(x) for x in items)+b'\n')
 receipt=pub.response_anchor(tail['attempt_id']);x=read(receipt);x['last_sha256']=tail['record_sha256'];x['raw_sha256']=tail['raw_response_sha256'];receipt.write_bytes(w.canonical(x))
 return raw_bytes
def execute(case):
 root=ROOT/'runs/faults'/case;assert not root.exists();root.mkdir(parents=True);start=time.monotonic();record={'case_id':case,'fault':NAMES[case],'control_verdict':'FAIL','expected_event':{'journal_overall':EXPECTED[case][0],'core_exception':EXPECTED[case][1],'core_message':EXPECTED[case][2]},'feasibility_implication':'Invalid/uncertain evidence cannot acquire normal VERIFIED eligibility or certified complete usage. No A/S domain is proven.'}
 try:
  pub=w.clone_fixture(root/'copy');shutil.copytree(pub.directory,root/'pre_fault_copy');wire=next((pub.directory/'wire').glob('*.jsonl'));aid=read(pub.ledger.path)['state']['attempts'][0]['attempt_id'];envelope=read(pub.ledger.path);row=envelope['state']['attempts'][0]
  if case=='N03':pub.attempt_anchor(aid).rename(root/'removed_dispatch.original.json')
  elif case=='N04':(pub.meta/'attempts'/(str(aid).zfill(6)+'.settlement.json')).rename(root/'removed_settlement.original.json')
  elif case=='N05':envelope['state']['attempts'].append(copy.deepcopy(row));write_ledger(pub,envelope)
  elif case=='N06':replace_raw_receipt(pub,wire,lambda raw:raw.update(response=raw['response']+' DELIBERATELY_CHANGED'))
  elif case=='N07':row.update(input_tokens=None,total_tokens=None);write_ledger(pub,envelope)
  elif case=='N08':
   raw=replace_raw_receipt(pub,wire,lambda value:value.update(done=False));save(root/'INCOMPLETE_RAW_BYTES.json',{'raw_base64':base64.b64encode(raw).decode(),'sha256':w.sha(raw)})
   try:decode(raw,SETTINGS.model)
   except ReceiptError as error:record['decoder_rejection']={'type':type(error).__name__,'message':str(error)}
   else:raise AssertionError('INCOMPLETE_RECEIPT_NOT_REJECTED')
   assert record['decoder_rejection']['message']=='provider_receipt_rejected: Incomplete/interrupted nonstreaming receipt'
  elif case=='N09':
   row.update(state='RESERVED',candidate=None,response_text=None,response_sha256=None,input_tokens=None,output_tokens=None,total_tokens=None,seconds=None);write_ledger(pub,envelope);wire.write_bytes(wire.read_bytes().splitlines()[0]+b'\n')
   for path in (pub.response_anchor(aid),pub.meta/'attempts'/(str(aid).zfill(6)+'.settlement.json')):path.rename(root/('removed_'+path.name))
  elif case=='N10':wire.write_bytes(wire.read_bytes()+b'{NOT_VALID_JSON}\n')
  elif case=='N11':row['candidate'].pop('call_id');write_ledger(pub,envelope)
  save(root/'MUTATED_BYTES_BEFORE_VERIFICATION.json',w.snapshot(pub.directory))
  report=w.verify_journals(pub);save(root/'UNCHANGED_JOURNAL_VERIFIER.json',report);core=w.protected_core(pub);save(root/'UNCHANGED_COMPLETED_CORE.json',core)
  state=read(pub.ledger.path)['state'];rows=state['attempts'];known=[a['total_tokens'] for a in rows if type(a.get('total_tokens')) is int]
  observed={'journal_overall':report['overall'],'core_passed':core['core']['passed'],'core_exception':core['core'].get('exception'),'core_message':core['core'].get('message'),'recorded_rows':len(rows),'known_fixture_token_subset':sum(known),'unknown_usage_rows':sum(a.get('total_tokens') is None for a in rows),'outstanding_rows':sum(a['state']=='RESERVED' for a in rows),'certified_complete_totals':None,'normal_verified_returned':core['core']['passed'],'source_bytes_preserved_during_core':core['source_bytes_unchanged']}
  record['observed_event']=observed;save(root/'OBSERVATION.json',observed)
  assert (observed['journal_overall'],observed['core_exception'],observed['core_message'])==EXPECTED[case], 'UNEXPECTED_NEGATIVE_DIAGNOSTIC'
  assert not observed['core_passed'] and observed['source_bytes_preserved_during_core']
  if case in ('N07','N09'):assert observed['unknown_usage_rows']>0 and observed['certified_complete_totals'] is None
  assert not any(w.COUNTERS.values());record['control_verdict']='PASS'
 except BaseException as error:record['error']={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
 finally:
  record['elapsed_time']=time.monotonic()-start;record['bound_seconds']=60;record['bound_satisfied']=record['elapsed_time']<60;record['tripwires']=dict(w.COUNTERS)
  if not record['bound_satisfied']:record['control_verdict']='FAIL'
  save(root/'CONTROL_RESULT.json',record)
 print(json.dumps({'case':case,'verdict':record['control_verdict'],'observed':record.get('observed_event'),'error':record.get('error')}),flush=True)
 return 0 if record['control_verdict']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',choices=EXPECTED,required=True);raise SystemExit(execute(p.parse_args().case))
