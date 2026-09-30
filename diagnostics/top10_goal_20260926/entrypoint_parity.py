"""Verify Kaggle file-path loading, both seats, against direct callable play."""

import hashlib
import json
from pathlib import Path
import sys

from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

CANDIDATE = ROOT / "exp_entrypoint_fix_20260926.py"
OLD = ROOT / "main_before_top10_goal_20260926_04b0bdc3.py"
BROKEN = ROOT / "main.py"
SEED = 2610901
OUTPUT = Path(__file__).with_name("entrypoint_parity.json")


def file_game(candidate, seat):
    files = [str(candidate), str(OLD)] if seat == 0 else [str(OLD), str(candidate)]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": SEED},
               debug=False)
    env.run(files)
    final = env.steps[-1]
    first_action = env.steps[1][seat].action
    return {
        "seat": seat,
        "candidate_reward": float(final[seat].reward),
        "opponent_reward": float(final[1 - seat].reward),
        "candidate_status": final[seat].status,
        "opponent_status": final[1 - seat].status,
        "first_action": first_action,
    }


def main():
    loaded_names = {
        path.name: get_last_callable(path.read_text(encoding="utf8"),
                                     path=str(path)).__name__
        for path in (BROKEN, CANDIDATE, OLD)
    }
    assert loaded_names[BROKEN.name] == "_clone_physical_match"
    assert loaded_names[CANDIDATE.name] == "kaggle_main_entrypoint"
    rows = []
    for seat in (0, 1):
        path_row = file_game(CANDIDATE, seat)
        direct = run_game(str(CANDIDATE), str(OLD), SEED, seat, False, None, {})
        assert path_row["candidate_status"] == path_row["opponent_status"] == "DONE"
        assert direct["candidate_status"] == direct["opponent_status"] == "DONE"
        assert path_row["candidate_reward"] == direct["candidate_reward"]
        assert path_row["opponent_reward"] == direct["opponent_reward"]
        assert path_row["first_action"]["market"]
        rows.append({"file_path": path_row, "direct": {
            "candidate_reward": direct["candidate_reward"],
            "opponent_reward": direct["opponent_reward"],
            "margin": direct["margin"],
        }})
        print(f"seat={seat} path/direct cash identical: "
              f"{path_row['candidate_reward']:.0f}/"
              f"{path_row['opponent_reward']:.0f}", flush=True)
    broken_row = file_game(BROKEN, 0)
    assert broken_row["candidate_reward"] == 3000.0
    assert broken_row["first_action"] == {"farmer": ["PASS"], "hands": [], "market": []}
    result = {
        "seed": SEED,
        "source_hashes": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (BROKEN, CANDIDATE, OLD)},
        "loaded_names": loaded_names,
        "fixed_rows": rows,
        "broken_path_negative_control": broken_row,
    }
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
