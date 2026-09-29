"""Reproduce ae349's terminal DECEM transition and measure actual market fills."""
from __future__ import annotations

from collections import Counter
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from diagnostics.local_target_20260928.run_lock import exclusive_run  # noqa: E402
from diagnostics.physical_route_rollout_20260928 import native_core as core  # noqa: E402
from diagnostics.physical_route_rollout_20260928.check import Box, state_from_frames  # noqa: E402
from diagnostics.stream_replay_io_20260928.cached_input import load_fixture  # noqa: E402

CANDIDATE = ROOT / "main_candidate_improved_20260929.py"
CANDIDATE_SHA = "ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb"
PANEL = ROOT / "diagnostics/combined_agent_257f_20260929/saved_panel"
MANIFEST = PANEL / "comparison_manifest.json"
RESULTS = PANEL / "comparison_manifest_results.jsonl"
RECEIPT = HERE / "trace_receipt.json"
PLAN = HERE / "PLAN.md"
LOCK = ROOT / "diagnostics/.shared_game_run.lock"
FIXTURE_ID = "top20-01-DECEM-114267880"
EXPECTED = {
    "manifest": "b5f7be800528fb8d070caa9fbaf3493c3b934c3176a6416590d2d6a2dd3ab3fe",
    "results": "ebe9c97327a0086766f67c88213e2fe086ebfa8f89d8ba84db8f5ba918091562",
    "candidate": CANDIDATE_SHA,
}
HELPERS = {
    "fast_game_cached.py": ROOT / "diagnostics/stream_replay_io_20260928/fast_game_cached.py",
    "cached_input.py": ROOT / "diagnostics/stream_replay_io_20260928/cached_input.py",
    "native_core.py": ROOT / "diagnostics/physical_route_rollout_20260928/native_core.py",
    "check.py": ROOT / "diagnostics/physical_route_rollout_20260928/check.py",
    "run_lock.py": ROOT / "diagnostics/local_target_20260928/run_lock.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest_json(value) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def read_trace(seat: int) -> list[dict]:
    path = HERE / f"ae349_decem_seat{seat}.jsonl.gz"
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    assert len(rows) == 719 and [int(row["step"]) for row in rows] == list(range(719))
    return rows


def load_inputs() -> tuple[dict, dict, dict]:
    assert sha(CANDIDATE) == EXPECTED["candidate"]
    assert sha(MANIFEST) == EXPECTED["manifest"]
    assert sha(RESULTS) == EXPECTED["results"]
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert receipt["complete"] and receipt["passed"] and receipt["diagnostic_only_fixed_tape"]
    assert receipt["candidate_sha256"] == EXPECTED["candidate"]
    helper_hashes = {"candidate": sha(CANDIDATE),
                     **{name: sha(path) for name, path in HELPERS.items()}}
    assert helper_hashes == receipt["helper_sha256"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fixtures = {
        int(case["candidate_seat"]): case["fixture"]
        for case in manifest["cases"]
        if case["fixture"]["fixture_id"] == FIXTURE_ID
    }
    assert set(fixtures) == {0, 1}
    reference_rows = {}
    for line in RESULTS.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("fixture_id") == FIXTURE_ID:
            reference_rows[int(row["candidate_seat"])] = row["candidate"]["raw"]
    assert set(reference_rows) == {0, 1}
    return fixtures, reference_rows, receipt


def analyze_seat(seat: int, fixture: dict, reference: dict, receipt_row: dict) -> dict:
    trace_path = HERE / f"ae349_decem_seat{seat}.jsonl.gz"
    trace_rows = read_trace(seat)
    assert sha(trace_path) == receipt_row["trace_sha256"]
    assert all(row["observation"]["player"] == seat for row in trace_rows)

    replay = load_fixture(fixture)
    assert len(replay["steps"]) == 1 and replay["configuration"]["episodeSteps"] == 720
    tape = json.loads(gzip.decompress(Path(fixture["source_action_tape_path"]).read_bytes()))["actions"]
    assert len(tape) == 719
    state = state_from_frames(replay["steps"][0])
    cfg = dict(replay["configuration"])
    cfg["seed"] = None
    env = Box(configuration=Box(**cfg), info={"seed": int(fixture["seed"])}, done=False)
    module_spec = importlib.util.spec_from_file_location(f"ae349_terminal_audit_seat{seat}", CANDIDATE)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    market_capture: dict = {}
    original_process_market = core._process_market

    def capture_market(current_state, current_env):
        obs = current_state[0].observation
        before = {
            "cash": [float(farm["money"]) for farm in obs.farms],
            "shed": [dict(item.observation.private.get("shed", {})) for item in current_state],
            "inventory": dict(obs.market["inventory"]),
            "prices": dict(obs.market["prices"]),
            "params": copy.deepcopy(obs.market.get("params")),
        }
        original_process_market(current_state, current_env)
        after_obs = current_state[0].observation
        after = {
            "cash": [float(farm["money"]) for farm in after_obs.farms],
            "shed": [dict(item.observation.private.get("shed", {})) for item in current_state],
            "inventory": dict(after_obs.market["inventory"]),
            "prices": dict(after_obs.market["prices"]),
            "params": copy.deepcopy(after_obs.market.get("params")),
        }
        market_capture.update(before=before, after=after)

    actions = []
    try:
        for step in range(719):
            obs = copy.deepcopy(dict(state[seat].observation, remainingOverageTime=60.0))
            action = module.agent(obs, cfg)
            actions.append(action)
            state[seat].action = action
            state[1 - seat].action = copy.deepcopy(tape[step])
            assert action == trace_rows[step]["action"], f"trace action mismatch at seat={seat}, step={step}"
            if step == 718:
                pre_action_cash = [float(farm["money"]) for farm in state[0].observation.farms]
                pre_action_margin = pre_action_cash[seat] - pre_action_cash[1 - seat]
                pre_action_shed = dict(state[seat].observation.private.get("shed", {}))
                pre_action_inventories = copy.deepcopy(
                    state[seat].observation.private.get("inventories", []))
                current_action = copy.deepcopy(action)
                rival_action = copy.deepcopy(tape[step])
                core._process_market = capture_market
            core.interpreter(state, env)
            if step == 718:
                core._process_market = original_process_market
            for item in state:
                item.observation.step = step + 1
        rewards = [float(item.reward) for item in state]
    finally:
        core._process_market = original_process_market

    telemetry = dict(getattr(module.agent, "telemetry", {}) or {})
    assert digest_json(actions) == digest_json([row["action"] for row in trace_rows])
    assert telemetry == reference["candidate_telemetry"]
    assert rewards[seat] == float(reference["candidate_reward"])
    assert rewards[1 - seat] == float(reference["opponent_reward"])
    assert state[seat].status == state[1 - seat].status == "DONE"
    assert market_capture and current_action == trace_rows[718]["action"]

    before, after = market_capture["before"], market_capture["after"]
    requested = Counter()
    for order in current_action.get("market", []):
        if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
            requested[str(order[1])] += max(0, int(order[2]))
    sold = {
        item: max(0, int(before["shed"][seat].get(item, 0)) - int(after["shed"][seat].get(item, 0)))
        for item in set(before["shed"][seat]) | set(after["shed"][seat])
        if int(before["shed"][seat].get(item, 0)) > int(after["shed"][seat].get(item, 0))
    }
    market_cash_delta = [after["cash"][idx] - before["cash"][idx] for idx in (0, 1)]
    pre_market_margin = before["cash"][seat] - before["cash"][1 - seat]
    post_market_margin = after["cash"][seat] - after["cash"][1 - seat]
    final_margin = rewards[seat] - rewards[1 - seat]
    final_shed = dict(state[seat].observation.private.get("shed", {}))
    final_inventories = copy.deepcopy(state[seat].observation.private.get("inventories", []))
    extra_fertilizer_prices = [
        core.market_price(
            "FERTILIZER",
            int(before["inventory"].get("FERTILIZER", 0))
            + int(sold.get("FERTILIZER", 0)) + offset,
            before["params"],
        )
        for offset in range(int(final_shed.get("FERTILIZER", 0)))
    ]
    return {
        "seat": seat,
        "trace_sha256": sha(trace_path),
        "candidate_action_hash": digest_json(actions),
        "terminal_transition": 718,
        "preterminal_cash": {"own": before["cash"][seat], "rival": before["cash"][1 - seat],
                             "margin": pre_action_margin},
        "worker_drops_then_market": {
            "pre_action_shed_before_worker_drops": pre_action_shed,
            "worker_commands": {"farmer": current_action.get("farmer", ["PASS"]),
                                "hands": current_action.get("hands", [])},
            "pre_action_worker_inventories": pre_action_inventories,
            "final_worker_inventories_after_terminal_transition": final_inventories,
            "market_shed_at_start": before["shed"][seat],
            "market_shed_after": after["shed"][seat],
            "requested_sell_units_by_item": dict(sorted(requested.items())),
            "actual_sell_units_by_item": dict(sorted(sold.items())),
            "market_cash_delta_own": market_cash_delta[seat],
            "market_cash_delta_rival": market_cash_delta[1 - seat],
            "market_margin_delta": post_market_margin - pre_market_margin,
            "market_prices_before": before["prices"],
            "market_prices_after": after["prices"],
            "final_shed_after_terminal_transition": final_shed,
            "static_extra_fertilizer_sale_calculation": {
                "units_remaining": int(final_shed.get("FERTILIZER", 0)),
                "marginal_prices": extra_fertilizer_prices,
                "extra_cash_if_sold_after_current_queue": sum(extra_fertilizer_prices),
                "terminal_margin_if_only_added": final_margin + sum(extra_fertilizer_prices),
                "scope": "Exact market-price calculation only; altered action was not simulated",
            },
            "opponent_market_orders": rival_action.get("market", []),
        },
        "terminal_rewards": {"own": rewards[seat], "rival": rewards[1 - seat],
                              "margin": final_margin,
                              "result": "win" if final_margin > 0 else "loss" if final_margin < 0 else "draw"},
        "reference_match": {
            "candidate_reward": rewards[seat] == float(reference["candidate_reward"]),
            "opponent_reward": rewards[1 - seat] == float(reference["opponent_reward"]),
            "margin": final_margin == float(reference["margin"]),
            "receipt_match": final_margin == float(receipt_row["actual_margin"]),
        },
    }


def main() -> None:
    fixtures, references, receipt = load_inputs()
    receipt_rows = {int(row["candidate_seat"]): row for row in receipt["games"]}
    with exclusive_run(LOCK):
        summaries = [analyze_seat(seat, fixtures[seat], references[seat], receipt_rows[seat])
                     for seat in (0, 1)]
    assert all(all(row["reference_match"].values()) for row in summaries)
    result = {
        "schema": "ae349-decem-terminal-market-analysis-v1",
        "diagnostic_only_fixed_tape": True,
        "candidate_sha256": EXPECTED["candidate"],
        "manifest_sha256": EXPECTED["manifest"],
        "reference_results_sha256": EXPECTED["results"],
        "trace_receipt_sha256": sha(RECEIPT),
        "plan_sha256": sha(PLAN),
        "analyzer_sha256": sha(Path(__file__)),
        "both_seats_reproduced": True,
        "seat_analysis": summaries,
    }
    out = HERE / "trace_analysis.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "analysis_sha256": sha(out),
        "seats": [{
            "seat": row["seat"],
            "preterminal_margin": row["preterminal_cash"]["margin"],
            "actual_sold_units": row["worker_drops_then_market"]["actual_sell_units_by_item"],
            "own_market_cash_delta": row["worker_drops_then_market"]["market_cash_delta_own"],
            "market_margin_delta": row["worker_drops_then_market"]["market_margin_delta"],
            "terminal_margin": row["terminal_rewards"]["margin"],
            "final_unsold_shed": row["worker_drops_then_market"]["final_shed_after_terminal_transition"],
            "result": row["terminal_rewards"]["result"],
        } for row in summaries],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
