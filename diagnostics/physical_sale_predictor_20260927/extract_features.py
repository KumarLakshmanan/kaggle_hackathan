"""Add current public harvest/worker geometry to the frozen sale opportunities."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.multigood_sale_race_20260927 import extract_dataset as previous  # noqa: E402

OLD = HERE.parent / "multigood_sale_race_20260927" / "opportunities.json"
NEW_AUDIT = HERE / "audit_new.json"
OUTPUT = HERE / "physical_opportunities.json"
ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
SHED = ((4, 4), (5, 4), (4, 5), (5, 5))


def distance(a, b) -> int:
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))


def physical(obs: dict, seat: int, item: str) -> dict[str, int]:
    rival = obs["farms"][1 - seat]
    workers = [rival["farmer"], *(rival.get("hands") or [])]
    ready = []
    producers = []
    for y, line in enumerate(rival.get("tiles") or []):
        for x, tile in enumerate(line):
            if not isinstance(tile, dict):
                continue
            product = tile.get("crop") or ANIMAL_PRODUCT.get(tile.get("animal"))
            if item == "FERTILIZER":
                if tile.get("animal") in ANIMAL_PRODUCT:
                    producers.append((x, y))
                    if tile.get("fertilizer_available"):
                        ready.append(((x, y), 1))
            elif product == item:
                producers.append((x, y))
                units = max(0, int(tile.get("yield_units", 0) or 0))
                if units:
                    ready.append(((x, y), units))
    worker_positions = {tuple(worker) for worker in workers}
    ready_units = sum(units for _, units in ready)
    ready_worker_units = sum(units for pos, units in ready if pos in worker_positions)
    worker_distance = min((distance(w, pos) for w in workers for pos, _ in ready), default=10)
    shed_distance = min((distance(pos, s) for pos, _ in ready for s in SHED), default=10)
    producer_positions = set(producers)
    return {
        "rival_ready_units": ready_units,
        "rival_ready_tiles": len(ready),
        "rival_worker_on_ready_units": ready_worker_units,
        "rival_worker_min_ready_distance": min(10, worker_distance),
        "rival_workers_on_item_tiles": sum(tuple(w) in producer_positions for w in workers),
        "rival_workers_near_shed": sum(min(distance(w, s) for s in SHED) <= 1 for w in workers),
        "rival_shed_min_ready_distance": min(10, shed_distance),
    }


def enrich(rows: list[dict], replay_dir: Path, seat_by_id: dict[int, int]) -> None:
    by_episode = defaultdict(list)
    for row in rows:
        by_episode[int(row["episode_id"])].append(row)
    for index, (episode, group) in enumerate(by_episode.items(), 1):
        replay = json.loads((replay_dir / f"episode-{episode}-replay.json").read_text(encoding="utf8"))
        steps = replay["steps"]
        seat = seat_by_id[episode]
        for row in group:
            step = int(row["step"])
            obs = steps[step][seat]["observation"]
            assert int(obs["player"]) == seat
            row["features"].update(physical(obs, seat, row["features"]["item"]))
        if index % 20 == 0:
            print("enriched episodes", index, flush=True)


def main() -> None:
    old_payload = json.loads(OLD.read_text(encoding="utf8"))
    new_audit = json.loads(NEW_AUDIT.read_text(encoding="utf8"))
    assert old_payload["episodes"] == 100 and len(new_audit["episodes"]) == 17
    old_audit_path = HERE.parent / "live_submission_56572390_20260926" / "audit_latest_100.json"
    old_audit = json.loads(old_audit_path.read_text(encoding="utf8"))
    assert hashlib.sha256(old_audit_path.read_bytes()).hexdigest() == old_payload["audit_sha256"]
    old_rows = old_payload["rows"]
    for row in old_rows:
        row["train"] = True
    old_seats = {int(row["episode_id"]): int(row["our_seat"]) for row in old_audit["episodes"]}
    enrich(old_rows, old_audit_path.parent, old_seats)
    old_ids = set(old_seats)
    assert len(old_ids) == 100
    # Reuse the exact frozen opportunity/label extractor; only its file root
    # is rebound to the newly downloaded, nonoverlapping public replays.
    previous.LIVE = HERE
    new_rows = []
    for entry in new_audit["episodes"]:
        new_rows.extend(previous.extract(entry, set()))
    new_seats = {int(row["episode_id"]): int(row["our_seat"]) for row in new_audit["episodes"]}
    assert not (old_ids & set(new_seats)) and len(new_seats) == 17
    enrich(new_rows, HERE, new_seats)
    labels = Counter(("train" if row["train"] else "holdout", row["rival_before_own"])
                     for row in [*old_rows, *new_rows])
    positives = Counter(row["features"]["item"] for row in new_rows if row["rival_before_own"])
    positive_episodes = {row["episode_id"] for row in new_rows if row["rival_before_own"]}
    summary = {
        "labels": {f"{split}_{label}": n for (split, label), n in sorted(labels.items())},
        "holdout_positive_episodes": len(positive_episodes),
        "holdout_positive_items": dict(sorted(positives.items())),
        "data_gate": (labels[("holdout", 1)] >= 100 and len(positive_episodes) >= 10
                      and sum(n >= 10 for n in positives.values()) >= 2),
    }
    payload = {"old_opportunities_sha256": hashlib.sha256(OLD.read_bytes()).hexdigest(),
               "new_audit_sha256": hashlib.sha256(NEW_AUDIT.read_bytes()).hexdigest(),
               "development_episodes": 100, "holdout_episodes": 17,
               "summary": summary, "rows": [*old_rows, *new_rows]}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
