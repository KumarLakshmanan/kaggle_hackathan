"""Rank local Python agents against a compact route panel.

This is a local comparison harness for downloaded public examples.  It never
submits anything to Kaggle and keeps import/runtime errors in the report
instead of aborting the whole pool.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import io
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


def _unique(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        digest = str(entry["action_sha256"])
        if digest in seen:
            continue
        seen.add(digest)
        result.append(entry)
    return result


def _play(job: tuple[str, str, int, int]) -> dict[str, Any]:
    candidate, opponent_path, seed, seat = job
    try:
        # Public notebooks often print banners at import time.  Keep those
        # diagnostics inside the per-job worker so a large pool cannot flood
        # the parent pipe and terminate the benchmark before writing JSON.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            row = run_game(
                candidate=candidate,
                opponent=f"rawroute:{opponent_path}",
                seed=seed,
                candidate_seat=seat,
                debug=False,
                capture_step=None,
                candidate_overrides={},
            )
        row["candidate"] = candidate
        row["opponent_path"] = opponent_path
        return row
    except Exception as error:  # noqa: BLE001 - preserve pool progress
        return {
            "candidate": candidate,
            "opponent_path": opponent_path,
            "seed": seed,
            "candidate_seat": seat,
            "error": f"{type(error).__name__}: {error}",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument(
        "--candidate-manifest",
        type=Path,
        help="Optional extraction manifest; benchmark only rows marked has_agent.",
    )
    parser.add_argument("--opponents", type=Path, required=True)
    parser.add_argument("--extra-candidate", action="append", type=Path, default=[])
    parser.add_argument("--max-candidates", type=int, default=20)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    if args.candidate_manifest:
        manifest = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
        manifest_rows = manifest.get("sources", manifest.get("agents", []))
        candidates = [
            args.candidate_root.parent / row["source"]
            for row in manifest_rows
            if (row.get("has_agent") or row.get("status") == "extracted") and row.get("source")
        ]
        candidates = sorted(
            (path for path in candidates if path.is_file()),
            key=lambda path: (-path.stat().st_size, str(path)),
        )
    else:
        candidates = sorted(args.candidate_root.rglob("*.py"), key=lambda path: (-path.stat().st_size, str(path)))
    candidates.extend(args.extra_candidate)
    seen_paths: set[str] = set()
    selected: list[Path] = []
    for path in candidates:
        resolved = str(path.resolve())
        if resolved in seen_paths or not path.is_file():
            continue
        seen_paths.add(resolved)
        selected.append(path)
        if len(selected) >= max(1, args.max_candidates):
            break
    opponents = _unique(json.loads(args.opponents.read_text(encoding="utf-8")))
    jobs = [
        (str(candidate.resolve()), str(Path(entry["path"]).resolve()), int(entry["seed"]), seat)
        for candidate in selected
        for entry in opponents
        for seat in (0, 1)
    ]
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for index, row in enumerate(pool.map(_play, jobs), start=1):
            rows.append(row)
            if "error" in row:
                print(f"[{index}/{len(jobs)}] ERROR {Path(row['candidate']).name}: {row['error']}", flush=True)

    groups: list[dict[str, Any]] = []
    for candidate in selected:
        path = str(candidate.resolve())
        subset = [row for row in rows if row["candidate"] == path]
        good = [row for row in subset if "error" not in row]
        margins = [float(row["margin"]) for row in good]
        paired: dict[int, float] = {}
        for row in good:
            paired.setdefault(int(row["seed"]), 0.0)
            paired[int(row["seed"])] += float(row["margin"])
        groups.append(
            {
                "candidate": path,
                "games": len(good),
                "errors": len(subset) - len(good),
                "wins": sum(value > 0 for value in margins),
                "draws": sum(value == 0 for value in margins),
                "losses": sum(value < 0 for value in margins),
                "paired_wins": sum(value > 0 for value in paired.values()),
                "paired_draws": sum(value == 0 for value in paired.values()),
                "paired_losses": sum(value < 0 for value in paired.values()),
                "mean_margin": sum(margins) / len(margins) if margins else None,
                "paired_mean_margin": sum(paired.values()) / len(paired) if paired else None,
            }
        )
    groups.sort(key=lambda group: (group["paired_losses"], -(group["paired_mean_margin"] or float("-inf"))))
    payload = {"candidates": len(selected), "opponents": len(opponents), "rows": rows, "groups": groups}
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for group in groups:
        print(
            f"candidate={Path(group['candidate']).name} games={group['games']} errors={group['errors']} "
            f"wins={group['wins']} losses={group['losses']} "
            f"paired={group['paired_wins']}/{group['paired_wins'] + group['paired_losses']} "
            f"mean={group['paired_mean_margin']}",
            flush=True,
        )
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
