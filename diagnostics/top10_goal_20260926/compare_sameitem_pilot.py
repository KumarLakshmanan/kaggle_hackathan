"""Compare the same-item unprotect pilot with exact matched mirror-8 rows."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "diagnostics/live_refresh_56530281_20260926"


def main() -> None:
    full = len(sys.argv) > 1 and sys.argv[1] == "full"
    old = json.loads((SOURCE / "main_local_40routes.json").read_text(encoding="utf8"))
    new = json.loads((HERE / ("sameitem_live40_routes.json" if full
                              else "sameitem_7routes.json")).read_text(encoding="utf8"))
    assert new["engine_version"] == old["engine_version"]
    if full:
        assert new["summary_sha256"] == old["summary_sha256"]
    indexed = {r["episode_id"]: r for r in old["rows"]}
    rows = []
    for cand in new["rows"]:
        base = indexed[cand["episode_id"]]
        assert (cand["action_sha256"], cand["seed"], cand["source_seat"]) == (
            base["action_sha256"], base["seed"], base["source_seat"])
        a = {g["candidate_seat"]: g for g in base["games"]}
        b = {g["candidate_seat"]: g for g in cand["games"]}
        assert set(a) == set(b) == {0, 1}
        assert all(g["candidate_status"] == g["opponent_status"] == "DONE" for g in b.values())
        rows.append({
            "episode_id": cand["episode_id"], "team": cand["team"],
            "baseline_pair_margin": base["pair_margin"],
            "candidate_pair_margin": cand["pair_margin"],
            "baseline_seat_wins": sum(g["margin"] > 0 for g in a.values()),
            "candidate_seat_wins": sum(g["margin"] > 0 for g in b.values()),
            "own_cash_delta": sum(b[s]["candidate_reward"] - a[s]["candidate_reward"]
                                  for s in (0, 1)),
            "rival_cash_delta": sum(b[s]["opponent_reward"] - a[s]["opponent_reward"]
                                    for s in (0, 1)),
        })
    output = HERE / ("sameitem_live40_comparison.json" if full
                     else "sameitem_7routes_comparison.json")
    output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf8")
    for row in rows:
        print(row["episode_id"], row["team"], row["baseline_pair_margin"],
              "->", row["candidate_pair_margin"], "own", row["own_cash_delta"],
              "rival", row["rival_cash_delta"])
    print("wins", sum(r["baseline_pair_margin"] > 0 for r in rows),
          "->", sum(r["candidate_pair_margin"] > 0 for r in rows),
          "seats", sum(r["baseline_seat_wins"] for r in rows),
          "->", sum(r["candidate_seat_wins"] for r in rows),
          "own", sum(r["own_cash_delta"] for r in rows),
          "rival", sum(r["rival_cash_delta"] for r in rows))
    print(output)


if __name__ == "__main__":
    main()
