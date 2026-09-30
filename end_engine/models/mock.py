"""Deterministic fixtures exercise orchestration; they are not model evaluations."""
from copy import deepcopy

from .base import ModelProvider, ModelResponse


MEMORY_CANDIDATES = (
    "Store agent observations and summaries in a persistent memory store. Retrieve records by relevance "
    "and recency. Periodically summarize older records and delete low-value raw observations. "
    "Keep important facts and a small working context for the current task.",
    "Use a durable memory store with separate working context, episodic records, and versioned semantic facts. "
    "Enforce a 256 MiB total persistent-memory quota, including indexes, summaries, and metadata, plus a "
    "16 KiB working-context cap. Admit writes transactionally only after reserving capacity; reject or evict "
    "when capacity is unavailable. Rank eviction by usefulness, recency, and retrieval frequency. "
    "Keep provenance links and confidence with each fact; summarize only when the new record costs less "
    "than its inputs. Compact periodically and measure size and retrieval usefulness.",
    "Use a durable memory store with working context, episodic records, and versioned semantic facts. "
    "Enforce a 256 MiB total storage quota covering records, indexes, summaries, metadata, logs, and temporary "
    "compaction files; cap working context at 16 KiB. Reserve 20% of storage for transactional compaction "
    "and recovery. Atomically reserve bytes before each write; evict low-value records or reject writes if "
    "the reservation fails. Compaction must operate within reserved headroom and recover from a committed "
    "manifest after crashes. Enforce a bounded log and bounded backup retention. Summaries retain provenance "
    "and consume the same quota. Cap pinned records at 10% of storage; when full, require explicit replacement "
    "or reject additional pins. Conflicting facts coexist with source, time, and confidence until evidence "
    "supports resolution. Under overload, return a visible admission failure rather than silently losing "
    "critical facts. Measure bytes, eviction rate, rejection rate, and retrieval utility. Verify with sustained "
    "ingestion, all-pinned saturation, concurrent write admission, and crash-during-compaction tests; assert "
    "that total storage never exceeds quota and committed records remain recoverable. These are proposed "
    "checks, not executed results. The tradeoff is explicitly bounded retention, not perfect lifetime recall.",
)


class MockProvider(ModelProvider):
    def __init__(self, *, scripted=None):
        self.scripted = {key: list(values) for key, values in (scripted or {}).items()}

    def metadata(self):
        return {"provider": "mock", "model": "deterministic-fixture-v1", "offline": True}

    def generate(self, request):
        return ModelResponse("Offline mock text response")

    def generate_structured(self, request):
        if request.purpose in self.scripted:
            if not self.scripted[request.purpose]:
                raise RuntimeError(f"Script exhausted for {request.purpose}")
            value = self.scripted[request.purpose].pop(0)
            if isinstance(value, Exception):
                raise value
            return value if isinstance(value, ModelResponse) else ModelResponse(deepcopy(value))
        context = request.context
        purpose = request.purpose
        if purpose == "classification":
            heuristic = context["heuristic"]
            result = {key: heuristic[key] for key in ("complexity", "confidence", "dimensions", "rationale")}
        elif purpose == "selection":
            used = context["state"]["operators_used"]
            if used and isinstance(used[0], list):
                used = [entry[0] for entry in used]
            names = [op["name"] for op in context["operators"]]
            name = next((name for name in ("ASSUMPTION", "WHAT_BREAKS", "VERIFY") if name in names and name not in used), names[0])
            result = {"operator": name, "reason": "Mock policy selects the next unused fixture operator", "priority": 0.8}
        elif purpose in ("initial_candidate", "revision"):
            iteration = context.get("iteration", 0)
            task = context["task"]
            if "memory" in task.lower():
                content = MEMORY_CANDIDATES[min(iteration, 2)]
            elif task.lower().startswith("uppercase "):
                content = task[len("uppercase "):].upper()
            else:
                content = f"Mock candidate {iteration} for: {task}. " + (
                    "Propose an initial solution." if iteration == 0 else
                    "Apply explicit limits, failure handling, and observable verification criteria.")
            result = {"content": content, "known_strengths": ["Explicit proposal"], "confidence": None}
        elif purpose == "critique":
            iteration = context["candidate"]["iteration"]
            if iteration == 0:
                finding = {"weakness_id": None, "type": "constraint", "severity": "high",
                           "description": "Summarization does not guarantee a hard storage bound.",
                           "evidence": "The initial proposal has no byte quota or admission control."}
            elif iteration == 1:
                finding = {"weakness_id": None, "type": "failure_mode", "severity": "high",
                           "description": "Compaction and pinned records can exhaust the storage budget.",
                           "evidence": "No compaction headroom, pin quota, or crash-recovery protocol is specified."}
            else:
                finding = None
            result = {"summary": "Inspect the proposal's unproven bounded-storage guarantee." if finding else
                      "No additional weakness in this deterministic fixture.", "findings": [finding] if finding else []}
        elif purpose == "revision_plan":
            result = {"changes": [{"targets": [w["id"]],
                       "action": ("Add a total byte quota and transactional admission control." if w["id"] == "W001" else
                                  "Reserve compaction headroom, cap pins, and specify crash recovery and saturation checks."),
                       "expected_effect": "Make storage limits explicit and testable under the identified failure conditions."}
                      for w in context["weaknesses"] if w["status"] == "open"]}
        elif purpose == "verification":
            iteration = context["candidate"]["iteration"]
            score = (0.56, 0.76, 0.94)[min(iteration, 2)]
            updates = []
            for weakness in context["weaknesses"]:
                if weakness["status"] == "open" and iteration >= (1 if weakness["id"] == "W001" else 2):
                    updates.append({"id": weakness["id"], "status": "resolved",
                                    "reason": "Candidate now specifies the missing quota mechanism and applicable checks (fixture judgment)."})
            result = {"passed": iteration >= 2, "score": score,
                      "dimensions": {name: score for name in context["dimensions"]},
                      "remaining_issues": [] if iteration >= 2 else ["Additional failure-mode scrutiny is needed."],
                      "weakness_updates": updates}
        elif purpose == "branch_generation":
            result = {"branches": [{"hypothesis": name,
                       "content": f"Mock competing approach for {context['task']}: {name}."}
                       for name in ("Incremental refinement", "Isolated components", "Staged validation")[:context["max_branches"]]]}
        elif purpose == "branch_evaluation":
            result = {"scores": {d: 0.8 for d in context["dimensions"]},
                      "strengths": ["A distinct fixture alternative"], "weaknesses": ["Requires real task-specific evaluation"],
                      "recommendation": "MERGE_COMPONENTS"}
        elif purpose == "synthesis":
            result = {"source_branches": [b["branch_id"] for b in context["branches"]],
                      "adopt": [{"branch": b["branch_id"], "element": b["content"]}
                                for b in context["branches"] if b["status"] == "PROMISING"],
                      "reject": [{"branch": b["branch_id"], "element": b["hypothesis"], "reason": "Non-promising fixture branch"}
                                 for b in context["branches"] if b["status"] != "PROMISING"]}
        else:
            raise ValueError(f"Unknown mock purpose: {purpose}")
        return ModelResponse(result)
