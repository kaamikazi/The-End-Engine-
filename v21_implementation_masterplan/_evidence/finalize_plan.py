"""Planning-document normalization only; no implementation source touched."""
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent
p=H/'build_tables.py';s=p.read_text(encoding='utf-8');s=s.replace('experimental_architectures_v1_r3/tests/cr2_v21/','experimental_architectures_v1_r3/cr2_v21_tests/');p.write_text(s,encoding='utf-8',newline='\n')
for p in P.glob('*.md'):
 s=p.read_text(encoding='utf-8')
 s=s.replace('Tests belong in a new future tests/cr2_v21/ namespace','Tests belong in a new future cr2_v21_tests/ namespace outside existing tests/ discovery')
 s=s.replace('Correct previous planning-path references to this location before implementation; historical discovery must not silently include new tests and then mislabel the total as the old244.','Historical discovery must not silently include new tests and then mislabel the total as the old244.')
 s=s.replace('48 planned vectors with all20 scenarios/positives and8 cleanup','45 planned vectors:20 primary scenarios (including3 positives),17 distinct fault-free controls and8 cleanup')
 s=s.replace('48 vectors:20 primary snapshot scenarios +20 positive counterparts +8 cleanup boundaries','45 vectors:20 primary scenarios (17 fault and3 positive) +17 distinct positive counterparts +8 cleanup boundaries')
 s=s.replace('20 required snapshot scenarios with a named positive counterpart each plus8 failure cleanup controls','20 required snapshot scenarios (including3 positive histories),17 distinct fault-free counterpart controls and8 failure cleanup controls')
 s=s.replace('20 required scenarios with a named positive counterpart each','20 required scenarios and17 distinct positive counterparts')
 p.write_text(s,encoding='utf-8',newline='\n')
print('Planning paths and nonduplicated B budget finalized; source files untouched.')
