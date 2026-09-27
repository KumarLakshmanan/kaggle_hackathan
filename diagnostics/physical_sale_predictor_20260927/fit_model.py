"""One frozen L2 logistic fit: old 100 episodes, new 17-episode holdout."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.multigood_sale_race_20260927 import fit_model as prior  # noqa: E402

INPUT = HERE / "physical_opportunities.json"
OUTPUT = HERE / "model_result.json"
PREDICTIONS = HERE / "holdout_predictions.json"
PHYSICAL = (
    "rival_ready_units", "rival_ready_tiles",
    "rival_worker_on_ready_units", "rival_worker_min_ready_distance",
    "rival_workers_on_item_tiles", "rival_workers_near_shed",
    "rival_shed_min_ready_distance",
)
NUMERIC = (*prior.NUMERIC, *PHYSICAL)


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf8"))
    assert payload["summary"]["data_gate"]
    rows = payload["rows"]
    train = np.array([bool(row["train"]) for row in rows])
    train_ids = {int(row["episode_id"]) for row in rows if row["train"]}
    holdout_ids = {int(row["episode_id"]) for row in rows if not row["train"]}
    assert not train_ids & holdout_ids and len(train_ids) == 100 and len(holdout_ids) == 17
    y = np.array([int(row["rival_before_own"]) for row in rows], dtype=float)
    raw = np.array([[float(row["features"][feature]) for feature in NUMERIC]
                    for row in rows], dtype=float)
    center = raw[train].mean(axis=0)
    scale = raw[train].std(axis=0)
    scale[scale < 1e-10] = 1.0
    numeric = np.clip((raw - center) / scale, -5.0, 5.0)
    item = np.zeros((len(rows), len(prior.PRODUCTS)), dtype=float)
    for index, row in enumerate(rows):
        item[index, prior.PRODUCTS.index(row["features"]["item"])] = 1.0
    X = np.c_[np.ones(len(rows)), numeric, item]
    Xtrain, ytrain = X[train], y[train]
    weights = np.zeros(X.shape[1], dtype=float)
    first = np.zeros_like(weights)
    second = np.zeros_like(weights)
    for step in range(1, prior.STEPS + 1):
        z = np.clip(Xtrain @ weights, -30, 30)
        probability = 1 / (1 + np.exp(-z))
        gradient = Xtrain.T @ (probability - ytrain) / len(ytrain)
        gradient[1:] += prior.RIDGE * weights[1:]
        first = 0.9 * first + 0.1 * gradient
        second = 0.999 * second + 0.001 * gradient * gradient
        weights -= prior.LEARNING_RATE * (first / (1 - 0.9 ** step)) / (
            np.sqrt(second / (1 - 0.999 ** step)) + 1e-8)
    probability = 1 / (1 + np.exp(-np.clip(X @ weights, -30, 30)))
    validation = prior.metrics(y[~train], probability[~train])
    passes = bool(validation["auc"] >= 0.70 and validation["top_quartile_lift"] >= 1.4)
    result = {
        "method": "development-only physical-feature L2 logistic regression",
        "numeric_features": NUMERIC, "products": prior.PRODUCTS,
        "ridge": prior.RIDGE, "steps": prior.STEPS,
        "learning_rate": prior.LEARNING_RATE,
        "development_episodes": len(train_ids), "holdout_episodes": len(holdout_ids),
        "center": center.tolist(), "scale": scale.tolist(),
        "weights": weights.tolist(),
        "development": prior.metrics(y[train], probability[train]),
        "holdout": validation, "passes_predictive_gate": passes,
    }
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf8")
    predictions = [
        {"episode_id": row["episode_id"], "step": row["step"],
         "item": row["features"]["item"], "label": row["rival_before_own"],
         "probability": float(p)}
        for row, p in zip(rows, probability) if not row["train"]
    ]
    PREDICTIONS.write_text(json.dumps(predictions, indent=2), encoding="utf8")
    print(json.dumps({"development": result["development"], "holdout": validation,
                      "passes_predictive_gate": passes}, indent=2), flush=True)


if __name__ == "__main__":
    main()
