"""Meaningful native parity, information boundaries and commitment probes."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; sys.path.insert(0, str(ROOT))
from kaggriculture_engine import native_core as core
from kaggriculture_engine.engine import canonical, Box
from kaggriculture_engine.pro import simulation, scheduler, scenarios, value
from kaggriculture_engine.pro.beliefs import RivalBelief
from kaggriculture_engine.pro.planner import search
from kaggriculture_engine.pro.runtime import itinerary


def main():
    jobs = json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
    rows = []; timings = {}; input_payload = None
    for rank in (1, 8, 10):
        job = next(j for j in jobs if j['rank'] == rank and j['candidate_seat'] == 0)
        replay = json.loads(gzip.decompress(Path(job['entry']['replay_path']).read_bytes()))
        for step in (0, 143, 144, 239, 478, 718):
            for seat in (0, 1):
                obs = copy.deepcopy(replay['steps'][step][seat]['observation']); obs['step'] = step
                cfg = dict(replay['configuration'], seed=999999)
                belief = RivalBelief().update(obs, cfg)
                alternative = scenarios.generate(obs, belief, anchors=True)
                assert alternative == scenarios.generate(obs, belief, anchors=True)
                assert alternative == scenarios.generate(obs, RivalBelief().update(obs, dict(cfg, seed=42)), anchors=True)
                act = replay['steps'][step+1][seat]['action']
                for scenario in alternative:
                    world = simulation.make_world(obs, cfg, scenario)
                    theirs = scenarios.rival_action(world, seat, act, scenario)
                    joint = [None, None]; joint[seat] = act; joint[1-seat] = theirs
                    cache = simulation.TransitionCache(2)
                    result = cache.advance(world, joint)
                    direct = copy.deepcopy(world)
                    for p in (0, 1): direct[0][p].action = copy.deepcopy(joint[p])
                    core.interpreter(*direct)
                    for entry in direct[0]: entry.observation.step = step+1
                    assert canonical(result) == canonical(direct)
                    repeat = cache.advance(world, joint); assert canonical(result) == canonical(repeat)
                    repeat[0][seat].observation.private['shed']['WHEAT'] = -1234
                    assert canonical(cache.advance(world, joint)) == canonical(result)
                    assert cache.hits == 2 and cache.misses == 1
                    rows.append({'rank': rank, 'step': step, 'seat': seat, 'scenario': scenario['name'], 'passed': True})
                if rank == 1 and step == 144 and seat == 0: input_payload = {'observation': obs, 'configuration': cfg}
        del replay
    cfg = {'turnsPerDay': 24, 'boardSize': 10, 'shedCapacity': 100, 'episodeSteps': 720,
           'maxMarketOrdersPerTurn': 10, 'farmHandCostMult': 1, 'weedSpawnChance': 0.}
    farm = core._new_farm(10, 3000); other = core._new_farm(10, 3000); private = core._new_private()
    obs = {'farms': [farm, other], 'private': private, 'player': 0, 'step': 0, 'day': 0, 'hour': 0,
           'market': core._new_market(), 'town': core._new_town()}
    private['seeds']['WHEAT'] = 2; farm['hands'] = [[3, 4]]; private['inventories'].append({})
    plan = scheduler.commitment(obs, {'WHEAT': 2}); act = scheduler.action(obs, cfg, plan)
    plants = [u for u in [act['farmer']]+act['hands'] if u[0] == 'PLANT']
    assert len(plants) == 2
    probe = simulation.make_world(obs, cfg, scenarios.generate(obs, RivalBelief().update(obs, cfg))[0])
    after = simulation.TransitionCache(0).advance(probe, [act, {'farmer':['PASS']}])
    assert scheduler.counts(after[0][0].observation.farms[0])['WHEAT'] == 2
    # Supply must be carried before feed can execute; animal ownership in shed is insufficient.
    animal_obs = copy.deepcopy(obs); af = animal_obs['farms'][0]; af['hands'] = []
    af['tiles'][4][4] = core._new_animal('GOOSE', 0)
    animal_obs['private'] = core._new_private(); animal_obs['private']['shed']['WHEAT'] = 2
    ap = scheduler.commitment(animal_obs); first = scheduler.action(animal_obs, cfg, ap)
    assert first['farmer'][0] == 'PICKUP'
    world = simulation.make_world(animal_obs, cfg, scenarios.generate(animal_obs, RivalBelief().update(animal_obs, cfg))[0])
    world = simulation.TransitionCache(0).advance(world, [first, {'farmer':['PASS']}])
    second = scheduler.action(simulation.observation(world, 0), cfg, ap)
    assert second['farmer'][0] == 'FEED'
    world = simulation.TransitionCache(0).advance(world, [second, {'farmer':['PASS']}])
    assert world[0][0].observation.farms[0]['tiles'][4][4]['fed_today']
    # Current seed holdings and animal commitments prevent duplicate purchase.
    assert not any(o[0] == 'BUY_ANIMAL' for o in first['market'])
    model = json.loads((HERE/'value_model.json').read_text())
    assert not set(model['train_episodes']) & set(model['holdout_episodes'])
    assert len(value.features(obs)) == model['feature_count']
    terminal = copy.deepcopy(obs); terminal['step'] = 719
    assert value.estimate(terminal, model)['uncertainty'] == 0
    spec = importlib.util.spec_from_file_location('pro_probe', HERE/'engineering_candidate.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    start = time.perf_counter(); module.agent(copy.deepcopy(obs), cfg); timings['initial_candidate_seconds'] = time.perf_counter()-start
    start = time.perf_counter()
    report = search(input_payload['observation'], input_payload['configuration'],
        RivalBelief().update(input_payload['observation'], input_payload['configuration']),
        lambda o, c: itinerary(module._DATA, o, c), model, max_transitions=4096, online=True)
    timings['online_macro_seconds'] = time.perf_counter()-start
    assert all(c['complete'] for c in report['cases']) and report['transitions'] <= 4096
    (HERE/'example_input.json').write_text(json.dumps(input_payload), encoding='utf-8')
    (HERE/'example_forecast.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    # Observe-only history cannot depend on a supplied hidden episode seed.
    for setting in (cfg, dict(cfg, seed=123)):
        tracker = RivalBelief(); tracker.update(obs, setting)
        result = tracker.update(dict(obs, step=1, hour=1), setting, {'market': []})
        if 'last' in locals(): assert result == last
        last = result
    # Cache benchmark compares exactly the same transitions and returns fresh values.
    tick = time.perf_counter(); cache = simulation.TransitionCache(4)
    for _ in range(40): cache.advance(probe, [act, {'farmer':['PASS']}])
    timings['cached_40_seconds'] = time.perf_counter()-tick
    tick = time.perf_counter(); empty = simulation.TransitionCache(0)
    for _ in range(40): empty.advance(probe, [act, {'farmer':['PASS']}])
    timings['uncached_40_seconds'] = time.perf_counter()-tick
    receipt = {'passed': True, 'native_parity_and_cache_cases': rows, 'case_count': len(rows),
        'focused_probes': ['distinct seeded planting', 'actual pickup before feed', 'existing animal commitment',
                           'group-separated fitting', 'terminal cash', 'complete macro horizons', 'hidden seed independence'],
        'timings': timings, 'macro_transitions': report['transitions'], 'macro_selected': report['selected'],
        'source_hashes': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'kaggriculture_engine/pro').glob('*.py')}}
    (HERE/'engineering_checks.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('native_parity_and_cache_cases', 'source_hashes')}, indent=2))


if __name__ == '__main__': main()
