from .base import CognitiveOperator
from .metadata import metadata_for


def default_operators():
    specifications = [
        ("WHY", "Check causal justification", ("causality", "correctness"),
         "Which important conclusions lack a causal justification? Identify what would establish the link."),
        ("HOW", "Make mechanisms executable", ("implementation", "completeness"),
         "Inspect how the proposed mechanism actually works. Identify missing operational steps and interfaces."),
        ("IF", "Test conditional behavior", ("uncertainty", "robustness"),
         "Vary an important operating condition. Which conclusion no longer follows and under what conditions?"),
        ("WHAT", "Clarify scope and definitions", ("ambiguity", "completeness"),
         "Identify ambiguous requirements, missing definitions, or outputs the task needs but the answer omits."),
        ("WHICH", "Check selection criteria", ("tradeoff", "alternatives"),
         "Which decision depends on unstated selection criteria? Compare the relevant tradeoffs."),
        ("CAN", "Check feasibility", ("feasibility", "constraints"),
         "Can this proposal be implemented within the stated resources and constraints? Find feasibility gaps."),
        ("WHAT_BREAKS", "Discover structural failure modes", ("failure_mode", "failure_modes", "robustness"),
         "Assume the proposal has been deployed and failed badly. Identify plausible structural causes, "
         "including overload, partial failure, recovery, and adversarial inputs."),
        ("WHY_NOT", "Challenge rejected choices", ("tradeoff", "alternatives"),
         "Challenge a rejected or ignored approach. Is its exclusion justified by evidence and constraints?"),
        ("IMPROVE", "Find material improvements", ("quality", "completeness"),
         "Find the change most likely to improve task outcomes materially. Explain its expected effect and cost."),
        ("ASSUMPTION", "Surface hidden dependencies", ("assumption", "uncertainty", "architecture"),
         "Identify hidden assumptions that the current answer depends on. State how each could be checked."),
        ("COUNTEREXAMPLE", "Falsify broad claims", ("counterexample", "correctness"),
         "Construct a concrete counterexample to a central claim. Explain exactly which claim it falsifies."),
        ("ALTERNATIVE", "Consider a different approach", ("architecture", "alternatives"),
         "Identify a materially different approach and the conditions in which it outperforms this proposal."),
        ("EVIDENCE", "Audit evidential support", ("evidence", "correctness"),
         "Identify unsupported factual or quantitative claims. Specify the evidence required to substantiate them."),
        ("CONSTRAINT", "Check requirement compliance", ("constraint", "constraints", "completeness"),
         "Check the answer against explicit task constraints. Identify a concrete violation or untested guarantee."),
        ("SECOND_ORDER_EFFECT", "Check downstream consequences", ("downstream", "safety", "failure_modes"),
         "Identify delayed consequences, feedback loops, and incentives introduced by the proposal."),
        ("SIMPLIFY", "Remove unnecessary complexity", ("complexity", "clarity"),
         "Find complexity that can be removed while preserving requirements. Identify the cost it currently imposes."),
        ("VERIFY", "Demand falsifiable checks", ("verification", "correctness"),
         "Identify important claims without a falsifiable check. Specify a test and an observable pass criterion."),
    ]
    return {name: CognitiveOperator(name, purpose, triggers, prompt, **metadata_for(name, triggers))
            for name, purpose, triggers, prompt in specifications}


__all__ = ["CognitiveOperator", "default_operators"]
