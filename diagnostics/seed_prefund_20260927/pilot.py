"""Four predeclared top-20 mechanism games, both seats of Boey/Vadim."""

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


def play(job):
    candidate, sha, row, seat = job
    assert hashlib.sha256(Path(candidate).read_bytes()).hexdigest() == sha
    game = run_game(candidate, "rawroute:" + row["path"], row["seed"], seat, False, 144, {})
    return {"team": row["team"], "team_id": row["team_id"], "rank": row["rank"],
            "episode_id": row["episode_id"], **game}


def main():
    build = json.loads((HERE / "build_manifest.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest() == build["plan_sha256"]
    assert hashlib.sha256(Path(build["candidate"]).read_bytes()).hexdigest() == build["candidate_sha256"]
    routes = json.loads((ROOT / "diagnostics/current_top20_20260927_163500/routes/summary.json").read_text(encoding="utf-8"))
    selected = [r for r in routes if r["team"] in ("Boey", "Vadim Vasilenko")]
    assert len(selected) == 2
    baseline = json.loads((ROOT / "diagnostics/current_top20_20260927_163500/assessment.json").read_text(encoding="utf-8"))
    old = {(g["team"], g["candidate_seat"]): g for g in baseline["games"]}
    jobs = [(build["candidate"], build["candidate_sha256"], row, seat)
            for row in selected for seat in (0, 1)]
    output = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
              "candidate_sha256": build["candidate_sha256"],
              "plan_sha256": build["plan_sha256"], "games": []}
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, j) for j in jobs]):
            game = future.result()
            game["old_margin"] = old[game["team"], game["candidate_seat"]]["margin"]
            output["games"].append(game)
            (HERE / "pilot.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
            print(game["team"], game["candidate_seat"], game["old_margin"], game["margin"],
                  (game.get("candidate_telemetry") or {}).get("seed_prefund_turns"), flush=True)
    output["complete"] = True
    (HERE / "pilot.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
