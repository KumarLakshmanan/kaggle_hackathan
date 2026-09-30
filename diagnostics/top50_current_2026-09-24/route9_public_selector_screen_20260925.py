"""Exploratory, read-only public-state screen for the sheep-heavy route.

This is not a deployable policy.  It selects from predeclared, single-feature
predicates with whole-team leave-one-out evaluation on an already-inspected
historical fixed-action panel.  No replay identity, seed, or future shop is
ever passed to a predicate.  The resulting panel is still development data.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "main_100routes_capture144_20260925.json"
FROZEN = ROOT / "main_100routes.json"
TREATMENT = ROOT / "route_force_9_100routes_20260925.json"

SHOP_PRODUCTS = {
    "BAKERY": {"WHEAT", "EGG"},
    "PIZZA_SHOP": {"WHEAT", "MILK", "TOMATO"},
    "BRUNCH_SPOT": {"WHEAT", "EGG", "STRAWBERRY"},
    "YARN_STORE": {"WOOL"},
    "ICE_CREAM_SHOP": {"WHEAT", "MILK", "STRAWBERRY"},
    "PET_CAFE": {"CARROT"},
    "SMOOTHIE_SHOP": {"MILK", "STRAWBERRY"},
    "FARMERS_MARKET": {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY"},
}


def key(row):
    return row["action_sha256"], row["seed"], row["source_seat"]


def features(capture):
    if capture["step"] != 144:
        raise ValueError("expected day-6 public observation")
    own = capture["farms"][capture["player"]]
    rival = capture["farms"][1 - capture["player"]]
    result = {
        "own_money": own["money"],
        "rival_money": rival["money"],
        "money_gap": own["money"] - rival["money"],
        "rival_cow": rival["counts"].get("COW", 0),
        "rival_sheep": rival["counts"].get("SHEEP", 0),
        "rival_cow_minus_sheep": rival["counts"].get("COW", 0)
        - rival["counts"].get("SHEEP", 0),
        "own_cow": own["counts"].get("COW", 0),
        "own_sheep": own["counts"].get("SHEEP", 0),
        "rival_melon": rival["counts"].get("MELON", 0),
        "rival_strawberry": rival["counts"].get("STRAWBERRY", 0),
    }
    for product in ("WOOL", "MILK", "STRAWBERRY", "TOMATO", "CARROT"):
        result[f"demand_{product.lower()}"] = sum(
            product in SHOP_PRODUCTS.get(shop, set()) for shop in capture["shops"][:2]
        )
    for product in ("WOOL", "MILK", "STRAWBERRY"):
        result[f"market_{product.lower()}"] = capture["inventory"][product]
    return result


GRIDS = {
    "own_money": (250, 500, 750, 1000, 1250, 1500),
    "rival_money": (0, 250, 500, 750, 1000, 1250, 1500),
    "money_gap": (-1000, -500, -250, 0, 250, 500, 1000),
    "rival_cow": tuple(range(1, 9)),
    "rival_sheep": tuple(range(1, 9)),
    "rival_cow_minus_sheep": tuple(range(-3, 6)),
    "own_cow": tuple(range(1, 9)),
    "own_sheep": tuple(range(1, 9)),
    "rival_melon": (2, 4, 6, 8, 10, 12, 14, 16),
    "rival_strawberry": (2, 4, 6, 8, 10, 12, 14, 16),
    "demand_wool": (1, 2),
    "demand_milk": (1, 2),
    "demand_strawberry": (1, 2),
    "demand_tomato": (1, 2),
    "demand_carrot": (1, 2),
    "market_wool": (9500, 9750, 10000, 10250, 10500),
    "market_milk": (9500, 9750, 10000, 10250, 10500),
    "market_strawberry": (9500, 9750, 10000, 10250, 10500),
}
RULES = [(name, operator, threshold) for name, thresholds in GRIDS.items()
         for threshold in thresholds for operator in ("<=", ">=")]


def selects(rule, f):
    if rule is None:
        return False
    name, operator, threshold = rule
    return f[name] <= threshold if operator == "<=" else f[name] >= threshold


def outcome(route, rule):
    margins = [
        route["candidate"][seat]["margin"]
        if selects(rule, route["features"][seat])
        else route["baseline"][seat]["margin"]
        for seat in range(2)
    ]
    return sum(margins), sum(margin > 0 for margin in margins)


def score(routes, rule):
    baseline_wins = sum(sum(game["margin"] for game in route["baseline"]) > 0
                        for route in routes)
    candidate_wins = sum(outcome(route, rule)[0] > 0 for route in routes)
    reversals = sum(
        sum(game["margin"] for game in route["baseline"]) > 0
        and outcome(route, rule)[0] <= 0 for route in routes
    )
    rescues = sum(
        sum(game["margin"] for game in route["baseline"]) <= 0
        and outcome(route, rule)[0] > 0 for route in routes
    )
    triggered = sum(any(selects(rule, f) for f in route["features"])
                    for route in routes)
    teams_triggered = len({route["team"] for route in routes
                           if any(selects(rule, f) for f in route["features"])})
    return {
        "baseline_wins": baseline_wins,
        "candidate_wins": candidate_wins,
        "rescues": rescues,
        "reversals": reversals,
        "triggered_routes": triggered,
        "triggered_teams": teams_triggered,
    }


def fit(routes):
    options = []
    for rule in RULES:
        stats = score(routes, rule)
        if stats["triggered_routes"] < 6 or stats["triggered_teams"] < 3:
            continue
        if stats["rescues"] == 0:
            continue
        # Strongly penalize a newly lost route; tie-break toward less exposure.
        utility = stats["rescues"] - 3 * stats["reversals"]
        if utility > 0:
            options.append((utility, -stats["reversals"],
                            -stats["triggered_routes"], rule, stats))
    if not options:
        return None, score(routes, None)
    best = max(options)
    return best[3], best[4]


def main():
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    forced = json.loads(TREATMENT.read_text(encoding="utf-8"))
    if base["engine_version"] != forced["engine_version"]:
        raise ValueError("engine mismatch")
    if base["summary_sha256"] != forced["summary_sha256"]:
        raise ValueError("route panel mismatch")
    by_key = {key(row): row for row in forced["rows"]}
    if len(base["rows"]) != len(by_key) or len(base["rows"]) != 100:
        raise ValueError("expected the exact 100-route panel")
    frozen_by_key = {key(row): row for row in frozen["rows"]}
    if set(frozen_by_key) != {key(row) for row in base["rows"]}:
        raise ValueError("captured routes differ from the frozen incumbent")
    routes = []
    for row in base["rows"]:
        candidate = by_key[key(row)]
        b_games = sorted(row["games"], key=lambda game: game["candidate_seat"])
        c_games = sorted(candidate["games"], key=lambda game: game["candidate_seat"])
        f_games = sorted(frozen_by_key[key(row)]["games"],
                         key=lambda game: game["candidate_seat"])
        if any((b["candidate_reward"], b["opponent_reward"], b["margin"],
                b["candidate_status"], b["opponent_status"])
               != (f["candidate_reward"], f["opponent_reward"], f["margin"],
                   f["candidate_status"], f["opponent_status"])
               for b, f in zip(b_games, f_games)):
            raise ValueError(f"capture run failed to reproduce {key(row)}")
        if any(b["candidate_status"] != "DONE" or c["candidate_status"] != "DONE"
               or b["candidate_seat"] != seat or c["candidate_seat"] != seat
               or b["candidate_capture"] is None
               for seat, (b, c) in enumerate(zip(b_games, c_games))):
            raise ValueError(f"incomplete route {key(row)}")
        routes.append({
            "team": row["team"],
            "episode_id": row["episode_id"],
            "features": [features(game["candidate_capture"]) for game in b_games],
            "baseline": b_games,
            "candidate": c_games,
        })

    full_rule, full_stats = fit(routes)
    teams = sorted({route["team"] for route in routes})
    if len({(route["team"], route["episode_id"]) for route in routes}) != len(routes):
        raise ValueError("team+episode is not a unique route key")
    held_out = {}
    folds = Counter()
    for team in teams:
        training = [route for route in routes if route["team"] != team]
        rule, _ = fit(training)
        folds[str(rule)] += 1
        for route in routes:
            if route["team"] == team:
                held_out[(team, route["episode_id"])] = outcome(route, rule)
    baseline_route_wins = sum(sum(g["margin"] for g in r["baseline"]) > 0
                              for r in routes)
    oof_route_wins = sum(margin > 0 for margin, _ in held_out.values())
    baseline_seat_wins = sum(g["margin"] > 0 for r in routes for g in r["baseline"])
    oof_seat_wins = sum(wins for _, wins in held_out.values())
    print(json.dumps({
        "full_fit_rule": full_rule,
        "full_fit_stats": full_stats,
        "whole_team_leave_one_out": {
            "baseline_route_wins": baseline_route_wins,
            "selected_route_wins": oof_route_wins,
            "baseline_seat_wins": baseline_seat_wins,
            "selected_seat_wins": oof_seat_wins,
            "fit_rules_by_fold": dict(folds),
            "rescues": [(r["team"], r["episode_id"]) for r in routes
                        if sum(g["margin"] for g in r["baseline"]) <= 0
                        and held_out[(r["team"], r["episode_id"])][0] > 0],
            "reversals": [(r["team"], r["episode_id"]) for r in routes
                          if sum(g["margin"] for g in r["baseline"]) > 0
                          and held_out[(r["team"], r["episode_id"])][0] <= 0],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
