"""Compare submitted and local policies on the 40 freshly observed live tapes."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def indexed(result):
    return {(route["episode_id"], game["candidate_seat"]): game
            for route in result["rows"] for game in route["games"]}


def main():
    live = load("audit_latest_40.json")["episodes"]
    manifest = load("summary.json")
    backup = load("submitted_backup_40routes.json")
    local = load("main_local_40routes.json")
    assert backup["summary_sha256"] == local["summary_sha256"]
    assert backup["summary_sha256"] == __import__("hashlib").sha256(
        (HERE / "summary.json").read_bytes()).hexdigest()
    assert len(live) == len(manifest) == 40
    old = indexed(backup)
    new = indexed(local)
    assert old.keys() == new.keys() and len(old) == 80
    source = {r["episode_id"]: r for r in manifest}
    live_by_id = {r["episode_id"]: r for r in live}
    rows = []
    for episode in sorted(source):
        observed = live_by_id[episode]
        seat_results = []
        for seat in (0, 1):
            a, b = old[(episode, seat)], new[(episode, seat)]
            assert a["candidate_status"] == a["opponent_status"] == "DONE"
            assert b["candidate_status"] == b["opponent_status"] == "DONE"
            if seat == observed["our_seat"]:
                assert a["candidate_reward"] == observed["our_cash"], episode
                assert a["opponent_reward"] == observed["rival_cash"], episode
                assert a["margin"] == observed["margin"], episode
            seat_results.append({
                "seat": seat,
                "submitted_margin": a["margin"], "local_margin": b["margin"],
                "submitted_own": a["candidate_reward"], "local_own": b["candidate_reward"],
                "submitted_rival": a["opponent_reward"], "local_rival": b["opponent_reward"],
                "own_cash_delta": b["candidate_reward"] - a["candidate_reward"],
                "rival_cash_delta": b["opponent_reward"] - a["opponent_reward"],
                "clone_equal_turns": b["candidate_telemetry"].get("clone_gate_equal_turns", 0),
                "clone_advance_turns": b["candidate_telemetry"].get("clone_gate_adv_turns", 0),
            })
        rows.append({
            "episode_id": episode, "team": source[episode]["team"],
            "live_margin": observed["margin"], "our_live_seat": observed["our_seat"],
            "submitted_pair_margin": sum(x["submitted_margin"] for x in seat_results),
            "local_pair_margin": sum(x["local_margin"] for x in seat_results),
            "seats": seat_results,
        })
    old_pair_wins = sum(r["submitted_pair_margin"] > 0 for r in rows)
    new_pair_wins = sum(r["local_pair_margin"] > 0 for r in rows)
    old_seat_wins = sum(s["submitted_margin"] > 0 for r in rows for s in r["seats"])
    new_seat_wins = sum(s["local_margin"] > 0 for r in rows for s in r["seats"])
    rescued = [r["episode_id"] for r in rows if r["submitted_pair_margin"] < 0 < r["local_pair_margin"]]
    reversed_ = [r["episode_id"] for r in rows if r["submitted_pair_margin"] > 0 > r["local_pair_margin"]]
    summary = {
        "submitted_pair_wins": old_pair_wins, "local_pair_wins": new_pair_wins,
        "submitted_seat_wins": old_seat_wins, "local_seat_wins": new_seat_wins,
        "rescued_episodes": rescued, "reversed_episodes": reversed_,
        "activated_seats": sum(s["clone_advance_turns"] > 0 for r in rows for s in r["seats"]),
        "total_advance_turns": sum(s["clone_advance_turns"] for r in rows for s in r["seats"]),
        "own_cash_delta": sum(s["own_cash_delta"] for r in rows for s in r["seats"]),
        "rival_cash_delta": sum(s["rival_cash_delta"] for r in rows for s in r["seats"]),
        "exact_original_seat_parity": "40/40 final own and rival cash, margin, DONE",
    }
    payload = {"submitted_sha256": backup["candidate_sha256"],
               "local_sha256": local["candidate_sha256"], "summary": summary, "rows": rows}
    (HERE / "live40_comparison.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("changed episodes", [(r["episode_id"], r["team"],
                              r["submitted_pair_margin"], r["local_pair_margin"])
                             for r in rows if r["submitted_pair_margin"] != r["local_pair_margin"]])


if __name__ == "__main__":
    main()
