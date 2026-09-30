import hashlib
from pathlib import Path
base = Path('diagnostics/fresh90_current_opening_20260929')
source = Path('diagnostics/fresh90_refresh_20260929/routes/development_latest/summary.json')
paths = [
    source,
    base / 'PLAN.md',
    base / 'family_analysis.json',
    base / 'candidate_01_family01_rank65.py',
    base / 'candidate_02_family02_rank16.py',
    base / 'candidate_03_family03_rank30.py',
    base / 'candidate_validation.json',
    base / 'melon_support.json',
    base / 'candidate_manifest.json',
    base / 'README.md',
]
lines = ['SHA-256 values for the frozen source, plan, validation, manifest, and candidate files.']
for path in paths:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f'{digest}  {path.as_posix()}')
(base / 'CANDIDATE_SHA256.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('\n'.join(lines))
