"""Exact native transaction ledger for every fresh-panel lost route, seat 0."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
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
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
LOSSES = HERE / "main_loss_manifest.json"
PANEL = HERE / "main_100routes.json"
OUTPUT = HERE / "all34_loss_ledgers_s0.json"
CACHE = HERE / "loss_ledgers_s0"


def cache_path(case: dict) -> Path:
    return CACHE / f"{case['episode_id']}-{case['action_sha256'][:12]}.json"


def play(job: tuple[dict, dict]) -> dict:
    case, expected = job
    data = run(candidate=str(SOURCE), opponent=f"rawroute:{case['opponent_path']}",
               seed=int(case["seed"]), candidate_seat=0)
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert (data["candidate_reward"], data["opponent_reward"]) == (
        expected["candidate_reward"], expected["opponent_reward"]), case["team"]
    own = ledger(data, 0)
    rival = ledger(data, 1)
    items = sorted(set(own["net_market_by_item"]) | set(rival["net_market_by_item"]))
    differences = {item: own["net_market_by_item"].get(item, 0)
                   - rival["net_market_by_item"].get(item, 0) for item in items}
    atomic = sum(own["atomic_cash"].values()) - sum(rival["atomic_cash"].values())
    other = own["other_cash"] - rival["other_cash"]
    assert abs(sum(differences.values()) + atomic + other - data["margin"]) < 1e-6
    row = {
        "rank": case["rank"], "team": case["team"], "seed": case["seed"],
        "episode_id": case["episode_id"], "shops_at_day6": case["shops_at_day6"],
        "action_sha256": case["action_sha256"],
        "margin": data["margin"], "own_cash": data["candidate_reward"],
        "rival_cash": data["opponent_reward"],
        "physical_mirror_turns": case["physical_mirror_turns"],
        "net_item_differences": differences,
        "sale_receipt_differences": {
            item: own["sale_cash"].get(item, 0) - rival["sale_cash"].get(item, 0)
            for item in items},
        "sale_unit_differences": {
            item: own["sale_units"].get(item, 0) - rival["sale_units"].get(item, 0)
            for item in items},
        "buy_cost_differences": {
            key: own["buy_cost"].get(key, 0) - rival["buy_cost"].get(key, 0)
            for key in sorted(set(own["buy_cost"]) | set(rival["buy_cost"]))},
        "atomic_cash_differences": {
            key: own["atomic_cash"].get(key, 0) - rival["atomic_cash"].get(key, 0)
            for key in sorted(set(own["atomic_cash"]) | set(rival["atomic_cash"]))},
        "other_cash_difference": other,
    }
    cache_path(case).write_text(json.dumps(row, ensure_ascii=False), encoding="utf8")
    return row


def main() -> None:
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    losses = json.loads(LOSSES.read_text(encoding="utf8"))
    panel = json.loads(PANEL.read_text(encoding="utf8"))
    expected = {(group["action_sha256"], int(group["seed"]), int(group["source_seat"])):
                next(game for game in group["games"] if game["candidate_seat"] == 0)
                for group in panel["rows"]}
    assert len(losses) == 34
    CACHE.mkdir(exist_ok=True)
    missing = [case for case in losses if not cache_path(case).is_file()]
    with ProcessPoolExecutor(max_workers=3) as pool:
        list(pool.map(play, [(case, expected[(case["action_sha256"], int(case["seed"]),
                                             int(case["source_seat"]))]) for case in missing]))
    rows = [json.loads(cache_path(case).read_text(encoding="utf8")) for case in losses]
    total = Counter()
    negative_count = Counter()
    for row in rows:
        for item, value in row["net_item_differences"].items():
            total[item] += value
            negative_count[item] += value < 0
    summary = {
        "routes": len(rows),
        "all_margin_negative": all(row["margin"] < 0 for row in rows),
        "item_net_cash_differences_total": dict(total),
        "routes_with_negative_item_difference": dict(negative_count),
        "atomic_cash_difference_total": sum(
            sum(row["atomic_cash_differences"].values()) for row in rows),
        "total_margin": sum(row["margin"] for row in rows),
    }
    OUTPUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2,
                                 ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
