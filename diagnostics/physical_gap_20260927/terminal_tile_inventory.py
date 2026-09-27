"""Read-only terminal tile-yield audit of the frozen 100 live replays."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "live_submission_56572390_20260926"
OUT = Path(__file__).with_name("terminal_tile_inventory.json")


def inventory(board):
    result = Counter()
    for row in board:
        for tile in row:
            if isinstance(tile, dict) and int(tile.get("yield_units", 0)) > 0:
                item = tile.get("crop") or tile.get("animal")
                if item:
                    result[item] += int(tile["yield_units"])
    return dict(result)


def main():
    audit = json.loads((ROOT / "audit_latest_100.json").read_text(encoding="utf-8"))
    rows = []
    for episode in audit["episodes"]:
        if episode["outcome"] != "loss":
            continue
        path = ROOT / f"episode-{episode['episode_id']}-replay.json"
        if not path.exists():
            raise FileNotFoundError(path)
        replay = json.loads(path.read_text(encoding="utf-8"))
        seat = int(episode["our_seat"])
        obs = replay["steps"][-1][seat]["observation"]
        own = obs["farms"][seat]
        rival = obs["farms"][1 - seat]
        rows.append({
            "episode_id": episode["episode_id"],
            "opponent": episode["opponent"],
            "margin": episode["margin"],
            "own_tile_yield": inventory(own["tiles"]),
            "rival_tile_yield": inventory(rival["tiles"]),
        })
    own_total = Counter()
    rival_total = Counter()
    for row in rows:
        own_total.update(row["own_tile_yield"])
        rival_total.update(row["rival_tile_yield"])
    result = {
        "source": str(ROOT / "audit_latest_100.json"),
        "losses": len(rows),
        "losses_with_own_yield": sum(bool(r["own_tile_yield"]) for r in rows),
        "own_total": dict(own_total),
        "rival_total": dict(rival_total),
        "rows": rows,
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    print(f"wrote={OUT}")


if __name__ == "__main__":
    main()
