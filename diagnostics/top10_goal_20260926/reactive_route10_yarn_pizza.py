"""Reactive screen of route 10 on previously selected Yarn/Pizza seeds."""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

HERE = Path(__file__).resolve().parent
CANDIDATE = ROOT / "exp_route_probe_20260926.py"
MAIN = ROOT / "main.py"
SEED_FILE = HERE / "native_yarn_pizza_reverse_seeds.json"
OUTPUT = HERE / "reactive_route10_yarn_pizza.json"


def play(job):
    seed, seat = job
    row = run_game(str(CANDIDATE), str(MAIN), seed, seat, False, 144,
                   {"_ROUTE_PROBE_ID": 10,
                    "_ROUTE_PROBE_SHOPS": ["YARN_STORE", "PIZZA_SHOP"]})
    capture = row.pop("candidate_capture")
    return {
        "seed": seed, "seat": seat,
        "shops": capture["shops"] if capture else None,
        "own_cash": row["candidate_reward"],
        "rival_cash": row["opponent_reward"],
        "margin": row["margin"],
        "statuses": [row["candidate_status"], row["opponent_status"]],
    }


def main():
    seeds = json.loads(SEED_FILE.read_text(encoding="utf8"))["selected"]
    jobs = [(seed, seat) for seed in seeds for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    summary = {
        "wins": sum(row["margin"] > 0 for row in rows),
        "losses": sum(row["margin"] < 0 for row in rows),
        "margin_sum": sum(row["margin"] for row in rows),
        "own_cash_sum": sum(row["own_cash"] for row in rows),
        "rival_cash_sum": sum(row["rival_cash"] for row in rows),
        "all_done": all(row["statuses"] == ["DONE", "DONE"] for row in rows),
        "shop_matches": sum(row["shops"] == ["YARN_STORE", "PIZZA_SHOP"] for row in rows),
    }
    OUTPUT.write_text(json.dumps({
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "main_sha256": hashlib.sha256(MAIN.read_bytes()).hexdigest(),
        "seeds": seeds, "summary": summary, "rows": rows,
    }, indent=2), encoding="utf8")
    for row in rows:
        print(row["seed"], row["seat"], f"{row['margin']:+.0f}", row["shops"], flush=True)
    print(summary)
    print(OUTPUT)


if __name__ == "__main__":
    main()
