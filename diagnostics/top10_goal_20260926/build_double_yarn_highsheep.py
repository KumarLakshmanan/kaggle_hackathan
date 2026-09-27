"""Build an isolated complete-route alternative for visible high-sheep rivals."""

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_double_yarn_highsheep_20260926.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"

TAIL = '''
# EXPERIMENT ONLY: select complete route 12 when two Yarn Stores and a visible
# rival sheep lead indicate that the incumbent route 9 is underproducing wool.
_DYHS_PARENT_ROUTER = _IMPL.chassis.router
_DYHS_REPORT = dict(dyhs_selected=0, dyhs_errors=0)


def _dyhs_rival_sheep(observation):
    player = int(observation['player'])
    rival = observation['farms'][1 - player]
    return sum(isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
               and tile.get('animal') == 'SHEEP'
               for row in rival['tiles'] for tile in row)


def _dyhs_router(observation, step, state):
    selected = _DYHS_PARENT_ROUTER(observation, step, state)
    if step == 144:
        try:
            shops = tuple((observation.get('town') or {}).get('unlocked_shops') or ())[:2]
            active = (selected == 9 and shops == ('YARN_STORE', 'YARN_STORE')
                      and _dyhs_rival_sheep(observation) >= 3)
        except Exception:
            _DYHS_REPORT['dyhs_errors'] += 1
            active = False
        state['dyhs_selected'] = active
        if active:
            _DYHS_REPORT['dyhs_selected'] += 1
    if 144 <= step < 648 and state.get('dyhs_selected'):
        state['route'] = 12
        return 12
    return selected


_IMPL.chassis.router = _dyhs_router
_DYHS_PARENT_AGENT = agent


def agent(observation, configuration=None):
    if int(observation.get('step', -1)) == 0:
        _DYHS_REPORT.update(dyhs_selected=0, dyhs_errors=0)
    action = _DYHS_PARENT_AGENT(observation, configuration)
    _DYHS_REPORT.update(getattr(_DYHS_PARENT_AGENT, 'telemetry', {}))
    return action


agent.telemetry = _DYHS_REPORT
kaggle_submission_agent = agent

'''


def main():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert digest == EXPECTED, digest
    source = SOURCE.read_text(encoding="utf8")
    assert source.count(MARKER) == 1
    candidate = source.replace(MARKER, TAIL + MARKER)
    ast.parse(candidate)
    OUTPUT.write_text(candidate, encoding="utf8")
    print(json.dumps({"source_sha256": digest,
                      "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
