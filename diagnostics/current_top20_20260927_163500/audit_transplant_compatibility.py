"""Compare current farm with recorded and native-replayed opponent farms at shop reveals.

This reads public replay observations only. No downloaded agent code is executed.
"""

from collections import Counter
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEAMS = ("DECEM", "Majkel1337")
STEPS = (71, 72, 73, 143, 144, 145)


def live_tiles(farm):
    out = {}
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind in (None, "EMPTY"):
                continue
            out[f"{y},{x}"] = {
                "kind": kind,
                "crop": tile.get("crop"),
                "animal": tile.get("animal"),
                "planted_day": tile.get("planted_day"),
                "placed_day": tile.get("placed_day"),
                "yield_units": tile.get("yield_units"),
            }
    return out


def profile(obs, seat):
    farm = obs["farms"][seat]
    private = obs["private"]
    sites = live_tiles(farm)
    return {
        "day": obs["day"], "hour": obs["hour"],
        "shops": obs["town"]["unlocked_shops"],
        "cash": farm["money"],
        "land": farm["unlocked_quadrants"],
        "farmer": farm["farmer"],
        "hands": farm["hands"],
        "crops": dict(Counter(t["crop"] for t in sites.values() if t["crop"])),
        "animals": dict(Counter(t["animal"] for t in sites.values() if t["animal"])),
        "tile_kinds": dict(Counter(t["kind"] for t in sites.values())),
        "sites": sites,
        "shed": {k: v for k, v in private["shed"].items() if v},
        "seeds": {k: v for k, v in private["seeds"].items() if v},
    }


def site_diff(own, target):
    a, b = own["sites"], target["sites"]
    compatible = lambda t: (t["kind"], t["crop"], t["animal"])
    overlap = [p for p in a.keys() & b.keys() if compatible(a[p]) == compatible(b[p])]
    mismatch = [p for p in a.keys() | b.keys() if p not in overlap]
    hands_a = Counter(map(tuple, own["hands"]))
    hands_b = Counter(map(tuple, target["hands"]))
    return {
        "same_site_count": len(overlap),
        "own_site_count": len(a),
        "target_site_count": len(b),
        "different_site_count": len(mismatch),
        "different_sites": sorted(mismatch),
        "hand_position_overlap": sum((hands_a & hands_b).values()),
        "own_hand_count": len(own["hands"]),
        "target_hand_count": len(target["hands"]),
        "farmer_same_position": own["farmer"] == target["farmer"],
    }


def load_gz(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def main():
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    output = {"method": "same source seed; native original shops; source episode observations and exact 4ee-vs-tape native event traces", "teams": {}}
    for team in TEAMS:
        entry = next(row for row in manifest["rows"] if row["team"] == team)
        native = load_gz(HERE / ("decem_current_seat0_events.json.gz" if team == "DECEM" else "majkel_current_seat0_events.json.gz"))
        source = load_gz(Path(entry["replay_path"]))
        seat = entry["source_seat"]
        assert native["seed"] == entry["seed"]
        profiles = {}
        for step in STEPS:
            own = profile(native["traces"][0][step]["observation"], 0)
            rival = profile(native["traces"][1][step]["observation"], 1)
            recorded = profile(source["steps"][step][seat]["observation"], seat)
            assert own["shops"] == rival["shops"] == recorded["shops"]
            profiles[str(step)] = {
                "ours": own,
                "native_tape_rival": rival,
                "source_recorded_tape": recorded,
                "ours_vs_native_tape_rival": site_diff(own, rival),
                "ours_vs_source_recorded_tape": site_diff(own, recorded),
            }
        own_actions = [x["action"] for x in native["traces"][0]]
        rival_actions = [x["action"] for x in native["traces"][1]]
        first_action_diff = next((i for i, (a, b) in enumerate(zip(own_actions, rival_actions)) if a != b), None)
        output["teams"][team] = {
            "source_episode": entry["episode_id"],
            "source_seat": seat,
            "seed": entry["seed"],
            "source_action_sha256": entry["action_sha256"],
            "first_action_difference_step": first_action_diff,
            "action_differences_before_step72": sum(a != b for a, b in zip(own_actions[:72], rival_actions[:72])),
            "action_differences_before_step144": sum(a != b for a, b in zip(own_actions[:144], rival_actions[:144])),
            "profiles": profiles,
        }
    path = HERE / "transplant_compatibility.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf8")
    print(path)
    for team, row in output["teams"].items():
        print("\n", team, "first action diff", row["first_action_difference_step"], "diff by 72/144", row["action_differences_before_step72"], row["action_differences_before_step144"])
        for step in STEPS:
            p = row["profiles"][str(step)]
            print("step", step, "shops", p["ours"]["shops"])
            for key in ("ours", "native_tape_rival", "source_recorded_tape"):
                x = p[key]
                print(key, "cash", x["cash"], "land", x["land"], "farmer", x["farmer"], "hands", x["hands"], "crops", x["crops"], "animals", x["animals"], "shed", x["shed"], "seeds", x["seeds"])
            for key in ("ours_vs_native_tape_rival", "ours_vs_source_recorded_tape"):
                x = p[key]
                print(key, "site exact", x["same_site_count"], "/", x["own_site_count"], x["target_site_count"], "hands overlap", x["hand_position_overlap"], "/", x["own_hand_count"], x["target_hand_count"])


if __name__ == "__main__":
    main()
