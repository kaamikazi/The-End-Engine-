"""Introspectable taxonomy and selection priors, separate from selection code."""

FAMILIES = {
    "foundational": ("WHY", "HOW", "WHAT", "CAN"),
    "adversarial": ("WHAT_BREAKS", "WHY_NOT", "COUNTEREXAMPLE"),
    "epistemic": ("ASSUMPTION", "EVIDENCE", "VERIFY"),
    "search": ("ALTERNATIVE", "WHICH"),
    "constraint": ("CONSTRAINT", "IF"),
    "systemic": ("SECOND_ORDER_EFFECT",),
    "optimization": ("IMPROVE", "SIMPLIFY"),
}
BRANCHING = {"ALTERNATIVE", "COUNTEREXAMPLE", "IF", "WHAT_BREAKS"}
TARGET_TYPES = {
    "ASSUMPTION": ("ASSUMPTION", "WEAKNESS", "WHOLE_CANDIDATE"),
    "EVIDENCE": ("EVIDENCE_GAP", "CLAIM", "WEAKNESS"),
    "VERIFY": ("CLAIM", "ASSUMPTION", "WEAKNESS"),
    "ALTERNATIVE": ("WEAKNESS", "COMPONENT", "WHOLE_CANDIDATE"),
    "CONSTRAINT": ("WEAKNESS", "CONSTRAINT", "WHOLE_CANDIDATE"),
}
EXTRA_TARGETS = {"ASSUMPTION": ("assumptions",), "EVIDENCE": ("evidence",),
                 "VERIFY": ("evidence", "verification"),
                 "SECOND_ORDER_EFFECT": ("second_order_effects",)}
FOLLOWUPS = {
    "foundational": ("ASSUMPTION", "VERIFY"),
    "adversarial": ("CONSTRAINT", "ALTERNATIVE", "VERIFY"),
    "epistemic": ("WHAT_BREAKS", "EVIDENCE", "VERIFY"),
    "search": ("WHICH", "CONSTRAINT", "SECOND_ORDER_EFFECT"),
    "constraint": ("WHAT_BREAKS", "ALTERNATIVE"),
    "systemic": ("CONSTRAINT", "VERIFY"),
    "optimization": ("VERIFY", "WHAT_BREAKS"),
}


def metadata_for(name, triggers):
    family = next(family for family, names in FAMILIES.items() if name in names)
    targets = tuple(dict.fromkeys((*triggers, *EXTRA_TARGETS.get(name, ()))))
    return dict(family=family, targets=targets,
                best_when=(f"Open uncertainty concerns {', '.join(targets)}", "A new target remains unexamined"),
                poor_when=("Same target and intent recently yielded duplicate findings", "Task is a trivial transformation"),
                cost=0.55 if name in BRANCHING else 0.3,
                novelty_bias=0.8 if family in ("search", "adversarial") else 0.6,
                can_branch=name in BRANCHING, compatible_followups=FOLLOWUPS[family],
                preferred_target_types=TARGET_TYPES.get(name, ("WEAKNESS", "COMPONENT", "WHOLE_CANDIDATE")))
