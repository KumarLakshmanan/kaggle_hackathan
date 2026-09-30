"""Compare strawberry-only lookahead on the mirror-eligible saved routes."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PANELS = (
    ("sep25", HERE / "mirror12_top100_old_routes.json"),
    ("sep26", ROOT / "diagnostics/top100_refresh_2026-09-26/main_local_100routes.json"),
)


def key(row):
    return row["action_sha256"], int(row["seed"]), int(row["source_seat"])


def verdict(margin):
    return "win" if margin > 0 else "loss" if margin < 0 else "draw"


def main():
    results = {}
    for label, baseline_path in PANELS:
        baseline = json.loads(baseline_path.read_text(encoding="utf8"))
        candidate = json.loads((HERE / f"mirror_straw24_{label}_eligible_results.json")
                               .read_text(encoding="utf8"))
        base = {key(row): row for row in baseline["rows"]}
        changed = []
        own_delta = rival_delta = margin_delta = 0.0
        rescues = reversals = 0
        seat_rescues = seat_reversals = 0
        for row in candidate["rows"]:
            prior = base[key(row)]
            old_games = {int(g["candidate_seat"]): g for g in prior["games"]}
            new_games = {int(g["candidate_seat"]): g for g in row["games"]}
            assert set(old_games) == set(new_games) == {0, 1}
            old_pair = sum(g["margin"] for g in old_games.values())
            new_pair = sum(g["margin"] for g in new_games.values())
            rescues += old_pair <= 0 < new_pair
            reversals += old_pair > 0 >= new_pair
            details = []
            for seat in (0, 1):
                old, new = old_games[seat], new_games[seat]
                assert old["candidate_status"] == old["opponent_status"] == "DONE"
                assert new["candidate_status"] == new["opponent_status"] == "DONE"
                od = new["candidate_reward"] - old["candidate_reward"]
                rd = new["opponent_reward"] - old["opponent_reward"]
                md = new["margin"] - old["margin"]
                assert od - rd == md
                own_delta += od
                rival_delta += rd
                margin_delta += md
                seat_rescues += old["margin"] <= 0 < new["margin"]
                seat_reversals += old["margin"] > 0 >= new["margin"]
                details.append({"seat": seat, "old_margin": old["margin"],
                                "new_margin": new["margin"], "own_delta": od,
                                "rival_delta": rd})
            if new_pair != old_pair:
                changed.append({"team": row["team"], "episode_id": row["episode_id"],
                                "old_pair_margin": old_pair, "new_pair_margin": new_pair,
                                "games": details})
        results[label] = {
            "baseline_full_routes": len(baseline["rows"]),
            "eligible_routes": len(candidate["rows"]),
            "changed_routes": len(changed), "rescues": rescues,
            "reversals": reversals, "seat_rescues": seat_rescues,
            "seat_reversals": seat_reversals, "own_cash_delta": own_delta,
            "rival_cash_delta": rival_delta, "margin_delta": margin_delta,
            "changed": changed,
        }
        print(label, {k: v for k, v in results[label].items() if k != "changed"})
    output = HERE / "mirror_straw24_panel_comparison.json"
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False),
                      encoding="utf8")
    print(output)


if __name__ == "__main__":
    main()
