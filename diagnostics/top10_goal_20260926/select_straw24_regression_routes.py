"""Select routes where the current physical-mirror gate ever opens."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PANELS = (
    ("sep25", ROOT / "diagnostics/top100_current_2026-09-25/summary.json",
     HERE / "mirror12_top100_old_routes.json"),
    ("sep26", ROOT / "diagnostics/top100_refresh_2026-09-26/summary.json",
     ROOT / "diagnostics/top100_refresh_2026-09-26/main_local_100routes.json"),
)


def identity(row):
    return row["action_sha256"], int(row["seed"]), int(row["source_seat"])


def main():
    for label, summary_path, baseline_path in PANELS:
        entries = json.loads(summary_path.read_text(encoding="utf8"))
        baseline = json.loads(baseline_path.read_text(encoding="utf8"))
        eligible = {
            identity(row) for row in baseline["rows"]
            if any((game.get("candidate_telemetry") or {}).get("clone_gate_equal_turns", 0) > 0
                   for game in row["games"])
        }
        selected = [row for row in entries if identity(row) in eligible]
        assert len(selected) == len(eligible)
        output = HERE / f"mirror_straw24_{label}_eligible_summary.json"
        output.write_text(json.dumps(selected, indent=2, ensure_ascii=False),
                          encoding="utf8")
        print(label, len(entries), len(selected), output)


if __name__ == "__main__":
    main()
