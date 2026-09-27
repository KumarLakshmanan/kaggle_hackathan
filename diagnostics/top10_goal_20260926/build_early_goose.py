"""Build early goose candidate and six-route original-shop development panel."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "main.py"
TAIL = HERE / "early_goose_tail.py"
OUT = ROOT / "exp_early_goose_20260926.py"
EXPECTED_BASE = "6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076"
EPISODES = (113208346, 113212937, 113212486,
            113216232, 113215474, 113214299)


def main():
    source = BASE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == EXPECTED_BASE
    raw = source + b"\n\n" + TAIL.read_bytes()
    compile(raw, str(OUT), "exec")
    OUT.write_bytes(raw)
    all_routes = json.loads((ROOT / "diagnostics/top100_current_2026-09-25/summary.json")
                            .read_text(encoding="utf-8"))
    selected = [r for r in all_routes if int(r["episode_id"]) in EPISODES
                and r["team"] in {"Boey", "ActiveMusyoku", "Ryo Hasegawa",
                                  "QQ农场", "Gatswei", "Planned Economy"}]
    assert len(selected) == len(EPISODES)
    summary = HERE / "early_goose_6routes_summary.json"
    summary.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
    print(OUT, hashlib.sha256(raw).hexdigest())
    print(summary, hashlib.sha256(summary.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
