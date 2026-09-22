"""Benchmark main.py against a previously materialized route-panel report."""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import io
import json
from pathlib import Path

from paired_benchmark import run_game


ROOT = Path(__file__).resolve().parent


def _entries(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        source_rows = payload
    elif "rows" in payload:
        source_rows = payload.get("rows", [])
    else:
        # Also accept the loss-regime report emitted by analyze_loss_regimes.py.
        source_rows = payload.get("loss_routes", [])
    seen = set()
    result = []
    for row in source_rows:
        route = str(row.get("opponent_path") or row.get("path") or "")
        route_path = Path(route)
        if not route_path.is_absolute():
            candidates = [ROOT / route_path, path.parent / route_path]
            route = str(next((candidate for candidate in candidates if candidate.is_file()), candidates[0]))
        seed = int(row.get("seed", 0))
        key = (route, seed)
        if not route or key in seen:
            continue
        seen.add(key)
        result.append({"route": route, "seed": seed, "team": row.get("team")})
    return result


def _play(job):
    candidate, route, seed, seat = job
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            row = run_game(
                candidate=candidate,
                opponent=f"rawroute:{route}",
                seed=seed,
                candidate_seat=seat,
                debug=False,
                capture_step=None,
                candidate_overrides={},
            )
        return {**row, "opponent_path": route}
    except Exception as error:  # noqa: BLE001 - preserve panel progress
        return {"seed": seed, "candidate_seat": seat, "opponent_path": route,
                "error": f"{type(error).__name__}: {error}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate", default="main.py")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    entries = _entries(args.input)
    jobs = [(args.candidate, item["route"], item["seed"], seat) for item in entries for seat in (0, 1)]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 10 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)
    good = [row for row in rows if "error" not in row]
    margins = [float(row["margin"]) for row in good]
    paired = {}
    for row in good:
        paired[int(row["seed"])] = paired.get(int(row["seed"]), 0.0) + float(row["margin"])
    summary = {
        "games": len(good),
        "errors": len(rows) - len(good),
        "wins": sum(margin > 0 for margin in margins),
        "draws": sum(margin == 0 for margin in margins),
        "losses": sum(margin < 0 for margin in margins),
        "paired_wins": sum(margin > 0 for margin in paired.values()),
        "paired_draws": sum(margin == 0 for margin in paired.values()),
        "paired_losses": sum(margin < 0 for margin in paired.values()),
        "mean_margin": sum(margins) / len(margins) if margins else None,
        "paired_mean_margin": sum(paired.values()) / len(paired) if paired else None,
    }
    payload = {"input": str(args.input), "rows": rows, "summary": summary}
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("SUMMARY " + json.dumps(summary, sort_keys=True))
    print(f"wrote={args.output}")


if __name__ == "__main__":
    main()
