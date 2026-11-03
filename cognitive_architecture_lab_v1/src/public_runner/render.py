"""Public-only renderer, copied in behavior from pinned public_loader (no import)."""
import json
from ..interfaces.contracts import public_task
def render_public_prompt(task):
    t=public_task(task)
    return '\n\n'.join((t['title'],t['task_statement'],'TASK_INPUT:\n'+json.dumps(t['input'],ensure_ascii=False,indent=2),
        'OUTPUT CONTRACT:\n'+json.dumps(t['output_contract'],ensure_ascii=False,indent=2),
        'Public reference identifiers: '+', '.join(t['public_reference_ids'])))
