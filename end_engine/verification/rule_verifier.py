from ..core.state import VerificationResult


class BasicRuleVerifier:
    """Deterministic content checks, not a semantic correctness assessment."""

    def __init__(self, *, min_characters=1, required_terms=(), forbidden_terms=()):
        if type(min_characters) is not int or min_characters < 1:
            raise ValueError("min_characters must be a positive integer")
        self.min_characters = min_characters
        self.required_terms = tuple(required_terms)
        self.forbidden_terms = tuple(forbidden_terms)

    def verify(self, task, candidate, trajectory):
        content = candidate.content.casefold()
        issues = []
        if len(candidate.content.strip()) < self.min_characters:
            issues.append(f"Content shorter than {self.min_characters} characters")
        missing = [term for term in self.required_terms if term.casefold() not in content]
        forbidden = [term for term in self.forbidden_terms if term.casefold() in content]
        issues.extend(f"Missing required term: {term}" for term in missing)
        issues.extend(f"Forbidden term: {term}" for term in forbidden)
        checks = 1 + len(self.required_terms) + len(self.forbidden_terms)
        score = 1 - len(issues) / checks
        return VerificationResult(not issues, score, (("rule_compliance", score),), tuple(issues),
                                  verifier="basic_rules")
