"""Check installed simulator parity with the actual submitted agent's episodes.

This extracts the observed opponent commands from each public Kaggle replay and
replays them against the frozen local main.py at the public episode seed. It is
a deterministic harness check, not a reactive-opponent performance estimate.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from paired_benchmark import run_game


HERE = Path(__file__).resolve().parent
MAIN = HERE.parent.parent / "main.py"
EXPECTED_MAIN_SHA = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"


def main():
    if hashlib.sha256(MAIN.read_bytes()).hexdigest() != EXPECTED_MAIN_SHA:
        raise RuntimeError("main.py changed since this submission; parity not comparable")
    paths = sorted(HERE.glob("episode-*-replay.json"))
    if not paths:
        raise RuntimeError("No saved public episodes found")
    failed = False
    for path in paths:
        replay = json.loads(path.read_text(encoding="utf-8-sig"))
        names = replay["info"]["TeamNames"]
        if len(names) != 2 or names.count("Lakshmanan R") != 1:
            raise RuntimeError(f"Unexpected team labels in {path.name}: {names}")
        our_seat = names.index("Lakshmanan R")
        rival_seat = 1 - our_seat
        if replay.get("module_version") != "1.32.7":
            raise RuntimeError(f"Different simulator version in {path.name}")
        actions = [step[rival_seat].get("action") or {} for step in replay["steps"][1:]]
        if len(actions) != 719:
            raise RuntimeError(f"Unexpected route length in {path.name}")
        seed = int(replay["info"]["seed"])
        route_path = HERE / f"opponent-{path.stem.replace('episode-', '').replace('-replay', '')}.json.gz"
        route = {
            "actions": actions,
            "metadata": {
                "episode_id": replay["info"]["EpisodeId"],
                "team": names[rival_seat],
                "source_seat": rival_seat,
                "seed": seed,
            },
        }
        if route_path.exists():
            with gzip.open(route_path, "rt", encoding="utf-8") as stream:
                if json.load(stream) != route:
                    raise RuntimeError(f"Existing extracted route differs: {route_path}")
        else:
            with gzip.open(route_path, "wt", encoding="utf-8", compresslevel=9) as stream:
                json.dump(route, stream, separators=(",", ":"))
        local = run_game(
            candidate=str(MAIN),
            opponent=f"rawroute:{route_path}",
            seed=seed,
            candidate_seat=our_seat,
            debug=False,
            capture_step=None,
            candidate_overrides={},
        )
        final = replay["steps"][-1]
        expected = (
            float(final[our_seat]["reward"]),
            float(final[rival_seat]["reward"]),
            final[our_seat]["status"],
            final[rival_seat]["status"],
        )
        actual = (
            local["candidate_reward"],
            local["opponent_reward"],
            local["candidate_status"],
            local["opponent_status"],
        )
        equal = actual == expected
        failed |= not equal
        print({
            "episode": replay["info"]["EpisodeId"],
            "seed": seed,
            "rival": names[rival_seat],
            "actual": actual,
            "expected": expected,
            "exact_parity": equal,
        }, flush=True)
    if failed:
        raise SystemExit("At least one Kaggle-vs-local replay outcome disagreed")


if __name__ == "__main__":
    main()
