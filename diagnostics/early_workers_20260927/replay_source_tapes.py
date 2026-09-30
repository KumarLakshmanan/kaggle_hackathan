"""Mechanism-only source-tape replay for the early-worker candidate.

The fixed opponent tapes are deliberately not treated as policy validation.
They establish whether the proposed work changes owned crop state and whether
the incumbent's existing harvest/replant/sell schedule monetizes any change.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import copy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EVENT_DIR = ROOT / "diagnostics" / "current_top20_20260927_163500"
sys.path.insert(0, str(ROOT))

import paired_benchmark as pb
from kaggle_environments import make

TRACE_FILES = {
    "DECEM": EVENT_DIR / "decem_current_seat0_events.json.gz",
    "Majkel1337": EVENT_DIR / "majkel_current_seat0_events.json.gz",
}
AGENTS = {
    "incumbent": ROOT / "main.py",
    "early_workers": ROOT / "exp_early_workers_20260927.py",
}


def item(d, key, default=None):
    return pb._value(d, key, default)


def get_trace(path: Path):
    trace = json.loads(gzip.decompress(path.read_bytes()))
    if int(trace["candidate_seat"]) != 0:
        raise ValueError(f"Expected candidate seat 0 in {path}")
    actions = [frame["action"] for frame in trace["traces"][1]]
    if len(actions) != 719:
        raise ValueError(f"Expected 719 opposing actions in {path}, found {len(actions)}")
    return trace, actions


def farm_snapshot(observation, seat=0):
    farms = list(item(observation, "farms", []) or [])
    farm = farms[seat] if seat < len(farms) else {}
    private = item(observation, "private", {}) or {}
    tiles = list(item(farm, "tiles", []) or [])
    crops = {}
    wheat_plots = []
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row if isinstance(row, (list, tuple)) else [row]):
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                crops[crop] = crops.get(crop, 0) + 1
                if crop == "WHEAT":
                    wheat_plots.append({
                        "xy": [x, y],
                        "planted_day": tile.get("planted_day"),
                        "yield_units": tile.get("yield_units"),
                        "watered_today": tile.get("watered_today"),
                        "consecutive_unwatered": tile.get("consecutive_unwatered"),
                    })
    town = item(observation, "town", {}) or {}
    market = item(observation, "market", {}) or {}
    return {
        "step": int(item(observation, "step", -1) or -1),
        "player": int(item(observation, "player", -1) if item(observation, "player", None) is not None else -1),
        "money": float(item(farm, "money", 0) or 0),
        "hands": list(item(farm, "hands", []) or []),
        "farmer": list(item(farm, "farmer", []) or []),
        "hires_today": int(item(farm, "hires_today", 0) or 0),
        "shed": dict(item(private, "shed", {}) or {}),
        "inventory": dict(item(private, "inventories", [{}])[0] or {}) if item(private, "inventories", None) else {},
        "seeds": dict(item(private, "seeds", {}) or {}),
        "crops": crops,
        "wheat_plots": wheat_plots,
        "shops": list(item(town, "unlocked_shops", []) or []),
        "market_inventory": dict(item(market, "inventory", {}) or {}),
        "market_prices": dict(item(market, "prices", {}) or {}),
    }


def run(agent_name: str, source_name: str, trace, opponent_actions):
    route_path = HERE / f"{source_name}_fixed_opponent.json.gz"
    route_path.write_bytes(gzip.compress(json.dumps({"actions": opponent_actions}, separators=(",", ":")).encode(), compresslevel=6))
    seed = int(trace["seed"])
    candidate, candidate_timing = pb._load_agent(str(AGENTS[agent_name]), f"early_mech_{agent_name}_{source_name}_{seed}")
    opponent, opponent_timing = pb._load_agent(f"rawroute:{route_path}", f"early_mech_tape_{source_name}_{seed}")

    class Recorder:
        def __init__(self, delegate):
            self.delegate = delegate
            self.calls = {}

        def __call__(self, observation, configuration=None):
            action = self.delegate(observation, configuration)
            step = int(item(observation, "step", len(self.calls)) or 0)
            self.calls[step] = {"observation": copy.deepcopy(observation), "action": copy.deepcopy(action)}
            return action

    recorder = Recorder(candidate)
    agents = [recorder, opponent]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(agents)

    records = []
    water_commands = 0
    water_owned_unwatered = 0
    water_state_changes = 0
    hand_movements = 0
    movement_state_changes = 0
    proposed_targets = []
    harvest_counts = {"WHEAT": 0, "other": 0}
    for step, call in sorted(recorder.calls.items()):
        obs = call["observation"]
        action = call["action"]
        if 20 <= step <= 95 or step in (119, 143, 167, 191, 215, 239, 263, 287, 311, 335, 359, 383, 407, 431, 455, 479, 503, 527, 551, 575, 599, 623, 647, 671, 695, 719):
            snap = farm_snapshot(obs)
            snap["action"] = action
            records.append(snap)

        for command in [item(action, "farmer", [])] + list(item(action, "hands", []) or []):
            if command and command[0] == "HARVEST":
                farms = list(item(obs, "farms", []) or [])
                farm = farms[0] if farms else {}
                units = [item(farm, "farmer", [])] + list(item(farm, "hands", []) or [])
                # The record is action-faithful; classify by the tile occupied
                # before the command resolves.
                unit_index = ([item(action, "farmer", [])] + list(item(action, "hands", []) or [])).index(command)
                pos = units[unit_index] if unit_index < len(units) else None
                tile = None
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    rows = list(item(farm, "tiles", []) or [])
                    x, y = int(pos[0]), int(pos[1])
                    tile = rows[y][x] if 0 <= y < len(rows) and 0 <= x < len(rows[y]) else None
                if isinstance(tile, dict) and tile.get("crop") == "WHEAT":
                    harvest_counts["WHEAT"] += 1
                else:
                    harvest_counts["other"] += 1
        if 25 <= step <= 47:
            farms = list(item(obs, "farms", []) or [])
            farm = farms[0] if farms else {}
            hands = list(item(farm, "hands", []) or [])
            hand_actions = list(item(action, "hands", []) or [])
            tiles = list(item(farm, "tiles", []) or [])
            for i, command in enumerate(hand_actions):
                op = command[0] if command else ""
                if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                    hand_movements += 1
                    if i < len(hands):
                        mx, my = int(hands[i][0]), int(hands[i][1])
                        dxdy = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}[op]
                        expected = [mx + dxdy[0], my + dxdy[1]]
                        next_call = recorder.calls.get(step + 1)
                        next_obs = item(next_call, "observation", {}) if next_call else {}
                        next_farms = list(item(next_obs, "farms", []) or [])
                        next_hands = list(item(next_farms[0], "hands", []) or []) if next_farms else []
                        if i < len(next_hands) and list(next_hands[i]) == expected:
                            movement_state_changes += 1
                if op != "WATER" or i >= len(hands):
                    continue
                water_commands += 1
                pos = hands[i]
                x, y = int(pos[0]), int(pos[1])
                tile = tiles[y][x] if y < len(tiles) and x < len(tiles[y]) else None
                target = {"step": step, "hand": i, "xy": [x, y], "kind": tile.get("kind") if isinstance(tile, dict) else tile,
                          "crop": tile.get("crop") if isinstance(tile, dict) else None,
                          "watered_before": tile.get("watered_today") if isinstance(tile, dict) else None}
                proposed_targets.append(target)
                if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", False):
                    water_owned_unwatered += 1
                    next_call = recorder.calls.get(step + 1)
                    next_obs = item(next_call, "observation", {}) if next_call else {}
                    next_farms = list(item(next_obs, "farms", []) or [])
                    next_farm = next_farms[0] if next_farms else {}
                    next_rows = list(item(next_farm, "tiles", []) or [])
                    next_tile = next_rows[y][x] if 0 <= y < len(next_rows) and 0 <= x < len(next_rows[y]) else None
                    if step == 47:
                        changed = isinstance(next_tile, dict) and next_tile.get("kind") == "PLANT" and int(next_tile.get("consecutive_unwatered", 99)) == 0
                    else:
                        changed = isinstance(next_tile, dict) and next_tile.get("kind") == "PLANT" and next_tile.get("watered_today") is True
                    target["effect_confirmed"] = changed
                    if changed:
                        water_state_changes += 1

    final = env.steps[-1]
    player_state = final[0]
    rival_state = final[1]
    result = {
        "candidate": agent_name,
        "opponent_tape": source_name,
        "source_episode_seed": seed,
        "source_candidate_reward": trace.get("candidate_reward"),
        "source_opponent_reward": trace.get("opponent_reward"),
        "source_margin": trace.get("margin"),
        "candidate_reward": pb._reward(player_state),
        "opponent_reward": pb._reward(rival_state),
        "margin": pb._reward(player_state) - pb._reward(rival_state),
        "result": "win" if pb._reward(player_state) > pb._reward(rival_state) else "loss" if pb._reward(player_state) < pb._reward(rival_state) else "draw",
        "status": [pb._status(player_state), pb._status(rival_state)],
        "frames": len(env.steps),
        "candidate_timing": pb._timing_dict(candidate_timing),
        "candidate_telemetry": pb._telemetry_dict(candidate_timing),
        "water_commands_day1": water_commands,
        "water_on_owned_unwatered_crop": water_owned_unwatered,
        "water_state_changes_confirmed_next_observation": water_state_changes,
        "hand_movements_day1": hand_movements,
        "hand_moves_confirmed_next_observation": movement_state_changes,
        "water_targets": proposed_targets,
        "wheat_harvest_actions_total": harvest_counts["WHEAT"],
        "other_harvest_actions_total": harvest_counts["other"],
        "records": records,
    }
    for timed in (candidate_timing, opponent_timing):
        if timed is not None and timed.module_name:
            sys.modules.pop(timed.module_name, None)
    return result


def main():
    old_path = HERE / "source_tape_replay.json"
    old = json.loads(old_path.read_text(encoding="utf8")) if old_path.exists() else {}
    results = {
        "engine_version": pb.engine_version,
        "agent_hashes": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in AGENTS.items()},
        "source_tapes": {},
        "runs": [r for r in old.get("runs", []) if r.get("candidate") == "incumbent"],
        "classification": "fixed-tape mechanism diagnostic only; not native/reacting policy evidence",
    }
    for source_name, path in TRACE_FILES.items():
        trace, actions = get_trace(path)
        results["source_tapes"][source_name] = {
            "path": str(path),
            "seed": trace.get("seed"),
            "candidate_seat": trace.get("candidate_seat"),
            "source_candidate_reward": trace.get("candidate_reward"),
            "source_opponent_reward": trace.get("opponent_reward"),
            "source_margin": trace.get("margin"),
            "opponent_action_sha256": hashlib.sha256(json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "source_step24": farm_snapshot(trace["traces"][0][24]["observation"]),
        }
        for agent_name in ("early_workers",):
            print(f"running {agent_name} vs fixed {source_name} tape (seed {trace['seed']})", flush=True)
            result = run(agent_name, source_name, trace, actions)
            results["runs"].append(result)
            print(f"  reward={result['candidate_reward']:.0f} rival={result['opponent_reward']:.0f} margin={result['margin']:+.0f} "
                  f"water={result['water_commands_day1']}/{result['water_state_changes_confirmed_next_observation']} "
                  f"moves={result['hand_movements_day1']}/{result['hand_moves_confirmed_next_observation']}", flush=True)
            (HERE / "source_tape_replay.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")
    (HERE / "source_tape_replay.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")


if __name__ == "__main__":
    main()
