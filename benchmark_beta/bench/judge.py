"""Blinded external pairwise judge (infrastructure). Not used for Benchmark Alpha scoring: every Alpha task has an
objective evaluator, and the rules prefer objective checks. Kept for later subjective tasks.

The judge sees only the task prompt and anonymous answers labelled "ANSWER A"/"ANSWER B" in a seeded random order.
Condition names, iteration counts, END scores, gate results, candidate IDs and rollback status are never passed.
The label-to-source mapping is returned separately and must be stored outside anything the judge sees."""
import random

from end_engine.models.base import ModelRequest

SCHEMA = {"type": "object", "properties": {"preferred": {"type": "string", "enum": ["A", "B", "TIE"]},
                                           "reason": {"type": "string", "minLength": 1}},
          "required": ["preferred", "reason"], "additionalProperties": False}


def blinded_pairwise(provider, task_prompt, answers, seed):
    """answers: {source_key: text} with exactly two entries. Returns (verdict mapped to source keys, mapping, request)."""
    keys = sorted(answers)
    if len(keys) != 2:
        raise ValueError("exactly two answers are compared")
    random.Random(seed).shuffle(keys)
    mapping = {"A": keys[0], "B": keys[1]}
    request = ModelRequest("blinded_external_judgment",
                           "You are an external evaluator. Compare two anonymous answers to the task on correctness and "
                           "on unsupported claims. Prefer neither answer for its length or confidence.",
                           {"task": task_prompt, "ANSWER A": answers[mapping["A"]], "ANSWER B": answers[mapping["B"]]},
                           SCHEMA)
    data = provider.generate_structured(request).content
    preferred = mapping.get(data["preferred"])  # None for TIE
    return {"preferred_source": preferred, "reason": data["reason"]}, mapping, request
