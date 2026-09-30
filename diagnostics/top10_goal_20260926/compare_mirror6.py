"""Compare mirror-6, local mirror-8, and uploaded backup on matched routes."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def index(payload: dict) -> dict:
    return {
        (row["action_sha256"], int(row["seed"]), int(row["source_seat"])): row
        for row in payload["rows"]
    }


def compare(panel: str, paths: dict[str, Path]) -> dict:
    payloads = {name: load(path) for name, path in paths.items()}
    assert len({p["summary_sha256"] for p in payloads.values()}) == 1
    assert len({p["engine_version"] for p in payloads.values()}) == 1
    indexed = {name: index(p) for name, p in payloads.items()}
    keys = set(indexed["backup"])
    assert len(keys) == (100 if panel == "top100" else 40)
    assert all(set(indexed[name]) == keys for name in indexed)
    routes = []
    for key in sorted(keys):
        base = indexed["backup"][key]
        row = {"episode_id": base["episode_id"], "team": base["team"],
               "seed": base["seed"], "source_seat": base["source_seat"]}
        for name in ("backup", "mirror8", "mirror6"):
            trial = indexed[name][key]
            assert trial["opponent_path"] == base["opponent_path"]
            games = {int(g["candidate_seat"]): g for g in trial["games"]}
            assert set(games) == {0, 1}
            assert all(g["candidate_status"] == g["opponent_status"] == "DONE"
                       for g in games.values())
            row[name] = {
                "pair_margin": sum(g["margin"] for g in games.values()),
                "seat_wins": sum(g["margin"] > 0 for g in games.values()),
                "own_cash": sum(g["candidate_reward"] for g in games.values()),
                "rival_cash": sum(g["opponent_reward"] for g in games.values()),
                "advance_turns": sum(g["candidate_telemetry"].get("clone_gate_adv_turns", 0)
                                     for g in games.values()),
                "activated_seats": sum(g["candidate_telemetry"].get("clone_gate_adv_turns", 0) > 0
                                       for g in games.values()),
            }
        routes.append(row)
    summary = {}
    for name in ("backup", "mirror8", "mirror6"):
        summary[name] = {
            "paired_wins": sum(r[name]["pair_margin"] > 0 for r in routes),
            "seat_wins": sum(r[name]["seat_wins"] for r in routes),
            "own_cash_sum": sum(r[name]["own_cash"] for r in routes),
            "rival_cash_sum": sum(r[name]["rival_cash"] for r in routes),
            "advance_turns": sum(r[name]["advance_turns"] for r in routes),
            "activated_seats": sum(r[name]["activated_seats"] for r in routes),
        }
    for baseline in ("backup", "mirror8"):
        summary[f"mirror6_vs_{baseline}"] = {
            "rescues": [(r["team"], r["episode_id"])
                        for r in routes if r[baseline]["pair_margin"] <= 0 < r["mirror6"]["pair_margin"]],
            "reversals": [(r["team"], r["episode_id"])
                          for r in routes if r["mirror6"]["pair_margin"] <= 0 < r[baseline]["pair_margin"]],
            "own_cash_delta": sum(r["mirror6"]["own_cash"] - r[baseline]["own_cash"]
                                  for r in routes),
            "rival_cash_delta": sum(r["mirror6"]["rival_cash"] - r[baseline]["rival_cash"]
                                    for r in routes),
        }
    result = {"panel": panel, "hashes": {name: p["candidate_sha256"]
                                            for name, p in payloads.items()},
              "summary_sha256": payloads["backup"]["summary_sha256"],
              "summary": summary, "routes": routes}
    dest = HERE / f"mirror6_{panel}_comparison.json"
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(panel, json.dumps(summary, indent=2, ensure_ascii=False), dest, sep="\n")
    return result


def main() -> None:
    selection = set(sys.argv[1:]) or {"live40", "top100"}
    assert selection <= {"live40", "top100"}
    if "live40" in selection:
        compare("live40", {
            "backup": ROOT / "diagnostics/live_refresh_56530281_20260926/submitted_backup_40routes.json",
            "mirror8": ROOT / "diagnostics/live_refresh_56530281_20260926/main_local_40routes.json",
            "mirror6": ROOT / "diagnostics/live_refresh_56530281_20260926/mirror6_40routes.json",
        })
    if "top100" in selection:
        compare("top100", {
            "backup": ROOT / "diagnostics/top100_current_2026-09-25/main_100routes.json",
            "mirror8": HERE / "clonegated_top100_routes.json",
            "mirror6": HERE / "mirror6_top100_routes.json",
        })


if __name__ == "__main__":
    main()
