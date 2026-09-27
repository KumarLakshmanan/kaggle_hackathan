"""Build a local shop-selected family of Matt Motoki public action plans."""

from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "main.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"
FAMILY = HERE / "matt_route_family"
OUTPUT = ROOT / "exp_matt_shop_family_20260926.py"


def main() -> None:
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    rows = json.loads((FAMILY / "summary.json").read_text(encoding="utf8"))
    assert len(rows) == 8
    packed = {}
    pairs = {}
    firsts = {}
    for row in rows:
        episode = int(row["episode_id"])
        with gzip.open(row["route_path"], "rt", encoding="utf8") as stream:
            payload = json.load(stream)
        actions = payload["actions"]
        assert len(actions) == 719
        packed[episode] = base64.b85encode(zlib.compress(
            json.dumps(actions, separators=(",", ":")).encode("utf8"), 9
        )).decode("ascii")
        pair = tuple(row["first_two_shops"])
        pairs.setdefault(pair, episode)
        firsts.setdefault(pair[0], episode)
    # This route is one of the five with a common exact first-24-action prefix.
    base = 113588519
    assert base in packed
    tail = f'''# EXPERIMENT ONLY: shop-selected Matt public plan family.
import base64 as _msf_b64, json as _msf_json, zlib as _msf_zlib
from copy import deepcopy as _msf_copy
_MSF_PACKED = {packed!r}
_MSF_ACTIONS = {{k: _msf_json.loads(_msf_zlib.decompress(_msf_b64.b85decode(v)))
                for k, v in _MSF_PACKED.items()}}
_MSF_PAIRS = {pairs!r}
_MSF_FIRSTS = {firsts!r}
_MSF_BASE = {base}
_MSF_PARENT = agent
_MSF_STATE = {{}}
_MSF_REPORT = dict(family_switches=0, family_fallbacks=0, family_source=0)
_ALT_MODE = "Original"
_ALT_RAW = _msf_copy(_MSF_ACTIONS[_MSF_BASE][:96])

def _msf_install(route_id):
    global _33_SF_TAPE, _ALT_RAW
    tape = _MSF_ACTIONS[route_id]
    for _route in _IMPL.chassis.routes.values():
        _route[:] = _msf_copy(tape)
    _33_SF_TAPE = _msf_copy(tape)
    _ALT_RAW = _msf_copy(tape[:96])
    _E402_CACHE.clear()

_msf_install(_MSF_BASE)

def agent(observation, configuration=None):
    seat = int(observation["player"])
    step = int(observation["step"])
    if step == 0:
        _MSF_STATE[seat] = _MSF_BASE
        _MSF_REPORT.update(family_switches=0, family_fallbacks=0,
                           family_source=_MSF_BASE)
        _msf_install(_MSF_BASE)
    shops = tuple(observation["town"]["unlocked_shops"][:2])
    if len(shops) >= 2 and shops in _MSF_PAIRS:
        selected = _MSF_PAIRS[shops]
    elif shops and shops[0] in _MSF_FIRSTS:
        selected = _MSF_FIRSTS[shops[0]]
    else:
        selected = _MSF_BASE
        if shops:
            _MSF_REPORT["family_fallbacks"] += 1
    if selected != _MSF_STATE.get(seat):
        _msf_install(selected)
        _MSF_STATE[seat] = selected
        _MSF_REPORT["family_switches"] += 1
        _MSF_REPORT["family_source"] = selected
    action = _MSF_PARENT(observation, configuration)
    _MSF_REPORT.update(getattr(_MSF_PARENT, "telemetry", {{}}))
    return action

agent.telemetry = _MSF_REPORT
kaggle_submission_agent = agent

'''
    source = SOURCE.read_text(encoding="utf8")
    assert source.count(MARKER) == 1
    candidate = source.replace(MARKER, tail + MARKER)
    ast.parse(candidate)
    OUTPUT.write_text(candidate, encoding="utf8")
    print(json.dumps({
        "candidate": str(OUTPUT),
        "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "base": base, "pairs": len(pairs), "firsts": len(firsts),
        "source": EXPECTED,
    }, indent=2))


if __name__ == "__main__":
    main()
