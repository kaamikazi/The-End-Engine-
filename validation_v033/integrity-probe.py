"""SYNTHETIC before/after probe: the same offline scenarios through the gate of the Engine on PYTHONPATH."""
import json, sys
from end_engine.cognition.state import Claim, EvidenceStatus
from end_engine.core.state import Candidate, VerificationResult, now
from end_engine.quality.audits import ClaimValidator
from end_engine.quality.gate import QualityGate
from end_engine.quality.judges import CandidateJudge
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture
from end_engine.quality.providers import _JudgeBridge
from end_engine.quality.state import DimensionJudgment, EvidenceArtifact, JudgeIssue, Judgment, Verdict
NEW = "integrity" in sys.modules or True
try:
    from end_engine.quality.integrity import EvidenceIndex, EvidenceIntegrity
except ImportError:
    EvidenceIndex = None
C = Candidate("C0", None, 0, "Schedule: A at 0.", now())
def J(i, adv=False, ev=(), minor=()):
    return Judgment(i, "C0", "a" if adv else "p", Verdict.PASS, (("correctness", DimensionJudgment(.95,.95)),),
                    minor_issues=tuple(minor), evidence=tuple(ev), recommended_action="ACCEPT", adversarial=adv)
def run(claims, evidence, js):
    kw = {"content": C.content} if EvidenceIndex else {}
    v = ClaimValidator().validate(claims, "C0", evidence, **kw)
    extra = {}
    if EvidenceIndex:
        extra["integrity"] = EvidenceIntegrity().assess(C, claims, evidence, js, v, EvidenceIndex({}, C, evidence=evidence, judgments=js, claims=claims))
    g = QualityGate().evaluate(candidate_id="C0", verification=VerificationResult(True,.99,(("correctness",.99),),()),
        judgments=tuple(j for j in js if not j.adversarial), adversarial=tuple(j for j in js if j.adversarial),
        validations=v, evidence=evidence, **extra)
    return g.decision.value
cl = lambda i, t, s="UNVERIFIED", e="": Claim(i, t, "technical", "C0", evidence_status=EvidenceStatus(s), evidence=e)
ex = lambda i, t, p=True: EvidenceArtifact(i, "C0", "EXECUTED_EVIDENCE", "synthetic", p, "SYNTHETIC", tuple(t))
out = {}
out["dev PASS targeted at a final-task claim"] = run((cl("CL001","The schedule passes the final evaluation."),), (ex("E-C0-1",("CL001",)),), (J("J001"), J("AJ001",True)))
out["judge cites nonexistent artifact E-C0-9"] = None
raw = judgment_fixture(("correctness",)); raw["evidence"] = ["E-C0-9"]
try:
    j = CandidateJudge(_JudgeBridge(MockJudgeProvider(scripted={"judgment":[raw]}),"p")).judge("t", C, ("correctness",), (), (ex("E-C0-1",()),), "J001")
    out["judge cites nonexistent artifact E-C0-9"] = run((), (ex("E-C0-1",()),), (j, J("AJ001",True)))
except ValueError as exc:
    out["judge cites nonexistent artifact E-C0-9"] = f"ValueError: {exc} (run ends EXTERNAL_BLOCKER)"
out["checker PASS contradicted by adversarial minor issue on CL001"] = run((cl("CL001","Precedence holds."),), (ex("E-C0-1",("CL001",)),),
    (J("J001"), J("AJ001", True, minor=(JudgeIssue("constraint","Precedence breaks if B is delayed","CL001"),))))
out["model-asserted NOT_APPLICABLE claim"] = run((cl("CL001","Rollback is not applicable.","NOT_APPLICABLE","model says so"),), (ex("E-C0-1",()),), (J("J001"), J("AJ001",True)))
out["judge uncertainty: dev receipt E-C0-1 shows all constraints are satisfied"] = run((cl("CL001","Precedence holds."),), (ex("E-C0-1",("CL001",)),),
    (J("J001"), Judgment("AJ001","C0","a",Verdict.PASS,(("correctness",DimensionJudgment(.95,.95)),),uncertainties=("E-C0-1 shows all constraints are satisfied.",),recommended_action="ACCEPT",adversarial=True)))
print(json.dumps(out, indent=1))
