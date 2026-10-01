"""Bounded open-loop planner over exact Kaggriculture native transitions.

This module is deliberately separate from the frozen online candidate. It
generates executable worker and market programs from the current observation,
then ranks exact scenario rollouts. Its leaf score includes only current cash
margin and discounted inventory salvage; it assigns no value to future output
that has not been produced in the native rollout.
"""
from __future__ import annotations

import copy
import itertools
import json
import time
from dataclasses import dataclass

from . import engine
from . import native_core as core


@dataclass(frozen=True)
class GeneratorLimits:
    """Hard synthesis limits; these bound candidate generation per beam node."""

    max_actions_per_node: int = 72
    max_single_changes: int = 20
    max_joint_changes: int = 28
    max_joint_pool_options: int = 18
    max_joint_combinations: int = 180
    max_workers_changed: int = 3
    max_options_per_worker_for_joint: int = 3
    max_worker_options_per_worker: int = 12
    max_coordinated_plant_groups: int = 12
    max_build_templates: int = 12
    max_compound_programs: int = 12
    max_investment_order_options: int = 16
    max_sale_candidates: int = 6
    max_market_program_candidates: int = 24
    max_added_investment_orders: int = 2
    max_added_sale_orders: int = 1
    max_seed_order_quantity: int = 3
    max_product_order_quantity: int = 2


DEFAULT_LIMITS = GeneratorLimits()


def _copy(value):
    return copy.deepcopy(value)


def _observation(observation):
    return observation


def _units_from_action(action, worker_count):
    units = [_copy(action.get('farmer', ['PASS']))]
    hands = action.get('hands', [])
    if not isinstance(hands, list):
        hands = []
    units.extend(_copy(hands[:max(0, worker_count - 1)]))
    units.extend([['PASS'] for _ in range(worker_count - len(units))])
    return units


def _action_from_units(reference, units, market=None):
    action = _copy(reference)
    action['farmer'] = _copy(units[0]) if units else ['PASS']
    action['hands'] = _copy(units[1:])
    action['market'] = _copy(reference.get('market', [])) if market is None else _copy(market)
    return action


def _normalize_action(action, worker_count):
    if not isinstance(action, dict):
        action = {}
    result = _copy(action)
    units = _units_from_action(result, worker_count)
    result['farmer'] = units[0]
    result['hands'] = units[1:]
    if not isinstance(result.get('market', []), list):
        result['market'] = []
    return result


def _positions(farm):
    return [list(farm.get('farmer', [0, 0]))] + [list(pos) for pos in farm.get('hands', [])]


def _tile(farm, pos):
    x, y = pos
    size = len(farm.get('tiles', []))
    if not (0 <= x < size and 0 <= y < size):
        return 'LOCKED'
    return farm['tiles'][y][x]


def _shed_access(board_size):
    return core._shed_access_tiles(board_size)


def _first_steps(source, target, board_size):
    """Return one-step shortest-path alternatives; locked tiles are traversable."""
    sx, sy = source
    tx, ty = target
    choices = []
    if tx > sx:
        choices.append(('EAST', sx + 1, sy))
    elif tx < sx:
        choices.append(('WEST', sx - 1, sy))
    if ty > sy:
        choices.append(('SOUTH', sx, sy + 1))
    elif ty < sy:
        choices.append(('NORTH', sx, sy - 1))
    result = []
    for name, x, y in choices:
        if 0 <= x < board_size and 0 <= y < board_size:
            result.append([name])
    return result


def _mature_harvestable(tile, day):
    if not isinstance(tile, dict) or tile.get('kind') != 'PLANT' or tile.get('yield_units', 0) <= 0:
        return False
    crop = tile.get('crop')
    if crop not in core.CROPS:
        return False
    crop_data = core.CROPS[crop]
    return day - int(tile.get('planted_day', day)) >= crop_data['first_yield_day']


def _pickup_needs(observation, worker_index):
    """Needed shed items inferred only from visible owned state and own stock."""
    seat = int(observation['player'])
    farm = observation['farms'][seat]
    private = observation['private']
    invs = private.get('inventories', [])
    inv = invs[worker_index] if worker_index < len(invs) else {}
    shed = private.get('shed', {})
    need = {}

    unfed = 0
    empty_structures = {animal: 0 for animal in core.ANIMALS}
    has_plant = False
    for row in farm.get('tiles', []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get('kind') == 'PLANT':
                has_plant = True
            animal = tile.get('animal')
            if animal in core.ANIMALS and not tile.get('fed_today', False):
                unfed += 1
            if tile.get('kind') in ('COOP', 'PASTURE') and animal is None:
                for animal_name, animal_data in core.ANIMALS.items():
                    if animal_data['structure'] == tile.get('kind'):
                        empty_structures[animal_name] += 1

    if shed.get('WHEAT', 0) > 0 and inv.get('WHEAT', 0) < min(3, max(1, unfed)):
        need['WHEAT'] = min(int(shed['WHEAT']), min(3, max(1, unfed)) - int(inv.get('WHEAT', 0)))
    if has_plant and shed.get('FERTILIZER', 0) > 0 and inv.get('FERTILIZER', 0) <= 0:
        need['FERTILIZER'] = 1
    for animal, count in empty_structures.items():
        if count > 0 and shed.get(animal, 0) > 0 and inv.get(animal, 0) < count:
            need[animal] = min(int(shed[animal]), count - int(inv.get(animal, 0)), 2)
    return need


def _unit_options(observation, worker_index, limits, configuration=None):
    """State-derived direct work and first steps toward feasible work targets."""
    seat = int(observation['player'])
    farm = observation['farms'][seat]
    private = observation['private']
    cfg = configuration or {}
    board_size = int(cfg.get('boardSize', len(farm['tiles'])))
    day = int(observation.get('day', 0))
    pos = _positions(farm)[worker_index]
    invs = private.get('inventories', [])
    inv = invs[worker_index] if worker_index < len(invs) else {}
    shed = private.get('shed', {})
    seeds = private.get('seeds', {})
    options = {}

    def add_goal(target, command, priority):
        target_tile = _tile(farm, target)
        shed_command = command and command[0] in ('DROP', 'PICKUP')
        if target_tile == 'LOCKED' and not shed_command:
            return
        distance = abs(pos[0] - target[0]) + abs(pos[1] - target[1])
        if distance == 0:
            key = engine.canonical(command)
            options[key] = max(priority, options.get(key, -10**9))
            return
        move_priority = priority - 3 * distance
        for move in _first_steps(pos, target, board_size):
            key = engine.canonical(move)
            options[key] = max(move_priority, options.get(key, -10**9))

    for y, row in enumerate(farm['tiles']):
        for x, tile in enumerate(row):
            if tile == 'LOCKED':
                continue
            target = [x, y]
            if isinstance(tile, dict):
                kind = tile.get('kind')
                if kind == 'PLANT':
                    if _mature_harvestable(tile, day):
                        add_goal(target, ['HARVEST'], 110)
                    if not tile.get('watered_today', False):
                        add_goal(target, ['WATER'], 32)
                    if inv.get('FERTILIZER', 0) > 0 and int(tile.get('fertilized_until_day', -1)) < day:
                        add_goal(target, ['FERTILIZE'], 38)
                elif kind in ('COOP', 'PASTURE'):
                    animal = tile.get('animal')
                    if animal in core.ANIMALS:
                        if int(tile.get('yield_units', 0)) > 0:
                            add_goal(target, ['HARVEST'], 105)
                        if not tile.get('fed_today', False) and inv.get('WHEAT', 0) > 0:
                            add_goal(target, ['FEED'], 88)
                        if (not tile.get('cared_today', False)
                                and (tile.get('fed_today', False) or inv.get('WHEAT', 0) > 0)):
                            add_goal(target, ['CARE'], 36)
                        if tile.get('fertilizer_available', False):
                            add_goal(target, ['COLLECT_FERTILIZER'], 48)
                    else:
                        for animal_name, animal_data in core.ANIMALS.items():
                            if animal_data['structure'] == kind and inv.get(animal_name, 0) > 0:
                                add_goal(target, ['PLACE', animal_name], 82)
                elif kind == 'WEED':
                    add_goal(target, ['DIG'], 44)
            elif tile is None:
                for crop, quantity in seeds.items():
                    if quantity > 0 and crop in core.CROPS:
                        add_goal(target, ['PLANT', crop], 64 + min(12, int(observation['market']['prices'].get(crop, 0)) // 20))
                available_animals = set()
                for animal_name in core.ANIMALS:
                    if inv.get(animal_name, 0) > 0 or shed.get(animal_name, 0) > 0:
                        available_animals.add(animal_name)
                for animal_name in sorted(available_animals):
                    if core.ANIMALS[animal_name]['structure'] == 'COOP':
                        add_goal(target, ['BUILD_COOP'], 45)
                    else:
                        add_goal(target, ['BUILD_PASTURE'], 45)

    # DROP clears the worker's entire pack, including any overflow. Native
    # rollout valuation decides whether a partially fitting drop is worthwhile.
    shed_capacity = int(cfg.get('shedCapacity', 100))
    shed_room = max(0, shed_capacity - sum(int(n) for n in shed.values()))
    if shed_room > 0 and any(int(n) > 0 for n in inv.values()):
        for target in _shed_access(board_size):
            add_goal(list(target), ['DROP'], 42)

    for item, qty in _pickup_needs(observation, worker_index).items():
        if qty <= 0:
            continue
        priority = 62 if item in core.ANIMALS else (54 if item == 'WHEAT' else 35)
        for target in _shed_access(board_size):
            add_goal(list(target), ['PICKUP', item, int(qty)], priority)

    ranked = sorted(options.items(), key=lambda pair: (-pair[1], pair[0]))
    return [(json.loads(command), priority) for command, priority in ranked[:limits.max_worker_options_per_worker]]


def _action_units_feasible(observation, units, configuration=None, baseline_units=None):
    """Use native unit transitions to reject clipped or ineffective work bundles."""
    seat = int(observation['player'])
    farm = observation['farms'][seat]
    private = observation['private']
    cfg = configuration or {}
    board_size = int(cfg.get('boardSize', len(farm['tiles'])))
    turns_per_day = max(1, int(cfg.get('turnsPerDay', 24)))
    shed_capacity = int(cfg.get('shedCapacity', 100))
    day = int(observation.get('day', 0))
    demand = {}
    for index, command in enumerate(units):
        if not (isinstance(command, list) and command and command[0] == 'PLANT'):
            continue
        if len(command) < 2 or command[1] not in core.CROPS or index >= len(units):
            return False
        crop = command[1]
        demand[crop] = demand.get(crop, 0) + 1
    blocked = {crop for crop, count in demand.items()
               if count > int(private.get('seeds', {}).get(crop, 0))}
    positions = _positions(farm)
    for index, command in enumerate(units):
        changed = baseline_units is None or index >= len(baseline_units) or command != baseline_units[index]
        if not changed or not (isinstance(command, list) and command and command[0] == 'CARE'):
            continue
        tile = _tile(farm, positions[index])
        if isinstance(tile, dict) and tile.get('animal') in core.ANIMALS and not tile.get('fed_today', False):
            fed_earlier = any(
                units[prior] == ['FEED'] and positions[prior] == positions[index]
                for prior in range(index)
            )
            if not fed_earlier:
                return False

    shadow_farm = _copy(farm)
    shadow_private = _copy(private)
    for index, command in enumerate(units):
        if not isinstance(command, list) or not command:
            return False
        if command[0] == 'PASS':
            continue
        changed = baseline_units is None or index >= len(baseline_units) or command != baseline_units[index]
        if command[0] == 'PICKUP' and changed:
            if len(command) < 2:
                return False
            requested = int(command[2]) if len(command) >= 3 else 1
            if requested <= 0 or int(shadow_private.get('shed', {}).get(command[1], 0)) < requested:
                return False
        before = engine.canonical([shadow_farm, shadow_private])
        allowed = ['PASS'] if (command[0] == 'PLANT' and len(command) >= 2
                               and command[1] in blocked) else command
        core._apply_unit_action(shadow_farm, shadow_private, index, allowed,
                                board_size, day, turns_per_day, shed_capacity)
        after = engine.canonical([shadow_farm, shadow_private])
        if changed and before == after:
            return False
    return True


def _investment_orders(observation, reference, configuration, limits):
    """Bounded investment menu, optionally preceded by one sale to fund it."""
    private = observation['private']
    farm = observation['farms'][int(observation['player'])]
    cfg = configuration or {}
    max_orders = max(1, int(cfg.get('maxMarketOrdersPerTurn', 10)))
    base = _copy(reference.get('market', []))
    room = max_orders - len(base)
    if room <= 0:
        return []

    investments = []
    workers = 1 + len(farm.get('hands', []))
    seed_qty = max(1, min(limits.max_seed_order_quantity, workers))
    for crop in core.CROPS:
        investments.append(['BUY_SEED', crop, seed_qty])
    for animal in core.ANIMALS:
        investments.append(['BUY_ANIMAL', animal, 1])
    product_qty = max(1, min(limits.max_product_order_quantity, workers))
    investments.extend([['BUY_PRODUCT', 'WHEAT', product_qty], ['BUY_PRODUCT', 'FERTILIZER', 1]])
    investments.extend([['HIRE'], ['BUY_LAND']])

    def order_cost(order):
        op = order[0]
        if op == 'BUY_SEED':
            return core.CROPS[order[1]]['seed'] * int(order[2])
        if op == 'BUY_ANIMAL':
            return core.ANIMALS[order[1]]['cost'] * int(order[2])
        if op == 'BUY_PRODUCT':
            return int(observation['market']['prices'].get(order[1], 100)) * int(order[2])
        if op == 'HIRE':
            return core._hire_cost(int(farm.get('hires_today', 0)),
                                   int(cfg.get('farmHandCostMult', core.FARM_HAND_COST_MULT)))
        if op == 'BUY_LAND':
            extra_land = max(0, len(farm.get('unlocked_quadrants', [])) - 1)
            return core.LAND_PRICES[extra_land] if extra_land < len(core.LAND_PRICES) else float('inf')
        return 0

    investments.sort(key=lambda order: (order_cost(order), engine.canonical(order)))
    selected_investments = investments[:limits.max_investment_order_options]
    # Preserve the costly expansion families inside the bounded menu. Land is
    # retained only while at least one native land purchase remains available.
    reserves = [order for order in investments if order[0] == 'BUY_ANIMAL']
    extra_land = max(0, len(farm.get('unlocked_quadrants', [])) - 1)
    if extra_land < len(core.LAND_PRICES):
        reserves.extend(order for order in investments if order[0] == 'BUY_LAND')
    for order in reserves:
        if order not in selected_investments and selected_investments:
            selected_investments[-1] = order
    investments = selected_investments
    sale_candidates = []
    already_selling = {}
    for order in base:
        if isinstance(order, list) and len(order) >= 3 and order[0] == 'SELL':
            already_selling[order[1]] = already_selling.get(order[1], 0) + max(0, int(order[2]))
    for item in core.PRODUCTS:
        stock = int(private.get('shed', {}).get(item, 0)) - already_selling.get(item, 0)
        if stock > 0:
            sale_candidates.append(['SELL', item, min(stock, 2)])
    sale_candidates.sort(key=lambda order: (-int(order[2]) * int(observation['market']['prices'].get(order[1], 0)), order[1]))
    sale_candidates = sale_candidates[:limits.max_sale_candidates]

    bundles = []
    max_invest = max(0, limits.max_added_investment_orders)
    for count in range(1, max_invest + 1):
        for bundle in itertools.combinations(investments, count):
            if len(bundle) > room:
                continue
            bundles.append((list(bundle), []))
            if len(sale_candidates) and count + 1 <= room and limits.max_added_sale_orders:
                for sale in sale_candidates:
                    if any(order[0] == 'BUY_PRODUCT' and order[1] == sale[1] for order in bundle):
                        continue
                    bundles.append((list(bundle), [_copy(sale)]))

    # Cheap bundles first so a tight node/time budget still tests funded starts.
    bundles.sort(key=lambda row: (
        sum(order_cost(order) for order in row[0]) - sum(
            int(sale[2]) * int(observation['market']['prices'].get(sale[1], 0)) for sale in row[1]),
        len(row[1]) * -1,
        engine.canonical([row[1], row[0]]),
    ))
    result = []
    seen = set()
    for investment_bundle, sales in bundles:
        additions = sales + investment_bundle
        if len(additions) > room:
            continue
        queue = base + additions
        key = engine.canonical(queue)
        if key in seen:
            continue
        seen.add(key)
        result.append((queue, additions))
    return result


def generate_actions(observation, reference, configuration=None, limits=DEFAULT_LIMITS):
    """Return bounded candidate programs, baseline first, with required orders.

    Each result is ``{'action': ..., 'required_orders': [...]}``. The latter
    lists only orders appended by this generator and is used to prove that a
    multi-order investment actually committed in every modeled scenario.
    """
    cfg = configuration or {}
    seat = int(observation['player'])
    farm = observation['farms'][seat]
    worker_count = 1 + len(farm.get('hands', []))
    reference = _normalize_action(reference, worker_count)
    base_units = _units_from_action(reference, worker_count)
    baseline = {'action': reference, 'required_orders': [], 'changed_workers': 0, 'branch_hint': 'baseline'}
    candidates = [baseline]
    seen = {engine.canonical(reference)}

    def add(units, market, required_orders=(), branch_hint=None):
        if len(candidates) >= limits.max_actions_per_node:
            return
        if not _action_units_feasible(observation, units, cfg, base_units):
            return
        action = _action_from_units(reference, units, market)
        key = engine.canonical(action)
        if key in seen:
            return
        seen.add(key)
        changed = sum(1 for old, new in zip(base_units, units) if old != new)
        candidates.append({'action': action, 'required_orders': _copy(list(required_orders)),
                           'changed_workers': changed, 'branch_hint': branch_hint})

    unit_options = []
    singles = []
    for index in range(worker_count):
        options = _unit_options(observation, index, limits, configuration)
        options = [(command, score) for command, score in options if command != base_units[index]]
        unit_options.append(options)
        for command, priority in options:
            units = _copy(base_units)
            units[index] = command
            singles.append((priority, index, command, units))
    singles.sort(key=lambda item: (-item[0], item[1], engine.canonical(item[2])))
    single_rows = singles[:limits.max_single_changes]
    for priority, index, command, units in single_rows:
        add(units, reference.get('market', []), branch_hint='physical')
        if len(candidates) >= limits.max_actions_per_node:
            return candidates

    # Small joint bundles permit independent workers to plant, care and move
    # together. The tuple pool caps combinatorics before cross-worker products.
    joint_pool = []
    per_worker = {}
    for row in singles:
        per_worker.setdefault(row[1], 0)
        if per_worker[row[1]] >= limits.max_options_per_worker_for_joint:
            continue
        joint_pool.append(row)
        per_worker[row[1]] += 1
        if len(joint_pool) >= limits.max_joint_pool_options:
            break
    joint_rows = []
    max_changed = max(2, min(limits.max_workers_changed, worker_count))
    joint_combinations = 0
    for size in range(2, max_changed + 1):
        for bundle in itertools.combinations(joint_pool, size):
            if joint_combinations >= limits.max_joint_combinations:
                break
            joint_combinations += 1
            indexes = [row[1] for row in bundle]
            if len(set(indexes)) != size:
                continue
            units = _copy(base_units)
            for row in bundle:
                units[row[1]] = _copy(row[2])
            if not _action_units_feasible(observation, units, cfg, base_units):
                continue
            score = sum(row[0] for row in bundle)
            joint_rows.append((score, units))
        if joint_combinations >= limits.max_joint_combinations:
            break
    joint_rows.sort(key=lambda row: (-row[0], engine.canonical(row[1])))
    for _, units in joint_rows[:limits.max_joint_changes]:
        add(units, reference.get('market', []), branch_hint='physical')
        if len(candidates) >= limits.max_actions_per_node:
            return candidates

    # Explicit coordinated planting: distinct workers on distinct empty tiles,
    # with total requests bounded by the seed count (the core rejects all
    # same-crop PLANT requests atomically when this limit is exceeded).
    positions = _positions(farm)
    plant_groups = 0
    for crop, seed_count in observation['private'].get('seeds', {}).items():
        if crop not in core.CROPS or int(seed_count) < 2:
            continue
        eligible = [i for i, pos in enumerate(positions)
                    if _tile(farm, pos) is None]
        for size in range(2, min(limits.max_workers_changed, worker_count, int(seed_count), 3) + 1):
            for worker_indexes in itertools.combinations(eligible, size):
                if len({tuple(positions[i]) for i in worker_indexes}) != size:
                    continue
                units = _copy(base_units)
                for index in worker_indexes:
                    units[index] = ['PLANT', crop]
                if _action_units_feasible(observation, units, cfg, base_units):
                    add(units, reference.get('market', []), branch_hint='physical')
                    plant_groups += 1
                if plant_groups >= limits.max_coordinated_plant_groups or len(candidates) >= limits.max_actions_per_node:
                    break
            if plant_groups >= limits.max_coordinated_plant_groups or len(candidates) >= limits.max_actions_per_node:
                break
        if plant_groups >= limits.max_coordinated_plant_groups or len(candidates) >= limits.max_actions_per_node:
            break

    if len(candidates) >= limits.max_actions_per_node:
        return candidates

    investment_programs = _investment_orders(observation, reference, cfg, limits)
    # Add standalone and funded multi-order programs after useful work actions.
    market_rows = []
    for market, required in investment_programs:
        market_rows.append((reference.get('market', []), market, required))
    # A worker can travel toward an empty owned plot or build on its current
    # empty tile while a new animal is bought. Market orders resolve after
    # worker actions, so the bought animal is placed on a later turn.
    build_templates = []
    build_seen = set()
    empty_targets = [(x, y) for y, row in enumerate(farm['tiles'])
                     for x, tile in enumerate(row) if tile is None]
    for worker_index, pos in enumerate(positions[:limits.max_build_templates]):
        for structure, command_name in (('COOP', 'BUILD_COOP'), ('PASTURE', 'BUILD_PASTURE')):
            if _tile(farm, pos) is None:
                choices = [(0, [command_name])]
            elif empty_targets:
                distance = min(abs(pos[0] - x) + abs(pos[1] - y) for x, y in empty_targets)
                target_rows = [(x, y) for x, y in empty_targets
                               if abs(pos[0] - x) + abs(pos[1] - y) == distance]
                choices = [(distance, move) for x, y in target_rows
                           for move in _first_steps(pos, [x, y], int(cfg.get('boardSize', len(farm['tiles']))))]
            else:
                choices = []
            for distance, command in choices:
                units = _copy(base_units)
                units[worker_index] = command
                key = engine.canonical([structure, units])
                if key in build_seen or not _action_units_feasible(observation, units, cfg, base_units):
                    continue
                build_seen.add(key)
                build_templates.append((distance, units, structure))
                if len(build_templates) >= limits.max_build_templates:
                    break
            if len(build_templates) >= limits.max_build_templates:
                break
        if len(build_templates) >= limits.max_build_templates:
            break

    # Limit market synthesis so it cannot crowd out exact physical branches.
    market_limit = min(limits.max_market_program_candidates,
                       max(1, limits.max_actions_per_node // 2))
    used_market = 0
    for _, market, required in market_rows:
        if len(candidates) >= limits.max_actions_per_node or used_market >= market_limit:
            break
        add(base_units, market, required, branch_hint='investment')
        used_market += 1
    if len(candidates) >= limits.max_actions_per_node:
        return candidates

    # A few compound action candidates let one-turn construction accompany a
    # new animal purchase, and let work continue while a funded investment is
    # queued. Full funding is checked by exact native transitions in search.
    physical_templates = []
    for _, _, _, units in singles[:6]:
        physical_templates.append(units)
    for _, units in joint_rows[:4]:
        physical_templates.append(units)
    physical_templates.extend(units for _, units, _ in build_templates)
    dedup_physical = {}
    for units in physical_templates:
        dedup_physical.setdefault(engine.canonical(units), units)
    physical_templates = list(dedup_physical.values())
    compound_count = 0
    per_animal_compounds = {animal: 0 for animal in core.ANIMALS}
    compound_rows = sorted(market_rows,
                           key=lambda row: (0 if any(order[0] == 'BUY_ANIMAL' for order in row[2]) else 1,
                                            engine.canonical(row[2])))
    for _, market, required in compound_rows:
        if compound_count >= limits.max_compound_programs or len(candidates) >= limits.max_actions_per_node:
            break
        bought_animals = {order[1] for order in required if order[0] == 'BUY_ANIMAL'}
        if bought_animals and all(per_animal_compounds[animal] >= 2 for animal in bought_animals):
            continue
        for units in physical_templates:
            commands = [units[0], *units[1:]]
            builds = {'GOOSE': 'BUILD_COOP', 'COW': 'BUILD_PASTURE', 'SHEEP': 'BUILD_PASTURE'}
            if bought_animals and not any(
                command and command[0] == builds[animal]
                for animal in bought_animals for command in commands
            ):
                continue
            previous_count = len(candidates)
            add(units, market, required, branch_hint='combined')
            if len(candidates) > previous_count:
                compound_count += 1
                for animal in bought_animals:
                    per_animal_compounds[animal] += 1
            if compound_count >= limits.max_compound_programs or len(candidates) >= limits.max_actions_per_node:
                break
        if compound_count >= limits.max_compound_programs:
            break
    return candidates


def _orders_committed(control_world, trial_world, seat, orders):
    """Require every appended market order's requested quantity to commit."""
    control_private = control_world[0][seat].observation.private
    trial_private = trial_world[0][seat].observation.private
    control_farm = control_world[0][seat].observation.farms[seat]
    trial_farm = trial_world[0][seat].observation.farms[seat]
    for order in orders:
        op = order[0]
        if op == 'BUY_SEED':
            if int(trial_private['seeds'].get(order[1], 0)) - int(control_private['seeds'].get(order[1], 0)) < int(order[2]):
                return False
        elif op in ('BUY_PRODUCT', 'BUY_ANIMAL'):
            if int(trial_private['shed'].get(order[1], 0)) - int(control_private['shed'].get(order[1], 0)) < int(order[2]):
                return False
        elif op == 'SELL':
            if int(control_private['shed'].get(order[1], 0)) - int(trial_private['shed'].get(order[1], 0)) < int(order[2]):
                return False
        elif op == 'HIRE':
            if len(trial_farm.get('hands', [])) - len(control_farm.get('hands', [])) < 1:
                return False
        elif op == 'BUY_LAND':
            if len(trial_farm.get('unlocked_quadrants', [])) - len(control_farm.get('unlocked_quadrants', [])) < 1:
                return False
    return True


def _node_utilities(worlds, seat):
    return [engine.terminal_value(world, seat) for world in worlds]


def _score(worlds, seat):
    utilities = _node_utilities(worlds, seat)
    margins = [engine.cash_margin(world, seat) for world in worlds]
    return (min(utilities), sum(utilities), min(margins), sum(margins))


@dataclass
class _Node:
    worlds: list
    actions: list
    score: tuple
    incumbent: bool = False
    branch: str = 'baseline'


def _branch_for(parent, action, reference, is_incumbent):
    if is_incumbent:
        return 'baseline'
    if parent.branch != 'baseline':
        return parent.branch
    worker_changed = (action.get('farmer') != reference.get('farmer')
                      or action.get('hands') != reference.get('hands'))
    market_changed = action.get('market') != reference.get('market')
    if worker_changed and market_changed:
        return 'combined'
    if market_changed:
        return 'investment'
    if worker_changed:
        return 'physical'
    return 'baseline'


def _node_state_key(node):
    # Public market/town and both hypothetical private states matter to later
    # exact price, supply and score transitions, so do not dedupe on farms only.
    return engine.canonical([
        [[state.observation for state in world[0]], [state.status for state in world[0]]]
        for world in node.worlds
    ])


def _select_beam(nodes, width):
    unique = {}
    for node in nodes:
        key = _node_state_key(node)
        current = unique.get(key)
        if current is None or (node.incumbent and not current.incumbent) or node.score > current.score:
            unique[key] = node
    rows = list(unique.values())
    chosen = []
    chosen_ids = set()
    baseline = [node for node in rows if node.incumbent]
    if baseline:
        best_baseline = max(baseline, key=lambda node: node.score)
        chosen.append(best_baseline)
        chosen_ids.add(id(best_baseline))
    # Reserve one branch for each distinct first-deviation family. This lets
    # committed plans survive an inventory-only intermediate dip without
    # assigning any value to hypothetical unexecuted production.
    for branch in ('investment', 'physical', 'combined'):
        if len(chosen) >= width:
            break
        group = [node for node in rows if node.branch == branch and id(node) not in chosen_ids]
        if group:
            best_branch = max(group, key=lambda node: node.score)
            chosen.append(best_branch)
            chosen_ids.add(id(best_branch))
    for node in sorted(rows, key=lambda item: item.score, reverse=True):
        if len(chosen) >= width:
            break
        if id(node) not in chosen_ids:
            chosen.append(node)
            chosen_ids.add(id(node))
    return chosen


def search_plan(observation, configuration, continuation, horizon=12, width=4,
                max_nodes=400, seconds=10., limits=DEFAULT_LIMITS):
    """Search common open-loop programs under explicit hypothetical rivals.

    The incumbent continuation is evaluated at every depth and retained in the
    beam. Alternative worker and market programs use the same native action
    transition in each scenario. If a bundle adds market orders, a second exact
    control rollout with identical worker actions proves each appended order
    committed fully in every scenario before that candidate is retained.
    """
    if not 1 <= int(horizon) <= 719 or int(width) < 1 or int(max_nodes) < 1 or float(seconds) <= 0:
        raise ValueError('Positive horizon, width, node and time budgets are required.')
    seat = int(observation['player'])
    cfg = dict(configuration or {})
    # Simulator seeds are fixed per explicit synthetic scenario. Do not let a
    # real episode seed influence the continuation either.
    cfg['seed'] = None
    scenario_defs = engine.DEFAULT_SCENARIOS
    worlds = [engine.make_world(observation, cfg, scenario) for scenario in scenario_defs]
    started = time.perf_counter()
    root = _Node(worlds, [], _score(worlds, seat), incumbent=True, branch='baseline')
    frontier = [root]
    effective_width = max(4, int(width))
    nodes = 0
    budget_exhausted = False
    generation_cap_at_limit = False
    completed = []
    deepest_partial = [root]
    effective_horizon = int(horizon)

    for depth in range(effective_horizon):
        expanded = []
        # Process incumbent first to preserve a verified continuation even when
        # the node or wall budget ends part-way through an iteration.
        current_nodes = sorted(frontier, key=lambda node: (not node.incumbent, tuple(-v for v in node.score)))
        for parent in current_nodes:
            if all(world[0][seat].status == 'DONE' for world in parent.worlds):
                completed.append(parent)
                continue
            visible = parent.worlds[0][0][seat].observation
            reference = _normalize_action(continuation(_copy(visible), cfg),
                                          1 + len(visible['farms'][seat].get('hands', [])))
            candidates = generate_actions(visible, reference, cfg, limits)
            if len(candidates) >= limits.max_actions_per_node:
                generation_cap_at_limit = True
            controls = {}
            for candidate_index, candidate in enumerate(candidates):
                is_incumbent = parent.incumbent and candidate_index == 0
                if nodes >= int(max_nodes) or (not is_incumbent and time.perf_counter() - started >= float(seconds)):
                    budget_exhausted = True
                    break
                action = candidate['action']
                next_worlds = []
                control_worlds = None
                if candidate['required_orders']:
                    unit_key = engine.canonical([action.get('farmer'), action.get('hands')])
                    if unit_key not in controls:
                        control_action = _action_from_units(reference, _units_from_action(action, 1 + len(action.get('hands', []))), reference.get('market', []))
                        controls[unit_key] = [
                            engine.advance(world, seat, control_action, reference, scenario)
                            for world, scenario in zip(parent.worlds, scenario_defs)
                        ]
                    control_worlds = controls[unit_key]
                for scenario_index, (world, scenario) in enumerate(zip(parent.worlds, scenario_defs)):
                    result = engine.advance(world, seat, action, reference, scenario)
                    if candidate['required_orders'] and not _orders_committed(
                            control_worlds[scenario_index], result, seat, candidate['required_orders']):
                        next_worlds = []
                        break
                    next_worlds.append(result)
                nodes += 1
                if not next_worlds:
                    continue
                incumbent_child = is_incumbent
                child = _Node(
                    next_worlds,
                    parent.actions + [_copy(action)],
                    _score(next_worlds, seat),
                    incumbent=incumbent_child,
                    branch=_branch_for(parent, action, reference, incumbent_child),
                )
                if len(child.actions) >= effective_horizon or all(w[0][seat].status == 'DONE' for w in next_worlds):
                    completed.append(child)
                else:
                    expanded.append(child)
                if nodes >= int(max_nodes) and candidate_index + 1 < len(candidates):
                    budget_exhausted = True
                    break
                if time.perf_counter() - started >= float(seconds) and candidate_index + 1 < len(candidates):
                    budget_exhausted = True
                    break
            if budget_exhausted:
                break
        if expanded:
            frontier = _select_beam(expanded, effective_width)
            deepest_partial = frontier
        else:
            if not completed:
                # No action survived, but the root or previous beam is still a
                # truthful partial recommendation and the continuation is retained.
                deepest_partial = current_nodes
            break
        if completed and all(len(node.actions) >= effective_horizon for node in completed):
            # Search completed requested depth; no shallower partial may outrank
            # a complete horizon simply because it avoided an investment cost.
            if not frontier:
                break
        if budget_exhausted:
            break

    if completed:
        # Final-season leaves are exact native outcomes; requested-horizon
        # leaves are exact to that horizon. Robust score is not a probability.
        selected = max(completed, key=lambda node: (node.score, len(node.actions)))
        if len(selected.actions) < effective_horizon and not all(
                world[0][seat].status == 'DONE' for world in selected.worlds):
            selected = max(deepest_partial, key=lambda node: (node.score, len(node.actions)))
            selected_complete = False
        else:
            selected_complete = True
    else:
        selected = max(deepest_partial, key=lambda node: (len(node.actions), node.score))
        selected_complete = False

    elapsed = time.perf_counter() - started
    result_rows = []
    for scenario, world, leaf_value in zip(scenario_defs, selected.worlds, _node_utilities(selected.worlds, seat)):
        farms = world[0][0].observation.farms
        result_rows.append({
            'name': scenario['name'],
            'assumption': {
                'rival_stock_multiplier': scenario['stock_multiplier'],
                'rival_market_mode': scenario['market_mode'],
                'rival_worker_actions': 'PASS',
                'synthetic_future_seed': scenario['future_seed'],
            },
            'own_coins': float(farms[seat]['money']),
            'opponent_coins': float(farms[1 - seat]['money']),
            'margin': engine.cash_margin(world, seat),
            'inventory_only_leaf_value': leaf_value,
            'status': world[0][seat].status,
        })
    return {
        'actions': selected.actions,
        'nodes': nodes,
        'evaluated_programs': nodes,
        'requested_horizon': effective_horizon,
        'completed_depth': len(selected.actions),
        'complete_horizon': selected_complete,
        'elapsed_seconds': elapsed,
        'budget_exhausted': budget_exhausted,
        'generation_limits': {
            'max_actions_per_node': limits.max_actions_per_node,
            'max_single_changes': limits.max_single_changes,
            'max_joint_changes': limits.max_joint_changes,
            'max_joint_pool_options': limits.max_joint_pool_options,
            'max_joint_combinations': limits.max_joint_combinations,
            'max_workers_changed': limits.max_workers_changed,
            'max_options_per_worker_for_joint': limits.max_options_per_worker_for_joint,
            'max_worker_options_per_worker': limits.max_worker_options_per_worker,
            'max_coordinated_plant_groups': limits.max_coordinated_plant_groups,
            'max_build_templates': limits.max_build_templates,
            'max_compound_programs': limits.max_compound_programs,
            'max_investment_order_options': limits.max_investment_order_options,
            'max_sale_candidates': limits.max_sale_candidates,
            'max_market_program_candidates': limits.max_market_program_candidates,
            'max_added_sale_orders': limits.max_added_sale_orders,
            'max_added_investment_orders': limits.max_added_investment_orders,
            'max_seed_order_quantity': limits.max_seed_order_quantity,
            'max_product_order_quantity': limits.max_product_order_quantity,
            'effective_beam_width': effective_width,
            'scenario_count': len(scenario_defs),
        },
        'estimated_leaf_value': selected.score[0],
        'scenario_results': result_rows,
        'assumptions': [
            {
                'name': scenario['name'],
                'rival_stock_multiplier': scenario['stock_multiplier'],
                'rival_market_mode': scenario['market_mode'],
                'rival_worker_actions': 'PASS',
                'synthetic_future_seed': scenario['future_seed'],
            }
            for scenario in scenario_defs
        ],
        'uses_hidden_rival_state': False,
        'uses_episode_seed': False,
        'final_season_forecast': all(world[0][seat].status == 'DONE' for world in selected.worlds),
        'selection_rule': 'Best complete requested horizon (or exact native final state) by minimum scenario inventory-only leaf value; incumbent continuation retained in beam.',
        'leaf_value_policy': 'Exact simulated cash margin plus discounted current inventory salvage; no credit for unexecuted planting, animal production, or other future output.',
        'uncertainty': 'The idle, mirror, and frontload scenarios are explicit unweighted hypotheses, not a probability distribution. A common open-loop action sequence is replanned on a new observation.',
        'limitation': 'When complete_horizon is false, outcomes end at completed_depth. Inventory-only leaves can undervalue investments whose production occurs after the rollout horizon.',
    }
