"""Compare single-file deployable features with offline replay extraction."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CANDIDATE = ROOT / "exp_physical_milk_sale_20260927.py"
REPLAYS = HERE.parent / "live_submission_56572390_20260926"
DATA = HERE / "physical_opportunities.json"
ACTION_OFFSET = 0


def main() -> None:
    spec = importlib.util.spec_from_file_location("physical_milk_candidate_parity", CANDIDATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    payload = json.loads(DATA.read_text(encoding="utf8"))
    examples = []
    episodes = set()
    for row in payload["rows"]:
        if (row["train"] and row["features"]["item"] == "MILK"
                and row["episode_id"] not in episodes):
            episodes.add(row["episode_id"])
            examples.append(row)
        if len(examples) == 5:
            break
    assert len(examples) == 5
    audit = json.loads((REPLAYS / "audit_latest_100.json").read_text(encoding="utf8"))
    seat_by_episode = {int(row["episode_id"]): int(row["our_seat"]) for row in audit["episodes"]}
    for row in examples:
        episode = int(row["episode_id"])
        seat = seat_by_episode[episode]
        replay = json.loads((REPLAYS / f"episode-{episode}-replay.json").read_text(encoding="utf8"))
        current = None
        for step in range(int(row["step"]) + 1):
            frame = replay["steps"][step][seat]
            action = replay["steps"][step + ACTION_OFFSET][seat].get("action") or {}
            state = module._ps_state(seat, step)
            current = module._ps_features(frame["observation"], action, state, step, seat)
            if any(isinstance(order, list) and len(order) >= 3
                   and order[:2] == ["SELL", "MILK"] and int(order[2] or 0) > 0
                   for order in action.get("market") or []):
                state["last_sale"] = step
        assert current is not None
        expected = row["features"]
        for key in module._PS_MODEL["numeric_features"]:
            assert abs(float(current[key]) - float(expected[key])) < 1e-9, (
                episode, row["step"], key, current[key], expected[key])
    print("matched", len(examples), "distinct development episodes, all numeric features")


if __name__ == "__main__":
    main()
