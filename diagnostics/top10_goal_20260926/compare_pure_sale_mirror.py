"""Evaluate the predeclared original-seat fixed-route development gate."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_submission_56572390_20260926" / "mirror_dev_routes" / "summary.json"
BASE = HERE / "pure_sale_dev_baseline39.json"
CANDIDATE = HERE / "pure_sale_dev_candidate39.json"
OUTPUT = HERE / "pure_sale_dev_comparison.json"


def games(path: Path) -> dict[tuple[int, int], dict]:
    panel = json.loads(path.read_text(encoding="utf8"))
    return {(int(group["episode_id"]), int(game["candidate_seat"])): game
            for group in panel["rows"] for game in group["games"]}


def main() -> None:
    live = json.loads(LIVE.read_text(encoding="utf8"))
    base = games(BASE)
    treatment = games(CANDIDATE)
    assert len(live) == 39 and len(base) == len(treatment) == 78
    rows = []
    for case in live:
        episode_id = int(case["episode_id"])
        for seat in (0, 1):
            control = base[episode_id, seat]
            trial = treatment[episode_id, seat]
            assert control["candidate_status"] == control["opponent_status"] == "DONE"
            assert trial["candidate_status"] == trial["opponent_status"] == "DONE"
            if seat == int(case["our_live_seat"]):
                assert (control["candidate_reward"], control["opponent_reward"]) == (
                    case["our_live_cash"], case["rival_live_cash"]), episode_id
            rows.append({
                "episode_id": episode_id, "team": case["team"],
                "screen_class": case["screen_class"], "seat": seat,
                "original_seat": seat == int(case["our_live_seat"]),
                "control_margin": control["margin"],
                "candidate_margin": trial["margin"],
                "margin_delta": trial["margin"] - control["margin"],
                "own_cash_delta": trial["candidate_reward"] - control["candidate_reward"],
                "rival_cash_delta": trial["opponent_reward"] - control["opponent_reward"],
                "max_candidate_call_ms": trial["candidate_timing"]["max_ms"],
                "candidate_errors": {key: value for key, value in
                                     (trial.get("candidate_telemetry") or {}).items()
                                     if key.endswith("errors") and value},
            })
    originals = [row for row in rows if row["original_seat"]]
    losses = [row for row in originals if row["screen_class"] == "loss"]
    controls = [row for row in originals if row["screen_class"] == "win"]
    summary = {
        "loss_rescues": sum(row["candidate_margin"] > 0 for row in losses),
        "control_win_reversals": sum(row["candidate_margin"] <= 0 for row in controls),
        "own_cash_delta_original": sum(row["own_cash_delta"] for row in originals),
        "rival_cash_delta_original": sum(row["rival_cash_delta"] for row in originals),
        "margin_delta_original": sum(row["margin_delta"] for row in originals),
        "changed_original_seats": sum(row["margin_delta"] != 0 for row in originals),
        "paired_positive_routes": sum(
            sum(row["margin_delta"] for row in rows if row["episode_id"] == case["episode_id"]) > 0
            for case in live),
        "max_candidate_call_ms": max(row["max_candidate_call_ms"] for row in rows),
        "candidate_error_games": sum(bool(row["candidate_errors"]) for row in rows),
    }
    summary["development_gate_passed"] = (
        summary["loss_rescues"] >= 5 and summary["control_win_reversals"] <= 1
        and summary["own_cash_delta_original"] > 0 and summary["candidate_error_games"] == 0)
    OUTPUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2,
                                 ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2))
    print("rescued:", [(row["episode_id"], row["team"], row["candidate_margin"])
                       for row in losses if row["candidate_margin"] > 0])
    print("reversed controls:", [(row["episode_id"], row["team"], row["candidate_margin"])
                                  for row in controls if row["candidate_margin"] <= 0])
    print(OUTPUT)


if __name__ == "__main__":
    main()
