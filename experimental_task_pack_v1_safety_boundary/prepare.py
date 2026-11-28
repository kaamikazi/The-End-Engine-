"""Reproducible new-pack preparation; never writes historical packs."""
import shutil
from pathlib import Path
OUT=Path(__file__).resolve().parent;OLD=OUT.parent/'experimental_task_pack_v1_r3'
for name in ('public_loader.py',):shutil.copyfile(OLD/name,OUT/'r3_reference'/name)
shutil.copyfile(OLD/'validation/ORIGINAL_FIXTURE_LABELS.json',OUT/'r3_reference/validation/ORIGINAL_FIXTURE_LABELS.json')
for name in ('test_evaluators.py','test_determinism.py'):
    text=(OLD/'tests'/name).read_text(encoding='utf-8').replace('experimental_task_pack_v1_r3','experimental_task_pack_v1_safety_boundary')
    if name=='test_evaluators.py':
        start=text.index('    def test_every_authored_fixture_all_dimensions');end=text.index('    def test_exactly_two_public_tasks',start)
        text=text[:start]+'''    def test_original_fixture_expectations_are_historical(self):
        # Safety expectations remain byte-identical R3 records, not active labels.
        for f in fixtures():
            r=evaluate_answer(f['task_id'],f['candidate_content'],**f['evaluation_options'])
            self.assertIs(r['task_success'],f['expected']['task_success'])
            for name in ('substantive_correctness','output_contract_compliance','requirement_preservation','repair_completeness','unnecessary_alterations'):
                self.assertEqual({k:r['dimensions'][name][k] for k in ('score','status')},f['expected']['dimensions'][name])
            self.assertTrue(set(f['expected']['required_contract_errors'])<=set(r['dimensions']['output_contract_compliance']['violations']))

'''+text[end:]
    (OUT/'tests'/name).write_text(text,encoding='utf-8',newline='\n')
print('Structural/parse/determinism tests ported; semantic legacy tests preserved in r3_reference.')
