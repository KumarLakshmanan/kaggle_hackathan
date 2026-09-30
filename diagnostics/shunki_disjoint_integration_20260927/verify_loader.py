import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kaggle_environments.agent import get_last_callable
from paired_benchmark import _load_module, make
from diagnostics.shunki_disjoint_integration_20260927.verify import branch, RIVALS


if __name__ == "__main__":
    manifest = json.loads((HERE / "manifest.json").read_text())
    candidate = Path(manifest["candidate"])
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == manifest["candidate_sha256"]
    result = json.loads((HERE / "verification.json").read_text())
    assert result["complete"] and result["passed"]
    loaded = get_last_callable(candidate.read_text(encoding="utf8"), path=str(candidate)).__name__
    assert loaded == "kaggle_disjoint_integrated_entrypoint"
    previous = {tuple(r["key"]): r["game"] for r in result["rows"]}
    rows = []
    for rival, seed, expected_branch in (("C95", 2680209, "F"), ("a2", 2690000, "Q")):
        for seat in (0, 1):
            opponent = _load_module(RIVALS[rival], "integrated_file_opponent")
            try:
                env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
                agents = [str(candidate), opponent.agent] if seat == 0 else [opponent.agent, str(candidate)]
                env.run(agents)
                final = env.steps[-1]
                cash = [float(final[seat].reward), float(final[1-seat].reward)]
                direct = previous[rival, seed, seat]
                assert cash == [direct["candidate_reward"], direct["opponent_reward"]]
                assert final[seat].status == final[1-seat].status == "DONE"
                assert branch(direct) == expected_branch
                nonpass = sum((frame[seat].action or {}).get("farmer", ["PASS"])[0] != "PASS" for frame in env.steps[1:])
                assert nonpass > 100
                rows.append({"rival": rival, "seed": seed, "seat": seat, "branch": expected_branch,
                             "file_cash": cash, "direct_cash": [direct["candidate_reward"], direct["opponent_reward"]],
                             "statuses": [final[seat].status, final[1-seat].status], "nonpass_farmer_commands": nonpass})
                print("File parity", rival, seed, seat, cash, flush=True)
            finally:
                sys.modules.pop(opponent.__name__, None)
    prior_path = ROOT / "diagnostics/shunki_farmice_observed_20260927/top50_decision.json"
    prior = json.loads(prior_path.read_text(encoding="utf8"))
    branches = []
    for row in prior["rows"]:
        for game in row["games"]:
            selected = branch(game)
            assert selected != "Q"
            assert (selected == "F") == (row["team"] == "DECEM")
            branches.append({"team": row["team"], "seat": game["candidate_seat"], "branch": selected,
                             "margin": game["margin"]})
    assert len(branches) == 100 and sum(x["margin"] > 0 for x in branches) == 88
    proof = {"candidate_sha256": manifest["candidate_sha256"], "new_games": 0, "reused_games": 100,
             "source_results": str(prior_path), "source_results_sha256": hashlib.sha256(prior_path.read_bytes()).hexdigest(),
             "sweeps": 44, "seat_wins": 88, "all_done": prior["all_done"], "branches": branches,
             "proof": "Shared a2 prefix; no saved case enters Q; only DECEM enters F. Every integrated action is therefore identical to its recorded component."}
    (HERE / "top50_reuse_proof.json").write_text(json.dumps(proof, indent=2, ensure_ascii=False), encoding="utf8")
    (HERE / "loader_parity.json").write_text(json.dumps({"candidate_sha256": manifest["candidate_sha256"],
                                                       "loaded_name": loaded, "rows": rows, "passed": True}, indent=2), encoding="utf8")
