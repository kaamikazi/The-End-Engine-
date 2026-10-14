"""Model-protocol failures (v0.3.5): a model's structured output that is malformed or references identifiers that do
not exist. This is not an external failure. EXTERNAL_BLOCKER stays reserved for conditions outside the model's output:
an unavailable provider or tool, transport or environment failures, exhausted external budgets.

Recovery is bounded: a failing stage gets at most `repair_attempts` targeted repair calls that state the validation
error and list the identifiers that are actually valid. Invalid identifiers are never mapped onto real ones, missing
semantic content is never manufactured, and every attempt is recorded in the trajectory (`protocol_events`)."""

SCHEMA_FAILURE = "MODEL_PROTOCOL_SCHEMA_FAILURE"          # unparseable JSON or schema violation
INVALID_REFERENCE = "MODEL_PROTOCOL_INVALID_REFERENCE"    # unknown or duplicate weakness/claim/branch identifier
INVALID_TRANSITION = "MODEL_PROTOCOL_INVALID_TRANSITION"  # a forbidden state transition (e.g. adopting a rejected branch)
UNGROUNDED_FINDING = "MODEL_PROTOCOL_UNGROUNDED_FINDING"  # a judge finding that does not resolve to the candidate
REPAIR_EXHAUSTED = "MODEL_PROTOCOL_REPAIR_EXHAUSTED"      # bounded repair did not yield usable output
CATEGORIES = (SCHEMA_FAILURE, INVALID_REFERENCE, INVALID_TRANSITION, UNGROUNDED_FINDING, REPAIR_EXHAUSTED)
EXTERNAL = "EXTERNAL_FAILURE"

REPAIR_INSTRUCTION = ("PROTOCOL REPAIR: your previous output for this request was rejected by validation. "
                      "Return a corrected output for the same request. Use only identifiers listed under "
                      "protocol_repair.allowed_identifiers; use null for a new weakness and an empty list where nothing "
                      "applies. Do not invent identifiers.")


class ModelProtocolError(ValueError):
    """Raised when model output violates the Engine protocol. A ValueError subclass for compatibility.
    Providers may raise it themselves to signal a model-output (not transport) failure."""

    def __init__(self, category, message, *, stage=None, invalid=(), allowed=None, output=None):
        super().__init__(message)
        self.category, self.stage = category, stage
        self.invalid = tuple(invalid)
        self.allowed = allowed           # {kind: [valid ids]} the model may use
        self.output = output             # the rejected (parsed) output, when available, for salvage


def repair_context(error, previous_output=None, attempt=1):
    return {"attempt": attempt, "category": error.category, "validation_error": str(error),
            "invalid_values": list(error.invalid), "allowed_identifiers": error.allowed or {},
            "previous_output": previous_output if previous_output is not None else error.output}


def termination_category(exc):
    return exc.category if isinstance(exc, ModelProtocolError) else EXTERNAL
