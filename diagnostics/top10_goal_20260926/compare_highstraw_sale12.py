"""Compare the isolated high-straw sale screen to exact current-main controls."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "diagnostics/top100_refresh_2026-09-26/mirror12_100routes.json"
TRIAL = Path(__file__).with_name("highstraw_sale12_losses31.json")
CAPTURE = ROOT / "diagnostics/top100_refresh_2026-09-26/losses_31_capture144.json"
OUT = Path(__file__).with_name("highstraw_sale12_comparison.json")

base = json.loads(BASE.read_text(encoding="utf8"))
trial = json.loads(TRIAL.read_text(encoding="utf8"))
capture = json.loads(CAPTURE.read_text(encoding="utf8"))
assert base["candidate_sha256"] == "0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a"
assert trial["candidate_sha256"] == "1f604b1bb56e9d56996b07fb268430bb1cc921a825b9d37efb7c51cb0a5b2a50"
assert trial["summary"]["all_done"] and len(trial["rows"]) == 31
by_hash = {row["action_sha256"]: row for row in base["rows"]}
by_cap = {row["action_sha256"]: row for row in capture["rows"]}
rows = []
for new in trial["rows"]:
    old = by_hash[new["action_sha256"]]
    cap = by_cap[new["action_sha256"]]
    assert (old["seed"], old["team"], old["source_seat"]) == (
        new["seed"], new["team"], new["source_seat"])
    old_games = {game["candidate_seat"]: game for game in old["games"]}
    new_games = {game["candidate_seat"]: game for game in new["games"]}
    assert old_games.keys() == new_games.keys() == {0, 1}
    cap0 = next(game["candidate_capture"] for game in cap["games"]
                if game["candidate_seat"] == 0)
    rival_straw = cap0["farms"][1]["counts"].get("STRAWBERRY", 0)
    own_straw = cap0["farms"][0]["counts"].get("STRAWBERRY", 0)
    seat_rows = []
    for seat in (0, 1):
        x, y = old_games[seat], new_games[seat]
        assert x["candidate_status"] == x["opponent_status"] == "DONE"
        assert y["candidate_status"] == y["opponent_status"] == "DONE"
        seat_rows.append({
            "seat": seat,
            "old_margin": x["margin"], "new_margin": y["margin"],
            "own_cash_delta": y["candidate_reward"] - x["candidate_reward"],
            "rival_cash_delta": y["opponent_reward"] - x["opponent_reward"],
        })
    rows.append({
        "team": new["team"], "action_sha256": new["action_sha256"],
        "rival_strawberries_day6": rival_straw,
        "own_strawberries_day6": own_straw,
        "gate_expected": rival_straw >= 7 and rival_straw - own_straw >= 3,
        "old_pair_margin": old["pair_margin"],
        "new_pair_margin": new["pair_margin"],
        "pair_margin_delta": new["pair_margin"] - old["pair_margin"],
        "games": seat_rows,
    })

summary = {
    "routes": len(rows),
    "gate_expected_routes": sum(r["gate_expected"] for r in rows),
    "changed_routes": sum(r["pair_margin_delta"] != 0 for r in rows),
    "rescues": sum(r["old_pair_margin"] <= 0 < r["new_pair_margin"] for r in rows),
    "margin_delta": sum(r["pair_margin_delta"] for r in rows),
    "own_cash_delta": sum(g["own_cash_delta"] for r in rows for g in r["games"]),
    "rival_cash_delta": sum(g["rival_cash_delta"] for r in rows for g in r["games"]),
    "worst": sorted(rows, key=lambda r: r["pair_margin_delta"])[0]["team"],
    "best": sorted(rows, key=lambda r: r["pair_margin_delta"])[-1]["team"],
}
OUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2,
                          ensure_ascii=False), encoding="utf8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
print(OUT)
