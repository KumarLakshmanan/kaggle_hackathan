"""Freeze public rival actions for all recent losses and ten closest wins."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUTES = HERE / "mirror_dev_routes"
AUDIT = HERE / "audit_latest_100.json"
OWN_NAME = "Lakshmanan R"


def main() -> None:
    episodes = json.loads(AUDIT.read_text(encoding="utf8"))["episodes"]
    losses = [row for row in episodes if row["outcome"] == "loss"]
    wins = sorted((row for row in episodes if row["outcome"] == "win"),
                  key=lambda row: (row["margin"], row["episode_id"]))[:10]
    assert len(losses) == 29 and len(wins) == 10
    selected = losses + wins
    ROUTES.mkdir(parents=True, exist_ok=True)
    rows = []
    for live in selected:
        episode_id = int(live["episode_id"])
        replay = json.loads((HERE / f"episode-{episode_id}-replay.json").read_text(encoding="utf8"))
        names = replay["info"]["TeamNames"]
        assert names.count(OWN_NAME) == 1
        own_seat = names.index(OWN_NAME)
        rival_seat = 1 - own_seat
        assert own_seat == live["our_seat"]
        actions = [frame[rival_seat].get("action") or
                   {"farmer": ["PASS"], "hands": [], "market": []}
                   for frame in replay["steps"][1:]]
        assert len(actions) == 719
        canonical = json.dumps(actions, separators=(",", ":"), sort_keys=True).encode("utf8")
        digest = hashlib.sha256(canonical).hexdigest()
        target = ROUTES / f"episode-{episode_id}-rival.json.gz"
        payload = {"metadata": {"episode_id": episode_id, "source_seat": rival_seat,
                                "seed": int(live["seed"]), "opponent_team": names[rival_seat],
                                "action_sha256": digest}, "actions": actions}
        with target.open("wb") as handle:
            with gzip.GzipFile(fileobj=handle, mode="wb", compresslevel=9, mtime=0) as packed:
                with io.TextIOWrapper(packed, encoding="utf8") as stream:
                    json.dump(payload, stream, separators=(",", ":"), sort_keys=True)
        rows.append({"path": str(target.resolve()), "episode_id": episode_id,
                     "team": names[rival_seat], "source_seat": rival_seat,
                     "seed": int(live["seed"]), "action_sha256": digest,
                     "num_actions": len(actions), "live_margin": live["margin"],
                     "our_live_cash": live["our_cash"],
                     "rival_live_cash": live["rival_cash"],
                     "our_live_seat": own_seat,
                     "screen_class": live["outcome"]})
        print(episode_id, live["outcome"], live["margin"], flush=True)
    output = ROUTES / "summary.json"
    output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf8")
    print("routes", len(rows), "distinct hashes", len({r["action_sha256"] for r in rows}))
    print(output, hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
