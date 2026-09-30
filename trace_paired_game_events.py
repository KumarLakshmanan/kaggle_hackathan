"""Passively instrument one Kaggriculture replay without changing agent policy.

In addition to candidate/opponent observation/action traces, this runner hooks
the installed simulator's unit-action and market-commit functions. Wrappers call
the original implementation once and return its result unchanged.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
from pathlib import Path
from typing import Any

from kaggle_environments import __version__ as engine_version
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as game

from paired_benchmark import _load_agent, _reward, _status, _value
from trace_paired_game import TraceAgent, _plain


def run(
    candidate: str,
    opponent: str,
    seed: int,
    candidate_seat: int,
    candidate_overrides: dict[str, Any] | None = None,
    coupled_shop_rng: bool = False,
    shop_sequence: list[str] | None = None,
) -> dict[str, Any]:
    traces: list[list[dict[str, Any]]] = [[], []]
    events: list[dict[str, Any]] = []
    turns: list[dict[str, Any]] = []
    candidate_agent, candidate_timing = _load_agent(
        candidate,
        f"event_candidate_s{seed}_p{candidate_seat}",
        overrides=candidate_overrides or {},
    )
    opponent_agent, opponent_timing = _load_agent(
        opponent, f"event_opponent_s{seed}_p{1-candidate_seat}"
    )
    agents: list[Any] = [None, None]
    agents[candidate_seat] = TraceAgent(candidate_agent, traces[candidate_seat])
    agents[1 - candidate_seat] = TraceAgent(opponent_agent, traces[1 - candidate_seat])

    context: dict[str, Any] = {}
    original = {
        "interpreter": None,
        "apply_unit_action": game._apply_unit_action,
        "commit_unit": game._commit_unit,
        "do_hire": game._do_hire,
        "do_buy_land": game._do_buy_land,
        "spawn_weeds": game._spawn_weeds,
        "end_of_day": game._end_of_day,
    }

    def _fixed_draw_count_weeds(farm, board_size, weed_chance, rng):
        # Diagnostic-only alternate environment. Consume one RNG draw for
        # every coordinate, even when occupied; apply weeds only on empty
        # coordinates. Subsequent shop draws then depend on seed/day rather
        # than the agents' occupancy patterns. Never use this for native scores.
        for y in range(board_size):
            for x in range(board_size):
                draw = rng.random()
                if farm["tiles"][y][x] is None and draw < weed_chance:
                    farm["tiles"][y][x] = {"kind": "WEED"}

    def _forced_shop_end_of_day(state, env, day):
        result = original["end_of_day"](state, env, day)
        interval = max(1, int(env.configuration.get("townShopUnlockInterval", 3)))
        next_day = day + 1
        if next_day > 0 and next_day % interval == 0:
            shop_index = next_day // interval - 1
            shops = state[0].observation.town["unlocked_shops"]
            if shop_sequence is not None and shop_index < len(shop_sequence) and shop_index < len(shops):
                shops[shop_index] = shop_sequence[shop_index]
        return result

    def _pid(farm: Any) -> int | None:
        return context.get("farms", {}).get(id(farm))

    def _snapshot_pair(farm: Any, private: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        return _plain(farm), _plain(private)

    def _tracked_unit(farm, private, idx, action, *args, **kwargs):
        player = _pid(farm)
        before_farm, before_private = _snapshot_pair(farm, private)
        result = original["apply_unit_action"](farm, private, idx, action, *args, **kwargs)
        after_farm, after_private = _snapshot_pair(farm, private)
        changed_farm = sorted(
            key for key in set(before_farm) | set(after_farm)
            if before_farm.get(key) != after_farm.get(key)
        )
        changed_private = sorted(
            key for key in set(before_private) | set(after_private)
            if before_private.get(key) != after_private.get(key)
        )
        events.append({
            "step": context.get("step"),
            "phase": "unit_action",
            "player": player,
            "actor": int(idx),
            "action": _plain(action),
            "changed": bool(changed_farm or changed_private),
            "farm_fields_changed": changed_farm,
            "private_fields_changed": changed_private,
        })
        return result

    def _tracked_commit(op, item, price, farm, private, market, shed_capacity=100):
        player = _pid(farm)
        before_cash = float(farm.get("money", 0) or 0)
        before_shed = int(private.get("shed", {}).get(item, 0) or 0)
        before_market = int(market.get("inventory", {}).get(item, 0) or 0)
        before_total_shed = sum(int(value or 0) for value in private.get("shed", {}).values())
        ok = original["commit_unit"](op, item, price, farm, private, market, shed_capacity)
        after_cash = float(farm.get("money", 0) or 0)
        after_shed = int(private.get("shed", {}).get(item, 0) or 0)
        after_market = int(market.get("inventory", {}).get(item, 0) or 0)
        if not ok:
            if op == "SELL" and before_shed <= 0:
                reason = "empty_shed"
            elif op in ("BUY_PRODUCT", "BUY_ANIMAL") and before_total_shed >= int(shed_capacity):
                reason = "shed_full"
            elif op in ("BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL") and before_cash < float(price):
                reason = "insufficient_cash"
            else:
                reason = "rejected_or_invalid"
        else:
            reason = None
        events.append({
            "step": context.get("step"),
            "phase": "market_unit",
            "player": player,
            "operation": str(op),
            "item": str(item),
            "quoted_unit_price": float(price),
            "success": bool(ok),
            "failure_reason": reason,
            "cash_before": before_cash,
            "cash_after": after_cash,
            "cash_delta": after_cash - before_cash,
            "item_shed_before": before_shed,
            "item_shed_after": after_shed,
            "market_inventory_before": before_market,
            "market_inventory_after": after_market,
        })
        return ok

    def _tracked_atomic(name, func, farm, *args, **kwargs):
        player = _pid(farm)
        before = _plain(farm)
        result = func(farm, *args, **kwargs)
        after = _plain(farm)
        changed = sorted(
            key for key in set(before) | set(after) if before.get(key) != after.get(key)
        )
        events.append({
            "step": context.get("step"),
            "phase": "market_atomic",
            "player": player,
            "operation": name,
            "success": bool(changed),
            "farm_fields_changed": changed,
            "cash_before": float(before.get("money", 0) or 0),
            "cash_after": float(after.get("money", 0) or 0),
        })
        return result

    def _tracked_hire(farm, private, board_size, mult=1):
        return _tracked_atomic(
            "HIRE", original["do_hire"], farm, private, board_size, mult
        )

    def _tracked_land(farm, board_size):
        return _tracked_atomic("BUY_LAND", original["do_buy_land"], farm, board_size)

    try:
        game._apply_unit_action = _tracked_unit
        game._commit_unit = _tracked_commit
        game._do_hire = _tracked_hire
        game._do_buy_land = _tracked_land
        if coupled_shop_rng:
            game._spawn_weeds = _fixed_draw_count_weeds
        if shop_sequence is not None:
            game._end_of_day = _forced_shop_end_of_day

        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": int(seed)},
            debug=False,
        )
        original["interpreter"] = env.interpreter

        def _tracked_interpreter(state, current_env):
            obs0 = state[0].observation
            step = int(_value(obs0, "step", -1))
            farms = _value(obs0, "farms", []) or []
            player_farms = {}
            player_privates = {}
            before_rows = []
            for player, player_state in enumerate(state):
                player_farm = farms[player] if player < len(farms) else None
                player_private = _value(player_state.observation, "private", {}) or {}
                if player_farm is not None:
                    player_farms[id(player_farm)] = player
                player_privates[id(player_private)] = player
                if player_farm is not None:
                    farm_copy, private_copy = _snapshot_pair(player_farm, player_private)
                    before_rows.append({
                        "player": player,
                        "cash": float(farm_copy.get("money", 0) or 0),
                        "shed": private_copy.get("shed", {}),
                        "seeds": private_copy.get("seeds", {}),
                        "hands": len(farm_copy.get("hands", []) or []),
                        "unlocked_quadrants": farm_copy.get("unlocked_quadrants", []),
                    })
            market = _plain(_value(obs0, "market", {}) or {})
            context.update(step=step, farms=player_farms, privates=player_privates)
            event_start = len(events)
            result = original["interpreter"](state, current_env)
            after_rows = []
            for player, player_state in enumerate(state):
                player_farm = farms[player] if player < len(farms) else None
                player_private = _value(player_state.observation, "private", {}) or {}
                if player_farm is not None:
                    farm_copy, private_copy = _snapshot_pair(player_farm, player_private)
                    after_rows.append({
                        "player": player,
                        "cash": float(farm_copy.get("money", 0) or 0),
                        "shed": private_copy.get("shed", {}),
                        "seeds": private_copy.get("seeds", {}),
                        "hands": len(farm_copy.get("hands", []) or []),
                        "unlocked_quadrants": farm_copy.get("unlocked_quadrants", []),
                    })
            turns.append({
                "step": step,
                "day": step // max(1, int(current_env.configuration.get("turnsPerDay", 24))),
                "hour": step % max(1, int(current_env.configuration.get("turnsPerDay", 24))),
                "market_before": market,
                "players_before": before_rows,
                "players_after": after_rows,
                "events_start": event_start,
                "events_end": len(events),
            })
            context.clear()
            return result

        env.interpreter = _tracked_interpreter
        env.run(agents)
        final = env.steps[-1]
        for player in (0, 1):
            if traces[player]:
                from trace_paired_game import _attach_transitions

                _attach_transitions(traces[player], final[player])
        candidate_reward = _reward(final[candidate_seat])
        opponent_reward = _reward(final[1 - candidate_seat])
        return {
            "engine_version": engine_version,
            "candidate": candidate,
            "candidate_overrides": candidate_overrides or {},
            "coupled_shop_rng": bool(coupled_shop_rng),
            "forced_shop_sequence": shop_sequence,
            "opponent": opponent,
            "seed": int(seed),
            "candidate_seat": int(candidate_seat),
            "candidate_reward": candidate_reward,
            "opponent_reward": opponent_reward,
            "margin": candidate_reward - opponent_reward,
            "candidate_status": _status(final[candidate_seat]),
            "opponent_status": _status(final[1 - candidate_seat]),
            "candidate_timing": candidate_timing.timing.__dict__,
            "opponent_timing": opponent_timing.timing.__dict__,
            "traces": traces,
            "turns": turns,
            "events": events,
        }
    finally:
        game._apply_unit_action = original["apply_unit_action"]
        game._commit_unit = original["commit_unit"]
        game._do_hire = original["do_hire"]
        game._do_buy_land = original["do_buy_land"]
        game._spawn_weeds = original["spawn_weeds"]
        game._end_of_day = original["end_of_day"]
        for timed in (candidate_timing, opponent_timing):
            if timed is not None and getattr(timed, "module_name", None):
                import sys

                sys.modules.pop(timed.module_name, None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--candidate-seat", type=int, choices=(0, 1), required=True)
    parser.add_argument(
        "--coupled-shop-rng", action="store_true",
        help="Diagnostic modified environment: fixed weed-draw count per tile,"
             " so shop unlock RNG is invariant to occupancy. Not a native score.",
    )
    parser.add_argument(
        "--shop-sequence-from", type=Path,
        help="Diagnostic modified environment: force the same shop unlocks as"
             " a previously recorded native event trace. Not a native score.",
    )
    parser.add_argument(
        "--candidate-override",
        action="append",
        default=[],
        metavar="NAME=JSON",
        help="Override a candidate module setting for a controlled experiment.",
    )
    parser.add_argument("--json-gz-out", type=Path, required=True)
    args = parser.parse_args()
    overrides: dict[str, Any] = {}
    for item in args.candidate_override:
        if "=" not in item:
            parser.error(f"candidate override must be NAME=JSON, got {item!r}")
        name, raw_value = item.split("=", 1)
        try:
            overrides[name] = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            parser.error(f"invalid JSON in candidate override {item!r}: {exc}")
    shop_sequence = None
    if args.shop_sequence_from is not None:
        with gzip.open(args.shop_sequence_from, "rt", encoding="utf-8") as handle:
            reference = json.load(handle)
        shop_sequence = list(reference["traces"][0][-1]["observation"]["town"]["unlocked_shops"])
    result = run(
        args.candidate,
        args.opponent,
        args.seed,
        args.candidate_seat,
        candidate_overrides=overrides,
        coupled_shop_rng=args.coupled_shop_rng,
        shop_sequence=shop_sequence,
    )
    args.json_gz_out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.json_gz_out, "wt", encoding="utf-8") as handle:
        json.dump(result, handle, separators=(",", ":"))
    print(
        f"engine={result['engine_version']} seed={args.seed} seat={args.candidate_seat} "
        f"margin={result['margin']:+.0f} status={result['candidate_status']}/"
        f"{result['opponent_status']} turns={len(result['turns'])} "
        f"events={len(result['events'])} out={args.json_gz_out}"
    )


if __name__ == "__main__":
    main()
