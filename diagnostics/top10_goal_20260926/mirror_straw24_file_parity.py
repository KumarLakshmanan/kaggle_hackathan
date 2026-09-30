"""Verify Kaggle's file-path loader executes the strawberry-only candidate."""

import hashlib
import json
from pathlib import Path
import sys

from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

CANDIDATE = ROOT / "exp_mirror_straw24_20260926.py"
BASE = ROOT / "main.py"
SEED = 2611700
OUTPUT = Path(__file__).with_name("mirror_straw24_file_parity.json")


def file_game(seat):
    files = [str(CANDIDATE), str(BASE)] if seat == 0 else [str(BASE), str(CANDIDATE)]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": SEED},
               debug=False)
    env.run(files)
    final = env.steps[-1]
    return {
        "candidate_reward": float(final[seat].reward),
        "opponent_reward": float(final[1-seat].reward),
        "candidate_status": final[seat].status,
        "opponent_status": final[1-seat].status,
        "first_action": env.steps[1][seat].action,
    }


def main():
    loaded = get_last_callable(CANDIDATE.read_text(encoding="utf8"),
                               path=str(CANDIDATE)).__name__
    assert loaded == "kaggle_main_entrypoint", loaded
    rows = []
    for seat in (0, 1):
        path_row = file_game(seat)
        direct = run_game(str(CANDIDATE), str(BASE), SEED, seat, False, None, {})
        assert path_row["candidate_status"] == path_row["opponent_status"] == "DONE"
        assert direct["candidate_status"] == direct["opponent_status"] == "DONE"
        assert path_row["candidate_reward"] == direct["candidate_reward"]
        assert path_row["opponent_reward"] == direct["opponent_reward"]
        assert path_row["first_action"]["market"]
        rows.append({"seat": seat, "file_path": path_row,
                     "direct": {"candidate_reward": direct["candidate_reward"],
                                "opponent_reward": direct["opponent_reward"],
                                "margin": direct["margin"]}})
        print(seat, direct["margin"], flush=True)
    OUTPUT.write_text(json.dumps({
        "seed": SEED, "loaded_name": loaded,
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
        "rows": rows,
    }, indent=2), encoding="utf8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
