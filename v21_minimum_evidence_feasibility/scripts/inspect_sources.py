"""Test-only source census and transparent relocation of existing mock evidence."""
import base64,copy,hashlib,json,os,shutil,sys
from pathlib import Path
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
CHECKOUT=Path('E:/The End Engine/v21_A0_feasibility/checkout')
MOCK=Path('E:/The End Engine/ir101_fix/wiring/mock_wiring')
CONDITIONS=('DIRECT','SELF_REFLECT','FROZEN_CURRENT_END','SPARSE_DELIBERATION','DIRECTED_REPAIR','BOUNDED_ALTERNATIVES')
os.environ['A0_SOURCE_CHECKOUT']=str(CHECKOUT)
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'support/harness'))
import probe_workers as w
from native_model_integration_v1.src.response_decoder.decode import decode
from native_model_integration_v1.src.provider_protocol.wire import SETTINGS
from src.shared.journals import verify_native_records

def read(p):return w.read(Path(p))
def save(p,x):w.write_json(Path(p),x)
def digest(p):return w.sha(Path(p).read_bytes())
def context(root):
 root=Path(root).resolve();ident=read(root/'publication/IDENTITY.json');data=read(root/ident['result_name'])
 ledger=object.__new__(w.Ledger);ledger.path=Path(ident['ledger_path']);ledger.limits=read(ledger.path)['state']['limits']
 assert ledger.path.resolve().is_relative_to(ROOT)
 pub=object.__new__(w.Publication);pub.directory=root;pub.meta=root/'publication';pub.ledger=ledger;pub.identity=ident;pub.identity_sha=w.sha(w.canonical(ident));pub.request=w.RunRequest(**data['request']);pub.effective=w.RunRequest(**data['effective_ledger_request']);pub.mode=ident['mode'];pub.final=root/ident['result_name'];pub.guard=root/'.publication.lock';pub.owner_path=pub.meta/'owner.json';pub.lease_path=pub.meta/'owner.lock';pub.fd=None;pub.fence=None;pub.token=None;pub.detached=False;pub.context=None
 return pub

def relocate(source,target,ledger_source):
 """Derived test fixture; preserves raw input separately, never forges original origin."""
 source=Path(source);target=Path(target);assert not target.exists();shutil.copytree(source,target)
 shutil.copyfile(ledger_source,target/'budget.json');shutil.copyfile(ledger_source.with_suffix('.closed.json'),target/'budget.closed.json')
 shutil.copyfile(ledger_source.with_suffix(ledger_source.suffix+'.lock'),target/'budget.json.lock')
 ident=read(target/'publication/IDENTITY.json');ident.update(output_directory=str(target.resolve()),ledger_path=str((target/'budget.json').resolve()));ih=w.sha(w.canonical(ident));(target/'publication/IDENTITY.json').write_bytes(w.canonical(ident))
 owner=read(target/'publication/owner.json');owner['identity_sha256']=ih;(target/'publication/owner.json').write_bytes(w.canonical(owner))
 for p in (target/'publication/attempts').glob('*.json'):
  x=read(p)
  if 'identity_sha256' in x:x['identity_sha256']=ih;p.write_bytes(w.canonical(x))
 for p in (target/'publication/attempts').glob('*.settlement.json'):
  x=read(p);aid=str(x['attempt_id']).zfill(6);x['dispatch_anchor_sha256']=digest(p.parent/(aid+'.json'));receipt=p.parent/(aid+'.response.json');x['response_anchor_sha256']=digest(receipt) if receipt.exists() else None;p.write_bytes(w.canonical(x))
 pub=context(target);data=read(pub.final);report=w.verify_journals(pub) if pub.mode=='ARCHITECTURE' else verify_native_records(pub,data['provider_records'])
 data['publication_identity_sha256']=ih;data['journal_integrity']=report;data['durable_journal_hashes']=report['trusted_hashes'];data.pop('artifact_payload_sha256',None);data['artifact_payload_sha256']=w.sha(w.canonical(data));raw=(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8');pub.final.write_bytes(raw)
 prepared=target/'publication/prepared'/(data['publication']['token']+'.json');a=read(prepared);a.update(identity_sha256=ih,payload_sha256=data['artifact_payload_sha256'],result_file_sha256=w.sha(raw));prepared.write_bytes(w.canonical(a));w.control(target/'.a0-L2.lock')
 save(target.parent/'RELOCATION.json',{'purpose':'DERIVED_OFFLINE_MOCK_NOT_ORIGINAL_RECORDING_ATTESTATION','source':str(source),'target':str(target),'original_final_sha256':digest(source/ident['result_name']),'derived_final_sha256':digest(pub.final),'modified_scope':'Copied path/identity/anchor consistency metadata and derived provenance report only; prompts, candidate text, algorithm data, settings, limits, source rows unchanged','new_model_calls':0,'new_reservations':0,'original_ledger_sha256':digest(ledger_source),'derived_ledger_sha256':digest(pub.ledger.path)})
 assert digest(ledger_source)==digest(pub.ledger.path)
 return pub

def inspect_condition(condition,archive):
 source=MOCK/('MOCK_EXP-001_'+condition);native=condition in CONDITIONS[:3];final=source/('COMMON_RESULT.json' if native else 'RESULT.json');data=read(final);ident=read(source/'publication/IDENTITY.json');envelope=read(MOCK/'GLOBAL_BUDGET.json');state=envelope['state'];assert w.sha(w.canonical(state))==envelope['state_sha256']
 rows=[a for a in state['attempts'] if a['run_id']==data['request']['run_id']];assert rows==data['result']['model_invocations'];assert len({a['attempt_id'] for a in state['attempts']})==len(state['attempts'])
 dest=archive/source.name;shutil.copytree(source,dest)
 refs={p.relative_to(source).as_posix():{'sha256':digest(p),'bytes':p.stat().st_size} for p in source.rglob('*') if p.is_file()}
 physical=[];wire_hashes=[]
 records=data['provider_records'];assert len(records)==len(rows)
 for index,row in enumerate(rows):
  aid=row['attempt_id'];rec=records[index];purpose=json.loads(row['purpose']);assert digest_bytes(rec['wire'].encode())==rec['wire_sha256'];wire_hashes.append(rec['wire_sha256']);receipt_error=None;receipt=None
  try:receipt=decode(rec['response'].encode('utf-8'),SETTINGS.model) if isinstance(rec.get('response'),str) else None
  except Exception as e:receipt_error={'type':type(e).__name__,'message':str(e)}
  attempts=source/'publication/attempts';dispatch=attempts/(str(aid).zfill(6)+'.json');reservation=attempts/(str(aid).zfill(6)+'.reservation.json');response=attempts/(str(aid).zfill(6)+'.response.json');settlement=attempts/(str(aid).zfill(6)+'.settlement.json')
  raw_ok=receipt is not None and receipt.get('response')==row.get('response_text') and row.get('response_sha256')==digest_bytes(row.get('response_text','').encode('utf-8'))
  usage_known=all(type(row.get(k)) is int and row[k]>=0 for k in ('input_tokens','output_tokens','total_tokens'))
  usage_match=usage_known and receipt is not None and receipt.get('prompt_eval_count')==row['input_tokens'] and receipt.get('eval_count')==row['output_tokens'] and row['input_tokens']+row['output_tokens']==row['total_tokens']
  physical.append({'condition':condition,'task_id':data['request']['task_id'],'run_id':row['run_id'],'attempt_id':aid,'purpose':purpose['purpose'],'source_final':str(final),'source_final_sha256':digest(final),'ledger_path':str(MOCK/'GLOBAL_BUDGET.json'),'ledger_sha256':digest(MOCK/'GLOBAL_BUDGET.json'),'reserved_attempt':'RECORDED_RESERVATION','dispatch_observation':'ORIGINAL_MOCK_TRANSPORT_RECORD' if native else 'ORIGINAL_MOCK_TRANSPORT_AND_DISPATCH_ANCHOR','dispatch_anchor_present':dispatch.exists(),'reservation_witness_present':reservation.exists(),'response_received':receipt is not None,'response_receipt_error':receipt_error,'response_anchor_present':response.exists(),'settled_state':row['state'],'settlement_witness_present':settlement.exists(),'unknown_outcome':row['state']=='RESERVED','input_tokens':row['input_tokens'],'output_tokens':row['output_tokens'],'total_tokens':row['total_tokens'],'usage_origin':'DETERMINISTIC_MOCK_RECEIPT_NOT_MEASURED_PROVIDER','usage_matches_mock_raw_receipt':usage_match,'raw_response_binding_matches':raw_ok,'request_wire_sha256':rec['wire_sha256'],'raw_response_sha256':digest_bytes(rec['response'].encode()) if isinstance(rec.get('response'),str) else None,'candidate_handle':row.get('candidate'),'candidate_lineage':[c for c in data['result']['all_generated_candidates'] if c['attempt_id']==aid],'seconds':row['seconds'],'complete_run_accounting_certified':False,'complete_run_totals':None,'observation_authority':'I_MAXIMUM_NO_COMMON_CUT','native_failure_durability_limit':native})
 summary={'condition':condition,'source':str(source),'source_final':str(final),'raw_final_sha256':digest(final),'source_mode':ident['mode'],'namespace':data['namespace'],'task_id':data['request']['task_id'],'initial_public_payload_sha256':digest_bytes(w.canonical(data['request']['public_task_payload'])),'initial_wire_sha256':wire_hashes[0],'requested':data['request'],'effective':data['effective_ledger_request'],'recorded_reserved_rows':len(rows),'recorded_mock_transport_records':len(records),'recorded_settled_rows':sum(a['state']!='RESERVED' for a in rows),'observed_fixture_input_sum':sum(a['input_tokens'] for a in rows) if all(a['input_tokens'] is not None for a in rows) else None,'observed_fixture_output_sum':sum(a['output_tokens'] for a in rows) if all(a['output_tokens'] is not None for a in rows) else None,'observed_fixture_total_sum':sum(a['total_tokens'] for a in rows) if all(a['total_tokens'] is not None for a in rows) else None,'physical_row_ids':[a['attempt_id'] for a in rows],'independent_reservation_witnesses':sum(p['reservation_witness_present'] for p in physical),'independent_dispatch_anchors':sum(p['dispatch_anchor_present'] for p in physical),'independent_settlement_witnesses':sum(p['settlement_witness_present'] for p in physical),'raw_receipts_consistent':all(p['raw_response_binding_matches'] and p['usage_matches_mock_raw_receipt'] for p in physical),'original_recorded_journal_status':data['journal_integrity']['overall'],'termination_reason':data['result']['termination_reason'],'generation_closed':data['generation_closed'],'initial_candidate':data['result']['initial_candidate'],'final_candidate':data['result']['final_candidate'],'candidate_count':len(data['result']['all_generated_candidates']),'input_file_hashes':refs,'scientific_scores':None,'complete_run_accounting_certified':False,'certified_totals':None}
 return summary,physical
def digest_bytes(raw):return hashlib.sha256(raw).hexdigest()
def main():
 assert not (ROOT/'inputs/original').exists();archive=ROOT/'inputs/original';archive.mkdir(parents=True);summaries=[];physical=[]
 for name in ('GLOBAL_BUDGET.json','GLOBAL_BUDGET.closed.json','GLOBAL_BUDGET.json.lock'):shutil.copyfile(MOCK/name,archive/name)
 for c in CONDITIONS:
  s,p=inspect_condition(c,archive);summaries.append(s);physical+=p
 assert len({s['initial_public_payload_sha256'] for s in summaries})==1 and len({s['initial_wire_sha256'] for s in summaries})==1
 save(ROOT/'source_matrix.json',{'source_commit':'783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e','source_root':str(MOCK),'fixture_task':'EXP-001','generation_runs_executed':0,'all_six_original_initial_wires_identical':True,'conditions':summaries})
 save(ROOT/'_evidence/PHYSICAL_SOURCE_CENSUS.json',physical)
 save(ROOT/'_evidence/ORIGINAL_GLOBAL_LEDGER.json',read(MOCK/'GLOBAL_BUDGET.json'))
 print(json.dumps({'conditions':len(summaries),'existing_mock_reserved_rows_inspected':len(physical),'new_reservations':0,'all_initial_wires_equal':True}),flush=True)
if __name__=='__main__':main()
