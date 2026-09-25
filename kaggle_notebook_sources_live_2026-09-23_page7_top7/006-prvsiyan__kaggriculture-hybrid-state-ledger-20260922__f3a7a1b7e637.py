import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use("seaborn-v0_8-whitegrid")
RNG = np.random.default_rng(20260922)

BASE_PRICE = {
    "WHEAT": 30.0, "CARROT": 45.0, "TOMATO": 60.0,
    "STRAWBERRY": 90.0, "MELON": 150.0,
    "EGG": 50.0, "MILK": 80.0, "WOOL": 100.0, "FERTILIZER": 40.0,
}
SELLABLE = tuple(BASE_PRICE)


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def visible_state_features(obs):
    market = _get(obs, "market", {}) or {}
    prices = _get(market, "prices", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    private = _get(obs, "private", {}) or {}
    money = float(_get(private, "money", _get(obs, "money", 0)) or 0)
    turn = int(_get(obs, "step", 0) or 0)
    rows = []
    for item in SELLABLE:
        quote = float(_get(prices, item, BASE_PRICE[item]) or BASE_PRICE[item])
        stock = int(_get(inventory, item, 0) or 0)
        gap = quote / BASE_PRICE[item] - 1.0
        rows.append((item, quote, stock, gap))
    quotes = pd.DataFrame(rows, columns=["item", "price", "inventory", "gap"])
    pressure = float((quotes["inventory"] / 10000.0).clip(0, 2).mean())
    best_gap = float(quotes["gap"].max())
    return {
        "turn": turn, "money": money, "inventory_pressure": pressure,
        "best_gap": best_gap, "quotes": quotes,
    }


def classify_regime(features, episode_steps=720):
    turn = features["turn"]
    if turn >= episode_steps - 48:
        return "liquidate"
    if features["money"] < 90 or features["inventory_pressure"] > 0.82:
        return "cash_conserve"
    if features["best_gap"] >= 0.12 and features["inventory_pressure"] < 0.62:
        return "premium_sell"
    if turn < 96:
        return "opening"
    return "grow"


def ledger_action_card(features, episode_steps=720, reserve=2):
    regime = classify_regime(features, episode_steps)
    q = features["quotes"].copy()
    orders = []
    if regime in {"premium_sell", "liquidate"}:
        q["score"] = q["gap"] * q["inventory"]
        if regime == "liquidate":
            candidates = q.sort_values(["inventory", "gap"], ascending=False)
        else:
            candidates = q[q["gap"] > 0.05].sort_values("score", ascending=False)
        for row in candidates.itertuples():
            qty = max(0, int(row.inventory) - (0 if regime == "liquidate" else reserve))
            if qty:
                orders.append(["SELL", row.item, min(qty, 12)])
    elif regime == "opening":
        orders = [["BUY_SEED", "WHEAT", 2], ["BUY_SEED", "MELON", 1]]
    elif regime == "grow":
        best = q.sort_values("gap", ascending=False).iloc[0]
        orders = [["BUY_SEED", str(best.item), 1]]
    else:  # cash_conserve
        orders = []
    return {"regime": regime, "market": orders[:10], "farmer": ["PASS"], "hands": []}


example_obs = {
    "step": 504, "private": {"money": 420},
    "market": {
        "prices": {"WHEAT": 42, "MELON": 188, "STRAWBERRY": 86},
        "inventory": {"WHEAT": 18, "MELON": 1, "STRAWBERRY": 4},
    },
}
example_features = visible_state_features(example_obs)
ledger_action_card(example_features)


def synthetic_state(game, turn):
    phase = turn / 720.0
    prices = {item: BASE_PRICE[item] * (1 + RNG.normal(0, 0.13)) for item in SELLABLE}
    inventory = {item: int(max(0, RNG.normal(5 + 15 * phase, 4))) for item in SELLABLE}
    return {
        "step": turn, "private": {"money": float(max(20, RNG.normal(420 - 230 * phase, 70)))},
        "market": {"prices": prices, "inventory": inventory},
    }

rows = []
for game in range(48):
    for turn in range(0, 720, 24):
        obs = synthetic_state(game, turn)
        f = visible_state_features(obs)
        regime = classify_regime(f)
        quote_signal = 100 * f["best_gap"]
        pressure_signal = 35 * f["inventory_pressure"]
        baseline_proxy = 1.8 * quote_signal - pressure_signal + RNG.normal(0, 8)
        switch_bonus = {"premium_sell": 24, "liquidate": 18, "cash_conserve": 8}.get(regime, 0)
        ledger_proxy = baseline_proxy + switch_bonus + RNG.normal(0, 3)
        rows.append({"game": game, "turn": turn, "phase": turn // 24, "regime": regime,
                     "baseline_proxy": baseline_proxy, "ledger_proxy": ledger_proxy})

proxy = pd.DataFrame(rows)
summary = pd.DataFrame({
    "mean_proxy": proxy[["baseline_proxy", "ledger_proxy"]].mean(),
    "median_proxy": proxy[["baseline_proxy", "ledger_proxy"]].median(),
})
summary["delta_vs_baseline"] = summary["mean_proxy"] - summary.loc["baseline_proxy", "mean_proxy"]
summary


fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
phase_means = proxy.groupby("phase")[["baseline_proxy", "ledger_proxy"]].mean()
phase_means.plot(ax=axes[0], color=["#94a3b8", "#16a34a"], linewidth=2)
axes[0].set_title("Proxy utility by visible turn")
axes[0].set_xlabel("Turn / 24")
axes[0].set_ylabel("Proxy utility")
axes[0].legend(["fixed schedule", "ledger switch"], frameon=False)

box = proxy.melt(id_vars=["game", "turn"], value_vars=["baseline_proxy", "ledger_proxy"],
                 var_name="policy", value_name="proxy utility")
box["policy"] = box["policy"].map({"baseline_proxy": "fixed schedule", "ledger_proxy": "ledger switch"})
box.boxplot(column="proxy utility", by="policy", ax=axes[1], grid=False)
axes[1].set_title("Distribution over visible states")
axes[1].set_xlabel("")
fig.suptitle("")
fig.tight_layout()
plt.show()


def agent_skeleton(obs, configuration=None):
    """Visible-state skeleton: add a tested farm route around this ledger."""
    features = visible_state_features(obs)
    card = ledger_action_card(features, episode_steps=int(_get(configuration or {}, "episodeSteps", 720) or 720))
    # Keep the returned shape valid while the farmer/hand route is developed.
    return {"farmer": card["farmer"], "hands": card["hands"], "market": card["market"]}

print("Example regime:", example_features and classify_regime(example_features))
print("Example action card:", ledger_action_card(example_features))
print("Rows in proxy A/B test:", len(proxy))
