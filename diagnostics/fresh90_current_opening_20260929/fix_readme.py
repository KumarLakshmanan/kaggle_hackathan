from pathlib import Path
p=Path('diagnostics/fresh90_current_opening_20260929/README.md')
s=p.read_text(encoding='utf-8')
s=s.replace('snapshot at **2026-09-29 17:04:25 UTC**. The source summary SHA-256 is', 'snapshot downloaded at **2026-09-29 17:04:23 UTC** (the collection receipt was written at 17:04:25 UTC). The source summary SHA-256 is')
s=s.replace('| `candidate_01_family01_rank65.py` | 65, 77 | action offset 144 | 65 |', '| `candidate_01_family01_rank65.py` | 65, 77 | checkpoint 144 (actions 0–143) | 65 |')
s=s.replace('| `candidate_02_family02_rank16.py` | 16, 83 | action offset 72 | 16 |', '| `candidate_02_family02_rank16.py` | 16, 83 | checkpoint 72 (actions 0–71) | 16 |')
s=s.replace('| `candidate_03_family03_rank30.py` | 30, 86 | action offset 72 | 30 |', '| `candidate_03_family03_rank30.py` | 30, 86 | checkpoint 72 (actions 0–71) | 30 |')
s=s.replace('The omitted fourth pair is ranks 56 and 79. It also shares through action\noffset 72;', 'The omitted fourth pair is ranks 56 and 79. It also shares through checkpoint\n72;')
p.write_text(s,encoding='utf-8')
