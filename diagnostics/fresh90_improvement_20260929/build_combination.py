"""Build the single predeclared combination after component panels complete."""
import ast
from datetime import datetime, timezone
import json
from run_panel import HERE, sha

base = HERE / 'baseline_cb76fbc4.py'
assert sha(base) == 'cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74'
base_rows = [json.loads(s) for s in (HERE / 'cb76_top100_jobs_results.jsonl').read_text().splitlines()]
lookup = {(r['fixture_id'], r['candidate_seat']): r for r in base_rows}
receipt = json.loads((HERE / 'funded_land_top100_jobs_receipt.json').read_text())
assert receipt['complete'] and receipt['completed_games'] == 200
land = [json.loads(s) for s in (HERE / 'funded_land_top100_jobs_results.jsonl').read_text().splitlines()]
land_lookup = {(r['rank'], r['candidate_seat']): r for r in land}
land_gain = sum(r['result'] == 'win' for r in land) - sum(r['result'] == 'win' for r in base_rows)
land_lost = [r for r in land if lookup[r['fixture_id'], r['candidate_seat']]['result'] == 'win' and r['result'] != 'win']
use_land = receipt['assessment']['funded_land']['all']['all_clean'] and land_gain > 0 and not land_lost
survivors = json.loads((HERE / 'route_search/survivors.json').read_text()) + json.loads((HERE / 'broad_routes/survivors.json').read_text())
assert len({v['pair'] for v in survivors}) == len(survivors)
selected, omitted = [], []
for v in survivors:
    if use_land and all(land_lookup[r['rank'], r['seat']]['result'] == 'win' for r in v['gained_wins']):
        omitted.append(v)
    else:
        selected.append(v)
rules = {v['pair']: int(v['route']) for v in sorted(selected, key=lambda v: v['pair'])}
suffix = f'''

_FRESH_COMPLETE_ROUTES = {rules!r}
for _fresh_pair, _fresh_route in _FRESH_COMPLETE_ROUTES.items():
    for _fresh_key in list(_DATA['route_map']):
        if _fresh_key == _fresh_pair or _fresh_key.startswith(_fresh_pair + '|'):
            _DATA['route_map'][_fresh_key] = _fresh_route
    _DATA['route_map'][_fresh_pair] = _fresh_route
_FRESH_COMPLETE_PARENT = agent

def agent(observation, configuration=None):
    result = _FRESH_COMPLETE_PARENT(observation, configuration)
    pair = '|'.join(observation['town']['unlocked_shops'][:2])
    active = int(observation['step']) >= 144 and pair in _FRESH_COMPLETE_ROUTES
    agent.telemetry['fresh_complete_pair'] = pair if active else ''
    agent.telemetry['fresh_complete_route'] = str(_FRESH_COMPLETE_ROUTES[pair]) if active else ''
    return result

agent.telemetry = {{}}

def kaggle_fresh_complete_schedule_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
source = base.read_text(encoding='utf-8') + suffix
if use_land:
    source += '\n' + (HERE / 'land_queue_suffix.py').read_text(encoding='utf-8')
source += '\n\ndef kaggle_fresh_execution_schedule_entrypoint(observation, configuration=None):\n    return agent(observation, configuration)\n'
ast.parse(source)
dest = HERE / 'candidate_fresh_combined_v1.py'
assert not dest.exists()
dest.write_text(source, encoding='utf-8', newline='\n')
manifest = dict(at_utc=datetime.now(timezone.utc).isoformat(), candidate=str(dest), candidate_sha256=sha(dest),
                parent_sha256=sha(base), use_funded_land=bool(use_land), land_point_gain=land_gain,
                selected_rules=rules, omitted_as_redundant=[v['pair'] for v in omitted],
                expected_entrypoint='kaggle_fresh_execution_schedule_entrypoint',
                plan_sha256=sha(HERE / 'COMBINATION_PLAN.md'),
                input_hashes={str(p): sha(p) for p in [HERE / 'route_search/survivors.json', HERE / 'broad_routes/survivors.json',
                                                       HERE / 'funded_land_top100_jobs_results.jsonl', HERE / 'land_queue_suffix.py']})
(HERE / 'combined_v1_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
