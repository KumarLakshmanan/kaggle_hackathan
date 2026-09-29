"""Freeze the exact-6d Pizza/Ice Cream pair candidate and no-game gates."""

from collections import Counter
from pathlib import Path
import ast
import copy
import gzip
import hashlib
import importlib.util
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT = ROOT / "diagnostics/a44_goose4_smoothie_source_20260929"
TARGET = "live-114238112"
PAIR = "PIZZA_SHOP|ICE_CREAM_SHOP"
KEY72 = "PIZZA_SHOP|M8+|C>S|G0"
FOCUS_FIXTURES = {
    TARGET,
    "public-win-114233677",
    "public-win-114251368",
    "public-win-114288078",
}
ROUTE = 113339524
EXPECTED_PAIRS = {
    TARGET: PAIR,
    "public-win-114233677": "PIZZA_SHOP|PIZZA_SHOP",
    "public-win-114251368": "PIZZA_SHOP|BAKERY",
    "public-win-114288078": "PIZZA_SHOP|YARN_STORE",
}
PARENT_SHA = "6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9"
ROOT_MAIN_SHA = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
ROUTE_SCREEN = ROOT / "diagnostics/production_leaf_selector_20260928"
ROUTE_CANDIDATE = ROUTE_SCREEN / "candidates/production_0ee065b6a6_113339524.py"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def import_candidate(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observations_through_144(path):
    result = {}
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            step = int(row.get("step", -1))
            if step <= 144:
                result[step] = row["observation"]
            if step == 144:
                break
    assert set(result) == set(range(145)), (path, sorted(result)[:3], sorted(result)[-3:])
    return result


def pair_at_144(path):
    observations = observations_through_144(path)
    shops = observations[144].get("town", {}).get("unlocked_shops", []) or []
    return "|".join(shops[:2]), observations


def static_layer_checks(text):
    tree = ast.parse(text)
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == "agent"]
    assert len(functions) == 1
    calls = [node for node in ast.walk(functions[0]) if isinstance(node, ast.Call)]
    assert sum(isinstance(call.func, ast.Name) and call.func.id == "_PIICE_PARENT"
               for call in calls) == 1
    assert sum(isinstance(call.func, ast.Name) and call.func.id == "_piice_commit"
               for call in calls) == 1
    assert not any(isinstance(node, ast.Subscript)
                   and isinstance(node.value, ast.Name)
                   and node.value.id == "observation"
                   and isinstance(node.slice, ast.Constant)
                   and node.slice.value in ("private", "seed", "money")
                   for node in ast.walk(tree))
    forbidden = ("fixture_id", "opponent_id", "seed", "configuration_seed", "coordinate")
    assert not any(token in text for token in forbidden)
    assert "step == 144" in text and 'branch == "source"' in text
    return {
        "one_parent_call": True,
        "one_route_commit_site": True,
        "public_shop_pair_and_existing_branch_only": True,
        "no_identity_private_seed_or_money_selector": True,
    }


def run_prefix_probe(base_path, candidate_path, features):
    focus_rows = sorted(
        (row for row in features["rows"]
         if row["fixture_id"] in FOCUS_FIXTURES
         and row["bridge_branch"] == "source"
         and row["rule_key"] == KEY72),
        key=lambda row: (row["fixture_id"], int(row["seat"])),
    )
    assert len(focus_rows) == 8
    results = []
    for source_row in focus_rows:
        pair, observations = pair_at_144(source_row["trace_path"])
        trigger = source_row["fixture_id"] == TARGET
        assert pair == EXPECTED_PAIRS[source_row["fixture_id"]]
        assert (pair == PAIR) == trigger
        seat = int(source_row["seat"])
        base = import_candidate(base_path, f"sixd_base_prefix_{source_row['fixture_id']}_{seat}")
        candidate = import_candidate(candidate_path, f"sixd_piice_prefix_{source_row['fixture_id']}_{seat}")
        for step in range(144):
            baseline_action = base.agent(copy.deepcopy(observations[step]))
            candidate_action = candidate.agent(copy.deepcopy(observations[step]))
            assert candidate_action == baseline_action, (source_row["fixture_id"], seat, step)
        farmice_before = copy.deepcopy(candidate._FARMICE_TAPE)
        donor_before = {
            name: (copy.deepcopy(donor["_DONOR_MAP"]), copy.deepcopy(donor["_DONOR_ROUTES"]))
            for name, donor in candidate._BRIDGE_DONORS.items()
        }
        baseline_action = base.agent(copy.deepcopy(observations[144]))
        candidate_action = candidate.agent(copy.deepcopy(observations[144]))
        telemetry = dict(candidate.agent.telemetry)
        assert candidate._BRIDGE_SELECTED == "source"
        assert telemetry.get("piice_key72") == KEY72
        changed_route_keys = {
            key for key in set(candidate._PIICE_BASE_ROUTE_MAP) | set(candidate._DATA["route_map"])
            if candidate._PIICE_BASE_ROUTE_MAP.get(key) != candidate._DATA["route_map"].get(key)
        }
        assert candidate._FARMICE_TAPE == farmice_before
        assert donor_before == {
            name: (donor["_DONOR_MAP"], donor["_DONOR_ROUTES"])
            for name, donor in candidate._BRIDGE_DONORS.items()
        }
        assert telemetry.get("piice_branch144") == "source"
        assert telemetry.get("piice_key144") == KEY72
        assert telemetry.get("piice_pair144") == EXPECTED_PAIRS[source_row["fixture_id"]]
        assert telemetry.get("piice_errors") == 0
        if trigger:
            assert candidate._DATA["route_map"].get(PAIR) == ROUTE
            assert changed_route_keys == {PAIR}
            assert candidate._hire_recovery_schedule(observations[144]) == candidate._DATA["routes"][str(ROUTE)]
            assert telemetry.get("piice_active144") is True
            assert telemetry.get("piice_route144") == str(ROUTE)
            assert candidate_action != baseline_action
        else:
            assert not changed_route_keys
            assert candidate._DATA["route_map"] == candidate._PIICE_BASE_ROUTE_MAP
            assert candidate._hire_recovery_schedule(observations[144]) == base._hire_recovery_schedule(observations[144])
            assert telemetry.get("piice_active144") is False
            assert telemetry.get("piice_route144") == ""
            assert telemetry.get("piice_active_turns") == 0
            assert candidate_action == baseline_action
        farm = observations[144]["farms"][int(observations[144]["player"])]
        results.append({
            "fixture_id": source_row["fixture_id"],
            "panel": source_row["panel"],
            "seat": seat,
            "trace_sha256": source_row["trace_sha256"],
            "pair_at_144": pair,
            "key72": telemetry.get("piice_key72"),
            "trigger": trigger,
            "bridge_branch": candidate._BRIDGE_SELECTED,
            "equal_agent_actions_steps_0_to_143": True,
            "equal_agent_action_step144": candidate_action == baseline_action,
            "baseline_action_sha256_step144": hashlib.sha256(
                json.dumps(baseline_action, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "candidate_action_sha256_step144": hashlib.sha256(
                json.dumps(candidate_action, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "candidate_action_step144": candidate_action,
            "state_step144": {
                "cash": farm["money"],
                "hands": len(farm["hands"]),
                "shed_wheat": observations[144]["private"]["shed"].get("WHEAT", 0),
                "shed_fertilizer": observations[144]["private"]["shed"].get("FERTILIZER", 0),
            },
            "selected_route": ROUTE if trigger else None,
            "schedule_resolves_from_step144": bool(trigger),
            "candidate_telemetry": telemetry,
            "game_transitions_run": 0,
        })
    return results


def main():
    # Static generated files may be rebuilt before any game starts. Never
    # replace or resume a simulator output/lock.
    for name in ("candidate.jsonl", "candidate.json", "combined_results.json", "run.lock"):
        if (HERE / name).exists():
            raise SystemExit(f"Outcome artifact already exists; refusing rebuild: {name}")

    parent_manifest = read(PARENT / "frozen_manifest.json")
    assert parent_manifest["complete"] and parent_manifest["candidate_sha256"] == PARENT_SHA
    for path, digest in parent_manifest["bindings"].items():
        assert Path(path).exists() and sha(path) == digest, path
    assert sha(PARENT / "candidate.py") == PARENT_SHA
    assert sha(ROOT / "main.py") == ROOT_MAIN_SHA
    route_pool = read(ROUTE_SCREEN / "pool.json")
    route_candidate = next(row for row in route_pool["candidates"]
                           if row["candidate"] == str(ROUTE_CANDIDATE)
                           and row["route"] == str(ROUTE))
    assert sha(ROUTE_CANDIDATE) == route_candidate["candidate_sha256"]
    route_module = import_candidate(ROUTE_CANDIDATE, "screened_piice_route_identity")
    assert str(ROUTE) in route_module._DATA["routes"]
    parent_module = import_candidate(PARENT / "candidate.py", "sixd_route_identity")
    base_route = str(parent_module._DATA["route_map"]["PIZZA_SHOP"])
    base_actions = parent_module._DATA["routes"][base_route]
    selected_actions = route_module._DATA["routes"][str(ROUTE)]
    assert len(selected_actions) == 719
    physical_prefix_diffs = [
        step for step in range(72, 144)
        if (base_actions[step].get("farmer"), base_actions[step].get("hands"))
        != (selected_actions[step].get("farmer"), selected_actions[step].get("hands"))
    ]
    raw_prefix_diffs = [step for step in range(72, 144)
                        if base_actions[step] != selected_actions[step]]
    assert not physical_prefix_diffs
    assert raw_prefix_diffs == [79]

    source_features = read(PARENT / "feature_rows.json")
    parent_panel = read(PARENT / "parent_panel.json")
    parent_results = read(PARENT / "combined_results.json")
    assert len(source_features["rows"]) == 208
    assert len({(row["fixture_id"], int(row["seat"])) for row in source_features["rows"]}) == 208
    source_key_rows = [row for row in source_features["rows"]
                       if row["bridge_branch"] == "source" and row["rule_key"] == KEY72]
    expected_focus_keys = {
        (fixture, seat) for fixture in FOCUS_FIXTURES for seat in (0, 1)
    }
    assert len(source_key_rows) == 8
    assert {(row["fixture_id"], int(row["seat"])) for row in source_key_rows} == expected_focus_keys
    assert len({row["fixture_id"] for row in parent_panel["fixtures"]}) == 104
    assert parent_results["complete"] and parent_results["candidate_sha256"] == PARENT_SHA
    assert len(parent_results["games"]) == 208
    assert all(row.get("clean") and row["candidate_status"] == row["opponent_status"] == "DONE"
               and row["frames"] == 720 for row in parent_results["games"])
    exact_pair_descendants = [key for key in parent_module._DATA["route_map"]
                              if key == PAIR or key.startswith(PAIR + "|")]
    assert exact_pair_descendants == []

    shutil.copyfile(PARENT / "candidate.py", HERE / "candidate_base.py")
    raw = (HERE / "candidate_base.py").read_bytes()
    layer = (HERE / "layer.py").read_bytes()
    candidate_bytes = raw.rstrip(b"\r\n") + b"\n\n" + layer
    candidate_path = HERE / "candidate.py"
    candidate_path.write_bytes(candidate_bytes)
    compile(candidate_bytes, str(candidate_path), "exec")
    assert sha(HERE / "candidate_base.py") == PARENT_SHA

    pair_rows = []
    for row in source_features["rows"]:
        pair, _ = pair_at_144(row["trace_path"])
        pair_rows.append({
            "fixture_id": row["fixture_id"],
            "panel": row["panel"],
            "seat": int(row["seat"]),
            "bridge_branch": row["bridge_branch"],
            "step72_rule_key": row["rule_key"],
            "step144_pair": pair,
            "trace_sha256": row["trace_sha256"],
        })
    counts = Counter(row["step144_pair"] for row in pair_rows)
    triggers = [row for row in pair_rows
                if row["bridge_branch"] == "source" and row["step144_pair"] == PAIR]
    assert counts[PAIR] == 2 and len(triggers) == 2
    assert {(row["fixture_id"], row["seat"]) for row in triggers} == {(TARGET, 0), (TARGET, 1)}
    assert all(row["panel"] == "loss30" for row in triggers)
    assert not any(row["panel"] == "top20" for row in triggers)
    focus = [row for row in pair_rows if row["fixture_id"] in FOCUS_FIXTURES]
    assert len(focus) == 8
    assert all(row["bridge_branch"] == "source" and row["step72_rule_key"] == KEY72
               for row in focus)
    assert {(row["fixture_id"], row["seat"]) for row in focus} == {
        (fixture, seat) for fixture in FOCUS_FIXTURES for seat in (0, 1)
    }
    assert all(row["step144_pair"] == EXPECTED_PAIRS[row["fixture_id"]] for row in focus)
    dump(HERE / "pair_rows.json", {
        "complete": True,
        "parent_candidate_sha256": PARENT_SHA,
        "source_feature_rows_sha256": sha(PARENT / "feature_rows.json"),
        "step144_pair_census": dict(sorted(counts.items())),
        "target_trigger_rows": triggers,
        "rows": pair_rows,
    })

    parent_rows = {(row["fixture_id"], int(row["candidate_seat"])): row
                   for row in parent_results["games"]}
    assert len(parent_rows) == 208
    focus_baselines = [parent_rows[(fixture, seat)]
                       for fixture in sorted(FOCUS_FIXTURES) for seat in (0, 1)]
    target_baselines = [parent_rows[(TARGET, seat)] for seat in (0, 1)]
    assert all(row["result"] == "loss" and row["margin"] == -8178.0
               for row in target_baselines)
    assert all(row["result"] == "win" for row in focus_baselines if row["fixture_id"] != TARGET)
    focus_fixtures = [row for row in parent_panel["fixtures"]
                      if row["fixture_id"] in FOCUS_FIXTURES]
    assert {row["fixture_id"] for row in focus_fixtures} == FOCUS_FIXTURES
    fixture_by_id = {row["fixture_id"]: row for row in focus_fixtures}
    assert fixture_by_id[TARGET]["panel"] == "loss30"
    assert all(fixture_by_id[fixture]["panel"] == "public-win"
               for fixture in FOCUS_FIXTURES if fixture != TARGET)
    dump(HERE / "parent_receipts.json", {
        "complete": True,
        "candidate_sha256": PARENT_SHA,
        "combined_results_sha256": sha(PARENT / "combined_results.json"),
        "feature_rows_sha256": sha(PARENT / "feature_rows.json"),
        "baseline_rows": [
            {key: row[key] for key in ("fixture_id", "candidate_seat", "result", "margin",
                                      "candidate_reward", "opponent_reward", "clean")}
            for row in focus_baselines
        ],
        "reusable_nontrigger_rows": 200,
    })
    ordered_fixtures = [fixture_by_id[TARGET]] + [
        fixture_by_id[fixture]
        for fixture in ("public-win-114233677", "public-win-114251368", "public-win-114288078")
    ]
    dump(HERE / "panel.json", {
        "candidate": "exact 6d plus step-144 public Pizza/Ice Cream continuation",
        "fixture_count": 4,
        "candidate_games": 8,
        "fixtures": ordered_fixtures,
        "expected_seats": [
            {"fixture_id": row["fixture_id"], "seat": int(row["candidate_seat"]),
             "panel": row["panel"], "bridge_branch": "source",
             "key72": KEY72, "pair": EXPECTED_PAIRS[row["fixture_id"]],
             "trigger": row["fixture_id"] == TARGET,
             "route": ROUTE if row["fixture_id"] == TARGET else None,
             "baseline_result": row["result"], "baseline_margin": row["margin"],
             "baseline_candidate_reward": row["candidate_reward"],
             "baseline_opponent_reward": row["opponent_reward"]}
            for row in focus_baselines
        ],
    })

    prefix = run_prefix_probe(PARENT / "candidate.py", candidate_path, source_features)
    dump(HERE / "prefix_probe.json", {
        "complete": True,
        "static_agent_calls_only": True,
        "game_transitions_run": 0,
        "parent_candidate_sha256": PARENT_SHA,
        "candidate_sha256": sha(candidate_path),
        "focus_rows": prefix,
    })
    layer_checks = static_layer_checks(layer.decode("utf-8"))
    preflight = {
        "schema": "a44-piice-exact6d-static-preflight-v1",
        "passed": True,
        "static_only": True,
        "game_transitions_run": 0,
        "experiment_completed": False,
        "promotion": False,
        "parent_candidate_sha256": PARENT_SHA,
        "candidate_sha256": sha(candidate_path),
        "feature_rows": 208,
        "fixtures": 104,
        "target_pair_rows": 2,
        "same_key_control_rows": 6,
        "source_branch_step72_key_census_rows": len(source_key_rows),
        "candidate_games": 8,
        "reused_parent_rows": 200,
        "target_pair_fixture": TARGET,
        "top20_trigger_rows": 0,
        "public_win_trigger_rows": 0,
        "control_fixtures": sorted(FOCUS_FIXTURES - {TARGET}),
        "all_triggers_source_branch": True,
        "screened_route_candidate_sha256": route_candidate["candidate_sha256"],
        "screened_route_matches_parent_route_bytes": True,
        "route_prefix_farmer_hands_equal_steps_72_to_143": True,
        "route_prefix_only_raw_delta_step79": raw_prefix_diffs,
        "route_exists": True,
        "route_length": len(selected_actions),
        "route_map_descendants_before_commit": 0,
        "route_map_diff_after_commit": [PAIR],
        "route_map_commit_scope": PAIR,
        "prefix_probe_sha256": sha(HERE / "prefix_probe.json"),
        "prefix_equal_steps": list(range(144)),
        "layer_static_checks": layer_checks,
        "parent_target_results": [row["result"] for row in target_baselines],
        "reactive_validation": False,
    }
    dump(HERE / "preflight.json", preflight)

    external_paths = [
        PARENT / "candidate.py", PARENT / "frozen_manifest.json", PARENT / "feature_rows.json",
        PARENT / "parent_panel.json", PARENT / "combined_results.json", PARENT / "preflight.json",
        PARENT / "RESULTS.md", ROOT / "diagnostics/production_leaf_selector_20260928/RESULTS.md",
        ROOT / "diagnostics/production_leaf_selector_20260928/selection.json",
        ROOT / "diagnostics/production_leaf_selector_20260928/pool.json",
        ROUTE_CANDIDATE,
        ROOT / "diagnostics/production_pair_continuations_20260928/RESULTS.md",
        ROOT / "diagnostics/production_pair_continuations_20260928/screen.jsonl",
    ]
    bindings = {str(path.resolve()): sha(path) for path in external_paths}
    for path in (HERE / name for name in (
        "PLAN.md", "layer.py", "build_preflight.py", "run_panel.py", "candidate_base.py", "candidate.py",
        "pair_rows.json", "parent_receipts.json", "panel.json", "prefix_probe.json", "preflight.json",
    )):
        bindings[str(path.resolve())] = sha(path)
    manifest = {
        "complete": True,
        "diagnostic_only": True,
        "parent_candidate_sha256": PARENT_SHA,
        "candidate_sha256": sha(candidate_path),
        "panel_sha256": sha(HERE / "panel.json"),
        "pair_rows_sha256": sha(HERE / "pair_rows.json"),
        "prefix_probe_sha256": sha(HERE / "prefix_probe.json"),
        "preflight_sha256": sha(HERE / "preflight.json"),
        "trace_count": 208,
        "reused_parent_rows": 200,
        "new_candidate_rows": 8,
        "bindings": bindings,
    }
    dump(HERE / "frozen_manifest.json", manifest)
    for path, digest in bindings.items():
        assert Path(path).exists() and sha(path) == digest, path
    print(json.dumps({
        "candidate_sha256": manifest["candidate_sha256"],
        "panel_sha256": manifest["panel_sha256"],
        "pair_rows_sha256": manifest["pair_rows_sha256"],
        "prefix_probe_sha256": manifest["prefix_probe_sha256"],
        "preflight_sha256": manifest["preflight_sha256"],
        "manifest_sha256": sha(HERE / "frozen_manifest.json"),
        "bindings": len(bindings),
        "target_pair_rows": len(triggers),
        "reusable_parent_rows": 200,
        "game_transitions_run": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
