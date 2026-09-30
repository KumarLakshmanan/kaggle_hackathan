import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


if __name__ == "__main__":
    source = HERE/"source_untrusted.py.txt"
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == "f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2"
    target = ROOT/"public_market_smart_f6a756cf_20260927.py"
    target.write_bytes(raw)
    rows = []
    for seed in range(2657000, 2657004):
        for seat in (0, 1):
            r = run_game(str(target), str(ROOT/"main_uploaded_shunki_schedule_20260927_3cc0f69f.py"), seed, seat, False, 144, {})
            rows.append(r)
            (HERE/"pilot.json").write_text(json.dumps({"candidate_sha256": digest, "rows": rows}, indent=2), encoding="utf8")
            print(seed, seat, r["margin"], r["candidate_status"], r["opponent_status"], flush=True)
