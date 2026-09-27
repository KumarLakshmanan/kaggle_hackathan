"""Build the isolated day-26 route-2 candidate from the current main snapshot."""

from pathlib import Path
import hashlib
import re


ROOT = Path(__file__).resolve().parents[2]
source_path = ROOT / "main.py"
output_path = ROOT / "exp_early_route2_20260927.py"
source = source_path.read_text(encoding="utf-8")
source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
expected_hash = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
if source_hash != expected_hash:
    raise SystemExit(f"main.py changed: {source_hash}; expected {expected_hash}")

lines = source.splitlines(keepends=True)
replacements = []
for number, line in enumerate(lines, start=1):
    if len(line) > 1000 or line.lstrip().startswith("#"):
        # Keep embedded compressed route data and source comments immutable.
        continue
    changed, count = re.subn(r"(?<!\d)648(?!\d)", "624", line)
    if count:
        replacements.append((number, line.rstrip(), changed.rstrip()))
        lines[number - 1] = changed

if not 15 <= len(replacements) <= 35:
    raise SystemExit(f"Unexpected threshold replacement count {len(replacements)}")
output_path.write_text("".join(lines), encoding="utf-8")
print(f"source_sha256={source_hash}")
print(f"candidate_sha256={hashlib.sha256(output_path.read_bytes()).hexdigest()}")
print(f"replaced_lines={len(replacements)}")
for number, old, new in replacements:
    print(f"{number}: {old}\n -> {new}")
