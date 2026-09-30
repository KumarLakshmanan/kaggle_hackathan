"""Kaggle file-loader versus direct-call parity, both seats on seed 0."""

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

CANDIDATE = ROOT / "exp_physical_milk_sale_20260927.py"
BASE = ROOT / "main.py"
SEED = 0
OUTPUT = HERE / "file_parity_seed0.json"
EXPECTED_LOADED = "kaggle_main_entrypoint"


def file_game(seat: int) -> dict:
    files = [str(CANDIDATE), str(BASE)] if seat == 0 else [str(BASE), str(CANDIDATE)]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": SEED}, debug=False)
    env.run(files)
    final = env.steps[-1]
    return {"candidate_reward": float(final[seat].reward),
            "opponent_reward": float(final[1-seat].reward),
            "candidate_status": final[seat].status,
            "opponent_status": final[1-seat].status,
            "first_action": env.steps[1][seat].action}


def main() -> None:
    loaded = get_last_callable(CANDIDATE.read_text(encoding="utf8"), path=str(CANDIDATE)).__name__
    assert loaded == EXPECTED_LOADED
    rows = []
    for seat in (0, 1):
        path = file_game(seat)
        direct = run_game(str(CANDIDATE), str(BASE), SEED, seat, False, None, {})
        assert path["candidate_status"] == path["opponent_status"] == "DONE"
        assert direct["candidate_status"] == direct["opponent_status"] == "DONE"
        assert path["candidate_reward"] == direct["candidate_reward"]
        assert path["opponent_reward"] == direct["opponent_reward"]
        assert path["first_action"]["market"]
        rows.append({"seat": seat, "file_path": path,
                     "direct": {"own": direct["candidate_reward"],
                                "rival": direct["opponent_reward"],
                                "margin": direct["margin"],
                                "telemetry": direct["candidate_telemetry"]}})
        print("seat", seat, "margin", direct["margin"], flush=True)
    result = {"seed": SEED, "loaded_name": loaded,
              "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
              "main_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
              "rows": rows}
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
