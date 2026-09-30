import ast
from datetime import datetime, timezone
import json
from run_panel import HERE, sha

base = HERE / 'baseline_cb76fbc4.py'
suffix = HERE / 'land_queue_suffix.py'
assert sha(base) == 'cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74'
dest = HERE / 'candidate_funded_land_v1.py'
assert not dest.exists()
source = base.read_text(encoding='utf-8') + '\n' + suffix.read_text(encoding='utf-8')
ast.parse(source)
dest.write_text(source, encoding='utf-8', newline='\n')
freeze = dict(at_utc=datetime.now(timezone.utc).isoformat(), candidate_sha256=sha(dest),
              base_sha256=sha(base), suffix_sha256=sha(suffix), plan_sha256=sha(HERE / 'LAND_QUEUE_PLAN.md'))
(HERE / 'land_queue_manifest.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
print(json.dumps(freeze, indent=2))
