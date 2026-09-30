"""Build an isolated observation-latched late strawberry sale candidate."""

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_mirror_stock_frontload_latched_20260927.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
APPEND = '''

# Isolated late observed-stock sale experiment, with public early-mirror latch.
_LATCH_PARENT = agent
_LATCH_STREAK = 0
_LATCHED = False
_LATCH_STATS = dict(latch_calls=0, latch_at=-1, latch_trigger_turns=0,
                    latch_requested_units=0, latch_errors=0)


def agent(observation, configuration=None):
    global _LATCH_STREAK, _LATCHED
    step = int(observation.get('step', -1)) if isinstance(observation, dict) else -1
    if step == 0:
        _LATCH_STREAK = 0
        _LATCHED = False
        _LATCH_STATS.update(latch_calls=0, latch_at=-1, latch_trigger_turns=0,
                            latch_requested_units=0, latch_errors=0)
    same = False
    aligned = False
    try:
        if 144 <= step < 718:
            same = _clone_physical_match(observation)
            _LATCH_STREAK = _LATCH_STREAK + 1 if same else 0
            if not _LATCHED and _LATCH_STREAK >= 24:
                _LATCHED = True
                _LATCH_STATS['latch_at'] = step
            farms = observation['farms']
            aligned = (len(farms) == 2
                       and farms[0]['farmer'] == farms[1]['farmer']
                       and farms[0]['hands'] == farms[1]['hands'])
    except Exception:
        _LATCH_STATS['latch_errors'] += 1
    action = _LATCH_PARENT(observation, configuration)
    _LATCH_STATS['latch_calls'] += 1
    try:
        if not (480 <= step < 718 and _LATCHED and not same and aligned
                and isinstance(action, dict)):
            return action
        market = action.get('market') or []
        if not isinstance(market, list) or len(market) >= 10:
            return action
        if any(isinstance(order, (list, tuple)) and order and
               (order[0] == 'BUY_PRODUCT' or
                (len(order) > 1 and order[0] == 'SELL' and order[1] == 'STRAWBERRY'))
               for order in market):
            return action
        commands = [action.get('farmer') or ['PASS'], *(action.get('hands') or [])]
        if any(isinstance(command, (list, tuple)) and len(command) > 1 and
               command[0] == 'PICKUP' and command[1] == 'STRAWBERRY'
               for command in commands):
            return action
        stock = int((observation.get('private') or {}).get('shed', {}).get('STRAWBERRY', 0) or 0)
        quote = int((observation.get('market') or {}).get('prices', {}).get('STRAWBERRY', 0) or 0)
        if stock < 4 or quote <= 1:
            return action
        _LATCH_STATS['latch_trigger_turns'] += 1
        _LATCH_STATS['latch_requested_units'] += stock
        return dict(action, market=[['SELL', 'STRAWBERRY', stock], *market])
    except Exception:
        _LATCH_STATS['latch_errors'] += 1
        return action


agent.telemetry = _LATCH_STATS
kaggle_submission_agent = agent


def kaggle_latched_stock_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    candidate = SOURCE.read_text(encoding="utf-8") + APPEND
    ast.parse(candidate)
    OUTPUT.write_text(candidate, encoding="utf-8")
    print(json.dumps({"source_sha256": EXPECTED,
                      "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
