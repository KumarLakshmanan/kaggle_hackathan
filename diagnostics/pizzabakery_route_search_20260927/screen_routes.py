"""Seat-0 fixed-tape development screen for all compatible complete routes."""

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

PANEL = HERE.parent / "top100_refresh_2026-09-26_0708" / "main_100routes.json"
TARGET = ["PIZZA_SHOP", "BAKERY"]
SOURCE_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"


def cases() -> list[dict]:
    panel = json.loads(PANEL.read_text(encoding="utf8"))
    assert panel["candidate_sha256"] == SOURCE_HASH
    output = []
    for row in panel["rows"]:
        old = next(game for game in row["games"] if game["candidate_seat"] == 0)
        if old["candidate_capture"]["shops"][:2] == TARGET:
            assert old["margin"] < 0
            output.append({"team": row["team"], "seed": row["seed"],
                           "opponent_path": row["opponent_path"],
                           "old_own": old["candidate_reward"],
                           "old_rival": old["opponent_reward"],
                           "old_margin": old["margin"]})
    assert len(output) == 3
    return output


def play(variant: dict, case: dict) -> dict:
    game = run_game(variant["path"], f"rawroute:{case['opponent_path']}",
                    int(case["seed"]), 0, False, 144, {})
    assert game["candidate_status"] == game["opponent_status"] == "DONE"
    assert game["candidate_capture"]["shops"][:2] == TARGET
    return {"route": variant["route"], "team": case["team"],
            "seed": case["seed"], "own": game["candidate_reward"],
            "rival": game["opponent_reward"], "margin": game["margin"],
            "delta_own": game["candidate_reward"] - case["old_own"],
            "delta_rival": game["opponent_reward"] - case["old_rival"],
            "delta_margin": game["margin"] - case["old_margin"],
            "max_ms": game["candidate_timing"]["max_ms"]}


def main() -> None:
    assert hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest() == SOURCE_HASH
    variants = json.loads((HERE / "variants.json").read_text(encoding="utf8"))
    assert len(variants) == 39
    assert all(hashlib.sha256(Path(v["path"]).read_bytes()).hexdigest() == v["sha256"]
               for v in variants)
    targets = cases()
    rows = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(play, variant, case)
                   for variant in variants for case in targets]
        for index, future in enumerate(as_completed(futures), 1):
            rows.append(future.result())
            if index % 15 == 0:
                print("completed", index, "of", len(futures), flush=True)
    rows.sort(key=lambda row: (row["route"], row["team"]))
    scores = []
    for variant in variants:
        sub = [row for row in rows if row["route"] == variant["route"]]
        assert len(sub) == 3
        score = {"route": variant["route"],
                 "min_margin_delta": min(row["delta_margin"] for row in sub),
                 "total_margin_delta": sum(row["delta_margin"] for row in sub),
                 "total_own_delta": sum(row["delta_own"] for row in sub),
                 "all_own_positive": all(row["delta_own"] > 0 for row in sub),
                 "all_margin_positive": all(row["delta_margin"] > 0 for row in sub)}
        score["gate_pass"] = (score["all_own_positive"] and score["all_margin_positive"]
                              and score["total_margin_delta"] >= 15000)
        scores.append(score)
    scores.sort(key=lambda s: (s["min_margin_delta"], s["total_margin_delta"]),
                reverse=True)
    selected = scores[0]
    payload = {"source_hash": SOURCE_HASH, "targets": targets,
               "selected": selected, "scores": scores, "rows": rows}
    (HERE / "fixed_screen.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                             encoding="utf8")
    print("selected", json.dumps(selected, ensure_ascii=False), flush=True)
    print("top5", json.dumps(scores[:5], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
