"""Read-only run/stage/attempt journal verification against separate anchors/ledger."""
import base64,json
from dataclasses import asdict
from pathlib import Path
from end_engine.models.base import ModelRequest
from native_model_integration_v1.src.provider_protocol.wire import validate_wire,SETTINGS
from native_model_integration_v1.src.response_decoder.decode import decode
from .strict_json import canonical,loads,read,sha
from .publication import durable
SCHEMA='abc-r2-journal-v1'
def entry(context,index,previous,state,**fields):
    value={'schema_version':SCHEMA,'run_id':context['run_id'],'attempt_id':context['attempt_id'],'stage':context['stage'],'index':index,'previous_sha256':previous,'state':state,**fields}
    value['record_sha256']=sha(canonical(value));return value

def prepare(transport,reference,req,structured,seed,wire,record):
    pub=transport.publication;sealed=transport.dispatch_context
    if sealed is None or sealed.payload_bytes!=reference:raise ValueError('Missing sealed dispatch journal context')
    c={'run_id':sealed.run_id,'attempt_id':sealed.physical_call_reservation,'stage':req.purpose};path=transport.journal_dir/(str(c['attempt_id']).zfill(6)+'-'+sha(wire)[:16]+'.jsonl')
    header=entry(c,0,None,'RESERVED_WIRE_READY',record=dict(record))
    anchor={'schema_version':'abc-r2-dispatch-anchor-v1','identity_sha256':pub.identity_sha,**c,'call_id':sealed.call_id,'spec':sealed.spec_bytes.decode(),'reference_wire_sha256':sha(reference),'provenance_sha256':sha(sealed.provenance_bytes),'wire_sha256':sha(wire),'journal_path':path.relative_to(pub.directory).as_posix(),'header_sha256':header['record_sha256'],'model_request':asdict(req),'structured':structured,'seed':seed}
    durable(pub.attempt_anchor(c['attempt_id']),anchor,True);transport.append_journal(path,header,'x');return c,path,header

def finish_entry(transport,context,path,header,state,**fields):
    tail=entry(context,1,header['record_sha256'],state,**fields);transport.append_journal(path,tail)
    receipt={'kind':state,'run_id':context['run_id'],'attempt_id':context['attempt_id'],'stage':context['stage'],'last_sha256':tail['record_sha256']}
    if state=='RAW_RESPONSE_RECEIVED':receipt['raw_sha256']=fields['raw_response_sha256']
    durable(transport.publication.response_anchor(context['attempt_id']),receipt,True)

def _verify_journals(pub):
    rows=[a for a in pub.ledger.state()['attempts'] if a['run_id']==pub.request.run_id];reports=[];trusted={};untrusted={};records=[];expected_paths=set()
    def report(row,status,code,path=None,**extra):
        r={'attempt_id':row['attempt_id'] if row else None,'status':status,'code':code,**extra}
        if path is not None:
            r['path']=path.relative_to(pub.directory).as_posix()
            if path.is_file():r['observed_current_bytes_sha256']=sha(path.read_bytes())
        reports.append(r)
        if path is not None and path.is_file():
            rel=path.relative_to(pub.directory).as_posix()
            if status=='VERIFIED':trusted[rel]=sha(path.read_bytes())
            else:untrusted[rel]={'sha256':sha(path.read_bytes()),'authority':'CURRENT_UNTRUSTED_OR_UNSETTLED_OBSERVATION','status':status}
    for row in rows:
        uncertain=row['state']!='SUCCEEDED' and row['total_tokens'] is None
        aid=row['attempt_id'];anchor_path=pub.attempt_anchor(aid);path=None
        if not anchor_path.exists():
            report(row,'UNKNOWN' if row['state']=='RESERVED' else 'MISSING','RESERVATION_WITHOUT_DISPATCH_EVIDENCE' if row['state']=='RESERVED' else 'MISSING_DISPATCH_ANCHOR');continue
        try:
            anchor=read(anchor_path);assert set(anchor)=={'schema_version','identity_sha256','run_id','attempt_id','stage','call_id','spec','reference_wire_sha256','provenance_sha256','wire_sha256','journal_path','header_sha256','model_request','structured','seed'}
            assert type(anchor['attempt_id']) is int and anchor['schema_version']=='abc-r2-dispatch-anchor-v1' and anchor['identity_sha256']==pub.identity_sha
            intent=loads(row['purpose']);spec=loads(anchor['spec']);stage=intent['purpose'];assert anchor['run_id']==pub.request.run_id and anchor['attempt_id']==aid and anchor['stage']==stage==spec['instruction_id']==spec['purpose'] and spec['run_id']==pub.request.run_id and spec['task_id']==pub.request.task_id and anchor['call_id']==spec['call_id']==intent['call_id'] and sha(anchor['spec'].encode())==intent['spec_sha256'] and anchor['reference_wire_sha256']==intent['wire_sha256']
            path=(pub.directory/anchor['journal_path']).resolve();assert path.is_relative_to(pub.directory/'wire') and path.suffix=='.jsonl';expected_paths.add(path)
            if not path.exists():report(row,'MISSING','MISSING_WIRE_JOURNAL',path);continue
            rawlines=path.read_bytes().splitlines();items=[];torn=False
            for index,line in enumerate(rawlines):
                try:items.append(loads(line,max_bytes=8000000,max_depth=128,max_nodes=100000))
                except ValueError:
                    # Only a syntactically incomplete last append is truncated.
                    # A complete duplicate-key/nonfinite/schema-invalid JSON record is corrupt.
                    try:json.loads(line.decode('utf-8'))
                    except json.JSONDecodeError:
                        if index==len(rawlines)-1 and not path.read_bytes().endswith(b'\n'):
                            torn=True;continue
                    raise
            if not items:
                report(row,'TRUNCATED' if uncertain else 'INCONSISTENT','INCOMPLETE_HEADER',path);continue
            assert len(items)<=2
            previous=None
            for index,item in enumerate(items):
                copied=dict(item);digest=copied.pop('record_sha256');assert sha(canonical(copied))==digest
                assert item['schema_version']==SCHEMA and item['run_id']==pub.request.run_id and item['attempt_id']==aid and item['stage']==stage and item['index']==index and item['previous_sha256']==previous
                expected_keys={'schema_version','run_id','attempt_id','stage','index','previous_sha256','state','record_sha256'}
                if index==0:expected_keys|={'record'}
                elif item['state']=='RAW_RESPONSE_RECEIVED':expected_keys|={'response','raw_response_base64','raw_response_sha256'}
                elif item['state']=='TRANSPORT_STOP':expected_keys|={'error_type'}
                else:raise ValueError('Unexpected journal state')
                assert set(item)==expected_keys;previous=digest
            header=items[0];assert header['state']=='RESERVED_WIRE_READY' and header['record_sha256']==anchor['header_sha256'];record=dict(header['record']);assert set(record)=={'stage','method','path','wire','wire_sha256','response','namespace'} and record['method']=='POST' and record['path']=='/api/generate' and record['namespace']=='MOCK_WIRING_ONLY_NOT_EMPIRICAL';wire=record['wire'].encode();assert sha(wire)==record['wire_sha256']==anchor['wire_sha256'] and record['stage']==stage and record['response'] is None
            request=ModelRequest(**anchor['model_request']);assert request.purpose==stage;assert validate_wire(loads(wire),request,anchor['structured'],anchor['seed'])==wire
            if torn:
                report(row,'TRUNCATED' if uncertain else 'INCONSISTENT','TORN_FINAL_APPEND',path);continue
            receipt_path=pub.response_anchor(aid)
            if len(items)==1:
                report(row,'UNKNOWN' if uncertain else 'INCONSISTENT','NO_RESPONSE_RECORD',path);continue
            tail=items[1]
            if not receipt_path.exists():report(row,'UNKNOWN' if row['state']=='RESERVED' else 'MISSING','MISSING_RESPONSE_ANCHOR',path);continue
            receipt=read(receipt_path);assert set(receipt)==({'kind','run_id','attempt_id','stage','last_sha256','raw_sha256'} if tail['state']=='RAW_RESPONSE_RECEIVED' else {'kind','run_id','attempt_id','stage','last_sha256'})
            assert receipt['run_id']==pub.request.run_id and receipt['attempt_id']==aid and receipt['stage']==stage and receipt['last_sha256']==tail['record_sha256'] and receipt['kind']==tail['state']
            receipt_valid=None
            if tail['state']=='RAW_RESPONSE_RECEIVED':
                raw=base64.b64decode(tail['raw_response_base64'],validate=True);assert sha(raw)==tail['raw_response_sha256']==receipt['raw_sha256'] and raw.decode('utf-8',errors='replace')==tail['response'];record['response']=tail['response']
                try:decoded=decode(raw,SETTINGS.model);receipt_valid=True
                except Exception:decoded=None;receipt_valid=False
                if row['state']=='SUCCEEDED':
                    assert decoded is not None and decoded['response']==row['response_text'] and sha(decoded['response'].encode())==row['response_sha256']
                    assert row['input_tokens']==decoded.get('prompt_eval_count') and row['output_tokens']==decoded.get('eval_count')
                    c=row['candidate'];assert c['task_id']==pub.request.task_id and c['call_id']==anchor['call_id'] and c['wire_sha256']==anchor['reference_wire_sha256'] and c['provenance_sha256']==anchor['provenance_sha256']
            else:
                assert row['state']!='SUCCEEDED';record['error_type']=tail['error_type']
            status='UNKNOWN' if row['state']=='RESERVED' else 'VERIFIED';report(row,status,'UNSETTLED_RESERVATION' if status=='UNKNOWN' else 'ANCHOR_CHAIN_LEDGER_MATCH',path,provider_receipt_valid=receipt_valid)
            if status=='VERIFIED':record['recovered_without_dispatch']=True;records.append(record)
        except (Exception,) as e:
            report(row,'CORRUPT','JOURNAL_SCHEMA_HASH_OR_LEDGER_MISMATCH',path,exception_type=type(e).__name__)
    wire=pub.directory/'wire'
    for path in sorted(wire.glob('*.jsonl')):
        if path.resolve() not in expected_paths:report(None,'CORRUPT','UNEXPECTED_OR_DUPLICATE_JOURNAL',path)
    bad=[r for r in reports if r['status'] in ('MISSING','CORRUPT','INCONSISTENT')];incomplete=[r for r in reports if r['status'] in ('TRUNCATED','UNKNOWN')]
    return {'schema_version':'abc-r2-journal-review-v1','overall':'BLOCKED' if bad else 'INTERRUPTED' if incomplete else 'VERIFIED','attempts':reports,'trusted_hashes':trusted,'untrusted_evidence':untrusted,'verified_provider_records':records,'host_compromise_protection':False}

def verify_journals(pub):
    from .provenance import reconcile, ProvenanceFault
    def wire_snapshot():
        return {p.relative_to(pub.directory).as_posix():sha(p.read_bytes())
                for p in sorted((pub.directory/'wire').glob('*.jsonl'))}
    before_wire = wire_snapshot()
    report = _verify_journals(pub)
    try:
        graph = reconcile(pub)
        if wire_snapshot() != before_wire or any(
                before_wire.get(name) != digest for name,digest in report['trusted_hashes'].items()):
            raise ProvenanceFault('WIRE_CHANGED_DURING_VERIFICATION')
        graph['wire_hashes'] = before_wire
        report['provenance_graph'] = graph
        if graph['overall'] != 'VERIFIED' and report['overall'] == 'VERIFIED':
            report['overall'] = 'INTERRUPTED'
            report['attempts'].append({'attempt_id': None, 'status': 'UNKNOWN',
                                      'code': 'MISSING_HISTORICAL_SETTLEMENT_WITNESS'})
    except (ValueError, KeyError, TypeError, OSError, AssertionError) as error:
        report['overall'] = 'BLOCKED'
        # Missing/damaged wire evidence can use the existing explicit blocked
        # terminal artifact when ledger lineage is still intact. Contradictory
        # ledger identity/settlement cannot be used to reconstruct candidates.
        report['attempts'].append({'attempt_id': None, 'status': 'INCONSISTENT',
                                  'code': 'PROVENANCE_GRAPH_INCONSISTENT',
                                  'detail': str(error) if isinstance(error, ProvenanceFault)
                                            else type(error).__name__})
    # A blocked aggregate is never eligible, regardless of the leaf reason.
    # Do not add fields to valid/uncertain reports: completed valid snapshots
    # retain their exact historical report shape.
    from .certification import disposition, EvidenceDisposition
    if disposition(report) is EvidenceDisposition.BLOCKED:
        report['requires_integrity_hold'] = True
    return report

def verify_native_records(pub,records):
    rows=pub.ledger.summary(pub.request.run_id)['attempts'];assert len(rows)==len(records)
    for row,record in zip(rows,records):
        spec=loads(row['purpose']);assert record['wire_sha256']==sha(record['wire'].encode())==spec['wire_sha256']
        if row['state']=='SUCCEEDED':
            assert record['response']==row['candidate']['raw_provider_response'];r=decode(record['response'].encode(),SETTINGS.model);assert row['response_text']==r['response'] and row['input_tokens']==r.get('prompt_eval_count') and row['output_tokens']==r.get('eval_count')
    return {'schema_version':'abc-r2-native-evidence-v1','overall':'VERIFIED','attempts':len(rows),'provider_records_sha256':sha(canonical(records)),'trusted_hashes':{},'untrusted_evidence':{},'scope':'Unchanged native in-memory/raw-ledger evidence; new r2 final publication anchors it, no retroactive claim of native per-wire crash journaling'}
