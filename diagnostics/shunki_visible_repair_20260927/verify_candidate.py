"""Check compiler, Kaggle entrypoint and both-seat file-loader parity."""

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

CANDIDATE = ROOT / "exp_shunki_visible_repair_20260927.py"
MAIN = ROOT / "main.py"
SEED = 2630399


def main() -> None:
    source = CANDIDATE.read_text(encoding="utf8")
    compile(source, str(CANDIDATE), "exec")
    selected = get_last_callable(source, path=str(CANDIDATE)).__name__
    assert selected == "kaggle_shunki_visible_repair_entrypoint", selected
    rows = []
    for seat in (0, 1):
        files = [str(CANDIDATE), str(MAIN)] if seat == 0 else [str(MAIN), str(CANDIDATE)]
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": SEED}, debug=False)
        env.run(files)
        final = env.steps[-1]
        direct = run_game(str(CANDIDATE), str(MAIN), SEED, seat, False, None, {})
        path_cash = [float(final[seat].reward), float(final[1 - seat].reward)]
        direct_cash = [direct["candidate_reward"], direct["opponent_reward"]]
        assert final[seat].status == final[1 - seat].status == "DONE"
        assert path_cash == direct_cash, (seat, path_cash, direct_cash)
        rows.append({"seat": seat, "file_cash": path_cash, "direct_cash": direct_cash,
                     "first_action": env.steps[1][seat].action})
        print(f"seat {seat} parity passed", flush=True)
    result = {"candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
              "main_sha256": hashlib.sha256(MAIN.read_bytes()).hexdigest(),
              "selected_callable": selected, "rows": rows}
    (HERE / "candidate_parity.json").write_text(json.dumps(result, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
