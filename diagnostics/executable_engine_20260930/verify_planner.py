"""Focused probes for the isolated generated-action planner (no full games)."""
from __future__ import annotations

import copy
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kaggriculture_engine import engine, native_core as core
from kaggriculture_engine import planner


CONFIG = {
    'boardSize': 10,
    'episodeSteps': 48,
    'turnsPerDay': 24,
    'maxMarketOrdersPerTurn': 10,
    'shedCapacity': 100,
    'farmHandCostMult': 1,
    'townShopUnlockInterval': 3,
    'townCenterSellInterval': 24,
    'townShopSellInterval': 4,
    'weedSpawnChance': 0.0,
    'marketParams': {},
    'seed': None,
}


def synthetic_observation(hands=0):
    farms = [core._new_farm(10, 3000), core._new_farm(10, 3000)]
    private = core._new_private()
    farms[0]['hands'] = [[3, 4] for _ in range(hands)]
    private['inventories'] = [{} for _ in range(hands + 1)]
    return {
        'player': 0,
        'farms': farms,
        'market': core._new_market(),
        'town': core._new_town(),
        'day': 0,
        'hour': 0,
        'step': 0,
        'private': private,
        'remainingOverageTime': 60,
    }


def continuation(observation, configuration):
    return {
        'farmer': ['PASS'],
        'hands': [['PASS'] for _ in observation['farms'][observation['player']].get('hands', [])],
        'market': [],
    }


def run():
    checks = []

    # Movement candidates are one legal, state-derived step toward owned work.
    obs = synthetic_observation()
    farm = obs['farms'][0]
    farm['farmer'] = [0, 0]
    obs['private']['seeds']['CARROT'] = 1
    ref = continuation(obs, CONFIG)
    actions = planner.generate_actions(obs, ref, CONFIG)
    moves = [row['action']['farmer'] for row in actions if row['action']['farmer'][0] in core.FARMER_MOVES]
    assert moves and all(len(command) == 1 for command in moves)
    for command in moves:
        dx, dy = core.FARMER_MOVES[command[0]]
        assert 0 <= farm['farmer'][0] + dx < CONFIG['boardSize']
        assert 0 <= farm['farmer'][1] + dy < CONFIG['boardSize']
    checks.append('bounded movement candidates stay in bounds')

    # Multiple workers request only available seeds and plant distinct current tiles.
    obs = synthetic_observation(hands=1)
    obs['farms'][0]['farmer'] = [0, 0]
    obs['farms'][0]['hands'] = [[1, 0]]
    obs['private']['seeds']['CARROT'] = 2
    ref = continuation(obs, CONFIG)
    candidates = planner.generate_actions(obs, ref, CONFIG)
    paired_plant = next(row['action'] for row in candidates
                        if row['action']['farmer'] == ['PLANT', 'CARROT']
                        and row['action']['hands'] == [['PLANT', 'CARROT']])
    world = engine.make_world(obs, CONFIG, engine.DEFAULT_SCENARIOS[0])
    next_state, _ = engine.advance(world, 0, paired_plant, ref, engine.DEFAULT_SCENARIOS[0])
    state = next_state[0].observation
    assert state.private['seeds']['CARROT'] == 0
    assert state.farms[0]['tiles'][0][0]['crop'] == 'CARROT'
    assert state.farms[0]['tiles'][0][1]['crop'] == 'CARROT'
    checks.append('coordinated planting is seed-funded and lands on distinct tiles')

    # Shed drop and pickup are generated only from the worker inventory/shed.
    obs = synthetic_observation()
    obs['farms'][0]['farmer'] = [4, 4]
    obs['private']['inventories'][0]['WHEAT'] = 1
    ref = continuation(obs, CONFIG)
    drop = next(row['action'] for row in planner.generate_actions(obs, ref, CONFIG)
                if row['action']['farmer'] == ['DROP'])
    world = engine.make_world(obs, CONFIG, engine.DEFAULT_SCENARIOS[0])
    dropped, _ = engine.advance(world, 0, drop, ref, engine.DEFAULT_SCENARIOS[0])
    assert dropped[0].observation.private['shed']['WHEAT'] == 1
    assert dropped[0].observation.private['inventories'][0].get('WHEAT', 0) == 0

    obs['private']['inventories'][0] = {}
    obs['private']['shed']['WHEAT'] = 2
    ref = continuation(obs, CONFIG)
    pickup = next(row['action'] for row in planner.generate_actions(obs, ref, CONFIG)
                  if row['action']['farmer'][0] == 'PICKUP'
                  and row['action']['farmer'][1] == 'WHEAT')
    world = engine.make_world(obs, CONFIG, engine.DEFAULT_SCENARIOS[0])
    picked, _ = engine.advance(world, 0, pickup, ref, engine.DEFAULT_SCENARIOS[0])
    assert picked[0].observation.private['shed']['WHEAT'] == 1
    assert picked[0].observation.private['inventories'][0]['WHEAT'] == 1

    # Native shed operations resolve before the locked-tile guard.
    obs = synthetic_observation()
    obs['farms'][0]['farmer'] = [5, 4]
    obs['private']['inventories'][0]['CARROT'] = 1
    ref = continuation(obs, CONFIG)
    locked_drop = next(row['action'] for row in planner.generate_actions(obs, ref, CONFIG)
                       if row['action']['farmer'] == ['DROP'])
    world = engine.make_world(obs, CONFIG, engine.DEFAULT_SCENARIOS[0])
    locked_result, _ = engine.advance(world, 0, locked_drop, ref, engine.DEFAULT_SCENARIOS[0])
    assert locked_result[0].observation.private['shed']['CARROT'] == 1
    checks.append('DROP and PICKUP match native shed and per-worker inventory changes')

    # Building/placement/feed/care/fertilizer work appears only when supported by state.
    obs = synthetic_observation()
    farm = obs['farms'][0]
    farm['farmer'] = [0, 0]
    farm['tiles'][0][0] = {'kind': 'COOP'}
    obs['private']['inventories'][0]['GOOSE'] = 1
    ref = continuation(obs, CONFIG)
    place = next(row['action'] for row in planner.generate_actions(obs, ref, CONFIG)
                 if row['action']['farmer'] == ['PLACE', 'GOOSE'])
    world = engine.make_world(obs, CONFIG, engine.DEFAULT_SCENARIOS[0])
    placed, _ = engine.advance(world, 0, place, ref, engine.DEFAULT_SCENARIOS[0])
    assert placed[0].observation.farms[0]['tiles'][0][0].get('animal') == 'GOOSE'

    # Buy occurs after worker work, so a new animal can fund a legal structure
    # build this turn and remains in the shed for a later PLACE action.
    obs = synthetic_observation()
    obs['farms'][0]['farmer'] = [0, 0]
    ref = continuation(obs, CONFIG)
    animal_build = next(row for row in planner.generate_actions(obs, ref, CONFIG)
                        if row['action']['farmer'] == ['BUILD_COOP']
                        and ['BUY_ANIMAL', 'GOOSE', 1] in row['required_orders'])
    for scenario in engine.DEFAULT_SCENARIOS:
        world = engine.make_world(obs, CONFIG, scenario)
        control = engine.advance(world, 0,
                                 dict(animal_build['action'], market=copy.deepcopy(ref['market'])),
                                 ref, scenario)
        trial = engine.advance(world, 0, animal_build['action'], ref, scenario)
        assert planner._orders_committed(control, trial, 0, animal_build['required_orders'])
        assert trial[0][0].observation.farms[0]['tiles'][0][0]['kind'] == 'COOP'
        assert trial[0][0].observation.private['shed']['GOOSE'] == 1
    checks.append('new animal purchase pairs with a native-legal build and commits in every scenario')

    tile = placed[0].observation.farms[0]['tiles'][0][0]
    assert tile['animal'] == 'GOOSE'
    obs = synthetic_observation(hands=1)
    obs['farms'][0]['farmer'] = [0, 0]
    obs['farms'][0]['hands'] = [[0, 0]]
    obs['farms'][0]['tiles'][0][0] = core._new_animal('GOOSE', 0)
    obs['private']['inventories'][0] = {'WHEAT': 1}
    obs['private']['inventories'][1] = {'WHEAT': 1}
    obs['farms'][0]['tiles'][0][0]['fertilizer_available'] = True
    ref = continuation(obs, CONFIG)
    generated = planner.generate_actions(obs, ref, CONFIG)
    assert any(row['action']['farmer'] == ['FEED'] and row['action']['hands'] == [['CARE']]
               for row in generated)
    collect = next(row['action'] for row in generated
                   if row['action']['farmer'] == ['COLLECT_FERTILIZER'])
    world = engine.make_world(obs, CONFIG, engine.DEFAULT_SCENARIOS[0])
    cared, _ = engine.advance(world, 0, {'farmer': ['FEED'], 'hands': [['CARE']], 'market': []}, ref,
                              engine.DEFAULT_SCENARIOS[0])
    assert cared[0].observation.farms[0]['tiles'][0][0]['fed_today']
    assert cared[0].observation.farms[0]['tiles'][0][0]['cared_today']
    world = engine.make_world(obs, CONFIG, engine.DEFAULT_SCENARIOS[0])
    collected, _ = engine.advance(world, 0, collect, ref, engine.DEFAULT_SCENARIOS[0])
    assert collected[0].observation.private['inventories'][0]['FERTILIZER'] == 1
    checks.append('animal placement, feed, care and fertilizer collection are state-derived')

    # Sale-funded multi-order purchases must really commit in every modeled world.
    obs = synthetic_observation()
    obs['farms'][0]['money'] = 10.0
    obs['private']['shed']['CARROT'] = 2
    ref = continuation(obs, CONFIG)
    bundle_rows = [row for row in planner.generate_actions(obs, ref, CONFIG)
                   if len(row['required_orders']) >= 2
                   and any(order[0] == 'SELL' for order in row['required_orders'])]
    assert bundle_rows
    candidate = next((row for row in bundle_rows
                      if len(row['required_orders']) == 3
                      and sum(order[0] != 'SELL' for order in row['required_orders']) == 2), None)
    assert candidate is not None
    for scenario in engine.DEFAULT_SCENARIOS:
        world = engine.make_world(obs, CONFIG, scenario)
        control_action = dict(candidate['action'], market=copy.deepcopy(ref['market']))
        control = engine.advance(world, 0, control_action, ref, scenario)
        trial = engine.advance(world, 0, candidate['action'], ref, scenario)
        assert planner._orders_committed(control, trial, 0, candidate['required_orders'])
    checks.append('sale-funded multi-order bundles prove every appended order committed')

    # Search reports exact partial depth under node exhaustion and selects a full horizon otherwise.
    obs = synthetic_observation()
    partial = planner.search_plan(obs, CONFIG, continuation, horizon=3, width=1,
                                  max_nodes=1, seconds=5.0)
    assert partial['nodes'] == 1
    assert partial['completed_depth'] == 1
    assert not partial['complete_horizon'] and partial['budget_exhausted']
    assert len(partial['scenario_results']) == len(engine.DEFAULT_SCENARIOS)
    assert all('margin' in row and 'inventory_only_leaf_value' in row for row in partial['scenario_results'])

    baseline_only = planner.GeneratorLimits(max_actions_per_node=1)
    complete = planner.search_plan(obs, CONFIG, continuation, horizon=2, width=1,
                                   max_nodes=4, seconds=5.0, limits=baseline_only)
    assert complete['completed_depth'] == 2
    assert complete['complete_horizon']
    assert complete['uses_hidden_rival_state'] is False
    assert complete['uses_episode_seed'] is False
    observed_seeds = []

    def record_config_seed(current_observation, configuration):
        observed_seeds.append(configuration.get('seed'))
        return continuation(current_observation, configuration)

    seeded_config = dict(CONFIG, seed=99887766)
    planner.search_plan(obs, seeded_config, record_config_seed, horizon=1, width=1,
                        max_nodes=1, seconds=5.0, limits=baseline_only)
    assert observed_seeds == [None]
    checks.append('search preserves incumbent, distinguishes partial/full horizon and clears the real seed')

    return checks


if __name__ == '__main__':
    completed = run()
    print('PASS focused planner probes: ' + '; '.join(completed))
