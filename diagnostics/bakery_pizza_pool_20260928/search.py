"""Finite complete-route development screen on three frozen public losses."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.opening_probe_v2_20260928 import qualify as q
from diagnostics.compatible_route_pool_20260928.search import write_candidate, SOURCE_SHA
from diagnostics.local_target_20260928.run_lock import exclusive_run

PAIR = 'BAKERY|PIZZA_SHOP'
FIXTURES = {'live-114235177','live-114243994','live-114289837'}
ROUTES = ['113334903','113340658','113357237','113416130','113431477','113470868',
          '113478215','113615383','113618016','113639519','113835510']


def key(row):
    return row['version'], row['rival'], row['candidate_seat']


def play_with_capture(job):
    original = q.TimedAgent
    class Capture144(original):
        def __init__(self,*args,**kwargs):
            if kwargs.get('capture_step') == 1:
                kwargs['capture_step'] = 144
            super().__init__(*args,**kwargs)
    q.TimedAgent = Capture144
    try:
        row = q.play(job)
        assert row['candidate_capture']['step'] == 144
        assert '|'.join(row['candidate_capture']['shops']) == PAIR
        return row
    finally:
        q.TimedAgent = original


def prepare():
    assert not (HERE/'pool.json').exists()
    assert q.sha(ROOT/'main.py') == SOURCE_SHA and q.sha(q.MANIFEST) == q.MANIFEST_SHA
    spec = importlib.util.spec_from_file_location('bakery_pool_source',ROOT/'main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = module._DATA
    prefix = data['opening'][:72] + data['routes'][str(data['route_map']['BAKERY'])][72:144]
    records, seen = [], set()
    source = (ROOT/'main.py').read_bytes()
    folder = HERE/'candidates'
    folder.mkdir(exist_ok=True)
    for route, actions in sorted(data['routes'].items()):
        if actions[:144] != prefix:
            continue
        digest = hashlib.sha256(json.dumps(actions,sort_keys=True,separators=(',', ':')).encode()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        assert len(actions) == 719
        target = folder/(route+'.py')
        records.append(dict(route=route,route_sha256=digest,candidate=str(target),
            candidate_sha256=write_candidate(source,{PAIR:int(route)},target)))
    assert [r['route'] for r in records] == ROUTES
    fixtures = [f for f in json.loads(q.MANIFEST.read_text(encoding='utf-8'))['live_losses'] if f['fixture_id'] in FIXTURES]
    assert len(fixtures) == 3
    pool = dict(source_sha256=SOURCE_SHA,manifest_sha256=q.MANIFEST_SHA,plan_sha256=q.sha(HERE/'PLAN.md'),
                coverage_sha256=q.sha(ROOT/'diagnostics/compatible_route_coverage_20260928/coverage.json'),
                pair=PAIR,variants=records,fixtures=fixtures,prepared_at_utc=datetime.now(timezone.utc).isoformat())
    (HERE/'pool.json').write_text(json.dumps(pool,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(dict(variants=len(records),games=66,pool_sha256=q.sha(HERE/'pool.json')),indent=2))


def run(workers):
    pool = json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    assert q.sha(ROOT/'main.py') == SOURCE_SHA == pool['source_sha256']
    assert q.sha(q.MANIFEST) == q.MANIFEST_SHA == pool['manifest_sha256']
    assert q.sha(HERE/'PLAN.md') == pool['plan_sha256']
    jobs = []
    for variant in pool['variants']:
        assert q.sha(variant['candidate']) == variant['candidate_sha256']
        for fixture in pool['fixtures']:
            for seat in (0,1):
                base = next(r for r in fixture['baseline_frozen_tape_both_seat_outcomes'] if r['seat']==seat)
                jobs.append(dict(version=variant['route'],rival=fixture['fixture_id'],team=fixture['team'],
                    candidate_seat=seat,seed=int(fixture['seed']),path=variant['candidate'],candidate_sha256=variant['candidate_sha256'],
                    opponent='rawroute:'+fixture['source_action_tape_path'],opponent_action_sha256=fixture['source_opponent_action_sha256'],
                    baseline_result=base['result'],baseline_margin=base['margin'],plan_sha256=pool['plan_sha256']))
    expected = {key(j):j for j in jobs}
    checkpoint = HERE/'screen.jsonl'
    rows = [json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    done = {key(r) for r in rows}
    assert len(done) == len(rows)
    for row in rows:
        assert all(row[k]==v for k,v in expected[key(row)].items())
    pending = [j for j in jobs if key(j) not in done]
    print(f'Bakery/Pizza pool {len(rows)}/66 done; {len(pending)} pending',flush=True)
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(pending),16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play_with_capture,j) for j in pending[start:start+16]]):
                    row=future.result()
                    assert key(row) not in done
                    done.add(key(row));rows.append(row)
                    output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
                    if len(rows)%6==0:
                        print(f'{len(rows)}/66 {row["version"]} {row["team"]} {row["result"]} {row["margin"]:+.0f}',flush=True)
    assert len(rows)==66
    result = dict(complete=True,all_done=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' for r in rows),
        no_errors=all(not r['candidate_errors'] and not r['opponent_errors'] for r in rows),
        pool_sha256=q.sha(HERE/'pool.json'),plan_sha256=pool['plan_sha256'],
        completed_at_utc=datetime.now(timezone.utc).isoformat(),games=sorted(rows,key=key))
    (HERE/'screen.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2))


def select():
    pool = json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    screen = json.loads((HERE/'screen.json').read_text(encoding='utf-8'))
    assert screen['complete'] and screen['all_done'] and screen['no_errors']
    assert screen['pool_sha256']==q.sha(HERE/'pool.json') and screen['plan_sha256']==q.sha(HERE/'PLAN.md')
    summaries = []
    for variant in pool['variants']:
        games = [r for r in screen['games'] if r['version']==variant['route']]
        assert len(games)==6
        pairs = {fixture:[r for r in games if r['rival']==fixture] for fixture in sorted(FIXTURES)}
        assert all(len(rows)==2 for rows in pairs.values())
        summaries.append(dict(route=variant['route'],
            both_seat_wins=sum(all(r['result']=='win' for r in rows) for rows in pairs.values()),
            win_points=sum(q.points(r) for r in games),margin_delta=sum(r['margin']-r['baseline_margin'] for r in games),
            regressions=sum(r['baseline_result']=='win' and r['result']!='win' for r in games),
            fixtures=[dict(fixture_id=f,team=rows[0]['team'],margins=[r['margin'] for r in rows]) for f,rows in pairs.items()]))
    eligible = [r for r in summaries if r['both_seat_wins']>0 and r['regressions']==0]
    result = dict(complete=True,passed=bool(eligible),pool_sha256=q.sha(HERE/'pool.json'),
        screen_sha256=q.sha(HERE/'screen.json'),plan_sha256=q.sha(HERE/'PLAN.md'),summaries=summaries,
        selected_replacements={},selected_at_utc=datetime.now(timezone.utc).isoformat())
    if eligible:
        best = sorted(eligible,key=lambda r:(-r['both_seat_wins'],-r['win_points'],-r['margin_delta'],int(r['route'])))[0]
        variant = next(v for v in pool['variants'] if v['route']==best['route'])
        candidate = HERE/'candidate_selected.py'
        candidate.write_bytes(Path(variant['candidate']).read_bytes())
        assert q.sha(candidate)==variant['candidate_sha256']
        result.update(candidate=str(candidate),candidate_sha256=q.sha(candidate),
                      selected_replacements={PAIR:int(best['route'])},selected_summary=best)
    (HERE/'selection.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='summaries'},indent=2,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('prepare','run','select'));parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    with exclusive_run(HERE/'search.lock'):
        {'prepare':prepare,'run':lambda:run(args.workers),'select':select}[args.phase]()
