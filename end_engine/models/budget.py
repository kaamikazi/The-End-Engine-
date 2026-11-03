"""A run-wide call counter shared by generators, judges, tools and decision providers."""
from collections import Counter


class RunBudgetExceeded(RuntimeError):
    pass


class RunCallBudget:
    def __init__(self, limit):
        if type(limit) is not int or limit < 0:
            raise ValueError("Run call limit must be a nonnegative integer")
        self.limit, self.used, self.by_kind = limit, 0, Counter()

    @property
    def remaining(self):
        return max(0, self.limit-self.used)

    def reserve(self, kind):
        if self.remaining == 0:
            raise RunBudgetExceeded("Shared run call budget exhausted")
        self.used += 1
        self.by_kind[kind] += 1

    def snapshot(self):
        return {"limit": self.limit, "used": self.used, "remaining": self.remaining, "by_kind": dict(self.by_kind)}
