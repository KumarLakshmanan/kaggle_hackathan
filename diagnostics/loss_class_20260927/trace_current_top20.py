"""Trace current 17:25z top20 misses plus the newly swept Majkel control."""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PANEL = ROOT / "diagnostics/current_top20_20260927_172258"
MAIN = ROOT / "main.py"
EXPECTED_MAIN_SHA256 = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
TEAMS = {"DECEM", "Boey", "Vadim Vasilenko", "Majkel1337"}
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402


def main() -> None:
    digest = hashlib.sha256(MAIN.read_bytes()).hexdigest()
    assert digest == EXPECTED_MAIN_SHA256, digest
    assessment = json.loads((PANEL / "assessment.json").read_text(encoding="utf-8"))
    manifest = json.loads((PANEL / "routes/summary.json").read_text(encoding="utf-8"))
    route_by_team = {row["team"]: row for row in manifest}
    rows = []
    trace_dir = HERE / "top20_traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    for game in assessment["games"]:
        if game["team"] not in TEAMS or int(game["candidate_seat"]) != 0:
            continue
        route = route_by_team[game["team"]]
        data = run(str(MAIN), f"rawroute:{route['path']}", int(game["seed"]), 0)
        assert data["candidate_status"] == data["opponent_status"] == "DONE"
        assert float(data["candidate_reward"]) == float(game["candidate_reward"])
        assert float(data["opponent_reward"]) == float(game["opponent_reward"])
        path = trace_dir / f"{game['team'].replace(' ', '_')}-episode-{game['episode_id']}-seat0.json.gz"
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            json.dump(data, handle, separators=(",", ":"))
        seat, rival = 0, 1
        market = {p: defaultdict(float) for p in (seat, rival)}
        sale_units = {p: Counter() for p in (seat, rival)}
        workers = {p: {"requested": Counter(), "changed": Counter(), "unchanged": Counter(),
                       "hand_changed": Counter(), "hand_unchanged": Counter()} for p in (seat, rival)}
        for event in data["events"]:
            p = event.get("player")
            if p not in market:
                continue
            if event["phase"] == "market_unit" and event["success"]:
                if event["operation"] in ("SELL", "BUY_PRODUCT"):
                    market[p][event["item"]] += float(event["cash_delta"])
                if event["operation"] == "SELL":
                    sale_units[p][event["item"]] += 1
            elif event["phase"] == "unit_action":
                action = event.get("action") or ["EMPTY"]
                op = str(action[0]) if action else "EMPTY"
                if op == "PASS":
                    continue
                changed = bool(event["changed"])
                workers[p]["requested"][op] += 1
                (workers[p]["changed"] if changed else workers[p]["unchanged"])[op] += 1
                if int(event.get("actor", -1)) >= 1:
                    (workers[p]["hand_changed"] if changed else workers[p]["hand_unchanged"])[op] += 1
        gaps = {item: round(market[seat].get(item, 0) - market[rival].get(item, 0), 2)
                for item in sorted(set(market[seat]) | set(market[rival]))}
        rows.append({
            "team": game["team"], "rank": int(game["rank"]), "episode_id": int(game["episode_id"]),
            "seed": int(game["seed"]), "margin": float(game["margin"]),
            "candidate_reward": float(data["candidate_reward"]),
            "opponent_reward": float(data["opponent_reward"]),
            "trace_path": str(path.resolve()),
            "product_net_cash_own_minus_rival": gaps,
            "product_net_cash_difference": round(sum(gaps.values()), 2),
            "product_net_cash_own": round(sum(market[seat].values()), 2),
            "product_net_cash_rival": round(sum(market[rival].values()), 2),
            "sale_units_own": dict(sale_units[seat]), "sale_units_rival": dict(sale_units[rival]),
            "worker_own": {k: dict(v) for k, v in workers[seat].items()},
            "worker_rival": {k: dict(v) for k, v in workers[rival].items()},
        })
    assert {r["team"] for r in rows} == TEAMS
    out = {"candidate_sha256": digest, "panel": str(PANEL.resolve()),
           "source_panel_sha256": hashlib.sha256((PANEL / "assessment.json").read_bytes()).hexdigest(),
           "interpretation": "One-seat native tape diagnostics only; the assessment already tested both seats. Majkel is a current swept control, not a live loss.",
           "rows": rows}
    target = HERE / "current_top20_ledgers.json"
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target.resolve()),
                      "rows": [{"team": r["team"], "margin": r["margin"],
                                "product_gap": r["product_net_cash_difference"],
                                "item_gaps": r["product_net_cash_own_minus_rival"],
                                "own_unchanged": r["worker_own"]["unchanged"],
                                "rival_unchanged": r["worker_rival"]["unchanged"]}
                               for r in rows]}, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
