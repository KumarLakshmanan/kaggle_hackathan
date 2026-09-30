"""Audit the eight-turn sale advance against the matched top-100 incumbent."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "diagnostics" / "top100_current_2026-09-25"
OUT = Path(__file__).resolve().parent


def key(row: dict) -> tuple[str, int, int]:
    return row["action_sha256"], int(row["seed"]), int(row["source_seat"])


def main() -> None:
    stem = sys.argv[1] if len(sys.argv) > 1 else "look8"
    if stem not in {"look8", "clonegated"}:
        raise ValueError(stem)
    base = json.loads((SOURCE / "main_100routes.json").read_text(encoding="utf-8"))
    treatment = json.loads((OUT / f"{stem}_top100_routes.json").read_text(encoding="utf-8"))
    assert base["summary_sha256"] == treatment["summary_sha256"]
    assert base["engine_version"] == treatment["engine_version"]
    baseline = {key(r): r for r in base["rows"]}
    assert len(baseline) == len(treatment["rows"]) == 100
    comparisons = []
    for candidate in treatment["rows"]:
        original = baseline[key(candidate)]
        assert original["opponent_path"] == candidate["opponent_path"]
        assert [g["candidate_seat"] for g in original["games"]] == [g["candidate_seat"] for g in candidate["games"]]
        assert all(g["candidate_status"] == g["opponent_status"] == "DONE" for g in candidate["games"])
        own_delta = sum(c["candidate_reward"] - b["candidate_reward"] for b, c in zip(original["games"], candidate["games"]))
        rival_delta = sum(c["opponent_reward"] - b["opponent_reward"] for b, c in zip(original["games"], candidate["games"]))
        comparisons.append({
            "team": candidate["team"], "episode_id": candidate["episode_id"],
            "baseline_margin": original["pair_margin"], "treatment_margin": candidate["pair_margin"],
            "own_cash_delta": own_delta, "rival_cash_delta": rival_delta,
            "baseline_seat_results": [g["result"] for g in original["games"]],
            "treatment_seat_results": [g["result"] for g in candidate["games"]],
        })
    summary = {
        "routes": len(comparisons),
        "baseline_pair_wins": sum(c["baseline_margin"] > 0 for c in comparisons),
        "treatment_pair_wins": sum(c["treatment_margin"] > 0 for c in comparisons),
        "rescued_routes": sum(c["baseline_margin"] <= 0 < c["treatment_margin"] for c in comparisons),
        "reversed_routes": sum(c["treatment_margin"] <= 0 < c["baseline_margin"] for c in comparisons),
        "baseline_seat_wins": sum(r == "win" for c in comparisons for r in c["baseline_seat_results"]),
        "treatment_seat_wins": sum(r == "win" for c in comparisons for r in c["treatment_seat_results"]),
        "rescued_seats": sum(a != "win" and b == "win" for c in comparisons for a, b in zip(c["baseline_seat_results"], c["treatment_seat_results"])),
        "reversed_seats": sum(a == "win" and b != "win" for c in comparisons for a, b in zip(c["baseline_seat_results"], c["treatment_seat_results"])),
        "own_cash_delta": sum(c["own_cash_delta"] for c in comparisons),
        "rival_cash_delta": sum(c["rival_cash_delta"] for c in comparisons),
        "max_candidate_call_ms": max(g["candidate_timing"]["max_ms"] for r in treatment["rows"] for g in r["games"]),
    }
    (OUT / f"{stem}_top100_comparison.json").write_text(
        json.dumps({"summary": summary, "comparisons": comparisons}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    print("rescues")
    for c in comparisons:
        if c["baseline_margin"] <= 0 < c["treatment_margin"]:
            print(c["team"], c["episode_id"], c["baseline_margin"], c["treatment_margin"],
                  c["own_cash_delta"], c["rival_cash_delta"])
    print("reversals")
    for c in comparisons:
        if c["treatment_margin"] <= 0 < c["baseline_margin"]:
            print(c["team"], c["episode_id"], c["baseline_margin"], c["treatment_margin"],
                  c["own_cash_delta"], c["rival_cash_delta"])


if __name__ == "__main__":
    main()
