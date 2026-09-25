"""Turn downloaded live replays into reproducible, fixed-opponent test routes."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROUTES = HERE / "routes"
OUR_NAME = "Lakshmanan R"


def main() -> None:
    ROUTES.mkdir(exist_ok=True)
    summary = []
    for replay_path in sorted(HERE.glob("episode-*-replay.json")):
        with replay_path.open(encoding="utf-8") as stream:
            replay = json.load(stream)
        names = replay["info"]["TeamNames"]
        if names.count(OUR_NAME) != 1:
            raise ValueError(f"Unexpected team names in {replay_path}: {names}")
        our_seat = names.index(OUR_NAME)
        source_seat = 1 - our_seat
        actions = [step[source_seat].get("action") or {} for step in replay["steps"][1:]]
        if len(actions) != 719:
            raise ValueError(f"Unexpected action count in {replay_path}: {len(actions)}")
        episode_id = int(replay["info"]["EpisodeId"])
        seed = int(replay["info"]["seed"])
        route = {
            "actions": actions,
            "metadata": {
                "episode_id": episode_id,
                "team": names[source_seat],
                "source_seat": source_seat,
                "seed": seed,
            },
        }
        action_bytes = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()
        route_path = ROUTES / f"opponent-{episode_id}.json.gz"
        if route_path.is_file():
            with gzip.open(route_path, "rt", encoding="utf-8") as stream:
                if json.load(stream) != route:
                    raise RuntimeError(f"Existing route changed: {route_path}")
        else:
            with gzip.open(route_path, "wt", encoding="utf-8", compresslevel=6) as stream:
                json.dump(route, stream, separators=(",", ":"))
        summary.append({
            "episode_id": episode_id,
            "team": names[source_seat],
            "seed": seed,
            "source_seat": source_seat,
            "our_live_seat": our_seat,
            "our_live_cash": replay["rewards"][our_seat],
            "rival_live_cash": replay["rewards"][source_seat],
            "action_sha256": hashlib.sha256(action_bytes).hexdigest(),
            "path": str(route_path),
        })
        print(f"extracted {episode_id}: {names[source_seat]}")
    output = ROUTES / "summary.json"
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(summary)} routes to {output}")


if __name__ == "__main__":
    main()
