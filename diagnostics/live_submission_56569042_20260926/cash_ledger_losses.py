"""Replay three close live losses and account for executed terminal cash."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "diagnostics" / "live_refresh_56530281_20260926"))

from trace_paired_game_events import run  # noqa: E402
from cash_ledger_close import ledger  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, default=HERE / "audit_latest_24.json")
    parser.add_argument("--episodes", type=int, nargs="*")
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf8"))
    selected = set(args.episodes or [])
    results = []
    for live in audit["episodes"]:
        if live["outcome"] != "loss" or (selected and live["episode_id"] not in selected):
            continue
        episode = int(live["episode_id"])
        seat = int(live["our_seat"])
        route = HERE / "loss_routes" / f"episode-{episode}-seat{1-seat}.json.gz"
        data = run(
            candidate=str(ROOT / "main.py"), opponent=f"rawroute:{route}",
            seed=int(live["seed"]), candidate_seat=seat,
        )
        assert data["candidate_status"] == data["opponent_status"] == "DONE"
        assert (data["candidate_reward"], data["opponent_reward"]) == (
            live["our_cash"], live["rival_cash"]
        ), episode
        ours = ledger(data, seat)
        rival = ledger(data, 1-seat)
        items = sorted(set(ours["net_market_by_item"]) | set(rival["net_market_by_item"]))
        differences = {
            item: ours["net_market_by_item"].get(item, 0)
            - rival["net_market_by_item"].get(item, 0)
            for item in items
        }
        atomic = sum(ours["atomic_cash"].values()) - sum(rival["atomic_cash"].values())
        other = ours["other_cash"] - rival["other_cash"]
        assert abs(sum(differences.values()) + atomic + other - live["margin"]) < 1e-6
        results.append({
            "episode_id": episode, "opponent": live["opponent"],
            "seed": live["seed"], "our_seat": seat, "margin": live["margin"],
            "ours": ours, "rival": rival, "net_item_differences": differences,
            "atomic_cash_difference": atomic, "other_cash_difference": other,
        })
        print(episode, live["opponent"], live["margin"],
              sorted(differences.items(), key=lambda row: row[1])[:5], flush=True)
    suffix = "selected" if selected else "all"
    output = HERE / f"cash_ledger_losses_{len(audit['episodes'])}_{suffix}.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf8")
    print(output)


if __name__ == "__main__":
    main()
