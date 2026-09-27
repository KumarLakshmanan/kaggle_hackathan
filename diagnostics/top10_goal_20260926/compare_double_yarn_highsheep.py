"""Exact-key comparison of the gated route-12 pilot with fresh baseline routes."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "diagnostics" / "top100_refresh_2026-09-26_0708" / "main_100routes.json"
CAND = HERE / "double_yarn_highsheep_4routes.json"
OUTPUT = HERE / "double_yarn_highsheep_comparison.json"


def main():
    base = json.loads(BASE.read_text(encoding="utf8"))
    cand = json.loads(CAND.read_text(encoding="utf8"))
    baseline = {str(Path(row["opponent_path"]).resolve()): row for row in base["rows"]}
    rows = []
    for treatment in cand["rows"]:
        before = baseline[str(Path(treatment["opponent_path"]).resolve())]
        old = {g["candidate_seat"]: g for g in before["games"]}
        new = {g["candidate_seat"]: g for g in treatment["games"]}
        assert old.keys() == new.keys() == {0, 1}
        games = []
        for seat in (0, 1):
            first, second = old[seat], new[seat]
            assert first["candidate_status"] == first["opponent_status"] == "DONE"
            assert second["candidate_status"] == second["opponent_status"] == "DONE"
            games.append({"seat": seat, "old_margin": first["margin"],
                          "new_margin": second["margin"],
                          "own_delta": second["candidate_reward"]-first["candidate_reward"],
                          "rival_delta": second["opponent_reward"]-first["opponent_reward"],
                          "gate_selected": second["candidate_telemetry"].get("dyhs_selected"),
                          "gate_errors": second["candidate_telemetry"].get("dyhs_errors")})
        rows.append({"team": treatment["team"],
                     "old_paired_margin": sum(g["old_margin"] for g in games),
                     "new_paired_margin": sum(g["new_margin"] for g in games),
                     "games": games})
    rows.sort(key=lambda x: x["team"])
    OUTPUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    for row in rows:
        print(row["team"], row["old_paired_margin"], row["new_paired_margin"],
              [(g["seat"], g["own_delta"], g["rival_delta"], g["gate_selected"], g["gate_errors"])
               for g in row["games"]])


if __name__ == "__main__":
    main()
