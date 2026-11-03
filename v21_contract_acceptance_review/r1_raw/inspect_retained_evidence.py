"""Reviewer-owned offline, read-only evidence probe. Never imports END runtime."""
from pathlib import Path
import argparse, base64, csv, hashlib, json, math

OUT=Path(r'E:\The End Engine\v21_contract_acceptance_review')
SRC=Path(r'E:\END-v102-V21-Contract-Checkpoint')
DOC=SRC/'experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1'
FIX=Path(r'E:\The End Engine\ca102\own')
args=argparse.ArgumentParser()
args.add_argument('--fixture-root',type=Path,default=FIX)
args.add_argument('--document-root',type=Path,default=DOC)
args.add_argument('--output',type=Path,default=OUT/'r1_raw/RETAINED_EVIDENCE_INSPECTION.json')
options=args.parse_args();FIX=options.fixture_root;DOC=options.document_root
def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def pairs(items):
    d={}
    for k,v in items:
        if k in d: raise ValueError('duplicate-key:'+k)
        d[k]=v
    return d
def load(raw): return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
def read(p): return load(p.read_bytes())
rows=list(csv.DictReader((DOC/'R1_SIXTEEN_CASE_REVALIDATION.csv').open(encoding='utf-8-sig',newline='')))
cases=[]
for proposed in rows:
    name=next(v for k,v in proposed.items() if k.lower() in ('case','case_id','mutation'))
    p=FIX/('ACCOUNT_'+name)
    raw={f.relative_to(p).as_posix():f.read_bytes() for f in p.rglob('*') if f.is_file()}
    identity=read(p/'publication/IDENTITY.json'); identity_sha=sha(canonical(identity))
    envelope=read(p/'budget.json'); state=envelope['state']; own=[a for a in state['attempts'] if a['run_id']==identity['run_id']]
    assert len(own)==1
    row=own[0]; aid=row['attempt_id']; base='publication/attempts/'+str(aid).zfill(6)
    reservation=load(raw[base+'.reservation.json']); dispatch=load(raw[base+'.json']); settlement=load(raw[base+'.settlement.json'])
    intent=load(row['purpose']); spec=load(dispatch['spec'])
    checks={
      'ledger_checksum':envelope['state_sha256']==sha(canonical(state)),
      'global_ids_order_unique':[a['attempt_id'] for a in state['attempts']]==list(range(1,len(state['attempts'])+1)),
      'reservation_identity':reservation['identity_sha256']==identity_sha and reservation['run_id']==identity['run_id'] and reservation['attempt_id']==aid,
      'reservation_original_state':reservation['reservation']['state']=='RESERVED',
      'reservation_row_identity':all(reservation['reservation'][k]==row[k] for k in ('attempt_id','run_id','purpose','token_ceiling','seconds_ceiling','started_unix')),
      'dispatch_identity':dispatch['identity_sha256']==identity_sha and dispatch['run_id']==identity['run_id'] and dispatch['attempt_id']==aid,
      'dispatch_spec_intent':sha(dispatch['spec'].encode())==intent['spec_sha256'] and dispatch['reference_wire_sha256']==intent['wire_sha256'] and dispatch['stage']==intent['purpose']==spec['purpose']==spec['instruction_id'] and dispatch['call_id']==intent['call_id']==spec['call_id'] and spec['run_id']==identity['run_id'] and spec['task_id']==identity['task_id'],
      'settlement_identity':settlement['identity_sha256']==identity_sha and settlement['run_id']==identity['run_id'] and settlement['attempt_id']==aid,
      'settlement_row_full_equality':canonical(settlement['settlement'])==canonical(row),
      'settlement_dispatch_commitment':settlement['dispatch_anchor_sha256']==sha(raw[base+'.json']),
      'registered_response_exists':base+'.response.json' in raw,
      'settlement_registered_response_commitment':base+'.response.json' in raw and settlement['response_anchor_sha256']==sha(raw[base+'.response.json']),
      'candidate_dispatch_binding':row['candidate']['call_id']==dispatch['call_id'] and row['candidate']['task_id']==identity['task_id'] and row['candidate']['wire_sha256']==dispatch['reference_wire_sha256'] and row['candidate']['provenance_sha256']==dispatch['provenance_sha256'],
      'candidate_response_text_digest':sha(row['response_text'].encode())==row['response_sha256'],
    }
    response=load(raw[base+'.response.json']) if checks['registered_response_exists'] else None
    if response:
        checks['response_identity']=response['run_id']==identity['run_id'] and response['attempt_id']==aid and response['stage']==dispatch['stage']
    anchors=json.loads(proposed['INDEPENDENT_WITNESS_REFS']) if 'INDEPENDENT_WITNESS_REFS' in proposed else None
    if anchors is None:
        for key,value in proposed.items():
            if value.startswith('[{"path"'):
                anchors=json.loads(value);break
    ref_checks=[{'path':a['path'],'expected':a['sha256'],'actual':sha(raw[a['path']]),'match':sha(raw[a['path']])==a['sha256']} for a in anchors]
    journals=[]
    for rel,data in raw.items():
        if rel.startswith('wire/'):
            parsed=[];parse_errors=[]
            for i,line in enumerate(data.splitlines()):
                try:parsed.append(load(line))
                except Exception as e:parse_errors.append({'line':i,'error':str(e)})
            wire_checks={'at_most_two_records':len(parsed)<=2,'all_records_strictly_parse':not parse_errors,'record_hashes':True,'index_order':True,'previous_links':True,'record_identity':True}
            previous=None
            for i,item in enumerate(parsed):
                unhashed={k:v for k,v in item.items() if k!='record_sha256'}
                wire_checks['record_hashes'] &= sha(canonical(unhashed))==item.get('record_sha256')
                wire_checks['index_order'] &= item.get('index')==i
                wire_checks['previous_links'] &= item.get('previous_sha256')==previous
                wire_checks['record_identity'] &= item.get('run_id')==identity['run_id'] and item.get('attempt_id')==aid and item.get('stage')==dispatch['stage']
                previous=item.get('record_sha256')
            header=parsed[0] if parsed else {}
            wire_checks['original_header_commitment']=header.get('record_sha256')==dispatch['header_sha256']
            record=header.get('record',{})
            wire_checks['wire_hash_original_commitment']=isinstance(record.get('wire'),str) and sha(record['wire'].encode())==record.get('wire_sha256')==dispatch['wire_sha256']
            tail=parsed[1] if len(parsed)>1 else {}
            wire_checks['original_tail_receipt_commitment']=bool(response) and tail.get('record_sha256')==response['last_sha256']
            try:
                provider=base64.b64decode(tail['raw_response_base64'],validate=True)
                wire_checks['raw_response_byte_commitment']=bool(response) and sha(provider)==tail['raw_response_sha256']==response.get('raw_sha256') and provider.decode('utf-8',errors='replace')==tail['response']
            except Exception:
                wire_checks['raw_response_byte_commitment']=False
            journals.append({'path':rel,'sha256':sha(data),'registered':rel==dispatch['journal_path'],'records':len(parsed),'parse_errors':parse_errors,'checks':wire_checks,'ids':[{'run_id':x.get('run_id'),'attempt_id':x.get('attempt_id'),'stage':x.get('stage'),'index':x.get('index')} for x in parsed],'same_bytes_as_registered':dispatch['journal_path'] in raw and data==raw[dispatch['journal_path']]})
    cases.append({'case':name,'path':str(p),'proposed_refs':ref_checks,'checks':checks,'observed_settlement_usage':{k:settlement['settlement'][k] for k in ('input_tokens','output_tokens','total_tokens','seconds')},'current_row_usage':{k:row[k] for k in ('input_tokens','output_tokens','total_tokens','seconds')},'journals':journals,'inventory':[{'path':k,'sha256':sha(v),'bytes':len(v)} for k,v in sorted(raw.items())],'current_authority':'I_MAXIMUM; no historical R1-GUARDED-CUT-2.1 writer-domain/guard/capture evidence','conditional_authority': 'S_RESERVATION_DISPATCH_ONLY' if name in ('ledger_disagreement','missing_response_anchor') else 'A_ANCHORED_GRAPH_CARDINALITY_1_ONLY_IF_NEW_CUT_AND_ORIGIN_PREREQUISITES_HOLD','full_run_certification':False})
report={'method':'Independent stdlib byte/field inspection; no END imports, no runtime capture, no author checker','cases':cases,'case_count':len(cases),'reference_count':sum(len(c['proposed_refs']) for c in cases),'reference_mismatches':[x for c in cases for x in c['proposed_refs'] if not x['match']],'failed_checks':{c['case']:[k for k,v in c['checks'].items() if not v] for c in cases},'documents':[{'name':f.name,'sha256':sha(f.read_bytes()),'bytes':len(f.read_bytes())} for f in sorted(DOC.iterdir()) if f.is_file()]}
options.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ('case_count','reference_count','reference_mismatches','failed_checks')},indent=2))
