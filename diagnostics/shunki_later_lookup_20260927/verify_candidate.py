"""Confirm Kaggle's final callable and both-seat file-loader parity."""

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

CANDIDATE = ROOT / "exp_shunki_later_lookup_20260927.py"
MAIN = ROOT / "main.py"


def main() -> None:
    build = json.loads((HERE / "build_manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == build["candidate_sha256"]
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == (
        "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b")
    loaded = get_last_callable(CANDIDATE.read_text(encoding="utf8"),
                               path=str(CANDIDATE)).__name__
    assert loaded == "kaggle_shunki_later_lookup_entrypoint", loaded
    rows = []
    for seat in (0, 1):
        files = [str(CANDIDATE), str(MAIN)] if seat == 0 else [str(MAIN), str(CANDIDATE)]
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 2630216},
                   debug=False)
        env.run(files)
        final = env.steps[-1]
        direct = run_game(str(CANDIDATE), str(MAIN), 2630216, seat, False, None, {})
        path_cash = [float(final[seat].reward), float(final[1 - seat].reward)]
        direct_cash = [direct["candidate_reward"], direct["opponent_reward"]]
        assert final[seat].status == final[1 - seat].status == "DONE"
        assert path_cash == direct_cash, (seat, path_cash, direct_cash)
        rows.append({"seat": seat, "file_cash": path_cash, "direct_cash": direct_cash,
                     "first_action": env.steps[1][seat].action})
        print("seat", seat, "file-loader parity passed", flush=True)
    (HERE / "candidate_parity.json").write_text(
        json.dumps({"loaded_name": loaded,
                    "candidate_sha256": build["candidate_sha256"],
                    "rows": rows}, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
