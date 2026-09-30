"""Feed a complete saved high-strawberry tape through the existing agent layers.

Experiment only: the resulting candidate is a local counterfactual, not a
promoted submission. Every chassis route receives the same donor plan so shop
routing cannot silently select the old farm. `_ALT_RAW` is updated because the
opening installer otherwise restores the old first 96 turns on step zero.
"""

from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
EXPECTED_SOURCE = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
PANEL = ROOT / "diagnostics" / "top100_refresh_2026-09-26"
DONORS = {
    "dsm": PANEL / "DSM-submission-56557996-episode-113531265-seat1.json.gz",
    "lucas": PANEL / "Lucas-Boesen-submission-56550474-episode-113534433-seat1.json.gz",
    "matt": PANEL / "Matt-Motoki-submission-56561861-episode-113535464-seat0.json.gz",
}
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("donor", choices=sorted(DONORS))
    args = parser.parse_args()

    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SOURCE
    path = DONORS[args.donor]
    with gzip.open(path, "rt", encoding="utf8") as stream:
        payload = json.load(stream)
    actions = payload["actions"]
    assert len(actions) == 719
    assert all(set(action) == {"farmer", "hands", "market"} for action in actions)
    packed = base64.b85encode(zlib.compress(
        json.dumps(actions, separators=(",", ":")).encode("utf8"), 9
    )).decode("ascii")

    tail = f'''# EXPERIMENT ONLY: complete {args.donor} plan with existing adaptive wrappers.
# Source action hash: {payload["metadata"]["action_sha256"]}
import base64 as _adr_b64, json as _adr_json, zlib as _adr_zlib
from copy import deepcopy as _adr_copy
_ADR_ACTIONS = _adr_json.loads(_adr_zlib.decompress(_adr_b64.b85decode({packed!r})))
for _adr_tape in _IMPL.chassis.routes.values():
    _adr_tape[:] = _adr_copy(_ADR_ACTIONS)
_ALT_RAW = _adr_copy(_ADR_ACTIONS[:96])
_ALT_MODE = "Original"
_33_SF_TAPE = _adr_copy(_ADR_ACTIONS)
del _adr_tape

'''
    source = SOURCE.read_text(encoding="utf8")
    assert source.count(MARKER) == 1
    candidate = source.replace(MARKER, tail + MARKER)
    ast.parse(candidate)
    output = ROOT / f"exp_adaptive_donor_{args.donor}_20260926.py"
    output.write_text(candidate, encoding="utf8")
    print(json.dumps({
        "donor": args.donor,
        "donor_action_hash": payload["metadata"]["action_sha256"],
        "source_sha256": EXPECTED_SOURCE,
        "candidate_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "output": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
