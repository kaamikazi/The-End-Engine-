"""One targeted attempt per malformed result; run-local, stage-local futility suppression."""
from collections import Counter


class RepairPolicy:
    def __init__(self, trajectory, failure_limit=2):
        self.trajectory, self.failure_limit = trajectory, failure_limit
        self.failures, self.active = Counter(), set()
        self.unknown_savings = False
        self.counts = Counter(repair_attempted=0, repair_succeeded=0, repair_failed=0,
                              repair_suppressed=0, invalid_elements_discarded=0,
                              calls_saved_by_suppression=0)
        self._save()

    def _save(self):
        self.trajectory.set('repair_statistics', {**self.counts, 'failures_by_stage': dict(self.failures),
                            'pending_stages': sorted(self.active), 'failure_limit': self.failure_limit,
                            'calls_saved_by_suppression': None if self.unknown_savings else
                                                        self.counts['calls_saved_by_suppression']})

    def begin(self, stage):
        reason = ('one targeted attempt already used for this result' if stage in self.active else
                  'stage has reached run-local repair failure limit' if self.failures[stage] >= self.failure_limit else None)
        if reason:
            self.counts['repair_suppressed'] += 1
            budget = getattr(self.trajectory, 'call_budget', None)
            saved = None if budget is not None and budget.remaining == 0 else 1
            if saved is None:
                self.unknown_savings = True
            else:
                self.counts['calls_saved_by_suppression'] += saved
            self.trajectory.record('protocol_event', {'stage': stage, 'action': 'repair_suppressed',
                'reason': reason, 'failures': self.failures[stage], 'calls_saved': saved}, 'protocol_events')
            self._save()
            return False
        self.active.add(stage)
        self.counts['repair_attempted'] += 1
        self._save()
        return True

    def finish(self, stage, succeeded):
        if stage not in self.active:
            return
        self.active.remove(stage)
        self.counts['repair_succeeded' if succeeded else 'repair_failed'] += 1
        if not succeeded:
            self.failures[stage] += 1
        self.trajectory.record('repair_outcome', {'stage': stage, 'accepted_and_used': succeeded,
            'outcome': 'repair_succeeded' if succeeded else 'repair_failed'}, 'repair_outcomes')
        self._save()

    def discarded(self, count):
        self.counts['invalid_elements_discarded'] += count
        self._save()


def repair_policy(trajectory, failure_limit=2):
    if not hasattr(trajectory, '_repair_policy'):
        trajectory._repair_policy = RepairPolicy(trajectory, failure_limit)
    return trajectory._repair_policy
