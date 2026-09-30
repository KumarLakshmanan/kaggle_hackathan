"""Evaluate the frozen day-16 tomato development gate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PANEL = ROOT / "diagnostics/top100_refresh_2026-09-26_0708"
META = HERE / "early_tomato16_panel20_meta.json"
BASE = HERE / "early_tomato16_baseline_capture20.json"
CANDIDATE = HERE / "early_tomato16_candidate20.json"
OUTPUT = HERE / "early_tomato16_comparison.json"


def keyed_games(panel: dict) -> dict[tuple[str, int, int, int], dict]:
    return {(row["action_sha256"], int(row["seed"]), int(row["source_seat"]),
             int(game["candidate_seat"])): game
            for row in panel["rows"] for game in row["games"]}


def main() -> None:
    meta = json.loads(META.read_text(encoding="utf8"))
    base = json.loads(BASE.read_text(encoding="utf8"))
    trial = json.loads(CANDIDATE.read_text(encoding="utf8"))
    full = json.loads((PANEL / "main_100routes.json").read_text(encoding="utf8"))
    old_games = keyed_games(base)
    new_games = keyed_games(trial)
    full_games = keyed_games(full)
    assert set(old_games) == set(new_games) and len(old_games) == 40
    for key, game in old_games.items():
        assert (game["candidate_reward"], game["opponent_reward"]) == (
            full_games[key]["candidate_reward"], full_games[key]["opponent_reward"]), key
    classes = {row["action_sha256"]: "target" for row in meta["targets"]}
    classes.update({row["action_sha256"]: "control" for row in meta["controls"]})
    rows = []
    for source in base["rows"]:
        identity = (source["action_sha256"], int(source["seed"]),
                    int(source["source_seat"]))
        controls = [old_games[identity + (seat,)] for seat in (0, 1)]
        candidates = [new_games[identity + (seat,)] for seat in (0, 1)]
        assert all(row["candidate_status"] == row["opponent_status"] == "DONE"
                   for row in controls + candidates)
        telemetry = [row.get("candidate_telemetry") or {} for row in candidates]
        rows.append({
            "team": source["team"], "action_sha256": source["action_sha256"],
            "screen_class": classes[source["action_sha256"]],
            "baseline_pair_margin": sum(row["margin"] for row in controls),
            "candidate_pair_margin": sum(row["margin"] for row in candidates),
            "pair_margin_delta": sum(row["margin"] for row in candidates)
                                 - sum(row["margin"] for row in controls),
            "own_cash_delta": sum(row["candidate_reward"] for row in candidates)
                              - sum(row["candidate_reward"] for row in controls),
            "rival_cash_delta": sum(row["opponent_reward"] for row in candidates)
                                - sum(row["opponent_reward"] for row in controls),
            "activated_seats": sum(t.get("v219_commitments", 0) > 0 for t in telemetry),
            "confirmed_plants": sum(t.get("v219_confirmed_plants", 0) for t in telemetry),
            "confirmed_harvest_units": sum(t.get("v219_confirmed_harvest_units", 0)
                                           for t in telemetry),
            "tomato_sale_requests": sum(t.get("v219_tomato_sale_requests", 0)
                                        for t in telemetry),
            "errors": sum(value for t in telemetry for key, value in t.items()
                          if key.endswith("errors") and isinstance(value, (int, float))),
            "max_call_ms": max(row["candidate_timing"]["max_ms"] for row in candidates),
            "seat_margins": {str(seat): [controls[seat]["margin"],
                                         candidates[seat]["margin"]] for seat in (0, 1)},
        })
    targets = [row for row in rows if row["screen_class"] == "target"]
    controls = [row for row in rows if row["screen_class"] == "control"]
    active = [row for row in rows if row["activated_seats"]]
    summary = {
        "targets": len(targets), "controls": len(controls),
        "activated_target_routes": sum(bool(row["activated_seats"]) for row in targets),
        "activated_control_routes": sum(bool(row["activated_seats"]) for row in controls),
        "target_rescues": sum(row["baseline_pair_margin"] < 0
                              and row["candidate_pair_margin"] > 0 for row in targets),
        "control_reversals": sum(row["candidate_pair_margin"] <= 0 for row in controls),
        "active_own_cash_delta": sum(row["own_cash_delta"] for row in active),
        "active_rival_cash_delta": sum(row["rival_cash_delta"] for row in active),
        "active_pair_margin_delta": sum(row["pair_margin_delta"] for row in active),
        "confirmed_plants": sum(row["confirmed_plants"] for row in active),
        "confirmed_harvest_units": sum(row["confirmed_harvest_units"] for row in active),
        "tomato_sale_requests": sum(row["tomato_sale_requests"] for row in active),
        "error_count": sum(row["errors"] for row in rows),
        "max_call_ms": max(row["max_call_ms"] for row in rows),
    }
    summary["fixed_route_gate_passed_except_sale_execution"] = (
        summary["activated_target_routes"] >= 3 and summary["target_rescues"] >= 2
        and summary["control_reversals"] == 0 and summary["active_own_cash_delta"] > 0
        and summary["active_pair_margin_delta"] > 0 and summary["error_count"] == 0
        and summary["confirmed_plants"] > 0 and summary["tomato_sale_requests"] > 0)
    OUTPUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2,
                                 ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2))
    for row in rows:
        if row["activated_seats"]:
            print(row["screen_class"], row["team"],
                  row["baseline_pair_margin"], row["candidate_pair_margin"],
                  "own", row["own_cash_delta"], "rival", row["rival_cash_delta"],
                  "plants", row["confirmed_plants"])
    print(OUTPUT)


if __name__ == "__main__":
    main()
