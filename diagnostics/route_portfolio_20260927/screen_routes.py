"""Matched-seed, both-seat fixed-route screen of four complete remappings."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from paired_benchmark import run_game  # noqa: E402

NEW_PANEL = HERE.parent / "top20_refresh_2026-09-26_1946" / "main_20routes.json"
OLD_PANEL = HERE.parent / "top100_refresh_2026-09-26_0708" / "main_100routes.json"
VARIANTS = HERE / "variants.json"
OUTPUT = HERE / "fixed_screen.json"


def cases() -> list[dict]:
    new = json.loads(NEW_PANEL.read_text(encoding="utf8"))
    old = json.loads(OLD_PANEL.read_text(encoding="utf8"))
    out = []
    for route in new["routes"]:
        if route["team"] not in ("Boey", "DECEM"):
            continue
        out.append({"team": route["team"], "seed": route["seed"],
                    "path": route["path"], "pair": "icebak" if route["team"] == "Boey" else "bakpizza",
                    "target": True,
                    "baseline": [new["executions"][route["execution_keys"][str(seat)]]
                                 for seat in (0, 1)]})
    mapping = {"Victor @ Tufa Labs": "icebak", "RS Turley": "bakpizza",
               "Yizhou": "bakpizza"}
    for route in old["rows"]:
        if route["team"] not in mapping:
            continue
        baseline = [next(game for game in route["games"] if game["candidate_seat"] == seat)
                    for seat in (0, 1)]
        expected_shops = (("ICE_CREAM_SHOP", "BAKERY") if mapping[route["team"]] == "icebak"
                          else ("BAKERY", "PIZZA_SHOP"))
        assert tuple(baseline[0]["candidate_capture"]["shops"][:2]) == expected_shops
        out.append({"team": route["team"], "seed": route["seed"],
                    "path": route["opponent_path"], "pair": mapping[route["team"]],
                    "target": False, "baseline": baseline})
    assert len(out) == 5
    return out


def play(job: tuple[dict, dict, int]) -> dict:
    variant, case, seat = job
    result = run_game(variant["path"], f"rawroute:{case['path']}",
                      int(case["seed"]), seat, False, 144, {})
    old = case["baseline"][seat]
    assert result["candidate_status"] == result["opponent_status"] == "DONE"
    return {"variant": variant["name"], "team": case["team"],
            "seed": case["seed"], "seat": seat, "target": case["target"],
            "old_own": old["candidate_reward"], "old_rival": old["opponent_reward"],
            "new_own": result["candidate_reward"],
            "new_rival": result["opponent_reward"],
            "old_margin": old["margin"], "new_margin": result["margin"],
            "delta_own": result["candidate_reward"] - old["candidate_reward"],
            "delta_rival": result["opponent_reward"] - old["opponent_reward"],
            "delta_margin": result["margin"] - old["margin"],
            "shops": result["candidate_capture"]["shops"][:2]}


def main() -> None:
    variants = json.loads(VARIANTS.read_text(encoding="utf8"))
    for variant in variants:
        assert hashlib.sha256(Path(variant["path"]).read_bytes()).hexdigest() == variant["sha256"]
    panel = cases()
    jobs = [(variant, case, seat) for variant in variants for case in panel
            if case["pair"] == variant["name"].split("_", 1)[0] for seat in (0, 1)]
    assert len(jobs) == 20
    rows = []
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(play, job) for job in jobs]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(json.dumps({k: row[k] for k in ("variant", "team", "seat", "delta_own", "delta_margin")}), flush=True)
    rows.sort(key=lambda r: (r["variant"], r["team"], r["seat"]))
    summary = []
    for variant in variants:
        subset = [r for r in rows if r["variant"] == variant["name"]]
        target = [r for r in subset if r["target"]]
        assert len(target) == 2
        reversals = [r for r in subset if r["old_margin"] > 0 and r["new_margin"] <= 0]
        gate = (all(r["delta_margin"] >= 5000 and r["delta_own"] > 0 for r in target)
                and not reversals and sum(r["delta_margin"] for r in subset) > 0)
        summary.append({"variant": variant["name"], "target_delta_own": sum(r["delta_own"] for r in target),
                        "target_delta_margin": sum(r["delta_margin"] for r in target),
                        "total_delta_own": sum(r["delta_own"] for r in subset),
                        "total_delta_margin": sum(r["delta_margin"] for r in subset),
                        "winning_control_reversals": [(r["team"], r["seat"]) for r in reversals],
                        "gate_pass": gate})
    OUTPUT.write_text(json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False, indent=2),
                      encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
