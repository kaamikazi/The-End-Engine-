"""Task output format vs. Engine protocol format (v0.3.5).

The task's output format is what the user asked for (e.g. a ```json code block, a JSON object). The Engine protocol
format is END's internal JSON. They are different things: Engine metadata must never replace or leak into the answer.
These checks are deterministic and conservative: only explicit, mechanically checkable requirements are detected, and
leakage is reported only for Engine-internal markers that the task itself does not mention. Provenance: ENGINE_DERIVED."""
import json
import re
import ast
import sys
from dataclasses import dataclass
from .task_contract import assertion_kind


class InspectedAnswer(str):
    """Engine-selected answer content; do not parse its literal text as another wrapper."""


@dataclass(frozen=True)
class AnswerRegion:
    content: str
    status: str
    reason: str


def extract_answer_region(content, explicit=None):
    if explicit is not None:
        if not isinstance(explicit, str) or not explicit.strip() or explicit not in content:
            return AnswerRegion(content, 'AMBIGUOUS', 'adapter boundary is not a verbatim response span')
        return AnswerRegion(explicit, 'ADAPTER_BOUNDARY', 'explicit adapter-owned answer span')
    # Only actual line fences affect wrapper parsing. Incidental inline backticks do not.
    fence, boundaries, opened, obscured = None, [], False, False
    for match in re.finditer(r'(?m)^.*$', content):
        line = match[0].strip()
        marker = re.fullmatch(r'(`{3,}|~{3,})([\w+-]*)\s*', line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not marker[2]:
                fence = None
        elif line == '</think>' and fence is None:
            boundaries.append(match.end())
        elif line == '</think>' and fence is not None:
            obscured = True
        elif line == '<think>' and fence is None:
            opened = True
    if len(boundaries) > 1 or (boundaries and not content[boundaries[0]:].strip()):
        return AnswerRegion(content, 'AMBIGUOUS', 'multiple or empty final-answer boundaries')
    if boundaries:
        return AnswerRegion(content[boundaries[0]:].lstrip('\r\n'), 'WRAPPER_BOUNDARY',
                            'single standalone deliberation terminator outside line fences')
    if (opened or fence and obscured) and not boundaries:
        return AnswerRegion(content, 'AMBIGUOUS', 'unclosed deliberation wrapper')
    return AnswerRegion(content, 'WHOLE_RESPONSE', 'no output wrapper boundary')


def candidate_answer(candidate):
    value = candidate.answer_content
    return InspectedAnswer(value if value is not None else extract_answer_region(candidate.content).content)

_FENCE_REQUIRED = re.compile(r"```\s*([A-Za-z][A-Za-z0-9_+-]*)")
_JSON_VALUE = re.compile(r"\bJSON\s+(object|array)\b", re.I)
LEAKAGE = (
    (re.compile(r"\bW\d{3}\b"), "weakness identifier"),
    (re.compile(r"\bCL\d{3}\b"), "claim identifier"),
    (re.compile(r"\bcandidate\s+C\d+\b", re.I), "candidate identifier"),
    (re.compile(r"\brevision plan\b", re.I), "revision plan"),
    (re.compile(r"\b(?:quality ?gate|cognitive operator|operator selection|weakness registry)\b", re.I), "Engine machinery"),
)


def task_requirements(task, contract=None):
    """Explicit, checkable output requirements stated in the task."""
    sentences = re.split(r'(?<=[.!?])\s+|\n+', task or '')
    if contract:
        sentences += list(contract.prescriptive_constraints)
    task = '\n'.join(s for s in sentences if assertion_kind(task or '', s, contract) == 'PRESCRIPTIVE_TASK_CONSTRAINT')
    requirements = [{"kind": "fenced_block", "language": language}
                    for language in dict.fromkeys(m.lower() for m in _FENCE_REQUIRED.findall(task or ""))]
    match = _JSON_VALUE.search(task or "")
    if match:
        requirements.append({"kind": "json_value", "type": match.group(1).lower()})
    elif re.search(r'\b(?:return|output|give)\b.{0,35}\bJSON\b', task or '', re.I):
        requirements.append({'kind':'json_value','type':'any'})
    if re.search(r'\bstrict JSON\b', task or '', re.I):
        requirements.append({'kind':'strict_json'})
    if re.search(r'\b(?:briefly explain|brief explanation|explain why)\b', task or '', re.I):
        requirements.append({'kind':'explanation_present'})
    if re.search(r'\b(?:do not use|without) external libraries\b', task or '', re.I):
        requirements.append({'kind':'stdlib_imports_only'})
    literal = re.search(r'^\s*Return\s+(?:the\s+)?(\w+)\s+(-?\d+(?:\.\d+)?|"[^"\n]+")\s+as\s+(?:a\s+)?JSON object',
                        task or '', re.I)
    if literal:
        requirements.append({'kind':'literal_field','key':literal[1], 'value':json.loads(literal[2])})
    count = re.search(r'\bexactly\s+(\d+|one|two|three|four|five)\s+(?:entries|items)\b', task or '', re.I)
    if count:
        value = {'one':1,'two':2,'three':3,'four':4,'five':5}.get(count[1].lower())
        value = int(count[1]) if value is None else value
        if value <= 64:
            requirements.append({'kind':'entry_count','count':value})
    return requirements


def final_answer_region(content):
    """A standalone provider deliberation terminator outside code fences is presentation metadata.

    Preserve raw candidates in the ledger; do not expose ignored pre-final assertions
    in EngineResult.answer. Inline/literal markers are not treated as delimiters.
    """
    return str(content) if isinstance(content, InspectedAnswer) else extract_answer_region(content).content


def _json_values(content):
    blocks = re.findall(r"```(?:json)?\s*\n(.*?)```", content, re.S | re.I)
    values = []
    try:
        values.append(json.loads(content.strip()))
    except ValueError:
        pass
    for block in blocks:
        try:
            values.append(json.loads(block))
        except ValueError:
            pass
    decoder = json.JSONDecoder()
    for i, ch in enumerate(content):
        if ch in "[{":
            try:
                values.append(decoder.raw_decode(content[i:])[0])
            except ValueError:
                continue
    return values


def format_violations(task, content, contract=None):
    content = final_answer_region(content or '')
    violations = []
    for requirement in task_requirements(task, contract):
        if requirement["kind"] == "fenced_block":
            if not re.search(r"```\s*" + re.escape(requirement["language"]) + r"\b", content or "", re.I):
                violations.append(f"missing the required ```{requirement['language']} code block")
        elif requirement['kind'] == 'entry_count':
            values = [v for v in _json_values(content or '') if isinstance(v, (list, dict))]
            if not values or len(values[0]) != requirement['count']:
                violations.append(f"required exactly {requirement['count']} JSON entries")
        elif requirement['kind'] == 'strict_json':
            value = content.strip()
            if any(r['kind'] == 'fenced_block' for r in task_requirements(task, contract)):
                blocks = re.findall(r'```json\s*\n(.*?)```', value, re.S | re.I)
                value = blocks[0] if len(blocks) == 1 else ''
            try:
                json.loads(value)
            except ValueError:
                violations.append('required strict JSON without non-JSON prose')
        elif requirement['kind'] == 'explanation_present':
            prose = re.sub(r'```.*?```', '', content, flags=re.S).strip()
            if not re.search(r'\w', prose):
                violations.append('missing the explicitly requested explanation outside code')
        elif requirement['kind'] == 'stdlib_imports_only':
            blocks = re.findall(r'```python\s*\n(.*?)```', content, re.S | re.I)
            for block in blocks or ([content] if 'Python' in task else []):
                try:
                    tree = ast.parse(block)
                except (SyntaxError, RecursionError):
                    continue  # inability to inspect is not proof of an external import
                for node in ast.walk(tree):
                    names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                            [node.module] if isinstance(node, ast.ImportFrom) and node.module else []
                    for name in names:
                        if name.split('.')[0] not in sys.stdlib_module_names:
                            violations.append('external module import violates task restriction: ' + name)
        elif requirement['kind'] == 'literal_field':
            values = [v for v in _json_values(content or '') if isinstance(v, dict)]
            if not values or values[0].get(requirement['key']) != requirement['value']:
                violations.append('required literal JSON field ' + requirement['key'])
        else:
            kind = dict if requirement["type"] == "object" else list
            values = _json_values(content or '')
            if not (bool(values) if requirement['type'] == 'any' else any(isinstance(v, kind) for v in values)):
                violations.append(f"no parseable JSON {requirement['type']}")
    return violations


def internal_leakage(task, content):
    """Engine-internal markers in the answer that the task does not itself mention."""
    found, task_text = [], (task or "").lower()
    content = final_answer_region(content or '')
    for pattern, label in LEAKAGE:
        for match in pattern.finditer(content or ""):
            if match.group(0).lower() not in task_text:
                found.append(f"{label}: {match.group(0)}")
    return list(dict.fromkeys(found))


# Agreement presented as confirmation: several people/models "confirmed"/"verified", or "independently confirmed".
_AGREEING = r"(?:engineers?|judges?|reviewers?|models?|agents?|experts?|developers?|people|teams?|sources?|witnesses?)"
CONSENSUS_AS_CONFIRMATION = re.compile(
    r"\b(?:both|all|two|three|several|multiple|many)\s+(?:[\w-]+\s+){0,3}?" + _AGREEING +
    r"\b[^.;\n]{0,60}\b(?:confirm\w*|verif\w*|prove[sdn]?|establish\w*|corroborat\w*)\b"
    r"|\bindependently\s+(?:confirmed|verified|corroborated|established)\b"
    r"|\b(?:consensus|unanimous\w*|agreement)\b[^.;\n]{0,40}\b(?:confirm\w*|verif\w*|prove[sdn]?|establish\w*)\b", re.I)


# Support that rests on agreement at all (reported, or claimed as confirmation).
AGREEMENT = re.compile(
    r"\b(?:both|all|two|three|several|multiple|many)\s+(?:[\w-]+\s+){0,3}?" + _AGREEING +
    r"\b[^.;\n]{0,60}\b(?:agree\w*|confirm\w*|said|say|wrote|believe\w*|concur\w*|report\w*|verif\w*)\b"
    r"|\b(?:consensus|unanimous\w*)\b|\bindependently\s+(?:confirmed|verified|corroborated)\b", re.I)


def consensus_kind(text):
    """MODEL_CONSENSUS / REPORTED_CONSENSUS when the text rests on agreement; "" otherwise."""
    match = AGREEMENT.search(text or "")
    if not match:
        return ""
    return ("MODEL_CONSENSUS" if re.search(r"\b(?:judges?|models?|agents?)\b", match.group(0), re.I)
            else "REPORTED_CONSENSUS")


def consensus_as_confirmation(content):
    """Sentences presenting agreement (REPORTED_CONSENSUS / MODEL_CONSENSUS) as if it were verification."""
    from ..quality.epistemic import NEGATION
    content = final_answer_region(content or '')
    sentences = re.split(r"(?<=[.!?])\s+|\n+", content)
    found = []
    for sentence in sentences:
        for clause in re.split(r'\bbut\b|\bhowever\b', sentence, flags=re.I):
            for match in CONSENSUS_AS_CONFIRMATION.finditer(clause):
                status = list(re.finditer(r'\b(?:confirm\w*|verif\w*|prove\w*|establish\w*|corroborat\w*)\b', match[0], re.I))
                if status and not NEGATION.search(clause[:match.start() + status[-1].start()]):
                    found.append(sentence.strip()[:200])
    return list(dict.fromkeys(found))


def check_candidate(task, candidate_id, content, contract=None):
    return {"candidate_id": candidate_id, "provenance": "ENGINE_DERIVED", "requirements": task_requirements(task, contract),
            "format_violations": format_violations(task, content, contract), "internal_leakage": internal_leakage(task, content),
            "consensus_as_confirmation": consensus_as_confirmation(content)}
