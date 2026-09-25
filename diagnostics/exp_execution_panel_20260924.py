"""Frozen broad-route panel for the day-28 execution experiment.

Diagnostic only.  The fixed-shop arm changes the simulator's shop draw after
each dawn; it is not a native Kaggriculture score and is never used by agents.
"""

from __future__ import annotations

import argparse
import concurrent.futures
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "diagnostics" / "replay_manifest_all_non_diag_gz_2026-09-24.json"
PANEL = ROOT / "diagnostics" / "exp_execution_panel_frozen_20260924.json"
BASE_SHA = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
FIXED_SHOPS = [
    "BAKERY", "PET_CAFE", "YARN_STORE", "PIZZA_SHOP",
    "FARMERS_MARKET", "SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT",
]
GROUPS = (
    "best_replay", "failed_replay", "ranks101-200", "ranks201-300",
    "ranks301-380", "ranks381-460", "ranks461-500", "ranks501-600",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def group_for(path: str) -> str | None:
    folder = Path(path).parent.name
    if folder == "routes" and Path(path).parent.parent.name in ("best_replay", "failed_replay"):
        return Path(path).parent.parent.name
    match = re.search(r"ranks(\d+)-(\d+)", folder)
    if match:
        lo = int(match.group(1))
        if 101 <= lo <= 200:
            return "ranks101-200"
        if 201 <= lo <= 300:
            return "ranks201-300"
        if 301 <= lo <= 380:
            return "ranks301-380"
        if 381 <= lo <= 460:
            return "ranks381-460"
        if 461 <= lo <= 500:
            return "ranks461-500"
        if 501 <= lo <= 600:
            return "ranks501-600"
    return None


def freeze() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    if source.get("candidate_sha256") != BASE_SHA or digest(ROOT / "main.py") != BASE_SHA:
        raise RuntimeError("The current main.py must match the frozen complete baseline manifest")
    executions = source["executions"]
    buckets = {group: [] for group in GROUPS}
    for route in source["routes"]:
        if route.get("status") != "ready":
            continue
        group = group_for(route["path"])
        if group is None:
            continue
        games = [executions.get(route["execution_keys"][str(seat)]) for seat in (0, 1)]
        if any(not game or game.get("candidate_status") != "DONE" or game.get("opponent_status") != "DONE" for game in games):
            continue
        row = {
            "group": group,
            "path": route["path"],
            "team": route.get("team"),
            "seed": int(route["seed"]),
            "action_sha256": route["action_sha256"],
            "raw_file_sha256": route["raw_file_sha256"],
            "baseline_seat_margins": [float(game["margin"]) for game in games],
            "baseline_pair_margin": sum(float(game["margin"]) for game in games),
        }
        row["selection_hash"] = hashlib.sha256(
            ("exp_execution_20260924:" + row["raw_file_sha256"]).encode()
        ).hexdigest()
        buckets[group].append(row)
    selected = []
    for group in GROUPS:
        rows = buckets[group]
        if len(rows) < 4:
            raise RuntimeError(f"Insufficient eligible routes in {group}: {len(rows)}")
        random_two = sorted(rows, key=lambda row: (row["selection_hash"], row["path"]))[:2]
        chosen = {row["path"] for row in random_two}
        worst_two = sorted(
            (row for row in rows if row["path"] not in chosen),
            key=lambda row: (row["baseline_pair_margin"], row["selection_hash"]),
        )[:2]
        selected.extend(random_two + worst_two)
    panel = {
        "purpose": "predeclared before experimental agent testing",
        "source": str(SOURCE),
        "source_sha256": digest(SOURCE),
        "baseline_main_sha256": BASE_SHA,
        "selection": "8 broad cohorts; per cohort 2 lowest salted SHA-256 paths plus 2 lowest remaining baseline paired margins; no experimental outcomes consulted",
        "fixed_shop_sequence": FIXED_SHOPS,
        "routes": selected,
    }
    if PANEL.exists():
        raise FileExistsError(f"Panel is already frozen: {PANEL}")
    save(PANEL, panel)
    print(f"Frozen {len(selected)} routes / {len(selected) * 2} seat games at {PANEL}")
    for row in selected:
        print(f"{row['group']:15s} {row['team']!s:24.24s} {row['seed']:10d} {row['baseline_pair_margin']:+9.0f} {Path(row['path']).name}")


def play(job: tuple[dict, int, str, str]) -> dict:
    route, seat, candidate, mode = job
    from kaggle_environments import __version__ as engine_version, make
    from kaggle_environments.envs.kaggriculture import kaggriculture as game
    from paired_benchmark import _load_agent, _reward, _status

    original_end_of_day = game._end_of_day

    def fixed_end_of_day(state, env, day):
        before = len(state[0].observation.town["unlocked_shops"])
        result = original_end_of_day(state, env, day)
        shops = state[0].observation.town["unlocked_shops"]
        if len(shops) > before and before < len(FIXED_SHOPS):
            shops[-1] = FIXED_SHOPS[before]
        return result

    candidate_agent = opponent_agent = None
    try:
        if mode == "fixed":
            game._end_of_day = fixed_end_of_day
        candidate_agent, timed_candidate = _load_agent(candidate, f"execution_{seat}_{route['seed']}")
        opponent_agent, timed_opponent = _load_agent(
            f"rawroute:{route['path']}", f"execution_raw_{1 - seat}_{route['seed']}"
        )
        agents = [candidate_agent, opponent_agent] if seat == 0 else [opponent_agent, candidate_agent]
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": route["seed"]}, debug=False)
        env.run(agents)
        final = env.steps[-1]
        own = final[seat]
        rival = final[1 - seat]
        own_reward = _reward(own)
        rival_reward = _reward(rival)
        margin = own_reward - rival_reward
        return {
            "path": route["path"], "seat": seat, "seed": route["seed"],
            "candidate_reward": own_reward, "opponent_reward": rival_reward,
            "margin": margin, "result": "W" if margin > 0 else "L" if margin < 0 else "D",
            "candidate_status": _status(own), "opponent_status": _status(rival),
            "frames": len(env.steps), "shops": list(final[0].observation.town["unlocked_shops"]),
            "telemetry": getattr(timed_candidate.function, "telemetry", None),
            "engine_version": engine_version,
        }
    finally:
        game._end_of_day = original_end_of_day
        for timed in (candidate_agent, opponent_agent):
            if timed is not None and getattr(timed, "module_name", None):
                sys.modules.pop(timed.module_name, None)


def run(candidate: Path, mode: str, output: Path, workers: int) -> None:
    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    if digest(ROOT / "main.py") != panel["baseline_main_sha256"]:
        raise RuntimeError("Baseline main.py changed after panel freeze")
    candidate = candidate.resolve()
    candidate_sha = digest(candidate)
    if output.exists():
        report = json.loads(output.read_text(encoding="utf-8"))
        if report["candidate_sha256"] != candidate_sha or report["mode"] != mode:
            raise RuntimeError("Existing report identity mismatch")
    else:
        report = {
            "panel": str(PANEL), "panel_sha256": digest(PANEL),
            "candidate": str(candidate), "candidate_sha256": candidate_sha,
            "mode": mode, "fixed_shop_sequence": FIXED_SHOPS if mode == "fixed" else None,
            "results": {},
        }
    jobs = [(row, seat, str(candidate), mode) for row in panel["routes"] for seat in (0, 1)
            if f"{row['path']}|{seat}" not in report["results"]]
    print(f"Running {len(jobs)} pending / {len(panel['routes']) * 2} total: {candidate.name} {mode}", flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            key = f"{result['path']}|{result['seat']}"
            report["results"][key] = result
            save(output, report)
            print(f"[{index}/{len(jobs)}] {result['result']} {result['margin']:+.0f} seat={result['seat']} {Path(result['path']).name}", flush=True)
    print(f"Report {output} ({len(report['results'])} games)")


def summarize() -> None:
    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    summary = {
        "panel": str(PANEL),
        "panel_sha256": digest(PANEL),
        "baseline_main_sha256": BASE_SHA,
        "experimental_sha256": digest(ROOT / "exp_agent_execution_20260924.py"),
        "modes": {},
    }
    for mode in ("native", "fixed"):
        base_path = ROOT / "diagnostics" / f"exp_execution_{mode}_baseline_20260924.json"
        test_path = ROOT / "diagnostics" / f"exp_execution_{mode}_treatment_20260924.json"
        base = json.loads(base_path.read_text(encoding="utf-8"))
        test = json.loads(test_path.read_text(encoding="utf-8"))
        if base["panel_sha256"] != summary["panel_sha256"] or test["panel_sha256"] != summary["panel_sha256"]:
            raise RuntimeError("Panel mismatch between paired arms")
        if base["candidate_sha256"] != BASE_SHA or test["candidate_sha256"] != summary["experimental_sha256"]:
            raise RuntimeError("Candidate hash mismatch between paired arms")
        paired = []
        for route in panel["routes"]:
            for seat in (0, 1):
                key = f"{route['path']}|{seat}"
                a = base["results"][key]
                b = test["results"][key]
                if any(row["candidate_status"] != "DONE" or row["opponent_status"] != "DONE" or row["frames"] != 720 for row in (a, b)):
                    raise RuntimeError(f"Incomplete game {key} {mode}")
                paired.append({
                    "group": route["group"], "team": route["team"],
                    "path": route["path"], "seat": seat,
                    "base_result": a["result"], "test_result": b["result"],
                    "base_margin": a["margin"], "test_margin": b["margin"],
                    "margin_delta": b["margin"] - a["margin"],
                    "own_cash_delta": b["candidate_reward"] - a["candidate_reward"],
                    "rival_cash_delta": b["opponent_reward"] - a["opponent_reward"],
                    "same_shops": a["shops"] == b["shops"],
                    "shops_base": a["shops"], "shops_test": b["shops"],
                    "late_care_candidates": (b.get("telemetry") or {}).get("late_care_candidates", 0),
                    "late_care_replaced": (b.get("telemetry") or {}).get("late_care_replaced", 0),
                    "late_care_storage_skips": (b.get("telemetry") or {}).get("late_care_storage_skips", 0),
                    "late_care_duplicate_skips": (b.get("telemetry") or {}).get("late_care_duplicate_skips", 0),
                    "late_care_errors": (b.get("telemetry") or {}).get("late_care_errors", 0),
                })
        route_rows = []
        for route in panel["routes"]:
            seats = [row for row in paired if row["path"] == route["path"]]
            a = sum(row["base_margin"] for row in seats)
            b = sum(row["test_margin"] for row in seats)
            route_rows.append({
                "group": route["group"], "team": route["team"], "path": route["path"],
                "base_result": "W" if a > 0 else "L" if a < 0 else "D",
                "test_result": "W" if b > 0 else "L" if b < 0 else "D",
                "base_pair_margin": a, "test_pair_margin": b,
                "pair_margin_delta": b - a,
            })
        deltas = [row["margin_delta"] for row in paired]
        grouped = defaultdict(list)
        for row in paired:
            grouped[row["group"]].append(row["margin_delta"])
        summary["modes"][mode] = {
            "games": len(paired), "routes": len(route_rows),
            "base_game_results": dict(Counter(row["base_result"] for row in paired)),
            "test_game_results": dict(Counter(row["test_result"] for row in paired)),
            "game_transitions": {f"{a}->{b}": n for (a, b), n in Counter((row["base_result"], row["test_result"]) for row in paired).items()},
            "route_transitions": {f"{a}->{b}": n for (a, b), n in Counter((row["base_result"], row["test_result"]) for row in route_rows).items()},
            "positive_margin_games": sum(n > 0 for n in deltas),
            "negative_margin_games": sum(n < 0 for n in deltas),
            "unchanged_margin_games": sum(n == 0 for n in deltas),
            "mean_margin_delta": statistics.fmean(deltas),
            "median_margin_delta": statistics.median(deltas),
            "min_margin_delta": min(deltas), "max_margin_delta": max(deltas),
            "total_own_cash_delta": sum(row["own_cash_delta"] for row in paired),
            "total_rival_cash_delta": sum(row["rival_cash_delta"] for row in paired),
            "different_shop_paths": sum(not row["same_shops"] for row in paired),
            "fixed_shop_paths_valid": all(row["shops_base"] == FIXED_SHOPS and row["shops_test"] == FIXED_SHOPS for row in paired) if mode == "fixed" else None,
            "late_care_candidates": sum(row["late_care_candidates"] for row in paired),
            "late_care_replaced": sum(row["late_care_replaced"] for row in paired),
            "late_care_storage_skips": sum(row["late_care_storage_skips"] for row in paired),
            "late_care_duplicate_skips": sum(row["late_care_duplicate_skips"] for row in paired),
            "late_care_errors": sum(row["late_care_errors"] for row in paired),
            "group_mean_margin_deltas": {group: statistics.fmean(values) for group, values in grouped.items()},
            "games_with_flips": [row for row in paired if row["base_result"] != row["test_result"]],
            "worst_five": sorted(paired, key=lambda row: row["margin_delta"])[:5],
            "best_five": sorted(paired, key=lambda row: row["margin_delta"], reverse=True)[:5],
        }
    out = ROOT / "diagnostics" / "exp_execution_summary_20260924.json"
    save(out, summary)
    for mode, result in summary["modes"].items():
        print(mode, json.dumps({key: value for key, value in result.items() if key not in ("games_with_flips", "worst_five", "best_five")}, ensure_ascii=False))
    print(f"Summary {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--mode", choices=("native", "fixed"), default="native")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.freeze:
        freeze()
    elif args.summarize:
        summarize()
    else:
        if args.candidate is None or args.output is None:
            parser.error("--candidate and --output are required to run")
        run(args.candidate, args.mode, args.output, args.workers)
