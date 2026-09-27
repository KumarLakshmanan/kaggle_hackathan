from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
import copy
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

MAIN = ROOT / 'main_uploaded_disjoint_integrated_20260927_c68fa46f.py'
EXPECTED = 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'


def play(job):
    route, seat, baseline = job
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == EXPECTED
    context = {}
    failures = []
    successes = Counter()
    snapshots = {}
    original_process = engine._process_market
    original_commit = engine._commit_unit
    original_hire = engine._do_hire
    original_land = engine._do_buy_land

    def record(operation, item, price, cash, reason):
        step = context['step']
        failures.append(dict(step=step, operation=operation, item=item,
                             price=price, cash=cash, reason=reason))
        if step not in snapshots:
            snapshots[step] = context['before']

    def tracked_process(state, env):
        obs = state[seat].observation
        context.update(step=int(state[0].observation.get('step', -1)),
                       own_farm=state[0].observation['farms'][seat],
                       before=dict(observation=copy.deepcopy(dict(obs)),
                                   actions=[copy.deepcopy(s.action) for s in state],
                                   configuration=dict(env.configuration)))
        return original_process(state, env)

    def tracked_commit(op, item, price, farm, private, market, shed_capacity=100):
        ours = farm is context.get('own_farm')
        cash = farm['money']
        shed_total = sum(private.get('shed', {}).values())
        ok = original_commit(op, item, price, farm, private, market, shed_capacity)
        if ours and op.startswith('BUY'):
            if ok:
                successes[op+':'+item] += 1
            else:
                reason = 'insufficient_cash' if cash < price else 'shed_full' if shed_total >= shed_capacity else 'other'
                record(op, item, price, cash, reason)
        return ok

    def tracked_hire(farm, private, board_size, mult=1):
        before, cash = len(farm['hands']), farm['money']
        result = original_hire(farm, private, board_size, mult)
        if farm is context.get('own_farm'):
            if len(farm['hands']) == before:
                record('HIRE', None, None, cash, 'unchanged')
            else:
                successes['HIRE'] += 1
        return result

    def tracked_land(farm, board_size):
        before, cash = len(farm['unlocked_quadrants']), farm['money']
        result = original_land(farm, board_size)
        if farm is context.get('own_farm'):
            if len(farm['unlocked_quadrants']) == before:
                record('BUY_LAND', None, None, cash, 'unchanged')
            else:
                successes['BUY_LAND'] += 1
        return result

    try:
        engine._process_market = tracked_process
        engine._commit_unit = tracked_commit
        engine._do_hire = tracked_hire
        engine._do_buy_land = tracked_land
        game = run_game(str(MAIN), 'rawroute:'+route['path'], int(route['seed']), seat, False, None, {})
        assert game['candidate_reward'] == baseline['candidate_reward']
        assert game['opponent_reward'] == baseline['opponent_reward']
        assert game['candidate_status'] == game['opponent_status'] == 'DONE'
        details = dict(team=route['team'], rank=route['rank'], episode_id=route['episode_id'],
                       candidate_seat=seat, baseline_cash_match=True, game=game,
                       failures=failures, successful_units=dict(successes), snapshots=snapshots)
        target = HERE / 'traces' / f"rank-{route['rank']}-seat-{seat}.json.gz"
        raw = json.dumps(details, separators=(',', ':'), ensure_ascii=False).encode('utf8')
        target.write_bytes(gzip.compress(raw))
        return dict(team=route['team'], rank=route['rank'], candidate_seat=seat,
                    baseline_cash_match=True, margin=game['margin'],
                    failures=failures, successful_units=dict(successes),
                    trace_path=str(target.resolve()), trace_sha256=hashlib.sha256(raw).hexdigest())
    finally:
        engine._process_market = original_process
        engine._commit_unit = original_commit
        engine._do_hire = original_hire
        engine._do_buy_land = original_land


if __name__ == '__main__':
    routes = json.loads((ROOT/'diagnostics/current_top100_20260927_0730/non_swept_routes.json').read_text())
    baseline = json.loads((ROOT/'diagnostics/current_top100_20260927_0730/assessment.json').read_text())['games']
    lookup = {(g['team_id'],g['candidate_seat']):g for g in baseline}
    jobs = [(r,seat,lookup[r['team_id'],seat]) for r in routes for seat in (0,1)]
    assert len(jobs) == 46
    (HERE/'traces').mkdir(exist_ok=True)
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), main_sha256=EXPECTED,
               independent_strength_evidence=False, complete=False, games=[])
    if (HERE/'audit.json').exists():
        previous = json.loads((HERE/'audit.json').read_text(encoding='utf8'))
        assert previous['complete'] and len(previous['games']) == 46
        assert not (HERE/'audit_before_seat1_identity_fix.json').exists()
        (HERE/'audit_before_seat1_identity_fix.json').write_text(json.dumps(previous,indent=2,ensure_ascii=False),encoding='utf8')
        # Engine market settlement uses the farms owned by state[0]. Both
        # observation copies have equal values but distinct object identities.
        # Prior seat-0 hooks were correct; rerun the affected seat-1 hooks only.
        out['games'] = [g for g in previous['games'] if g['candidate_seat'] == 0]
        out['reused_seat0_games'] = 23
        out['instrumentation_fix'] = 'Use state[0] farm identity for market settlement in both seats'
        jobs = [j for j in jobs if j[1] == 1]
        for r,seat,_ in jobs:
            p = HERE/'traces'/f"rank-{r['rank']}-seat-{seat}.json.gz"
            p.rename(p.with_name(p.name.replace('.json.gz','.before-identity-fix.json.gz')))
    def save():
        (HERE/'audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play,j) for j in jobs]):
            row = future.result()
            out['games'].append(row)
            out['games'].sort(key=lambda g:(g['rank'],g['candidate_seat']))
            save()
            print(f"{len(out['games'])}/46 rank={row['rank']} seat={row['candidate_seat']} "
                  f"failures={len(row['failures'])} cash_match={row['baseline_cash_match']}",flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat())
    save()
