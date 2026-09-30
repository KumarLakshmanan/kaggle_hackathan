"""Freeze every double-Yarn route from the fresh top-100 panel."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FRESH = ROOT / "diagnostics" / "top100_refresh_2026-09-26_0708"
SOURCE = FRESH / "routes" / "summary.json"
BASE = FRESH / "main_100routes.json"
OUTPUT = HERE / "double_yarn_highsheep_4routes_summary.json"


def main():
    source = {str(Path(x["path"]).resolve()): x
              for x in json.loads(SOURCE.read_text(encoding="utf8"))}
    baseline = json.loads(BASE.read_text(encoding="utf8"))
    selected = []
    for row in baseline["rows"]:
        captured = row["games"][0]["candidate_capture"]
        if captured["shops"] != ["YARN_STORE", "YARN_STORE"]:
            continue
        entry = source[str(Path(row["opponent_path"]).resolve())]
        selected.append(entry)
        player = int(captured["player"])
        rival = captured["farms"][1-player]["counts"]
        print(entry["team"], "sheep", rival.get("SHEEP", 0),
              "paired_margin", sum(g["margin"] for g in row["games"]))
    assert len(selected) == 4, len(selected)
    assert {x["team"] for x in selected} == {"mhw", "ShunkiKyoya", "AI是我的豆包", "dodsters"}
    OUTPUT.write_text(json.dumps(selected, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
