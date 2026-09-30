import hashlib
from pathlib import Path
base = Path('diagnostics/fresh90_leading_openings_20260930')
files = [
    ('PLAN.md', base/'PLAN.md'),
    ('source_summary', Path('diagnostics/fresh90_refresh_20260929/routes/development_latest/summary.json')),
    ('candidate_top_rank_1.py', base/'candidate_top_rank_1.py'),
    ('candidate_top_rank_2.py', base/'candidate_top_rank_2.py'),
    ('candidate_top_rank_3.py', base/'candidate_top_rank_3.py'),
    ('static_day0_comparison.json', base/'static_day0_comparison.json'),
    ('candidate_manifest.json', base/'candidate_manifest.json'),
    ('README.md', base/'README.md'),
]
lines = [f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {label}' for label,path in files]
(base/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
