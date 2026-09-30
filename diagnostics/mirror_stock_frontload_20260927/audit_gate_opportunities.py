"""Read frozen public replays for an observation-only persistent mirror gate."""

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_submission_56572390_20260926"
SUMMARY = LIVE / "mirror_dev_routes" / "summary.json"
OUT = HERE / "gate_opportunities.json"


def matched(observation):
    farms = observation["farms"]
    return (farms[0]["tiles"] == farms[1]["tiles"]
            and farms[0]["farmer"] == farms[1]["farmer"]
            and farms[0]["hands"] == farms[1]["hands"])


def inspect(row):
    episode = row["episode_id"]
    replay = json.loads((LIVE / f"episode-{episode}-replay.json").read_text(encoding="utf-8"))
    seat = int(row["our_live_seat"])
    streak = longest = match_turns = 0
    latched_at = None
    stock_steps = []
    possible_steps = []
    near_steps = []
    aligned_steps = []
    eligible_steps = []
    eligible_below60_steps = []
    target_state = []
    for step in range(144, min(718, len(replay["steps"]))):
        frame = replay["steps"][step][seat]
        observation = frame["observation"]
        same = matched(observation)
        match_turns += same
        streak = streak + 1 if same else 0
        longest = max(longest, streak)
        if latched_at is None and streak >= 24:
            latched_at = step
        if step < 480:
            continue
        shed = observation.get("private", {}).get("shed", {})
        stock = int(shed.get("STRAWBERRY", 0) or 0)
        quote = int(observation["market"]["prices"].get("STRAWBERRY", 0) or 0)
        if stock >= 4 and quote > 1:
            stock_steps.append(step)
            if latched_at is not None:
                possible_steps.append(step)
                if not same:
                    near_steps.append(step)
                    farms = observation["farms"]
                    aligned = (farms[0]["farmer"] == farms[1]["farmer"]
                               and farms[0]["hands"] == farms[1]["hands"])
                    if aligned:
                        aligned_steps.append(step)
                        action = frame.get("action") or {}
                        market = action.get("market") or [] if isinstance(action, dict) else []
                        commands = ([action.get("farmer") or ["PASS"],
                                     *(action.get("hands") or [])]
                                    if isinstance(action, dict) else [])
                        can_add = (isinstance(market, list) and len(market) < 10
                                   and not any(isinstance(order, (list, tuple)) and order
                                               and (order[0] == "BUY_PRODUCT" or
                                                    (len(order) > 1 and order[0] == "SELL"
                                                     and order[1] == "STRAWBERRY"))
                                               for order in market)
                                   and not any(isinstance(command, (list, tuple))
                                               and len(command) > 1
                                               and command[0] == "PICKUP"
                                               and command[1] == "STRAWBERRY"
                                               for command in commands))
                        if can_add:
                            eligible_steps.append(step)
                            if quote < 60:
                                eligible_below60_steps.append(step)
        if episode == 113642505 and 686 <= step <= 693:
            target_state.append({"step": step, "stock": stock, "quote": quote,
                                 "same": same, "latched": latched_at is not None,
                                 "aligned": (observation["farms"][0]["farmer"]
                                             == observation["farms"][1]["farmer"]
                                             and observation["farms"][0]["hands"]
                                             == observation["farms"][1]["hands"]),
                                 "action": frame.get("action")})
    return {"episode_id": episode, "class": row["screen_class"],
            "margin": row["live_margin"], "match_turns": match_turns,
            "longest_streak": longest, "latched_at": latched_at,
            "stock_steps": stock_steps, "possible_steps": possible_steps,
            "near_steps": near_steps, "aligned_steps": aligned_steps,
            "eligible_steps": eligible_steps,
            "eligible_below60_steps": eligible_below60_steps,
            "target_state": target_state}


def main():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows = [inspect(row) for row in summary]
    OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for row in rows:
        print(row["episode_id"], row["class"], row["margin"],
              "match", row["match_turns"], "longest", row["longest_streak"],
              "latched", row["latched_at"], "stock", len(row["stock_steps"]),
              "possible", len(row["possible_steps"]),
              "near", len(row["near_steps"]),
              "aligned", len(row["aligned_steps"]),
              "eligible", len(row["eligible_steps"]),
              "below60", len(row["eligible_below60_steps"]),
              "target", 689 in row["possible_steps"])
        if row["target_state"]:
            print("TARGET_STATE", json.dumps(row["target_state"], ensure_ascii=False))
    print(OUT)


if __name__ == "__main__":
    main()
