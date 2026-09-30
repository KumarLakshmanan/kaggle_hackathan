"""Verify promoted main.py through Kaggle's file-path loader in both seats."""

import hashlib
import json
from pathlib import Path
import sys

from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
BACKUP = ROOT / "main_before_mirror_straw24_20260926_08aa268a.py"
SEED = 2611700
OUTPUT = Path(__file__).with_name("mirror_straw24_promoted_parity.json")


def file_game(seat):
    files = [str(MAIN), str(BACKUP)] if seat == 0 else [str(BACKUP), str(MAIN)]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": SEED},
               debug=False)
    env.run(files)
    final = env.steps[-1]
    return {
        "main_reward": float(final[seat].reward),
        "backup_reward": float(final[1-seat].reward),
        "main_status": final[seat].status,
        "backup_status": final[1-seat].status,
        "first_action": env.steps[1][seat].action,
    }


def main():
    main_hash = hashlib.sha256(MAIN.read_bytes()).hexdigest()
    backup_hash = hashlib.sha256(BACKUP.read_bytes()).hexdigest()
    assert main_hash == "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
    assert backup_hash == "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
    loaded = get_last_callable(MAIN.read_text(encoding="utf8"), path=str(MAIN)).__name__
    assert loaded == "kaggle_main_entrypoint", loaded
    rows = []
    for seat in (0, 1):
        file_result = file_game(seat)
        direct = run_game(str(MAIN), str(BACKUP), SEED, seat, False, None, {})
        assert file_result["main_status"] == file_result["backup_status"] == "DONE"
        assert direct["candidate_status"] == direct["opponent_status"] == "DONE"
        assert file_result["main_reward"] == direct["candidate_reward"]
        assert file_result["backup_reward"] == direct["opponent_reward"]
        assert file_result["first_action"]["market"]
        rows.append({"seat": seat, "file_path": file_result,
                     "direct_margin": direct["margin"]})
        print(f"seat={seat} margin={direct['margin']}", flush=True)
    OUTPUT.write_text(json.dumps({"seed": SEED, "loaded_name": loaded,
                                  "main_sha256": main_hash,
                                  "backup_sha256": backup_hash,
                                  "rows": rows}, indent=2), encoding="utf8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
