"""Screen complete public sources for a portable alternative day-six farm."""

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
SOURCES = {
    "flexonafft": PUBLIC / "008-flexonafft__kaggriculture-most-powerfull-route__9cb64592d5e1.py",
    "ahmed_early_yarn": PUBLIC / "090-ahmedberatozer__kaggriculture-v50-early-yarn-commit__2e6ca2db4630.py",
    "sunil_top10": PUBLIC / "088-sunil123kumar__kaggriculture-top-10-public-bots__92fef310abf8.py",
}
SEED = 2610910
OUTPUT = Path(__file__).with_name("opening_source_scan.json")


def play(item):
    name, path = item
    try:
        row = run_game(str(path), str(MAIN), SEED, 0, False, 144, {})
        capture = row["candidate_capture"]
        if capture is None:
            return {"name": name,
                    "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "margin": row["margin"],
                    "own_cash": row["candidate_reward"],
                    "rival_cash": row["opponent_reward"],
                    "candidate_status": row["candidate_status"],
                    "opponent_status": row["opponent_status"],
                    "error": "no day-6 capture"}
        farm = capture["farms"][0]
        return {"name": name, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "margin": row["margin"], "own_cash": row["candidate_reward"],
                "rival_cash": row["opponent_reward"],
                "candidate_status": row["candidate_status"],
                "opponent_status": row["opponent_status"],
                "shops": capture["shops"], "day6_counts": farm["counts"],
                "day6_money": farm["money"]}
    except Exception as error:
        return {"name": name, "error": f"{type(error).__name__}: {error}"}


def main():
    rows = []
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(play, item): item[0] for item in SOURCES.items()}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    OUTPUT.write_text(json.dumps({
        "seed": SEED, "main_sha256": hashlib.sha256(MAIN.read_bytes()).hexdigest(),
        "rows": rows,
    }, indent=2, ensure_ascii=False), encoding="utf8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
