"""Re-trace only the already-scored DECEM fixed-tape policy-seat fixtures."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kaggle_environments import __version__ as ENGINE_VERSION  # noqa: E402
from trace_paired_game_events import run  # noqa: E402

HERE = Path(__file__).resolve().parent
ROUTE = ROOT / "diagnostics/current_top20_20260927_172258/routes/DECEM-submission-56601866-episode-114267880-seat1.json.gz"
RAW_REPLAY = ROOT / "diagnostics/current_top20_20260927_172258/raw_archive/episode-114267880-replay.json.gz"
SCREEN = ROOT / "diagnostics/historical_policy_screen_20260928/screen.json"
SEED = 1390733823
EXPECTED_ENGINE = "1.32.7"
EXPECTED_ROUTE_SHA = "a326e4f9e779ce21762e8cac5a0058884a1676271f296bf4c2291180b0175226"
EXPECTED_REPLAY_SHA = "1d6a1d7ce66a2e07bd1576528e930ac5f13777fdb88f673eea3aa0a4c34c8072"
EXPECTED_ACTION = "a326e4f9e779ce21762e8cac5a0058884a1676271f296bf4c2291180b0175226"
SOURCES = {
    "4ee": (ROOT / "main.py", "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed", -62163.0),
    "V43": (ROOT / "main_v43_current.py", "69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3", -14744.0),
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def action_digest(actions: list) -> str:
    raw = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha_bytes(raw)


def main() -> None:
    assert ENGINE_VERSION == EXPECTED_ENGINE, ENGINE_VERSION
    route_obj = json.loads(gzip.decompress(ROUTE.read_bytes()))
    assert len(route_obj["actions"]) == 719
    assert action_digest(route_obj["actions"]) == EXPECTED_ACTION
    replay_raw = gzip.decompress(RAW_REPLAY.read_bytes())
    assert sha_bytes(replay_raw) == EXPECTED_REPLAY_SHA

    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    v43_row = next(item for item in screen["candidate_fixture_results"]
                   if item["candidate"] == "v43_decoded"
                   and item["fixture"]["team"] == "DECEM")
    prior_v43 = {int(row["candidate_seat"]): float(row["margin"])
                 for row in v43_row["seats"]}
    assert prior_v43 == {0: -14744.0, 1: -14744.0}, prior_v43
    assessment = json.loads((ROOT / "diagnostics/current_top20_20260927_172258/assessment.json").read_text(encoding="utf-8"))
    incumbent = [row for row in assessment["games"]
                 if row["team"] == "DECEM" and int(row["episode_id"]) == 114267880]
    assert {int(row["candidate_seat"]): float(row["margin"]) for row in incumbent} == {
        0: -62163.0, 1: -62163.0
    }
    assert all(sha_file(path) == expected for path, expected, _ in SOURCES.values())

    outputs = []
    opponent = "rawroute:" + str(ROUTE.resolve())
    for label, (source, expected_hash, expected_margin) in SOURCES.items():
        for seat in (0, 1):
            assert sha_file(source) == expected_hash
            result = run(str(source), opponent, SEED, seat)
            assert result["engine_version"] == EXPECTED_ENGINE
            assert result["candidate_status"] == result["opponent_status"] == "DONE"
            assert len(result["traces"][0]) == len(result["traces"][1]) == 719
            # The simulator calls the wrapped interpreter twice at step zero,
            # so there are 720 snapshots but 719 unique traced action steps.
            assert len(result["turns"]) == 720
            assert len({int(row["step"]) for row in result["turns"]}) == 719
            assert float(result["margin"]) == expected_margin, (
                label, seat, result["margin"], expected_margin
            )
            result["diagnostic_label"] = "repeat of pre-existing fixed-tape result; not a new strength test"
            result["source_label"] = label
            result["source_sha256"] = expected_hash
            result["route_action_sha256"] = EXPECTED_ACTION
            result["raw_replay_sha256"] = EXPECTED_REPLAY_SHA
            out = HERE / f"{label}-seat{seat}.json.gz"
            with gzip.open(out, "wt", encoding="utf-8") as handle:
                json.dump(result, handle, separators=(",", ":"))
            outputs.append({
                "policy": label, "seat": seat, "margin": result["margin"],
                "trace_records_each": 719, "instrumented_turn_snapshots": 720,
                "events": len(result["events"]), "path": str(out.resolve()),
            })
            print(f"{label} seat {seat}: margin {result['margin']:+.0f}; "
                  f"events={len(result['events'])}; output={out}", flush=True)
            assert sha_file(source) == expected_hash

    assert all(sha_file(path) == expected for path, expected, _ in SOURCES.values())
    print(json.dumps({
        "engine_version": ENGINE_VERSION,
        "main_sha256_after": sha_file(ROOT / "main.py"),
        "v43_sha256_after": sha_file(ROOT / "main_v43_current.py"),
        "route_action_sha256": EXPECTED_ACTION,
        "replay_sha256": EXPECTED_REPLAY_SHA,
        "traces": outputs,
    }, indent=2))


if __name__ == "__main__":
    main()
