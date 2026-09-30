"""Bind the one-feature rollout experiment to exact submitted cb76 bytes."""
import ast
import json
from pathlib import Path
from datetime import datetime, timezone
from run_panel import sha, HERE

base = HERE / 'baseline_cb76fbc4.py'
assert sha(base) == 'cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74'
suffix = HERE / 'rollout_suffix.py'
candidate = HERE / 'candidate_rollout_v1.py'
assert not candidate.exists()
source = base.read_text(encoding='utf-8') + '\n\n' + suffix.read_text(encoding='utf-8')
ast.parse(source)
candidate.write_text(source, encoding='utf-8', newline='\n')
manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
                candidate=str(candidate), candidate_sha256=sha(candidate),
                baseline=str(base), baseline_sha256=sha(base), suffix_sha256=sha(suffix),
                plan_sha256=sha(HERE / 'ROLLOUT_PLAN.md'),
                expected_entrypoint='kaggle_fresh90_rollout_entrypoint')
(HERE / 'rollout_v1_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
