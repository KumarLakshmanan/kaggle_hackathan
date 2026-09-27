"""Exact native event ledgers for the two lost refreshed top-20 routes."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "diagnostics" / "live_refresh_56530281_20260926"))

from trace_paired_game_events import run  # noqa: E402
from cash_ledger_close import ledger  # noqa: E402

SOURCE = ROOT / "main.py"
EXPECTED_SHA = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
PANEL = HERE / "main_20routes.json"
OUTPUT = HERE / "two_loss_ledgers.json"


def farm_counts(farm: dict) -> dict:
    counts = Counter()
    for line in farm["tiles"]:
        for tile in line:
            if isinstance(tile, dict):
                kind = tile.get("crop") or tile.get("animal")
                if kind:
                    counts[kind] += 1
    return dict(counts)


def play(job: tuple[dict, dict]) -> dict:
    route, expected = job
    data = run(candidate=str(SOURCE), opponent=f"rawroute:{route['path']}",
               seed=int(route["seed"]), candidate_seat=0)
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert (data["candidate_reward"], data["opponent_reward"]) == (
        expected["candidate_reward"], expected["opponent_reward"]), route["team"]
    own, rival = ledger(data, 0), ledger(data, 1)
    items = sorted(set(own["net_market_by_item"]) | set(rival["net_market_by_item"]))
    differences = {item: own["net_market_by_item"].get(item, 0)
                   - rival["net_market_by_item"].get(item, 0) for item in items}
    atomic = sum(own["atomic_cash"].values()) - sum(rival["atomic_cash"].values())
    other = own["other_cash"] - rival["other_cash"]
    assert abs(sum(differences.values()) + atomic + other - data["margin"]) < 1e-6
    checkpoints = []
    for day in (6, 12, 18, 24, 29):
        obs = data["traces"][0][day * 24]["observation"]
        checkpoints.append({"day": day,
                            "shops": obs["town"]["unlocked_shops"],
                            "own_money": obs["farms"][0]["money"],
                            "rival_money": obs["farms"][1]["money"],
                            "own_counts": farm_counts(obs["farms"][0]),
                            "rival_counts": farm_counts(obs["farms"][1]),
                            "own_hands": len(obs["farms"][0]["hands"]),
                            "rival_hands": len(obs["farms"][1]["hands"])})
    trace_path = HERE / f"{route['team'].replace(' ', '_')}_trace_s0.json.gz"
    with gzip.open(trace_path, "wt", encoding="utf8", compresslevel=6) as handle:
        json.dump(data, handle, separators=(",", ":"), ensure_ascii=False)
    return {"team": route["team"], "seed": route["seed"],
            "episode_id": route["episode_id"], "source_seat": route["source_seat"],
            "action_sha256": route["action_sha256"],
            "margin": data["margin"], "own_cash": data["candidate_reward"],
            "rival_cash": data["opponent_reward"], "net_item_differences": differences,
            "sale_unit_differences": {item: own["sale_units"].get(item, 0)
                                      - rival["sale_units"].get(item, 0) for item in items},
            "own_sale_units": own["sale_units"], "rival_sale_units": rival["sale_units"],
            "own_atomic_cash": own["atomic_cash"],
            "rival_atomic_cash": rival["atomic_cash"],
            "atomic_difference": atomic, "other_difference": other,
            "checkpoints": checkpoints, "trace_path": str(trace_path)}


def main() -> None:
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA
    panel = json.loads(PANEL.read_text(encoding="utf8"))
    jobs = []
    for route in panel["routes"]:
        if route["team"] not in ("Boey", "DECEM"):
            continue
        expected = panel["executions"][route["execution_keys"]["0"]]
        jobs.append((route, expected))
    assert len(jobs) == 2
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(play, jobs))
    OUTPUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf8")
    for row in rows:
        print(row["team"], row["margin"],
              sorted(row["net_item_differences"].items(), key=lambda kv: kv[1])[:5],
              row["checkpoints"][0]["shops"])
    print(OUTPUT)


if __name__ == "__main__":
    main()
