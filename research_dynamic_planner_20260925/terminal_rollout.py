"""Controlled full-game A/B evaluator for Kaggriculture research agents.

This is *not* a submission agent. It compares an unchanged control policy with
one experimental policy while both players continue reacting to observations.
Optionally, exogenous shop unlocks are pinned to a previously observed native
schedule; market stock, prices, purchases, sales, weeds, and opponent actions
are never pinned. A saved-action replay cannot validate these causal effects.

The intended next use is a one-investment complete-bundle policy ablation.
Only after its control wrapper reproduces the original policy should an
experimental selector be evaluated here.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys

from kaggle_environments import __version__ as engine_version
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paired_benchmark import run_game


def source_hash(specification: str) -> str | None:
    """Hash local Python artifacts; built-in agent names have no local hash."""
    path = Path(specification)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def load_shop_schedule(audit_path: Path, expected_seed: int) -> dict[int, list[str]]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    seed = int(audit["seed"])
    if seed != expected_seed:
        raise ValueError(f"Shop audit seed {seed} differs from requested seed {expected_seed}")
    schedule = {}
    for row in audit["daily"]:
        day = int(row["day"])
        if day in schedule:
            raise ValueError(f"Duplicate shop day {day}")
        schedule[day] = list(row["shops"])
    if 0 not in schedule:
        raise ValueError("Shop audit must include the initial day")
    return schedule


@contextmanager
def matched_shops(schedule: dict[int, list[str]] | None):
    """Replace only future shop unlocks; restore the exact engine function."""
    if schedule is None:
        yield []
        return
    original = engine._end_of_day
    overrides = []

    def end_day(state, env, day):
        result = original(state, env, day)
        next_day = day + 1
        if next_day in schedule:
            town = state[0].observation.town
            requested = schedule[next_day]
            if list(town["unlocked_shops"]) != requested:
                overrides.append(next_day)
            town["unlocked_shops"] = list(requested)
        return result

    engine._end_of_day = end_day
    try:
        yield overrides
    finally:
        engine._end_of_day = original


def score_block(control: dict, treatment: dict) -> dict:
    """Separate own gains from rival changes, preserving terminal win labels."""
    if int(control["candidate_seat"]) != int(treatment["candidate_seat"]):
        raise ValueError("A/B rows have different seats")
    if int(control["seed"]) != int(treatment["seed"]):
        raise ValueError("A/B rows have different seeds")
    own_delta = treatment["candidate_reward"] - control["candidate_reward"]
    rival_delta = treatment["opponent_reward"] - control["opponent_reward"]
    margin_delta = own_delta - rival_delta
    if abs(margin_delta - (treatment["margin"] - control["margin"])) > 1e-7:
        raise AssertionError("Terminal cash and reported margin disagree")
    return {
        "seed": int(control["seed"]),
        "seat": int(control["candidate_seat"]),
        "control_own": control["candidate_reward"],
        "control_rival": control["opponent_reward"],
        "treatment_own": treatment["candidate_reward"],
        "treatment_rival": treatment["opponent_reward"],
        "own_delta": own_delta,
        "rival_delta": rival_delta,
        "margin_delta": margin_delta,
        "control_result": control["result"],
        "treatment_result": treatment["result"],
        "all_done": all(
            row[f"{party}_status"] == "DONE"
            for row in (control, treatment)
            for party in ("candidate", "opponent")
        ),
        "control_max_agent_ms": control["candidate_timing"]["max_ms"],
        "treatment_max_agent_ms": treatment["candidate_timing"]["max_ms"],
    }


def run_ab(control: str, treatment: str, opponent: str, seeds: list[int],
           audit: Path | None = None) -> dict:
    if audit is not None and len(seeds) != 1:
        raise ValueError("One observed shop audit can pin only its own seed")
    schedules = {seeds[0]: load_shop_schedule(audit, seeds[0])} if audit else {}
    blocks = []
    raw_rows = []
    shop_overrides = {}
    for seed in seeds:
        schedule = schedules.get(seed)
        for seat in (0, 1):
            arms = {}
            for name, path in (("control", control), ("treatment", treatment)):
                with matched_shops(schedule) as overrides:
                    row = run_game(path, opponent, seed, seat, False, None, {})
                arms[name] = row
                raw_rows.append({"arm": name, **row})
                shop_overrides[f"{seed}:{seat}:{name}"] = sorted(set(overrides))
            block = score_block(arms["control"], arms["treatment"])
            blocks.append(block)
            print(
                f"seed={seed} seat={seat} "
                f"control={block['control_own']:.0f}/{block['control_rival']:.0f} "
                f"treatment={block['treatment_own']:.0f}/{block['treatment_rival']:.0f} "
                f"delta_own={block['own_delta']:+.0f} "
                f"delta_rival={block['rival_delta']:+.0f} "
                f"delta_margin={block['margin_delta']:+.0f} "
                f"results={block['control_result']}->{block['treatment_result']}"
            )
    by_seed = {}
    for seed in seeds:
        rows = [row for row in blocks if row["seed"] == seed]
        by_seed[str(seed)] = {
            "seat_averaged_own_delta": sum(r["own_delta"] for r in rows) / len(rows),
            "seat_averaged_margin_delta": sum(r["margin_delta"] for r in rows) / len(rows),
            "control_pair_win": sum(r["control_result"] == "win" for r in rows) == 2,
            "treatment_pair_win": sum(r["treatment_result"] == "win" for r in rows) == 2,
        }
    return {
        "engine_version": engine_version,
        "control": control,
        "control_sha256": source_hash(control),
        "treatment": treatment,
        "treatment_sha256": source_hash(treatment),
        "opponent": opponent,
        "opponent_sha256": source_hash(opponent),
        "seeds": seeds,
        "shop_schedule_source": str(audit) if audit else None,
        "shop_schedule_sha256": source_hash(str(audit)) if audit else None,
        "shop_overrides": shop_overrides,
        "blocks": blocks,
        "seed_blocks": by_seed,
        "summary": {
            "all_done": all(r["all_done"] for r in blocks),
            "control_wins": sum(r["control_result"] == "win" for r in blocks),
            "treatment_wins": sum(r["treatment_result"] == "win" for r in blocks),
            "mean_own_delta": sum(r["own_delta"] for r in blocks) / len(blocks),
            "mean_margin_delta": sum(r["margin_delta"] for r in blocks) / len(blocks),
            "loss_to_win": sum(r["control_result"] != "win" and r["treatment_result"] == "win" for r in blocks),
            "win_to_loss": sum(r["control_result"] == "win" and r["treatment_result"] != "win" for r in blocks),
        },
        "raw_rows": raw_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", required=True, help="Frozen control Python agent")
    parser.add_argument("--treatment", required=True, help="Experimental Python agent")
    parser.add_argument("--opponent", required=True, help="Reactive opponent Python agent")
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--shop-audit", type=Path,
                        help="Native audit with observed daily shop sequence; one seed only")
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    if not args.seeds:
        parser.error("at least one seed is required")
    payload = run_ab(args.control, args.treatment, args.opponent,
                     args.seeds, args.shop_audit)
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("SUMMARY", json.dumps(payload["summary"], sort_keys=True))
    print("wrote", args.json_out)


if __name__ == "__main__":
    main()
