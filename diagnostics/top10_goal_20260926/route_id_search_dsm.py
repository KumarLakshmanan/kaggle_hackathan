"""Screen every complete native route on DSM's saved original-shop loss."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

CANDIDATE = ROOT / "exp_route_probe_20260926.py"
ROUTE = ROOT / "diagnostics/top100_refresh_2026-09-26" / (
    "DSM-submission-56557996-episode-113531265-seat1.json.gz")
OUTPUT = Path(__file__).with_name("route_id_search_dsm.json")
SEED = 1681313608


def play(route_id: int) -> dict:
    row = run_game(str(CANDIDATE), f"rawroute:{ROUTE}", SEED, 0, False,
                   None, {"_ROUTE_PROBE_ID": route_id})
    return {
        "route_id": route_id,
        "margin": row["margin"],
        "own_cash": row["candidate_reward"],
        "rival_cash": row["opponent_reward"],
        "status": [row["candidate_status"], row["opponent_status"]],
        "max_call_ms": row["candidate_timing"]["max_ms"],
    }


def main() -> None:
    spec = importlib.util.spec_from_file_location("route_probe_listing", CANDIDATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    route_ids = sorted(module._IMPL.chassis.routes)
    rows = []
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(play, route_id): route_id for route_id in route_ids}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(row["route_id"], f"{row['margin']:+.0f}", row["status"], flush=True)
    rows.sort(key=lambda row: row["route_id"])
    assert len(rows) == len(route_ids)
    OUTPUT.write_text(json.dumps({
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "opponent_sha256": hashlib.sha256(ROUTE.read_bytes()).hexdigest(),
        "seed": SEED, "seat": 0, "shop_pair": ["BRUNCH_SPOT", "YARN_STORE"],
        "rows": rows,
    }, indent=2), encoding="utf8")
    print("best", [(r["route_id"], r["margin"]) for r in
                   sorted(rows, key=lambda r: -r["margin"])[:10]], flush=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
