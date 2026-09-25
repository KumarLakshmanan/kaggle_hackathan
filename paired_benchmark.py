"""Paired-seat strength and efficiency benchmark for Kaggriculture agents.

Each seed is played twice with seats swapped.  Modules are reloaded for every
game so stateful agents cannot leak state between episodes.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
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
    max_step: int = -1


class TimedAgent:
    def __init__(
        self,
        function: Callable[..., Any],
        capture_step: int | None = None,
        module_name: str | None = None,
    ):
        self.function = function
        self.timing = Timing()
        self.capture_step = capture_step
        self.capture: dict[str, Any] | None = None
        self.module_name = module_name
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
        observed_step = _value(observation, "step", -1)
        if (
            self.capture_step is not None
            and self.capture is None
            and int(observed_step if observed_step is not None else -1) == self.capture_step
        ):
            self.capture = _capture_public(observation)
        started = time.perf_counter()
        try:
            if self.accepts_configuration:
                return self.function(observation, configuration)
            return self.function(observation)
        finally:
            elapsed = time.perf_counter() - started
            self.timing.calls += 1
            self.timing.seconds += elapsed
            if elapsed > self.timing.max_seconds:
                self.timing.max_seconds = elapsed
                self.timing.max_step = int(observed_step if observed_step is not None else -1)


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
    private = _value(observation, "private", {}) or {}
    farms = list(_value(observation, "farms", []) or [])
    return {
        "step": int(_value(observation, "step", -1) or -1),
        "player": int(_value(observation, "player", 0) or 0),
        "shops": list(_value(town, "unlocked_shops", []) or []),
        "prices": dict(_value(market, "prices", {}) or {}),
        "inventory": dict(_value(market, "inventory", {}) or {}),
        "private_shed": dict(_value(private, "shed", {}) or {}),
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
    # Dataclasses (and some other decorators) resolve the defining module via
    # sys.modules while the class body is being executed. Register before
    # exec_module so otherwise-valid standalone agents can be imported.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
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
    try:
        _apply_overrides(module, overrides or {})
        function = getattr(module, "agent", None)
        if not callable(function):
            raise RuntimeError(f"No callable agent(obs) in {path.resolve()}")
        return TimedAgent(function, capture_step, module.__name__)
    except Exception:
        sys.modules.pop(module.__name__, None)
        raise


def _load_agent(
    specification: str,
    tag: str,
    capture_step: int | None = None,
    overrides: dict[str, Any] | None = None,
) -> tuple[Any, TimedAgent | None]:
    if specification.lower() == "pass":
        timed = TimedAgent(_pass_agent, capture_step)
        return timed, timed
    delayed_switch = specification.lower().startswith("v31-switch:")
    readable_route = specification.lower().startswith("v26-route:")
    route_preempt = specification.lower().startswith("route+preempt:")
    raw_route = specification.lower().startswith("rawroute:")
    if (
        delayed_switch
        or readable_route
        or route_preempt
        or raw_route
        or specification.lower().startswith("route:")
    ):
        route_path = Path(specification.split(":", 1)[1]).resolve()
        with gzip.open(route_path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        actions = payload.get("actions", [])
        if len(actions) != 719:
            raise RuntimeError(f"Expected 719 actions in {route_path}, found {len(actions)}")
        if raw_route:
            base_path = Path(__file__).resolve().parent / "raw_route_agent.py"
        elif delayed_switch:
            base_path = Path(__file__).resolve().parent / "main_v31_observable_portfolio.py"
        elif readable_route:
            base_path = Path(__file__).resolve().parent / "main.py"
        else:
            base_path = Path(__file__).resolve().parent / "v13r3_notebook_output" / "main.py"
        module = _load_module(base_path, f"route_proxy_{tag}")
        try:
            if raw_route:
                module.ACTIONS = actions
            elif delayed_switch:
                original_activate = module._activate_action_book

                def activate_delayed(obs: Any, step: int) -> str:
                    mode = original_activate(obs, step)
                    if mode == "alternate" and step >= 144:
                        module._ACTIONS = actions
                    return mode

                module._activate_action_book = activate_delayed
            else:
                module._ACTIONS = actions
            if readable_route:
                module._PRIMARY_ACTIONS = actions
                module._ALTERNATE_ACTIONS = actions
                module._counter_order = lambda action, step: action

                def activate_route(_obs: Any, _step: int) -> str:
                    module._ACTIONS = actions
                    return "primary"

                module._activate_action_book = activate_route
            else:
                module._PREEMPT_ENABLED = route_preempt
            _apply_overrides(module, overrides or {})
            function = getattr(module, "agent")
            timed = TimedAgent(function, capture_step, module.__name__)
            return timed, timed
        except Exception:
            sys.modules.pop(module.__name__, None)
            raise
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
        "max_step": timing.max_step,
    }


def _telemetry_dict(timed: TimedAgent | None) -> dict[str, Any] | None:
    if timed is None:
        return None
    telemetry = getattr(timed.function, "telemetry", None)
    if not isinstance(telemetry, Mapping):
        return None
    return {
        str(key): value
        for key, value in telemetry.items()
        if value is None or isinstance(value, (str, int, float, bool))
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
    candidate_timing = None
    opponent_timing = None
    try:
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
            "candidate_telemetry": _telemetry_dict(candidate_timing),
            "candidate_capture": candidate_timing.capture if candidate_timing else None,
            "opponent_timing": _timing_dict(opponent_timing),
        }
    finally:
        for timed in (candidate_timing, opponent_timing):
            if timed is not None and timed.module_name:
                sys.modules.pop(timed.module_name, None)


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
        for candidate_seat in (0, 1):
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
