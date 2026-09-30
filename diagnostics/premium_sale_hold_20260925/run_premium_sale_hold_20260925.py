"""Exact 1.32.7 replay harness for the premium-sale-hold investigation.

All outputs are confined to this study directory.  The baseline phase is
deliberately run before a treatment is selected; the treatment phase uses the
same raw opponent action tape and either native shop draws or the exact shop
sequence from that seat's baseline trace.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import trace_paired_game_events as trace_runner
from kaggle_environments import __version__ as ENGINE_VERSION
from kaggle_environments.envs.kaggriculture import kaggriculture as game


STUDY = Path(__file__).resolve().parent
MANIFEST = ROOT / "diagnostics" / "top50_current_2026-09-24" / "main_100routes.json"
BASE = ROOT / "main.py"
WRAPPER = ROOT / "exp_premium_sale_hold_20260925.py"
EXPECTED_ENGINE = "1.32.7"
EXPECTED_BASE_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
PRESELECTED = {
    112933589: {"stratum": "loss", "team": "Excluding", "paired_control": 112935831},
    112941285: {"stratum": "loss", "team": "ActiveMusyoku", "paired_control": 112939403},
    112935831: {"stratum": "winning_control", "team": "HowardLeeTW", "paired_loss": 112933589},
    112939403: {"stratum": "winning_control", "team": "Gleb Tumanov", "paired_loss": 112941285},
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_cohort() -> list[dict[str, Any]]:
    if ENGINE_VERSION != EXPECTED_ENGINE:
        raise RuntimeError(f"Expected Kaggriculture engine {EXPECTED_ENGINE}, got {ENGINE_VERSION}")
    if _sha256(BASE) != EXPECTED_BASE_SHA256:
        raise RuntimeError("main.py differs from the frozen 2026-09-24 baseline; refusing to benchmark")
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("engine_version") != EXPECTED_ENGINE:
        raise RuntimeError("Source benchmark manifest is not from engine 1.32.7")
    if payload.get("candidate_sha256") != EXPECTED_BASE_SHA256:
        raise RuntimeError("Source benchmark manifest does not match frozen main.py")
    source_rows = payload.get("rows", [])
    cohort = []
    for episode_id, design in PRESELECTED.items():
        matches = [
            row for row in source_rows
            if int(row.get("episode_id", -1)) == episode_id
            and row.get("team") == design["team"]
        ]
        if len(matches) != 1:
            raise RuntimeError(f"Frozen route {episode_id} missing or team mismatch")
        row = matches[0]
        path = Path(row["opponent_path"]).resolve()
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            route = json.load(stream)
        actions = route.get("actions")
        action_sha = _json_digest(actions)
        if len(actions or []) != 719 or action_sha != row["action_sha256"]:
            raise RuntimeError(f"Frozen route/action digest mismatch for episode {episode_id}")
        cohort.append(
            {
                **design,
                "episode_id": episode_id,
                "seed": int(row["seed"]),
                "route_path": str(path),
                "action_sha256": action_sha,
                "baseline_seat_results": row.get("games", []),
            }
        )
    return cohort


def _plain(value: Any) -> Any:
    return trace_runner._plain(value)


def _sum_counts(mapping: Any) -> int:
    if not isinstance(mapping, dict):
        return 0
    return sum(max(0, int(value or 0)) for value in mapping.values())


def _run_one(job: dict[str, Any]) -> dict[str, Any]:
    episode_id = int(job["episode_id"])
    seat = int(job["seat"])
    mode = str(job["mode"])
    candidate = str(BASE if mode == "baseline" else WRAPPER)
    baseline_path = STUDY / f"baseline_{episode_id}_seat{seat}.json.gz"
    shop_sequence = None
    if mode == "fixed_shop":
        if not baseline_path.is_file():
            raise FileNotFoundError(f"Need native baseline first: {baseline_path}")
        with gzip.open(baseline_path, "rt", encoding="utf-8") as stream:
            baseline = json.load(stream)
        shop_sequence = list(
            baseline["traces"][seat][-1]["observation"]["town"]["unlocked_shops"]
        )

    overflow_rows: list[dict[str, Any]] = []
    original_end_of_day = game._end_of_day
    original_make = trace_runner.make
    original_load_agent = trace_runner._load_agent
    captured_env: dict[str, Any] = {}
    captured_candidate: dict[str, Any] = {}

    def track_end_of_day(state: Any, env: Any, day: int) -> Any:
        capacity = int(env.configuration.get("shedCapacity", 100))
        for player, player_state in enumerate(state):
            observation = trace_runner._value(player_state, "observation", {}) or {}
            private = trace_runner._value(observation, "private", {}) or {}
            shed = trace_runner._value(private, "shed", {}) or {}
            inventories = trace_runner._value(private, "inventories", []) or []
            carried_by_item: dict[str, int] = {}
            for inventory in inventories:
                for item, count in (inventory or {}).items():
                    carried_by_item[str(item)] = carried_by_item.get(str(item), 0) + max(0, int(count or 0))
            shed_total = _sum_counts(shed)
            capacity_room = max(0, capacity - shed_total)
            carried_total = _sum_counts(carried_by_item)
            discarded = max(0, carried_total - capacity_room)
            if discarded:
                overflow_rows.append(
                    {
                        "day": int(day),
                        "player": int(player),
                        "units": discarded,
                        "shed_before": shed_total,
                        "carried_before": carried_total,
                        "room_before": capacity_room,
                        "carried_by_item": carried_by_item,
                    }
                )
        return original_end_of_day(state, env, day)

    def capture_make(*args: Any, **kwargs: Any) -> Any:
        env = original_make(*args, **kwargs)
        captured_env["env"] = env
        return env

    def capture_load_agent(*args: Any, **kwargs: Any) -> Any:
        loaded = original_load_agent(*args, **kwargs)
        specification = args[0] if args else kwargs.get("specification", "")
        if str(specification).lower() == str(WRAPPER).lower():
            timed = loaded[1]
            function = getattr(timed, "function", None)
            telemetry = getattr(function, "telemetry", None)
            if isinstance(telemetry, dict):
                captured_candidate["telemetry"] = telemetry
        return loaded

    game._end_of_day = track_end_of_day
    trace_runner.make = capture_make
    trace_runner._load_agent = capture_load_agent
    try:
        opponent = "rawroute:" + str(Path(job["route_path"]).resolve())
        result = trace_runner.run(
            candidate,
            opponent,
            int(job["seed"]),
            seat,
            shop_sequence=shop_sequence,
        )
        result["study_mode"] = mode
        result["episode_id"] = episode_id
        result["team"] = str(job["team"])
        result["stratum"] = str(job["stratum"])
        result["route_action_sha256"] = str(job["action_sha256"])
        result["overflow_events"] = overflow_rows
        result["terminal_inventory"] = {}

        env = captured_env.get("env")
        if env is None or not env.steps:
            raise RuntimeError("Trace runner did not expose final simulator state")
        final = env.steps[-1]
        for player, player_state in enumerate(final):
            observation = trace_runner._plain(
                trace_runner._value(player_state, "observation", {}) or {}
            )
            private = observation.get("private", {}) or {}
            farms = observation.get("farms", []) or []
            farm = farms[player] if player < len(farms) else {}
            shed = private.get("shed", {}) or {}
            inventories = private.get("inventories", []) or []
            carried: dict[str, int] = {}
            for inventory in inventories:
                for item, count in (inventory or {}).items():
                    carried[str(item)] = carried.get(str(item), 0) + max(0, int(count or 0))
            result["terminal_inventory"][str(player)] = {
                "cash": float((farm or {}).get("money", 0) or 0),
                "shed": {str(k): int(v or 0) for k, v in shed.items() if int(v or 0)},
                "carried": {k: v for k, v in carried.items() if v},
                "shed_total": _sum_counts(shed),
                "carried_total": _sum_counts(carried),
            }

        trace = result["traces"][seat]
        premium = {"STRAWBERRY", "MELON", "MILK", "WOOL"}
        sale_receipts: dict[str, float] = {}
        sale_units: dict[str, int] = {}
        for event in result["events"]:
            if (
                event.get("phase") == "market_unit"
                and int(event.get("player", -1)) == seat
                and event.get("operation") == "SELL"
                and event.get("success")
            ):
                item = str(event.get("item"))
                sale_units[item] = sale_units.get(item, 0) + 1
                sale_receipts[item] = sale_receipts.get(item, 0.0) + float(event.get("cash_delta", 0) or 0)

        max_shed = [0, 0]
        for turn in result["turns"]:
            for when in ("players_before", "players_after"):
                for row in turn.get(when, []) or []:
                    player = int(row.get("player", 0))
                    max_shed[player] = max(max_shed[player], _sum_counts(row.get("shed", {})))
        result["study_metrics"] = {
            "candidate_seat": seat,
            "own_cash": float(result["candidate_reward"]),
            "rival_cash": float(result["opponent_reward"]),
            "own_strawberry_sold": int(sale_units.get("STRAWBERRY", 0)),
            "own_strawberry_receipts": float(sale_receipts.get("STRAWBERRY", 0)),
            "own_premium_sold": {k: sale_units.get(k, 0) for k in sorted(premium)},
            "own_premium_receipts": {k: sale_receipts.get(k, 0.0) for k in sorted(premium)},
            "max_shed_units": max_shed[seat],
            "shed_capacity": int(game.specification.get("configuration", {}).get("shedCapacity", {}).get("default", 100)),
            "own_overflow_units": sum(int(row["units"]) for row in overflow_rows if int(row["player"]) == seat),
            "rival_overflow_units": sum(int(row["units"]) for row in overflow_rows if int(row["player"]) != seat),
            "own_terminal_unsold": result["terminal_inventory"][str(seat)],
            "candidate_timing": dict(result["candidate_timing"]),
            "candidate_telemetry": dict(captured_candidate.get("telemetry", {})),
            "status": [result["candidate_status"], result["opponent_status"]],
            "shop_sequence": list(trace[-1]["observation"]["town"]["unlocked_shops"]),
            "observation_steps": [int(row["step"]) for row in trace],
        }
        return result
    finally:
        game._end_of_day = original_end_of_day
        trace_runner.make = original_make
        trace_runner._load_agent = original_load_agent


def _write_gzip(path: Path, payload: Any) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing study output: {path}")
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as stream:
        json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("baseline", "fixed_shop", "native"), required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    cohort = _load_cohort()
    plan = {
        "engine_version": ENGINE_VERSION,
        "base_sha256": _sha256(BASE),
        "candidate_sha256": _sha256(WRAPPER) if WRAPPER.exists() else None,
        "preselected_cohort": cohort,
        "reason": "Loss/control pairs were selected in the existing 12-route ledger before this experiment.",
        "study_phase": args.phase,
    }
    plan_path = STUDY / "cohort_manifest.json"
    if args.phase == "baseline" and not plan_path.exists():
        plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    jobs = [
        {**route, "seat": seat, "mode": "baseline" if args.phase == "baseline" else args.phase}
        for route in cohort
        for seat in (0, 1)
    ]
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_run_one, job): job for job in jobs}
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            job = futures[future]
            result = future.result()
            episode_id = int(job["episode_id"])
            seat = int(job["seat"])
            prefix = "baseline" if args.phase == "baseline" else args.phase
            file_name = f"{prefix}_{episode_id}_seat{seat}.json.gz"
            _write_gzip(STUDY / file_name, result)
            metrics = result["study_metrics"]
            results.append(
                {
                    "episode_id": episode_id,
                    "team": job["team"],
                    "stratum": job["stratum"],
                    "seat": seat,
                    "file": file_name,
                    "engine_version": result["engine_version"],
                    "route_action_sha256": job["action_sha256"],
                    **metrics,
                }
            )
            print(
                f"[{index}/{len(jobs)}] {job['team']} e{episode_id} seat={seat} "
                f"own/rival={metrics['own_cash']:.0f}/{metrics['rival_cash']:.0f} "
                f"straw={metrics['own_strawberry_sold']} units/{metrics['own_strawberry_receipts']:.0f} "
                f"overflow={metrics['own_overflow_units']} status={metrics['status']}",
                flush=True,
            )
    results.sort(key=lambda row: (row["episode_id"], row["seat"]))
    summary = {
        "engine_version": ENGINE_VERSION,
        "base_sha256": _sha256(BASE),
        "candidate_sha256": _sha256(WRAPPER) if WRAPPER.exists() else None,
        "phase": args.phase,
        "games": len(results),
        "done_games": sum(row["status"] == ["DONE", "DONE"] for row in results),
        "results": results,
    }
    summary_path = STUDY / f"{args.phase}_summary.json"
    if summary_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing study output: {summary_path}")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
