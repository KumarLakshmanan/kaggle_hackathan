"""Summarize exact Boey sell-failure event traces without touching main.py.

The trace captures and matched-control games are written separately under
diagnostics/boey_sell_20260925/. This script only reads those traces and writes
the requested report in that directory.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "diagnostics" / "boey_sell_20260925"
FROZEN_MAIN_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
ROUTES = {
    "boey_112939032": {
        "team": "Boey", "episode": 112939032, "seed": 1016478476,
        "route_file": "Boey-submission-56521745-episode-112939032-seat1.json.gz",
    },
    "boey_112940236": {
        "team": "Boey", "episode": 112940236, "seed": 409584214,
        "route_file": "Boey-submission-56521745-episode-112940236-seat1.json.gz",
    },
    "control_ryo_112931133": {
        "team": "Ryo Hasegawa", "episode": 112931133, "seed": 1038853615,
        "route_file": "Ryo-Hasegawa-submission-56506377-episode-112931133-seat0.json.gz",
    },
    "control_gleb_112939403": {
        "team": "Gleb Tumanov", "episode": 112939403, "seed": 1231382306,
        "route_file": "Gleb-Tumanov-submission-56357593-episode-112939403-seat1.json.gz",
    },
}


def read_trace(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def summarize_trace(path: Path) -> dict[str, Any]:
    result = read_trace(path)
    player = int(result["candidate_seat"])
    events = [
        event for event in result["events"]
        if event.get("player") == player and event.get("phase") == "market_unit"
    ]
    failed = [
        event for event in events
        if event.get("operation") == "SELL"
        and event.get("failure_reason") == "empty_shed"
    ]
    successful = [
        event for event in events
        if event.get("operation") == "SELL" and event.get("success")
    ]

    # The simulator's empty-stock failure is a strict no-op. Assert every
    # captured failure has the expected unchanged state before reporting it.
    for event in failed:
        assert event["item_shed_before"] == 0
        assert event["item_shed_after"] == 0
        assert event["cash_before"] == event["cash_after"]
        assert event["market_inventory_before"] == event["market_inventory_after"]

    failure_by_item: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"units": 0, "quoted_value": 0.0, "steps": []}
    )
    failure_by_step: dict[tuple[int, str], dict[str, Any]] = defaultdict(
        lambda: {"units": 0, "quoted_value": 0.0}
    )
    for event in failed:
        item = str(event["item"])
        step = int(event["step"])
        price = float(event["quoted_unit_price"])
        item_row = failure_by_item[item]
        item_row["units"] += 1
        item_row["quoted_value"] += price
        item_row["steps"].append(step)
        step_row = failure_by_step[(step, item)]
        step_row["units"] += 1
        step_row["quoted_value"] += price

    sales_by_item: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"units": 0, "receipts": 0.0}
    )
    for event in successful:
        row = sales_by_item[str(event["item"])]
        row["units"] += 1
        row["receipts"] += float(event["cash_delta"])

    frames = {
        int(frame["step"]): frame
        for frame in result["traces"][player]
    }
    shed_access = {(4, 4), (5, 4), (4, 5), (5, 5)}
    failure_details = []
    all_events = result["events"]
    event_positions = {id(event): index for index, event in enumerate(all_events)}
    for event in failed:
        event_index = event_positions[id(event)]
        prior_sales_same_step = [
            earlier for earlier in all_events[:event_index]
            if earlier.get("player") == player
            and earlier.get("phase") == "market_unit"
            and earlier.get("operation") == "SELL"
            and earlier.get("item") == event["item"]
            and earlier.get("success")
            and earlier.get("step") == event.get("step")
        ]
        frame = frames.get(int(event["step"]), {})
        observation = frame.get("observation", {})
        private = observation.get("private", {}) or {}
        inventories = private.get("inventories", []) or []
        farm = (observation.get("farms", []) or [{}] * (player + 1))[player]
        positions = [farm.get("farmer")] + list(farm.get("hands", []) or [])
        carried = 0
        carried_near_shed = 0
        carrier_rows = []
        for idx, inventory in enumerate(inventories):
            qty = int((inventory or {}).get(event["item"], 0) or 0)
            carried += qty
            pos = positions[idx] if idx < len(positions) else None
            if pos is not None and tuple(pos) in shed_access:
                carried_near_shed += qty
            if qty:
                action = frame.get("action", {}) or {}
                commands = [action.get("farmer")] + list(action.get("hands", []) or [])
                carrier_rows.append({
                    "actor": idx,
                    "units": qty,
                    "position": pos,
                    "at_shed_access": pos is not None and tuple(pos) in shed_access,
                    "current_unit_action": commands[idx] if idx < len(commands) else None,
                })
        already_delivering = sum(
            carrier["units"] for carrier in carrier_rows
            if carrier["at_shed_access"]
            and (
                carrier["current_unit_action"] == ["DROP"]
                or (
                    isinstance(carrier["current_unit_action"], list)
                    and len(carrier["current_unit_action"]) >= 2
                    and carrier["current_unit_action"][0] == "PLACE"
                    and carrier["current_unit_action"][1] == event["item"]
                )
            )
        )
        accessible_not_delivering = max(0, carried_near_shed - already_delivering)
        requested_same_item = sum(
            int(order[2]) for order in (frame.get("action", {}) or {}).get("market", []) or []
            if isinstance(order, list) and len(order) >= 3
            and order[0] == "SELL" and order[1] == event["item"]
        )
        remaining_sell_capacity = max(
            0, requested_same_item - len(prior_sales_same_step)
        )
        immediate_extra_units = min(accessible_not_delivering, remaining_sell_capacity)
        failure_details.append({
            "step": int(event["step"]),
            "item": str(event["item"]),
            "quote": float(event["quoted_unit_price"]),
            "carried_units": carried,
            "carried_units_at_shed": carried_near_shed,
            "carriers": carrier_rows,
            "current_market_orders": (frame.get("action", {}) or {}).get("market", []),
            "prior_same_step_successful_sell_units": len(prior_sales_same_step),
            "prior_same_step_successful_sell_receipts": sum(
                float(sale["cash_delta"]) for sale in prior_sales_same_step
            ),
            "cargo_at_shed_not_already_delivering": accessible_not_delivering,
            "current_sell_order_units_remaining": remaining_sell_capacity,
            "immediate_extra_units_upper_bound": immediate_extra_units,
            "immediate_extra_receipts_upper_bound": (
                immediate_extra_units * float(event["quoted_unit_price"])
            ),
        })

    final = result["turns"][-1]["players_after"]
    last_frame = result["traces"][player][-1]
    last_observation = last_frame.get("observation", {})
    final_carried: Counter[str] = Counter()
    for inventory in (last_observation.get("private", {}) or {}).get("inventories", []) or []:
        final_carried.update(inventory or {})
    terminal_step = int(last_frame["step"])
    terminal_requested = {
        str(order[1]): int(order[2])
        for order in (last_frame.get("action", {}) or {}).get("market", []) or []
        if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL"
    }
    terminal_successes: dict[str, int] = defaultdict(int)
    terminal_receipts: dict[str, float] = defaultdict(float)
    for event in events:
        if (
            event.get("step") == terminal_step
            and event.get("operation") == "SELL"
            and event.get("success")
        ):
            terminal_successes[str(event["item"])] += 1
            terminal_receipts[str(event["item"])] += float(event["cash_delta"])
    shops = result["traces"][player][0]["observation"]["town"]["unlocked_shops"]
    return {
        "file": path.name,
        "seed": int(result["seed"]),
        "seat": player,
        "candidate_cash": float(result["candidate_reward"]),
        "rival_cash": float(result["opponent_reward"]),
        "margin": float(result["margin"]),
        "candidate_status": result["candidate_status"],
        "rival_status": result["opponent_status"],
        "shops": shops,
        "empty_sell_attempts": len(failed),
        "empty_sell_quoted_upper_bound": sum(
            float(event["quoted_unit_price"]) for event in failed
        ),
        "failure_by_item": dict(failure_by_item),
        "failure_by_step": [
            {"step": step, "item": item, **values}
            for (step, item), values in sorted(failure_by_step.items())
        ],
        "failure_details": failure_details,
        "failure_units_with_matching_cargo": sum(
            detail["carried_units"] > 0 for detail in failure_details
        ),
        "failure_units_with_cargo_at_shed": sum(
            detail["carried_units_at_shed"] > 0 for detail in failure_details
        ),
        "failures_after_same_step_successful_sale": sum(
            detail["prior_same_step_successful_sell_units"] > 0
            for detail in failure_details
        ),
        "failures_without_same_step_successful_sale": sum(
            detail["prior_same_step_successful_sell_units"] == 0
            for detail in failure_details
        ),
        "direct_execution_extra_receipts_ceiling": sum(
            detail["immediate_extra_receipts_upper_bound"]
            for detail in failure_details
        ),
        "successful_sell_units": len(successful),
        "successful_sell_receipts": sum(float(event["cash_delta"]) for event in successful),
        "sales_by_item": dict(sales_by_item),
        "final_shed": final[player]["shed"],
        "last_trace_step": int(last_frame["step"]),
        "last_observed_carried": dict(final_carried),
        "terminal_sell_requested": terminal_requested,
        "terminal_sell_successes": dict(terminal_successes),
        "terminal_sell_receipts": dict(terminal_receipts),
        "all_empty_failures_are_noops": True,
    }


def fmt_money(value: float) -> str:
    return f"{value:,.0f}"


def render_report(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Boey rank-35 sell-attempt diagnosis — 2026-09-25",
        "",
        "## Scope and frozen inputs",
        "",
        "This is an offline replay diagnostic against the exact captured opponent tapes. "
        "Boey episodes 112939032 and 112940236 are both rank-35 loss routes. The two "
        "preselected winning controls are Ryo Hasegawa 112931133 (clear high-cash win) "
        "and Gleb Tumanov 112939403 (thin positive lower-cash win). Every route is "
        "replayed with our agent in both seats. The frozen baseline `main.py` SHA-256 "
        f"is `{FROZEN_MAIN_SHA256}`; capture mode refuses to run if it differs.",
        "",
        "## Native baseline results",
        "",
        "| Route | Seat | Our terminal cash | Rival terminal cash | Margin | Empty-shed SELL units | Quoted-price sum* | After same-step sale | No prior same-step sale | Direct on-access execution ceiling‡ | Successful SELL units / receipts | Final carried → terminal sells† |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        name = row["file"].replace("baseline_", "").replace(".json.gz", "")
        terminal = ", ".join(
            f"{item} {row['terminal_sell_successes'].get(item, 0)}/{quantity}"
            for item, quantity in sorted(row["terminal_sell_requested"].items())
        ) or "no final SELL"
        lines.append(
            f"| {name} | {row['seat']} | {fmt_money(row['candidate_cash'])} | "
            f"{fmt_money(row['rival_cash'])} | {fmt_money(row['margin'])} | "
            f"{row['empty_sell_attempts']} | {fmt_money(row['empty_sell_quoted_upper_bound'])} | "
            f"{row['failures_after_same_step_successful_sale']} | "
            f"{row['failures_without_same_step_successful_sale']} | "
            f"≤{fmt_money(row['direct_execution_extra_receipts_ceiling'])} | "
            f"{row['successful_sell_units']} / {fmt_money(row['successful_sell_receipts'])} | "
            f"{terminal}; final shed empty={not any(row['final_shed'].values())} |"
        )
    lines.extend([
        "",
        "\\* The quoted-price sum is only the value of hypothetical units at those "
        "historical quotes. It is not forgone revenue: the candidate had zero stock "
        "of the named product when each unit was committed.",
        "",
        "‡ A generous same-turn upper bound from matching inventory already carried "
        "at a shed-access tile, not already being dropped, and still within the current "
        "SELL quantity. It assumes the action can be replaced by a deposit without "
        "opportunity cost and prices do not fall across added units. It excludes cargo "
        "farther from the shed; it is not a realized gain.",
        "",
        "† `item x/y` compares successful terminal-step unit sales with the final "
        "action's requested quantity. The last observation's carried goods are not "
        "terminal inventory if that final action deposits and sells them.",
        "",
        "## Failure signature on Boey 112939032",
        "",
    ])
    target = [row for row in rows if "boey_112939032" in row["file"]]
    if target:
        for row in target:
            by_item = ", ".join(
                f"{item}: {data['units']} units, quote-sum {fmt_money(data['quoted_value'])}"
                for item, data in sorted(row["failure_by_item"].items())
            ) or "none"
            by_step = ", ".join(
                f"t{item['step']} {item['item']}×{item['units']}"
                for item in row["failure_by_step"]
            ) or "none"
            lines.append(
                f"- Seat {row['seat']}: {row['empty_sell_attempts']} failed units "
                f"({by_item}); event steps: {by_step}. Every failure has zero own cash "
                "delta, zero item stock before/after, and unchanged market inventory. "
                f"{row['failures_after_same_step_successful_sale']} failed units came "
                "after at least one successful same-item sale by us during that same "
                f"market phase; {row['failures_without_same_step_successful_sale']} had "
                "no same-step sale before the failed unit. Pre-action carried inventory "
                "is not evidence of unsold cargo at the failure point because unit "
                "actions and successful sales happen earlier in the turn."
            )
    boey_rows = [
        row for row in rows
        if "boey_" in row["file"] and row["seat"] == 0
    ]
    if boey_rows:
        lines.extend(["", "## Immediate delivery counterfactual ceiling", ""])
        for row in boey_rows:
            recoverable = [
                detail for detail in row["failure_details"]
                if detail["immediate_extra_units_upper_bound"] > 0
            ]
            cases = "; ".join(
                f"t{detail['step']} {detail['item']} up to "
                f"{detail['immediate_extra_units_upper_bound']}×"
                f"{fmt_money(detail['quote'])}"
                for detail in recoverable
            ) or "none"
            lines.append(
                f"- Episode {row['file'].split('_')[2]}: {cases}; gross upper bound "
                f"≤{fmt_money(row['direct_execution_extra_receipts_ceiling'])} per seat. "
                "This assumes replacing the unit action with a deposit has no value or "
                "worker cost and holds price fixed; it is not a tested policy gain."
            )
        lines.append(
            "The 2026-09-24 panel consultation used roughly 4–6k/seat as a scale "
            "target for strategic changes. These single-turn local ceilings are only "
            "about 2.5–3.2% of 4k, before displaced-action cost or falling sale quotes, "
            "and below 0.7% of either Boey route's paired deficit."
        )
    lines.extend([
        "",
        "## Engine-level cause and decision",
        "",
        "In Kaggriculture 1.32.7, `_process_market` resolves each player's queued "
        "market orders in per-unit lockstep. `_commit_unit('SELL', ...)` immediately "
        "returns false when that item's shed count is zero, before changing cash, shed, "
        "or market inventory; the engine then marks that player's current order done. "
        "The other player's quoted unit still commits. Thus these failed units are not "
        "rejected sales of available stock and do not directly leak money or market "
        "supply. The table's quoted-price sum is deliberately not counted as a loss.",
        "",
        "The current policy already has a sale-lead/reservation layer. The high-value "
        "STRAWBERRY examples at steps 382 and 429 are instructive: matching carry was "
        "deposited before the market. At t382 `SELL STRAWBERRY 16` sold 8 units, then "
        "the ninth attempt failed; at t429 `SELL STRAWBERRY 12` sold 10, then the "
        "eleventh attempt failed. The goods were not stranded. On Boey 112940236 at "
        "t649, `SELL FERTILIZER 18` committed 16 units before its first empty-shed "
        "failure; later queued `BUY_PRODUCT FERTILIZER 2` and `SELL FERTILIZER 1` "
        "still committed. The queue did not lose that later execution. "
        "Across the panel, 14–21 of the Boey failed units and 9–14 on the controls follow "
        "a successful same-item sale in that same market phase. The remaining units "
        "have no stock at commit time. The per-seat upper bound for immediately "
        "reachable, not-already-delivering carry is shown in the table and assumes away "
        "the displaced worker action and any price decline; it is not realized cash. "
        "For Boey 112939032, the last pre-action carried CARROT/WHEAT/WOOL quantities "
        "are matched against actual terminal-step SELL commits in the table; the final "
        "shed is empty, so this snapshot is not unsold terminal value. No cash-scale "
        "fix is justified, so no candidate is implemented and `main.py` is unchanged.",
        "",
        "Fixed-shop reruns are unnecessary for this negative finding: no treatment "
        "changes occupancy or market actions, and the native baseline replays reproduce "
        "the frozen cash outcomes. A policy-level deferral/reordering candidate would "
        "require its own matched fixed-shop and native test before any claim.",
        "",
        "## Reproduction",
        "",
        "From the repository root, run the standalone capture and report driver:",
        "",
        "```powershell",
        "python -B -X utf8 exp_boey_sell_20260925.py --capture --report",
        "```",
        "Capture mode skips existing files and writes only missing traces under the "
        "approved diagnostic directory. The equivalent single-game CLI is `python -B "
        "-X utf8 trace_paired_game_events.py --candidate main.py --opponent "
        "'rawroute:<absolute-route-json.gz>' --seed <seed> --candidate-seat <0-or-1> "
        "--json-gz-out diagnostics\\boey_sell_20260925\\baseline_<route>_s<seat>.json.gz`.",
        "",
        "All generated trace/report files are confined to `diagnostics/boey_sell_20260925/`.",
        "",
    ])
    return "\n".join(lines)


def capture_missing_traces() -> None:
    main_path = ROOT / "main.py"
    digest = hashlib.sha256(main_path.read_bytes()).hexdigest()
    if digest != FROZEN_MAIN_SHA256:
        raise SystemExit(
            f"Refusing replay: main.py SHA-256 {digest} != frozen {FROZEN_MAIN_SHA256}"
        )
    OUT.mkdir(parents=True, exist_ok=True)
    from trace_paired_game_events import run

    for route_id, route in ROUTES.items():
        opponent_path = (
            ROOT / "diagnostics" / "top50_current_2026-09-24" / "routes"
            / route["route_file"]
        )
        if not opponent_path.is_file():
            raise SystemExit(f"Missing captured route: {opponent_path}")
        for seat in (0, 1):
            output_path = OUT / f"baseline_{route_id}_s{seat}.json.gz"
            if output_path.exists():
                print(f"skip existing {output_path.relative_to(ROOT)}")
                continue
            trace = run(
                str(main_path),
                f"rawroute:{opponent_path}",
                int(route["seed"]),
                seat,
            )
            if trace["candidate_status"] != "DONE" or trace["opponent_status"] != "DONE":
                raise RuntimeError(
                    f"Incomplete replay {route_id} seat {seat}: "
                    f"{trace['candidate_status']}/{trace['opponent_status']}"
                )
            with gzip.open(output_path, "wt", encoding="utf-8") as handle:
                json.dump(trace, handle, separators=(",", ":"))
            print(
                f"captured {route_id} seat={seat} own={trace['candidate_reward']:.0f} "
                f"rival={trace['opponent_reward']:.0f} margin={trace['margin']:+.0f} "
                f"-> {output_path.relative_to(ROOT)}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true", help="capture missing native traces")
    parser.add_argument("--report", action="store_true", help="write and print REPORT.md")
    args = parser.parse_args()
    if args.capture:
        capture_missing_traces()
    missing = []
    rows = []
    for route_id in ROUTES:
        for seat in (0, 1):
            path = OUT / f"baseline_{route_id}_s{seat}.json.gz"
            if not path.is_file():
                missing.append(str(path))
                continue
            rows.append(summarize_trace(path))
    if missing:
        raise SystemExit("Missing traces:\n" + "\n".join(missing))
    rows.sort(key=lambda row: (row["file"], row["seat"]))
    report = render_report(rows)
    if args.report:
        (OUT / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
