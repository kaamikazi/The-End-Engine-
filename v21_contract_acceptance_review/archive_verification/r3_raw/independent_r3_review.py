"""Independent offline contract probes. No author checker/runtime imported; writes reviewer output only.
Run with installed Python310 -B (jsonschema 4.26.0); no package installation/network.
Semantic oracle is explicitly synthetic, NOT a replacement for F01/capture verification.
"""
import copy, csv, hashlib, importlib.metadata, json, math, pathlib, sys
from jsonschema import Draft7Validator
import jsonschema

ROOT = pathlib.Path(r'E:\The End Engine\v21_contract_acceptance_review')
RAW = ROOT / 'r3_raw'
SPEC = pathlib.Path(r'E:\END-v102-V21-Contract-Checkpoint\experimental_architectures_v1_r3\validation\contract_reconciliation_v2_1')
S = json.loads((SPEC/'R3_SCHEMA_SPECIFICATION.json').read_text(encoding='utf-8'))
H = '1'*64
A,S_T,I,U,X = [x for x in S['definitions']['snapshot']['properties']['tier']['enum']]
N,R,D = [x for x in S['definitions']['envelope']['properties']['variant']['enum']]
NORMAL = {'COMPLETED','NO_ACTIONABLE_REVISION','INVALID_RESPONSE','PROTOCOL_FAILURE'}
RESTRICT = {'INTERRUPTED','BUDGET_EXHAUSTED','TIME_EXHAUSTED','EXTERNAL_BLOCKER','UNRESOLVED'}
UNCERTAIN = RESTRICT | {'INVALID_RESPONSE','PROTOCOL_FAILURE'}
def dump(path, x):
    path.write_text(json.dumps(x, indent=2, ensure_ascii=False, allow_nan=False)+'\n',encoding='utf-8')
def ref(origin='RESERVATION'):
    return {'path': 'capture/'+origin.lower()+'.json','sha256':H,'origin':origin}
def snapshot(tier=A):
    j=[A,S_T,I,U,X].index(tier)
    return dict(tier=tier,capture_id='capture1',coordination=['VERIFIED_COOPERATIVE_CUT','VERIFIED_COOPERATIVE_CUT','NO_COMMON_CUT','VIOLATED','UNSUPPORTED'][j],writer_domain_ref=H if j<2 else None,inventory_digest=H if j<2 else None,content_digest=H if j<2 else None,witness_coverage=['CLOSED_ACCOUNTING_GRAPH','INCOMPLETE_OR_CONTRADICTORY','INDIVIDUAL_GROUPS_ONLY','UNSTABLE','UNSUPPORTED'][j],origin_scope='COOPERATING_LOCAL_WRITERS_NOT_PROVIDER_ATTESTATION')
def claim(kind='RECORDED_IDENTITY'):
    graph=kind=='ANCHORED_GRAPH_CARDINALITY'
    return dict(claim_kind=kind,value={'attempt_ids':[1],'cardinality':1} if graph else {'attempt_id':1},evidence_authority='GUARDED_VISIBLE_GRAPH' if graph else 'RECORDED_ONLY',scope=dict(run_id='run1',attempt_ids=[1],coverage='ANCHORED_GRAPH_IN_CUT' if graph else 'CAPTURED_RECORD_GROUP',excluded_claims=['PROVIDER_INFERENCE_COUNT','ERASURE_RESISTANCE','ANSWER_CORRECTNESS','COMPLETE_RUN_COST']),source_refs=[ref()],snapshot_id='capture1',verification_status='CORROBORATED_WITHIN_SCOPE' if graph else 'OBSERVED',limitations=['Recorded local identity only'],full_run_certification_permitted=False)
def candidates(observed=False):
    return dict(observation_state='AVAILABLE',history_coverage='PARTIAL',entries=[dict(candidate_id='C0',attempt_id=1,availability='PRESENT',content='answer',content_sha256=hashlib.sha256(b'answer').hexdigest(),binding_authority='OBSERVED_ONLY' if observed else 'SOURCE_VERIFIED_BINDING',response_validity='UNASSESSED' if observed else 'ELIGIBLE',eligible_for_selection=not observed,lineage=dict(status='OBSERVED' if observed else 'VERIFIED',parent_ids=[]),handle=dict(status='CORROBORATED_NOT_CERTIFIED' if observed else 'SOURCE_VERIFIED_BINDING',output_id='output1',binding_refs=[ref('SETTLEMENT')]),source_refs=[ref('JOURNAL')])],initial_ref='C0',initial_ref_state='BOUND_INITIAL')
def no_candidates():
    return dict(observation_state='NONE_SUPPORTABLE',history_coverage='UNKNOWN',entries=[],initial_ref=None,initial_ref_state='NOT_KNOWN',unavailable_reason='NO_JUSTIFIED_IDENTITIES')
def base(variant=N,tier=A,provenance=None,reason=None,cause='INTEGRITY_HOLD'):
    diag=variant==D
    x=dict(schema_version='end-outcome/2.1-proposal.1',contract_version='end-certification/2.1-proposal.1',variant=variant,run_binding=dict(run_id='run1',task_id='task1',condition_id='DIRECT',identity_sha256=H),artifact_persisted=not diag,persistence_scope='REFERENCED_SOURCE_ARTIFACT_NOT_ENVELOPE',provenance_eligible=not diag,provenance=dict(status=provenance or ('BLOCKED' if diag else 'VERIFIED'),report_sha256=H,scope='RECORDED_PROVENANCE_NOT_ANSWER_CORRECTNESS'),termination_reason=reason or ('EXTERNAL_BLOCKER' if diag else 'INTERRUPTED' if variant==R else 'COMPLETED'),answer_success='NOT_ASSERTED',candidate_selected=not diag,selected_candidate_ref=None if diag else 'C0',candidates=candidates(diag),accounting=dict(state='UNKNOWN' if tier==X else 'PARTIAL',snapshot=snapshot(tier),observations=[] if tier==X else [claim('ANCHORED_GRAPH_CARDINALITY' if tier==A else 'RECORDED_IDENTITY')],complete_totals=None,incomplete_reason='PROVENANCE_BLOCKED' if diag else 'MISSING_WITNESS'),scientific_score_available=False,scientific_score=None,scientific_score_status='NOT_COMPUTED',diagnostics=[dict(code='OBSERVATION_LIMIT',severity='ERROR' if diag else 'WARNING',detail='synthetic review fixture',source_refs=[])],publication=dict(kind='NO_ARTIFACT') if diag else dict(kind='VERIFIED_LEGACY_SOURCE_RECORD',source_contract='legacy-normal-1.0.1',path='RESULT.json',file_name='RESULT.json',sha256=H,verification_check_id='check1',verified_at_capture_id='capture1'))
    if tier==X:x['candidates']=no_candidates();x['candidate_selected']=False;x['selected_candidate_ref']=None
    if diag:x.update(diagnostic_cause=cause,prior_artifact_observation={'state':'NONE_OBSERVED'})
    return x

Draft7Validator.check_schema(S)
V=Draft7Validator(S)
MEM=[Draft7Validator({'$schema':S['$schema'],'definitions':S['definitions'],'allOf':[b]}) for b in S['oneOf']]
fixtures=[];results=[]
def probe(name,x,expected,category='structural'):
    x=copy.deepcopy(x); fixtures.append({'name':name,'category':category,'expected_structural_member_count':expected,'instance':x})
    matches=[i for i,v in enumerate(MEM) if v.is_valid(x)]
    errors=list(V.iter_errors(x))
    leaves=[]
    def collect(e):
        if e.context:
            for c in e.context:collect(c)
        else:leaves.append(dict(path=list(e.absolute_path),schema_path=list(e.absolute_schema_path),validator=e.validator,message=e.message))
    for e in errors:collect(e)
    row=dict(name=name,category=category,expected_member_count=expected,actual_member_count=len(matches),matching_variants=[N,R,D] if False else [[N,R,D][i] for i in matches],standard_valid=not errors,expectation_match=(len(matches)==expected and bool(matches)==(not errors)),errors=leaves)
    results.append(row);return row

# Independently specified truth table: no code/fixtures from author validation.
for variant in (N,R,D):
 for prov in ('VERIFIED','INTERRUPTED','UNKNOWN','BLOCKED'):
  for reason in sorted(NORMAL|RESTRICT):
   for tier in (A,S_T,I,U,X):
    x=base(variant,tier,prov,reason)
    eligible=(variant==N and prov=='VERIFIED' and reason in NORMAL) or (variant==R and ((prov=='VERIFIED' and reason in RESTRICT) or (prov in ('INTERRUPTED','UNKNOWN') and reason in UNCERTAIN)))
    ok=(eligible and tier in (A,S_T)) or (variant==D and prov=='BLOCKED' and reason=='EXTERNAL_BLOCKER')
    probe('partition_%s_%s_%s_%s'%(variant,prov,reason,tier),x,int(ok),'partition')

for idx,variant in enumerate((N,R,D)):
 x=base(variant)
 probe('positive_member_'+variant,x,1)
 for key in S['definitions']['envelope']['required']+(['diagnostic_cause','prior_artifact_observation'] if variant==D else []):
    y=copy.deepcopy(x);del y[key];probe('missing_'+variant+'_'+key,y,0,'required')
 for field in S['x-contract']['legacy_outer_fields_forbidden']:
  for value in (None,False,{},'C0'):
    y=copy.deepcopy(x);y[field]=value;probe('forbidden_'+variant+'_'+field+'_'+repr(value),y,0,'additionalProperties')
 def mutate_tree(value,path=()):
    if isinstance(value,dict):
      y=copy.deepcopy(x);target=y
      for p in path:target=target[p]
      target['reviewer_unknown_property']=True;probe('closed_'+variant+'_'+repr(path),y,0,'nested_additionalProperties')
      for key in value:
       y=copy.deepcopy(x);target=y
       for p in path:target=target[p]
       del target[key];probe('nested_missing_'+variant+'_'+repr(path+(key,)),y,0,'nested_required')
      for k,v in value.items():mutate_tree(v,path+(k,))
    elif isinstance(value,list):
      for i,v in enumerate(value):mutate_tree(v,path+(i,))
 mutate_tree(x)
 for key in ('schema_version','contract_version','variant','answer_success','scientific_score_status'):
  for value in ('UNKNOWN_FUTURE',None,False):
   y=copy.deepcopy(x);y[key]=value;probe('bad_enum_'+variant+'_'+key+'_'+repr(value),y,0,'enum')
 for key in ('candidate_selected','artifact_persisted','provenance_eligible'):
  for value in (None,0,1,'true',[]):
   y=copy.deepcopy(x);y[key]=value;probe('bad_boolean_'+variant+'_'+key+'_'+repr(value),y,0,'type')

def mutation(name,fn,expected=0,original=None,cat='conditional'):
 x=copy.deepcopy(original or base());fn(x);return probe(name,x,expected,cat)
mutation('candidate_id_bool',lambda x:x['candidates']['entries'][0].update(attempt_id=True))
mutation('candidate_id_zero',lambda x:x['candidates']['entries'][0].update(attempt_id=0))
mutation('candidate_id_fraction',lambda x:x['candidates']['entries'][0].update(attempt_id=1.5))
mutation('draft07_integral_float',lambda x:x['candidates']['entries'][0].update(attempt_id=1.0),1)
mutation('scientific_score_numeric',lambda x:x.update(scientific_score=0.9))
mutation('scientific_score_claimed',lambda x:x.update(scientific_score_available=True))
mutation('answer_success_claimed',lambda x:x.update(answer_success='CORRECT'))
mutation('selected_ref_null',lambda x:x.update(selected_candidate_ref=None))
mutation('unselected_ref_present',lambda x:x.update(candidate_selected=False))
mutation('complete_totals_null',lambda x:x['accounting'].update(state='COMPLETE'))
mutation('partial_totals_present',lambda x:x['accounting'].update(complete_totals={}))
mutation('partial_reason_missing',lambda x:x['accounting'].pop('incomplete_reason'))
mutation('S_no_fact',lambda x:x['accounting'].update(observations=[]),original=base(tier=S_T))
mutation('A_no_graph',lambda x:x['accounting'].update(observations=[claim()]))
mutation('S_graph',lambda x:x['accounting'].update(observations=[claim('ANCHORED_GRAPH_CARDINALITY')]),original=base(tier=S_T))
mutation('missing_candidate_selected',lambda x:x['candidates']['entries'][0].update(availability='MISSING',content=None,content_sha256=None,missing_reason='SOURCE_ABSENT'))
mutation('lineage_unavailable_selected',lambda x:x['candidates']['entries'][0].update(lineage=dict(status='UNAVAILABLE',parent_ids=None,unavailable_reason='NOT_ESTABLISHED')))
mutation('handle_missing_selected',lambda x:x['candidates']['entries'][0].update(handle=dict(status='MISSING',output_id=None,binding_refs=[])))
mutation('diagnostic_selected',lambda x:x.update(candidate_selected=True,selected_candidate_ref='C0'),original=base(D))
mutation('diagnostic_source_publication',lambda x:x.update(publication=base()['publication']),original=base(D))
mutation('diagnostic_certified_candidate',lambda x:x.update(candidates=candidates()),original=base(D))
mutation('diagnostic_persisted_no_artifact',lambda x:x.update(artifact_persisted=True),original=base(D))
mutation('diagnostic_file_positive',lambda x:x.update(artifact_persisted=True,publication=dict(kind='DIAGNOSTIC_FILE',path='publication/recovery_holds/probe_1.json',sha256=H)),1,base(D))
for tier in (I,U,X):
 probe('snapshot_unavailable_'+tier,base(D,tier,'UNKNOWN',cause='SNAPSHOT_AUTHORITY_UNAVAILABLE'),1,'cross_contract')
 probe('unsupported_cause_'+tier,base(D,tier,'UNKNOWN',cause='UNSUPPORTED_OBSERVATION'),1,'cross_contract')
for tier in (A,S_T):
 probe('snapshot_unavailable_forbids_'+tier,base(D,tier,'UNKNOWN',cause='SNAPSHOT_AUTHORITY_UNAVAILABLE'),0,'cross_contract')
probe('typed_error_outside',{'type':'ArtifactIntegrity','reason':'COMPLETED_RESULT_NOT_VERIFIED'},0,'outside_union')
probe('legacy_shape_outside',{'implementation_version':'1.0.1','result':{},'C0':'a','FINAL':'a'},0,'outside_union')

# Resolve every local JSON pointer without network or an author checker.
refs=[]
def walk(node,path=()):
 if isinstance(node,dict):
  if '$ref' in node:
   ptr=node['$ref'];target=S
   assert ptr.startswith('#/'),ptr
   for part in ptr[2:].split('/'):target=target[part.replace('~1','/').replace('~0','~')]
   refs.append({'path':list(path),'ref':ptr,'resolved':True})
  for key,val in node.items():walk(val,path+(key,))
 elif isinstance(node,list):
  for i,val in enumerate(node):walk(val,path+(i,))
walk(S)

# Explicit synthetic oracle: an external verifier must establish these facts in real code.
def oracle(x):
 return dict(grounded=True,source_pass=True,source_hash=H,source_path='RESULT.json',source_capture='capture1',run_binding=copy.deepcopy(x['run_binding']),cut_verified=True,cut_tier=x['accounting']['snapshot']['tier'],witness_ids=[1],all_claims=copy.deepcopy(x['accounting']['observations']),independent_channels=True,refs_valid=True,source_candidate_content='answer',candidate_proof=True,handle_proof=True,history_empty=False,initial_id='C0',diagnostic_grounded=True,no_future_generation=True,raw_usage_coverage=True,known_costs=True,totals=dict(physical_attempts=1,input_tokens=10,output_tokens=5,total_tokens=15,wall_time=1.0),prior_immutable=True,diagnostic_persisted=True)
def semantic(x,o):
 failures=[]
 def fail(rule,why):failures.append({'rule':rule,'reason':why})
 tier=x['accounting']['snapshot']['tier'];cap=x['accounting']['snapshot']['capture_id'];diag=x['variant']==D
 if not o['grounded']:fail('E01','ungrounded run')
 if not diag and (not o['source_pass'] or x['publication']['sha256']!=o['source_hash'] or x['publication']['path']!=o['source_path'] or x['publication']['verified_at_capture_id']!=o['source_capture'] or o['source_capture']!=cap or x['run_binding']!=o['run_binding']):fail('E01','source proof/bytes/path/identity/same-cut mismatch')
 if tier in (A,S_T) and (not o['cut_verified'] or tier!=o['cut_tier']):fail('E02','cooperative cut/witness tier not established')
 obs=x['accounting']['observations']
 if obs!=o['all_claims'] or not o['refs_valid']:fail('A01','unsupported/omitted claim or unresolved retained refs')
 for c in obs:
  if c['snapshot_id']!=cap or c['scope']['run_id']!=x['run_binding']['run_id']:fail('A01','claim capture/run mismatch')
  if c['claim_kind']=='ANCHORED_GRAPH_CARDINALITY':
   ids=c['value']['attempt_ids']
   if tier!=A or c['scope']['coverage']!='ANCHORED_GRAPH_IN_CUT' or ids!=sorted(set(ids)) or ids!=c['scope']['attempt_ids'] or ids!=o['witness_ids'] or c['value']['cardinality']!=len(ids):fail('A02','graph scope/IDs/cardinality differs from positively verified witness set')
  if c['claim_kind'] in ('CORROBORATED_RESERVATION_DISPATCH','CORROBORATED_IDENTITY_GROUP') and not o['independent_channels']:fail('A03','copies do not prove independent original channels')
  if c['claim_kind']=='USAGE_METADATA' and c['verification_status']=='CORROBORATED_WITHIN_SCOPE':
   vs=[c['value'][k] for k in ('input_tokens','output_tokens','total_tokens')]
   if all(v['state']=='KNOWN_RECORDED' for v in vs) and vs[0]['value']+vs[1]['value']!=vs[2]['value']:fail('A04','corroborated usage arithmetic invalid')
 if x['accounting']['state']=='COMPLETE':
  totals=x['accounting']['complete_totals']
  if tier!=A or x['provenance']['status']!='VERIFIED' or not all(o[k] for k in ('no_future_generation','raw_usage_coverage','known_costs')) or any(totals[k]!=v for k,v in o['totals'].items()) or totals['input_tokens']+totals['output_tokens']!=totals['total_tokens']:fail('A05','complete source coverage/sum/closure unavailable')
 cs=x['candidates'];entries=cs['entries'];ids=[]
 for c in entries:
  if c['candidate_id'] in ids or (c['availability']=='PRESENT' and (c['content_sha256']!=hashlib.sha256(c['content'].encode('utf-8')).hexdigest() or c['content']!=o['source_candidate_content'])) or not o['candidate_proof']:fail('C01','candidate uniqueness/content/source proof mismatch')
  if c['lineage']['status']=='VERIFIED' and any(p not in ids for p in c['lineage']['parent_ids']):fail('C01','parent not earlier bound candidate')
  ids.append(c['candidate_id'])
 if cs['initial_ref'] is not None and cs['initial_ref']!=o['initial_id']:fail('C01','initial candidate rebound')
 if x['candidate_selected']:
  selected=[c for c in entries if c['candidate_id']==x['selected_candidate_ref']]
  if len(selected)!=1 or not o['handle_proof'] or not o['candidate_proof']:fail('C02','selection/handle lacks current source proof')
 if (diag and x['candidate_selected']) or (cs['observation_state']=='KNOWN_EMPTY_HISTORY' and not o['history_empty']):fail('C03','diagnostic selection or unsupported known-empty history')
 p=x['publication']
 if not diag and pathlib.PurePosixPath(p['path']).name!=p['file_name']:fail('P01','source basename mismatch')
 if diag and (not o['prior_immutable'] or (x['artifact_persisted'] and not o['diagnostic_persisted'])):fail('P01','prior artifact altered or diagnostic persistence not evidenced')
 if diag and not o['diagnostic_grounded']:fail('V01','diagnostic cause not grounded; generic exceptions remain external')
 return failures

semantic_results=[];semantic_fixtures=[]
def semprobe(name,x,change=None,expected_rules=()):
 o=oracle(x)
 if change:change(x,o)
 errors=semantic(x,o);structural=V.is_valid(x)
 row=dict(name=name,structural_member_count=sum(v.is_valid(x) for v in MEM),semantic_failures=errors,expected_failure_rules=list(expected_rules),expectation_match=(set(expected_rules)=={e['rule'] for e in errors}),normatively_accepted=structural and not errors,scope='SYNTHETIC_EXTERNAL_ORACLE_ONLY_NOT_RUNTIME_PROOF')
 semantic_results.append(row);semantic_fixtures.append(dict(name=name,instance=x,external_synthetic_oracle=o));return row
semprobe('positive_selected_normal',base())
semprobe('positive_guarded_S_legacy_terminal',base(tier=S_T))
semprobe('positive_restricted_C0_unknown_later_cost',base(R,S_T,'UNKNOWN'))
semprobe('positive_diagnostic_A_count_no_certification',base(D))
semprobe('positive_diagnostic_I_recorded_identity',base(D,I))
semprobe('positive_unstable_unavailable_diagnostic',base(D,U,'UNKNOWN',cause='SNAPSHOT_AUTHORITY_UNAVAILABLE'))
semprobe('positive_unsupported_no_candidates',base(D,X,'UNKNOWN',cause='UNSUPPORTED_OBSERVATION'))
semprobe('source_pass_boolean_forgery',base(),lambda x,o:o.update(source_pass=False),('E01',))
semprobe('foreign_same_hash_source_path',base(),lambda x,o:x['publication'].update(path='foreign/RESULT.json'),('E01',))
semprobe('source_other_capture',base(),lambda x,o:o.update(source_capture='capture2'),('E01',))
semprobe('source_identity_rebound',base(),lambda x,o:x['run_binding'].update(task_id='foreign'),('E01',))
semprobe('hash_equality_without_domain',base(),lambda x,o:o.update(cut_verified=False),('E02',))
semprobe('missing_mandatory_witness_A_forgery',base(),lambda x,o:o.update(cut_tier=S_T),('E02',))
semprobe('omitted_justified_claim',base(),lambda x,o:o['all_claims'].append(claim()),('A01',))
semprobe('unresolved_capture_reference',base(),lambda x,o:o.update(refs_valid=False),('A01',))
semprobe('claim_other_snapshot',base(),lambda x,o:(x['accounting']['observations'][0].update(snapshot_id='other'),o.update(all_claims=copy.deepcopy(x['accounting']['observations']))),('A01',))
semprobe('graph_cardinality_mismatch',base(),lambda x,o:(x['accounting']['observations'][0]['value'].update(cardinality=2),o.update(all_claims=copy.deepcopy(x['accounting']['observations']))),('A02',))
semprobe('empty_graph_without_positive_evidence',base(),lambda x,o:(x['accounting']['observations'][0]['value'].update(attempt_ids=[],cardinality=0),x['accounting']['observations'][0]['scope'].update(attempt_ids=[]),o.update(all_claims=copy.deepcopy(x['accounting']['observations']))),('A02',))
g=base(D,S_T);c=claim();c.update(claim_kind='CORROBORATED_RESERVATION_DISPATCH',value=dict(attempt_id=1,reservation_sha256=H,dispatch_sha256=H),evidence_authority='LOCAL_WITNESS_GROUP',source_refs=[ref(),ref('DISPATCH')]);g['accounting']['observations']=[c]
semprobe('positive_independent_reservation_dispatch',copy.deepcopy(g))
semprobe('copied_witnesses_false_independence',g,lambda x,o:o.update(independent_channels=False),('A03',))
g=base(D,S_T);c=claim();c.update(claim_kind='USAGE_METADATA',value=dict(attempt_id=1,input_tokens=dict(state='KNOWN_RECORDED',value=10),output_tokens=dict(state='KNOWN_RECORDED',value=5),total_tokens=dict(state='KNOWN_RECORDED',value=15),raw_receipt_status='INVALID'),evidence_authority='RECORDED_USAGE_NOT_COMPLETE_COST',verification_status='CORROBORATED_WITHIN_SCOPE');g['accounting']['observations']=[c]
semprobe('positive_recorded_metadata_not_total',copy.deepcopy(g))
semprobe('usage_arithmetic_false_corroboration',g,lambda x,o:(x['accounting']['observations'][0]['value']['total_tokens'].update(value=16),o.update(all_claims=copy.deepcopy(x['accounting']['observations']))),('A04',))
g=base();g['accounting'].update(state='COMPLETE',complete_totals=dict(physical_attempts=1,input_tokens=10,output_tokens=5,total_tokens=15,wall_time=1.0,authority='COMPLETE_RECORDED_ACCOUNTING_WITHIN_DECLARED_LOCAL_SCOPE',source_refs=[ref('SETTLEMENT')]))
del g['accounting']['incomplete_reason'];probe('complete_accounting_positive',g,1,'complete_totals')
semprobe('positive_complete_totals',copy.deepcopy(g))
semprobe('unknown_cost_cannot_be_complete',copy.deepcopy(g),lambda x,o:o.update(known_costs=False),('A05',))
semprobe('unclosed_generation_cannot_be_complete',copy.deepcopy(g),lambda x,o:o.update(no_future_generation=False),('A05',))
semprobe('invalid_raw_cannot_be_complete',copy.deepcopy(g),lambda x,o:o.update(raw_usage_coverage=False),('A05',))
semprobe('complete_sum_mismatch',g,lambda x,o:x['accounting']['complete_totals'].update(total_tokens=14),('A05',))
for key in ('physical_attempts','input_tokens','output_tokens','total_tokens','wall_time'):
 mutation('complete_negative_'+key,lambda x,key=key:x['accounting']['complete_totals'].update({key:-1}),original=copy.deepcopy(g),cat='numeric_bounds')
semprobe('self_rehashed_substitute_answer',base(),lambda x,o:x['candidates']['entries'][0].update(content='substitute',content_sha256=hashlib.sha256(b'substitute').hexdigest()),('C01',))
semprobe('later_parent_false_lineage',base(),lambda x,o:x['candidates']['entries'][0]['lineage'].update(parent_ids=['C9']),('C01',))
semprobe('selection_ref_unbound',base(),lambda x,o:x.update(selected_candidate_ref='C9'),('C02',))
semprobe('rebound_handle',base(),lambda x,o:o.update(handle_proof=False),('C02',))
g=base(D);g['candidates']=dict(observation_state='KNOWN_EMPTY_HISTORY',history_coverage='COMPLETE',entries=[],initial_ref=None,initial_ref_state='NONE_GENERATED')
semprobe('unknown_history_not_known_empty',g,expected_rules=('C03',))
semprobe('publication_basename_mismatch',base(),lambda x,o:(x['publication'].update(file_name='COMMON_RESULT.json')),('P01',))
semprobe('suspect_prior_preserved',base(D),lambda x,o:x.update(prior_artifact_observation=dict(state='PRESENT',path='RESULT.json',sha256=H,currently_verified=False,verification_outcome='REJECTED')))
semprobe('generic_exception_must_not_be_diagnostic',base(D),lambda x,o:o.update(diagnostic_grounded=False),('V01',))

# Strict parsing is separate from Draft07. Keep exact invalid source text and errors.
parse_results=[]
def strict_load(raw):
 def pairs(ps):
  result={}
  for k,v in ps:
   if k in result:raise ValueError('DUPLICATE_KEY:'+k)
   result[k]=v
  return result
 def number(token):
  value=float(token)
  if not math.isfinite(value):raise ValueError('NONFINITE_OR_OVERFLOW:'+token)
  return value
 def constant(token):raise ValueError('INVALID_JSON_NUMBER:'+token)
 return json.loads(raw,object_pairs_hook=pairs,parse_float=number,parse_constant=constant)
for name,raw,ok in [('duplicate_root','{"a":1,"a":2}',False),('duplicate_nested','{"x":{"a":1,"a":2}}',False),('nan','{"a":NaN}',False),('infinity','{"a":Infinity}',False),('minus_infinity','{"a":-Infinity}',False),('finite_overflow','{"a":1e9999}',False),('finite_number','{"a":1e2}',True),('valid_zero','{"a":0}',True)]:
 try:value=strict_load(raw);accepted=True;error=None
 except Exception as exc:accepted=False;error=repr(exc)
 parse_results.append(dict(name=name,raw=raw,expected_accepted=ok,accepted=accepted,error=error,expectation_match=ok==accepted))

rows=list(csv.DictReader((SPEC/'R3_NORMATIVE_FIELD_MATRIX.csv').open(encoding='utf-8',newline='')))
matrix_fail=[]
for row in rows:
 if row['FIELD'] in S['definitions']['envelope']['properties']:
  if json.loads(row['BASE_DEFINITION'])!=S['definitions']['envelope']['properties'][row['FIELD']]:matrix_fail.append(row['FIELD'])
  is_required=row['FIELD'] in S['definitions']['envelope']['required'] or (row['VARIANT']==D and row['FIELD'] in ('diagnostic_cause','prior_artifact_observation'))
  if (row['PRESENCE']=='REQUIRED')!=is_required:matrix_fail.append(row['VARIANT']+':presence:'+row['FIELD'])
summary=dict(validator='python-jsonschema',validator_version=importlib.metadata.version('jsonschema'),validator_module=jsonschema.__file__,python=sys.version,python_executable=sys.executable,no_packages_installed=True,offline=True,author_checker_used=False,schema_sha256=hashlib.sha256((SPEC/'R3_SCHEMA_SPECIFICATION.json').read_bytes()).hexdigest(),metaschema_check='PASS',local_references=len(refs),unresolved_references=0,structural_fixtures=len(results),structural_expectation_matches=sum(r['expectation_match'] for r in results),structural_expectation_failures=[r['name'] for r in results if not r['expectation_match']],accepted_structural_fixtures=sum(r['standard_valid'] for r in results),rejected_structural_fixtures=sum(not r['standard_valid'] for r in results),multi_member_instances=[r['name'] for r in results if r['actual_member_count']>1],semantic_oracle_cases=len(semantic_results),semantic_expectation_failures=[r['name'] for r in semantic_results if not r['expectation_match']],strict_parsing_cases=len(parse_results),strict_parse_failures=[r['name'] for r in parse_results if not r['expectation_match']],matrix_rows=len(rows),matrix_base_presence_failures=matrix_fail,limitations=['Standard Draft07 ignores x-semantic-rules.','Semantic tests use explicit synthetic external facts, never authenticate source/capture/provider.','No actual new adapter/capture protocol installed or executed.','Finite fixtures are not proof of all possible instances; disjointness additionally follows from required variant constants.'])
RAW.mkdir(exist_ok=True,parents=True)
dump(RAW/'STRUCTURAL_FIXTURES.json',fixtures);dump(RAW/'STRUCTURAL_RAW_RESULTS.json',results);dump(RAW/'LOCAL_REFERENCE_RESULTS.json',refs);dump(RAW/'SEMANTIC_FIXTURES.json',semantic_fixtures);dump(RAW/'SEMANTIC_RAW_RESULTS.json',semantic_results);dump(RAW/'STRICT_PARSE_RESULTS.json',parse_results);dump(ROOT/'R3_STANDARD_VALIDATOR_RESULTS.json',summary)
cross_names=['positive_guarded_S_legacy_terminal','positive_restricted_C0_unknown_later_cost','positive_diagnostic_A_count_no_certification','positive_diagnostic_I_recorded_identity','positive_unstable_unavailable_diagnostic','positive_unsupported_no_candidates','source_other_capture','hash_equality_without_domain','missing_mandatory_witness_A_forgery','unknown_cost_cannot_be_complete','suspect_prior_preserved','rebound_handle']
cross=dict(scope='INDEPENDENT_DOCUMENT_AND_SYNTHETIC_MODEL_CHECKS_NOT_RUNTIME_ACCEPTANCE',semantic_cases=[r for r in semantic_results if r['name'] in cross_names],structural_cases=[r for r in results if r['category']=='cross_contract' or r['name'].startswith('partition_ELIGIBLE_NORMAL_TERMINAL_BLOCKED') or r['name'] in ('diagnostic_selected','diagnostic_source_publication','diagnostic_certified_candidate','forbidden_NONCERTIFYING_DIAGNOSTIC_result_{}')],notes=['Guarded S is orthogonal to legacy source verification; complete new totals stay null.','I/U/X cannot make current v2.1 eligible source views.','A graph cardinality cannot override BLOCKED source provenance.','Valid C0 may remain source selected in restricted UNKNOWN terminal, with partial/null later cost.','Current F01 source verification must run against same guarded state.'])
dump(ROOT/'R1_R3_CROSS_CONTRACT_TESTS.json',cross)
print(json.dumps(summary,indent=2))
