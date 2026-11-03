"""Repair only newly authored plan text; never touch scientific/source inputs."""
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent
changes=[]
for p in list(P.glob('*.md'))+list(H.glob('*.py')):
 s=p.read_text(encoding='utf-8');original=s
 for _ in range(3):
  for char in '–—→≤≥×…‘’“”':
   try:bad=char.encode('utf-8').decode('cp1252')
   except UnicodeError:continue
   s=s.replace(bad,char)
 if p.suffix=='.py':s=s.replace('.read_text(encoding='utf-8')',".read_text(encoding='utf-8')")
 if s!=original:p.write_text(s,encoding='utf-8',newline='\n');changes.append(p.name)
print(changes)
