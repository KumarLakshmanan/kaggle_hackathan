"""Causal execution diagnostics for the eight known replay losses."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game import run


def audit(row):
    d = run(str(ROOT / "exp_shunki_land_retry_20260927.py"),
            "rawroute:" + row["route_path"], row["seed"], 0)
    records = d["traces"][0]
    counts, details = Counter(), []
    for rec in records:
        obs, action = rec["observation"], rec["action"]
        farm = obs["farms"][0]
        pos = [farm["farmer"]] + farm["hands"]
        invs = obs["private"]["inventories"]
        units = [action.get("farmer", [])] + action.get("hands", [])
        for actor, (xy, unit, inv) in enumerate(zip(pos, units, invs)):
            if not unit:
                continue
            x, y = xy
            tile, op = farm["tiles"][y][x], unit[0]
            reason = None
            if tile == "LOCKED" and op in ("PLANT", "WATER", "HARVEST", "FEED", "FERTILIZE", "CARE"):
                reason = "locked_" + op
            elif op == "FEED" and isinstance(tile, dict) and tile.get("animal") and not tile.get("fed_today") and not inv.get("WHEAT", 0):
                reason = "feed_without_wheat"
            elif op == "FERTILIZE" and isinstance(tile, dict) and tile.get("crop") and not inv.get("FERTILIZER", 0):
                reason = "fertilize_without_supply"
            elif op == "PLANT" and isinstance(tile, dict) and tile.get("kind") == "WEED":
                reason = "plant_on_weed"
            elif op == "PLANT" and tile is None and not obs["private"]["seeds"].get(unit[1], 0):
                reason = "plant_without_seed"
            if reason:
                counts[reason] += 1
                if counts[reason] <= 4:
                    details.append({"step": obs["step"], "actor": actor, "position": xy,
                                    "reason": reason, "action": unit, "inventory": inv,
                                    "tile": tile, "shed": obs["private"]["shed"]})
    last = records[-1]
    obs = last["observation"]
    result = {"team": row["team"], "seed": row["seed"],
              "margin": d["candidate_reward"] - d["opponent_reward"],
              "candidate_cash": d["candidate_reward"], "opponent_cash": d["opponent_reward"],
              "counts": dict(counts), "examples": details,
              "last_private": obs["private"], "last_prices": obs["market"]["prices"],
              "last_positions": [obs["farms"][0]["farmer"]] + obs["farms"][0]["hands"],
              "last_action": last["action"], "shops": obs["town"]["unlocked_shops"]}
    return result


if __name__ == "__main__":
    rows = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/comparison.json").read_text(encoding="utf8"))["losses"]
    results = []
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(audit, row) for row in rows]):
            r = future.result()
            results.append(r)
            print(r["team"], r["margin"], r["counts"], flush=True)
    (HERE / "remaining_execution_audit.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")
