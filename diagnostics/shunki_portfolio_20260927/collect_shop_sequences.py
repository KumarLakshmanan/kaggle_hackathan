"""Extract verified public shop reveal sequences from frozen source replays."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SAMPLE = HERE.parent / "public_route_native_screen_20260927" / "shunki_replays"
INCOMING = HERE / "incoming"
REVEAL_STEPS = (72, 144, 216, 288, 360, 432, 504, 576, 648)
TEAM = "ShunkiKyoya"


def collect(row: dict) -> dict:
    episode = row["episode_id"]
    sample = SAMPLE / f"episode-{episode}-replay.json"
    if sample.is_file() and sample.stat().st_size:
        path = sample
    else:
        INCOMING.mkdir(exist_ok=True)
        path = INCOMING / f"episode-{episode}-replay.json"
        if not path.is_file() or not path.stat().st_size:
            last_error = ""
            for _ in range(3):
                result = subprocess.run(
                    [sys.executable, "-m", "kaggle", "competitions", "replay",
                     str(episode), "-p", str(INCOMING), "-q"],
                    capture_output=True, text=True, encoding="utf8", errors="replace")
                last_error = result.stderr[:400]
                if result.returncode == 0 and path.is_file() and path.stat().st_size:
                    break
            else:
                raise RuntimeError(f"Replay {episode} unavailable: {last_error}")
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row["replay_sha256"], episode
    replay = json.loads(raw)
    seat = replay["info"]["TeamNames"].index(TEAM)
    assert seat == row["source_seat"]
    assert replay["statuses"] == ["DONE", "DONE"]
    steps = replay["steps"]
    reveals = {str(t): list(steps[t][seat]["observation"]["town"]["unlocked_shops"])
               for t in REVEAL_STEPS}
    assert reveals["144"][:2] == row["shops_day6"]
    if path.resolve().parent == INCOMING.resolve():
        path.unlink()
    return {"episode_id": episode, "source_seat": seat,
            "seed": row["seed"], "replay_sha256": row["replay_sha256"],
            "reveals": reveals}


def main() -> None:
    manifest_path = HERE / "route_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["total"] == 203
    partial = HERE / "shop_sequences_partial.json"
    rows_by_id = {}
    if partial.is_file():
        previous = json.loads(partial.read_text(encoding="utf8"))
        assert previous["manifest_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
        rows_by_id = {row["episode_id"]: row for row in previous["rows"]}
    source_rows = manifest["rows"]
    remaining = [row for row in source_rows if row["episode_id"] not in rows_by_id]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(collect, row): row["episode_id"] for row in remaining}
        for future in as_completed(futures):
            row = future.result()
            rows_by_id[row["episode_id"]] = row
            if len(rows_by_id) % 10 == 0 or len(rows_by_id) == 203:
                ordered = [rows_by_id[source["episode_id"]] for source in source_rows
                           if source["episode_id"] in rows_by_id]
                partial.write_text(json.dumps({
                    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                    "rows": ordered}, ensure_ascii=False, indent=2), encoding="utf8")
                print(f"shop sequences {len(rows_by_id)}/203", flush=True)
    ordered = [rows_by_id[source["episode_id"]] for source in source_rows]
    (HERE / "shop_sequences.json").write_text(json.dumps({
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "rows": ordered}, ensure_ascii=False, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
