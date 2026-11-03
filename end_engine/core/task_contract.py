"""Explicit task authority, with conservative lexical fallback; never a fact checker."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TaskContract:
    prescriptive_constraints: tuple[str, ...] = ()
    descriptive_assertions: tuple[str, ...] = ()
    mandatory_revision: bool = False
    reference_ids: tuple[str, ...] = ()

    def __post_init__(self):
        for name in ('prescriptive_constraints', 'descriptive_assertions'):
            value = getattr(self, name)
            if not isinstance(value, tuple) or len(value) > 32 or any(
                    not isinstance(s, str) or not s.strip() or len(s) > 1500 for s in value):
                raise ValueError(f'{name} must be a bounded tuple of nonempty strings')
        if type(self.mandatory_revision) is not bool:
            raise ValueError('mandatory_revision must be boolean')
        if not isinstance(self.reference_ids, tuple) or len(self.reference_ids) > 64 or any(
                not isinstance(s, str) or not re.fullmatch(r'[\w.-]{1,80}', s) for s in self.reference_ids):
            raise ValueError('reference_ids must be a bounded tuple of declared identifiers')
        if {normalize(s) for s in self.prescriptive_constraints} & {normalize(s) for s in self.descriptive_assertions}:
            raise ValueError('A task assertion cannot be both descriptive and prescriptive')


def normalize(text):
    return re.sub(r'\s+', ' ', text.replace('`', '').strip()).lower().strip(' ."\'')


_PRESCRIPTIVE = re.compile(
    r'\b(?:for this hypothetical|assume\b|suppose\b|treat .{1,80} as\b|'
    r'return\b|output\b|produce\b|do not use\b|cite only\b|give .{0,50}(?:json|code block)|use exactly\b|'
    r'must (?:return|output|use)|required .{0,30}(?:format|field|key|code block))', re.I)


def assertion_kind(task, reference, contract=None):
    """Unknown descriptive wording is TASK_PROVIDED, never verified truth.

    Only explicit caller metadata or an imperative/explicit hypothetical in the
    matching task sentence grants prescriptive authority. A judge cannot grant it.
    """
    contract = contract or TaskContract()
    ref = normalize(reference)
    if not ref:
        return 'AMBIGUOUS_TASK_PROVIDED'
    for name, kind in (('prescriptive_constraints', 'PRESCRIPTIVE_TASK_CONSTRAINT'),
                       ('descriptive_assertions', 'DESCRIPTIVE_TASK_ASSERTION')):
        if any(ref == normalize(s) or ref in normalize(s) for s in getattr(contract, name)):
            return kind
    sentences = [s for s in re.split(r'(?<=[.!?])\s+|\n+', task) if s.strip()]
    matched = [s for s in sentences if ref in normalize(s) or normalize(s) in ref]
    if not matched:
        return 'AMBIGUOUS_TASK_PROVIDED'
    kinds = {'PRESCRIPTIVE_TASK_CONSTRAINT' if _PRESCRIPTIVE.search(s) else
             'DESCRIPTIVE_TASK_ASSERTION' for s in matched}
    return next(iter(kinds)) if len(kinds) == 1 else 'AMBIGUOUS_TASK_PROVIDED'
