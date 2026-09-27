"""Compact opponent actions from already downloaded public live replays."""

import gzip
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUTES = HERE / "routes"
AUDIT = HERE / "audit_latest_40.json"
OWN_NAME = "Lakshmanan R"


def main() -> None:
    episodes = json.loads(AUDIT.read_text(encoding="utf-8"))["episodes"]
    ROUTES.mkdir(parents=True, exist_ok=True)
    rows = []
    for summary in episodes:
        episode = int(summary["episode_id"])
        raw_path = HERE / f"episode-{episode}-replay.json"
        replay = json.loads(raw_path.read_text(encoding="utf-8"))
        names = replay["info"]["TeamNames"]
        assert names.count(OWN_NAME) == 1
        own_seat = names.index(OWN_NAME)
        rival_seat = 1 - own_seat
        actions = [
            frame[rival_seat].get("action")
            or {"farmer": ["PASS"], "hands": [], "market": []}
            for frame in replay["steps"][1:]
        ]
        assert len(actions) == 719
        canonical = json.dumps(actions, separators=(",", ":"), sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()
        target = ROUTES / f"episode-{episode}-rival.json.gz"
        payload = {"metadata": {"episode_id": episode, "source_seat": rival_seat,
                                "seed": int(summary["seed"]), "opponent_team": names[rival_seat],
                                "action_sha256": digest},
                   "actions": actions}
        with target.open("wb") as handle:
            with gzip.GzipFile(fileobj=handle, mode="wb", compresslevel=9, mtime=0) as packed:
                with io.TextIOWrapper(packed, encoding="utf-8") as text:
                    json.dump(payload, text, separators=(",", ":"), sort_keys=True)
        rows.append({"path": str(target.resolve()), "episode_id": episode,
                     "team": names[rival_seat], "source_seat": rival_seat,
                     "seed": int(summary["seed"]), "submission_id": 56530281,
                     "team_id": None, "action_sha256": digest,
                     "num_actions": len(actions), "live_margin": summary["margin"],
                     "our_seat": own_seat})
    output = HERE / "summary.json"
    output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print("routes", len(rows), "distinct hashes", len({r["action_sha256"] for r in rows}))
    print(output, hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
