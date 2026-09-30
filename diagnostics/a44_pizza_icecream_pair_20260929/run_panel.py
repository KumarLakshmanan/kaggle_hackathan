"""Run the frozen eight-game Pizza/Ice Cream continuation diagnostic."""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.stream_replay_io_20260928.fast_game_cached import play


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_frozen():
    manifest = read(HERE / "frozen_manifest.json")
    assert manifest["complete"] and manifest["diagnostic_only"]
    for name, digest in manifest["bindings"].items():
        path = Path(name)
        assert path.exists() and sha(path) == digest, f"Frozen input changed: {path}"
    preflight = read(HERE / "preflight.json")
    assert preflight["passed"] and preflight["static_only"]
    assert preflight["game_transitions_run"] == 0
    assert preflight["candidate_games"] == 8
    assert preflight["target_pair_rows"] == 2
    assert preflight["same_key_control_rows"] == 6
    assert sha(HERE / "candidate.py") == manifest["candidate_sha256"]
    assert sha(HERE / "panel.json") == manifest["panel_sha256"]
    panel = read(HERE / "panel.json")
    keys = {(row["fixture_id"], int(row["seat"])) for row in panel["expected_seats"]}
    expected = {(fixture["fixture_id"], seat)
                for fixture in panel["fixtures"] for seat in (0, 1)}
    assert keys == expected and len(keys) == 8 and len(panel["fixtures"]) == 4
    assert sum(bool(row["trigger"]) for row in panel["expected_seats"]) == 2
    return manifest, panel


def activation_checks(row, expected):
    telemetry = row.get("candidate_telemetry", {})
    trigger = bool(expected["trigger"])
    checks = {
        "clean_done_720": row["candidate_status"] == row["opponent_status"] == "DONE"
                          and row["frames"] == 720 and not row.get("candidate_errors"),
        "source_branch": telemetry.get("piice_branch144") == expected["bridge_branch"],
        "step72_key": telemetry.get("piice_key72") == expected["key72"],
        "step144_key": telemetry.get("piice_key144") == expected["key72"],
        "public_pair": telemetry.get("piice_pair144") == expected["pair"],
        "activation_state": telemetry.get("piice_active144") is trigger,
        "selected_route": telemetry.get("piice_route144") == ("113339524" if trigger else ""),
        "active_turns": telemetry.get("piice_active_turns") == (575 if trigger else 0),
        "zero_layer_errors": telemetry.get("piice_errors", 0) == 0,
    }
    return checks


def baseline_match(row, expected):
    fields = ("result", "margin", "candidate_reward", "opponent_reward",
              "candidate_status", "opponent_status", "frames")
    return {field: row[field] == expected[
        "baseline_" + ("result" if field == "result" else
                       "margin" if field == "margin" else
                       "candidate_reward" if field == "candidate_reward" else
                       "opponent_reward" if field == "opponent_reward" else "")]
            for field in fields if field in ("result", "margin", "candidate_reward", "opponent_reward")}


def run():
    manifest, panel = verify_frozen()
    ledger_path = HERE / "candidate.jsonl"
    receipt_path = HERE / "candidate.json"
    assert not ledger_path.exists() and not receipt_path.exists(), \
        "Runner never resumes or overwrites output"
    baseline = read(HERE / "parent_receipts.json")
    baseline_rows = {(row["fixture_id"], int(row["candidate_seat"])): row
                     for row in baseline["baseline_rows"]}
    fixture_by_id = {row["fixture_id"]: row for row in panel["fixtures"]}
    rows = []
    candidate_path = HERE / "candidate.py"
    with ledger_path.open("x", encoding="utf-8") as stream:
        for expected in panel["expected_seats"]:
            seat = int(expected["seat"])
            key = expected["fixture_id"], seat
            parent = baseline_rows[key]
            row = play(fixture_by_id[key[0]], candidate_path,
                       manifest["candidate_sha256"], seat)
            row.update(version="a44_piice_step144_route113339524",
                       panel=expected["panel"], panel_sha256=manifest["panel_sha256"],
                       runner_sha256=sha(HERE / "run_panel.py"))
            row.update(parent_result=parent["result"], parent_margin=parent["margin"],
                       delta_own=row["candidate_reward"] - parent["candidate_reward"],
                       delta_rival=row["opponent_reward"] - parent["opponent_reward"],
                       delta_margin=row["margin"] - parent["margin"])
            row["activation_checks"] = activation_checks(row, expected)
            row["activation_passed"] = all(row["activation_checks"].values())
            row["baseline_match"] = baseline_match(row, expected)
            row["baseline_preserved"] = (all(row["baseline_match"].values())
                                          if not expected["trigger"] else None)
            row["clean"] = row["activation_checks"]["clean_done_720"]
            rows.append(row)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
            print("piice_panel", len(rows), "/ 8", key, row["result"], row["margin"],
                  "trigger", expected["trigger"],
                  "activation", row["activation_passed"], flush=True)

    targets = [row for row in rows if row["fixture_id"] == "live-114238112"]
    controls = [row for row in rows if row["fixture_id"] != "live-114238112"]
    receipt = {
        "complete": True,
        "clean": len(rows) == 8 and all(row["clean"] for row in rows),
        "activation_passed": all(row["activation_passed"] for row in rows),
        "both_target_seats_win": len(targets) == 2 and all(row["result"] == "win" for row in targets),
        "six_control_rows_preserved": len(controls) == 6 and all(
            row["baseline_preserved"] is True for row in controls),
        "diagnostic_only": True,
        "fixed_tape_only": True,
        "promotion": False,
        "candidate_sha256": manifest["candidate_sha256"],
        "parent_candidate_sha256": manifest["parent_candidate_sha256"],
        "panel_sha256": manifest["panel_sha256"],
        "runner_sha256": sha(HERE / "run_panel.py"),
        "games": rows,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["passed"] = all(receipt[name] for name in (
        "clean", "activation_passed", "both_target_seats_win", "six_control_rows_preserved"))
    with receipt_path.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return receipt


def report():
    manifest, _ = verify_frozen()
    receipt = read(HERE / "candidate.json")
    parent = read(ROOT / "diagnostics/a44_goose4_smoothie_source_20260929/combined_results.json")
    panel = read(ROOT / "diagnostics/a44_goose4_smoothie_source_20260929/parent_panel.json")
    assert receipt["complete"] and receipt["clean"]
    rows = {(row["fixture_id"], int(row["candidate_seat"])): row for row in parent["games"]}
    added = {(row["fixture_id"], int(row["candidate_seat"])): row for row in receipt["games"]}
    assert len(rows) == 208 and len(added) == 8 and set(rows) >= set(added)
    rows.update(added)
    fixture_panels = {row["fixture_id"]: row["panel"] for row in panel["fixtures"]}
    summaries = {}
    for name in ("loss30", "top20", "public-win"):
        fixture_ids = sorted(fid for fid, panel_name in fixture_panels.items()
                             if panel_name == name)
        sweeps = sum(all(rows[(fid, seat)]["result"] == "win" for seat in (0, 1))
                     for fid in fixture_ids)
        wins = sum(rows[(fid, seat)]["result"] == "win"
                   for fid in fixture_ids for seat in (0, 1))
        summaries[name] = {"fixtures": len(fixture_ids), "seat_wins": wins,
                           "both_seat_sweeps": sweeps}
    outcome = {
        "complete": True,
        "diagnostic_only": True,
        "fixed_tape_only": True,
        "candidate_sha256": manifest["candidate_sha256"],
        "parent_candidate_sha256": manifest["parent_candidate_sha256"],
        "new_candidate_games": 8,
        "decision_equivalent_reused_parent_games": 200,
        "summaries": summaries,
        "target_rows": [row for row in receipt["games"]
                        if row["fixture_id"] == "live-114238112"],
        "control_rows": [row for row in receipt["games"]
                         if row["fixture_id"] != "live-114238112"],
        "fixed_panel_gate_passed": receipt["passed"],
        "promotion": False,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with (HERE / "combined_results.json").open("x", encoding="utf-8") as stream:
        json.dump(outcome, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return outcome


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"candidate", "report"}:
        raise SystemExit("usage: run_panel.py candidate|report")
    with exclusive_run(HERE / "run.lock"):
        verify_frozen()
        result = run() if sys.argv[1] == "candidate" else report()
        print(json.dumps({key: value for key, value in result.items() if key != "games"},
                         ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
