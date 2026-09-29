"""Read-only audit of the completed Goose panel; runs no game simulations."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def read_json(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def result_pass(row: dict, feature: dict, normalize_route: bool) -> dict[str, bool]:
    telemetry = row["candidate_telemetry"]
    expected_route = feature["selected_route"] or ""
    actual_route = telemetry.get("a44_goose4_route", "")
    if normalize_route:
        route_ok = str(actual_route) == str(expected_route) if expected_route else actual_route == ""
    else:
        route_ok = actual_route == expected_route
    return {
        "branch": telemetry.get("a44_goose4_branch72", "")
        == (feature["bridge_branch"] if feature["bridge_branch"] == "source" else ""),
        "key": telemetry.get("a44_goose4_key72", "")
        == (feature["rule_key"] if feature["bridge_branch"] == "source" else ""),
        "route": route_ok,
        "turns": telemetry.get("a44_goose4_turns", 0) == (647 if expected_route else 0),
        "errors": telemetry.get("a44_goose4_errors", 0) == 0,
    }


def mean(rows: list[dict], field: str) -> float:
    return round(sum(float(row[field]) for row in rows) / len(rows), 1) if rows else 0.0


def main() -> None:
    candidate = read_json("candidate.json")
    source_controls = read_json("source_public.json")
    features = read_json("feature_rows.json")["rows"]
    feature_map = {(row["fixture_id"], row["seat"]): row for row in features}
    rows = candidate["games"]
    assert len(rows) == 208 and candidate["complete"]
    assert len(feature_map) == 208

    raw_checks = []
    normalized_checks = []
    for row in rows:
        key = (row["fixture_id"], row["candidate_seat"])
        feature = feature_map[key]
        raw = result_pass(row, feature, normalize_route=False)
        normalized = result_pass(row, feature, normalize_route=True)
        raw_checks.append(raw)
        normalized_checks.append(normalized)

    panels = {}
    for panel_name in ("loss30", "public-win", "top20"):
        panel_rows = [row for row in rows if row["panel"] == panel_name]
        fixture_ids = sorted({row["fixture_id"] for row in panel_rows})
        by_key = {(row["fixture_id"], row["candidate_seat"]): row for row in panel_rows}
        candidate_sweeps = [
            fixture for fixture in fixture_ids
            if all(by_key[(fixture, seat)]["result"] == "win" for seat in (0, 1))
        ]
        source_sweeps = [
            fixture for fixture in fixture_ids
            if all(by_key[(fixture, seat)]["parent_result"] == "win" for seat in (0, 1))
        ]
        rescues = sorted(set(candidate_sweeps) - set(source_sweeps))
        regressions = sorted(set(source_sweeps) - set(candidate_sweeps))
        seat_changes = []
        for fixture in fixture_ids:
            changes = []
            for seat in (0, 1):
                row = by_key[(fixture, seat)]
                if row["parent_result"] != row["result"]:
                    changes.append({
                        "seat": seat,
                        "source": row["parent_result"],
                        "candidate": row["result"],
                    })
            if changes:
                seat_changes.append({"fixture_id": fixture, "changes": changes})
        panels[panel_name] = {
            "fixtures": len(fixture_ids),
            "games": len(panel_rows),
            "candidate_wdl": dict(Counter(row["result"] for row in panel_rows)),
            "a44_wdl": dict(Counter(row["parent_result"] for row in panel_rows)),
            "candidate_both_seat_sweeps": len(candidate_sweeps),
            "a44_both_seat_sweeps": len(source_sweeps),
            "rescued_fixtures": rescues,
            "lost_sweeps": regressions,
            "seat_result_changes": seat_changes,
            "mean_candidate_margin": mean(panel_rows, "margin"),
            "mean_a44_margin": mean(panel_rows, "parent_margin"),
            "mean_delta_margin": mean(panel_rows, "delta_margin"),
            "mean_delta_own_cash": mean(panel_rows, "delta_own"),
            "mean_delta_rival_cash": mean(panel_rows, "delta_rival"),
        }

    bindings = [
        "candidate.json", "candidate.jsonl", "candidate.py", "source_a44.py",
        "source_public.json", "source_public.jsonl", "feature_rows.json",
        "panel.json", "frozen_manifest.json", "run_study.py",
    ]
    file_bindings = {name: file_sha(HERE / name) for name in bindings}
    route_mismatches = [
        rows[index]["fixture_id"] for index, checks in enumerate(raw_checks)
        if not checks["route"] and result_pass(rows[index], feature_map[(rows[index]["fixture_id"], rows[index]["candidate_seat"])], True)["route"]
    ]
    audit = {
        "audit_type": "posthoc read-only receipt audit; no simulations run",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_sha256": candidate["candidate_sha256"],
        "source_a44_sha256": candidate["source_a44_sha256"],
        "panel_sha256": candidate["panel_sha256"],
        "candidate_rows": len(rows),
        "candidate_clean_rows": sum(bool(row["clean"]) for row in rows),
        "candidate_error_rows": sum(bool(row["candidate_errors"]) for row in rows),
        "source_control_rows": len(source_controls["games"]),
        "source_controls_complete": source_controls["complete"],
        "source_controls_clean": source_controls["clean"],
        "activation_check": {
            "runner_recorded_pass_rows": sum(bool(row["activation_passed"]) for row in rows),
            "runner_recorded_fail_rows": sum(not bool(row["activation_passed"]) for row in rows),
            "branch_key_turns_errors_pass_rows": sum(all(check[key] for key in ("branch", "key", "turns", "errors")) for check in raw_checks),
            "raw_route_scalar_mismatches": len(route_mismatches),
            "raw_route_scalar_mismatch_fixture_ids": sorted(set(route_mismatches)),
            "route_scalar_conversion": "compare str(telemetry route) to str(feature selected_route); no policy data changed",
            "posthoc_normalized_pass_rows": sum(all(check.values()) for check in normalized_checks),
        },
        "panels": panels,
        "fixed_tape_only": True,
        "promotion": False,
        "promotion_decision": "reject this candidate for promotion: 21/30 loss30 sweeps is below the frozen 27/30 target; advance only to separate pasture research",
        "file_sha256": file_bindings,
    }
    output = HERE / "posthoc_audit.json"
    encoded = (json.dumps(audit, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if output.exists():
        if output.read_bytes() != encoded:
            raise FileExistsError(f"Refusing to replace existing audit output: {output}")
    else:
        output.write_bytes(encoded)
    print(json.dumps({key: value for key, value in audit.items() if key not in ("file_sha256",)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
