"""Join the frozen 16-seed day-six A/B/C native comparison by full case."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    "A_incumbent": HERE / "route_A_dev16.json",
    "B_model": HERE / "route_B_dev16.json",
    "C_force": HERE / "route_C_dev16.json",
}


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["engine_version"] == "1.32.7"
    assert data["summary"]["all_done"]
    for role in ("candidate", "opponent"):
        data[role + "_sha256"] = hashlib.sha256((ROOT / data[role]).read_bytes()).hexdigest()
    assert sorted({int(r["seed"]) for r in data["rows"]}) == list(range(2613000, 2613016))
    return data


def key(row: dict) -> tuple[int, int]:
    return int(row["seed"]), int(row["candidate_seat"])


def compare(base: dict, treatment: dict) -> dict:
    a = {key(row): row for row in base["rows"]}
    b = {key(row): row for row in treatment["rows"]}
    assert len(a) == len(b) == 32 and set(a) == set(b)
    assert base["candidate_sha256"] == base["opponent_sha256"]
    assert treatment["opponent_sha256"] == base["opponent_sha256"]
    cases = []
    pairs = defaultdict(dict)
    for case in sorted(a):
        original, trial = a[case], b[case]
        assert original["candidate_status"] == original["opponent_status"] == "DONE"
        assert trial["candidate_status"] == trial["opponent_status"] == "DONE"
        own_delta = trial["candidate_reward"] - original["candidate_reward"]
        rival_delta = trial["opponent_reward"] - original["opponent_reward"]
        margin = trial["candidate_reward"] - trial["opponent_reward"]
        margin_delta = own_delta - rival_delta
        assert margin_delta == margin - (original["candidate_reward"]
                                          - original["opponent_reward"])
        row = dict(seed=case[0], seat=case[1], own=trial["candidate_reward"],
                   rival=trial["opponent_reward"], margin=margin,
                   delta_own=own_delta, delta_rival=rival_delta,
                   delta_margin=margin_delta,
                   shops=trial["candidate_capture"]["shops"],
                   telemetry=trial["candidate_telemetry"],
                   max_call_ms=trial["candidate_timing"]["max_ms"])
        cases.append(row)
        pairs[case[0]][case[1]] = row
    seeds = []
    for seed, seats in sorted(pairs.items()):
        assert set(seats) == {0, 1}
        rows = list(seats.values())
        seeds.append(dict(seed=seed, paired_margin=sum(r["margin"] for r in rows),
                          delta_own=sum(r["delta_own"] for r in rows),
                          delta_rival=sum(r["delta_rival"] for r in rows),
                          delta_margin=sum(r["delta_margin"] for r in rows),
                          triggered=any(r["telemetry"].get("rc_triggered", 0)
                                        for r in rows),
                          route0=any(r["telemetry"].get("rc_model_route0", 0)
                                     or r["telemetry"].get("rc_force_route0", 0)
                                     for r in rows)))
    summary = dict(
        paired_wins=sum(r["paired_margin"] > 0 for r in seeds),
        paired_losses=sum(r["paired_margin"] < 0 for r in seeds),
        paired_draws=sum(r["paired_margin"] == 0 for r in seeds),
        seat_wins=sum(r["margin"] > 0 for r in cases),
        seat_losses=sum(r["margin"] < 0 for r in cases),
        seat_draws=sum(r["margin"] == 0 for r in cases),
        rescued_draws_or_losses=sum(r["paired_margin"] > 0 for r in seeds),
        reversed_wins=0,
        own_cash=sum(r["own"] for r in cases),
        rival_cash=sum(r["rival"] for r in cases),
        paired_margin=sum(r["margin"] for r in cases),
        delta_own=sum(r["delta_own"] for r in cases),
        delta_rival=sum(r["delta_rival"] for r in cases),
        delta_margin=sum(r["delta_margin"] for r in cases),
        worst_seat_delta=min(r["delta_margin"] for r in cases),
        worst_paired_delta=min(r["delta_margin"] for r in seeds),
        triggered_seeds=sum(r["triggered"] for r in seeds),
        switched_seeds=sum(r["route0"] for r in seeds),
        max_agent_call_ms=max(r["max_call_ms"] for r in cases),
        errors=sum(r["telemetry"].get("rc_errors", 0) for r in cases),
    )
    return dict(source_sha256=treatment["candidate_sha256"],
                opponent_sha256=treatment["opponent_sha256"],
                cases=cases, seeds=seeds, summary=summary)


def main() -> None:
    inputs = {name: load(path) for name, path in INPUTS.items()}
    base = inputs["A_incumbent"]
    results = {name: compare(base, payload) for name, payload in inputs.items()}
    output = HERE / "route_abc_dev16_comparison.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for name, result in results.items():
        print(name, json.dumps(result["summary"], sort_keys=True))
        print("changed", [(r["seed"], r["seat"], r["delta_own"],
                           r["delta_rival"], r["delta_margin"])
                          for r in result["cases"] if r["delta_margin"]])
    print(output)


if __name__ == "__main__":
    main()
