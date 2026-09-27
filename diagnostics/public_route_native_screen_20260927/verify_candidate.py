"""Kaggle loader and raw-action parity for the packaged candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

CANDIDATE = ROOT / "exp_shunki_public_route_20260927.py"
BASE = ROOT / "main.py"
MANIFEST = json.loads((ROOT / "diagnostics" / "top10_goal_20260926" /
                       "double_yarn_highsheep_4routes_summary.json").read_text(encoding="utf8"))
SOURCE = next(row for row in MANIFEST if row["team"] == "ShunkiKyoya")


def file_game(seed: int, seat: int) -> dict:
    files = [str(CANDIDATE), str(BASE)] if seat == 0 else [str(BASE), str(CANDIDATE)]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(files)
    final = env.steps[-1]
    return {"own": float(final[seat].reward), "rival": float(final[1-seat].reward),
            "statuses": [final[seat].status, final[1-seat].status],
            "first_action": env.steps[1][seat].action}


def main() -> None:
    loaded = get_last_callable(CANDIDATE.read_text(encoding="utf8"), path=str(CANDIDATE)).__name__
    assert loaded == "kaggle_shunki_recorded_entrypoint"
    rows = []
    for seat in (0, 1):
        packaged = run_game(str(CANDIDATE), str(BASE), 2628016, seat, False, None, {})
        raw = run_game(f"rawroute:{SOURCE['path']}", str(BASE), 2628016, seat, False, None, {})
        assert packaged["candidate_status"] == packaged["opponent_status"] == "DONE"
        assert (packaged["candidate_reward"], packaged["opponent_reward"]) == (
            raw["candidate_reward"], raw["opponent_reward"])
        path = file_game(0, seat)
        direct = run_game(str(CANDIDATE), str(BASE), 0, seat, False, None, {})
        assert path["statuses"] == ["DONE", "DONE"]
        assert (path["own"], path["rival"]) == (
            direct["candidate_reward"], direct["opponent_reward"])
        rows.append({"seat": seat,
                     "development_raw_route_cash": [raw["candidate_reward"], raw["opponent_reward"]],
                     "development_packaged_cash": [packaged["candidate_reward"], packaged["opponent_reward"]],
                     "seed0_file_cash": [path["own"], path["rival"]],
                     "seed0_direct_cash": [direct["candidate_reward"], direct["opponent_reward"]],
                     "first_action": path["first_action"]})
        print("seat", seat, "raw and loader parity passed", flush=True)
    result = {"loaded_name": loaded,
              "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
              "main_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
              "source_action_sha256": SOURCE["action_sha256"], "rows": rows}
    (HERE / "candidate_parity.json").write_text(json.dumps(result, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
