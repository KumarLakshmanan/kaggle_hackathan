"""Read-only collection of recent public Matt Motoki action schedules."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent / "matt_route_family"
KAGGLE = Path(r"C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe")
EPISODES = (
    113590912, 113588519, 113587547, 113587690,
    113581344, 113577828, 113576724, 113571925,
)


def digest(actions: list[dict]) -> str:
    return hashlib.sha256(json.dumps(actions, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def fetch(episode: int) -> dict:
    replay_path = HERE / f"episode-{episode}-replay.json"
    if not replay_path.is_file() or replay_path.stat().st_size == 0:
        result = subprocess.run(
            [str(KAGGLE), "competitions", "replay", str(episode),
             "-p", str(HERE), "-q"],
            text=True, encoding="utf8", capture_output=True, check=True,
        )
        if not replay_path.is_file() or replay_path.stat().st_size == 0:
            raise RuntimeError(f"Replay {episode} is not ready: {result.stdout} {result.stderr}")
    replay = json.loads(replay_path.read_text(encoding="utf8"))
    names = replay["info"]["TeamNames"]
    seats = [i for i, name in enumerate(names) if name == "Matt Motoki"]
    if len(seats) != 1:
        raise ValueError(f"Expected Matt Motoki once: {episode} {names}")
    seat = seats[0]
    actions = [frame[seat].get("action") or {"farmer": ["PASS"],
                                               "hands": [], "market": []}
               for frame in replay["steps"][1:]]
    if len(actions) != 719:
        raise ValueError(f"Unexpected action count: {episode} {len(actions)}")
    shops = []
    for day in range(30):
        obs = replay["steps"][day * 24][seat]["observation"]
        shops.append(list(obs["town"]["unlocked_shops"]))
    metadata = {
        "episode_id": episode, "seed": int(replay["info"]["seed"]),
        "team": names[seat], "source_seat": seat,
        "opponent": names[1-seat], "reward": replay["rewards"][seat],
        "opponent_reward": replay["rewards"][1-seat],
        "action_sha256": digest(actions),
        "opening_24_sha256": digest(actions[:24]),
        "opening_96_sha256": digest(actions[:96]),
        "opening_144_sha256": digest(actions[:144]),
        "first_two_shops": shops[6][:2], "shops_by_day": shops,
    }
    route_path = HERE / f"episode-{episode}-seat{seat}.json.gz"
    with route_path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf8") as stream:
                json.dump({"metadata": metadata, "actions": actions}, stream,
                          separators=(",", ":"), sort_keys=True)
    metadata["route_path"] = str(route_path.resolve())
    return metadata


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(fetch, EPISODES))
    output = HERE / "summary.json"
    output.write_text(json.dumps(rows, indent=2, ensure_ascii=False),
                      encoding="utf8")
    for row in rows:
        print(row["episode_id"], row["first_two_shops"],
              row["opening_24_sha256"][:8],
              row["opening_96_sha256"][:8],
              row["action_sha256"][:8],
              row["reward"], row["opponent_reward"])
    print(output)


if __name__ == "__main__":
    main()
