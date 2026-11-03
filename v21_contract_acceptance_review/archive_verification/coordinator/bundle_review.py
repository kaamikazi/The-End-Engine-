"""Mechanical packaging of completed independent reviewer-owned artifacts."""
import hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent.parent
Z=H/'V21_CONTRACT_ACCEPTANCE_REVIEW_BUNDLE.zip'
receipt=H/'V21_REVIEW_BUNDLE_RECEIPT.json'
required=['V21_INDEPENDENT_REVIEW.md','R1_SNAPSHOT_DECISION.md','R1_WRITER_DOMAIN_AUDIT.md','R1_WITNESS_CASES.csv','R1_DOWNGRADE_REVIEW.csv','R3_SCHEMA_DECISION.md','R3_STANDARD_VALIDATOR_RESULTS.json','R3_SEMANTIC_RULE_AUDIT.md','R1_R3_CROSS_CONTRACT_TESTS.json','R2_R4_R5_PRESERVATION.md','IMPLEMENTATION_PREREQUISITES.md','FINAL_VERDICT.json']
def sha(data):return hashlib.sha256(data).hexdigest()
for n in required: assert (H/n).is_file(),n
assert not Z.exists() and not receipt.exists()
assert json.loads((H/'coordinator/PRESERVATION.json').read_text())['passed']
files={p.relative_to(H).as_posix():p.read_bytes() for p in H.rglob('*') if p.is_file() and not any(part in ['archive_verification','__pycache__'] for part in p.relative_to(H).parts) and p.name not in [Z.name,receipt.name,'BUNDLE_MANIFEST.json']}
manifest={'files':{n:{'bytes':len(data),'sha256':sha(data)} for n,data in sorted(files.items())},'scope':'Independent AI contract acceptance evidence; no runtime or human scientific acceptance','reviewed_commit':'783aa1d23ba2ca8c4fd28cdaf993ea2f66b5294e','coordinator_role':'Prior author: mechanical identity, preservation and packaging only; fresh reviewer agents own judgments'}
(H/'BUNDLE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
files['BUNDLE_MANIFEST.json']=(H/'BUNDLE_MANIFEST.json').read_bytes()
with zipfile.ZipFile(Z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,data in sorted(files.items()):z.writestr(n,data)
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 assert set(z.namelist())==set(files)
 for n,data in files.items():assert z.read(n)==data
 target=H/'archive_verification';assert not target.exists()
 target.mkdir()
 for n in z.namelist():
  dest=(target/n).resolve();assert dest.is_relative_to(target.resolve())
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(n))
for n,data in files.items():assert (H/'archive_verification'/n).read_bytes()==data
record={'archive':str(Z),'bytes':Z.stat().st_size,'sha256':sha(Z.read_bytes()),'members':len(files),'required_deliverables':len(required),'zip_crc':'PASS','all_archived_member_bytes':'PASS','actual_extracted_member_bytes':'PASS','manifest_member_hashes':'PASS','receipt_is_external_to_archive':True,'git_mutations':0,'provider_calls':0,'benchmarks':0}
receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
