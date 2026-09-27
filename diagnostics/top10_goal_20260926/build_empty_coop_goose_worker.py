"""Experimental one-goose worker for an otherwise unused existing coop."""

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
DEST = ROOT / "exp_empty_coop_goose_worker_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"
TAIL = '''# EXPERIMENT ONLY: one dedicated worker services a funded unused goose coop.
_GOOSE_WORKER_PARENT = agent
_GOOSE_WORKER_STATE = {}
_GOOSE_WORKER_STATS = dict(goose_worker_sites=0, goose_worker_hires=0,
                           goose_worker_commands=0, goose_worker_errors=0)

def _goose_worker_at_shed(pos):
    return tuple(pos) in ((4, 4), (5, 4), (4, 5), (5, 5))

def _goose_worker_move(pos, target):
    x, y = pos
    tx, ty = target
    if x < tx: return ['EAST']
    if x > tx: return ['WEST']
    if y < ty: return ['SOUTH']
    if y > ty: return ['NORTH']
    return ['PASS']

def _goose_worker_command(obs, state, index):
    farm = obs['farms'][int(obs['player'])]
    private = obs['private']
    pos = farm['hands'][index]
    inv = private['inventories'][index + 1]
    site = state['site']
    sx, sy = site
    tile = farm['tiles'][sy][sx]
    shed = private['shed']
    hour = int(obs['step']) % 24
    if not isinstance(tile, dict) or tile.get('kind') != 'COOP':
        return ['PASS']
    if _goose_worker_at_shed(pos):
        if not tile.get('animal') and inv.get('GOOSE', 0) == 0 and shed.get('GOOSE', 0) > 0:
            return ['PICKUP', 'GOOSE', 1]
        if inv.get('WHEAT', 0) == 0 and shed.get('WHEAT', 0) > 0:
            return ['PICKUP', 'WHEAT', 1]
    if tuple(pos) != tuple(site):
        return _goose_worker_move(pos, site)
    if not tile.get('animal'):
        return ['PLACE', 'GOOSE', 1] if inv.get('GOOSE', 0) else ['PASS']
    if not tile.get('fed_today') and inv.get('WHEAT', 0) > 0:
        return ['FEED']
    if not tile.get('fed_today') and shed.get('WHEAT', 0) > 0 and hour < 14:
        return _goose_worker_move(pos, (4, 4))
    if not tile.get('cared_today'):
        return ['CARE']
    if tile.get('yield_units', 0) > 0:
        return ['HARVEST']
    if tile.get('fertilizer_available'):
        return ['COLLECT_FERTILIZER']
    return ['PASS']

def agent(observation, configuration=None):
    try:
        step = int(observation['step'])
        seat = int(observation['player'])
        if step == 0:
            _GOOSE_WORKER_STATE.pop(seat, None)
            _GOOSE_WORKER_STATS.update(goose_worker_sites=0, goose_worker_hires=0,
                                       goose_worker_commands=0, goose_worker_errors=0)
        action = _GOOSE_WORKER_PARENT(observation, configuration)
        farm = observation['farms'][seat]
        if step == 264 and 'BRUNCH_SPOT' in observation['town']['unlocked_shops']:
            sites = [(x, y) for y, row in enumerate(farm['tiles']) for x, tile in enumerate(row)
                     if isinstance(tile, dict) and tile.get('kind') == 'COOP'
                     and not tile.get('animal')]
            market = [list(o) for o in action.get('market', [])]
            if sites and len(market) < 10 and farm['money'] >= 300:
                site = min(sites, key=lambda p: abs(p[0]-4)+abs(p[1]-4))
                _GOOSE_WORKER_STATE[seat] = {'site': site, 'hand_day': -1, 'hand_index': -1}
                market.append(['BUY_ANIMAL', 'GOOSE', 1])
                _GOOSE_WORKER_STATS['goose_worker_sites'] += 1
                action = dict(action, market=market)
        state = _GOOSE_WORKER_STATE.get(seat)
        if not state:
            return action
        day, hour = divmod(step, 24)
        if 11 <= day <= 29 and hour == 1:
            market = [list(o) for o in action.get('market', [])]
            if len(market) < 10:
                parent_hires = sum(o and o[0] == 'HIRE' for o in market)
                state['hand_day'] = day
                state['hand_index'] = len(farm['hands']) + parent_hires
                market.append(['HIRE'])
                _GOOSE_WORKER_STATS['goose_worker_hires'] += 1
                if len(market) < 10:
                    market.append(['BUY_PRODUCT', 'WHEAT', 2])
                action = dict(action, market=market)
        if state['hand_day'] == day and 0 <= state['hand_index'] < len(farm['hands']):
            index = state['hand_index']
            command = _goose_worker_command(observation, state, index)
            hands = [list(c) for c in action.get('hands', [])]
            while len(hands) <= index:
                hands.append(['PASS'])
            hands[index] = command
            if command != ['PASS']:
                _GOOSE_WORKER_STATS['goose_worker_commands'] += 1
            action = dict(action, hands=hands)
        shed_eggs = int(observation['private']['shed'].get('EGG', 0))
        market = [list(o) for o in action.get('market', [])]
        if shed_eggs > 0 and len(market) < 10 and not any(
                len(o) >= 2 and o[:2] == ['SELL', 'EGG'] for o in market):
            market.insert(0, ['SELL', 'EGG', shed_eggs])
            action = dict(action, market=market)
        _GOOSE_WORKER_STATS.update(getattr(_GOOSE_WORKER_PARENT, 'telemetry', {}))
        return action
    except Exception:
        _GOOSE_WORKER_STATS['goose_worker_errors'] += 1
        return _GOOSE_WORKER_PARENT(observation, configuration)

agent.telemetry = _GOOSE_WORKER_STATS
kaggle_submission_agent = agent

'''

raw = SOURCE.read_text(encoding="utf8")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
assert raw.count(MARKER) == 1
candidate = raw.replace(MARKER, TAIL + MARKER)
ast.parse(candidate)
DEST.write_text(candidate, encoding="utf8")
print(DEST, hashlib.sha256(DEST.read_bytes()).hexdigest())
