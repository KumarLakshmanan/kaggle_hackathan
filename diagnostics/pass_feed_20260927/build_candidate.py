"""Append the experimental carried-wheat feed wrapper to frozen main.py."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_pass_feed_20260927.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"

WRAPPER = r'''

# EXPERIMENTAL 2026-09-26: use spare carried wheat on an otherwise idle animal.
_PASS_FEED_PARENT = agent
_PASS_FEED_REPORT = {"triggers": 0, "errors": 0}

def agent(observation, configuration=None):
    if int(observation.get("step", -1)) == 0:
        _PASS_FEED_REPORT.update(triggers=0, errors=0)
    action = _PASS_FEED_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        day = step // 24
        if not 12 <= day <= 28:
            return action
        player = int(observation["player"])
        farm = observation["farms"][player]
        private = observation["private"]
        positions = [farm["farmer"]] + list(farm["hands"])
        commands = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        if len(commands) != len(positions):
            return action
        result = None
        for actor, (pos, command) in enumerate(zip(positions, commands)):
            if not command or command[0] != "PASS":
                continue
            inv = private["inventories"][actor]
            if inv.get("WHEAT", 0) < 2:
                continue
            tile = farm["tiles"][pos[1]][pos[0]]
            if not isinstance(tile, dict) or tile.get("animal") not in ("COW", "SHEEP"):
                continue
            if tile.get("fed_today"):
                continue
            if result is None:
                result = copy.deepcopy(action)
            if actor == 0:
                result["farmer"] = ["FEED"]
            else:
                result["hands"][actor - 1] = ["FEED"]
            _PASS_FEED_REPORT["triggers"] += 1
        return result if result is not None else action
    except Exception:
        _PASS_FEED_REPORT["errors"] += 1
        return action

agent.telemetry = _PASS_FEED_REPORT

# Kaggle's file-path loader must see the actual policy callable last.
def kaggle_main_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''


def main() -> None:
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED
    OUTPUT.write_bytes(raw + WRAPPER.encode("utf8"))
    print(OUTPUT, hashlib.sha256(OUTPUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
