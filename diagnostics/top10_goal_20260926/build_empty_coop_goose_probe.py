"""Probe whether the current planner places a funded goose in an empty coop."""

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
DEST = ROOT / "exp_empty_coop_goose_probe_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"
TAIL = '''# EXPERIMENT ONLY: fund one existing empty coop; no unit actions overridden.
_EMPTY_COOP_PARENT = agent
_EMPTY_COOP_STATS = dict(empty_coop_exposed=0, goose_buy_added=0)

def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _EMPTY_COOP_STATS.update(empty_coop_exposed=0, goose_buy_added=0)
    action = _EMPTY_COOP_PARENT(observation, configuration)
    if step != 264 or 'BRUNCH_SPOT' not in observation['town']['unlocked_shops']:
        _EMPTY_COOP_STATS.update(getattr(_EMPTY_COOP_PARENT, 'telemetry', {}))
        return action
    farm = observation['farms'][int(observation['player'])]
    empty = sum(isinstance(t, dict) and t.get('kind') == 'COOP' and not t.get('animal')
                for row in farm['tiles'] for t in row)
    if empty:
        _EMPTY_COOP_STATS['empty_coop_exposed'] += 1
    market = [list(o) for o in action.get('market', [])]
    if not empty or len(market) >= 10 or farm['money'] < 300:
        _EMPTY_COOP_STATS.update(getattr(_EMPTY_COOP_PARENT, 'telemetry', {}))
        return action
    market.append(['BUY_ANIMAL', 'GOOSE', 1])
    _EMPTY_COOP_STATS['goose_buy_added'] += 1
    _EMPTY_COOP_STATS.update(getattr(_EMPTY_COOP_PARENT, 'telemetry', {}))
    return dict(action, market=market)

agent.telemetry = _EMPTY_COOP_STATS
kaggle_submission_agent = agent

'''

raw = SOURCE.read_text(encoding="utf8")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
assert raw.count(MARKER) == 1
candidate = raw.replace(MARKER, TAIL + MARKER)
ast.parse(candidate)
DEST.write_text(candidate, encoding="utf8")
print(DEST, hashlib.sha256(DEST.read_bytes()).hexdigest())
