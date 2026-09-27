"""Exact-key comparison of same-item candidate and current top-100 panel."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding="utf8"))


def key(row):
    return row["action_sha256"], int(row["seed"]), int(row["source_seat"])


def main():
    old = load(HERE / "clonegated_top100_routes.json")
    new = load(HERE / "sameitem_top100_routes.json")
    assert old["summary_sha256"] == new["summary_sha256"]
    assert old["engine_version"] == new["engine_version"]
    baseline = {key(row): row for row in old["rows"]}
    assert len(baseline) == len(new["rows"]) == 100
    rows = []
    for candidate in new["rows"]:
        previous = baseline[key(candidate)]
        assert previous["opponent_path"] == candidate["opponent_path"]
        a = {game["candidate_seat"]: game for game in previous["games"]}
        b = {game["candidate_seat"]: game for game in candidate["games"]}
        assert set(a) == set(b) == {0, 1}
        assert all(g["candidate_status"] == g["opponent_status"] == "DONE"
                   for g in b.values())
        rows.append({
            "team": candidate["team"], "episode_id": candidate["episode_id"],
            "seed": candidate["seed"], "source_seat": candidate["source_seat"],
            "baseline_pair_margin": previous["pair_margin"],
            "candidate_pair_margin": candidate["pair_margin"],
            "baseline_seat_wins": sum(g["margin"] > 0 for g in a.values()),
            "candidate_seat_wins": sum(g["margin"] > 0 for g in b.values()),
            "own_cash_delta": sum(b[s]["candidate_reward"] - a[s]["candidate_reward"]
                                  for s in (0, 1)),
            "rival_cash_delta": sum(b[s]["opponent_reward"] - a[s]["opponent_reward"]
                                    for s in (0, 1)),
        })
    summary = {
        "baseline_paired_wins": sum(r["baseline_pair_margin"] > 0 for r in rows),
        "candidate_paired_wins": sum(r["candidate_pair_margin"] > 0 for r in rows),
        "baseline_seat_wins": sum(r["baseline_seat_wins"] for r in rows),
        "candidate_seat_wins": sum(r["candidate_seat_wins"] for r in rows),
        "own_cash_delta": sum(r["own_cash_delta"] for r in rows),
        "rival_cash_delta": sum(r["rival_cash_delta"] for r in rows),
        "rescues": [(r["team"], r["episode_id"])
                    for r in rows if r["baseline_pair_margin"] <= 0
                    < r["candidate_pair_margin"]],
        "reversals": [(r["team"], r["episode_id"])
                      for r in rows if r["candidate_pair_margin"] <= 0
                      < r["baseline_pair_margin"]],
    }
    dest = HERE / "sameitem_top100_comparison.json"
    dest.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2,
                               ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(dest)


if __name__ == "__main__":
    main()
