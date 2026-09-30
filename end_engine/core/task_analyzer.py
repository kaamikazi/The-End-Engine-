import re
from dataclasses import replace

from .state import Complexity, ReasoningBudget, TaskAnalysis, to_data
from ..models.base import ModelRequest
from ..models.schema import ANALYSIS, validate


BUDGETS = {
    Complexity.FAST: ReasoningBudget(0, 0, 0),
    Complexity.NORMAL: ReasoningBudget(1, 2, 3),
    Complexity.DEEP: ReasoningBudget(2, 4, 6),
    Complexity.CRITICAL: ReasoningBudget(3, 5, 8),
}


class TaskAnalyzer:
    def analyze(self, task, provider=None, *, use_llm=False, mode=None, max_cycles=None):
        analysis = self._heuristic(task)
        if use_llm and mode is None:
            if provider is None:
                raise ValueError("LLM classification requires a provider")
            data = provider.generate_structured(ModelRequest(
                "classification", "Classify the task by ambiguity, dependencies, consequence and verification difficulty. "
                "FAST is a narrow transformation; NORMAL ordinary work; DEEP synthesis/design; "
                "CRITICAL high-consequence or explicitly maximum-quality work. Return a concise rationale.",
                {"task": task, "heuristic": to_data(analysis)}, ANALYSIS)).content
            validate(data, ANALYSIS)
            complexity = Complexity(data["complexity"])
            analysis = TaskAnalysis(complexity, data["confidence"], BUDGETS[complexity],
                                    tuple(dict.fromkeys(data["dimensions"])), data["rationale"], "llm")
        if mode is not None:
            complexity = Complexity(mode)
            analysis = replace(analysis, complexity=complexity, reasoning_budget=BUDGETS[complexity],
                               source="override", rationale=f"User-selected {mode} mode")
        if max_cycles is not None:
            budget = analysis.reasoning_budget
            # FAST always remains zero-cycle; explicit caps may also lower minimums.
            cap = 0 if analysis.complexity is Complexity.FAST else max_cycles
            analysis = replace(analysis, reasoning_budget=ReasoningBudget(
                min(budget.min_cycles, cap), min(budget.target_cycles, cap), cap))
        return analysis

    def _heuristic(self, task):
        lower = task.lower()
        words = re.findall(r"\b\w+\b", lower)
        clauses = len(re.findall(r"[;\n]|\b(?:must|unless|while|without|provided|subject to)\b", lower))
        questions = task.count("?")
        enumerated = len(re.findall(r"(?:^|\n)\s*(?:\d+[.)]|[-*])\s", task))
        constraints = clauses + enumerated
        risk = bool(re.search(r"\b(?:irreversible|life.critical|safety.critical|production data|maximum quality|high.consequence|major system architecture)\b", lower))
        synthesis = bool(re.search(r"\b(?:architectur\w*|research|synthesi\w*|strategy|proof|prove|debug\w*|trade.?offs?|design)\b", lower))
        narrow = bool(re.match(r"\s*(?:uppercase|lowercase|capitalize|format|convert|sort|calculate|what is \d|reverse)\b", lower))
        # Structural signals make long, constrained, multi-part requests expensive even
        # without domain keywords. Short unfamiliar requests conservatively use NORMAL.
        load = (len(words) >= 80) + (constraints >= 3) + (questions >= 3) + synthesis
        if risk:
            level, confidence = Complexity.CRITICAL, 0.88
        elif synthesis or load >= 2:
            level, confidence = Complexity.DEEP, 0.82
        elif narrow and len(words) <= 35 and constraints <= 1 and questions <= 1:
            level, confidence = Complexity.FAST, 0.90
        else:
            level, confidence = Complexity.NORMAL, 0.65
        dimensions = ("correctness", "completeness", "robustness", "clarity")
        if synthesis:
            dimensions += ("architecture", "failure_modes", "alternatives")
        if risk:
            dimensions += ("safety",)
        return TaskAnalysis(level, confidence, BUDGETS[level], dimensions,
                            f"{len(words)} words, {constraints} constraint/structure signals, "
                            f"{questions} questions; synthesis={synthesis}, high_consequence={risk}")
