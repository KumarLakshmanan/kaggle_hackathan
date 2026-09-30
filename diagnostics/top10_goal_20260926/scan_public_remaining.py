"""Screen remaining runnable public source files for a stronger day-six farm."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
PUBLIC = ROOT / "kaggle_complete_agents_live_2026-09-23_page6_top100"
SEED = 2610910
OUTPUT = Path(__file__).with_name("public_remaining_opening_scan.json")
EXCLUDE_PREFIX = {
    "008-", "019-", "025-", "039-", "054-", "065-", "068-", "087-", "090-",
}


def play(path: Path) -> dict:
    name = path.name
    try:
        row = run_game(str(path), str(MAIN), SEED, 0, False, 144, {})
        capture = row["candidate_capture"]
        result = {
            "name": name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "margin": row["margin"],
            "status": [row["candidate_status"], row["opponent_status"]],
        }
        if capture:
            result["shops"] = capture["shops"]
            result["day6_counts"] = capture["farms"][0]["counts"]
            result["day6_money"] = capture["farms"][0]["money"]
        return result
    except Exception as exc:
        return {"name": name, "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    sources = [p for p in sorted(PUBLIC.glob("*.py"))
               if not any(p.name.startswith(prefix) for prefix in EXCLUDE_PREFIX)]
    rows = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(play, path): path.name for path in sources}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    OUTPUT.write_text(json.dumps({
        "seed": SEED,
        "main_sha256": hashlib.sha256(MAIN.read_bytes()).hexdigest(),
        "rows": rows,
    }, indent=2, ensure_ascii=False), encoding="utf8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
