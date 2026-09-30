"""Frozen retrospective screen for current-4ee land retry; local tapes only."""

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCREEN = ROOT / "diagnostics/historical_policy_screen_20260928/screen.py"
CANDIDATE = {
    "name": "land_retry_4ee",
    "path": "diagnostics/loss_class_20260927/exp_land_retry_current_4ee.py",
    "sha256": "675893edc7ff07517dc57f60d322341b131ecd0d5286d9728d98d423cdc35e51",
}


def main():
    spec = importlib.util.spec_from_file_location("frozen_historical_screen", SCREEN)
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    assert source.engine_version == source.EXPECTED_ENGINE
    assert source.sha(source.BASELINE.read_bytes()) == source.EXPECTED_MAIN
    candidate_path = ROOT / CANDIDATE["path"]
    assert hashlib.sha256(candidate_path.read_bytes()).hexdigest() == CANDIDATE["sha256"]
    fixtures = source.load_and_check_fixtures()
    results = []
    for fixture in fixtures:
        item = source.play((CANDIDATE, fixture))
        results.append(item)
        print(item["fixture"]["team"],
              [(s["result"], s["margin"]) for s in item["seats"]], flush=True)
    results.sort(key=lambda item: item["fixture"]["rank"])
    assert len(results) == 5
    assert source.sha(source.BASELINE.read_bytes()) == source.EXPECTED_MAIN
    assert source.sha(candidate_path.read_bytes()) == CANDIDATE["sha256"]
    summary = source.analyze_candidate(CANDIDATE["name"], fixtures, results)
    payload = {"candidate": CANDIDATE, "results": results, "summary": summary,
               "main_sha256": source.EXPECTED_MAIN,
               "top_manifest_sha256": source.EXPECTED_TOP_MANIFEST,
               "top_assessment_sha256": source.EXPECTED_TOP_ASSESSMENT,
               "interpretation": "Fixed saved-action diagnostic only; opponents do not react."}
    (HERE / "screen.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"target_both_seat_sweeps": summary["target_both_seat_sweeps"],
                      "control_both_seat_sweeps": summary["control_both_seat_sweeps"],
                      "target_flip_seats": summary["target_flip_seats"]}, indent=2))


if __name__ == "__main__":
    main()
