import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

if __name__=='__main__':
    parent=ROOT/'main_candidate_dsm_frontloaded_bank_20260927_dd420938.py'
    raw=parent.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='dd4209389689bc8ecd33ac19124b754054cfc9439abc4f27bae3faf682abceff'
    tail=(HERE/'tail.py.txt').read_bytes()
    data=raw+tail
    ast.parse(data)
    digest=hashlib.sha256(data).hexdigest()
    candidate=ROOT/'exp_dsm_weed_window_20260927.py'
    backup=ROOT/f'main_candidate_dsm_weed_window_20260927_{digest[:8]}.py'
    assert not candidate.exists() and not backup.exists()
    candidate.write_bytes(data);backup.write_bytes(data)
    out=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),candidate=str(candidate),candidate_sha256=digest,
             backup=str(backup),parent_sha256=hashlib.sha256(raw).hexdigest(),tail_sha256=hashlib.sha256(tail).hexdigest(),
             plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest())
    (HERE/'build_manifest.json').write_text(json.dumps(out,indent=2),encoding='utf8')
    print(json.dumps(out,indent=2))
