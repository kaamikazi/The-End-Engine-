"""Copy exact reviewed documents into the reviewer bundle; never alter originals."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent.parent
sources=[(Path('E:/END-v102-V21-Contract-Checkpoint/experimental_architectures_v1_r3/validation/contract_reconciliation_v2_1'),'specification'),(Path('E:/The End Engine/v2_contract_acceptance_review_20261020/review'),'prior_v2_review')]
manifest={}
for source,label in sources:
 for p in source.iterdir():
  if not p.is_file():continue
  target=H/'review_inputs'/label/p.name
  assert not target.exists()
  data=p.read_bytes();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  manifest[target.relative_to(H).as_posix()]={'source':str(p),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
(H/'coordinator/REVIEW_INPUTS_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'exact_copied_input_files':len(manifest)}))
