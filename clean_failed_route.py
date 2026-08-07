"""Extract an opponent route and remove replay-specific weed repair scars.

The submitted agent remains plain Python.  This utility only prepares research
route data: when a replay action DIGs a tile that the observation proves is a
WEED, the following shifted actions reveal the intended principal variation.
Those actions are shifted back so future games repair only weeds that actually
exist in their own state.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path


def actor_action(action: dict, actor_index: int) -> list:
    if actor_index == 0:
        return list(action.get("farmer") or ["PASS"])
    hands = list(action.get("hands") or [])
    index = actor_index - 1
    return list(hands[index] if index < len(hands) else ["PASS"])


def set_actor_action(action: dict, actor_index: int, value: list) -> None:
    if actor_index == 0:
        action["farmer"] = list(value)
        return
    hands = list(action.get("hands") or [])
    index = actor_index - 1
    while len(hands) <= index:
        hands.append(["PASS"])
    hands[index] = list(value)
    action["hands"] = hands


def tile_at(farm: dict, position: list) -> object:
    try:
        return farm["tiles"][int(position[1])][int(position[0])]
    except (IndexError, KeyError, TypeError, ValueError):
        return None


def clean(replay_path: Path, own_team: str, destination: Path) -> dict:
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    names = list(replay.get("info", {}).get("TeamNames", []))
    own_seat = names.index(own_team)
    opponent_seat = 1 - own_seat
    actions = [
        copy.deepcopy(frame[opponent_seat].get("action"))
        or {"farmer": ["PASS"], "hands": [], "market": []}
        for frame in replay["steps"][1:]
    ]
    cleaned = copy.deepcopy(actions)
    repairs = []

    for step, action in enumerate(actions):
        if step + 3 >= len(actions):
            break
        observation = replay["steps"][step][opponent_seat]["observation"]
        farm = observation["farms"][opponent_seat]
        positions = [farm.get("farmer"), *list(farm.get("hands") or [])]
        for actor_index, position in enumerate(positions):
            order = actor_action(action, actor_index)
            tile = tile_at(farm, position)
            if not order or order[0] != "DIG":
                continue
            if not isinstance(tile, dict) or tile.get("kind") != "WEED":
                continue
            intended = []
            for offset in range(3):
                recovered = actor_action(actions[step + 1 + offset], actor_index)
                set_actor_action(cleaned[step + offset], actor_index, recovered)
                intended.append(recovered)
            repairs.append(
                {
                    "step": step,
                    "actor_index": actor_index,
                    "position": position,
                    "restored_actions": intended,
                }
            )

    canonical = json.dumps(cleaned, separators=(",", ":"), sort_keys=True).encode("utf-8")
    metadata = {
        "source_replay": replay_path.name,
        "episode_id": int(replay_path.stem),
        "seed": replay.get("info", {}).get("seed"),
        "opponent_team": names[opponent_seat],
        "engine_version": replay.get("module_version"),
        "action_count": len(cleaned),
        "action_sha256": hashlib.sha256(canonical).hexdigest(),
        "weed_repairs_removed": repairs,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
            with io.TextIOWrapper(gz, encoding="utf-8") as text:
                json.dump(
                    {"metadata": metadata, "actions": cleaned},
                    text,
                    separators=(",", ":"),
                    sort_keys=True,
                )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("replay", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--own-team", default="Lakshmanan R")
    args = parser.parse_args()
    metadata = clean(args.replay.resolve(), args.own_team, args.destination.resolve())
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
