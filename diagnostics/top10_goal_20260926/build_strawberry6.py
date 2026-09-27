"""Build a separate six-site strawberry opening candidate.

The source route buys six melon seeds over steps 6, 7, 9 and 10, then
plants them on steps 7, 8, 10 and 11. This swaps that complete funded
bundle without changing later route logic. It is a screening experiment.
"""

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_strawberry6_opening_20260926.py"
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"

TAIL = '''
# EXPERIMENT ONLY: funded six-site strawberry opening.
_STRAW6_PARENT = agent
_STRAW6_STATS = dict(straw6_changed=0, straw6_skipped=0)
_STRAW6_BUYS = {6: 2, 7: 1, 9: 1, 10: 2}
_STRAW6_PLANTS = {7: 2, 8: 1, 10: 1, 11: 2}

def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _STRAW6_STATS.update(straw6_changed=0, straw6_skipped=0)
    action = _STRAW6_PARENT(observation, configuration)
    buy_expected = _STRAW6_BUYS.get(step, 0)
    plant_expected = _STRAW6_PLANTS.get(step, 0)
    if not (buy_expected or plant_expected):
        _STRAW6_STATS.update(getattr(_STRAW6_PARENT, 'telemetry', {}))
        return action
    market = [list(order) for order in action.get('market', [])]
    hands = [list(command) for command in action.get('hands', [])]
    buy_matches = [order for order in market
                   if len(order) >= 3 and order[:2] == ['BUY_SEED', 'MELON']]
    plant_matches = [command for command in hands
                     if command == ['PLANT', 'MELON']]
    if sum(int(order[2]) for order in buy_matches) != buy_expected or len(plant_matches) != plant_expected:
        _STRAW6_STATS['straw6_skipped'] += 1
        _STRAW6_STATS.update(getattr(_STRAW6_PARENT, 'telemetry', {}))
        return action
    for order in buy_matches:
        order[1] = 'STRAWBERRY'
    for command in plant_matches:
        command[1] = 'STRAWBERRY'
    _STRAW6_STATS['straw6_changed'] += 1
    _STRAW6_STATS.update(getattr(_STRAW6_PARENT, 'telemetry', {}))
    return dict(action, market=market, hands=hands)

agent.telemetry = _STRAW6_STATS
kaggle_submission_agent = agent

'''

source = SOURCE.read_text(encoding="utf8")
assert source.count(MARKER) == 1
candidate = source.replace(MARKER, TAIL + MARKER)
ast.parse(candidate)
OUTPUT.write_text(candidate, encoding="utf8")
print({
    "main_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    "candidate": str(OUTPUT),
})
