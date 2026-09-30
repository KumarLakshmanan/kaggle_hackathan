"""Passive feasibility traces for an observed-demand crop controller."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game import run


if __name__ == "__main__":
    candidate = ROOT / "main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == "3cc0f69fcb9f6a8bee17bf6789f0f321a17f0d47324c462def1e783d6921a603"
    routes = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
    results = []
    for team in ("Snorlax", "We wanna be tomatos", "Majkel1337"):
        route = next(r for r in routes if r["team"] == team)
        target = HERE / f"episode-{route['episode_id']}-seat0.json.gz"
        if target.exists():
            with gzip.open(target, "rt", encoding="utf8") as handle:
                trace = json.load(handle)
        else:
            trace = run(str(candidate), "rawroute:" + route["path"], route["seed"], 0)
            with gzip.open(target, "wt", encoding="utf8") as handle:
                json.dump(trace, handle, separators=(",", ":"))
        records = trace["traces"][0]
        planted, purchases, windows = [], [], []
        for rec in records[144:]:
            step, obs, action = rec["step"], rec["observation"], rec["action"]
            positions = [obs["farms"][0]["farmer"], *obs["farms"][0]["hands"]]
            commands = [action.get("farmer", []), *action.get("hands", [])]
            for order in action.get("market", []):
                if order[:2] == ["BUY_SEED", "STRAWBERRY"]:
                    purchases.append({"step": step, "quantity": order[2]})
            for actor, (pos, command) in enumerate(zip(positions, commands)):
                if command[:2] == ["PLANT", "STRAWBERRY"]:
                    planted.append({"step": step, "actor": actor, "position": pos,
                                    "shops": obs["town"]["unlocked_shops"], "cash": obs["farms"][0]["money"],
                                    "prices": {k: obs["market"]["prices"][k] for k in ("STRAWBERRY", "MELON")}})
                tile = obs["farms"][0]["tiles"][pos[1]][pos[0]]
                if not isinstance(tile, dict) or tile.get("crop") != "STRAWBERRY" or step + 2 >= 719 or step//24 != (step+2)//24:
                    continue
                ops = []
                for later in records[step:step+3]:
                    farm = later["observation"]["farms"][0]
                    poses = [farm["farmer"], *farm["hands"]]
                    units = [later["action"].get("farmer", []), *later["action"].get("hands", [])]
                    if actor >= len(poses) or actor >= len(units) or poses[actor] != pos or not units[actor]:
                        break
                    ops.append(units[actor][0])
                if len(ops) == 3 and all(op in ("WATER", "FERTILIZE", "HARVEST", "PASS", "CARE") for op in ops):
                    windows.append({"step": step, "actor": actor, "position": pos, "operations": ops,
                                    "planted_day": tile.get("planted_day")})
        result = {"team": team, "seed": route["seed"], "margin": trace["margin"],
                  "statuses": [trace["candidate_status"], trace["opponent_status"]],
                  "late_strawberry_seed_orders": purchases, "late_strawberry_plantings": planted,
                  "three_slot_windows": windows, "trace": str(target)}
        results.append(result)
        (HERE / "audit.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")
        print(team, "late plantings", len(planted), "three-slot windows", len(windows), "margin", trace["margin"], flush=True)
