"""Small strict JSON Schema subset; no third-party dependency needed."""
import math


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


STRING = {"type": "string", "minLength": 1}
STRINGS = {"type": "array", "items": STRING}
SCORE = {"type": "number", "minimum": 0, "maximum": 1}
FINDING = obj({"weakness_id": {"type": ["string", "null"]}, "type": STRING,
               "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
               "description": STRING, "evidence": STRING})
CANDIDATE = obj({"content": STRING, "known_strengths": STRINGS,
                 "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1}})
CRITIQUE = obj({"summary": STRING, "findings": {"type": "array", "items": FINDING}})

# Optional v0.2 artifacts keep v0.1 provider responses valid.
BRIEF = {"type": "string", "minLength": 1, "maxLength": 1500}
EVIDENCE_STATUS = {"type": "string", "enum": ["SUPPORTED", "UNVERIFIED", "CONTRADICTED", "NOT_APPLICABLE"]}
ASSUMPTION_STATUS = {"type": "string", "enum": ["UNTESTED", "SUPPORTED", "WEAKENED", "INVALIDATED", "ACCEPTED_RISK"]}
CRITIQUE["properties"].update({
    "claims": {"type": "array", "maxItems": 8, "items": obj({"text": BRIEF, "type": STRING,
        "evidence_status": EVIDENCE_STATUS, "evidence": BRIEF})},
    "assumptions": {"type": "array", "maxItems": 8, "items": obj({"statement": BRIEF,
        "risk": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        "status": ASSUMPTION_STATUS, "evidence": BRIEF})},
    "claim_updates": {"type": "array", "maxItems": 16, "items": obj({"id": STRING,
        "status": EVIDENCE_STATUS, "evidence": BRIEF})},
    "assumption_updates": {"type": "array", "maxItems": 16, "items": obj({"id": STRING,
        "status": ASSUMPTION_STATUS, "evidence": BRIEF})},
    "reframing": obj({"reframed_problem": BRIEF, "reason": BRIEF, "confidence": SCORE}),
})
PLAN = obj({"changes": {"type": "array", "items": obj({
    "targets": STRINGS, "action": STRING, "expected_effect": STRING})}})
ANALYSIS = obj({"complexity": {"type": "string", "enum": ["fast", "normal", "deep", "critical"]},
                "confidence": SCORE, "dimensions": {"type": "array", "items": STRING, "minItems": 1},
                "rationale": STRING})
SELECTION = obj({"operator": STRING, "reason": STRING, "priority": SCORE})


def verification_schema(dimensions):
    return obj({"passed": {"type": "boolean"}, "score": SCORE,
                "dimensions": obj({d: SCORE for d in dimensions}), "remaining_issues": STRINGS,
                "weakness_updates": {"type": "array", "items": obj({"id": STRING,
                    "status": {"type": "string", "enum": ["open", "resolved", "accepted_risk", "invalidated"]},
                    "reason": STRING})}})


def validate(value, schema, path="$", *, _depth=0):
    if _depth > 100:
        raise ValueError("Structured output exceeds maximum nesting")
    kind = schema.get("type")
    kinds = kind if isinstance(kind, list) else [kind]
    matches = {"null": value is None, "string": isinstance(value, str),
               "boolean": type(value) is bool, "integer": type(value) is int,
               "number": type(value) in (int, float), "object": isinstance(value, dict),
               "array": isinstance(value, list)}
    if not any(matches.get(k, False) for k in kinds):
        raise ValueError(f"{path}: expected {kind}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: invalid enum value {value!r}")
    if type(value) in (int, float):
        if not math.isfinite(value) or value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            raise ValueError(f"{path}: number outside allowed range")
    if isinstance(value, str) and len(value.strip()) < schema.get("minLength", 0):
        raise ValueError(f"{path}: empty string")
    if isinstance(value, str) and len(value) > schema.get("maxLength", math.inf):
        raise ValueError(f"{path}: string too long")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            raise ValueError(f"{path}: missing keys {sorted(missing)}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False and value.keys() - props.keys():
            raise ValueError(f"{path}: unexpected keys {sorted(value.keys() - props.keys())}")
        for key, item in value.items():
            if key in props:
                validate(item, props[key], f"{path}.{key}", _depth=_depth + 1)
    if isinstance(value, list):
        if len(value) > schema.get("maxItems", math.inf):
            raise ValueError(f"{path}: too many items")
        if len(value) < schema.get("minItems", 0):
            raise ValueError(f"{path}: too few items")
        for i, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{i}]", _depth=_depth + 1)
    return value
