"""Deterministic sidecar diagnostics for the 2026-09-24 top-50 replay panel.

Run from the repository root:
    python -X utf8 diagnostics/top50_current_2026-09-24/loss_cluster_sidecar_20260924.py

Default, --markdown, --preselect-ledger-panel, and --summarize-ledger are read-only.
--ledger-study runs the 24 preselected native games and writes one compact gzip
artifact; it refuses to overwrite an existing artifact. --trace invokes one
specified local simulation in memory without writing a trace file. Tape counts
are *attempted* commands, not successful transactions in the new matchup.
"""

from __future__ import annotations

from collections import Counter
from collections import defaultdict
import argparse
import concurrent.futures
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean, median
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FROZEN_MAIN_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
ANIMAL_PRODUCTS = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_route(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def tape_features(actions: list[dict]) -> dict:
    market = Counter()
    items = Counter()
    field = Counter()
    for action in actions:
        for order in action.get("market", []):
            if order:
                market[order[0]] += 1
                if len(order) >= 3 and order[0] in ("SELL", "BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"):
                    items[(order[0], order[1])] += max(0, int(order[2]))
        for command in [action.get("farmer", []), *action.get("hands", [])]:
            if command:
                field[command[0]] += 1
                if len(command) >= 2 and command[0] == "PLANT":
                    items[("PLANT", command[1])] += 1
    return {
        "market": market,
        "items": items,
        "field": field,
        "sell_intent": sum(q for (op, _), q in items.items() if op == "SELL"),
        "harvest_intent": field["HARVEST"],
        "plant_intent": field["PLANT"],
        "care_intent": field["CARE"] + field["FEED"],
    }


def panel() -> tuple[list[dict], dict]:
    benchmark_path = HERE / "main_100routes.json"
    summary_path = HERE / "routes" / "summary.json"
    benchmark = load_json(benchmark_path)
    manifest = load_json(summary_path)
    leaderboard = load_json(HERE / "routes" / "leaderboard_snapshot.json")
    assert isinstance(benchmark, dict) and isinstance(manifest, list)
    assert isinstance(leaderboard, list)
    assert hashlib.sha256(summary_path.read_bytes()).hexdigest() == benchmark["summary_sha256"]
    assert benchmark["candidate_sha256"] == FROZEN_MAIN_SHA256
    assert benchmark["engine_version"] == "1.32.7"
    assert len(manifest) == len(benchmark["rows"]) == 100
    rank_by_team_id = {int(item["teamId"]): int(item["rank"]) for item in leaderboard}
    source_by_path = {Path(item["path"]).name: item for item in manifest}
    rows = []
    for row in benchmark["rows"]:
        route_path = HERE / "routes" / Path(row["opponent_path"]).name
        source = source_by_path[route_path.name]
        assert source["action_sha256"] == row["action_sha256"]
        tape = load_route(route_path)
        assert len(tape["actions"]) == source["num_actions"] == 719
        actual_hash = hashlib.sha256(
            json.dumps(tape["actions"], sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert actual_hash == source["action_sha256"] == tape["metadata"]["action_sha256"]
        games = row["games"]
        assert len(games) == 2
        assert {g["candidate_seat"] for g in games} == {0, 1}
        assert sum(g["margin"] for g in games) == row["pair_margin"]
        rows.append({
            "rank": rank_by_team_id[int(source["team_id"])],
            "team": source["team"],
            "episode": source["episode_id"],
            "seed": source["seed"],
            "source_seat": source["source_seat"],
            "file": route_path.name,
            "source_reward": tape["metadata"].get("team_reward"),
            "ours": mean(g["candidate_reward"] for g in games),
            "theirs": mean(g["opponent_reward"] for g in games),
            "margin": row["pair_margin"] / 2,
            "seat_margins": [g["margin"] for g in games],
            "seat_ours": [g["candidate_reward"] for g in games],
            "seat_theirs": [g["opponent_reward"] for g in games],
            "tape": tape_features(tape["actions"]),
        })
    assert len({r["file"] for r in rows}) == 100
    assert sum(r["margin"] < 0 for r in rows) == 33
    assert len({r["team"] for r in rows}) == 50
    return rows, benchmark


def stratum(row: dict, own_mid: float, rival_mid: float) -> str:
    if row["ours"] < own_mid and row["theirs"] > rival_mid:
        return "both"
    if row["ours"] < own_mid:
        return "own-low"
    return "rival-high"


def ledger_panel(rows: list[dict]) -> list[tuple[str, dict, dict | None]]:
    """Preselect six double-loss routes and six distinct-team winning controls.

    Controls are greedily matched within the same leaderboard decile by
    source-episode cash, rank, and source seat. Exclude obvious fixed-tape cash
    collapses/spikes (>25k change in public opponent cash versus source); this
    uses only the frozen benchmark, not new traces or hidden inventory.
    The selected list is for *future diagnosis*, not a policy routing table.
    """
    target_teams = {"Excluding", "Boey", "ActiveMusyoku"}
    targets = sorted((r for r in rows if r["team"] in target_teams),
                     key=lambda r: (r["rank"], r["episode"]))
    assert len(targets) == 6 and all(r["margin"] < 0 for r in targets)
    selected = [("loss", row, None) for row in targets]
    used_teams = set(target_teams)
    used_episodes = {r["episode"] for r in targets}
    for target in targets:
        decile = (target["rank"] - 1) // 10
        pool = [r for r in rows
                if all(margin > 0 for margin in r["seat_margins"])
                and (r["rank"] - 1) // 10 == decile
                and r["team"] not in used_teams
                and r["episode"] not in used_episodes
                and abs(r["theirs"] - r["source_reward"]) <= 25000]
        if not pool:
            raise ValueError(f"No distinct winning control for {target['file']}")
        control = min(pool, key=lambda r: (
            abs(r["source_reward"] - target["source_reward"])
            + 2000 * abs(r["rank"] - target["rank"])
            + 5000 * (r["source_seat"] != target["source_seat"]),
            abs(r["source_reward"] - target["source_reward"]),
            abs(r["rank"] - target["rank"]), r["file"],
        ))
        used_teams.add(control["team"])
        used_episodes.add(control["episode"])
        selected.append(("win-control", control, target))
    assert len(selected) == 12 and len({r["file"] for _, r, _ in selected}) == 12
    assert len({r["episode"] for _, r, _ in selected}) == 12
    return selected


def public_farm_capacity(farm: dict) -> dict:
    """Count only tiles visible in the shared farm observation."""
    plants = Counter()
    animals = Counter()
    for line in farm.get("tiles", []):
        for tile in line:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                plants[tile.get("crop")] += 1
            if tile.get("animal"):
                animals[tile["animal"]] += 1
    return {"plants": dict(plants), "animals": dict(animals),
            "land": len(farm.get("unlocked_quadrants", []))}


def public_farm_daily(farm: dict) -> dict:
    """Aggregate an observation's public plant/animal cohorts; no private state."""
    plants = Counter()
    animals = Counter()
    ripe = Counter()
    for line in farm.get("tiles", []):
        for tile in line:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                crop = str(tile["crop"])
                plants[(crop, int(tile.get("planted_day", -1)))] += 1
                ripe[crop] += int(tile.get("yield_units", 0) or 0)
            elif tile.get("animal"):
                animal = str(tile["animal"])
                animals[(animal, int(tile.get("placed_day", -1)))] += 1
                ripe[ANIMAL_PRODUCTS.get(animal, animal)] += int(tile.get("yield_units", 0) or 0)
    return {
        "plants": {f"{crop}@{day}": count for (crop, day), count in sorted(plants.items())},
        "animals": {f"{animal}@{day}": count for (animal, day), count in sorted(animals.items())},
        "visible_yield_units": dict(sorted(ripe.items())),
        "land": len(farm.get("unlocked_quadrants", [])),
    }


def _unit_context(frame: dict, actor: int) -> tuple[dict, dict | None]:
    """Resolve one own actor's visible tile before an executed unit action."""
    obs = frame["observation"]
    farm = obs["farms"][frame["player"]]
    hands = farm.get("hands", [])
    position = farm.get("farmer") if actor == 0 else hands[actor - 1] if actor - 1 < len(hands) else None
    if position is None:
        return farm, None
    x, y = map(int, position)
    tile = farm["tiles"][y][x]
    return farm, tile if isinstance(tile, dict) else None


def _ledger_worker(job: tuple[str, dict, int | None, int]) -> dict:
    """Run one native game and return bounded own/public aggregates only."""
    role, row, target_episode, seat = job
    sys.path.insert(0, str(ROOT))
    from trace_paired_game_events import run

    trace = run(str(ROOT / "main.py"), "rawroute:" + str(HERE / "routes" / row["file"]),
                int(row["seed"]), seat)
    assert trace["engine_version"] == "1.32.7"
    assert trace["candidate_status"] == trace["opponent_status"] == "DONE"
    assert trace["candidate_reward"] == row["seat_ours"][seat]
    assert trace["opponent_reward"] == row["seat_theirs"][seat]
    assert trace["margin"] == row["seat_margins"][seat]
    turns = {int(turn["step"]): turn for turn in trace["turns"] if int(turn["step"]) >= 0}
    frames = {int(frame["step"]): frame for frame in trace["traces"][seat]}
    assert set(turns) == set(frames) == set(range(719))
    events_by_day = defaultdict(list)
    for event in trace["events"]:
        step = event.get("step")
        if event.get("player") == seat and isinstance(step, int) and 0 <= step <= 718:
            events_by_day[step // 24].append(event)

    daily = []
    totals_cash = Counter()
    totals_units = Counter()
    totals_cost = Counter()
    totals_harvest = Counter()
    totals_confirmed = Counter()
    totals_requested = Counter()
    first_commitment = {}
    for day in range(30):
        first_step = day * 24
        last_step = min(first_step + 23, 718)
        opening = float(turns[first_step]["players_before"][seat]["cash"])
        closing = float(turns[last_step]["players_after"][seat]["cash"])
        obs = frames[first_step]["observation"]
        own_farm, rival_farm = obs["farms"][seat], obs["farms"][1 - seat]
        receipts_cash, receipts_units = Counter(), Counter()
        costs, harvest, confirmed, requested = Counter(), Counter(), Counter(), Counter()
        for step in range(first_step, last_step + 1):
            action = frames[step]["action"]
            for command in [action.get("farmer", []), *action.get("hands", [])]:
                if command and command[0] in ("PLANT", "PLACE", "WATER", "FEED", "CARE", "HARVEST", "DROP", "FERTILIZE"):
                    key = str(command[0]) + (":" + str(command[1]) if command[0] in ("PLANT", "PLACE") and len(command) > 1 else "")
                    requested[key] += 1
        for event in events_by_day[day]:
            step = int(event["step"])
            phase = event.get("phase")
            if phase in ("market_unit", "market_atomic") and event.get("success"):
                operation = str(event["operation"])
                delta = float(event.get("cash_delta", event["cash_after"] - event["cash_before"]))
                if operation == "SELL":
                    item = str(event["item"])
                    assert delta > 0
                    receipts_cash[item] += delta
                    receipts_units[item] += 1
                elif delta < 0:
                    item = str(event.get("item", ""))
                    key = operation + (":" + item if item else "")
                    costs[key] -= delta
                    if operation in ("BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND"):
                        first_commitment.setdefault(key, step)
            elif phase == "unit_action" and event.get("changed"):
                command = event.get("action", [])
                if not command:
                    continue
                operation = str(command[0])
                _, tile = _unit_context(frames[step], int(event["actor"]))
                if operation in ("PLANT", "PLACE") and len(command) > 1:
                    key = operation + ":" + str(command[1])
                    confirmed[key] += 1
                    first_commitment.setdefault(key, step)
                elif operation in ("WATER", "FERTILIZE") and tile and tile.get("crop"):
                    confirmed[operation + ":" + str(tile["crop"])] += 1
                elif operation in ("FEED", "CARE") and tile and tile.get("animal"):
                    confirmed[operation + ":" + str(tile["animal"])] += 1
                elif operation == "HARVEST" and tile:
                    item = tile.get("crop") or ANIMAL_PRODUCTS.get(tile.get("animal"))
                    if item:
                        qty = int(tile.get("yield_units", 0) or 0)
                        assert qty > 0
                        harvest[str(item)] += qty
                        confirmed["HARVEST:" + str(item)] += 1
                elif operation == "DROP":
                    confirmed["DROP"] += 1
        assert round(opening + sum(receipts_cash.values()) - sum(costs.values()) - closing, 6) == 0
        totals_cash.update(receipts_cash)
        totals_units.update(receipts_units)
        totals_cost.update(costs)
        totals_harvest.update(harvest)
        totals_confirmed.update(confirmed)
        totals_requested.update(requested)
        daily.append({
            "day": day, "open": opening, "close": closing,
            "receipts_cash": dict(sorted(receipts_cash.items())),
            "receipts_units": dict(sorted(receipts_units.items())),
            "costs": dict(sorted(costs.items())),
            "harvest_units": dict(sorted(harvest.items())),
            "confirmed": dict(sorted(confirmed.items())),
            "requested": dict(sorted(requested.items())),
            "shops": list(obs["town"]["unlocked_shops"]),
            "prices": dict(sorted(obs["market"]["prices"].items())),
            "own_farm": public_farm_daily(own_farm),
            "rival_public_cash": float(rival_farm["money"]),
            "rival_public_farm": public_farm_daily(rival_farm),
        })
    assert daily[0]["open"] == 3000.0
    assert daily[-1]["close"] == trace["candidate_reward"]
    assert round(sum(totals_cash.values()) - sum(totals_cost.values()) + 3000 - trace["candidate_reward"], 6) == 0
    return {
        "role": role, "matched_loss_episode": target_episode,
        "rank": row["rank"], "team": row["team"], "episode": row["episode"],
        "source_seat": row["source_seat"], "source_reward": row["source_reward"],
        "source_file": row["file"], "candidate_seat": seat,
        "seed": row["seed"], "candidate_reward": trace["candidate_reward"],
        "rival_public_reward": trace["opponent_reward"], "margin": trace["margin"],
        "shops_final": daily[-1]["shops"],
        "totals": {"receipts_cash": dict(sorted(totals_cash.items())),
                   "receipts_units": dict(sorted(totals_units.items())),
                   "costs": dict(sorted(totals_cost.items())),
                   "harvest_units": dict(sorted(totals_harvest.items())),
                   "confirmed": dict(sorted(totals_confirmed.items())),
                   "requested": dict(sorted(totals_requested.items()))},
        "first_commitment_step": dict(sorted(first_commitment.items())),
        "daily": daily,
    }


def run_ledger_study(rows: list[dict], benchmark: dict, workers: int, out: Path) -> None:
    if hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest() != FROZEN_MAIN_SHA256:
        raise ValueError("main.py no longer matches the frozen benchmark")
    destination = out.resolve()
    if not destination.is_relative_to(HERE):
        raise ValueError("compact output must be inside the top50_current_2026-09-24 directory")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing {destination}")
    selected = ledger_panel(rows)
    jobs = [(role, row, target["episode"] if target else None, seat)
            for role, row, target in selected for seat in (0, 1)]
    first = _ledger_worker(jobs[0])
    results = [first]
    print(f"DONE 1/24 {first['role']} rank={first['rank']} "
          f"episode={first['episode']} seat={first['candidate_seat']} "
          f"own={first['candidate_reward']:.0f} rival={first['rival_public_reward']:.0f}",
          flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, min(4, workers))) as pool:
        futures = {pool.submit(_ledger_worker, job): job for job in jobs[1:]}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"DONE {len(results)}/24 {result['role']} rank={result['rank']} "
                  f"episode={result['episode']} seat={result['candidate_seat']} "
                  f"own={result['candidate_reward']:.0f} rival={result['rival_public_reward']:.0f}",
                  flush=True)
    results.sort(key=lambda r: (r["role"] != "loss", r["rank"], r["episode"], r["candidate_seat"]))
    assert len(results) == 24
    payload = {
        "schema": "kaggriculture-ledger-12-route-v1",
        "candidate_sha256": FROZEN_MAIN_SHA256,
        "summary_sha256": benchmark["summary_sha256"],
        "engine_version": benchmark["engine_version"],
        "selection": "ledger_panel: three predeclared double-loss teams, six distinct both-seat-winning matched controls",
        "game_count": 24,
        "route_count": 12,
        "rows": results,
    }
    with gzip.open(destination, "wt", encoding="utf-8", compresslevel=9) as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"COMPACT {destination} bytes={destination.stat().st_size} games=24", flush=True)


def read_compact(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["schema"] == "kaggriculture-ledger-12-route-v1"
    assert payload["candidate_sha256"] == FROZEN_MAIN_SHA256
    assert payload["game_count"] == len(payload["rows"]) == 24
    assert payload["route_count"] == len({row["source_file"] for row in payload["rows"]}) == 12
    assert len({(row["source_file"], row["candidate_seat"]) for row in payload["rows"]}) == 24
    assert all({row["candidate_seat"] for row in payload["rows"]
                if row["source_file"] == name} == {0, 1}
               for name in {row["source_file"] for row in payload["rows"]})
    for row in payload["rows"]:
        assert len(row["daily"]) == 30
        assert row["candidate_reward"] - row["rival_public_reward"] == row["margin"]
        assert row["daily"][0]["open"] == 3000
        for day, entry in enumerate(row["daily"]):
            assert entry["day"] == day
            if day:
                assert entry["open"] == row["daily"][day - 1]["close"]
            assert round(entry["open"] + sum(entry["receipts_cash"].values())
                         - sum(entry["costs"].values()) - entry["close"], 6) == 0
        assert row["daily"][-1]["close"] == row["candidate_reward"]
        for key in ("receipts_cash", "receipts_units", "costs", "harvest_units",
                    "confirmed", "requested"):
            aggregate = Counter()
            for entry in row["daily"]:
                aggregate.update(entry[key])
            assert dict(aggregate) == row["totals"][key]
    return payload


def summarize_ledger_study(path: Path) -> None:
    payload = read_compact(path)
    print("CHECK games=24 routes=12 daily_ledgers=720 all_reconciled=yes")
    print("PAIR loss_ep control_ep seat own_loss own_control rival_public_loss rival_public_control "
          "own_gap rival_gap margin_loss margin_control")
    for loss in [r for r in payload["rows"] if r["role"] == "loss"]:
        seat = loss["candidate_seat"]
        control = next(r for r in payload["rows"]
                       if r["role"] == "win-control" and r["matched_loss_episode"] == loss["episode"]
                       and r["candidate_seat"] == seat)
        own_gap = loss["candidate_reward"] - control["candidate_reward"]
        rival_gap = loss["rival_public_reward"] - control["rival_public_reward"]
        print("PAIR", loss["episode"], control["episode"], seat,
              loss["candidate_reward"], control["candidate_reward"],
              loss["rival_public_reward"], control["rival_public_reward"],
              own_gap, rival_gap, loss["margin"], control["margin"])
        if seat != 0:
            continue
        lr, cr = loss["totals"], control["totals"]
        product_diffs = sorted(((item,
                                 lr["receipts_cash"].get(item, 0) - cr["receipts_cash"].get(item, 0),
                                 lr["receipts_units"].get(item, 0), cr["receipts_units"].get(item, 0),
                                 lr["harvest_units"].get(item, 0), cr["harvest_units"].get(item, 0))
                                for item in set(lr["receipts_cash"]) | set(cr["receipts_cash"])),
                               key=lambda x: abs(x[1]), reverse=True)
        cost_diffs = sorted(((key, lr["costs"].get(key, 0) - cr["costs"].get(key, 0))
                             for key in set(lr["costs"]) | set(cr["costs"])),
                            key=lambda x: abs(x[1]), reverse=True)
        focus = product_diffs[0][0]
        first_receipt_day = next((day for day in range(30)
                                  if abs(sum(loss["daily"][i]["receipts_cash"].get(focus, 0)
                                             - control["daily"][i]["receipts_cash"].get(focus, 0)
                                             for i in range(day + 1))) >= 1000), None)
        first_persistent_own_gap = next((day for day in range(30)
                                         if all(loss["daily"][later]["close"]
                                                - control["daily"][later]["close"] <= -1000
                                                for later in range(day, 30))), None)
        def visible_capacity(game: dict, day: int, item: str) -> int:
            farm = game["daily"][day]["own_farm"]
            if item in ("WOOL", "MILK", "EGG"):
                animal = {"WOOL": "SHEEP", "MILK": "COW", "EGG": "GOOSE"}[item]
                return sum(count for key, count in farm["animals"].items() if key.startswith(animal + "@"))
            return sum(count for key, count in farm["plants"].items() if key.startswith(item + "@"))
        first_focus_capacity_gap = next((day for day in range(30)
                                         if visible_capacity(loss, day, focus)
                                         != visible_capacity(control, day, focus)), None)
        first_shop_gap = next((day for day in range(30)
                               if loss["daily"][day]["shops"] != control["daily"][day]["shops"]), None)
        focus_units_loss = lr["receipts_units"].get(focus, 0)
        focus_units_control = cr["receipts_units"].get(focus, 0)
        focus_price_loss = lr["receipts_cash"].get(focus, 0) / focus_units_loss if focus_units_loss else 0
        focus_price_control = cr["receipts_cash"].get(focus, 0) / focus_units_control if focus_units_control else 0
        quantity_contribution = ((focus_units_loss - focus_units_control)
                                 * (focus_price_loss + focus_price_control) / 2)
        price_contribution = ((focus_price_loss - focus_price_control)
                              * (focus_units_loss + focus_units_control) / 2)
        print("DETAIL", loss["episode"], "first_shop_path_diff_day", first_shop_gap,
              "shops_first2", loss["shops_final"][:2], control["shops_final"][:2],
              "shops_later", loss["shops_final"][2:], control["shops_final"][2:])
        print("DETAIL", loss["episode"], "own_receipts_loss_control",
              (sum(lr["receipts_cash"].values()), sum(cr["receipts_cash"].values())),
              "own_costs_loss_control", (sum(lr["costs"].values()), sum(cr["costs"].values())))
        print("DETAIL", loss["episode"], "top_receipt_diffs_cash_units_harvest", product_diffs[:5],
              "top_cost_diffs", cost_diffs[:5])
        print("DETAIL", loss["episode"], "first_focus_receipt_1k_day", focus, first_receipt_day,
              "first_persistent_own_cash_gap_1k_day", first_persistent_own_gap,
              "first_focus_public_capacity_diff_day", first_focus_capacity_gap,
              "focus_max_public_capacity_loss_control",
              (max(visible_capacity(loss, day, focus) for day in range(30)),
               max(visible_capacity(control, day, focus) for day in range(30))),
              "focus_avg_realized_price_loss_control",
              (round(focus_price_loss, 2), round(focus_price_control, 2)),
              "focus_receipt_gap_quantity_price_split",
              (round(quantity_contribution), round(price_contribution)),
              "focus_confirmed_loss_control", [(key, lr["confirmed"].get(key, 0), cr["confirmed"].get(key, 0))
                                               for key in ("PLANT:" + focus,
                                                           "WATER:" + focus,
                                                           "PLACE:" + {"WOOL": "SHEEP", "MILK": "COW", "EGG": "GOOSE"}.get(focus, focus),
                                                           "FEED:" + {"WOOL": "SHEEP", "MILK": "COW", "EGG": "GOOSE"}.get(focus, focus),
                                                           "CARE:" + {"WOOL": "SHEEP", "MILK": "COW", "EGG": "GOOSE"}.get(focus, focus))
                                               if lr["confirmed"].get(key, 0) or cr["confirmed"].get(key, 0)])
        print("DETAIL", loss["episode"], "selected_day_cash", [
            (day, loss["daily"][day]["close"], control["daily"][day]["close"],
             loss["daily"][day]["rival_public_cash"], control["daily"][day]["rival_public_cash"])
            for day in (0, 6, 9, 12, 15, 18, 21, 24, 27, 29)])


def trace_sample(rows: list[dict], spec: str, forced_shops: list[str] | None = None,
                 public_ledger: bool = False) -> None:
    """Run just one specified native replay in memory; create no trace file."""
    if hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest() != FROZEN_MAIN_SHA256:
        raise ValueError("main.py no longer matches the frozen benchmark; cannot compare a new trace")
    rank_text, episode_text, seat_text = spec.split(":")
    rank, episode, seat = int(rank_text), int(episode_text), int(seat_text)
    assert seat in (0, 1)
    matches = [r for r in rows if r["rank"] == rank and r["episode"] == episode]
    if len(matches) != 1:
        raise ValueError(f"Expected one route for {spec}, found {len(matches)}")
    row = matches[0]
    sys.path.insert(0, str(ROOT))
    from trace_paired_game_events import run

    result = run(str(ROOT / "main.py"), "rawroute:" + str(HERE / "routes" / row["file"]),
                 row["seed"], seat, shop_sequence=forced_shops)
    assert result["engine_version"] == "1.32.7"
    if forced_shops is None:
        assert result["candidate_reward"] == row["seat_ours"][seat]
        assert result["opponent_reward"] == row["seat_theirs"][seat]
    print("TRACE", spec, row["team"], "mode", "native" if forced_shops is None else "forced_shops_modified_env",
          "source_reward", row["source_reward"],
          "ours", result["candidate_reward"], "theirs", result["opponent_reward"],
          "margin", result["margin"])

    shops = []
    for day in range(30):
        frame = result["traces"][seat][day * 24]
        observed = frame["observation"]
        unlocked = observed["town"]["unlocked_shops"]
        if len(unlocked) > len(shops):
            print("SHOP", day, unlocked[len(shops):])
            shops = unlocked
        if day in (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 29):
            farms = observed["farms"]
            print("DAY", day, "cash", farms[seat]["money"], farms[1-seat]["money"])
            if public_ledger:
                print("FARM", day, "ours", public_farm_capacity(farms[seat]),
                      "rival_public", public_farm_capacity(farms[1-seat]))

    for label, player in (("ours", seat),):
        sold_cash = Counter()
        sold_units = Counter()
        spent = Counter()
        rejected = Counter()
        for event in result["events"]:
            if event.get("player") != player or event.get("phase") not in ("market_unit", "market_atomic"):
                continue
            op = event["operation"]
            if not event.get("success"):
                rejected[(op, event.get("failure_reason"))] += 1
            elif op == "SELL":
                sold_cash[event["item"]] += event["cash_delta"]
                sold_units[event["item"]] += 1
            else:
                spent[(op, event.get("item", ""))] += event["cash_before"] - event["cash_after"]
        last = result["turns"][-1]["players_after"][player]
        print("ECON", label, "sold_cash", dict(sold_cash), "sold_units", dict(sold_units),
              "spent", {str(k): v for k, v in spent.items() if v},
              "rejected", {str(k): v for k, v in rejected.items() if v},
              "final_shed", {k: v for k,v in last["shed"].items() if v})
    if public_ledger:
        turns_by_step = {int(turn["step"]): turn for turn in result["turns"] if int(turn["step"]) >= 0}
        for day in range(30):
            start_step = day * 24
            end_step = min(start_step + 23, 718)
            opening = turns_by_step[start_step]["players_before"][seat]["cash"]
            closing = turns_by_step[end_step]["players_after"][seat]["cash"]
            revenue = Counter()
            spending = Counter()
            service = Counter()
            for event in result["events"]:
                if event.get("player") != seat or event.get("step", -1) // 24 != day:
                    continue
                if event.get("phase") in ("market_unit", "market_atomic") and event.get("success"):
                    delta = event.get("cash_delta", event["cash_after"] - event["cash_before"])
                    key = event.get("operation", "")
                    if delta > 0:
                        revenue[key] += delta
                    elif delta < 0:
                        spending[key] -= delta
                if event.get("phase") == "unit_action" and event.get("changed"):
                    action = event.get("action", [])
                    if action and action[0] in ("PLANT", "WATER", "FERTILIZE", "HARVEST", "FEED", "CARE", "DROP"):
                        service[action[0] + (":" + str(action[1]) if action[0] == "PLANT" and len(action) > 1 else "")] += 1
            assert round(opening + sum(revenue.values()) - sum(spending.values()) - closing, 6) == 0
            print("LEDGER", day, "open", opening, "close", closing,
                  "receipts", dict(revenue), "costs", dict(spending), "service", dict(service))
    print("END_TRACE", spec)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", action="append", default=[], metavar="RANK:EPISODE:SEAT",
                        help="Run only these specified native event traces in memory")
    parser.add_argument("--force-shops", type=str, default=None, metavar="SHOP,SHOP,...",
                        help="Diagnostic modified environment; requires exactly one --trace")
    parser.add_argument("--public-ledger", action="store_true",
                        help="With --trace, print exact own day ledger and public farm snapshots")
    parser.add_argument("--markdown", action="store_true", help="Print a Markdown table of all 33 losses")
    parser.add_argument("--preselect-ledger-panel", action="store_true",
                        help="Print 12 preselected routes for a future both-seat cash-ledger study; no sims")
    parser.add_argument("--ledger-study", action="store_true",
                        help="Run the predeclared 12-route x both-seat native study (24 games)")
    parser.add_argument("--compact-out", type=Path,
                        help="New .json.gz path inside this diagnostics directory for bounded daily aggregates")
    parser.add_argument("--workers", type=int, default=3, help="Ledger-study processes (1-4, default 3)")
    parser.add_argument("--summarize-ledger", type=Path,
                        help="Read a compact ledger artifact and print bounded paired evidence; no sims")
    args = parser.parse_args()
    rows, benchmark = panel()
    if args.force_shops is not None and not args.trace:
        parser.error("--force-shops requires --trace")
    if args.public_ledger and not args.trace:
        parser.error("--public-ledger requires --trace")
    if args.ledger_study:
        if args.trace or args.force_shops or args.public_ledger or not args.compact_out:
            parser.error("--ledger-study requires --compact-out and no trace/modified-environment options")
        run_ledger_study(rows, benchmark, args.workers, args.compact_out)
        return
    if args.summarize_ledger:
        summarize_ledger_study(args.summarize_ledger)
        return
    if args.preselect_ledger_panel:
        print("| Role | Matched loss episode | Rank | Team | Episode | Source seat | Source cash | Route file |")
        print("| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |")
        for role, row, target in ledger_panel(rows):
            print(f"| {role} | {target['episode'] if target else '—'} | {row['rank']} | "
                  f"{row['team']} | {row['episode']} | {row['source_seat']} | "
                  f"{row['source_reward']:,.0f} | `{row['file']}` |")
        return
    if args.trace:
        if args.force_shops is not None and len(args.trace) != 1:
            parser.error("--force-shops requires exactly one --trace")
        forced_shops = args.force_shops.split(",") if args.force_shops else None
        if forced_shops is not None and len(forced_shops) != 8:
            parser.error("--force-shops requires exactly eight shops")
        for spec in args.trace:
            trace_sample(rows, spec, forced_shops, args.public_ledger)
        return
    if args.markdown:
        own_mid = median(r["ours"] for r in rows)
        rival_mid = median(r["theirs"] for r in rows)
        losses = sorted((r for r in rows if r["margin"] < 0), key=lambda r: (r["rank"], r["episode"]))
        by_stratum = defaultdict(list)
        for r in losses:
            by_stratum[stratum(r, own_mid, rival_mid)].append(r)
        print("| Cluster | Routes | Sum of paired deficits | Median own cash | Median rival cash |")
        print("| --- | ---: | ---: | ---: | ---: |")
        for name in ("rival-high", "both", "own-low"):
            selection = by_stratum[name]
            print(f"| {name} | {len(selection)} | {sum(2*r['margin'] for r in selection):,.0f} | "
                  f"{median(r['ours'] for r in selection):,.0f} | {median(r['theirs'] for r in selection):,.0f} |")
        print("\n| Rank | Episode | Team | Cluster | Own cash / seat | Rival cash / seat | Paired margin | Replay − source rival cash |")
        print("| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |")
        for r in losses:
            print(f"| {r['rank']} | {r['episode']} | {r['team']} | {stratum(r, own_mid, rival_mid)} | "
                  f"{r['ours']:,.1f} | {r['theirs']:,.1f} | {2*r['margin']:+,.0f} | "
                  f"{r['theirs']-r['source_reward']:+,.1f} |")
        return
    losses = sorted((r for r in rows if r["margin"] < 0), key=lambda r: (r["rank"], r["episode"]))
    print("candidate_sha256", benchmark["candidate_sha256"])
    print("summary_sha256", benchmark["summary_sha256"])
    print("route_results", benchmark["route_paired_results"])
    print("panel_medians", "ours", median(r["ours"] for r in rows), "theirs", median(r["theirs"] for r in rows))
    print("loss_medians", "ours", median(r["ours"] for r in losses), "theirs", median(r["theirs"] for r in losses))
    own_mid = median(r["ours"] for r in rows)
    rival_mid = median(r["theirs"] for r in rows)
    quadrants = Counter((r["ours"] < own_mid, r["theirs"] > rival_mid) for r in losses)
    print("loss_quadrants (own_below_panel_median, rival_above_panel_median)", dict(quadrants))
    for outcome, selection in (("loss", losses), ("win", [r for r in rows if r["margin"] > 0])):
        print(outcome, "n", len(selection), "median_source_delta", median(r["theirs"] - r["source_reward"] for r in selection),
              "median_own", median(r["ours"] for r in selection), "median_rival", median(r["theirs"] for r in selection))
    rank_bands = defaultdict(list)
    for r in rows:
        rank_bands[(r["rank"] - 1) // 10 + 1].append(r)
    for band, selection in sorted(rank_bands.items()):
        print("rank_band", f"{(band-1)*10+1}-{band*10}", "losses", sum(r["margin"] < 0 for r in selection),
              "median_own", median(r["ours"] for r in selection), "median_rival", median(r["theirs"] for r in selection))
    print("source_delta_outliers", sorted(((r["team"], r["episode"], round(r["theirs"]-r["source_reward"]))
                                            for r in rows), key=lambda x: abs(x[2]), reverse=True)[:15])
    print("seat_discordant", [(r["team"], r["episode"], r["seat_margins"])
                              for r in rows if (r["seat_margins"][0] > 0) != (r["seat_margins"][1] > 0)])
    teams = defaultdict(list)
    for r in rows:
        teams[r["team"]].append(r)
    print("team_split_episodes", sum((a["margin"] > 0) != (b["margin"] > 0) for a,b in teams.values()))
    print("losses: rank episode team ours theirs avg_margin source_reward source_delta seat_margins sell_intent harvest plant care")
    for r in losses:
        t = r["tape"]
        print(r["rank"], r["episode"], r["team"], round(r["ours"]), round(r["theirs"]),
              round(r["margin"]), r["source_reward"], round(r["theirs"] - r["source_reward"]), r["seat_margins"],
              t["sell_intent"], t["harvest_intent"], t["plant_intent"], t["care_intent"], sep="\t")


if __name__ == "__main__":
    main()
