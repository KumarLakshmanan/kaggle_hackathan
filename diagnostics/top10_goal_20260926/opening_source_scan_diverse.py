"""Screen structurally different public sources on the same native seed."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path

from opening_source_scan import ROOT, MAIN, PUBLIC, SEED, play

SOURCES = {
    "municef_single": PUBLIC / "039-municef1__lb-2448-single-file-kaggriculture-agent__38fcbf4318bf.py",
    "guru_dynamic": PUBLIC / "054-guruprasaathas111__kaggriculture-fully-dynamic-autonomous-agent__fd7c685e864e.py",
    "mzcao7_ml": PUBLIC / "019-mzcao7__kaggriculture-2476-8-peak-lightgbm-xgboost__f8a9ad8b21f4.py",
    "lynn_better": ROOT / "kaggle_complete_agents_live_2026-09-22_current_page4_top100"
    / "047-lynnsakurai__farming-score-v2-a-better-approach__a766a32bc792.py",
}
OUTPUT = Path(__file__).with_name("opening_source_scan_diverse.json")


def main():
    rows = []
    with ProcessPoolExecutor(max_workers=4) as pool:
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
