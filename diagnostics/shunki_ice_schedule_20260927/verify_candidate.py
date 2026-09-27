"""Kaggle final-callable and exact file/direct execution parity, both seats."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable
from paired_benchmark import run_game


def main():
    candidate = ROOT / "exp_shunki_ice_schedule_20260927.py"
    baseline = ROOT / "main.py"
    build = json.loads((HERE / "build_manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == build["candidate_sha256"]
    loaded = get_last_callable(candidate.read_text(encoding="utf8"), path=str(candidate)).__name__
    assert loaded == "kaggle_shunki_ice_schedule_entrypoint", loaded
    selected = json.loads((HERE / "seed_selection.json").read_text(encoding="utf8"))["selected"]
    seed = selected[0]
    rows = []
    for seat in (0, 1):
        agents = [str(candidate), str(baseline)] if seat == 0 else [str(baseline), str(candidate)]
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run(agents)
        final = env.steps[-1]
        direct = run_game(str(candidate), str(baseline), seed, seat, False, None, {})
        path_cash = [float(final[seat].reward), float(final[1 - seat].reward)]
        direct_cash = [direct["candidate_reward"], direct["opponent_reward"]]
        assert final[seat].status == final[1 - seat].status == "DONE"
        assert direct["candidate_status"] == direct["opponent_status"] == "DONE"
        assert path_cash == direct_cash, (seat, path_cash, direct_cash)
        rows.append({"seat": seat, "file_cash": path_cash, "direct_cash": direct_cash,
                     "first_action": env.steps[1][seat].action})
        print("file-loader parity passed", seat, path_cash, flush=True)
    (HERE / "candidate_parity.json").write_text(json.dumps({"candidate_sha256": build["candidate_sha256"],
                                                           "loaded_name": loaded, "seed": seed, "rows": rows}, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
