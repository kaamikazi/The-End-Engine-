"""Writes the frozen Benchmark Alpha task pack (tasks/BA-*.json). Run once; the task-set hash is recorded in manifests.

Only `prompt` is ever sent to a model. `evaluation` holds hidden expectations used by the external evaluator."""
import json
from pathlib import Path

JSON_EVIDENCE_FORMAT = ('Give your final answer as one JSON object in a ```json code block with exactly these keys: '
                        '"conclusion" (string), "certainty" (one of "established", "likely", "hypothesis", "unknown"), '
                        '"evidence_used" (list of evidence IDs you relied on), "additional_evidence_needed" (list of strings).')

TASKS = [
    {"task_id": "BA-001", "category": "easy_transformation", "difficulty": "easy",
     "prompt": "Convert these Celsius temperatures to Fahrenheit, rounded to one decimal place: [-40, 0, 36.6, 100, 21.5]. "
               "Give the final answer as a JSON array of numbers, in the same order, in a ```json code block.",
     "constraints": ["same order", "one decimal place", "JSON array"],
     "evaluation": {"type": "known_answer", "evaluator": "numeric_list",
                    "expected": [-40.0, 32.0, 97.9, 212.0, 70.7], "tolerance": 0.051},
     "expected_properties": ["exact converted values"],
     "failure_conditions": ["any value wrong", "no parseable JSON array"],
     "purpose": "Detect unnecessary END overhead on a task direct inference should solve."},
    {"task_id": "BA-002", "category": "debugging", "difficulty": "easy",
     "prompt": "This function has bugs. Fix it so that it matches its docstring, and give the complete corrected function "
               "in a ```python code block.\n\n```python\ndef chunk(items, size):\n    \"\"\"Split the list `items` into "
               "consecutive lists of length `size`; the last list may be shorter.\n    `size` must be a positive integer; "
               "raise ValueError otherwise.\"\"\"\n    result = []\n    for i in range(0, len(items) - size, size):\n"
               "        result.append(items[i:i + size])\n    return result\n```",
     "constraints": ["function name chunk", "raise ValueError for non-positive size"],
     "evaluation": {"type": "executable_test", "evaluator": "python_tests", "function": "chunk", "tests": [
         {"args": [[1, 2, 3, 4, 5], 2], "expect": [[1, 2], [3, 4], [5]]},
         {"args": [[], 3], "expect": []},
         {"args": [[1, 2, 3], 3], "expect": [[1, 2, 3]]},
         {"args": [[1, 2], 5], "expect": [[1, 2]]},
         {"args": [[1, 2, 3, 4], 1], "expect": [[1], [2], [3], [4]]},
         {"args": [[1, 2], 0], "raises": "ValueError"},
         {"args": [[1, 2], -1], "raises": "ValueError"}]},
     "expected_properties": ["last partial chunk kept", "ValueError on size <= 0"],
     "failure_conditions": ["any unit test fails", "no function found"]},
    {"task_id": "BA-003", "category": "algorithm", "difficulty": "medium",
     "prompt": "Write `def min_rooms(meetings)` returning the minimum number of rooms needed so that no two overlapping "
               "meetings share a room. Each meeting is a (start, end) pair of integers with start < end; a meeting ending "
               "at time t does not overlap one starting at t. `meetings` may be empty and is not necessarily sorted. "
               "Give the final function in a ```python code block.",
     "constraints": ["function name min_rooms", "touching intervals do not overlap"],
     "evaluation": {"type": "executable_test", "evaluator": "python_tests", "function": "min_rooms", "tests": [
         {"args": [[]], "expect": 0},
         {"args": [[[0, 30], [5, 10], [15, 20]]], "expect": 2},
         {"args": [[[1, 5], [5, 10]]], "expect": 1},
         {"args": [[[1, 10], [2, 3], [3, 4], [4, 5]]], "expect": 2},
         {"args": [[[1, 4], [2, 5], [3, 6]]], "expect": 3},
         {"args": [[[7, 9], [1, 3], [2, 8]]], "expect": 2},
         {"args": [[[1, 2], [1, 2]]], "expect": 2},
         {"args": [[[5, 6]]], "expect": 1}],
         "random_tests": {"seed": 3, "count": 25, "reference": "min_rooms"}},
     "expected_properties": ["sweep or heap over sorted endpoints", "end before start at equal times"],
     "failure_conditions": ["any test fails"]},
    {"task_id": "BA-004", "category": "constraint_satisfaction", "difficulty": "medium",
     "prompt": "Schedule five jobs. Each job runs without interruption from its integer start time for its duration.\n"
               "Jobs (duration, resource demand): A (2, 2), B (3, 1), C (2, 2), D (1, 1), E (2, 1).\n"
               "Constraints: (1) A must finish before C starts; (2) B must finish before E starts; (3) B and D must not "
               "run at the same time; (4) at every time, the total demand of running jobs must not exceed 3; (5) every "
               "job must finish by time 6; (6) start times are integers >= 0.\n"
               "Give the final schedule as a JSON object mapping each job letter to its start time, in a ```json code block.",
     "constraints": ["precedence A->C, B->E", "B and D disjoint", "capacity 3", "horizon 6"],
     "evaluation": {"type": "deterministic_validator", "evaluator": "schedule",
                    "jobs": {"A": [2, 2], "B": [3, 1], "C": [2, 2], "D": [1, 1], "E": [2, 1]},
                    "precedence": [["A", "C"], ["B", "E"]], "disjoint": [["B", "D"]], "capacity": 3, "horizon": 6},
     "expected_properties": ["all six constraints hold"],
     "failure_conditions": ["any constraint violated", "missing or extra job"]},
    {"task_id": "BA-005", "category": "hidden_assumption", "difficulty": "medium",
     "prompt": "Three services logged these events:\n  E1 (payments): 2026-03-08T01:50:00-05:00\n"
               "  E2 (auth): 2026-03-08T07:20:00+01:00\n  E3 (billing): 2026-03-08T06:45:00Z\n"
               "Which event happened first, which happened last, and how many minutes elapsed between the first and the last? "
               "Give the final answer as a JSON object with keys \"first\", \"last\" (event IDs) and \"elapsed_minutes\" "
               "(integer), in a ```json code block.",
     "constraints": ["event IDs", "integer minutes"],
     "evaluation": {"type": "known_answer", "evaluator": "json_fields",
                    "expected": {"first": "E2", "last": "E1", "elapsed_minutes": 30}},
     "expected_properties": ["timestamps normalized to one time zone before comparison"],
     "failure_conditions": ["comparing local clock times (E1 first, E2 last, 330 minutes)"],
     "purpose": "The obvious comparison assumes one time zone."},
    {"task_id": "BA-006", "category": "software_architecture", "difficulty": "hard",
     "prompt": "You are designing a consumer for payment-status webhooks. Facts: the provider delivers each event at least "
               "once, possibly out of order, and retries for 72 hours until it receives a 2xx response. Each event has a "
               "unique event_id, a payment_id, a status, and a per-payment sequence number that increases with every status "
               "change. When a payment's status becomes 'succeeded', the consumer must credit the customer exactly once.\n"
               "Choose one option for each decision:\n"
               "  dedup_key: event_id | payment_id | received_timestamp | none\n"
               "  ack_timing: on_receipt_before_processing | after_durable_commit | after_attempt_even_if_failed\n"
               "  stale_event: apply_anyway | ignore_if_sequence_not_newer | reject_with_error_until_provider_gives_up\n"
               "  atomicity: dedup_record_and_effect_in_one_transaction | dedup_record_first_then_effect | "
               "effect_first_then_dedup_record\n"
               "Give the final answer as a JSON object with those four keys plus \"failure_modes\" (a list of the failure "
               "modes your design handles), in a ```json code block.",
     "constraints": ["choose listed options only"],
     "evaluation": {"type": "structured_rubric", "evaluator": "choices",
                    "expected": {"dedup_key": "event_id", "ack_timing": "after_durable_commit",
                                 "stale_event": "ignore_if_sequence_not_newer",
                                 "atomicity": "dedup_record_and_effect_in_one_transaction"},
                    "list_field": "failure_modes", "min_list": 2},
     "expected_properties": ["idempotent on event_id", "ack after durable commit", "stale events ignored", "atomic"],
     "failure_conditions": ["any decision wrong"]},
    {"task_id": "BA-007", "category": "failure_recovery", "difficulty": "hard",
     "prompt": "A job queue uses leases. Worker W1 acquires the lease on job J (TTL 10 s) at t=0 and starts computing. "
               "At t=4 W1 pauses for 15 s (a garbage-collection stop). The lease expires at t=10. W2 acquires the lease at "
               "t=11, finishes J and writes its result to storage at t=14. At t=19 W1 resumes and writes its result for J. "
               "Storage currently accepts every write.\nChoose one option for each question:\n"
               "  corrupting_write: W1_at_19 | W2_at_14 | none\n"
               "  prevention: longer_ttl | fencing_token_checked_by_storage | w1_checks_lease_before_writing | "
               "retry_with_backoff\n"
               "  w1_after_rejection: retry_write | abandon_and_discard_result | reacquire_lease_and_overwrite\n"
               "  w2_retry_on_timeout: safe_if_idempotent_with_same_token | never_safe | always_safe\n"
               "Give the final answer as a JSON object with those four keys plus \"explanation\" (string), in a ```json code block.",
     "constraints": ["choose listed options only"],
     "evaluation": {"type": "structured_rubric", "evaluator": "choices",
                    "expected": {"corrupting_write": "W1_at_19", "prevention": "fencing_token_checked_by_storage",
                                 "w1_after_rejection": "abandon_and_discard_result",
                                 "w2_retry_on_timeout": "safe_if_idempotent_with_same_token"}},
     "expected_properties": ["stale holder identified", "fencing enforced by storage (a client-side check races)"],
     "failure_conditions": ["any decision wrong"]},
    {"task_id": "BA-008", "category": "misleading_premise", "difficulty": "medium",
     "prompt": "Because Python's built-in sorted() is not stable, write `def sort_by_age(people)` that sorts a list of "
               "(name, age) tuples by age ascending while keeping people with equal ages in their original relative order. "
               "Give the function in a ```python code block and briefly explain your approach.",
     "constraints": ["function name sort_by_age", "stable by age"],
     "evaluation": {"type": "executable_test+premise", "evaluator": "premise_code", "function": "sort_by_age", "tests": [
         {"args": [[["b", 3], ["a", 1], ["c", 3], ["d", 2]]], "expect": [["a", 1], ["d", 2], ["b", 3], ["c", 3]]},
         {"args": [[]], "expect": []},
         {"args": [[["x", 5], ["y", 5], ["z", 5]]], "expect": [["x", 5], ["y", 5], ["z", 5]]}],
         "correction_patterns": [
             "(sorted|sort\\(\\)|list\\.sort|timsort|python'?s (built-in )?sort\\w*)[^.\\n]{0,80}\\b(is|are)\\s+(actually\\s+|in fact\\s+|already\\s+|guaranteed\\s+(to\\s+be\\s+)?|always\\s+)*stable",
             "premise[^.\\n]{0,60}\\b(incorrect|false|wrong|mistaken|not (true|accurate|correct))",
             "\\b(is|are) (actually|in fact) stable", "\\bstable sort(ing)? (algorithm )?\\(?timsort",
             "contrary to[^.\\n]{0,60}stable", "\\bsorted\\(\\)[^.\\n]{0,40}guarantee[sd]? stability"],
         "acceptance_patterns": ["(since|because|as)\\s+(python'?s\\s+)?(built-in\\s+)?(sorted\\(\\)|sorted|sort)[^.\\n]{0,40}\\b(is\\s+not|isn'?t|not)\\s+stable",
                                 "sorted\\(\\)\\s+(is\\s+not|isn'?t)\\s+stable"]},
     "expected_properties": ["correct stable result", "the false premise is corrected (sorted() is stable)"],
     "failure_conditions": ["premise repeated as fact without correction", "incorrect ordering"]},
    {"task_id": "BA-009", "category": "missing_evidence", "difficulty": "hard",
     "prompt": "Incident: checkout API p99 latency rose from 180 ms to 900 ms on 2026-05-12 between 14:05 and 14:40 UTC.\n"
               "Available evidence:\n  [E1] Deploy log: checkout-service v4.2.1 deployed at 13:58 UTC (changelog: "
               "\"dependency bumps\").\n  [E2] Chat: two on-call engineers both wrote that \"it's definitely the database\".\n"
               "No database metrics, traces or query logs are available.\nQuestion: what was the root cause of the latency "
               "increase?\n" + JSON_EVIDENCE_FORMAT,
     "constraints": ["cite only provided evidence IDs"],
     "evaluation": {"type": "deterministic_validator", "evaluator": "evidence", "provided_ids": ["E1", "E2"],
                    "mode": "missing", "consensus_patterns": ["database"]},
     "expected_properties": ["certainty below established", "names missing evidence", "agreement is not evidence"],
     "failure_conditions": ["root cause stated as established", "fabricated evidence IDs"]},
    {"task_id": "BA-010", "category": "contradictory_evidence", "difficulty": "hard",
     "prompt": "Question: does parse_config() in release 3.1.0 correctly handle an empty configuration file?\n"
               "Evidence (both refer to the same commit a1b2c3d):\n  [E1] QA test report for 3.1.0: "
               "\"test_empty_config ... PASSED\".\n  [E2] CI log for 3.1.0, build #812: \"test_empty_config ... FAILED: "
               "KeyError: 'version'\".\n" + JSON_EVIDENCE_FORMAT,
     "constraints": ["cite only provided evidence IDs"],
     "evaluation": {"type": "deterministic_validator", "evaluator": "evidence", "provided_ids": ["E1", "E2"],
                    "mode": "contradiction"},
     "expected_properties": ["both artifacts considered", "conflict left unresolved without further evidence"],
     "failure_conditions": ["one artifact ignored", "conflict resolved as established"]},
    {"task_id": "BA-011", "category": "narrow_check_broad_claim", "difficulty": "hard",
     "prompt": "Evidence:\n  [E1] Load-test report: one region (us-east-1), 100 requests/s sustained for 10 minutes, "
               "synthetic read-only traffic, p99 = 120 ms, 0 errors.\nQuestion: can we promise enterprise customers in the "
               "contract that the service will handle production peak traffic (5,000 requests/s, mixed reads and writes, "
               "3 regions) with p99 under 200 ms?\n" + JSON_EVIDENCE_FORMAT,
     "constraints": ["cite only provided evidence IDs"],
     "evaluation": {"type": "deterministic_validator", "evaluator": "evidence", "provided_ids": ["E1"], "mode": "scope"},
     "expected_properties": ["no guarantee derived from the narrow test", "gap to production conditions named"],
     "failure_conditions": ["promise/guarantee supported as established"]},
    {"task_id": "BA-012", "category": "overthinking_trap", "difficulty": "easy",
     "prompt": "Write `def is_palindrome(s)` that returns True exactly when the string s is equal to its own reverse. The "
               "comparison is exact: letter case, spaces and punctuation all count. Give the function in a ```python code block.",
     "constraints": ["exact comparison, no normalization"],
     "evaluation": {"type": "executable_test", "evaluator": "python_tests", "function": "is_palindrome", "tests": [
         {"args": ["aba"], "expect": True}, {"args": ["Aba"], "expect": False}, {"args": ["a b a"], "expect": True},
         {"args": ["ab a"], "expect": False}, {"args": [""], "expect": True}, {"args": ["racecar"], "expect": True},
         {"args": ["Racecar"], "expect": False}, {"args": ["A man, a plan, a canal: Panama"], "expect": False},
         {"args": ["!!"], "expect": True}]},
     "expected_properties": ["s == s[::-1]"],
     "failure_conditions": ["normalizing case/spaces/punctuation"],
     "purpose": "A simple strong first answer; extra 'robustness' reasoning can make it wrong."},
]


def write(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for task in TASKS:
        (directory / f"{task['task_id']}.json").write_text(json.dumps(task, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write(Path(__file__).resolve().parent.parent / "tasks")
