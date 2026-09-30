"""Compare complete saved-action panels by route hash and candidate seat."""

import json
from pathlib import Path
import sys


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf8"))
    assert data["summary"]["all_done"] and data["unique_routes"] == 100
    assert len(data["rows"]) == 100
    rows = {row["action_sha256"]: row for row in data["rows"]}
    assert len(rows) == 100
    return rows, data


def compare(base_path, candidate_path, output_path):
    base, a = load(base_path)
    candidate, b = load(candidate_path)
    assert base.keys() == candidate.keys()
    route_rows = []
    game_rows = []
    for key in base:
        old, new = base[key], candidate[key]
        assert (old["episode_id"], old["source_seat"], old["seed"]) == (
            new["episode_id"], new["source_seat"], new["seed"])
        old_games = {g["candidate_seat"]: g for g in old["games"]}
        new_games = {g["candidate_seat"]: g for g in new["games"]}
        assert old_games.keys() == new_games.keys() == {0, 1}
        for seat in (0, 1):
            x, y = old_games[seat], new_games[seat]
            assert x["candidate_status"] == x["opponent_status"] == "DONE"
            assert y["candidate_status"] == y["opponent_status"] == "DONE"
            game_rows.append({
                "hash": key, "team": old["team"], "seat": seat,
                "old_margin": x["margin"], "new_margin": y["margin"],
                "margin_delta": y["margin"] - x["margin"],
                "own_cash_delta": y["candidate_reward"] - x["candidate_reward"],
                "rival_cash_delta": y["opponent_reward"] - x["opponent_reward"],
                "old_adv_turns": (x["candidate_telemetry"] or {}).get("clone_gate_adv_turns", 0),
                "new_adv_turns": (y["candidate_telemetry"] or {}).get("clone_gate_adv_turns", 0),
            })
        route_rows.append({
            "hash": key, "team": old["team"],
            "old_margin": old["pair_margin"],
            "new_margin": new["pair_margin"],
            "margin_delta": new["pair_margin"] - old["pair_margin"],
        })
    summary = {
        "base_sha256": a["candidate_sha256"],
        "candidate_sha256": b["candidate_sha256"],
        "route_wins": [sum(r["old_margin"] > 0 for r in route_rows),
                       sum(r["new_margin"] > 0 for r in route_rows)],
        "seat_wins": [sum(g["old_margin"] > 0 for g in game_rows),
                      sum(g["new_margin"] > 0 for g in game_rows)],
        "route_rescues": sum(r["old_margin"] <= 0 < r["new_margin"] for r in route_rows),
        "route_reversals": sum(r["old_margin"] > 0 >= r["new_margin"] for r in route_rows),
        "seat_rescues": sum(g["old_margin"] <= 0 < g["new_margin"] for g in game_rows),
        "seat_reversals": sum(g["old_margin"] > 0 >= g["new_margin"] for g in game_rows),
        "changed_routes": sum(r["margin_delta"] != 0 for r in route_rows),
        "changed_games": sum(g["margin_delta"] != 0 for g in game_rows),
        "margin_delta": sum(r["margin_delta"] for r in route_rows),
        "own_cash_delta": sum(g["own_cash_delta"] for g in game_rows),
        "rival_cash_delta": sum(g["rival_cash_delta"] for g in game_rows),
        "worst_route_delta": min(r["margin_delta"] for r in route_rows),
        "best_route_delta": max(r["margin_delta"] for r in route_rows),
        "advanced_games": sum(g["new_adv_turns"] > 0 for g in game_rows),
    }
    result = {"summary": summary,
              "changed_routes": [r for r in route_rows if r["margin_delta"]],
              "changed_games": [g for g in game_rows if g["margin_delta"]]}
    Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    compare(*sys.argv[1:])
