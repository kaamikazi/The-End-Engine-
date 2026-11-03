"""AST/text inspection only: never imports or executes implementation modules."""
import ast,csv,hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;R=Path('E:/END-v102-V21-Contract-Checkpoint');D=R/'experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1'
def writecsv(p,rows,fields):
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
symbols=[];calls=[];tests=[];errors=[]
for p in sorted(R.rglob('*.py')):
 rel=p.relative_to(R).as_posix()
 if '.git' in p.parts or '__pycache__' in p.parts:continue
 try:text=p.read_text(encoding='utf-8-sig');tree=ast.parse(text)
 except (ValueError,UnicodeError,SyntaxError) as e:errors.append({'path':rel,'error':str(e)});continue
 aliases={}
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom):
   for item in n.names:aliases[item.asname or item.name]=(n.module or '')+'.'+item.name
 def visit(node,prefix=''):
  for c in ast.iter_child_nodes(node):
   if isinstance(c,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
    q=prefix+c.name;symbols.append({'path':rel,'symbol':q,'line':c.lineno,'end_line':c.end_lineno})
    if c.name.startswith('test_'):tests.append({'path':rel,'test':q,'line':c.lineno})
    visit(c,q+'.')
   else:visit(c,prefix)
 visit(tree)
 for n in ast.walk(tree):
  if not isinstance(n,ast.Call):continue
  target=ast.unparse(n.func);last=target.rsplit('.',1)[-1];resolved=aliases.get(target,target)
  if last in {'finish','publish','verify_semantics','verify_completed','_verify_completed','blocked_recovery','execute'} or resolved.endswith(('.execute','.blocked_recovery')):
   calls.append({'path':rel,'line':n.lineno,'call':target,'import_resolution':resolved,'expression':ast.get_source_segment(text,n) or target,'test_or_evidence':bool(re.search(r'(^|/)(tests?|validation|probes|bench)(/|_)',rel))})
writecsv(H/'STATIC_CALL_SITES.csv',calls,['path','line','call','import_resolution','expression','test_or_evidence'])
(H/'SOURCE_SYMBOLS.json').write_text(json.dumps(symbols,indent=2)+'\n');(H/'TEST_SYMBOLS.json').write_text(json.dumps(tests,indent=2)+'\n')
schema=json.loads((D/'R3_SCHEMA_SPECIFICATION.json').read_text(encoding='utf-8'));csvs={n:list(csv.DictReader((D/n).open(encoding='utf-8-sig',newline=''))) for n in ['R1_DOWNGRADE_MATRIX.csv','R1_SIXTEEN_CASE_REVALIDATION.csv','R3_NORMATIVE_FIELD_MATRIX.csv']}
cross=json.loads(Path('E:/The End Engine/v21_contract_acceptance_review/R1_R3_CROSS_CONTRACT_TESTS.json').read_text(encoding='utf-8'))
summary={'source_symbols':len(symbols),'call_sites':len(calls),'test_symbols':len(tests),'parse_errors':errors,'schema_definitions':list(schema['definitions']),'semantic_rules':schema['x-semantic-rules'],'contract_csvs':{k:{'rows':len(v),'columns':list(v[0]),'records':v} for k,v in csvs.items()},'cross_contract_review_structure':list(cross) if isinstance(cross,dict) else {'rows':len(cross)}}
(H/'STATIC_INSPECTION.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['contract_csvs','semantic_rules']}));print(json.dumps({'semantic_rules':summary['semantic_rules']}))
