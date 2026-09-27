"""Development-only probability audit for freezing an action threshold."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.multigood_sale_race_20260927 import fit_model as prior  # noqa: E402


def main() -> None:
    model = json.loads((HERE / "model_result.json").read_text(encoding="utf8"))
    rows = json.loads((HERE / "physical_opportunities.json").read_text(encoding="utf8"))["rows"]
    means = np.array(model["center"])
    scales = np.array(model["scale"])
    weights = np.array(model["weights"])
    groups = defaultdict(list)
    for row in rows:
        if not row["train"]:
            continue
        features = row["features"]
        vector = np.array([features[key] for key in model["numeric_features"]], dtype=float)
        vector = np.clip((vector - means) / scales, -5, 5)
        z = weights[0] + vector @ weights[1:1 + len(vector)]
        z += weights[1 + len(vector) + model["products"].index(features["item"])]
        probability = float(1 / (1 + np.exp(-np.clip(z, -30, 30))))
        groups[features["item"]].append((probability, int(row["rival_before_own"]),
                                          features["rival_ready_units"], row["episode_id"]))
    summary = {}
    for item, values in sorted(groups.items()):
        probs = np.array([v[0] for v in values])
        labels = np.array([v[1] for v in values])
        summary[item] = {
            "n": len(values), "positives": int(labels.sum()),
            "p75": float(np.quantile(probs, 0.75)),
            "p90": float(np.quantile(probs, 0.90)),
            "p_at_least_0_2": int((probs >= 0.2).sum()),
            "precision_at_least_0_2": float(labels[probs >= 0.2].mean()) if (probs >= 0.2).any() else None,
            "p_at_least_0_3": int((probs >= 0.3).sum()),
            "precision_at_least_0_3": float(labels[probs >= 0.3].mean()) if (probs >= 0.3).any() else None,
            "p_at_least_0_3_ready3": int(sum(v[0] >= 0.3 and v[2] >= 3 for v in values)),
            "precision_at_least_0_3_ready3": (
                sum(v[1] for v in values if v[0] >= 0.3 and v[2] >= 3)
                / max(1, sum(v[0] >= 0.3 and v[2] >= 3 for v in values))),
        }
    (HERE / "development_score_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
