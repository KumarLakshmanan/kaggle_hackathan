"""Confirm route 10 on both seats and a same-episode winning control."""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

CANDIDATE = ROOT / "exp_route_probe_20260926.py"
MANIFEST = ROOT / "diagnostics/top100_refresh_2026-09-26/summary.json"
BASELINE = ROOT / "diagnostics/top100_refresh_2026-09-26/main_local_100routes.json"
TEAMS = ("mtmr_s1", "YumeNeko", "Lucas Boesen", "forever young")
OUTPUT = Path(__file__).with_name("route10_yarn_pizza_confirm.json")


def play(job):
    entry, seat = job
    row = run_game(str(CANDIDATE), f"rawroute:{entry['path']}", int(entry["seed"]),
                   seat, False, 144, {"_ROUTE_PROBE_ID": 10,
                                      "_ROUTE_PROBE_SHOPS": ["YARN_STORE", "PIZZA_SHOP"]})
    capture = row.pop("candidate_capture")
    return {
        "team": entry["team"], "action_sha256": entry["action_sha256"],
        "seed": entry["seed"], "seat": seat,
        "shops": capture["shops"] if capture else None,
        "own_cash": row["candidate_reward"],
        "rival_cash": row["opponent_reward"],
        "margin": row["margin"],
        "statuses": [row["candidate_status"], row["opponent_status"]],
    }


def main():
    entries = json.loads(MANIFEST.read_text(encoding="utf8"))
    chosen = [entry for entry in entries if entry["team"] in TEAMS]
    assert len(chosen) == len(TEAMS)
    baseline = json.loads(BASELINE.read_text(encoding="utf8"))
    old = {entry["action_sha256"]: entry for entry in baseline["rows"]}
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, [(entry, seat) for entry in chosen for seat in (0, 1)]))
    summary = {}
    for entry in chosen:
        part = [row for row in rows if row["action_sha256"] == entry["action_sha256"]]
        previous = old[entry["action_sha256"]]["pair_margin"]
        summary[entry["team"]] = {
            "shops": part[0]["shops"],
            "baseline_pair_margin": previous,
            "route10_pair_margin": sum(row["margin"] for row in part),
            "delta": sum(row["margin"] for row in part) - previous,
            "all_done": all(row["statuses"] == ["DONE", "DONE"] for row in part),
        }
    OUTPUT.write_text(json.dumps({
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "summary": summary, "rows": rows,
    }, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
