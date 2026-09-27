"""Check predeclared day-16 tomato opportunity exposure before treatment."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
META = HERE / "early_tomato16_panel20_meta.json"
BASE = HERE / "early_tomato16_baseline_capture20.json"
OUTPUT = HERE / "early_tomato16_exposure.json"


def visible_gate(capture: dict) -> bool:
    farm = capture["farms"][capture["player"]]
    demand = sum(shop in ("PIZZA_SHOP", "FARMERS_MARKET")
                 for shop in capture["shops"])
    return (farm["land"] == 3 and farm["money"] >= 12000
            and capture["prices"]["TOMATO"] >= 70 and demand >= 2)


def main() -> None:
    meta = json.loads(META.read_text(encoding="utf8"))
    panel = json.loads(BASE.read_text(encoding="utf8"))
    classes = {row["action_sha256"]: "target" for row in meta["targets"]}
    classes.update({row["action_sha256"]: "control" for row in meta["controls"]})
    assert len(classes) == 20 and len(panel["rows"]) == 20
    rows = []
    for group in panel["rows"]:
        games = sorted(group["games"], key=lambda game: game["candidate_seat"])
        assert len(games) == 2
        seats = []
        for game in games:
            cap = game["candidate_capture"]
            assert cap and cap["step"] == 384
            farm = cap["farms"][cap["player"]]
            seats.append({"seat": game["candidate_seat"], "visible_gate": visible_gate(cap),
                          "money": farm["money"], "land": farm["land"],
                          "tomato_price": cap["prices"]["TOMATO"],
                          "tomato_shop_count": sum(shop in ("PIZZA_SHOP", "FARMERS_MARKET")
                                                   for shop in cap["shops"]),
                          "shops": cap["shops"], "margin": game["margin"]})
        rows.append({"team": group["team"], "action_sha256": group["action_sha256"],
                     "screen_class": classes[group["action_sha256"]], "seats": seats,
                     "both_seats_gate": all(seat["visible_gate"] for seat in seats)})
    targets = [row for row in rows if row["screen_class"] == "target"]
    controls = [row for row in rows if row["screen_class"] == "control"]
    summary = {"targets": len(targets), "controls": len(controls),
               "target_routes_both_seats_gate": sum(row["both_seats_gate"] for row in targets),
               "control_routes_both_seats_gate": sum(row["both_seats_gate"] for row in controls)}
    summary["exposure_gate_passed"] = summary["target_routes_both_seats_gate"] >= 3
    OUTPUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2,
                                 ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2))
    for row in rows:
        if row["both_seats_gate"]:
            print(row["screen_class"], row["team"], row["seats"][0]["tomato_price"],
                  row["seats"][0]["tomato_shop_count"])
    print(OUTPUT)


if __name__ == "__main__":
    main()
