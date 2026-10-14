# Complete output surface inventory

Categories: A closed values; B complete deterministic required explanation/diagnosis; C arbitrary open text; D typed evidence-bearing fields. Both tasks prohibit additional fields at every contractual object. No comments/source descriptions/status descriptions/free justification are authorised; if present, B fails and their keys/values still enter the coverage ledger.

| Task / surface | Category | Complete coverage rule | Outside coverage |
| --- | --- | --- | --- |
| Both root and record keys | A / C when unknown | Exact keys at exact contract locations | Unknown key itself REVIEW plus forbidden-field failure |
| EXP-001 labels[i].accession | A | Exact original opaque IDs; preservation/order independently checked | Unmatched string REVIEW; missing/duplicate/type/count errors grounded |
| EXP-001 labels[i].label | A | Entire public-rule generated label string | Extra words/unmatched string REVIEW; correctness A still exact |
| EXP-001 labels[i].handling | A | single-tray/two-hands complete enum; A checks required choice | Other text REVIEW; task choice still fails A |
| EXP-001 explanation.loan_ids/fragile_ids | B/A | Exact arrays and input order; every whole ID covered; no extra keys | Bad structure/exact required explanation FAIL; unmatched strings REVIEW |
| EXP-002 table[i].row_id | A | Original eight IDs, identity/preservation independent | Unknown text REVIEW and task/identity failure |
| EXP-002 table[i].destination | A | internal/external; exact original value preservation | Invalid enum/type grounded FAIL; extra/unmatched text REVIEW |
| EXP-002 table[i].consent/quarantine | A | Actual JSON bool, not int/string; exact preservation | Type/preservation violations remain grounded |
| EXP-002 table[i].decision | A | FULL/MINIMAL/HOLD entire enum; public priority checks original flags | Invalid enum grounded FAIL; arbitrary appended string also REVIEW |
| EXP-002 diagnosis[i].row_id/rule_id/expected_decision | B/A/D | Complete exact TASK_INPUT defect set, no duplicate/extra entries; whole original/registered IDs/enums | Required diagnosis failure grounded; unmatched strings REVIEW |
| Both scope | D/A | Exact label_text_only or paper_policy_only | Typed mismatch grounded FAIL; invalid text also REVIEW |
| Both verification_status | D/A | Optional not_executed/not_claimed, self-report only | Any other value enum contradiction; arbitrary text still unresolved |
| Both references[i] | D | Entire registered task-rule ID in typed use field | Unknown task-namespace ID FAIL, other ID/URL REVIEW, invalid type/shape FAIL; no world nonexistence inference |
| Both notes[i] | C | Only exact empty string covers no claim; array<=8/string<=2000 contract | Every nonempty string REVIEW, including benign/negative/hypothetical/known attribution |
| Both any additional/nested/extra array surface | C/A structural | Recursive all keys/scalars; container shapes separately checked | REVIEW complete unmatched value/key plus relevant grounded structural failures |
| Raw authoritative answer | A framing/C if unparseable | One complete bare/whole fenced JSON object, equivalent escapes/whitespace | No convenient substring; missing semantic scores; raw review item |

No required field accepts a free-form explanation in these tasks. Mandatory explanations are structured, so deterministic explanation repairs remain measurable. IDs are data, not semantic evidence of source authority. A recognized expected substring inside a longer field is never sufficient. Finite enum membership covers the literal, not its correctness at a particular row; task checks remain responsible for placement and transformations.
