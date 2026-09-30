"""Freeze the current local policy's fresh top-100 saved-route losses."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / "summary.json").read_text(encoding="utf8"))
results = json.loads((HERE / "main_local_100routes.json").read_text(encoding="utf8"))
key = lambda row: (row["action_sha256"], int(row["seed"]), int(row["source_seat"]))
losses = {key(row) for row in results["rows"] if row["pair_margin"] < 0}
selected = [row for row in manifest if key(row) in losses]
assert len(selected) == len(losses) == 31
dest = HERE / "losses_31_summary.json"
dest.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf8")
print(dest)
