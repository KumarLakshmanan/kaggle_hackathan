"""Build a compact feature table for the downloaded top-player replay panel.

The raw replay corpus is large.  This utility deliberately loads one replay,
extracts only the opponent-state snapshots an online agent can observe early
in a game, and then releases the replay before moving to the next file.
"""

from __future__ import annotations

import collections
import gc
import json
from pathlib import Path
from typing import Any


ROOT = Path("top20_replays")
SUMMARY = Path("top20_routes_all_2026-09-21/summary.json")
HOZUMA_REPORT = Path("benchmark_force_hozuma_all_v1327.json")
QQ_REPORT = Path("benchmark_force_qq_all_v1327.json")
OUT = Path("route_tape_features_2026-09-21.json")
SNAPSHOT_STEPS = (1, 2, 3, 5, 10, 20, 73)
TILE_FIELDS = (
    "kind_PASTURE",
    "kind_PLANT",
    "kind_COOP",
    "kind_WEED",
    "crop_CARROT",
    "crop_STRAWBERRY",
    "crop_MELON",
    "crop_WHEAT",
    "animal_SHEEP",
    "animal_COW",
)


def _tile_counts(farm: dict[str, Any]) -> collections.Counter[str]:
    counts: collections.Counter[str] = collections.Counter()
    for row in farm.get("tiles", []) or []:
        if not isinstance(row, list):
            continue
        for tile in row:
            if not isinstance(tile, dict):
                continue
            for field in ("kind", "crop", "animal"):
                value = tile.get(field)
                if value:
                    counts[f"{field}_{str(value).upper()}"] += 1
    return counts


def _snapshot(replay: dict[str, Any], seat: int) -> list[float]:
    values: list[float] = []
    for step in SNAPSHOT_STEPS:
        frame = replay["steps"][step][seat]
        farm = frame["observation"]["farms"][seat]
        counts = _tile_counts(farm)
        values.extend(
            [
                float(farm.get("money", 0) or 0),
                float(len(farm.get("hands", []) or [])),
                float(farm.get("hires_today", 0) or 0),
            ]
        )
        values.extend(float(counts.get(field, 0)) for field in TILE_FIELDS)
    return values


def main() -> None:
    entries = json.loads(SUMMARY.read_text(encoding="utf-8"))
    hozuma = json.loads(HOZUMA_REPORT.read_text(encoding="utf-8"))
    qq = json.loads(QQ_REPORT.read_text(encoding="utf-8"))
    h_by_hash = {row["action_sha256"]: row for row in hozuma["rows"]}
    q_by_hash = {row["action_sha256"]: row for row in qq["rows"]}

    by_replay: dict[Path, list[dict[str, Any]]] = collections.defaultdict(list)
    for entry in entries:
        if entry["action_sha256"] in h_by_hash and entry["action_sha256"] in q_by_hash:
            by_replay[ROOT / entry["source"] / entry["file"]].append(entry)

    output: list[dict[str, Any]] = []
    total = len(by_replay)
    for index, (path, replay_entries) in enumerate(sorted(by_replay.items()), 1):
        replay = json.loads(path.read_text(encoding="utf-8"))
        for entry in replay_entries:
            digest = entry["action_sha256"]
            h = h_by_hash[digest]
            q = q_by_hash[digest]
            output.append(
                {
                    "action_sha256": digest,
                    "episode_id": int(entry["episode_id"]),
                    "team": entry["team"],
                    "source": entry["source"],
                    "source_seat": int(entry["source_seat"]),
                    "features": _snapshot(replay, int(entry["source_seat"])),
                    "hozuma_pair_margin": float(h["pair_margin"]),
                    "qq_pair_margin": float(q["pair_margin"]),
                }
            )
        del replay
        if index % 10 == 0 or index == total:
            print(f"processed {index}/{total}", flush=True)
        if index % 20 == 0:
            gc.collect()

    output.sort(key=lambda row: row["action_sha256"])
    OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(output), "replays": total, "output": str(OUT.resolve())}))


if __name__ == "__main__":
    main()
