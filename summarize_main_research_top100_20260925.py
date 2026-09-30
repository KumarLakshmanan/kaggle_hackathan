"""Audited comparison on the archived 100-team fixed-action route panel.

This intentionally does not estimate live Kaggle rating or adapt replay
opponents to a changed policy. Every route is evaluated in both seats.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sign(value):
    return "win" if value > 0 else "loss" if value < 0 else "draw"


def _counts(values):
    result = {"wins": 0, "losses": 0, "draws": 0}
    keys = {"win": "wins", "loss": "losses", "draw": "draws"}
    for value in values:
        result[keys[_sign(value)]] += 1
    total = sum(result.values())
    return {**result, "total": total,
            "win_pct": round(100*result["wins"]/total, 3),
            "loss_pct": round(100*result["losses"]/total, 3),
            "draw_pct": round(100*result["draws"]/total, 3)}


def compare(baseline_path, candidate_path, manifest_path):
    baseline, candidate, manifest = map(_read,
                                        (baseline_path, candidate_path,
                                         manifest_path))
    manifest_hash = hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()
    for name, result in (("baseline", baseline), ("candidate", candidate)):
        if result["summary_sha256"].lower() != manifest_hash:
            raise ValueError(f"{name} was not run on this exact manifest")
        if result["unique_routes"] != 244 or len(result["rows"]) != 244:
            raise ValueError(f"{name} does not contain all 244 routes")
    by_path = {str(Path(item["path"]).resolve()): item for item in manifest}
    if len({item["team_id"] for item in manifest}) != 100:
        raise ValueError("Manifest must cover exactly 100 team IDs")
    base_routes = {group["opponent_path"]: group for group in baseline["rows"]}
    cand_routes = {group["opponent_path"]: group for group in candidate["rows"]}
    if set(base_routes) != set(cand_routes) or set(base_routes) != set(by_path):
        raise ValueError("Baseline, candidate and manifest have different routes")

    per_team = defaultdict(list)
    per_team_baseline = defaultdict(list)
    base_route_margin, cand_route_margin = [], []
    base_seat_margin, cand_seat_margin = [], []
    own_change, rival_change, activations = 0., 0., 0
    route_rescues = route_reversals = seat_rescues = seat_reversals = 0
    incomplete = []
    worst = []
    for path in sorted(by_path):
        b, c, item = base_routes[path], cand_routes[path], by_path[path]
        if (b["seed"], b["source_seat"], b["action_sha256"]) != (
                c["seed"], c["source_seat"], c["action_sha256"]):
            raise ValueError(f"Mismatched route record: {path}")
        if (int(c["seed"]), int(c["source_seat"]), c["action_sha256"]) != (
                int(item["seed"]), int(item["source_seat"]), item["action_sha256"]):
            raise ValueError(f"Mismatched manifest record: {path}")
        bg = {int(g["candidate_seat"]): g for g in b["games"]}
        cg = {int(g["candidate_seat"]): g for g in c["games"]}
        if set(bg) != {0, 1} or set(cg) != {0, 1}:
            raise ValueError(f"Route missing a candidate seat: {path}")
        bm, cm = float(b["pair_margin"]), float(c["pair_margin"])
        base_route_margin.append(bm)
        cand_route_margin.append(cm)
        per_team[int(item["team_id"])].append(cm)
        per_team_baseline[int(item["team_id"])].append(bm)
        route_rescues += bm <= 0 < cm
        route_reversals += bm > 0 >= cm
        for seat in (0, 1):
            x, y = bg[seat], cg[seat]
            for name, game in (("baseline", x), ("candidate", y)):
                if game["candidate_status"] != "DONE" or game["opponent_status"] != "DONE":
                    incomplete.append((name, path, seat,
                                       game["candidate_status"],
                                       game["opponent_status"]))
            base_seat_margin.append(float(x["margin"]))
            cand_seat_margin.append(float(y["margin"]))
            own_change += y["candidate_reward"]-x["candidate_reward"]
            rival_change += y["opponent_reward"]-x["opponent_reward"]
            activations += int(y["candidate_telemetry"].get("research_changes", 0))
            seat_rescues += x["margin"] <= 0 < y["margin"]
            seat_reversals += x["margin"] > 0 >= y["margin"]
        worst.append({"team": item["team"], "seed": item["seed"],
                      "margin_change": cm-bm,
                      "baseline_margin": bm, "candidate_margin": cm})
    if incomplete:
        raise ValueError(f"Unfinished games: {incomplete[:5]!r}")
    team_majorities = [_sign(sum(_sign(v) == "win" for v in margins)
                             - sum(_sign(v) == "loss" for v in margins))
                       for margins in per_team.values()]
    def equal_team_rate(groups, result):
        return round(100*sum(
            sum(_sign(m) == result for m in margins)/len(margins)
            for margins in groups.values())/len(groups), 3)
    return {
        "scope": "archived 2026-09-22 top-100 team fixed-action routes; not adaptive opponents",
        "teams": len(per_team), "routes": len(cand_route_margin),
        "seat_games": len(cand_seat_margin),
        "manifest_sha256": manifest_hash,
        "baseline_sha256": baseline["candidate_sha256"],
        "candidate_sha256": candidate["candidate_sha256"],
        "all_games_done": True,
        "baseline_routes": _counts(base_route_margin),
        "candidate_routes": _counts(cand_route_margin),
        "baseline_seats": _counts(base_seat_margin),
        "candidate_seats": _counts(cand_seat_margin),
        "candidate_team_route_majorities": {
            status: team_majorities.count(status)
            for status in ("win", "loss", "draw")},
        "baseline_equal_team_win_pct": equal_team_rate(per_team_baseline, "win"),
        "candidate_equal_team_win_pct": equal_team_rate(per_team, "win"),
        "candidate_equal_team_loss_pct": equal_team_rate(per_team, "loss"),
        "route_rescues": route_rescues,
        "route_reversals": route_reversals,
        "seat_rescues": seat_rescues,
        "seat_reversals": seat_reversals,
        "candidate_research_substitutions": activations,
        "aggregate_own_cash_change": own_change,
        "aggregate_rival_cash_change": rival_change,
        "aggregate_margin_change": own_change-rival_change,
        "worst_route_margin_changes": sorted(worst, key=lambda v: v["margin_change"])[:10],
        "best_route_margin_changes": sorted(worst, key=lambda v: -v["margin_change"])[:10],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    args = parser.parse_args()
    result = compare(args.baseline, args.candidate, args.manifest)
    args.json_out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "teams", "routes", "seat_games", "all_games_done",
        "baseline_routes", "candidate_routes", "baseline_seats",
        "candidate_seats", "route_rescues", "route_reversals",
        "aggregate_own_cash_change", "aggregate_margin_change")}, indent=2))
    print("wrote", args.json_out)


if __name__ == "__main__":
    main()
