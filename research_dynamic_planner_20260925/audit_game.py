"""Run a real-engine game with compact production and failed-action evidence."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_agent, _timing_dict
from kaggle_environments import make, __version__
from kaggle_environments.envs.kaggriculture import kaggriculture as engine


def counts(farm):
    result = Counter()
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                result[tile.get("crop", tile.get("animal", tile["kind"]))] += 1
    return dict(result)


def run(candidate, opponent, seed, seat, output, overrides=None):
    agent, timed = _load_agent(str(candidate), "dynamic_audit", overrides=overrides)
    rival, rival_timed = _load_agent(opponent, "rival_audit")
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=True)
    success, failed = Counter(), Counter()
    failures, daily = [], []
    losses = {"plants_died": 0, "animals_escaped": 0, "discarded_inventory": 0}
    original = engine._apply_unit_action
    original_plants = engine._daily_refresh_plants
    original_animals = engine._daily_refresh_animals
    original_drop = engine._drop_inventories_to_shed
    original_commit = engine._commit_unit
    receipts, spending, sold, bought = Counter(), Counter(), Counter(), Counter()

    # The framework deep-copies interpreter state, so object identity against
    # env.state is not a valid player test. Engine unit and refresh order is
    # player 0 then player 1; each unit group starts with farmer index zero.
    counters = {"unit_player": -1, "plants": -1, "animals": -1, "drop": -1, "step": 0}

    def apply(farm, private, idx, action, *args, **kwargs):
        if idx == 0:
            counters["unit_player"] = (counters["unit_player"]+1) % 2
        active = counters["unit_player"] == seat
        if active:
            counters["private"] = private
        if active:
            pos = tuple(engine._farmer_position(farm, idx))
            before = (pos, deepcopy(farm["tiles"][pos[1]][pos[0]]),
                      dict(private["inventories"][idx]), dict(private["shed"]), dict(private["seeds"]))
        result = original(farm, private, idx, action, *args, **kwargs)
        if active:
            newpos = tuple(engine._farmer_position(farm, idx))
            after = (newpos, deepcopy(farm["tiles"][pos[1]][pos[0]]),
                     dict(private["inventories"][idx]), dict(private["shed"]), dict(private["seeds"]))
            op = action[0] if action else "PASS"
            if before == after and op != "PASS":
                failed[op] += 1
                if len(failures) < 50:
                    failures.append({"step": counters["step"],
                                     "worker": idx, "pos": pos, "action": action,
                                     "tile": before[1], "inventory": before[2]})
            elif before != after:
                success[op] += 1
        return result

    def refresh_plants(farm, *args):
        counters["plants"] = (counters["plants"]+1) % 2
        active = counters["plants"] == seat
        before = counts(farm) if active else {}
        result = original_plants(farm, *args)
        if active:
            after = counts(farm)
            losses["plants_died"] += sum(max(0, before.get(k, 0)-after.get(k, 0)) for k in engine.CROPS)
        return result

    def refresh_animals(farm, *args):
        counters["animals"] = (counters["animals"]+1) % 2
        active = counters["animals"] == seat
        before = counts(farm) if active else {}
        result = original_animals(farm, *args)
        if active:
            after = counts(farm)
            losses["animals_escaped"] += sum(max(0, before.get(k, 0)-after.get(k, 0)) for k in engine.ANIMALS)
        return result

    def drop(private, capacity):
        counters["drop"] = (counters["drop"]+1) % 2
        active = counters["drop"] == seat
        total = sum(private["shed"].values()) + sum(sum(i.values()) for i in private["inventories"])
        if active:
            losses["discarded_inventory"] += max(0, total-capacity)
        return original_drop(private, capacity)

    def wrapped(obs, cfg):
        counters["step"] = int(obs.get("step", 0))
        action = agent(obs, cfg)
        if obs.get("hour", 0) == 0:
            state = timed.function.__globals__.get("_STATES", {}).get(seat)
            daily.append({"day": obs["day"], "money": obs["farms"][seat]["money"],
                          "counts": counts(obs["farms"][seat]),
                          "rival_money": obs["farms"][1-seat]["money"],
                          "rival_counts": counts(obs["farms"][1-seat]),
                          "shed": dict(obs["private"]["shed"]),
                          "prices": dict(obs["market"]["prices"]),
                          "project_scores": {k: v.get("score") for k, v in getattr(state, "values", {}).items()},
                          "shops": list(obs["town"]["unlocked_shops"])})
        return action

    def commit(op, item, quoted, farm, private, market, *args, **kwargs):
        before = farm["money"]
        result = original_commit(op, item, quoted, farm, private, market, *args, **kwargs)
        if private is counters.get("private"):
            change = farm["money"]-before
            if change > 0:
                receipts[item] += change
                sold[item] += 1
            elif change < 0:
                spending[item] -= change
                bought[item] += 1
        return result

    engine._apply_unit_action = apply
    engine._daily_refresh_plants = refresh_plants
    engine._daily_refresh_animals = refresh_animals
    engine._drop_inventories_to_shed = drop
    engine._commit_unit = commit
    try:
        env.run([wrapped, rival] if seat == 0 else [rival, wrapped])
    finally:
        engine._apply_unit_action = original
        engine._daily_refresh_plants = original_plants
        engine._daily_refresh_animals = original_animals
        engine._drop_inventories_to_shed = original_drop
        engine._commit_unit = original_commit
    final = env.state
    result = {
        "candidate": str(Path(candidate).resolve()),
        "candidate_sha256": hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),
        "local_dependency_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__).with_name("candidate.py"),
                      Path(__file__).with_name("economics.py")) if p.exists()
        },
        "overrides": overrides or {},
        "engine_version": __version__, "seed": seed, "seat": seat,
        "opponent": opponent,
        "cash": [s.observation.farms[i]["money"] for i, s in enumerate(final)],
        "status": [s.status for s in final], "frames": len(env.steps),
        "success": dict(success), "noops": dict(failed), "failure_examples": failures,
        "receipts": dict(receipts), "spending": dict(spending),
        "sold": dict(sold), "bought": dict(bought),
        "losses": losses, "daily": daily, "timing": _timing_dict(timed),
        "telemetry": dict(getattr(timed.function, "telemetry", {})),
        "final_shed": dict(final[seat].observation.private.shed),
        "final_cargo": deepcopy(final[seat].observation.private.inventories),
        "final_counts": counts(final[seat].observation.farms[seat]),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("daily", "failure_examples", "final_cargo")}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default=str(Path(__file__).with_name("candidate.py")))
    parser.add_argument("--opponent", default="pass")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--seat", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--override", action="append", default=[])
    args = parser.parse_args()
    overrides = {}
    for raw in args.override:
        key, value = raw.split("=", 1)
        try:
            overrides[key] = json.loads(value)
        except json.JSONDecodeError:
            overrides[key] = value
    run(args.candidate, args.opponent, args.seed, args.seat, args.output, overrides)
