"""Select activation seeds from incumbent-only, native shop observations."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
import paired_benchmark  # noqa: E402

MAIN = ROOT / "main.py"
PRIOR = ROOT / "main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
CANDIDATE = HERE / "exp_land_retry_current_4ee.py"
EXPECTED_MAIN = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
EXPECTED_PRIOR = "3cc0f69fcb9f6a8bee17bf6789f0f321a17f0d47324c462def1e783d6921a603"
EXPECTED_CANDIDATE = "675893edc7ff07517dc57f60d322341b131ecd0d5286d9728d98d423cdc35e51"
FIRST_N = 16
MAX_RETRY_STEP = 600
CHUNK_SIZE = 8
WORKERS = 6


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_one(seed: int) -> dict:
    main_module = paired_benchmark._load_module(MAIN, f"land_scan_main_{seed}")
    prior_module = paired_benchmark._load_module(PRIOR, f"land_scan_prior_{seed}")
    candidate_module = paired_benchmark._load_module(CANDIDATE, f"land_scan_candidate_{seed}")
    candidate_module._LAND_INTENT.clear()
    prior_name = prior_module.__name__
    main_name = main_module.__name__
    candidate_name = candidate_module.__name__
    steps_seen = 0
    first_two_shops = None
    failed_land_steps: list[int] = []
    retry_trigger = None
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": int(seed)}, debug=False)
    try:
        states = env.reset()
        while True:
            observations = [state.observation for state in states]
            obs = observations[0]
            step = int(obs["step"])
            steps_seen += 1
            action = main_module.agent(obs, env.configuration)
            base_action = copy.deepcopy(action)
            if first_two_shops is None and len(obs["town"]["unlocked_shops"]) >= 2:
                first_two_shops = list(obs["town"]["unlocked_shops"][:2])

            farm = obs["farms"][0]
            land_before = len(farm["unlocked_quadrants"])

            # Only inspect the frozen layer after a scheduled land order has
            # demonstrably failed in an earlier native step.
            if failed_land_steps and step > failed_land_steps[-1] and step < MAX_RETRY_STEP:
                repaired = candidate_module._land_repair(
                    copy.deepcopy(obs), copy.deepcopy(base_action), env.configuration
                )
                before_orders = list(base_action.get("market", []))
                after_orders = list(repaired.get("market", []))
                if after_orders != before_orders and any(
                    order and order[0] == "BUY_LAND" for order in after_orders
                ):
                    retry_trigger = {
                        "failed_land_step": failed_land_steps[-1],
                        "retry_step": step,
                        "retry_day": step // 24,
                        "cash_at_retry_observation": float(farm["money"]),
                        "owned_at_retry_observation": land_before,
                        "shops_at_retry_observation": list(obs["town"]["unlocked_shops"]),
                        "market_before": before_orders,
                        "market_after": after_orders,
                    }
                    break

            # The opponent remains the previous submitted policy, which
            # reacts to the native public state and endogenous shops.
            actions = [action, prior_module.agent(observations[1], env.configuration)]
            states = env.step(actions)
            next_obs = states[0].observation
            if any(order and order[0] == "BUY_LAND" for order in base_action.get("market", [])):
                next_land = len(next_obs["farms"][0]["unlocked_quadrants"])
                if next_land <= land_before:
                    failed_land_steps.append(step)
            if int(next_obs["step"]) >= MAX_RETRY_STEP:
                break
            if all(state.status != "ACTIVE" for state in states):
                break

        row = {
            "seed": int(seed),
            "eligible": retry_trigger is not None,
            "first_two_shops": first_two_shops,
            "failed_land_steps": failed_land_steps,
            "retry_trigger": retry_trigger,
            "scan_steps": steps_seen,
            "scan_stop": "first_funded_retry" if retry_trigger else "step_600_or_terminal",
            "scan_status": [state.status for state in states],
        }
        return row
    finally:
        for name in (prior_name, main_name, candidate_name):
            sys.modules.pop(name, None)


def scan_pool(start: int, end: int, label: str, output_name: str) -> None:
    assert sha(MAIN) == EXPECTED_MAIN
    assert sha(PRIOR) == EXPECTED_PRIOR
    candidate_hash = sha(CANDIDATE)
    assert not EXPECTED_CANDIDATE or candidate_hash == EXPECTED_CANDIDATE
    assert start <= end

    scanned: list[dict] = []
    selected: list[dict] = []
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for chunk_start in range(start, end + 1, CHUNK_SIZE):
            chunk_end = min(end, chunk_start + CHUNK_SIZE - 1)
            batch = list(range(chunk_start, chunk_end + 1))
            batch_rows = list(pool.map(scan_one, batch))
            batch_rows.sort(key=lambda row: row["seed"])
            scanned.extend(batch_rows)
            selected.extend(row for row in batch_rows if row["eligible"])
            if len(selected) >= FIRST_N:
                selected = selected[:FIRST_N]
                break
            print(
                f"{label}: scanned {chunk_start}-{chunk_end}; eligible "
                f"{len(selected)}/{FIRST_N}", flush=True
            )

    selected_ids = [row["seed"] for row in selected]
    payload = {
        "label": label,
        "candidate_sha256": candidate_hash,
        "incumbent_sha256": EXPECTED_MAIN,
        "selection_reference": str(PRIOR.resolve()),
        "selection_reference_sha256": EXPECTED_PRIOR,
        "scan_bounds": [start, end],
        "first_n": FIRST_N,
        "chunk_size": CHUNK_SIZE,
        "workers": WORKERS,
        "selection_rule": (
            "First ascending seeds where incumbent seat 0 requests a route-intended "
            "BUY_LAND that fails to increase owned quadrants, and at a later native "
            "observation before step 600 the frozen retry layer appends a funded "
            "BUY_LAND after its commitment and reserve checks. Selection uses no rewards."
        ),
        "scanned_count": len(scanned),
        "eligible_count_scanned": sum(row["eligible"] for row in scanned),
        "selected_seeds": selected_ids,
        "selected": selected,
        "scanned": scanned,
        "complete": len(selected_ids) == FIRST_N,
    }
    target = HERE / output_name
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in (
        "label", "scan_bounds", "scanned_count", "eligible_count_scanned",
        "selected_seeds", "complete"
    )}, indent=2), flush=True)
    if len(selected_ids) != FIRST_N:
        raise SystemExit(f"Only {len(selected_ids)} eligible seeds in frozen scan range")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: select_land_retry_seeds.py START END OUTPUT_NAME")
    lo, hi = map(int, sys.argv[1:3])
    filename = sys.argv[3]
    label = "development" if lo == 2730000 else "confirmation"
    scan_pool(lo, hi, label, filename)
