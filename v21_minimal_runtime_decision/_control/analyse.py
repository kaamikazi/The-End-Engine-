"""Static text/AST analysis only. No project imports or runtime execution."""
import ast,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('E:/The End Engine/v21_A0_feasibility/checkout')
FEAS=Path('E:/The End Engine/v21_minimum_evidence_feasibility')
NAMES={'lock','_write','_read','register','reserve','finish','state','summary','dispatch','reserve_request','close_generation','_closed_runs','event','claim','release','detach','publish','verify_completed','_verify_completed','append_journal','prepare','finish_entry','record_reservation','record_settlement','durable','exclusive_publish','mkdir','write_text','write_bytes','replace','rename','unlink','link','open','save','Ledger','Publication','Session','NativeGateway','StageTransport','run_baseline','baseline','blocked_recovery'}
def save(name,value):(ROOT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def scope(rel):
 parts=rel.split('/')
 if any(p in {'tests','validation','feasibility_v21','benchmarks'} for p in parts) or parts[-1].startswith(('test_','validate')):return 'TEST_VALIDATION_OR_RESEARCH_NOT_PRODUCTION_ENROLLMENT'
 if parts[0] in {'experimental_architectures_v1','experimental_architectures_v1_r2'}:return 'HISTORICAL_SOURCE_UNENROLLED'
 return 'SOURCE_CANDIDATE_REQUIRES_PROFILE_ADMISSION'
def main():
 files=sorted(SOURCE.rglob('*.py'));rows=[];defs=[];failures=[];ledger_writes=[];private_candidates=[];all_hashes={}
 for path in files:
  if '.git' in path.relative_to(SOURCE).parts:continue
  raw=path.read_bytes();rel=path.relative_to(SOURCE).as_posix();all_hashes[rel]=sha(raw)
  try:text=raw.decode('utf-8-sig');tree=ast.parse(text,filename=str(path))
  except (UnicodeError,SyntaxError) as e:failures.append({'file':rel,'error':str(e)});continue
  parents={child:parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
  imports={}
  for node in tree.body:
   if isinstance(node,ast.ImportFrom):
    for alias in node.names:imports[alias.asname or alias.name]=('.'*node.level+(node.module or '')+'.'+alias.name)
   elif isinstance(node,ast.Import):
    for alias in node.names:imports[alias.asname or alias.name.split('.')[0]]=alias.name
  def enclosing(node):
   chain=[];p=parents.get(node)
   while p is not None:
    if isinstance(p,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):chain.append(p.name)
    p=parents.get(p)
   return '.'.join(reversed(chain)) or '<module>'
  for node in ast.walk(tree):
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
    parent=enclosing(node);defs.append({'file':rel,'symbol':(parent+'.' if parent!='<module>' else '')+node.name,'line':node.lineno,'end_line':node.end_lineno,'file_sha256':sha(raw)})
   if not isinstance(node,ast.Call):continue
   name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
   if name not in NAMES:continue
   expr=ast.unparse(node.func);caller=enclosing(node);context=[];p=parents.get(node)
   while p is not None:
    if isinstance(p,(ast.With,ast.AsyncWith)):context.extend(ast.unparse(item.context_expr) for item in p.items)
    p=parents.get(p)
   binding='UNRESOLVED_RECEIVER_NOT_ASSUMED_LEDGER';confidence='SYNTACTIC_CANDIDATE'
   if rel=='cognitive_architecture_lab_v1/src/accounting/ledger.py' and expr.startswith('self.'):
    binding='Ledger instance method in defining class';confidence='EXACT_DEFINITION_AND_SELF_BINDING'
   elif name=='Ledger':binding=imports.get('Ledger','UNKNOWN_Ledger_BINDING');confidence='IMPORT_BINDING_ONLY'
   elif '.ledger.' in expr or expr.startswith('ledger.'):
    reviewed=rel.split('/')[0] in {'experimental_architectures_v1_r3','native_model_integration_v1','runtime_isolation_v1','cognitive_architecture_lab_v1'} and '/src/' in rel
    binding=('Budget Ledger receiver evidenced in reviewed current import/constructor flow; no dynamic trace' if reviewed else 'UNRESOLVED_LEDGER_NAMED_RECEIVER_NOT_ASSUMED_BUDGET_LEDGER')
    confidence='MANUAL_CRITICAL_FLOW_PLUS_SYNTAX' if reviewed else 'HISTORICAL_TEST_OR_OTHER_LEDGER_RECEIVER_UNRESOLVED'
   elif name in imports:binding=imports[name];confidence='IMPORT_BINDING_ONLY'
   effect='MUTATION_OR_INITIALIZATION' if name in {'_write','register','reserve','finish','close_generation','event','claim','detach','publish','append_journal','prepare','finish_entry','record_reservation','record_settlement','durable','exclusive_publish','mkdir','write_text','write_bytes','replace','rename','unlink','link','Ledger','Publication','Session','NativeGateway','StageTransport','run_baseline','baseline','blocked_recovery'} else 'READ_LOCK_OR_CALL_BOUNDARY_REQUIRING_CONTEXT'
   boundary='Classify actual receiver/resource; no automatic closed-domain claim'
   if rel=='cognitive_architecture_lab_v1/src/accounting/ledger.py':boundary='Proposed new outer L2 in Ledger.lock before existing L3/control open; _write ownership assertion before pending create'
   elif name in {'durable','append_journal'}:boundary='Proposed storage-sink L2 keyed to actual enrolled ledger; never hold it across later L1/D acquisition'
   elif name=='close_generation':boundary='D then L2 through closure read/merge/pending/replace, not only inner ledger read'
   rows.append({'source_file':rel,'absolute_file':str(path),'line':node.lineno,'caller_symbol':caller,'callee_expression':expr,'callee_name':name,'receiver_binding':binding,'binding_confidence':confidence,'effect_category':effect,'lexical_with_context':json.dumps(context),'call_text':(ast.get_source_segment(text,node) or '')[:900],'file_sha256':sha(raw),'scope':scope(rel),'proposed_boundary_or_disposition':boundary,'limitation':'Static candidate edge, not dynamic invocation, authenticated origin or host-wide completeness'})
   if name=='_write':
    private_candidates.append({'file':rel,'caller':caller,'line':node.lineno,'expression':expr,'lexical_with_context':context})
    if rel=='cognitive_architecture_lab_v1/src/accounting/ledger.py' and expr=='self._write':ledger_writes.append({'caller':caller,'line':node.lineno,'under_self_lock':any(x=='self.lock()' for x in context)})
 assert len(ledger_writes)==4 and all(x['under_self_lock'] for x in ledger_writes)
 with (ROOT/'COMPLETE_WRITER_CALL_GRAPH.csv').open('w',encoding='utf-8',newline='') as stream:
  writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 save('_control/SOURCE_SYMBOLS.json',defs);save('_control/SOURCE_HASHES.json',all_hashes)
 save('_control/CALL_GRAPH_SCOPE.json',{'python_files_read':len(all_hashes),'candidate_edges':len(rows),'parse_failures':failures,'ledger_internal_write_calls':ledger_writes,'all_private_write_candidates':private_candidates,'complete_means':'All syntactic candidates in the enumerated checkout Python file set; unresolved/dynamic/external actor edges are explicitly not a closed-domain proof. Current code path analysis qualifies the critical edges separately.','runtime_imports':0,'runtime_tests':0,'actual_writer_enrollment':False})
 contract=SOURCE/'experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1';inputs={}
 for folder in (contract,FEAS):
  selected=list(folder.iterdir()) if folder==contract else [folder/name for name in ['MINIMUM_EVIDENCE_FEASIBILITY_REPORT.md','WRITER_EXCLUSION_ASSESSMENT.md','SIX_CONDITION_ACCOUNTING_MATRIX.csv','PHYSICAL_ATTEMPT_EVIDENCE_MATRIX.csv','COST_COMPARABILITY_DECISION.md','NEGATIVE_CONTROL_RESULTS.json','SCIENTIFIC_READINESS_GAPS.md','NEXT_IMPLEMENTATION_SCOPE.md','FINAL_DECISION.json','SOURCE_PRESERVATION.json']]
  for p in selected:
   if p.is_file():
    raw=p.read_bytes();text=raw.decode('utf-8');inputs[str(p)]={'sha256':sha(raw),'bytes':len(raw)}
    if p.suffix=='.json':json.loads(text)
    elif p.suffix=='.csv':list(csv.DictReader(text.splitlines()))
 ip=Path('E:/The End Engine/v21_implementation_masterplan/IP01_IP09_TRACEABILITY.csv');prerequisites=list(csv.DictReader(ip.open(encoding='utf-8',newline='')));assert [x['ID'] for x in prerequisites]==['IP'+str(i).zfill(2) for i in range(1,10)];save('_control/IP01_IP09_READ.json',prerequisites);inputs[str(ip)]={'sha256':sha(ip.read_bytes()),'rows':9};save('_control/INPUT_READ_RECEIPT.json',inputs)
 if not (ROOT/'_control/INSPECTION_LIMITS.json').exists():
  save('_control/INSPECTION_LIMITS.json',{'scope':'Earlier optional guessed-path errors, not runtime or test failures','attempts':[{'path':'end_engine/trajectory.py','actual_error':'rg: The system cannot find the file specified. (os error 2)','combined_shell_exit':0,'underlying_rg_exit':'NOT_SEPARATELY_RECORDED'},{'path':'end_engine/ledger/','actual_error':'rg: The system cannot find the file specified. (os error 2)','combined_shell_exit':1}],'resolved_actual_paths':['end_engine/experience/ledger.py:JsonLedger.save','end_engine/experience/schema.py:Trajectory'],'required_source_file_unavailable':False,'runtime_tests':0})
 print(json.dumps({'python_files_read':len(all_hashes),'candidate_call_edges':len(rows),'parse_failures':len(failures),'ledger_internal_write_calls':ledger_writes,'private_write_candidate_count':len(private_candidates),'contract_and_report_inputs':len(inputs)}),flush=True)
if __name__=='__main__':main()
