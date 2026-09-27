"""Build a self-contained visible-stock sale candidate from the uploaded main."""

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_mirror_stock_frontload_20260927.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
APPEND = '''

# Isolated observed-stock mirror sale race experiment.
_STOCK_PARENT = agent
_STOCK_STATS = dict(stock_calls=0, stock_trigger_turns=0, stock_requested_units=0,
                    stock_errors=0)

def agent(observation, configuration=None):
    if isinstance(observation, dict) and int(observation.get('step', -1)) == 0:
        _STOCK_STATS.update(stock_calls=0, stock_trigger_turns=0,
                            stock_requested_units=0, stock_errors=0)
    action = _STOCK_PARENT(observation, configuration)
    _STOCK_STATS['stock_calls'] += 1
    try:
        if not isinstance(observation, dict) or not isinstance(action, dict):
            return action
        step = int(observation.get('step', -1))
        if not 480 <= step < 718 or not _clone_physical_match(observation):
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
        _STOCK_STATS['stock_trigger_turns'] += 1
        _STOCK_STATS['stock_requested_units'] += stock
        return dict(action, market=[['SELL', 'STRAWBERRY', stock], *market])
    except Exception:
        _STOCK_STATS['stock_errors'] += 1
        return action

agent.telemetry = _STOCK_STATS
kaggle_submission_agent = agent

def kaggle_stock_frontload_entrypoint(observation, configuration=None):
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
