"""Run only after both native gates; verify the exact Kaggle file entry point."""
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


if __name__ == "__main__":
    candidate = ROOT / "exp_shunki_market_queue_20260927.py"
    baseline = ROOT / "main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == manifest["candidate_sha256"]
    result = json.loads((HERE / "confirmation.json").read_text(encoding="utf8"))
    assert result["candidate_sha256"] == manifest["candidate_sha256"] and result["passed"]
    assert len(result["completed_phases"]) == 3 and len(result["rows"]) == 384
    loaded = get_last_callable(candidate.read_text(encoding="utf8"), path=str(candidate)).__name__
    assert loaded == "kaggle_market_queue_entrypoint", loaded
    seed = 2660000
    rows = []
    for seat in (0, 1):
        paths = [str(candidate), str(baseline)] if seat == 0 else [str(baseline), str(candidate)]
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run(paths)
        final = env.steps[-1]
        direct = run_game(str(candidate), str(baseline), seed, seat, False, 144, {})
        file_cash = [float(final[seat].reward), float(final[1-seat].reward)]
        direct_cash = [direct["candidate_reward"], direct["opponent_reward"]]
        assert file_cash == direct_cash
        assert final[seat].status == final[1-seat].status == "DONE"
        assert direct["candidate_status"] == direct["opponent_status"] == "DONE"
        assert direct["candidate_telemetry"]["queue_turns"] > 0
        rows.append({"seat": seat, "file_cash": file_cash, "direct_cash": direct_cash,
                     "statuses": [final[seat].status, final[1-seat].status],
                     "direct_max_ms": direct["candidate_timing"]["max_ms"],
                     "first_action": env.steps[1][seat].action})
        print("Both-seat loader parity", seat, file_cash, flush=True)
    (HERE / "loader_parity.json").write_text(json.dumps({"candidate_sha256": manifest["candidate_sha256"],
                                                          "loaded_name": loaded, "seed": seed, "rows": rows,
                                                          "pass": True}, indent=2), encoding="utf8")
