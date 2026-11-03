import json
import re
import os


def redact(text):
    """Defensive projection redaction; only projected fields are ever serialized."""
    text = str(text)
    for name in ("TYPESAFE_API_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY","GEMINI_API_KEY","GITHUB_TOKEN","HF_TOKEN"):
        value = os.environ.get(name, "").strip()
        if len(value) >= 8:
            text = text.replace(value, "[REDACTED]")
    patterns = (r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{12,}", r"\b(?:ghp_|github_pat_|AIza|hf_)[A-Za-z0-9_-]{12,}",
                r"(?i)\bbearer\s+\S+", r"(?i)\b(?:[A-Z_]*API_KEY|PASSWORD|SECRET|AUTHORIZATION)\s*[:=]\s*\S+")
    for pattern in patterns:
        text = re.sub(pattern, "[REDACTED]", str(text))
    return str(text)


class DecisionContextBuilder:
    def build(self, state, ranking, operators, *, remaining_calls):
        families = sorted({operators[r.operator].family for r in ranking})
        utilities = {family: round(max(r.utility for r in ranking if operators[r.operator].family == family), 3)
                     for family in families}
        data = {"candidate_id": state.current_candidate_id, "mode": state.complexity,
                "unresolved_issues": [{"id": w.id, "category": w.type, "severity": w.severity,
                                       "description": redact(w.description)[:160]} for w in state.open_weaknesses[:8]],
                "available_families": families, "family_utility": utilities,
                "recent_family_history": [o.family for o in state.recent_outcomes[-6:]],
                "repetition": [{"operator": r.operator, "penalty": round(r.scores.repetition_penalty, 3)} for r in ranking[:8]],
                "remaining_budget": {**dict(state.remaining_budget), "decision_calls": remaining_calls}}
        return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
