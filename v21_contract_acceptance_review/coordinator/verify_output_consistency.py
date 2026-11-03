"""Mechanical consistency checks; no acceptance judgment."""
import csv,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent.parent
out={'scope':'Mechanical agreement of reported counts and reviewer raw results, not acceptance judgment','raw_result_files':{}}
summary=json.loads((H/'R3_STANDARD_VALIDATOR_RESULTS.json').read_text())
for name,key in [('STRUCTURAL_RAW_RESULTS.json','structural_fixtures'),('SEMANTIC_RAW_RESULTS.json','semantic_oracle_cases'),('STRICT_PARSE_RESULTS.json','strict_parsing_cases')]:
 data=(H/'r3_raw'/name).read_bytes();rows=json.loads(data)
 assert len(rows)==summary[key] and all(r['expectation_match'] for r in rows)
 out['raw_result_files'][name]={'expectations':len(rows),'mismatches':0,'sha256':hashlib.sha256(data).hexdigest()}
out['csv_rows']={n:len(list(csv.DictReader((H/n).open(encoding='utf-8-sig',newline='')))) for n in ['R1_WITNESS_CASES.csv','R1_DOWNGRADE_REVIEW.csv']}
assert list(out['csv_rows'].values())==[16,20]
out['passed']=True
(H/'coordinator/OUTPUT_CONSISTENCY.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
