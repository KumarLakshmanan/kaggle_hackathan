"""Freeze the 17 public rival action histories as native diagnostic routes."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "physical_sale_predictor_20260927"
ROUTES = HERE / "routes"
OUR_NAME = "Lakshmanan R"


def main() -> None:
    audit = json.loads((SOURCE / "audit_new.json").read_text(encoding="utf8"))
    assert audit["submission"] == 56572390 and len(audit["episodes"]) == 17
    ROUTES.mkdir(exist_ok=True)
    rows = []
    for live in audit["episodes"]:
        episode = int(live["episode_id"])
        replay = json.loads((SOURCE / f"episode-{episode}-replay.json").read_text(encoding="utf8"))
        names = replay["info"]["TeamNames"]
        assert names.count(OUR_NAME) == 1
        own_seat = names.index(OUR_NAME)
        rival_seat = 1-own_seat
        assert own_seat == int(live["our_seat"])
        actions = [frame[rival_seat].get("action") or
                   {"farmer": ["PASS"], "hands": [], "market": []}
                   for frame in replay["steps"][1:]]
        assert len(actions) == 719
        canonical = json.dumps(actions, separators=(",", ":"), sort_keys=True).encode("utf8")
        digest = hashlib.sha256(canonical).hexdigest()
        target = ROUTES / f"episode-{episode}-rival.json.gz"
        payload = {"metadata": {"episode_id": episode, "source_seat": rival_seat,
                                "seed": int(live["seed"]),
                                "opponent_team": names[rival_seat],
                                "action_sha256": digest},
                   "actions": actions}
        with target.open("wb") as handle:
            with gzip.GzipFile(fileobj=handle, mode="wb", compresslevel=9, mtime=0) as packed:
                with io.TextIOWrapper(packed, encoding="utf8") as stream:
                    json.dump(payload, stream, separators=(",", ":"), sort_keys=True)
        rows.append({"episode_id": episode, "seed": int(live["seed"]),
                     "team": names[rival_seat], "source_seat": rival_seat,
                     "our_seat": own_seat, "action_sha256": digest,
                     "path": str(target.resolve()), "live_margin": live["margin"],
                     "our_live_cash": live["our_cash"],
                     "rival_live_cash": live["rival_cash"],
                     "outcome": live["outcome"]})
    (ROUTES / "summary.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf8")
    print("routes", len(rows), "distinct_hashes", len({r["action_sha256"] for r in rows}))
    print("losses", sum(r["outcome"] == "loss" for r in rows))


if __name__ == "__main__":
    main()
