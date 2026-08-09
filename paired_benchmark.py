"""Paired-seat strength and efficiency benchmark for Kaggriculture agents.

Each seed is played twice with seats swapped.  Modules are reloaded for every
game so stateful agents cannot leak state between episodes.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import inspect
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from kaggle_environments import __version__ as engine_version
from kaggle_environments import make


@dataclass
class Timing:
    calls: int = 0
    seconds: float = 0.0
    max_seconds: float = 0.0


class TimedAgent:
    def __init__(self, function: Callable[..., Any], capture_step: int | None = None):
        self.function = function
        self.timing = Timing()
        self.capture_step = capture_step
        self.capture: dict[str, Any] | None = None
        try:
            signature = inspect.signature(function)
            positional = [
                parameter
                for parameter in signature.parameters.values()
                if parameter.kind
                in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
            ]
            self.accepts_configuration = len(positional) >= 2
        except (TypeError, ValueError):
            self.accepts_configuration = False

    def __call__(self, observation: Any, configuration: Any = None) -> Any:
        capturing = (
            self.capture_step is not None
            and self.capture is None
            and int(_value(observation, "step", -1) or -1) == self.capture_step
        )
        if capturing:
            self.capture = _capture_public(observation)
        started = time.perf_counter()
        try:
            if self.accepts_configuration:
                result = self.function(observation, configuration)
            else:
                result = self.function(observation)
            if capturing and self.capture is not None:
                self.capture["action"] = result
            return result
        finally:
            elapsed = time.perf_counter() - started
            self.timing.calls += 1
            self.timing.seconds += elapsed
            self.timing.max_seconds = max(self.timing.max_seconds, elapsed)


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def _pass_agent(obs: Any) -> dict[str, Any]:
    player = int(_value(obs, "player", 0) or 0)
    farms = list(_value(obs, "farms", []) or [])
    farm = farms[player] if player < len(farms) else {}
    hands = list(_value(farm, "hands", []) or [])
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in hands],
        "market": [],
    }


def _farm_signature(farm: Any) -> dict[str, Any]:
    counts: dict[str, int] = {}
    weeds = 0
    occupied: list[list[Any]] = []
    for y, row in enumerate(_value(farm, "tiles", []) or []):
        for x, tile in enumerate(row if isinstance(row, list) else [row]):
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "WEED":
                weeds += 1
            occupied.append(
                [
                    x,
                    y,
                    tile.get("kind"),
                    tile.get("crop"),
                    tile.get("animal"),
                ]
            )
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    counts[value] = counts.get(value, 0) + 1
                    break
    return {
        "money": float(_value(farm, "money", 0.0) or 0.0),
        "hands": len(_value(farm, "hands", []) or []),
        "land": len(_value(farm, "unlocked_quadrants", []) or []),
        "weeds": weeds,
        "counts": counts,
        "occupied": occupied,
    }


def _capture_public(observation: Any) -> dict[str, Any]:
    market = _value(observation, "market", {}) or {}
    town = _value(observation, "town", {}) or {}
    farms = list(_value(observation, "farms", []) or [])
    return {
        "step": int(_value(observation, "step", -1) or -1),
        "player": int(_value(observation, "player", 0) or 0),
        "shops": list(_value(town, "unlocked_shops", []) or []),
        "prices": dict(_value(market, "prices", {}) or {}),
        "inventory": dict(_value(market, "inventory", {}) or {}),
        "farms": [_farm_signature(farm) for farm in farms],
    }


def _load_module(path: Path, tag: str) -> Any:
    resolved = path.resolve()
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()[:12]
    module_name = f"paired_{tag}_{digest}_{time.time_ns()}"
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import agent: {resolved}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _apply_overrides(module: Any, overrides: dict[str, Any]) -> None:
    for name, value in overrides.items():
        if not hasattr(module, name):
            raise RuntimeError(f"Agent module has no setting {name!r}")
        setattr(module, name, value)


def _load_file_agent(
    path: Path,
    tag: str,
    capture_step: int | None = None,
    overrides: dict[str, Any] | None = None,
) -> TimedAgent:
    module = _load_module(path, tag)
    _apply_overrides(module, overrides or {})
    function = getattr(module, "agent", None)
    if not callable(function):
        raise RuntimeError(f"No callable agent(obs) in {resolved}")
    return TimedAgent(function, capture_step)


def _load_agent(
    specification: str,
    tag: str,
    capture_step: int | None = None,
    overrides: dict[str, Any] | None = None,
) -> tuple[Any, TimedAgent | None]:
    if specification.lower() == "pass":
        timed = TimedAgent(_pass_agent, capture_step)
        return timed, timed
    if specification.lower().startswith("agent-threat:"):
        agent_text, threat_text = specification.split(":", 1)[1].split("|", 1)
        module = _load_module(Path(agent_text).resolve(), f"agent_threat_{tag}")
        with gzip.open(Path(threat_text).resolve(), "rt", encoding="utf-8") as handle:
            threat_actions = json.load(handle).get("actions", [])
        hazards: dict[str, list[list[Any]]] = {}
        for step, action in enumerate(threat_actions):
            quantities: dict[str, int] = {}
            for order in action.get("market", []) or []:
                if len(order) >= 3 and order[0] == "SELL":
                    quantities[str(order[1])] = quantities.get(str(order[1]), 0) + int(order[2])
            if quantities:
                hazards[str(step)] = [
                    [item, 1.0, float(quantity), 1] for item, quantity in quantities.items()
                ]
        module._GOLD_HAZARD = hazards
        _apply_overrides(module, overrides or {})
        timed = TimedAgent(getattr(module, "agent"), capture_step)
        return timed, timed
    delayed_switch = specification.lower().startswith("v31-switch:")
    v37_switch = specification.lower().startswith("v37-switch:")
    v37_switch_threat = specification.lower().startswith("v37-switch-threat:")
    v37_step1 = specification.lower().startswith("v37-step1:")
    v37_step216 = specification.lower().startswith("v37-step216:")
    v37_step288 = specification.lower().startswith("v37-step288:")
    v37_step360 = specification.lower().startswith("v37-step360:")
    v32_switch = specification.lower().startswith(("v32-switch:", "v32-switch-threat:"))
    v32base_switch = specification.lower().startswith("v32base-switch:")
    v32base_step1 = specification.lower().startswith("v32base-step1:")
    v32base_step144 = specification.lower().startswith("v32base-step144:")
    pasture5_switch = specification.lower().startswith("pasture5-switch:")
    step_one_switch = specification.lower().startswith(("step1-route:", "step1-threat:"))
    step144_switch = specification.lower().startswith("step144-route:")
    readable_route = specification.lower().startswith("v26-route:")
    threat_route = specification.lower().startswith("route-threat:")
    portfolio_threat = specification.lower().startswith("portfolio-threat:")
    hybrid_route = specification.lower().startswith(("hybrid-route:", "hybrid-threat:"))
    route_preempt = specification.lower().startswith("route+preempt:")
    wheat_first_route = specification.lower().startswith("wheat-first-route:")
    if (
        delayed_switch
        or v37_switch
        or v37_switch_threat
        or v37_step1
        or v37_step216
        or v37_step288
        or v37_step360
        or v32_switch
        or v32base_switch
        or v32base_step1
        or v32base_step144
        or pasture5_switch
        or step_one_switch
        or step144_switch
        or readable_route
        or threat_route
        or portfolio_threat
        or hybrid_route
        or route_preempt
        or wheat_first_route
        or specification.lower().startswith("route:")
    ):
        route_argument = specification.split(":", 1)[1]
        threat_actions = None
        opening_actions = None
        if v37_switch_threat:
            route_text, threat_text = route_argument.split("|", 1)
            route_path = Path(route_text).resolve()
            with gzip.open(Path(threat_text).resolve(), "rt", encoding="utf-8") as handle:
                threat_actions = json.load(handle).get("actions", [])
        elif threat_route:
            route_text, threat_text = route_argument.split("|", 1)
            route_path = Path(route_text).resolve()
            with gzip.open(Path(threat_text).resolve(), "rt", encoding="utf-8") as handle:
                threat_actions = json.load(handle).get("actions", [])
        elif hybrid_route:
            opening_text, route_text = route_argument.split("|", 1)
            with gzip.open(Path(opening_text).resolve(), "rt", encoding="utf-8") as handle:
                opening_actions = json.load(handle).get("actions", [])
            route_path = Path(route_text).resolve()
        elif portfolio_threat:
            route_text, threat_text = route_argument.split("|", 1)
            route_path = Path(route_text).resolve()
            with gzip.open(Path(threat_text).resolve(), "rt", encoding="utf-8") as handle:
                threat_actions = json.load(handle).get("actions", [])
        else:
            route_path = Path(route_argument).resolve()
        with gzip.open(route_path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        actions = payload.get("actions", [])
        if len(actions) != 719:
            raise RuntimeError(f"Expected 719 actions in {route_path}, found {len(actions)}")
        if wheat_first_route:
            # Preserve the route's complete opening portfolio but execute its
            # WHEAT product purchase before the price can be moved by the
            # opponent.  This is the observable-policy variant used by the
            # current opening-order search.
            actions = [
                {
                    "farmer": list(actions[0].get("farmer") or ["PASS"]),
                    "hands": [list(order) for order in actions[0].get("hands", []) or []],
                    "market": [list(order) for order in actions[0].get("market", []) or []],
                },
                *actions[1:],
            ]
            market = actions[0]["market"]
            wheat = next(
                (
                    order for order in market
                    if len(order) >= 3 and order[0] == "BUY_PRODUCT"
                    and order[1] == "WHEAT"
                ),
                None,
            )
            if wheat is not None:
                actions[0]["market"] = [wheat, *[order for order in market if order is not wheat]]
        if delayed_switch:
            base_path = Path(__file__).resolve().parent / "main_v31_observable_portfolio.py"
        elif (
            v37_switch or v37_switch_threat or v37_step1
            or v37_step216 or v37_step288 or v37_step360
        ):
            base_path = Path(__file__).resolve().parent / "main.py"
        elif v32base_switch or v32base_step1 or v32base_step144:
            base_path = Path(__file__).resolve().parent / "main_v32_observable_portfolio.py"
        elif v32_switch or pasture5_switch or step_one_switch or step144_switch:
            base_path = Path(__file__).resolve().parent / "main.py"
        elif readable_route:
            base_path = Path(__file__).resolve().parent / "main.py"
        elif threat_route or portfolio_threat or hybrid_route:
            base_path = Path(__file__).resolve().parent / "main.py"
        else:
            base_path = Path(__file__).resolve().parent / "v13r3_notebook_output" / "main.py"
        module = _load_module(base_path, f"route_proxy_{tag}")
        if (
            v37_switch or v37_switch_threat or v37_step1
            or v37_step216 or v37_step288 or v37_step360
        ):
            original_select = module._select_public_book
            switch_step = (
                1 if v37_step1 else
                216 if v37_step216 else
                288 if v37_step288 else
                360 if v37_step360 else
                144
            )

            def select_v37(obs: Any, step: int) -> None:
                original_select(obs, step)
                if step >= switch_step:
                    module._ACTIONS = actions

            module._select_public_book = select_v37
        elif delayed_switch or v32_switch or v32base_switch or v32base_step1 or v32base_step144 or pasture5_switch or step_one_switch or step144_switch:
            original_activate = module._activate_action_book

            def activate_delayed(obs: Any, step: int) -> str:
                mode = original_activate(obs, step)
                if pasture5_switch and step == 1:
                    player = int(_value(obs, "player", 0) or 0)
                    farms = list(_value(obs, "farms", []) or [])
                    opponent_farm = farms[1 - player] if len(farms) >= 2 else {}
                    hands = len(_value(opponent_farm, "hands", []) or [])
                    tiles = list(_value(opponent_farm, "tiles", []) or [])
                    center = tiles[4][4] if len(tiles) > 4 and len(tiles[4]) > 4 else None
                    if hands >= 5 and isinstance(center, dict) and center.get("kind") == "PASTURE":
                        module._OPPONENT_PASTURE[player] = True
                        module._PORTFOLIO_MODE[player] = "alternate"
                        module._ACTIONS = module._ALTERNATE_ACTIONS
                        mode = "alternate"
                threshold = 1 if (step_one_switch or v32base_step1) else 144
                if step >= threshold and (step_one_switch or v32base_step1 or v32base_step144 or step144_switch or mode == "alternate"):
                    module._ACTIONS = actions
                return mode

            module._activate_action_book = activate_delayed
        else:
            module._ACTIONS = actions
        if hybrid_route:
            module._PRIMARY_ACTIONS = actions
            module._ALTERNATE_ACTIONS = actions

            def activate_hybrid(_obs: Any, step: int) -> str:
                module._ACTIONS = opening_actions if step == 0 else actions
                return "primary"

            module._activate_action_book = activate_hybrid
            # V36+ selects its tape through ``_select_public_book`` instead of
            # ``_activate_action_book``.  Override both hooks so hybrid-route
            # experiments actually use the requested continuation regardless
            # of which transparent wrapper is currently in main.py.
            if hasattr(module, "_select_public_book"):
                def select_hybrid(_obs: Any, step: int) -> None:
                    module._ACTIONS = opening_actions if step == 0 else actions

                module._select_public_book = select_hybrid
        elif readable_route:
            module._PRIMARY_ACTIONS = actions
            module._ALTERNATE_ACTIONS = actions
            module._counter_order = lambda action, step: action

            def activate_route(_obs: Any, _step: int) -> str:
                module._ACTIONS = actions
                return "primary"

            module._activate_action_book = activate_route
        elif route_preempt or wheat_first_route or specification.lower().startswith("route:"):
            module._PREEMPT_ENABLED = route_preempt
        if threat_route or portfolio_threat:
            module._PREEMPT_ENABLED = True
            module._PRIMARY_ACTIONS = actions
            module._ALTERNATE_ACTIONS = actions

            def activate_threat_route(_obs: Any, _step: int) -> str:
                module._ACTIONS = actions
                return "primary"

            module._activate_action_book = activate_threat_route
        if threat_route or portfolio_threat or "-threat:" in specification.lower():
            hazards: dict[str, list[list[Any]]] = {}
            for step, action in enumerate(threat_actions or actions):
                rows: dict[str, int] = {}
                for order in action.get("market", []) or []:
                    if len(order) >= 3 and order[0] == "SELL":
                        rows[str(order[1])] = rows.get(str(order[1]), 0) + int(order[2])
                if rows:
                    hazards[str(step)] = [
                        [item, 1.0, float(quantity), 1] for item, quantity in rows.items()
                    ]
            module._GOLD_HAZARD = hazards
        # Raw route proxies can participate in opening-portfolio searches via
        # the same override used by generated routers.  Define the setting
        # before validation, then apply it to a private copy of turn zero.
        if not hasattr(module, "OPENING_MARKET_OVERRIDE"):
            module.OPENING_MARKET_OVERRIDE = None
        if not hasattr(module, "ACTION_PATCHES"):
            module.ACTION_PATCHES = {}
        _apply_overrides(module, overrides or {})
        if module.OPENING_MARKET_OVERRIDE is not None:
            module._ACTIONS = [
                {
                    "farmer": list(module._ACTIONS[0].get("farmer") or ["PASS"]),
                    "hands": [
                        list(order) for order in module._ACTIONS[0].get("hands", []) or []
                    ],
                    "market": [list(order) for order in module.OPENING_MARKET_OVERRIDE],
                },
                *module._ACTIONS[1:],
            ]
        if module.ACTION_PATCHES:
            if not isinstance(module.ACTION_PATCHES, dict):
                raise RuntimeError("ACTION_PATCHES must be a JSON object")
            module._ACTIONS = list(module._ACTIONS)
            for raw_step, patch in module.ACTION_PATCHES.items():
                step = int(raw_step)
                if not 0 <= step < len(module._ACTIONS) or not isinstance(patch, dict):
                    raise RuntimeError(f"invalid action patch at step {raw_step!r}")
                original = module._ACTIONS[step]
                module._ACTIONS[step] = {
                    "farmer": list(patch.get("farmer", original.get("farmer") or ["PASS"])),
                    "hands": [
                        list(order)
                        for order in patch.get("hands", original.get("hands", []) or [])
                    ],
                    "market": [
                        list(order)
                        for order in patch.get("market", original.get("market", []) or [])
                    ],
                }
        function = getattr(module, "agent")
        timed = TimedAgent(function, capture_step)
        return timed, timed
    path = Path(specification)
    if path.is_file():
        timed = _load_file_agent(path, tag, capture_step, overrides)
        return timed, timed
    # Kaggle built-ins such as "starter" are resolved by Environment.run.
    return specification, None


def _reward(state: Any) -> float:
    return float(_value(state, "reward", 0.0) or 0.0)


def _status(state: Any) -> str:
    return str(_value(state, "status", "UNKNOWN"))


def _timing_dict(timed: TimedAgent | None) -> dict[str, float | int] | None:
    if timed is None:
        return None
    timing = timed.timing
    mean = timing.seconds / timing.calls if timing.calls else 0.0
    return {
        "calls": timing.calls,
        "seconds": timing.seconds,
        "mean_us": mean * 1_000_000,
        "max_ms": timing.max_seconds * 1_000,
    }


def run_game(
    candidate: str,
    opponent: str,
    seed: int,
    candidate_seat: int,
    debug: bool,
    capture_step: int | None,
    candidate_overrides: dict[str, Any],
) -> dict[str, Any]:
    candidate_agent, candidate_timing = _load_agent(
        candidate,
        f"candidate_s{seed}_p{candidate_seat}",
        capture_step,
        candidate_overrides,
    )
    opponent_agent, opponent_timing = _load_agent(
        opponent, f"opponent_s{seed}_p{1 - candidate_seat}"
    )
    agents = (
        [candidate_agent, opponent_agent]
        if candidate_seat == 0
        else [opponent_agent, candidate_agent]
    )

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": int(seed)},
        debug=debug,
    )
    started = time.perf_counter()
    env.run(agents)
    wall_seconds = time.perf_counter() - started

    final = env.steps[-1]
    opponent_seat = 1 - candidate_seat
    candidate_reward = _reward(final[candidate_seat])
    opponent_reward = _reward(final[opponent_seat])
    margin = candidate_reward - opponent_reward
    return {
        "seed": seed,
        "candidate_seat": candidate_seat,
        "candidate_reward": candidate_reward,
        "opponent_reward": opponent_reward,
        "margin": margin,
        "result": "win" if margin > 0 else "loss" if margin < 0 else "draw",
        "candidate_status": _status(final[candidate_seat]),
        "opponent_status": _status(final[opponent_seat]),
        "frames": len(env.steps),
        "wall_seconds": wall_seconds,
        "candidate_timing": _timing_dict(candidate_timing),
        "candidate_capture": candidate_timing.capture if candidate_timing else None,
        "opponent_timing": _timing_dict(opponent_timing),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    margins = [float(row["margin"]) for row in rows]
    rewards = [float(row["candidate_reward"]) for row in rows]
    paired_margins: dict[int, float] = {}
    for row in rows:
        seed = int(row["seed"])
        paired_margins[seed] = paired_margins.get(seed, 0.0) + float(row["margin"])

    candidate_timings = [
        row["candidate_timing"] for row in rows if row["candidate_timing"] is not None
    ]
    calls = sum(int(item["calls"]) for item in candidate_timings)
    seconds = sum(float(item["seconds"]) for item in candidate_timings)
    max_ms = max((float(item["max_ms"]) for item in candidate_timings), default=0.0)

    def counts(values: list[float]) -> dict[str, int]:
        return {
            "wins": sum(value > 0 for value in values),
            "draws": sum(value == 0 for value in values),
            "losses": sum(value < 0 for value in values),
        }

    return {
        "games": len(rows),
        "seeds": len(paired_margins),
        "game_results": counts(margins),
        "paired_results": counts(list(paired_margins.values())),
        "mean_margin": statistics.fmean(margins),
        "median_margin": statistics.median(margins),
        "mean_reward": statistics.fmean(rewards),
        "min_reward": min(rewards),
        "max_reward": max(rewards),
        "mean_wall_seconds": statistics.fmean(float(row["wall_seconds"]) for row in rows),
        "agent_calls": calls,
        "agent_mean_us": (seconds / calls * 1_000_000) if calls else None,
        "agent_max_ms": max_ms if calls else None,
        "paired_margins": paired_margins,
        "all_done": all(
            row["candidate_status"] == "DONE" and row["opponent_status"] == "DONE"
            for row in rows
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, help="Agent .py path or built-in name")
    parser.add_argument("--opponent", required=True, help="Agent .py path or built-in name")
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument(
        "--seats",
        nargs="+",
        type=int,
        choices=(0, 1),
        default=[0, 1],
        help="Candidate seats to benchmark (default: both)",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--capture-step", type=int)
    parser.add_argument(
        "--candidate-override",
        action="append",
        default=[],
        metavar="NAME=JSON",
        help="Override a candidate module setting after import",
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    candidate_overrides: dict[str, Any] = {}
    for raw in args.candidate_override:
        if "=" not in raw:
            parser.error(f"Invalid override {raw!r}; expected NAME=JSON")
        name, value = raw.split("=", 1)
        try:
            candidate_overrides[name] = json.loads(value)
        except json.JSONDecodeError:
            candidate_overrides[name] = value

    print(f"engine={engine_version} candidate={args.candidate} opponent={args.opponent}")
    rows: list[dict[str, Any]] = []
    for seed in args.seeds:
        for candidate_seat in args.seats:
            row = run_game(
                args.candidate,
                args.opponent,
                seed,
                candidate_seat,
                args.debug,
                args.capture_step,
                candidate_overrides,
            )
            rows.append(row)
            print(
                f"seed={seed} seat={candidate_seat} result={row['result']:4s} "
                f"reward={row['candidate_reward']:9.0f} "
                f"opp={row['opponent_reward']:9.0f} margin={row['margin']:+9.0f} "
                f"status={row['candidate_status']}/{row['opponent_status']} "
                f"wall={row['wall_seconds']:.2f}s",
                flush=True,
            )

    summary = summarize(rows)
    print("SUMMARY " + json.dumps(summary, sort_keys=True))
    if args.json_out:
        payload = {
            "engine_version": engine_version,
            "candidate": args.candidate,
            "opponent": args.opponent,
            "candidate_overrides": candidate_overrides,
            "rows": rows,
            "summary": summary,
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
