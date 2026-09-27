"""Screen saved high-strawberry routes on fresh native seeds against main."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
LOSSES = ROOT / "diagnostics/top100_refresh_2026-09-26/losses_31_summary.json"
TEAMS = ("mtmr_s1", "YumeNeko", "Lucas Boesen", "Matt Motoki", "marwar22")
SEEDS = tuple(range(2610960, 2610964))
OUTPUT = Path(__file__).with_name("high_straw_raw_screen.json")


def play(job):
    team, path, seed, seat = job
    row = run_game(f"rawroute:{path}", str(MAIN), seed, seat, False, 144, {})
    capture = row.pop("candidate_capture")
    return {
        "team": team, "seed": seed, "seat": seat,
        "shops": capture["shops"] if capture else None,
        "day6_counts": capture["farms"][seat]["counts"] if capture else None,
        "own_cash": row["candidate_reward"],
        "rival_cash": row["opponent_reward"],
        "margin": row["margin"],
        "statuses": [row["candidate_status"], row["opponent_status"]],
    }


def main():
    entries = json.loads(LOSSES.read_text(encoding="utf8"))
    by_team = {entry["team"]: entry for entry in entries}
    assert all(team in by_team for team in TEAMS)
    jobs = [(team, by_team[team]["path"], seed, seat)
            for team in TEAMS for seed in SEEDS for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(row["team"], row["seed"], row["seat"],
                  f"{row['margin']:+.0f}", row["statuses"], flush=True)
    summary = {}
    for team in TEAMS:
        part = [row for row in rows if row["team"] == team]
        summary[team] = {
            "wins": sum(row["margin"] > 0 for row in part),
            "margin_sum": sum(row["margin"] for row in part),
            "all_done": all(row["statuses"] == ["DONE", "DONE"] for row in part),
            "day6_counts": part[0]["day6_counts"],
        }
    OUTPUT.write_text(json.dumps({
        "main_sha256": hashlib.sha256(MAIN.read_bytes()).hexdigest(),
        "route_sha256": {team: hashlib.sha256(Path(by_team[team]["path"]).read_bytes()).hexdigest()
                         for team in TEAMS},
        "seeds": SEEDS, "summary": summary, "rows": rows,
    }, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2), flush=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
