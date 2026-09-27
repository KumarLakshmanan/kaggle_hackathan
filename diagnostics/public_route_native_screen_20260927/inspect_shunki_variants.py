"""Read-only sample of one opponent's public action schedules."""

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
REPLAYS = HERE / "shunki_replays"
TEAM = "ShunkiKyoya"
SUBMISSION = 56553856


def digest(actions: list) -> str:
    return hashlib.sha256(json.dumps(actions, sort_keys=True,
                                    separators=(",", ":"), ensure_ascii=False).encode("utf8")).hexdigest()


def download(episode: int) -> Path:
    REPLAYS.mkdir(exist_ok=True)
    path = REPLAYS / f"episode-{episode}-replay.json"
    if not path.is_file() or path.stat().st_size == 0:
        result = subprocess.run([sys.executable, "-m", "kaggle", "competitions",
                                 "replay", str(episode), "-p", str(REPLAYS), "-q"],
                                capture_output=True, text=True, encoding="utf8", errors="replace")
        if result.returncode:
            raise RuntimeError(f"Replay {episode}: {result.stderr[:500]}")
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Replay {episode} unavailable")
    return path


def profile(path: Path) -> dict:
    replay = json.loads(path.read_text(encoding="utf8"))
    names = replay["info"]["TeamNames"]
    assert names.count(TEAM) == 1, names
    seat = names.index(TEAM)
    steps = replay["steps"]
    actions = [(frame[seat].get("action") or {}) for frame in steps[1:]]
    assert len(actions) == 719
    obs = steps[144][seat]["observation"]
    return {"episode_id": int(path.stem.split("-")[1]), "source_seat": seat,
            "names": names, "shops_day6": obs["town"]["unlocked_shops"][:2],
            "action_sha256": digest(actions),
            "prefix_144_sha256": digest(actions[:144]),
            "prefix_72_sha256": digest(actions[:72]),
            "actions": actions}


def main() -> None:
    listing_text = (HERE / "shunki_episodes.json").read_text(encoding="utf-8-sig")
    listing, _ = json.JSONDecoder().raw_decode(listing_text)
    public = [row for row in listing if row["state"] == "EpisodeState.COMPLETED"
              and row["type"] == "EpisodeType.EPISODE_TYPE_PUBLIC"]
    selected = [int(row["id"]) for row in public[:12]]
    assert len(selected) == 12
    ready = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download, episode): episode for episode in selected}
        for future in as_completed(futures):
            episode = futures[future]
            ready[episode] = future.result()
            print("ready", episode, ready[episode].stat().st_size, flush=True)
    profiles = [profile(ready[episode]) for episode in selected]
    source_manifest = json.loads((ROOT / "diagnostics" / "top10_goal_20260926" /
                                  "double_yarn_highsheep_4routes_summary.json").read_text(encoding="utf8"))
    source = next(row for row in source_manifest if row["team"] == TEAM)
    with gzip.open(source["path"], "rt", encoding="utf8") as handle:
        reference = json.load(handle)["actions"]
    ref_prefix = digest(reference[:144])
    ref72 = digest(reference[:72])
    rows = []
    for p in profiles:
        actions = p.pop("actions")
        common = 0
        for old, new in zip(reference, actions):
            if old != new:
                break
            common += 1
        p["common_action_prefix_with_double_yarn_source"] = common
        rows.append(p)
    result = {"submission": SUBMISSION, "team": TEAM,
              "selected_episode_ids": selected,
              "reference_action_sha256": source["action_sha256"],
              "reference_prefix_144_sha256": ref_prefix,
              "reference_prefix_72_sha256": ref72,
              "distinct_144_prefixes": len({row["prefix_144_sha256"] for row in rows}),
              "distinct_72_prefixes": len({row["prefix_72_sha256"] for row in rows}),
              "distinct_shop_pairs": len({tuple(row["shops_day6"]) for row in rows}),
              "rows": rows}
    (HERE / "shunki_sample_profile.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print({key: result[key] for key in ("distinct_144_prefixes", "distinct_72_prefixes",
                                         "distinct_shop_pairs")}, flush=True)
    for row in rows:
        print(row["episode_id"], row["shops_day6"],
              row["common_action_prefix_with_double_yarn_source"],
              row["prefix_144_sha256"][:10], flush=True)


if __name__ == "__main__":
    main()
