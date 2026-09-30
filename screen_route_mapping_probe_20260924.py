"""Screen existing route IDs on one saved replay, then require held-out testing.

This is an offline development tool.  It never inserts the replay seed, team,
or future shop sequence into the agent policy.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import gzip
import importlib.util
import json
from pathlib import Path

from paired_benchmark import run_game
from trace_paired_game_events import run as run_fixed_shop_game


def _route_ids() -> list[int]:
    spec = importlib.util.spec_from_file_location("route_screen_agent", "exp_route_mapping_probe_20260924.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load probe agent")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return sorted(module._BASE._IMPL.chassis.routes)


def _play(job: tuple[str, str, int, int, int, list[str] | None]) -> dict:
    candidate, opponent, seed, seat, route_id, shop_sequence = job
    try:
        if shop_sequence is None:
            result = run_game(
                candidate=candidate,
                opponent=opponent,
                seed=seed,
                candidate_seat=seat,
                debug=False,
                capture_step=None,
                candidate_overrides={"_TEST_ROUTE_ID": route_id},
            )
        else:
            result = run_fixed_shop_game(
                candidate=candidate, opponent=opponent, seed=seed,
                candidate_seat=seat,
                candidate_overrides={"_TEST_ROUTE_ID": route_id},
                shop_sequence=shop_sequence,
            )
        return {
            "route_id": route_id,
            "seat": seat,
            "margin": result["margin"],
            "candidate_status": result["candidate_status"],
            "opponent_status": result["opponent_status"],
            "candidate_reward": result["candidate_reward"],
            "opponent_reward": result["opponent_reward"],
        }
    except Exception as error:
        return {"route_id": route_id, "seat": seat, "error": repr(error)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--shop-sequence-from", type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    args = parser.parse_args()

    matches = [row for row in json.loads(args.summary.read_text(encoding="utf-8"))
               if int(row["seed"]) == args.seed]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one route for seed {args.seed}, found {len(matches)}")
    opponent = "rawroute:" + str(Path(matches[0]["path"]).resolve())
    candidate = str(Path("exp_route_mapping_probe_20260924.py").resolve())
    shop_sequence = None
    if args.shop_sequence_from is not None:
        with gzip.open(args.shop_sequence_from, "rt", encoding="utf-8") as handle:
            baseline = json.load(handle)
        if int(baseline["seed"]) != args.seed or int(baseline["candidate_seat"]) != args.seat:
            raise ValueError("Fixed-shop source must match the screened seed and seat")
        shop_sequence = list(baseline["traces"][args.seat][-1]["observation"]
                             ["town"]["unlocked_shops"])
    jobs = [(candidate, opponent, args.seed, args.seat, route_id, shop_sequence)
            for route_id in _route_ids()]
    rows = []
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(_play, job) for job in jobs]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(f"route={row['route_id']} seat={row['seat']} "
                  f"margin={row.get('margin')} error={row.get('error')}", flush=True)
    rows.sort(key=lambda row: row["route_id"])
    args.json_out.write_text(json.dumps({
        "seed": args.seed, "seat": args.seat,
        "opponent_path": matches[0]["path"],
        "source_action_sha256": matches[0]["action_sha256"],
        "shop_sequence_from": str(args.shop_sequence_from) if args.shop_sequence_from else None,
        "candidate": candidate, "rows": rows,
    }, indent=2), encoding="utf-8")
    ranked = [row for row in rows if row.get("candidate_status") == "DONE"
              and row.get("opponent_status") == "DONE"]
    ranked.sort(key=lambda row: float(row["margin"]), reverse=True)
    print("TOP " + json.dumps(ranked[:12]))


if __name__ == "__main__":
    main()
