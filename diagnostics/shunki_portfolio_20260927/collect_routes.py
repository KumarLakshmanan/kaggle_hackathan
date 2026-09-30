"""Stream exact public replay actions into compact route artifacts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SAMPLE = HERE.parent / "public_route_native_screen_20260927" / "shunki_replays"
LISTING = HERE.parent / "public_route_native_screen_20260927" / "shunki_episodes.json"
INCOMING = HERE / "incoming"
ROUTES = HERE / "routes"
TEAM = "ShunkiKyoya"
SUBMISSION = 56553856


def digest(actions: list) -> str:
    raw = json.dumps(actions, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf8")
    return hashlib.sha256(raw).hexdigest()


def fetch_and_extract(episode: int) -> dict:
    INCOMING.mkdir(exist_ok=True)
    ROUTES.mkdir(exist_ok=True)
    sample = SAMPLE / f"episode-{episode}-replay.json"
    temporary = INCOMING / f"episode-{episode}-replay.json"
    if sample.is_file() and sample.stat().st_size:
        path = sample
        remove_after = False
    else:
        path = temporary
        remove_after = not path.exists()
        if not path.is_file() or path.stat().st_size == 0:
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
    replay_hash = hashlib.sha256(raw).hexdigest()
    replay = json.loads(raw)
    names = replay["info"]["TeamNames"]
    assert names.count(TEAM) == 1, (episode, names)
    seat = names.index(TEAM)
    assert replay["statuses"] == ["DONE", "DONE"], (episode, replay["statuses"])
    steps = replay["steps"]
    actions = [(frame[seat].get("action") or {}) for frame in steps[1:]]
    assert len(actions) == 719
    shops = list(steps[144][seat]["observation"]["town"]["unlocked_shops"][:2])
    assert len(shops) == 2
    route = {"actions": actions,
             "metadata": {"submission_id": SUBMISSION, "episode_id": episode,
                          "source_seat": seat, "seed": replay["info"]["seed"],
                          "shops_day6": shops, "replay_sha256": replay_hash}}
    route_path = ROUTES / f"episode-{episode}-route.json.gz"
    with gzip.open(route_path, "wt", encoding="utf8", compresslevel=9) as handle:
        json.dump(route, handle, ensure_ascii=False, separators=(",", ":"))
    with gzip.open(route_path, "rt", encoding="utf8") as handle:
        verified = json.load(handle)
    assert verified == route
    if remove_after:
        assert path.resolve().parent == INCOMING.resolve()
        path.unlink()
    return {"episode_id": episode, "source_seat": seat,
            "seed": replay["info"]["seed"], "shops_day6": shops,
            "action_sha256": digest(actions),
            "prefix_72_sha256": digest(actions[:72]),
            "prefix_144_sha256": digest(actions[:144]),
            "replay_sha256": replay_hash,
            "route_path": str(route_path.resolve()),
            "route_bytes": route_path.stat().st_size}


def main() -> None:
    text = LISTING.read_text(encoding="utf-8-sig")
    listing, _ = json.JSONDecoder().raw_decode(text)
    selected = [int(row["id"]) for row in listing
                if row["state"] == "EpisodeState.COMPLETED"
                and row["type"] == "EpisodeType.EPISODE_TYPE_PUBLIC"]
    assert len(selected) == 203 and len(set(selected)) == 203
    rows_by_id = {}
    partial = HERE / "collection_partial.json"
    if partial.exists():
        previous = json.loads(partial.read_text(encoding="utf8"))
        assert previous["submission"] == SUBMISSION
        rows_by_id = {int(row["episode_id"]): row for row in previous["rows"]}
    remaining = [episode for episode in selected if episode not in rows_by_id]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_and_extract, episode): episode for episode in remaining}
        for future in as_completed(futures):
            row = future.result()
            rows_by_id[int(row["episode_id"])] = row
            if len(rows_by_id) % 10 == 0 or len(rows_by_id) == len(selected):
                rows = [rows_by_id[episode] for episode in selected if episode in rows_by_id]
                partial.write_text(json.dumps({"submission": SUBMISSION,
                                               "selected_ids": selected,
                                               "rows": rows}, ensure_ascii=False, indent=2),
                                   encoding="utf8")
                print(f"extracted {len(rows_by_id)}/{len(selected)}", flush=True)
    rows = [rows_by_id[episode] for episode in selected]
    by_pair = {}
    by_first = {}
    for row in rows:
        pair = tuple(row["shops_day6"])
        by_pair.setdefault(pair, []).append(row)
        by_first.setdefault(pair[0], []).append(row)
    conflicts = [{"shops": list(pair), "action_hashes": sorted({row["action_sha256"] for row in group}),
                  "episodes": [row["episode_id"] for row in group]}
                 for pair, group in by_pair.items()
                 if len({row["action_sha256"] for row in group}) > 1]
    first_conflicts = [{"first_shop": shop,
                        "prefix_144_hashes": sorted({row["prefix_144_sha256"] for row in group})}
                       for shop, group in by_first.items()
                       if len({row["prefix_144_sha256"] for row in group}) > 1]
    result = {"submission": SUBMISSION,
              "listing_sha256": hashlib.sha256(LISTING.read_bytes()).hexdigest(),
              "selected_ids": selected,
              "total": len(rows),
              "distinct_first_shops": len(by_first),
              "distinct_shop_pairs": len(by_pair),
              "distinct_first_72_prefixes": len({row["prefix_72_sha256"] for row in rows}),
              "first_shop_prefix_conflicts": first_conflicts,
              "same_pair_action_conflicts": conflicts,
              "pair_counts": [{"shops": list(pair), "episodes": len(group),
                               "action_hashes": len({row["action_sha256"] for row in group})}
                              for pair, group in sorted(by_pair.items())],
              "rows": rows}
    (HERE / "route_manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print({key: result[key] for key in ("total", "distinct_first_shops",
                                         "distinct_shop_pairs", "distinct_first_72_prefixes")}, flush=True)
    print("first_shop_conflicts", len(first_conflicts),
          "same_pair_conflicts", len(conflicts), flush=True)


if __name__ == "__main__":
    main()
