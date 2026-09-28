"""Aggregate the predeclared 12-game tape feasibility pilot."""

import gzip
import json
from pathlib import Path

from audit_fresh_losses import summarize

HERE = Path(__file__).resolve().parent


if __name__ == "__main__":
    pilot = json.loads((HERE / "full_tape_pilot.json").read_text(encoding="utf8"))
    structure = json.loads((HERE / "fresh_loss_structure.json").read_text(encoding="utf8"))
    assert pilot["complete"] and len(pilot["games"]) == 12
    out = {}
    for team, slug in (("DECEM", "decem"), ("Majkel1337", "majkel")):
        games = [g for g in pilot["games"] if g["team"] == team]
        source_shops = structure[team]["players"]["ours"]["states"]["455"]["shops"]
        source_trace = json.loads(gzip.decompress((HERE / f"{slug}_current_seat0_events.json.gz").read_bytes()))
        pilot_trace = json.loads(gzip.decompress((HERE / f"{slug}_full_tape_seed2716201_events.json.gz").read_bytes()))
        source_rival = summarize(source_trace, 720, 1)
        pilot_candidate = summarize(pilot_trace, 720, 0)
        by_seed = []
        for seed in pilot["seeds"]:
            pair = sorted((g for g in games if g["seed"] == seed), key=lambda g: g["candidate_seat"])
            assert len(pair) == 2
            by_seed.append({"seed": seed, "margins": [g["margin"] for g in pair],
                            "candidate_cash": [g["candidate_reward"] for g in pair],
                            "reacting_main_cash": [g["opponent_reward"] for g in pair],
                            "shops": pair[0]["candidate_capture"]["shops"],
                            "shops_match_source_first_two": pair[0]["candidate_capture"]["shops"][:2] == source_shops[:2],
                            "land_at_day18_last_hour": [g["candidate_capture"]["farms"][g["candidate_seat"]]["land"] for g in pair],
                            "hands_at_day18_last_hour": [g["candidate_capture"]["farms"][g["candidate_seat"]]["hands"] for g in pair]})
        out[team] = {
            "source_shops_first_two": source_shops[:2],
            "wins": sum(g["result"] == "win" for g in games),
            "draws": sum(g["result"] == "draw" for g in games),
            "losses": sum(g["result"] == "loss" for g in games),
            "all_done_720": all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in games),
            "pairs": by_seed,
            "seed2716201_worker_nochange_source_rival": source_rival["worker_nochange_nonpass"],
            "seed2716201_worker_nochange_pilot_tape": pilot_candidate["worker_nochange_nonpass"],
            "source_rival_sale_coins": source_rival["sale_coins"],
            "pilot_tape_sale_coins_seed2716201": pilot_candidate["sale_coins"],
            "source_rival_sales_by_item": source_rival["sales"],
            "pilot_tape_sales_by_item_seed2716201": pilot_candidate["sales"],
        }
    (HERE / "full_tape_pilot_summary.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps({team: {k:v for k,v in row.items() if k not in ("source_rival_sales_by_item", "pilot_tape_sales_by_item_seed2716201")} for team,row in out.items()}, indent=2))
