"""One-seat development search; no claim of independent validation."""
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


def play(job):
    pair, episode, case = job
    row = run_game(str(ROOT / "exp_shunki_route_search_20260927.py"),
                   "rawroute:" + case["route_path"], case["seed"], 0, False, 144,
                   {"_PORT_PAIR": pair, "_PORT_EPISODE": episode})
    assert row["candidate_capture"]["shops"][:2] == pair
    assert row["candidate_telemetry"]["portfolio_turns"] == 575
    return {"shops": pair, "episode": episode, "team": case["team"], "seed": case["seed"],
            "own_cash": row["candidate_reward"], "rival_cash": row["opponent_reward"],
            "margin": row["margin"], "statuses": [row["candidate_status"], row["opponent_status"]],
            "max_ms": row["candidate_timing"]["max_ms"]}


if __name__ == "__main__":
    manifest = json.loads((HERE / "search_manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(Path(manifest["candidate"]).read_bytes()).hexdigest() == manifest["candidate_sha256"]
    jobs = [(t["shops"], episode, case) for t in manifest["targets"]
            for episode in t["eligible"] for case in t["cases"]]
    rows = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            rows.append(future.result())
            if len(rows) % 12 == 0 or len(rows) == len(jobs):
                (HERE / "search_partial.json").write_text(json.dumps({"rows": rows}, indent=2, ensure_ascii=False), encoding="utf8")
                print(f"schedule search {len(rows)}/{len(jobs)}; wins so far {sum(r['margin'] > 0 for r in rows)}", flush=True)
    (HERE / "search_results.json").write_text(json.dumps({"candidate_sha256": manifest["candidate_sha256"], "rows": rows}, indent=2, ensure_ascii=False), encoding="utf8")
