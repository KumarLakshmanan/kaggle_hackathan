"""Frozen development-only logistic fit for the sale-race data gate."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
INPUT = HERE / "opportunities.json"
OUTPUT = HERE / "model_result.json"
PREDICTIONS = HERE / "holdout_predictions.json"
NUMERIC = (
    "step", "hour", "stock", "quote", "market_inventory",
    "quote_delta_1", "quote_delta_4", "inventory_delta_1",
    "inventory_delta_4", "since_own_sale", "own_producers",
    "rival_producers", "own_money_delta_4", "rival_money_delta_4",
    "physical_match_fraction", "market_order_count",
)
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
RIDGE = 0.01
STEPS = 1000
LEARNING_RATE = 0.05


def auc(y: np.ndarray, p: np.ndarray) -> float:
    pos = int(y.sum())
    neg = len(y) - pos
    if pos == 0 or neg == 0:
        return float("nan")
    order = np.argsort(p, kind="stable")
    rank = np.empty(len(y), dtype=float)
    rank[order] = np.arange(1, len(y) + 1)
    # Scores are continuous; exact ties are grouped to make the metric robust.
    ordered = p[order]
    starts = np.flatnonzero(np.r_[True, ordered[1:] != ordered[:-1]])
    ends = np.r_[starts[1:], len(ordered)]
    for start, end in zip(starts, ends):
        if end - start > 1:
            rank[order[start:end]] = (start + 1 + end) / 2
    return float((rank[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    size = len(y)
    top = max(1, math.ceil(size / 4))
    chosen = np.argsort(-p, kind="stable")[:top]
    prevalence = float(y.mean())
    precision = float(y[chosen].mean())
    return {
        "n": size, "positives": int(y.sum()), "prevalence": prevalence,
        "auc": auc(y, p), "top_quartile_n": top,
        "top_quartile_positives": int(y[chosen].sum()),
        "top_quartile_precision": precision,
        "top_quartile_lift": precision / prevalence if prevalence else None,
        "mean_predicted_probability": float(p.mean()),
    }


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf8"))
    assert payload["summary"]["data_gate"]
    rows = payload["rows"]
    train = np.array([bool(row["train"]) for row in rows])
    dev_ids = {row["episode_id"] for row in rows if row["train"]}
    hold_ids = {row["episode_id"] for row in rows if not row["train"]}
    assert not dev_ids & hold_ids and len(dev_ids) == 39 and len(hold_ids) == 61
    y = np.array([int(row["rival_before_own"]) for row in rows], dtype=float)
    raw = np.array([[float(row["features"][key]) for key in NUMERIC]
                    for row in rows], dtype=float)
    center = raw[train].mean(axis=0)
    scale = raw[train].std(axis=0)
    scale[scale < 1e-10] = 1.0
    numeric = np.clip((raw - center) / scale, -5.0, 5.0)
    item = np.zeros((len(rows), len(PRODUCTS)), dtype=float)
    for i, row in enumerate(rows):
        item[i, PRODUCTS.index(row["features"]["item"])] = 1.0
    X = np.c_[np.ones(len(rows)), numeric, item]
    Xdev, ydev = X[train], y[train]
    weight = np.zeros(X.shape[1], dtype=float)
    first = np.zeros_like(weight)
    second = np.zeros_like(weight)
    for step in range(1, STEPS + 1):
        z = np.clip(Xdev @ weight, -30, 30)
        probability = 1 / (1 + np.exp(-z))
        gradient = Xdev.T @ (probability - ydev) / len(ydev)
        gradient[1:] += RIDGE * weight[1:]
        first = 0.9 * first + 0.1 * gradient
        second = 0.999 * second + 0.001 * gradient * gradient
        first_hat = first / (1 - 0.9 ** step)
        second_hat = second / (1 - 0.999 ** step)
        weight -= LEARNING_RATE * first_hat / (np.sqrt(second_hat) + 1e-8)
    probability = 1 / (1 + np.exp(-np.clip(X @ weight, -30, 30)))
    validation = metrics(y[~train], probability[~train])
    decision = bool(validation["auc"] >= 0.70 and
                    validation["top_quartile_lift"] >= 1.4)
    result = {
        "method": "development-only standardized L2 logistic regression",
        "numeric_features": NUMERIC, "products": PRODUCTS,
        "ridge": RIDGE, "steps": STEPS, "learning_rate": LEARNING_RATE,
        "train_episodes": len(dev_ids), "holdout_episodes": len(hold_ids),
        "center": center.tolist(), "scale": scale.tolist(),
        "weights": weight.tolist(),
        "train": metrics(y[train], probability[train]),
        "holdout": validation,
        "passes_predictive_gate": decision,
    }
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf8")
    predictions = [
        {"episode_id": row["episode_id"], "step": row["step"],
         "item": row["features"]["item"], "label": row["rival_before_own"],
         "probability": float(p)}
        for row, p in zip(rows, probability) if not row["train"]
    ]
    PREDICTIONS.write_text(json.dumps(predictions, indent=2), encoding="utf8")
    print(json.dumps({"train": result["train"], "holdout": validation,
                      "passes_predictive_gate": decision}, indent=2))


if __name__ == "__main__":
    main()
