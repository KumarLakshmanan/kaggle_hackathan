"""Compare exact same-tape Yizhou seat-0 traces for 4ee and c68."""

from collections import Counter
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads(gzip.decompress((HERE / name).read_bytes()))


def cash(record, seat):
    return float(record["observation"]["farms"][seat]["money"])


def market_set(action):
    return Counter(json.dumps(x, sort_keys=True) for x in action.get("market", []))


def action_diff(new, old):
    return {
        "any": new != old,
        "market_order": new.get("market") != old.get("market"),
        "market_orders_or_quantities": market_set(new) != market_set(old),
        "physical_farmer": new.get("farmer") != old.get("farmer"),
        "physical_hands": new.get("hands") != old.get("hands"),
    }


if __name__ == "__main__":
    new = read("yizhou_current_seat0_trace.json.gz")
    old = read("yizhou_prior_seat0_trace.json.gz")
    assert new["candidate_seat"] == old["candidate_seat"] == 0
    assert new["seed"] == old["seed"] == 383655650
    assert (new["candidate_reward"], new["opponent_reward"]) == (157368, 91286)
    assert (old["candidate_reward"], old["opponent_reward"]) == (171155, 73418)
    a, b = new["traces"][0], old["traces"][0]
    rival_a, rival_b = new["traces"][1], old["traces"][1]
    assert len(a) == len(b) == len(rival_a) == len(rival_b) == 719
    assert all(x["action"] == y["action"] for x, y in zip(rival_a, rival_b))
    comparisons = [action_diff(x["action"], y["action"]) for x, y in zip(a, b)]
    first_steps = {
        key: next((i for i, row in enumerate(comparisons) if row[key]), None)
        for key in comparisons[0]
    }
    action_counts = {key: sum(row[key] for row in comparisons) for key in comparisons[0]}
    first_cash = next((i for i in range(719) if cash(a[i], 0) != cash(b[i], 0)
                       or cash(a[i], 1) != cash(b[i], 1)), None)
    first_prices = next((i for i in range(719) if a[i]["observation"]["market"]
                         != b[i]["observation"]["market"]), None)
    first_shops = next((i for i in range(719) if a[i]["observation"]["town"]
                        != b[i]["observation"]["town"]), None)
    checkpoints = []
    for i in [0, 1, 2, 144, 170, 171, 216, 252, 288, 360, 432, 504, 576, 648, 718]:
        na, nb = cash(a[i], 0), cash(a[i], 1)
        oa, ob = cash(b[i], 0), cash(b[i], 1)
        checkpoints.append({"step": i, "day": a[i]["observation"]["day"],
                            "hour": a[i]["observation"]["hour"],
                            "new_own": na, "old_own": oa, "delta_own": na - oa,
                            "new_rival": nb, "old_rival": ob, "delta_rival": nb - ob,
                            "delta_margin": (na - nb) - (oa - ob)})
    end = {"step": 719, "new_own": new["candidate_reward"],
           "old_own": old["candidate_reward"], "delta_own": new["candidate_reward"] - old["candidate_reward"],
           "new_rival": new["opponent_reward"], "old_rival": old["opponent_reward"],
           "delta_rival": new["opponent_reward"] - old["opponent_reward"],
           "delta_margin": new["margin"] - old["margin"]}
    checkpoints.append(end)
    changes = []
    for i in range(719):
        pre = (cash(a[i], 0) - cash(a[i], 1)) - (cash(b[i], 0) - cash(b[i], 1))
        if i < 718:
            post = (cash(a[i+1], 0) - cash(a[i+1], 1)) - (cash(b[i+1], 0) - cash(b[i+1], 1))
        else:
            post = end["delta_margin"]
        change = post - pre
        if change:
            changes.append({"step": i, "day": a[i]["observation"]["day"],
                            "hour": a[i]["observation"]["hour"], "delta_margin_change": change,
                            "new_action": a[i]["action"], "old_action": b[i]["action"],
                            "rival_action": rival_a[i]["action"],
                            "new_transition": a[i]["transition"], "old_transition": b[i]["transition"]})
    out = {
        "source_episode_id": 114255901, "seed": 383655650, "candidate_seat": 0,
        "first_action_divergence": first_steps,
        "action_divergence_counts": action_counts,
        "first_realized_cash_divergence_pre_step": first_cash,
        "first_market_state_divergence_pre_step": first_prices,
        "first_shop_divergence_pre_step": first_shops,
        "first_action_detail": {str(i): {
            "new_action": a[i]["action"], "old_action": b[i]["action"],
            "new_transition": a[i]["transition"], "old_transition": b[i]["transition"],
        } for i in sorted(set(v for v in first_steps.values() if v is not None) | {170, 171})},
        "checkpoints": checkpoints,
        "largest_negative_margin_turns": sorted(changes, key=lambda x: x["delta_margin_change"])[:12],
        "largest_positive_margin_turns": sorted(changes, key=lambda x: -x["delta_margin_change"])[:12],
        "nonzero_margin_change_turns": len(changes),
    }
    (HERE / "yizhou_mechanism.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps({k:v for k,v in out.items() if k not in ("largest_negative_margin_turns", "largest_positive_margin_turns", "first_action_detail")}, indent=2))
