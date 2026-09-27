"""Fresh both-seat native trial of three complete public route templates."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
MANIFEST = json.loads((ROOT / "diagnostics" / "top10_goal_20260926" /
                       "double_yarn_highsheep_4routes_summary.json").read_text(encoding="utf8"))
TEMPLATES = {row["team"]: row for row in MANIFEST if row["team"] != "dodsters"}
SELECTION = json.loads((HERE / "seed_selection.json").read_text(encoding="utf8"))
SEEDS = tuple(SELECTION["selected"])


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    spec = str(MAIN) if arm == "control" else f"rawroute:{TEMPLATES[arm]['path']}"
    game = run_game(spec, str(MAIN), seed, seat, False, 144, {})
    return {"arm": arm, "seed": seed, "seat": seat,
            "own_cash": game["candidate_reward"],
            "rival_cash": game["opponent_reward"],
            "margin": game["margin"],
            "statuses": [game["candidate_status"], game["opponent_status"]],
            "shops_at_day6": game["candidate_capture"]["shops"][:2],
            "max_candidate_ms": game["candidate_timing"]["max_ms"]}


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == MAIN_HASH
    assert SELECTION["main_sha256"] == MAIN_HASH and len(SEEDS) == 8
    for row in TEMPLATES.values():
        with gzip.open(row["path"], "rt", encoding="utf8") as handle:
            route = json.load(handle)
        assert len(route["actions"]) == 719
        assert route["action_sha256"] == row["action_sha256"] if "action_sha256" in route else True
    jobs = [(arm, seed, seat) for arm in ("control", *TEMPLATES)
            for seed in SEEDS for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 8 == 0:
                (HERE / "reactive_partial.json").write_text(
                    json.dumps({"completed": len(rows), "rows": rows}, indent=2), encoding="utf8")
                print(f"completed {len(rows)}/{len(jobs)}", flush=True)
    by = {(row["arm"], row["seed"], row["seat"]): row for row in rows}
    summaries = []
    for arm in TEMPLATES:
        seat_rows = []
        paired = []
        for seed in SEEDS:
            pair = []
            for seat in (0, 1):
                control = by[("control", seed, seat)]
                candidate = by[(arm, seed, seat)]
                entry = {"seed": seed, "seat": seat,
                         "control_margin": control["margin"],
                         "candidate_margin": candidate["margin"],
                         "delta_own": candidate["own_cash"] - control["own_cash"],
                         "delta_rival": candidate["rival_cash"] - control["rival_cash"],
                         "delta_margin": candidate["margin"] - control["margin"],
                         "candidate_shops": candidate["shops_at_day6"],
                         "control_shops": control["shops_at_day6"],
                         "statuses": candidate["statuses"]}
                seat_rows.append(entry)
                pair.append(entry)
            paired.append({"seed": seed,
                           "delta_margin": sum(x["delta_margin"] for x in pair),
                           "delta_own": sum(x["delta_own"] for x in pair),
                           "delta_rival": sum(x["delta_rival"] for x in pair),
                           "both_done": all(x["statuses"] == ["DONE", "DONE"] for x in pair)})
        seat_wins = sum(row["delta_margin"] > 0 for row in seat_rows)
        pair_wins = sum(row["delta_margin"] > 0 for row in paired)
        own = sum(row["delta_own"] for row in paired)
        margin = sum(row["delta_margin"] for row in paired)
        worst = min(row["delta_margin"] for row in paired)
        gate = (all(row["both_done"] for row in paired) and pair_wins >= 6
                and seat_wins >= 12 and own > 0 and worst >= -10000)
        summaries.append({"arm": arm, "source_action_sha256": TEMPLATES[arm]["action_sha256"],
                          "paired_seed_wins": pair_wins, "seat_wins": seat_wins,
                          "total_delta_own": own,
                          "total_delta_rival": sum(row["delta_rival"] for row in paired),
                          "total_delta_margin": margin, "worst_paired_delta_margin": worst,
                          "both_done": all(row["both_done"] for row in paired),
                          "gate_pass": gate, "paired": paired, "seats": seat_rows})
    output = {"main_sha256": MAIN_HASH, "seed_selection": SELECTION,
              "summaries": summaries,
              "rows": sorted(rows, key=lambda row: (row["arm"], row["seed"], row["seat"]))}
    (HERE / "reactive_screen.json").write_text(json.dumps(output, indent=2), encoding="utf8")
    for summary in summaries:
        print({key: summary[key] for key in ("arm", "paired_seed_wins", "seat_wins",
                                             "total_delta_own", "total_delta_rival",
                                             "total_delta_margin", "worst_paired_delta_margin",
                                             "both_done", "gate_pass")}, flush=True)


if __name__ == "__main__":
    main()
