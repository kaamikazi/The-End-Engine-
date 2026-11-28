"""Future runners load only public task information. No evaluator/fixture imports."""
import json
from pathlib import Path

PUBLIC_KEYS=('task_id','title','task_statement','input','output_contract','public_reference_ids')
def load_public_task(task_id):
    if task_id not in ('EXP-001','EXP-002'):raise ValueError('Unknown public task ID')
    path=Path(__file__).resolve().parent/'tasks'/f'{task_id}.json'
    task=json.loads(path.read_text(encoding='utf-8'))
    if set(task)!=set(PUBLIC_KEYS):raise ValueError('Public task contains unapproved material')
    return task

def render_public_prompt(task_id):
    t=load_public_task(task_id)
    return '\n\n'.join((t['title'],t['task_statement'],'TASK_INPUT:\n'+json.dumps(t['input'],ensure_ascii=False,indent=2),
        'OUTPUT CONTRACT:\n'+json.dumps(t['output_contract'],ensure_ascii=False,indent=2),
        'Public reference identifiers: '+', '.join(t['public_reference_ids'])))
