"""Shadow-test eligibility for the one-slot surplus-sale experiment.

This harness replays the unchanged H6 candidate on a preselected, loss-enriched
set of fixed tapes. It does not alter candidate actions. It records when a
single extra sale could conservatively be appended using only the current
observation, current action queue, and same-turn commands.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from kaggle_environments import __version__ as engine_version
from trace_paired_game import run as run_trace


ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / "main_frontier_h6_candidate_2026-09-24.py"
OUTPUT = ROOT / "diagnostics" / "frontier_h6_5e7_surplus_sale_shadow_24routes_48games_2026-09-24.json"
PANEL_SOURCES = (
    ("301-420", ROOT / "diagnostics" / "mainfrontier_h6_opening_B_ranks301-420_full_2026-09-24.json"),
    ("421-460", ROOT / "diagnostics" / "frontier_h6_5e7_ranks421-460_full_2026-09-24.json"),
    ("461-500", ROOT / "diagnostics" / "frontier_h6_5e7_ranks461-500_full_2026-09-24.json"),
    ("501-600", ROOT / "diagnostics" / "frontier_h6_current_candidate_ranks501-600_full98_2026-09-24.json"),
)
MAX_EXTRA_UNITS = 10
WORKERS = 6

_POLICY_MODULE = None
_MARKET_CONFIG = {
    "boardSize": 10,
    "turnsPerDay": 24,
    "shedCapacity": 100,
    "maxMarketOrdersPerTurn": 10,
    "townShopSellInterval": 4,
    "townCenterSellInterval": 24,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose_routes() -> list[dict[str, Any]]:
    """Select three loss and three two-seat-win routes from each rank band."""
    selected: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for band, source in PANEL_SOURCES:
        panel = json.loads(source.read_text(encoding="utf-8"))
        rows = panel["rows"]
        losses = sorted(
            (row for row in rows if float(row["pair_margin"]) < 0),
            key=lambda row: (float(row["pair_margin"]), str(row["opponent_path"])),
        )
        controls = sorted(
            (
                row for row in rows
                if float(row["pair_margin"]) > 0
                and all(game["result"] == "win" for game in row["games"])
            ),
            key=lambda row: (float(row["pair_margin"]), str(row["opponent_path"])),
        )
        if len(losses) < 3 or len(controls) < 3:
            raise ValueError(f"{band}: need 3 losses and 3 two-seat-win controls")
        # Two largest deficits plus the closest loss. In a band with exactly
        # three losses this simply selects all three.
        chosen = losses[:2] + [losses[-1]]
        chosen += controls[:3]
        for stratum, row in (
            [("loss", item) for item in chosen[:3]]
            + [("control", item) for item in chosen[3:]]
        ):
            path = str(row["opponent_path"])
            if path in seen_paths:
                raise ValueError(f"Duplicate replay path across panels: {path}")
            seen_paths.add(path)
            selected.append(
                {
                    "band": band,
                    "stratum": stratum,
                    "team": row["team"],
                    "seed": int(row["seed"]),
                    "opponent_path": path,
                    "action_sha256": row.get("action_sha256"),
                    "baseline_pair_margin": float(row["pair_margin"]),
                    "baseline_games": [
                        {
                            "candidate_seat": int(game["candidate_seat"]),
                            "candidate_reward": float(game["candidate_reward"]),
                            "opponent_reward": float(game["opponent_reward"]),
                            "result": game["result"],
                            "candidate_status": game["candidate_status"],
                            "opponent_status": game["opponent_status"],
                        }
                        for game in row["games"]
                    ],
                }
            )
    return selected


def _policy_module():
    global _POLICY_MODULE
    if _POLICY_MODULE is None:
        name = f"shadow_h6_policy_{os.getpid()}"
        spec = importlib.util.spec_from_file_location(name, CANDIDATE)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot import candidate for its H6 ranker: {CANDIDATE}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _POLICY_MODULE = module
    return _POLICY_MODULE


def _shadow_events(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find conservative surplus-sale opportunities without changing actions."""
    policy = _policy_module()
    eligible_items = [item for item in policy._H6_MARKET_PARAMS if item in policy._IG_CASH]
    cap = int(_MARKET_CONFIG["maxMarketOrdersPerTurn"])
    events: list[dict[str, Any]] = []

    for record in records:
        action = record.get("action")
        obs = record.get("observation")
        if not isinstance(action, dict) or not isinstance(obs, dict):
            continue
        market = list(action.get("market") or [])
        if len(market) >= cap:
            continue
        shed = (obs.get("private", {}) or {}).get("shed", {}) or {}
        sales: dict[str, int] = {}
        buys: set[str] = set()
        for order in market:
            if not isinstance(order, (list, tuple)) or len(order) < 2:
                continue
            if order[0] == "SELL" and len(order) >= 3:
                try:
                    sales[str(order[1])] = sales.get(str(order[1]), 0) + max(0, int(order[2]))
                except (TypeError, ValueError):
                    continue
            elif order[0] == "BUY_PRODUCT":
                buys.add(str(order[1]))

        pickups: dict[str, int] = {}
        commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
        for command in commands:
            if not isinstance(command, (list, tuple)) or len(command) < 2 or command[0] != "PICKUP":
                continue
            item = str(command[1])
            try:
                quantity = max(1, int(command[2])) if len(command) >= 3 else 1
            except (TypeError, ValueError):
                quantity = 1
            pickups[item] = pickups.get(item, 0) + quantity

        candidates: list[tuple[float, int, str, int, int, int]] = []
        for index, item in enumerate(eligible_items):
            if item in buys:
                continue
            price = int((obs.get("market", {}).get("prices", {}) or {}).get(item, 0) or 0)
            if price < 2:  # preserve the base policy's minimum-price safety check
                continue
            # Count only goods already in the shed. Ignore same-turn deposits,
            # and subtract current sales plus explicit same-turn pickups.
            before = max(0, int(shed.get(item, 0) or 0))
            available = max(0, before - sales.get(item, 0) - pickups.get(item, 0))
            if available <= 0:
                continue
            quantity = min(MAX_EXTRA_UNITS, available)
            score, _urgent = policy._h6_order_score(
                obs, _MARKET_CONFIG, ["SELL", item, quantity]
            )
            candidates.append((float(score), -index, item, quantity, before, price))

        if candidates:
            score, _order, item, quantity, before, price = max(candidates)
            events.append(
                {
                    "step": int(record.get("step", -1)),
                    "day": int(obs.get("day", -1)),
                    "hour": int(obs.get("hour", -1)),
                    "item": item,
                    "quantity": quantity,
                    "h6_score": score,
                    "quoted_price": price,
                    "shed_before": before,
                    "same_turn_sell_reserved": sales.get(item, 0),
                    "same_turn_pickup_reserved": pickups.get(item, 0),
                    "original_queue_length": len(market),
                    "free_slots": cap - len(market),
                    "cash_before": float(obs["farms"][int(obs["player"])]["money"]),
                }
            )
    return events


def run_one(job: dict[str, Any]) -> dict[str, Any]:
    trace = run_trace(
        str(CANDIDATE),
        "rawroute:" + str(job["opponent_path"]),
        int(job["seed"]),
        int(job["candidate_seat"]),
    )
    seat = int(job["candidate_seat"])
    events = _shadow_events(trace["traces"][seat])
    baseline = next(
        row for row in job["baseline_games"]
        if int(row["candidate_seat"]) == seat
    )
    return {
        "band": job["band"],
        "stratum": job["stratum"],
        "team": job["team"],
        "seed": int(job["seed"]),
        "opponent_path": job["opponent_path"],
        "action_sha256": job.get("action_sha256"),
        "candidate_seat": seat,
        "baseline_pair_margin": job["baseline_pair_margin"],
        "baseline_expected": baseline,
        "trace_result": {
            "candidate_reward": trace["candidate_reward"],
            "opponent_reward": trace["opponent_reward"],
            "margin": trace["margin"],
            "candidate_status": trace["candidate_status"],
            "opponent_status": trace["opponent_status"],
            "frames": len(trace["traces"][seat]),
        },
        "baseline_reproduced": (
            float(trace["margin"]) == float(baseline["candidate_reward"] - baseline["opponent_reward"])
            and trace["candidate_status"] == baseline["candidate_status"]
            and trace["opponent_status"] == baseline["opponent_status"]
        ),
        "eligible_decisions": len(events),
        "eligible_units": sum(int(event["quantity"]) for event in events),
        "events": events,
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {OUTPUT}")
    selected = choose_routes()
    jobs = [
        {**route, "candidate_seat": seat}
        for route in selected
        for seat in (0, 1)
    ]
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(run_one, job): job for job in jobs}
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            row = future.result()
            rows.append(row)
            print(
                f"[{index}/{len(jobs)}] {row['band']} {row['stratum']} {row['team']} "
                f"seat={row['candidate_seat']} margin={row['trace_result']['margin']:+.0f} "
                f"eligible={row['eligible_decisions']} reproduced={row['baseline_reproduced']}",
                flush=True,
            )

    rows.sort(key=lambda row: (row["band"], row["opponent_path"], row["candidate_seat"]))
    by_band: dict[str, dict[str, Any]] = {}
    for band, _source in PANEL_SOURCES:
        band_rows = [row for row in rows if row["band"] == band]
        loss_rows = [row for row in band_rows if row["stratum"] == "loss"]
        control_rows = [row for row in band_rows if row["stratum"] == "control"]
        by_band[band] = {
            "games": len(band_rows),
            "loss_games_with_eligible_sale": sum(row["eligible_decisions"] > 0 for row in loss_rows),
            "control_games_with_eligible_sale": sum(row["eligible_decisions"] > 0 for row in control_rows),
            "loss_eligible_decisions": sum(row["eligible_decisions"] for row in loss_rows),
            "control_eligible_decisions": sum(row["eligible_decisions"] for row in control_rows),
            "baseline_reproduced_games": sum(bool(row["baseline_reproduced"]) for row in band_rows),
        }

    output = {
        "candidate": str(CANDIDATE),
        "candidate_sha256": sha256(CANDIDATE),
        "engine_version": engine_version,
        "selection": selected,
        "shadow_rule": {
            "max_extra_orders_per_decision": 1,
            "max_extra_units_per_order": MAX_EXTRA_UNITS,
            "append_only_if_free_slot": True,
            "eligible_products": [
                item for item in _policy_module()._H6_MARKET_PARAMS
                if item in _policy_module()._IG_CASH
            ],
            "minimum_quoted_price": 2,
            "stock_basis": "current own shed only; subtract same-turn scheduled SELLs and explicit PICKUPs; ignore deposits",
            "product_ranker": "candidate _h6_order_score, with the candidate's default Kaggriculture configuration",
            "limitations": [
                "Shadow only; actions and scores are unchanged.",
                "Does not estimate future-policy inventory reservations or realized settlement prices.",
                "A positive eligibility count is necessary for the proposed treatment to affect that trace, not evidence of benefit.",
            ],
        },
        "summary": {
            "routes": len(selected),
            "games": len(rows),
            "all_done": all(
                row["trace_result"]["candidate_status"] == "DONE"
                and row["trace_result"]["opponent_status"] == "DONE"
                for row in rows
            ),
            "baseline_reproduced_games": sum(bool(row["baseline_reproduced"]) for row in rows),
            "loss_games_with_eligible_sale": sum(
                row["stratum"] == "loss" and row["eligible_decisions"] > 0 for row in rows
            ),
            "control_games_with_eligible_sale": sum(
                row["stratum"] == "control" and row["eligible_decisions"] > 0 for row in rows
            ),
            "loss_eligible_decisions": sum(
                row["eligible_decisions"] for row in rows if row["stratum"] == "loss"
            ),
            "control_eligible_decisions": sum(
                row["eligible_decisions"] for row in rows if row["stratum"] == "control"
            ),
            "by_band": by_band,
        },
        "games": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print("SUMMARY " + json.dumps(output["summary"], ensure_ascii=False, sort_keys=True))
    print(f"wrote={OUTPUT}")


if __name__ == "__main__":
    main()
