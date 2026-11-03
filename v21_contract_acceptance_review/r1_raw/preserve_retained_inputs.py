"""Copy only the sixteen small synthetic fixtures and reviewed contract docs."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
inspection=json.loads((ROOT/'RETAINED_EVIDENCE_INSPECTION.json').read_text(encoding='utf-8'))
receipt=[]
for case in inspection['cases']:
    source=Path(case['path']);dest=ROOT/'retained_fixtures'/source.name
    for item in case['inventory']:
        src=source/item['path'];dst=dest/item['path'];raw=src.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==item['sha256']
        dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists(): assert dst.read_bytes()==raw
        else: shutil.copy2(src,dst)
        assert dst.read_bytes()==raw
        receipt.append({'original':str(src),'copy':dst.relative_to(ROOT).as_posix(),'sha256':item['sha256'],'bytes':len(raw)})
source_docs=Path(r'E:\END-v102-V21-Contract-Checkpoint\experimental_architectures_v1_r3\validation\contract_reconciliation_v2_1')
for item in inspection['documents']:
    src=source_docs/item['name'];dst=ROOT/'contract_documents'/item['name'];raw=src.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists(): assert dst.read_bytes()==raw
    else: shutil.copy2(src,dst)
    receipt.append({'original':str(src),'copy':dst.relative_to(ROOT).as_posix(),'sha256':item['sha256'],'bytes':len(raw)})
(ROOT/'PRESERVED_INPUT_COPY_RECEIPT.json').write_text(json.dumps({'scope':'Small controlled synthetic forensic fixtures plus exact contract documents; path-bound copied evidence is not a relocatable valid certificate','files':receipt,'file_count':len(receipt),'total_bytes':sum(r['bytes'] for r in receipt),'all_bytes_verified':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(receipt),'bytes':sum(r['bytes'] for r in receipt),'all_bytes_verified':True}))
