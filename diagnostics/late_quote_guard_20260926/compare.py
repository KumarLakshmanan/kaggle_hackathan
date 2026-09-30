"""Apply frozen original-seat development gate to the quote60 candidate."""

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LIVE = ROOT / "diagnostics" / "live_submission_56572390_20260926" / "mirror_dev_routes" / "summary.json"
BASE = ROOT / "diagnostics" / "top10_goal_20260926" / "pure_sale_dev_baseline39.json"
TRIAL = HERE / "quote60_dev_candidate39.json"
OUTPUT = HERE / "quote60_dev_comparison.json"
SOURCE_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
TRIAL_HASH = "6c1d950191cc876755163c8df2de23d8e146a14a3ee34ab33e70098ee203c808"


def games(panel):
    return {(int(group["episode_id"]), int(game["candidate_seat"])): game
            for group in panel["rows"] for game in group["games"]}


def main():
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    base_panel = json.loads(BASE.read_text(encoding="utf-8"))
    trial_panel = json.loads(TRIAL.read_text(encoding="utf-8"))
    assert base_panel["candidate_sha256"] == SOURCE_HASH
    assert trial_panel["candidate_sha256"] == TRIAL_HASH
    assert base_panel["summary_sha256"] == trial_panel["summary_sha256"]
    base, trial = games(base_panel), games(trial_panel)
    assert len(live) == 39 and len(base) == len(trial) == 78
    rows = []
    for case in live:
        episode_id = int(case["episode_id"])
        for seat in (0, 1):
            control, candidate = base[episode_id, seat], trial[episode_id, seat]
            assert control["candidate_status"] == control["opponent_status"] == "DONE"
            assert candidate["candidate_status"] == candidate["opponent_status"] == "DONE"
            if seat == int(case["our_live_seat"]):
                assert (control["candidate_reward"], control["opponent_reward"]) == (case["our_live_cash"], case["rival_live_cash"])
            rows.append({"episode_id": episode_id, "team": case["team"], "screen_class": case["screen_class"],
                         "seat": seat, "original_seat": seat == int(case["our_live_seat"]),
                         "baseline_margin": control["margin"], "candidate_margin": candidate["margin"],
                         "margin_delta": candidate["margin"] - control["margin"],
                         "own_cash_delta": candidate["candidate_reward"] - control["candidate_reward"],
                         "rival_cash_delta": candidate["opponent_reward"] - control["opponent_reward"],
                         "candidate_errors": {key: value for key, value in (candidate.get("candidate_telemetry") or {}).items() if key.endswith("errors") and value}})
    originals = [row for row in rows if row["original_seat"]]
    losses = [row for row in originals if row["screen_class"] == "loss"]
    controls = [row for row in originals if row["screen_class"] == "win"]
    summary = {"loss_rescues": sum(row["candidate_margin"] > 0 for row in losses),
               "control_win_reversals": sum(row["candidate_margin"] <= 0 for row in controls),
               "own_cash_delta_original": sum(row["own_cash_delta"] for row in originals),
               "rival_cash_delta_original": sum(row["rival_cash_delta"] for row in originals),
               "margin_delta_original": sum(row["margin_delta"] for row in originals),
               "changed_original_seats": sum(row["margin_delta"] != 0 for row in originals),
               "candidate_error_games": sum(bool(row["candidate_errors"]) for row in rows),
               "max_candidate_call_ms": max(game["candidate_timing"]["max_ms"] for game in trial.values())}
    summary["development_gate_passed"] = (summary["loss_rescues"] >= 5 and summary["control_win_reversals"] <= 1
                                          and summary["own_cash_delta_original"] > 0 and summary["margin_delta_original"] > 0
                                          and summary["candidate_error_games"] == 0)
    OUTPUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("rescued", [(row["team"], row["candidate_margin"]) for row in losses if row["candidate_margin"] > 0])
    print("reversed", [(row["team"], row["candidate_margin"]) for row in controls if row["candidate_margin"] <= 0])


if __name__ == "__main__":
    main()
