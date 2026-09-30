"""Freeze the appended candidate and an immutable hash-named backup."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE_SHA = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base = ROOT / "main_uploaded_purchase_iterated_20260927_4eeac9c3.py"
    current = ROOT / "main.py"
    tail = HERE / "tail.py"
    plan = HERE / "PLAN.md"
    assert digest(base) == digest(current) == BASE_SHA
    raw = base.read_bytes() + b"\n\n" + tail.read_bytes()
    compile(raw, "exp_seed_prefund_20260927.py", "exec")
    sha = hashlib.sha256(raw).hexdigest()
    candidate = ROOT / "exp_seed_prefund_20260927.py"
    backup = ROOT / f"main_candidate_seed_prefund_20260927_{sha[:8]}.py"
    assert not candidate.exists() and not backup.exists()
    candidate.write_bytes(raw)
    backup.write_bytes(raw)
    output = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "base": str(base), "base_sha256": BASE_SHA,
        "plan_sha256": digest(plan), "tail_sha256": digest(tail),
        "candidate": str(candidate), "candidate_sha256": sha,
        "backup": str(backup), "entrypoint": "kaggle_seed_prefund_entrypoint",
        "main_unchanged": digest(current) == BASE_SHA,
    }
    (HERE / "build_manifest.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
