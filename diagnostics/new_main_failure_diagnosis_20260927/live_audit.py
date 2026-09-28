"""Summarize all actual public 4ee episodes without executing rival code."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "new_live_56609430_20260927" / "raw"


def count_tiles(farm):
    result = Counter()
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                name = tile.get("crop") or tile.get("animal")
                if name:
                    result[name] += 1
    return dict(result)


def summarize_player(steps, seat):
    requested = Counter()
    worker = Counter()
    for frame in steps[1:]:
        action = frame[seat].get("action") or {}
        for order in action.get("market") or []:
            if not order:
                continue
            op = order[0]
            item = order[1] if len(order) > 1 else ""
            qty = order[2] if len(order) > 2 else 1
            requested[op + ":" + str(item)] += int(qty or 0)
        for unit in [action.get("farmer"), *(action.get("hands") or [])]:
            if unit and unit[0] != "PASS":
                worker[unit[0]] += 1
    milestones = {}
    for step in (0, 72, 144, 216, 288, 360, 432, 504, 576, 648, 719):
        obs = steps[step][seat]["observation"]
        farm = obs["farms"][seat]
        milestones[str(step)] = {
            "cash": farm["money"],
            "hands": len(farm["hands"]),
            "land": len(farm["unlocked_quadrants"]),
            "tiles": count_tiles(farm),
            "shed": {k: v for k, v in (obs.get("private", {}).get("shed") or {}).items() if v},
            "shops": obs["town"]["unlocked_shops"],
        }
    return {"requested_market_units": dict(requested),
            "worker_commands": dict(worker), "milestones": milestones}


def main():
    rows = []
    for receipt_path in sorted(RAW.glob("episode-*-receipt.json")):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if "margin" not in receipt:
            continue
        with gzip.open(receipt["replay_path"], "rt", encoding="utf-8") as fh:
            replay = json.load(fh)
        assert replay["statuses"] == ["DONE", "DONE"] and len(replay["steps"]) == 720
        seat = receipt["candidate_seat"]
        steps = replay["steps"]
        assert steps[719][seat]["reward"] == receipt["own_cash"]
        rows.append({
            "episode_id": receipt["episode_id"], "opponent": receipt["opponent"],
            "rank": receipt["opponent_snapshot_ranks"][0]["rank"] if receipt["opponent_snapshot_ranks"] else None,
            "seat": seat, "seed": receipt["seed"], "margin": receipt["margin"],
            "result": receipt["result"], "cash": [receipt["own_cash"], receipt["opponent_cash"]],
            "replay": receipt["replay_path"], "candidate": summarize_player(steps, seat),
            "opponent_state": summarize_player(steps, 1-seat),
        })
    out = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
           "submission_id": 56609430, "all_public_episodes": len(rows),
           "results": dict(Counter(r["result"] for r in rows)), "rows": rows}
    (HERE / "live_ledger.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in rows:
        if row["result"] != "loss":
            continue
        a = row["candidate"]["milestones"]
        b = row["opponent_state"]["milestones"]
        print(row["episode_id"], row["opponent"], row["margin"], "shops", a["144"]["shops"],
              "cash_margin_d6", a["144"]["cash"] - b["144"]["cash"],
              "cash_margin_d18", a["432"]["cash"] - b["432"]["cash"],
              "tiles_d6", a["144"]["tiles"], b["144"]["tiles"])


if __name__ == "__main__":
    main()
