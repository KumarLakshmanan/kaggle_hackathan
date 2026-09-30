"""Correct forecast planting semantics and freeze the V2 selection rule."""
import ast
from datetime import datetime, timezone
import json
from run_panel import sha, HERE

base = HERE / 'baseline_cb76fbc4.py'
assert sha(base) == 'cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74'
suffix_path = HERE / 'rollout_suffix.py'
assert sha(suffix_path) == 'a97990704fc0937e73eaa00c2de41e37d6a382f8c20c7319fb9a2114b53bc11d'
suffix = suffix_path.read_text(encoding='utf-8')
helper = '''
def _f90_plant_forecast(obs, action, cfg):
    saved = dict(_PARTIAL_STATS)
    try:
        return _partial_plant(obs, action, cfg)
    finally:
        _PARTIAL_STATS.clear()
        _PARTIAL_STATS.update(saved)


'''
suffix = suffix.replace('def _f90_forecast(', helper + 'def _f90_forecast(', 1)
needle = "        _PLANT_CORE['interpreter'](states, env)"
assert suffix.count(needle) == 1
suffix = suffix.replace(needle, "        for item in states:\n            item.action = _f90_plant_forecast(item.observation, item.action, visible_cfg)\n" + needle)
suffix = suffix.replace('best_key, selected = (1500.0, 3000.0), None', 'best_key, selected = (1000.0, 0.0), None')
suffix = suffix.replace('if worst > 1500 and mean > 3000 and min(own_gains) >= 0 and (worst, mean) > best_key:',
                        'if worst >= 0 and mean > 1000 and min(own_gains) >= 0 and (mean, worst) > best_key:')
suffix = suffix.replace('best_key, selected = (worst, mean), route', 'best_key, selected = (mean, worst), route')
suffix = suffix.replace('kaggle_fresh90_rollout_entrypoint', 'kaggle_fresh90_rollout_v2_entrypoint')
target = HERE / 'candidate_rollout_v2.py'
assert not target.exists()
source = base.read_text(encoding='utf-8') + '\n\n' + suffix
ast.parse(source)
target.write_text(source, encoding='utf-8', newline='\n')
manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), candidate=str(target),
                candidate_sha256=sha(target), baseline=str(base), baseline_sha256=sha(base),
                plan_sha256=sha(HERE / 'ROLLOUT_V2_PLAN.md'),
                expected_entrypoint='kaggle_fresh90_rollout_v2_entrypoint',
                forecast_partial_planting=True, scenario_selection='minimum paired margin >=0, mean >1000, own >=0')
(HERE / 'rollout_v2_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
