from ..models.schema import BRIEF, SCORE, STRING, STRINGS, obj


# v0.3.5: grounding fields are optional (additive); older judges and fixtures remain valid.
ISSUE = obj({"category": BRIEF, "description": BRIEF, "target": STRING,
             "fatal": {"type": "boolean"}, "evidence": STRINGS,
             "claim_type": {"type": "string", "enum": ["CANDIDATE_INTERNAL", "TASK_CONSTRAINT", "EXTERNAL_FACT",
                                                           "EXTERNAL_FACTUAL", "EPISTEMIC_STATUS"]},
             "source_claim": {"type": "string", "maxLength": 1500},
             "alleged_defect": {"type": "string", "maxLength": 1500},
             "basis": {"type": "string", "maxLength": 1500},
             "candidate_quote": {"type": "string", "maxLength": 1500},
             "task_reference": {"type": "string", "maxLength": 1500}},
            required=["category", "description", "target", "fatal", "evidence"])


def judgment_schema(dimensions):
    return obj({"verdict": {"type": "string", "enum": ["PASS", "NEEDS_REVISION", "FAIL", "INCONCLUSIVE"]},
                "dimensions": obj({d: obj({"score": SCORE, "confidence": SCORE}) for d in dimensions}),
                "fatal_issues": {"type": "array", "maxItems": 12, "items": ISSUE},
                "major_issues": {"type": "array", "maxItems": 12, "items": ISSUE},
                "minor_issues": {"type": "array", "maxItems": 12, "items": ISSUE},
                "uncertainties": STRINGS, "evidence": STRINGS,
                "recommended_action": {"type": "string", "enum": ["ACCEPT", "REVISE", "REJECT", "REVIEW"]}})


def comparison_schema(dimensions):
    return obj({"preferred": {"type": "string", "enum": ["A", "B", "TIE", "INCONCLUSIVE"]},
                "dimensions": obj({d: {"type": "string", "enum": ["A", "B", "TIE", "INCONCLUSIVE"]} for d in dimensions}),
                "delta": obj({d: {"type": "number", "minimum": -1, "maximum": 1} for d in dimensions}),
                "reason": BRIEF})


TESTS = obj({"tests": {"type": "array", "maxItems": 4, "items": obj({
    "target": STRING, "scenario": BRIEF, "expected_property": BRIEF,
    "execution_status": {"type": "string", "enum": ["UNEXECUTED", "REASONED", "SIMULATED", "EXECUTABLE"]}})}})
