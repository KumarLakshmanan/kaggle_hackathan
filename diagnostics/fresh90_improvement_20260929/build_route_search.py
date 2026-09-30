"""Freeze exact-prefix, single-pair whole-schedule counterfactuals."""
import ast
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
from run_panel import ROOT, HERE, sha

base = HERE / 'baseline_cb76fbc4.py'
assert sha(base) == 'cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74'
spec = importlib.util.spec_from_file_location('route_search_base', base)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
data = module._DATA
entries = json.loads((HERE / 'fresh_top100_entries.json').read_text(encoding='utf-8'))
baseline = [json.loads(s) for s in (HERE / 'cb76_top20_jobs_results.jsonl').read_text().splitlines()]
targets = [r for r in baseline if r['candidate_seat'] == 0 and r['result'] == 'loss']
assert {r['rank'] for r in targets} == {8, 9, 10, 19}
outdir = HERE / 'route_search'
outdir.mkdir(exist_ok=True)
assert not (outdir / 'screen_jobs.json').exists()
variants = []
jobs = []
for pair in sorted({r['candidate_telemetry']['minimal_route_pair144'] for r in targets}):
    first = str(data['route_map'][pair.split('|')[0]])
    prefix = data['opening'][:72] + data['routes'][first][72:144]
    distinct = {}
    for route in sorted(data['routes']):
        tape = data['routes'][route]
        if tape[:144] == prefix:
            signature = json.dumps(tape[144:], sort_keys=True, separators=(',', ':'))
            distinct.setdefault(signature, route)
    for route in distinct.values():
        label = pair.lower() + '_' + route
        label = label.replace('|', '_')
        dest = outdir / ('candidate_' + label + '.py')
        assert not dest.exists()
        suffix = f'''

_F90_PAIR = {pair!r}
_F90_ROUTE = {int(route)!r}
for _f90_key in list(_DATA['route_map']):
    if _f90_key == _F90_PAIR or _f90_key.startswith(_F90_PAIR + '|'):
        _DATA['route_map'][_f90_key] = _F90_ROUTE
_DATA['route_map'][_F90_PAIR] = _F90_ROUTE
_F90_PAIR_PARENT = agent


def agent(observation, configuration=None):
    result = _F90_PAIR_PARENT(observation, configuration)
    agent.telemetry['fresh_pair_route'] = str(_F90_ROUTE)
    agent.telemetry['fresh_pair_active'] = int(observation['step']) >= 144 and '|'.join(observation['town']['unlocked_shops'][:2]) == _F90_PAIR
    return result


agent.telemetry = {{}}


def kaggle_fresh_pair_route_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
        source = base.read_text(encoding='utf-8') + suffix
        ast.parse(source)
        dest.write_text(source, encoding='utf-8', newline='\n')
        digest = sha(dest)
        variants.append(dict(label=label, pair=pair, route=route, path=str(dest), candidate_sha256=digest))
        for row in targets:
            if row['candidate_telemetry']['minimal_route_pair144'] != pair:
                continue
            entry = next(e for e in entries if e['rank'] == row['rank'])
            fixture = f"{entry['team_id']}:{entry['episode_id']}"
            jobs.append(dict(job_id=f'{label}:{fixture}:0', fixture_id=fixture, label=label,
                path=str(dest), candidate_sha256=digest, candidate_seat=0, rank=entry['rank'],
                team=entry['team'], team_id=entry['team_id'], episode_id=entry['episode_id'],
                seed=entry['seed'], action_sha256=entry['action_sha256'], replay_sha256=entry['replay_sha256'],
                pair=pair, route=route, entry=entry))
(outdir / 'variants.json').write_text(json.dumps(variants, indent=2), encoding='utf-8')
(outdir / 'screen_jobs.json').write_text(json.dumps(jobs, indent=2), encoding='utf-8')
receipt = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), baseline_sha256=sha(base),
               plan_sha256=sha(HERE / 'ROUTE_SEARCH_PLAN.md'), variants=len(variants), games=len(jobs),
               jobs_sha256=sha(outdir / 'screen_jobs.json'), candidate_catalog_sha256=sha(outdir / 'variants.json'),
               all_prefixes_exact=True, development_only=True)
(outdir / 'freeze.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
