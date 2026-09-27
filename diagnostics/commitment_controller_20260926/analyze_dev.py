"""Exact A/B/C native comparison for the predeclared day-11 commitment block."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = {
    "A_incumbent": HERE / "incumbent_dev16.json",
    "B_model": HERE / "model_fixed_dev16.json",
    "C_force": HERE / "force_fixed_dev16.json",
}


def load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf8"))
    assert payload["engine_version"] == "1.32.7"
    assert payload["summary"]["all_done"]
    for role in ("candidate", "opponent"):
        artifact = HERE.parents[1] / payload[role]
        payload[role + "_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    payload["seeds"] = sorted({int(row["seed"]) for row in payload["rows"]})
    return payload


def row_key(row: dict) -> tuple[int, int]:
    return int(row["seed"]), int(row["candidate_seat"])


def margin(row: dict) -> float:
    return float(row["candidate_reward"] - row["opponent_reward"])


def summarize(base: dict, arm: dict) -> dict:
    baseline = {row_key(r): r for r in base["rows"]}
    tested = {row_key(r): r for r in arm["rows"]}
    assert len(baseline) == len(tested) == 32
    assert set(baseline) == set(tested)
    assert base["opponent_sha256"] == arm["opponent_sha256"]
    assert base["candidate_sha256"] == arm["opponent_sha256"]
    assert base["engine_version"] == arm["engine_version"]
    assert base["seeds"] == arm["seeds"] == list(range(2612000, 2612016))
    cases = []
    pairs = defaultdict(dict)
    for key in sorted(baseline):
        a, b = baseline[key], tested[key]
        da = float(b["candidate_reward"] - a["candidate_reward"])
        dr = float(b["opponent_reward"] - a["opponent_reward"])
        dm = da - dr
        assert dm == margin(b) - margin(a)
        assert a["candidate_status"] == a["opponent_status"] == "DONE"
        assert b["candidate_status"] == b["opponent_status"] == "DONE"
        record = dict(seed=key[0], seat=key[1], baseline_own=a["candidate_reward"],
                      baseline_rival=a["opponent_reward"], own=b["candidate_reward"],
                      rival=b["opponent_reward"], baseline_margin=margin(a),
                      margin=margin(b), delta_own=da, delta_rival=dr,
                      delta_margin=dm, shops=b["candidate_capture"]["shops"],
                      telemetry=b["candidate_telemetry"],
                      max_call_ms=b["candidate_timing"]["max_ms"])
        cases.append(record)
        pairs[key[0]][key[1]] = record
    assert all(set(seats) == {0, 1} for seats in pairs.values())
    seed_rows = []
    for seed, seats in sorted(pairs.items()):
        a, b = seats[0], seats[1]
        seed_rows.append(dict(seed=seed,
                              baseline_paired_margin=a["baseline_margin"] + b["baseline_margin"],
                              paired_margin=a["margin"] + b["margin"],
                              delta_own=a["delta_own"] + b["delta_own"],
                              delta_rival=a["delta_rival"] + b["delta_rival"],
                              delta_margin=a["delta_margin"] + b["delta_margin"],
                              activated=a["telemetry"].get("cc_triggered", 0) > 0
                              or b["telemetry"].get("cc_triggered", 0) > 0))
    return dict(cases=cases, seeds=seed_rows, summary=dict(
        paired_wins=sum(r["paired_margin"] > 0 for r in seed_rows),
        paired_losses=sum(r["paired_margin"] < 0 for r in seed_rows),
        paired_draws=sum(r["paired_margin"] == 0 for r in seed_rows),
        seat_wins=sum(r["margin"] > 0 for r in cases),
        seat_losses=sum(r["margin"] < 0 for r in cases),
        seat_draws=sum(r["margin"] == 0 for r in cases),
        rescued_losses=sum(r["baseline_paired_margin"] <= 0 < r["paired_margin"]
                           for r in seed_rows),
        reversed_wins=sum(r["baseline_paired_margin"] > 0 >= r["paired_margin"]
                          for r in seed_rows),
        own_cash=sum(r["own"] for r in cases),
        rival_cash=sum(r["rival"] for r in cases),
        margin=sum(r["margin"] for r in cases),
        delta_own=sum(r["delta_own"] for r in cases),
        delta_rival=sum(r["delta_rival"] for r in cases),
        delta_margin=sum(r["delta_margin"] for r in cases),
        worst_seat_delta=min(r["delta_margin"] for r in cases),
        worst_paired_delta=min(r["delta_margin"] for r in seed_rows),
        activated_seeds=sum(r["activated"] for r in seed_rows),
        max_internal_call_ms=max(r["max_call_ms"] for r in cases),
        errors=sum(r["telemetry"].get("cc_errors", 0) for r in cases),
    ))


def main() -> None:
    inputs = {name: load(path) for name, path in SOURCES.items()}
    base = inputs["A_incumbent"]
    results = {name: summarize(base, payload) for name, payload in inputs.items()}
    output = HERE / "abc_fixed_dev16_comparison.json"
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")
    for name, result in results.items():
        print(name, json.dumps(result["summary"], sort_keys=True))
        print("changed cases", [(r["seed"], r["seat"], r["delta_own"],
                                 r["delta_rival"], r["delta_margin"],
                                 r["telemetry"].get("cc_predicted_min"))
                                for r in result["cases"] if r["delta_margin"]])
    print(output)


if __name__ == "__main__":
    main()
