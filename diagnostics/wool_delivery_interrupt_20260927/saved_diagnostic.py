"""Single saved-route executability check; not policy validation."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402


def main() -> None:
    rows = json.loads((HERE.parent / "new_live17_diagnosis_20260927" / "routes" / "summary.json").read_text(encoding="utf8"))
    row = next(x for x in rows if x["episode_id"] == 113800419)
    opponent = f"rawroute:{row['path']}"
    baseline = run_game(str(ROOT / "main.py"), opponent, int(row["seed"]), int(row["our_seat"]), False, None, {})
    candidate = run_game(str(ROOT / "exp_wool_delivery_interrupt_20260927.py"), opponent, int(row["seed"]), int(row["our_seat"]), False, None, {})
    assert baseline["candidate_reward"] == row["our_live_cash"]
    assert baseline["opponent_reward"] == row["rival_live_cash"]
    assert baseline["candidate_status"] == candidate["candidate_status"] == "DONE"
    assert baseline["opponent_status"] == candidate["opponent_status"] == "DONE"
    result = {
        "episode_id": row["episode_id"], "seed": row["seed"],
        "seat": row["our_seat"],
        "baseline": {"own": baseline["candidate_reward"], "rival": baseline["opponent_reward"], "margin": baseline["margin"]},
        "candidate": {"own": candidate["candidate_reward"], "rival": candidate["opponent_reward"], "margin": candidate["margin"], "telemetry": candidate["candidate_telemetry"]},
        "delta_own": candidate["candidate_reward"] - baseline["candidate_reward"],
        "delta_rival": candidate["opponent_reward"] - baseline["opponent_reward"],
        "delta_margin": candidate["margin"] - baseline["margin"],
        "note": "fixed saved rival actions cannot validate improvement",
    }
    (HERE / "saved_diagnostic.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
