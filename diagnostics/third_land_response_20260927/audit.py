"""Read-only audit of day-10 live land commitments and route compatibility."""

from collections import Counter
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import main  # The submitted local source; never downloaded opponent code.

HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "diagnostics/new_live_56609430_20260927"
CASES = json.loads((SOURCE / "structural_audit/bundle_cases.json").read_text(encoding="utf8"))["cases"]
COHORT = json.loads((SOURCE / "cohort_165306.json").read_text(encoding="utf8"))
GAMES = {g["episode_id"]: g for g in COHORT["games"]}
ROUTES = main._DATA["routes"]
ROUTE_MAP = main._DATA["route_map"]


def investment_signature(action):
    return sorted(tuple(order) for order in (action.get("market") or [])
                  if order and order[0] in ("HIRE", "BUY_LAND", "BUY_ANIMAL", "BUY_SEED"))


def worker_signature(action):
    return action.get("farmer"), action.get("hands")


def selected_route(shops, step):
    route = None
    for count in range(1, min(len(shops), 8) + 1):
        if step < 72 * count:
            break
        candidate = ROUTE_MAP.get("|".join(shops[:count]))
        if candidate is not None:
            route = candidate
    return str(route if route is not None else next(iter(ROUTES)))


def region_counts(farm, region):
    result = Counter()
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            if region == "SW" and not (x < 5 and y >= 5):
                continue
            name = tile.get("crop") or tile.get("animal")
            if name:
                result[name] += 1
    return dict(result)


def action_stats(steps, seat, lo, hi):
    worker = Counter()
    investments = Counter()
    orders = Counter()
    for step in range(lo, hi + 1):
        action = steps[step + 1][seat].get("action") or {}
        for unit in [action.get("farmer"), *(action.get("hands") or [])]:
            if unit:
                worker[unit[0]] += 1
        for order in action.get("market") or []:
            if not order:
                continue
            op = order[0]
            item = order[1] if len(order) > 1 else ""
            qty = order[2] if len(order) > 2 else 1
            orders[op + ":" + item] += qty
            if op in ("HIRE", "BUY_LAND", "BUY_ANIMAL", "BUY_SEED"):
                investments[op + ":" + item] += qty
    return dict(worker=worker, investments=investments, orders=orders)


def audit_case(case):
    game = GAMES[case["episode_id"]]
    steps = json.loads(gzip.decompress(Path(game["replay_path"]).read_bytes()))["steps"]
    seat = game["candidate_seat"]
    shops = case["shops"]
    chosen = selected_route(shops, 240)
    chosen_tape = ROUTES[chosen]
    observed_actions = [(steps[t + 1][seat].get("action") or {}) for t in range(240)]
    compatible_full = []
    compatible_day9 = []
    compatible_worker_day9 = []
    compatible_observed_worker_investment = []
    for route, tape in ROUTES.items():
        if tape[:240] == chosen_tape[:240]:
            compatible_full.append(route)
        if tape[216:240] == chosen_tape[216:240]:
            compatible_day9.append(route)
        if all((a["farmer"], a["hands"]) == (b["farmer"], b["hands"])
               for a, b in zip(tape[216:240], chosen_tape[216:240])):
            compatible_worker_day9.append(route)
        if all(worker_signature(tape[t]) == worker_signature(observed_actions[t])
               and investment_signature(tape[t]) == investment_signature(observed_actions[t])
               for t in range(240)):
            compatible_observed_worker_investment.append(route)
    raw_worker_matches = sum(
        (chosen_tape[t]["farmer"], chosen_tape[t]["hands"])
        == ((steps[t + 1][seat].get("action") or {}).get("farmer"),
            (steps[t + 1][seat].get("action") or {}).get("hands"))
        for t in range(216, 240)
    )
    counts = {}
    for step in (240, 241, 242, 264, 266, 288, 312, 336, 408, 719):
        obs = steps[step][seat]["observation"]
        farm = obs["farms"][seat]
        counts[str(step)] = dict(cash=farm["money"], land=len(farm["unlocked_quadrants"]),
                                 sw=region_counts(farm, "SW"))
    day_peak_hands = {}
    for day in (10, 11, 12):
        day_peak_hands[str(day)] = max(
            len(steps[t][seat]["observation"]["farms"][seat]["hands"])
            for t in range(24 * day, 24 * (day + 1))
        )
    investments = []
    for t in range(240, 289):
        action = steps[t + 1][seat].get("action") or {}
        for order in action.get("market") or []:
            if order and order[0] in ("BUY_LAND", "HIRE", "BUY_ANIMAL", "BUY_SEED"):
                investments.append(dict(step=t + 1, order=order))
    return dict(episode_id=case["episode_id"], opponent=case["opponent"], result=case["result"],
                margin=case["margin"], shops=shops, route=chosen,
                raw_worker_matches_day9=raw_worker_matches,
                compatible_full=compatible_full, compatible_day9=compatible_day9,
                compatible_worker_day9=compatible_worker_day9,
                compatible_observed_worker_investment=compatible_observed_worker_investment,
                counts=counts, day_peak_hands=day_peak_hands,
                investments=investments,
                action_stats_240_311=action_stats(steps, seat, 240, 311))


def main_audit():
    rows = [audit_case(c) for c in CASES]
    (HERE / "route_and_execution.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf8")
    for row in rows:
        print(row["episode_id"], row["result"], row["route"],
              len(row["compatible_full"]), len(row["compatible_day9"]),
              len(row["compatible_worker_day9"]), row["raw_worker_matches_day9"],
              row["counts"]["312"]["sw"],
              {k: row["action_stats_240_311"]["investments"].get(k, 0)
               for k in ("BUY_LAND:", "HIRE:")})


if __name__ == "__main__":
    main_audit()
