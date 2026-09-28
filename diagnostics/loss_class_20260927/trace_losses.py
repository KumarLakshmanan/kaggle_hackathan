"""Native replay diagnostics for all 21 4ee live losses at cutoff 17:12Z.

The current submitted file is run against each saved public opponent tape on
the original seed and seat. This measures mechanisms only; it is not policy
validation. No candidate or submission is changed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
COHORT = ROOT / "diagnostics/new_live_56609430_20260927/cohort_171158.json"
MAIN = ROOT / "main.py"
EXPECTED_MAIN_SHA256 = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
EXPECTED_LOSSES = 21
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402


def period(step: int) -> str:
    day = int(step) // 24
    return "d00_09" if day < 10 else "d10_19" if day < 20 else "d20_29"


def trace_one(game: dict) -> dict:
    episode_id = int(game["episode_id"])
    source = Path(game["replay_path"])
    raw = gzip.decompress(source.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == game["replay_sha256"], episode_id
    replay = json.loads(raw)
    assert replay["module_version"] == "1.32.7"
    assert replay["statuses"] == ["DONE", "DONE"] and len(replay["steps"]) == 720
    seat = int(game["candidate_seat"])
    rival = 1 - seat
    actions = [frame[rival].get("action") or {} for frame in replay["steps"][1:720]]
    assert len(actions) == 719
    route_dir = HERE / "routes"
    trace_dir = HERE / "traces"
    route_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)
    route_path = route_dir / f"episode-{episode_id}-seat{seat}.json.gz"
    with gzip.open(route_path, "wt", encoding="utf-8") as handle:
        json.dump({"actions": actions}, handle, separators=(",", ":"))

    data = run(str(MAIN), f"rawroute:{route_path}", int(game["seed"]), seat)
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert data["candidate_reward"] == game["own_cash"], (episode_id, data["candidate_reward"], game["own_cash"])
    assert data["opponent_reward"] == game["opponent_cash"], (episode_id, data["opponent_reward"], game["opponent_cash"])
    trace_path = trace_dir / f"episode-{episode_id}-seat{seat}-events.json.gz"
    with gzip.open(trace_path, "wt", encoding="utf-8") as handle:
        json.dump(data, handle, separators=(",", ":"))

    market = {p: {"by_item": defaultdict(float), "sale_units": Counter(),
                  "buy_product_units": Counter(), "failures": Counter()}
              for p in (seat, rival)}
    worker = {p: {"by_action": Counter(), "changed": Counter(),
                  "unchanged": Counter(), "hands_changed": Counter(),
                  "hands_unchanged": Counter()} for p in (seat, rival)}
    market_period = {p: defaultdict(float) for p in (seat, rival)}
    worker_period = {p: defaultdict(Counter) for p in (seat, rival)}
    for event in data["events"]:
        p = event.get("player")
        if p not in market:
            continue
        step = int(event["step"])
        if event["phase"] == "market_unit":
            op, item = event["operation"], event["item"]
            if event["success"]:
                delta = float(event["cash_delta"])
                if op in ("SELL", "BUY_PRODUCT"):
                    market[p]["by_item"][item] += delta
                    market_period[p][period(step)] += delta
                if op == "SELL":
                    market[p]["sale_units"][item] += 1
                elif op == "BUY_PRODUCT":
                    market[p]["buy_product_units"][item] += 1
            else:
                market[p]["failures"][f"{op}:{item}:{event.get('failure_reason')}"] += 1
        elif event["phase"] == "unit_action":
            action = event.get("action") or ["EMPTY"]
            op = str(action[0]) if action else "EMPTY"
            if op == "PASS":
                continue
            actor = int(event.get("actor", -1))
            changed = bool(event["changed"])
            worker[p]["by_action"][op] += 1
            (worker[p]["changed"] if changed else worker[p]["unchanged"])[op] += 1
            if actor >= 1:
                (worker[p]["hands_changed"] if changed else worker[p]["hands_unchanged"])[op] += 1
            worker_period[p][period(step)][("changed:" if changed else "unchanged:") + op] += 1

    def plain_counter(c):
        return dict(sorted(c.items()))

    def product_diff():
        own = market[seat]["by_item"]
        opp = market[rival]["by_item"]
        return {item: round(float(own.get(item, 0) - opp.get(item, 0)), 2)
                for item in sorted(set(own) | set(opp))}

    return {
        "episode_id": episode_id, "opponent": game["opponent"],
        "rank": int(game["opponent_snapshot_ranks"][0]["rank"]),
        "seed": int(game["seed"]), "seat": seat, "margin": float(game["margin"]),
        "candidate_reward": float(data["candidate_reward"]),
        "opponent_reward": float(data["opponent_reward"]),
        "trace_path": str(trace_path.resolve()), "route_path": str(route_path.resolve()),
        "product_net_cash_own_minus_rival": product_diff(),
        "product_net_cash_total_own": round(sum(market[seat]["by_item"].values()), 2),
        "product_net_cash_total_rival": round(sum(market[rival]["by_item"].values()), 2),
        "product_net_cash_difference": round(sum(market[seat]["by_item"].values())-
                                              sum(market[rival]["by_item"].values()), 2),
        "worker_own": {"requested": plain_counter(worker[seat]["by_action"]),
                       "changed": plain_counter(worker[seat]["changed"]),
                       "unchanged": plain_counter(worker[seat]["unchanged"]),
                       "hand_changed": plain_counter(worker[seat]["hands_changed"]),
                       "hand_unchanged": plain_counter(worker[seat]["hands_unchanged"])},
        "worker_rival": {"requested": plain_counter(worker[rival]["by_action"]),
                         "changed": plain_counter(worker[rival]["changed"]),
                         "unchanged": plain_counter(worker[rival]["unchanged"]),
                         "hand_changed": plain_counter(worker[rival]["hands_changed"]),
                         "hand_unchanged": plain_counter(worker[rival]["hands_unchanged"])},
        "worker_period_own": {k: plain_counter(v) for k, v in worker_period[seat].items()},
        "worker_period_rival": {k: plain_counter(v) for k, v in worker_period[rival].items()},
        "market_period_net_own": {k: round(v, 2) for k, v in market_period[seat].items()},
        "market_period_net_rival": {k: round(v, 2) for k, v in market_period[rival].items()},
        "market_failures_own": plain_counter(market[seat]["failures"]),
        "market_failures_rival": plain_counter(market[rival]["failures"]),
    }


def main() -> None:
    digest = hashlib.sha256(MAIN.read_bytes()).hexdigest()
    assert digest == EXPECTED_MAIN_SHA256, digest
    cohort_raw = COHORT.read_bytes()
    cohort = json.loads(cohort_raw)
    losses = [g for g in cohort["games"] if g["result"] == "loss"]
    assert len(losses) == EXPECTED_LOSSES, len(losses)
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(trace_one, losses))
    rows.sort(key=lambda row: row["episode_id"])
    output = {
        "candidate_sha256": digest,
        "cohort_sha256": hashlib.sha256(cohort_raw).hexdigest(),
        "cohort_episode_count": len(cohort["games"]),
        "loss_count": len(rows),
        "selection": "All 21 losses in cohort_171158.json; no further outcome filter.",
        "interpretation": "Exact original-seat/seed replay diagnosis only; saved opponent actions do not validate policy changes.",
        "all_cash_parity": True,
        "rows": rows,
    }
    target = HERE / "live_loss_ledgers.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target.resolve()), "losses": len(rows),
                      "cash_parity": output["all_cash_parity"],
                      "largest_product_gaps": sorted(
                          [{"team": r["opponent"], "episode": r["episode_id"],
                            "margin": r["margin"], "product_gap": r["product_net_cash_difference"],
                            "item_gaps": r["product_net_cash_own_minus_rival"]}
                           for r in rows], key=lambda x: x["product_gap"])[:6]},
                     indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
