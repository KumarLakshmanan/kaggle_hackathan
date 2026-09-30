"""Static no-op proof for the hash-bound Ghost Ice wheat-gate derivative.

This is source/data analysis only. It does not import or call the agent, load a
game engine, or advance a game. PLAN_V2.md supersedes the original replay-heavy
procedure in PLAN.md.
"""

from collections import Counter
from pathlib import Path
import ast
import base64
import copy
import gzip
import hashlib
import json
import zlib


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GOOSE = ROOT / "diagnostics/a44_source_bridge_goose_4leaf_20260929"
SIXD = ROOT / "diagnostics/a44_goose4_smoothie_source_20260929"
FEATURES_PATH = GOOSE / "feature_rows.json"
PANEL_PATH = HERE / "panel.json"
PATCH_PATH = HERE / "patch_spec.json"
CANDIDATE_PATH = HERE / "candidate.py"
PARENT_PATH = SIXD / "candidate.py"
EXPECTED_A44 = "a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f"
EXPECTED_GOOSE4 = "c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632"
EXPECTED_6D = "6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9"
EXPECTED_CANDIDATE = "228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767"
GHOST_KEY = "ICE_CREAM_SHOP|M8+|C>S|G0"
GHOST_ROUTE = 113360743
GOOSE4_ROUTE = 113470868
WHEAT_LIMIT = 9975
EXPECTED_TRIGGERS = {("live-114288168", 0), ("live-114288168", 1)}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pretty_json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_new_json(path, value):
    path = Path(path)
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite frozen output: {path}")
    with path.open("xb") as stream:
        stream.write(pretty_json(value))


def verify_manifest(path, expected_candidate, expected_a44):
    manifest = read_json(path)
    assert manifest.get("complete") is True and manifest.get("diagnostic_only") is True
    assert manifest.get("candidate_sha256") == expected_candidate, path
    assert manifest.get("source_a44_sha256") == expected_a44, path
    bindings = manifest.get("bindings")
    assert isinstance(bindings, dict) and bindings
    checked = {}
    for raw_path, expected_sha in bindings.items():
        source = Path(raw_path)
        assert source.is_file() and sha(source) == expected_sha, f"Stale parent binding: {source}"
        checked[str(source.resolve())] = expected_sha
    return manifest, checked


def parse_source(path):
    with Path(path).open("r", encoding="utf-8", newline="") as stream:
        text = stream.read()
    return text, ast.parse(text, filename=str(path))


def assignments(tree, name):
    found = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                found.append(node.value)
    return found


def literal_assignment(tree, name):
    values = assignments(tree, name)
    assert len(values) == 1, (name, len(values))
    return ast.literal_eval(values[0])


def embedded_data(path):
    """Decode the frozen literal _DATA blob without executing policy code."""
    _, tree = parse_source(path)
    values = assignments(tree, "_DATA")
    assert len(values) == 1, (path, len(values))
    encoded_calls = [
        node for node in ast.walk(values[0])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("b85decode", "b64decode")
    ]
    assert len(encoded_calls) == 1, (path, len(encoded_calls))
    call = encoded_calls[0]
    assert len(call.args) == 1 and isinstance(call.args[0], ast.Constant)
    encoded = call.args[0].value
    assert isinstance(encoded, str) and len(encoded) > 100_000
    raw = (base64.b85decode(encoded) if call.func.attr == "b85decode"
           else base64.b64decode(encoded))
    data = json.loads(zlib.decompress(raw).decode("utf-8"))
    assert isinstance(data, dict) and "route_map" in data and "routes" in data
    return data


def function_nodes(tree, name):
    return [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]


def unique_function_source(text, tree, name):
    nodes = function_nodes(tree, name)
    assert len(nodes) == 1, (name, len(nodes))
    segment = ast.get_source_segment(text, nodes[0])
    assert segment
    return segment, nodes[0]


def goose_agent_source(text, tree):
    matches = []
    for node in function_nodes(tree, "agent"):
        if any(isinstance(item, ast.Call) and isinstance(item.func, ast.Name)
               and item.func.id == "_a44_goose4_active" for item in ast.walk(node)):
            matches.append(node)
    assert len(matches) == 1
    segment = ast.get_source_segment(text, matches[0])
    assert segment
    return segment, matches[0]


def verify_byte_exact_patch(parent_text, candidate_text, spec):
    assert spec.get("schema") == "kaggriculture-candidate-patch/v1"
    assert Path(spec["parent_candidate_path"]).resolve() == PARENT_PATH.resolve()
    assert hashlib.sha256(parent_text.encode("utf-8")).hexdigest() == EXPECTED_6D
    patched = parent_text
    names = []
    for item in spec["patches"]:
        before, after = item["before_utf8"], item["after_utf8"]
        assert hashlib.sha256(before.encode("utf-8")).hexdigest() == item["before_sha256"]
        assert hashlib.sha256(after.encode("utf-8")).hexdigest() == item["after_sha256"]
        assert patched.count(before) == 1, item["name"]
        patched = patched.replace(before, after, 1)
        names.append(item["name"])
    assert patched == candidate_text
    assert hashlib.sha256(candidate_text.encode("utf-8")).hexdigest() == EXPECTED_CANDIDATE
    return names


def public_key(observation):
    shops = observation["town"]["unlocked_shops"]
    rival = observation["farms"][1 - int(observation["player"])]
    melon = cow = sheep = goose = 0
    for row in rival["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                melon += tile.get("crop") == "MELON"
                cow += tile.get("animal") == "COW"
                sheep += tile.get("animal") == "SHEEP"
                goose += tile.get("animal") == "GOOSE"
    comparison = "C<S" if cow < sheep else "C>S" if cow > sheep else "C=S"
    return shops[0] + "|" + ("M8+" if melon >= 8 else "M<8") + "|" + comparison + ("|G+" if goose > 0 else "|G0")


def read_step72(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                step = int(row.get("step", row.get("observation", {}).get("step", -1)))
                if step == 72:
                    observation = row["observation"]
                    assert int(observation["step"]) == 72
                    return observation
                assert step < 72, f"Missing step72 in {path}"
    raise AssertionError(f"Trace ended before step72: {path}")


def route_scope(candidate_data, parent_data, route_data, parent_text, parent_tree, candidate_text, candidate_tree):
    base_map = candidate_data["route_map"]
    parent_map = parent_data["route_map"]
    assert base_map == parent_map
    ice_keys = sorted(key for key in base_map if key.split("|", 1)[0] == "ICE_CREAM_SHOP")
    assert len(ice_keys) == 155
    assert "ICE_CREAM_SHOP" in base_map
    goose_rules = literal_assignment(candidate_tree, "_A44_GOOSE4_RULES")
    parent_rules = literal_assignment(parent_tree, "_A44_GOOSE4_RULES")
    assert goose_rules == parent_rules
    assert goose_rules[GHOST_KEY] == GOOSE4_ROUTE

    ghost_schedule = candidate_data["routes"][str(GHOST_ROUTE)]
    source_schedule = route_data["routes"][str(GHOST_ROUTE)]
    assert ghost_schedule == source_schedule and len(ghost_schedule) == 719
    incumbent = candidate_data["routes"][str(GOOSE4_ROUTE)]
    divergence = next((i for i, pair in enumerate(zip(incumbent, ghost_schedule)) if pair[0] != pair[1]), None)
    assert divergence == 72

    stable_functions = ("_a44_goose4_key", "_a44_goose4_active",
                        "_a44_goose4_commit", "_hire_recovery_schedule")
    stable_function_hashes = {}
    for name in stable_functions:
        old_source, _ = unique_function_source(parent_text, parent_tree, name)
        new_source, _ = unique_function_source(candidate_text, candidate_tree, name)
        assert old_source == new_source, f"Unexpected changed helper: {name}"
        stable_function_hashes[name] = hashlib.sha256(old_source.encode("utf-8")).hexdigest()
    commit_source, _ = unique_function_source(candidate_text, candidate_tree, "_a44_goose4_commit")
    assert "_BRIDGE_DONORS" not in commit_source
    assert "if shop == 'FARMERS_MARKET':" in commit_source

    after = copy.deepcopy(base_map)
    for key in list(after):
        if key.split("|", 1)[0] == "ICE_CREAM_SHOP":
            after[key] = GHOST_ROUTE
    after["ICE_CREAM_SHOP"] = GHOST_ROUTE
    assert set(after) == set(base_map)
    assert all(after[key] == GHOST_ROUTE for key in ice_keys)
    assert all(after[key] == base_map[key] for key in set(base_map) - set(ice_keys))

    parent_reset, _ = unique_function_source(parent_text, parent_tree, "_a44_goose4_reset")
    reset_source, _ = unique_function_source(candidate_text, candidate_tree, "_a44_goose4_reset")
    reset_lines = (
        "_DATA['route_map'].clear()",
        "_DATA['route_map'].update(copy.deepcopy(_A44_GOOSE4_BASE_ROUTE_MAP))",
        "_FARMICE_TAPE = copy.deepcopy(_A44_GOOSE4_BASE_FARMICE)",
    )
    for line in reset_lines:
        assert parent_reset.count(line) == reset_source.count(line) == 1
    assert all(line in reset_source for line in reset_lines)
    return {
        "ice_descendant_count": len(ice_keys),
        "ice_route_map_rows": [
            {"key": key, "parent_route": base_map[key], "trigger_route": after[key]}
            for key in ice_keys
        ],
        "outside_ice_route_map_unchanged": True,
        "route_map_reset_statements_unchanged": True,
        "farmice_reset_statement_unchanged": True,
        "new_ghost_telemetry_reset_is_additive": True,
        "ice_commit_does_not_write_farmice": True,
        "commit_does_not_reference_donor_maps": True,
        "all_route_map_keys_preserved": True,
        "route_schedule_length": len(ghost_schedule),
        "route_schedule_sha256": hashlib.sha256(canonical_json(ghost_schedule)).hexdigest(),
        "route_schedule_matches_bound_source_file": True,
        "first_route_action_difference_zero_based": divergence,
        "unchanged_helper_sha256": stable_function_hashes,
    }


def feature_census(features, panel, candidate_data, goose_rules):
    rows = features["rows"]
    counts = Counter()
    fixture_seats = set()
    trace_paths = set()
    triggers = set()
    route_rows = []
    panel_rows = {(row["fixture_id"], int(row["candidate_seat"])): row for row in panel["games"]}
    assert len(panel_rows) == 12
    for row in rows:
        fixture_id, seat = row["fixture_id"], int(row["seat"])
        key = (fixture_id, seat)
        assert key not in fixture_seats
        fixture_seats.add(key)
        counts[row["panel"]] += 1
        trace = Path(row["trace_path"])
        assert trace.is_file() and sha(trace) == row["trace_sha256"], trace
        assert str(trace.resolve()) not in trace_paths
        trace_paths.add(str(trace.resolve()))
        observation = read_step72(trace)
        leaf = public_key(observation)
        assert leaf == row["rule_key"], (key, leaf, row["rule_key"])
        branch = row["bridge_branch"]
        wheat = int(observation["market"]["inventory"]["WHEAT"])
        active = int(observation["step"]) == 72 and branch == "source" and leaf == GHOST_KEY and wheat <= WHEAT_LIMIT
        parent_route = goose_rules.get(leaf) if branch == "source" else None
        candidate_route = GHOST_ROUTE if active else parent_route
        assert active == (key in EXPECTED_TRIGGERS), (key, branch, leaf, wheat, active)
        if active:
            triggers.add(key)
        if not active:
            assert candidate_route == parent_route
        if branch == "shared151":
            assert active is False and candidate_route is None
        assert branch in ("source", "shared151")

        entry = {
            "fixture_id": fixture_id, "seat": seat, "panel": row["panel"],
            "bridge_branch": branch, "step72_public_key": leaf, "step72_public_wheat": wheat,
            "triggered": active, "parent_selected_route": parent_route,
            "candidate_selected_route": candidate_route,
            "nontrigger_route_equivalent": candidate_route == parent_route,
            "trace_path": str(trace.resolve()), "trace_sha256": row["trace_sha256"],
        }
        route_rows.append(entry)

        if key in panel_rows:
            planned = panel_rows[key]
            assert planned["source_trace_sha256"] == row["trace_sha256"]
            assert planned["step72_branch"] == branch
            assert planned["step72_public_key"] == leaf
            assert int(planned["step72_public_wheat"]) == wheat
            assert bool(planned["expected_trigger"]) == active
            assert int(planned["expected_derivative_route"]) == candidate_route
            if active:
                assert int(planned["expected_parent_goose4_route"]) == GOOSE4_ROUTE
            else:
                assert int(planned["expected_parent_goose4_route"]) == parent_route

    assert len(rows) == len(fixture_seats) == 208
    assert len({fixture for fixture, _ in fixture_seats}) == 104
    assert len(trace_paths) == 208
    assert counts == Counter({"loss30": 60, "public-win": 108, "top20": 40})
    assert triggers == EXPECTED_TRIGGERS
    assert sum(item["step72_public_key"] == GHOST_KEY for item in route_rows) == 12
    assert sum(item["triggered"] for item in route_rows if item["panel"] == "top20") == 0
    assert sum(item["triggered"] for item in route_rows if item["panel"] == "public-win") == 0
    assert sum(item["triggered"] for item in route_rows if item["bridge_branch"] == "shared151") == 0
    nontrigger = [item for item in route_rows if not item["triggered"]]
    assert len(nontrigger) == 206 and all(item["nontrigger_route_equivalent"] for item in nontrigger)
    assert len([item for item in panel_rows.values() if not item["expected_trigger"]]) == 10
    return {
        "feature_rows": 208,
        "fixtures": 104,
        "unique_fixture_seat_rows": 208,
        "unique_bound_trace_paths": 208,
        "panel_coverage": dict(counts),
        "source_branch_rows": 190,
        "shared151_branch_rows": 18,
        "coarse_ice_key_rows": 12,
        "coarse_ice_key_fixtures": 6,
        "trigger_rows": len(triggers),
        "trigger_census": [item for item in route_rows if item["triggered"]],
        "all_feature_decisions": route_rows,
        "nontrigger_rows": 206,
        "nontrigger_selected_route_mismatches": 0,
        "top20_trigger_rows": 0,
        "public_win_trigger_rows": 0,
        "shared151_trigger_rows": 0,
        "panel_false_trigger_controls": 10,
    }


def main():
    assert not (HERE / "preflight.json").exists()
    assert not (HERE / "frozen_manifest.json").exists()
    source_a44_path = ROOT / "diagnostics/a44_source_bridge_goose_4leaf_20260929/source_a44.py"
    goose_candidate_path = GOOSE / "candidate.py"
    assert sha(source_a44_path) == EXPECTED_A44
    assert sha(goose_candidate_path) == EXPECTED_GOOSE4
    assert sha(PARENT_PATH) == EXPECTED_6D
    assert sha(CANDIDATE_PATH) == EXPECTED_CANDIDATE

    parent_text, parent_tree = parse_source(PARENT_PATH)
    candidate_text, candidate_tree = parse_source(CANDIDATE_PATH)
    patch_spec = read_json(PATCH_PATH)
    patch_names = verify_byte_exact_patch(parent_text, candidate_text, patch_spec)
    expected_constants = {
        "_A44_GHOST_WHEAT_KEY72": GHOST_KEY,
        "_A44_GHOST_WHEAT_ROUTE72": GHOST_ROUTE,
        "_A44_GHOST_WHEAT_MAX_STOCK72": WHEAT_LIMIT,
    }
    for name, value in expected_constants.items():
        assert literal_assignment(candidate_tree, name) == value
    helper_source, _ = unique_function_source(candidate_text, candidate_tree, "_a44_ghost_wheat_trigger")
    assert "int(step) == 72" in helper_source
    assert "bridge_branch == 'source'" in helper_source
    assert "leaf == _A44_GHOST_WHEAT_KEY72" in helper_source
    assert "observation['market']['inventory']['WHEAT']" in helper_source
    assert "<= _A44_GHOST_WHEAT_MAX_STOCK72" in helper_source
    assert "private" not in helper_source.lower() and "cash" not in helper_source.lower()
    ghost_telemetry_keys = {
        "a44_ghost_wheat_branch72", "a44_ghost_wheat_key72",
        "a44_ghost_wheat_checked72", "a44_ghost_wheat_stock72",
        "a44_ghost_wheat_active72", "a44_ghost_wheat_route72",
    }
    telemetry_reads = [
        node for node in ast.walk(candidate_tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name) and node.value.id == "_A44_GOOSE4_STATS"
        and isinstance(node.slice, ast.Constant) and node.slice.value in ghost_telemetry_keys
        and isinstance(node.ctx, ast.Load)
    ]
    assert telemetry_reads == []

    goose_manifest_path = GOOSE / "frozen_manifest.json"
    sixd_manifest_path = SIXD / "frozen_manifest.json"
    goose_manifest, goose_inputs = verify_manifest(goose_manifest_path, EXPECTED_GOOSE4, EXPECTED_A44)
    sixd_manifest, sixd_inputs = verify_manifest(sixd_manifest_path, EXPECTED_6D, EXPECTED_A44)
    assert sixd_manifest["goose4_candidate_sha256"] == EXPECTED_GOOSE4
    assert sixd_manifest["feature_rows_sha256"] == sha(FEATURES_PATH)
    assert sixd_manifest["parent_manifest_sha256"] == sha(SIXD / "goose4_parent_manifest.json")
    assert sha(SIXD / "goose4_parent_manifest.json") == sha(goose_manifest_path)
    assert sixd_manifest["preflight_sha256"] == sha(SIXD / "preflight.json")

    features = read_json(FEATURES_PATH)
    panel = read_json(PANEL_PATH)
    assert features["complete"] is True and features["source_a44_sha256"] == EXPECTED_A44
    assert features["production_pool_sha256"] == "5414c0a94dfc7f8330eebace627512c1d834b1e565b44ef6093fed7268860dda"
    assert panel["status"] == "frozen_plan_no_outcome_games"
    assert panel["candidate_sha256"] == EXPECTED_CANDIDATE
    assert panel["parent_candidate_sha256"] == EXPECTED_6D
    assert panel["goose4_candidate_sha256"] == EXPECTED_GOOSE4
    assert panel["feature_rows_sha256"] == sha(FEATURES_PATH)
    assert panel["candidate_route_source_sha256"] == sha(ROOT / panel["proposed_rule"]["candidate_route_source_file"])
    assert panel["accepted_combined_results_sha256"] == sha(SIXD / "combined_results.json")
    assert len(panel["games"]) == 12 and panel["fixture_count"] == 6

    candidate_data = embedded_data(CANDIDATE_PATH)
    parent_data = embedded_data(PARENT_PATH)
    assert candidate_data == parent_data
    route_source = ROOT / panel["proposed_rule"]["candidate_route_source_file"]
    route_data = embedded_data(route_source)
    goose_rules = literal_assignment(candidate_tree, "_A44_GOOSE4_RULES")
    route_checks = route_scope(candidate_data, parent_data, route_data, parent_text, parent_tree, candidate_text, candidate_tree)
    census = feature_census(features, panel, candidate_data, goose_rules)

    proposal = ROOT / "diagnostics/residual_ice_wheat_gate_20260929/PROPOSAL.md"
    evidence = ROOT / "diagnostics/residual_ice_wheat_gate_20260929/evidence.json"
    evidence_json = read_json(evidence)
    assert evidence_json["status"] == "static_proposal_only_no_experiment_no_promotion"
    assert evidence_json["input_sha256"].get("diagnostics/a44_goose4_smoothie_source_20260929/candidate.py") == EXPECTED_6D

    preflight = {
        "schema": "a44-goose4-smoothie-ghost-wheat-static-preflight-v2",
        "passed": True,
        "static_only": True,
        "policy_action_calls": 0,
        "saved_observation_decisions_replayed": 0,
        "engine_transitions": 0,
        "outcome_games_run": 0,
        "experiment_completed": False,
        "promotion": False,
        "source_a44_sha256": EXPECTED_A44,
        "goose4_candidate_sha256": EXPECTED_GOOSE4,
        "parent_candidate_sha256": EXPECTED_6D,
        "candidate_sha256": EXPECTED_CANDIDATE,
        "patch_replacements": patch_names,
        "byte_exact_parent_patch_reconstruction": True,
        "feature_census": census,
        "route_map_and_reset_scope": route_checks,
        "structural_nontrigger_decision_equivalence": {
            "rows_proven": 206,
            "false_predicate_selects_exact_parent_rule_route": True,
            "unchanged_key_activation_commit_and_route_helpers": True,
            "base_route_map_and_farmice_reset_statements_unchanged": True,
            "added_telemetry_reset_is_additive": True,
            "ghost_telemetry_never_read_by_selection_logic": True,
            "all_embedded_route_data_identical_to_exact_6d_parent": True,
            "pre_step72_code_bytes_identical": True,
            "after_step72_state_equivalent_when_predicate_false": True,
            "proof": (
                "The candidate is the byte-exact 6d source plus the four bound replacements. "
                "For every nontrigger feature row, its route expression selects the exact parent "
                "rule route (or None); the unchanged commit helper therefore produces the same "
                "route map and the unchanged reset restores the same base state. No other action "
                "decision code changes, so the policy decisions remain equivalent on these rows."
            ),
            "action_stream_replay_claimed": False,
        },
        "source_shared151_isolation": {
            "source_branch_rows": 190,
            "shared151_rows": 18,
            "shared151_activation_count": 0,
            "donor_maps_unmodified_by_commit_path": True,
        },
        "target_panel": {
            "fixtures": panel["fixtures"],
            "game_count": 12,
            "trigger_seats": 2,
            "false_trigger_controls": 10,
            "outcome_games_not_run": True,
            "fixed_tape_only": True,
            "reactive_validation": "not run; awaits root review and outcome panel",
        },
        "verified_parent_manifests": {
            str(goose_manifest_path.resolve()): {"sha256": sha(goose_manifest_path), "binding_count": len(goose_inputs)},
            str(sixd_manifest_path.resolve()): {"sha256": sha(sixd_manifest_path), "binding_count": len(sixd_inputs)},
        },
    }
    write_new_json(HERE / "preflight.json", preflight)

    # Inherit both already-verified manifests, then bind this plan, evidence,
    # candidate and each feature trace directly into the new experiment freeze.
    input_bindings = dict(goose_inputs)
    input_bindings.update(sixd_inputs)
    direct_inputs = [
        source_a44_path, goose_candidate_path, PARENT_PATH,
        goose_manifest_path, sixd_manifest_path,
        SIXD / "goose4_parent_manifest.json", SIXD / "preflight.json",
        SIXD / "candidate.json", SIXD / "candidate.jsonl", SIXD / "combined_results.json",
        SIXD / "feature_rows.json", SIXD / "parent_panel.json", SIXD / "panel.json",
        FEATURES_PATH, route_source,
        ROOT / "diagnostics/ice_finalist_controls_20260928/screen.json",
        ROOT / "diagnostics/ice_finalist_controls_20260928/pool.json",
        ROOT / "diagnostics/stream_replay_io_20260928/cached_input.py",
        ROOT / "diagnostics/stream_replay_io_20260928/initial_states.json",
        proposal, evidence,
    ]
    direct_inputs.extend(Path(row["trace_path"]) for row in features["rows"])
    for path in direct_inputs:
        assert path.is_file(), path
        resolved = str(path.resolve())
        if resolved in input_bindings:
            continue  # The inherited frozen manifest already rehashed this file.
        input_bindings[resolved] = sha(path)
    for relative, expected_sha in evidence_json["input_sha256"].items():
        source = ROOT / relative
        resolved = str(source.resolve())
        assert source.is_file(), source
        if resolved in input_bindings:
            assert input_bindings[resolved] == expected_sha, source
        else:
            assert sha(source) == expected_sha, source
            input_bindings[resolved] = expected_sha

    output_names = ["candidate.py", "patch_spec.json", "panel.json", "PLAN.md", "PLAN_V2.md", "preflight.py", "preflight.json"]
    output_bindings = {name: sha(HERE / name) for name in output_names}
    manifest = {
        "schema": "a44-goose4-smoothie-ghost-wheat-freeze-v2",
        "complete": True,
        "diagnostic_only": True,
        "static_only": True,
        "outcome_games_run": 0,
        "experiment_completed": False,
        "promotion": False,
        "source_a44_sha256": EXPECTED_A44,
        "goose4_candidate_sha256": EXPECTED_GOOSE4,
        "parent_candidate_sha256": EXPECTED_6D,
        "candidate_sha256": EXPECTED_CANDIDATE,
        "feature_rows_sha256": sha(FEATURES_PATH),
        "preflight_sha256": sha(HERE / "preflight.json"),
        "verified_parent_binding_counts": {"goose4": len(goose_inputs), "accepted_6d": len(sixd_inputs)},
        "input_binding_count": len(input_bindings),
        "input_bindings": dict(sorted(input_bindings.items())),
        "output_bindings": output_bindings,
    }
    write_new_json(HERE / "frozen_manifest.json", manifest)

    final = read_json(HERE / "frozen_manifest.json")
    assert final["complete"] is True and final["outcome_games_run"] == 0
    for name, expected_sha in final["output_bindings"].items():
        assert sha(HERE / name) == expected_sha, name
    assert sha(HERE / "preflight.json") == final["preflight_sha256"]
    print(json.dumps({
        "passed": True,
        "static_only": True,
        "policy_action_calls": 0,
        "outcome_games_run": 0,
        "candidate_sha256": EXPECTED_CANDIDATE,
        "preflight_sha256": sha(HERE / "preflight.json"),
        "manifest_sha256": sha(HERE / "frozen_manifest.json"),
        "input_bindings": len(input_bindings),
        "verified_parent_bindings": len(goose_inputs) + len(sixd_inputs),
        "feature_rows": 208,
        "trigger_rows": len(census["trigger_census"]),
        "nontrigger_rows_proven": census["nontrigger_rows"],
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
