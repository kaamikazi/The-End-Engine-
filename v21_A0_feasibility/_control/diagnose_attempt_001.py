"""Read-only diagnosis of the failed new supplemental probe; no assertion edits."""
import json,os,sys
from pathlib import Path
E=Path(__file__).resolve().parent.parent;C=E/'checkout';os.environ['A0_SOURCE_CHECKOUT']=str(C)
sys.path.insert(0,str(E/'runs/attempt_001/executed_scaffolding'))
import probe_workers as w
result={}
for name in ['corrupt','missing_reservation']:
 root=E/'runs/attempt_001/A0-11'/name;pub=w.context(root);report=w.verify_journals(pub);result[name]={'standalone_journal_status':report['overall'],'standalone_graph_status':report.get('provenance_graph',{}).get('overall'),'unchanged_completed_core':w.protected_core(pub)}
result['counter_receipt']=w.COUNTERS
out=E/'_control/ATTEMPT_001_DIAGNOSIS.json';assert not out.exists();w.write_json(out,result)
print(json.dumps({n:{'journal':r['standalone_journal_status'],'graph':r['standalone_graph_status'],'core':r['unchanged_completed_core']['core']} for n,r in result.items() if n!='counter_receipt'}))
