"""Bounded offline final-day worker-consolidation feasibility experiment.

This is an oracle replay diagnostic, not a submission policy. It reads the
frozen action trace only to reconstruct that run's already-planned schedule.
Any future online rule would have to derive tasks from the live observation
and its own schedule; it must not use these trace paths or replay identity.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import trace_paired_game_events as event_runner


OUT = Path(__file__).resolve().parent
TRACE_FILE = ""
TRACE_PLAYER = 0
OMIT_LAST_HIRE = False
ACTION_PATCHES: dict[str, Any] = {}
_TRACE_CACHE: dict[str, dict[int, dict[str, Any]]] = {}

TARGET_TRACE = ROOT / "diagnostics/top50_current_2026-09-24/neartie_marwar22_trace_20260925.json.gz"
CONTROL_TRACE = ROOT / "diagnostics/top50_current_2026-09-24/demand_gleb_control_trace_20260925.json.gz"
FINAL_HIRE_STEP = 697
DAY_START = 697
DAY_END = 718
MAX_EXACT_PAIR_TESTS = 4

MOVES = {
    "NORTH": (0, -1), "EAST": (1, 0), "SOUTH": (0, 1), "WEST": (-1, 0),
}
SHED_TILES = {(4, 4), (5, 4), (4, 5), (5, 5)}


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _read_trace(path: str | Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _step_map(path: str | Path, player: int) -> dict[int, dict[str, Any]]:
    key = str(Path(path).resolve()) + f"#{player}"
    if key not in _TRACE_CACHE:
        data = _read_trace(path)
        _TRACE_CACHE[key] = {int(row["step"]): row for row in data["traces"][player]}
    return _TRACE_CACHE[key]


def _command_at(action: dict[str, Any], actor: int) -> list[Any]:
    if actor == 0:
        return list(action.get("farmer") or ["PASS"])
    hands = action.get("hands") or []
    return list(hands[actor - 1]) if actor - 1 < len(hands) else ["PASS"]


def _set_command(action: dict[str, Any], actor: int, command: list[Any]) -> None:
    if actor == 0:
        action["farmer"] = list(command)
    else:
        action["hands"][actor - 1] = list(command)


def agent(observation: Any, configuration: Any = None) -> dict[str, Any]:
    """Replay a frozen schedule, optionally applying the offline treatment."""
    if not TRACE_FILE:
        return {"farmer": ["PASS"], "hands": [], "market": []}
    step = int(observation.get("step", -1))
    rows = _step_map(TRACE_FILE, int(TRACE_PLAYER))
    row = rows.get(step)
    if row is None:
        farms = observation.get("farms") or []
        player = int(observation.get("player", 0) or 0)
        hands = farms[player].get("hands", []) if player < len(farms) else []
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in hands], "market": []}
    action = copy.deepcopy(row["action"])
    if OMIT_LAST_HIRE:
        if step == FINAL_HIRE_STEP:
            market = action.get("market") or []
            hire_positions = [i for i, order in enumerate(market) if order and order[0] == "HIRE"]
            if hire_positions:
                market.pop(hire_positions[-1])
        if step > FINAL_HIRE_STEP:
            action["hands"] = list(action.get("hands") or [])[:10]
    patches = ACTION_PATCHES or {}
    for patch in patches.get(str(step), []):
        _set_command(action, int(patch["actor"]), list(patch["command"]))
    return action


def _position(obs: dict[str, Any], seat: int, actor: int) -> tuple[int, int]:
    farm = obs["farms"][seat]
    p = farm["farmer"] if actor == 0 else farm["hands"][actor - 1]
    return int(p[0]), int(p[1])


def _dist(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _is_free_unit_slot(event: dict[str, Any] | None, actor: int) -> bool:
    if not event or not event.get("changed"):
        return True
    position_field = "farmer" if actor == 0 else "hands"
    return (
        set(event.get("farm_fields_changed") or []) <= {position_field}
        and not (event.get("private_fields_changed") or [])
    )


def _bundles(data: dict[str, Any], seat: int) -> tuple[int, list[dict[str, Any]]]:
    rows = {int(row["step"]): row for row in data["traces"][seat]}
    donor_actor = len(rows[698]["observation"]["farms"][seat]["hands"])
    donor = {s: _command_at(row["action"], donor_actor) for s, row in rows.items() if s >= 698}
    events = {(int(e["step"]), int(e["actor"])): e for e in data["events"]
              if e.get("player") == seat and e.get("phase") == "unit_action"}

    def make(name: str, first_op: str, second_op: str | None, item: str, first_step: int,
             deadline: int) -> dict[str, Any]:
        task_steps = [s for s, cmd in donor.items() if cmd and cmd[0] == first_op]
        if len(task_steps) != 1:
            raise RuntimeError(f"Expected one donor {first_op} task, found {task_steps}")
        task_step = task_steps[0]
        target = _position(rows[task_step]["observation"], seat, donor_actor)
        if not events.get((task_step, donor_actor), {}).get("changed"):
            raise RuntimeError(f"Donor task {first_op} at {task_step} had no effect")
        following: list[int] = []
        if second_op:
            second = [s for s, cmd in donor.items() if s > task_step and cmd and cmd[0] == second_op]
            if len(second) != 1:
                raise RuntimeError(f"Expected one donor {second_op} after {task_step}, got {second}")
            second_step = second[0]
            following.append(second_step)
            after = rows[second_step + 1]["observation"]["private"]["inventories"][donor_actor]
            before = rows[second_step]["observation"]["private"]["inventories"][donor_actor]
            quantity = int(after.get(item, 0)) - int(before.get(item, 0))
            if quantity <= 0:
                raise RuntimeError(f"Could not verify donor output {item} after {second_op}")
        else:
            after = rows[task_step + 1]["observation"]["private"]["inventories"][donor_actor]
            before = rows[task_step]["observation"]["private"]["inventories"][donor_actor]
            quantity = int(after.get(item, 0)) - int(before.get(item, 0))
            if quantity <= 0:
                raise RuntimeError(f"Could not verify donor output {item}")
        drops = [s for s, cmd in donor.items() if s > task_step and cmd and cmd[0] == "DROP"]
        if not drops:
            raise RuntimeError(f"No same-day donor DROP after {first_op}")
        drop_step = drops[0]
        drop_pos = _position(rows[drop_step]["observation"], seat, donor_actor)
        return {
            "name": name, "first_op": first_op, "second_op": second_op,
            "item": item, "quantity": quantity, "target": list(target),
            "donor_actor": donor_actor, "task_steps": [task_step, *following],
            "delivery_step": drop_step, "delivery_position": list(drop_pos),
            "window_start": first_step, "deadline": deadline,
        }

    crop = make("water_harvest_deliver", "WATER", "HARVEST", "CARROT", 697, 711)
    fert = make("collect_fertilizer_deliver", "COLLECT_FERTILIZER", None, "FERTILIZER", 697, 717)
    return donor_actor, [crop, fert]


def _insertion_candidates(
    data: dict[str, Any], seat: int, bundle: dict[str, Any], limit: int = 12
) -> list[dict[str, Any]]:
    """Search contiguous local insertions into slots with no baseline effects.

    Each insertion must fit the bundle's shortest-path route and restore that
    surviving unit to its trace position before rejoining its original plan.
    This is deliberately a bounded sufficient-condition screen, not a global
    schedule optimizer.
    """
    rows = {int(row["step"]): row for row in data["traces"][seat]}
    unit_events = {(int(e["step"]), int(e["actor"])): e for e in data["events"]
                   if e.get("player") == seat and e.get("phase") == "unit_action"}
    donor_actor = int(bundle["donor_actor"])
    candidates: list[dict[str, Any]] = []
    for actor in range(donor_actor):
        first_start = max(int(bundle["window_start"]), 698 if actor == 10 else 697)
        for start in range(first_start, int(bundle["deadline"]) + 1):
            if actor > len(rows[start]["observation"]["farms"][seat]["hands"]):
                continue
            start_pos = _position(rows[start]["observation"], seat, actor)
            target = tuple(bundle["target"])
            # Compact valid task bundle: route in, productive task(s), return
            # to the donor's shed-access tile, and deposit only this output.
            core = _dist(start_pos, target) + (2 if bundle["second_op"] else 1)
            core += _dist(target, tuple(bundle["delivery_position"])) + 1
            for end in range(start + core - 1, int(bundle["deadline"]) + 1):
                if end + 1 not in rows:
                    continue
                post_pos = _position(rows[end + 1]["observation"], seat, actor)
                required = core + _dist(tuple(bundle["delivery_position"]), post_pos)
                if required > end - start + 1:
                    continue
                if not all(_is_free_unit_slot(unit_events.get((s, actor)), actor)
                           for s in range(start, end + 1)):
                    continue
                candidates.append({
                    "actor": actor, "start": start, "end": end,
                    "start_position": list(start_pos), "rejoin_position": list(post_pos),
                    "minimum_actions": required,
                    "free_slots": end - start + 1,
                })
    return sorted(candidates, key=lambda x: (
        x["minimum_actions"], x["start"], x["actor"], x["end"]
    ))[:limit]


def _route(a: tuple[int, int], b: tuple[int, int]) -> list[list[str]]:
    x, y = a
    tx, ty = b
    out: list[list[str]] = []
    while x != tx:
        op = "EAST" if tx > x else "WEST"
        x += 1 if tx > x else -1
        out.append([op])
    while y != ty:
        op = "SOUTH" if ty > y else "NORTH"
        y += 1 if ty > y else -1
        out.append([op])
    return out


def _make_patch(
    data: dict[str, Any], seat: int, bundle: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    rows = {int(row["step"]): row for row in data["traces"][seat]}
    actor, start, end = candidate["actor"], candidate["start"], candidate["end"]
    cursor = _position(rows[start]["observation"], seat, actor)
    commands = _route(cursor, tuple(bundle["target"]))
    if bundle["second_op"]:
        commands.extend([[bundle["first_op"]], [bundle["second_op"]]])
    else:
        commands.append([bundle["first_op"]])
    target = tuple(bundle["target"])
    shed = tuple(bundle["delivery_position"])
    commands.extend(_route(target, shed))
    commands.append(["PLACE", bundle["item"], int(bundle["quantity"])])
    commands.extend(_route(shed, tuple(candidate["rejoin_position"])))
    if len(commands) > end - start + 1:
        raise RuntimeError("Insertion candidate route exceeded its reserved window")
    commands.extend([["PASS"]] * (end - start + 1 - len(commands)))
    return {str(start + offset): [{"actor": actor, "command": command}]
            for offset, command in enumerate(commands)}


def _merge_patches(*patches: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, list[dict[str, Any]]] = {}
    for patch in patches:
        for step, rows in patch.items():
            merged.setdefault(step, []).extend(copy.deepcopy(rows))
    return merged


def _capture_run(candidate_overrides: dict[str, Any], opponent: str, seed: int, seat: int) -> dict[str, Any]:
    captured: dict[str, Any] = {}
    original_make = event_runner.make

    class Proxy:
        def __init__(self, wrapped: Any):
            object.__setattr__(self, "_wrapped", wrapped)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._wrapped, name)

        def __setattr__(self, name: str, value: Any) -> None:
            setattr(self._wrapped, name, value)

        def run(self, *agents: Any) -> Any:
            result = self._wrapped.run(*agents)
            captured["final"] = self._wrapped.steps[-1]
            captured["frames"] = len(self._wrapped.steps)
            return result

    def capture_make(*args: Any, **kwargs: Any) -> Proxy:
        return Proxy(original_make(*args, **kwargs))

    event_runner.make = capture_make
    try:
        result = event_runner.run(
            candidate=str(Path(__file__).resolve()), opponent=opponent, seed=seed,
            candidate_seat=seat, candidate_overrides=candidate_overrides,
        )
    finally:
        event_runner.make = original_make
    final = captured.get("final")
    final_obs = _plain(getattr(final[seat], "observation", {})) if final else {}
    result["final_observation"] = final_obs
    result["frames"] = captured.get("frames")
    return result


def _physical_signature(obs: dict[str, Any], seat: int, survivors: int) -> dict[str, Any]:
    farm = obs["farms"][seat]
    private = obs.get("private", {})
    return {
        "farmer": farm.get("farmer"),
        "surviving_hand_positions": (farm.get("hands") or [])[:survivors],
        "tiles": farm.get("tiles"),
        "shed": private.get("shed"),
        "seeds": private.get("seeds"),
        "surviving_inventories": (private.get("inventories") or [])[:survivors + 1],
    }


def _sell_signature(events: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    rows = []
    for e in events:
        if e.get("phase") == "market_unit" and e.get("operation") == "SELL":
            rows.append((e.get("step"), e.get("player"), e.get("item"), e.get("success"),
                         round(float(e.get("quoted_unit_price", 0) or 0), 4),
                         round(float(e.get("cash_delta", 0) or 0), 4)))
    return rows


def _donor_effects(events: list[dict[str, Any]], seat: int, donor: int) -> list[dict[str, Any]]:
    return [{"step": e.get("step"), "op": (e.get("action") or [None])[0],
             "position": e.get("position"), "changed": e.get("changed"),
             "farm_fields_changed": e.get("farm_fields_changed"),
             "private_fields_changed": e.get("private_fields_changed")}
            for e in events if e.get("player") == seat and e.get("actor") == donor
            and e.get("phase") == "unit_action" and e.get("changed")
            and int(e.get("step", -1)) >= 696]


def _consequential_effect_counts(events: list[dict[str, Any]], seat: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    position_fields = {"farmer", "hands"}
    for event in events:
        if event.get("player") != seat or event.get("phase") != "unit_action" or not event.get("changed"):
            continue
        farm_fields = sorted(set(event.get("farm_fields_changed") or []) - position_fields)
        private_fields = sorted(event.get("private_fields_changed") or [])
        if not farm_fields and not private_fields:
            continue
        action = event.get("action") or [None]
        op = action[0]
        if op == "DROP" or (op == "PLACE" and "shed" in private_fields):
            op = "DEPOSIT"
        key = json.dumps([op, farm_fields, private_fields], separators=(",", ":"))
        counts[key] = counts.get(key, 0) + 1
    return counts


def _bundle_executed(
    result: dict[str, Any], seat: int, bundle: dict[str, Any], actor: int
) -> bool:
    event_map = {(int(e.get("step", -1)), int(e.get("actor", -1))): e
                 for e in result.get("events", [])
                 if e.get("player") == seat and e.get("phase") == "unit_action"}
    matches: dict[str, list[int]] = {op: [] for op in
        (bundle["first_op"], bundle.get("second_op"), "PLACE") if op}
    for row in result.get("traces", [[]])[seat]:
        step = int(row.get("step", -1))
        if not 696 <= step <= int(bundle["deadline"]):
            continue
        action = row.get("action") or {}
        command = _command_at(action, actor)
        op = command[0] if command else None
        if op not in matches:
            continue
        obs = row.get("observation") or {}
        pos = _position(obs, seat, actor)
        event = event_map.get((step, actor), {})
        if op == "PLACE":
            if len(command) < 3 or command[1] != bundle["item"] or int(command[2]) != int(bundle["quantity"]):
                continue
            if pos not in SHED_TILES:
                continue
        elif list(pos) != bundle["target"]:
            continue
        if event.get("changed"):
            matches[op].append(step)
    if not matches[bundle["first_op"]]:
        return False
    last_task_step = max(matches[bundle["first_op"]])
    if bundle.get("second_op"):
        second_steps = [s for s in matches[bundle["second_op"]] if s > min(matches[bundle["first_op"]])]
        if not second_steps:
            return False
        last_task_step = max(last_task_step, min(second_steps))
    return any(s > last_task_step for s in matches["PLACE"])


def _run_summary(result: dict[str, Any], seat: int, donor: int, survivors: int) -> dict[str, Any]:
    final = result.get("final_observation") or {}
    own = final.get("farms", [{}] * 2)[seat] if final else {}
    rival = final.get("farms", [{}] * 2)[1 - seat] if final else {}
    return {
        "engine_version": result.get("engine_version"), "seed": result.get("seed"),
        "seat": seat, "status": [result.get("candidate_status"), result.get("opponent_status")],
        "frames": result.get("frames"), "own_cash": result.get("candidate_reward"),
        "rival_cash": result.get("opponent_reward"), "margin": result.get("margin"),
        "own_hands": len(own.get("hands") or []), "rival_hands": len(rival.get("hands") or []),
        "own_shed": final.get("private", {}).get("shed"),
        "own_seeds": final.get("private", {}).get("seeds"),
        "candidate_timing": result.get("candidate_timing"),
        "donor_effects": _donor_effects(result.get("events", []), seat, donor),
        "sell_units": len(_sell_signature(result.get("events", []))),
    }


def _compare(base: dict[str, Any], trial: dict[str, Any], seat: int, survivors: int) -> dict[str, Any]:
    bobs, tobs = base.get("final_observation") or {}, trial.get("final_observation") or {}
    bphys = _physical_signature(bobs, seat, survivors)
    tphys = _physical_signature(tobs, seat, survivors)
    return {
        "own_physical_state_equal": bphys == tphys,
        "physical_mismatch_fields": [k for k in bphys if bphys.get(k) != tphys.get(k)],
        "sales_exact_by_step_and_unit": _sell_signature(base.get("events", [])) == _sell_signature(trial.get("events", [])),
        "consequential_action_effects_equal": _consequential_effect_counts(base.get("events", []), seat)
            == _consequential_effect_counts(trial.get("events", []), seat),
        "rival_cash_equal": base.get("opponent_reward") == trial.get("opponent_reward"),
        "own_cash_delta": round(float(trial.get("candidate_reward", 0)) - float(base.get("candidate_reward", 0)), 4),
        "frames_equal": base.get("frames") == trial.get("frames"),
    }


def _case(trace_path: Path, omission_comparator: bool, exact_pair_limit: int) -> dict[str, Any]:
    data = _read_trace(trace_path)
    seat = int(data["candidate_seat"])
    opponent = str(data["opponent"])
    if not opponent.startswith("rawroute:"):
        raise RuntimeError(f"Expected frozen raw-route opponent in {trace_path}")
    opponent_path = (ROOT / opponent.split(":", 1)[1]).resolve()
    donor, bundles = _bundles(data, seat)
    survivors = donor - 1
    started = time.perf_counter()
    candidates = {b["name"]: _insertion_candidates(data, seat, b) for b in bundles}
    search_seconds = time.perf_counter() - started
    baseline_overrides = {"TRACE_FILE": str(trace_path.resolve()), "TRACE_PLAYER": seat,
                          "OMIT_LAST_HIRE": False, "ACTION_PATCHES": {}}
    baseline = _capture_run(baseline_overrides, f"rawroute:{opponent_path}", int(data["seed"]), seat)
    baseline_exact = (
        baseline.get("candidate_reward") == data.get("candidate_reward")
        and baseline.get("opponent_reward") == data.get("opponent_reward")
        and baseline.get("margin") == data.get("margin")
        and baseline.get("candidate_status") == "DONE"
        and baseline.get("opponent_status") == "DONE"
    )
    trials: list[dict[str, Any]] = []
    pair_candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for a, b in itertools.product(candidates[bundles[0]["name"]], candidates[bundles[1]["name"]]):
        if a["actor"] == b["actor"]:
            continue
        if a["actor"] == b["actor"] and max(a["start"], b["start"]) <= min(a["end"], b["end"]):
            continue
        pair_candidates.append((a, b))
    pair_candidates.sort(key=lambda pair: (
        pair[0]["minimum_actions"] + pair[1]["minimum_actions"],
        pair[0]["start"] + pair[1]["start"], pair[0]["actor"], pair[1]["actor"],
    ))
    exact_treatment_count = 0
    for a, b in pair_candidates[:exact_pair_limit]:
        patches = _merge_patches(
            _make_patch(data, seat, bundles[0], a), _make_patch(data, seat, bundles[1], b)
        )
        overrides = {"TRACE_FILE": str(trace_path.resolve()), "TRACE_PLAYER": seat,
                     "OMIT_LAST_HIRE": True, "ACTION_PATCHES": patches}
        trial = _capture_run(overrides, f"rawroute:{opponent_path}", int(data["seed"]), seat)
        exact_treatment_count += 1
        comparison = _compare(baseline, trial, seat, survivors)
        donor_removed = not _donor_effects(trial.get("events", []), seat, donor)
        same_game = trial.get("candidate_status") == "DONE" and trial.get("opponent_status") == "DONE"
        tasks_executed = (
            _bundle_executed(trial, seat, bundles[0], a["actor"])
            and _bundle_executed(trial, seat, bundles[1], b["actor"])
        )
        task_trace = [e for e in trial.get("events", []) if e.get("player") == seat
                      and e.get("phase") == "unit_action" and e.get("action", [None])[0]
                      in {"WATER", "HARVEST", "COLLECT_FERTILIZER", "PLACE", "DROP"}]
        # The exact terminal-state and market checks are the binding equivalence
        # tests; task actions are also retained as auditable evidence.
        valid = (baseline_exact and same_game and donor_removed and tasks_executed
                 and comparison["own_physical_state_equal"]
                 and comparison["sales_exact_by_step_and_unit"]
                 and comparison["consequential_action_effects_equal"]
                 and comparison["rival_cash_equal"]
                 and comparison["own_cash_delta"] == 89)
        trials.append({
            "kind": "bounded_task_reassignment", "recipient_actors": [a["actor"], b["actor"]],
            "insertions": [a, b], "comparison": comparison,
            "both_task_bundles_executed": tasks_executed, "valid": valid,
            "summary": _run_summary(trial, seat, donor, survivors),
            "relevant_task_actions": task_trace,
        })
        if valid:
            break
    if omission_comparator:
        omission_overrides = {"TRACE_FILE": str(trace_path.resolve()), "TRACE_PLAYER": seat,
                              "OMIT_LAST_HIRE": True, "ACTION_PATCHES": {}}
        omitted = _capture_run(omission_overrides, f"rawroute:{opponent_path}", int(data["seed"]), seat)
        trials.append({
            "kind": "invalid_remove_only_comparator_not_a_treatment",
            "comparison": _compare(baseline, omitted, seat, survivors),
            "valid": False,
            "summary": _run_summary(omitted, seat, donor, survivors),
        })
    return {
        "trace": str(trace_path.relative_to(ROOT)), "seed": data["seed"], "seat": seat,
        "baseline_trace": {"own_cash": data["candidate_reward"], "rival_cash": data["opponent_reward"],
                           "margin": data["margin"], "status": [data["candidate_status"], data["opponent_status"]]},
        "baseline_exact_replay": _run_summary(baseline, seat, donor, survivors),
        "baseline_matches_frozen_trace": baseline_exact,
        "donor_actor": donor, "final_hire_cost": 89,
        "bundles": bundles,
        "search": {
            "method": "contiguous shortest-route local insertion into baseline slots with no non-position effects; recipient must rejoin its source position by bundle deadline",
            "max_exact_pair_tests": exact_pair_limit,
            "candidate_insertions_by_bundle": {name: rows for name, rows in candidates.items()},
            "pair_candidate_count": len(pair_candidates),
            "exact_treatment_replays": exact_treatment_count,
            "search_seconds": round(search_seconds, 6),
        },
        "trials": trials,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--max-exact-pair-tests", type=int, default=MAX_EXACT_PAIR_TESTS)
    parser.add_argument("--skip-omission-comparator", action="store_true")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cases = [
        _case(TARGET_TRACE, not args.skip_omission_comparator, args.max_exact_pair_tests),
        _case(CONTROL_TRACE, not args.skip_omission_comparator, args.max_exact_pair_tests),
    ]
    result = {
        "title": "Offline final-day worker consolidation feasibility",
        "date": "2026-09-25", "engine_version": cases[0]["baseline_exact_replay"]["engine_version"],
        "policy_change": False, "submission": False,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "cases": cases,
    }
    json_path = args.out_dir / "results.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report_path = args.out_dir / "REPORT.md"
    report_path.write_text(_render_report(result), encoding="utf-8")
    print(f"wrote {report_path}\nwrote {json_path}")
    for case in cases:
        print(case["trace"], "baseline exact=", case["baseline_matches_frozen_trace"],
              "local pairs=", case["search"]["pair_candidate_count"],
              "treatment replays=", case["search"]["exact_treatment_replays"])


def _render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Bounded offline worker-consolidation feasibility — 2026-09-25", "",
        "**Decision: no task-preserving treatment established; no policy change or submission.**",
        "The experiment is offline-only and uses frozen traces as schedule evidence. It does not propose a route/replay-aware agent rule.", "",
        "The local insertion neighborhood requires each donor bundle to be inserted as a contiguous shortest-path route into a surviving unit's slots that had no non-position economic effect, then return that unit to its trace position by the donor bundle's delivery deadline. The two bundles must fit on distinct surviving units. The pair search is capped at the recorded limit. This is a bounded feasibility screen, not a proof against all possible rescheduling.", "",
        "| Case | Frozen baseline own / rival | Baseline replay exact | Eligible crop insertions | Eligible fertilizer insertions | Pairings | Exact task treatments |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for c in result["cases"]:
        b = c["baseline_trace"]
        counts = c["search"]["candidate_insertions_by_bundle"]
        lines.append(
            f"| `{Path(c['trace']).name}` | {b['own_cash']:,.0f} / {b['rival_cash']:,.0f} ({b['margin']:+,.0f}) | "
            f"{c['baseline_matches_frozen_trace']} | {len(counts['water_harvest_deliver'])} | "
            f"{len(counts['collect_fertilizer_deliver'])} | {c['search']['pair_candidate_count']} | "
            f"{c['search']['exact_treatment_replays']} |"
        )
    lines += ["", "The target trace identifies the final 89-coin hire on step 697. Its trailing hand completes the following observed bundles:", ""]
    for b in result["cases"][0]["bundles"]:
        lines.append(
            f"- `{b['name']}`: {b['item']} ×{b['quantity']}; task at `{b['target']}`, "
            f"delivery at step {b['delivery_step']} / `{b['delivery_position']}`."
        )
    lines += ["", "Exact replay details", ""]
    for c in result["cases"]:
        lines.append(f"### `{Path(c['trace']).name}`")
        lines.append("")
        base = c["baseline_exact_replay"]
        lines.append(
            f"Baseline tape replay: own {base['own_cash']:,.0f}, rival {base['rival_cash']:,.0f}, "
            f"margin {base['margin']:+,.0f}; status `{base['status']}`; {base['frames']} frames. "
            f"Exact-match to frozen rewards/status: `{c['baseline_matches_frozen_trace']}`."
        )
        for t in c["trials"]:
            s = t["summary"]
            lines.append("")
            lines.append(
                f"- `{t['kind']}`: own {s['own_cash']:,.0f}, rival {s['rival_cash']:,.0f}, "
                f"margin {s['margin']:+,.0f}; valid treatment `{t['valid']}`; "
                f"own cash delta {t['comparison']['own_cash_delta']:+,.0f}, "
                f"rival cash delta {s['rival_cash'] - c['baseline_trace']['rival_cash']:+,.0f}; "
                f"physical equal `{t['comparison']['own_physical_state_equal']}`, "
                f"sales exact `{t['comparison']['sales_exact_by_step_and_unit']}`, "
                f"rival cash equal `{t['comparison']['rival_cash_equal']}`. "
                f"Candidate-call max {s['candidate_timing'].get('max_seconds', 0)*1000:.3f} ms, "
                f"episode frames {s['frames']}."
            )
        lines.append("")
    lines += [
        f"Search elapsed {result['elapsed_seconds']:.3f} s across both cases (includes exact replays).",
        "The reported per-call maximum includes the oracle tape's one-time gzip load and is not an online-policy latency estimate.",
        "The remove-only comparator, when present, is explicitly invalid: it is not a consolidation treatment and cannot establish feasibility. A successful treatment would additionally require both donor bundles to be executed, exact same-day sell commits, equivalent own physical state (excluding the intentionally removed worker), rival cash unchanged, and +89 own cash from the omitted hire. No such treatment is claimed unless a trial is marked valid.",
        "", "Run command:", "", "```powershell", "python diagnostics\\worker_consolidation_20260925\\experiment.py", "```", "",
        "The existing parent 24-route audit was not read, edited, or run by this experiment.", "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
