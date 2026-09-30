"""Training-only static exposure/price-impact check for policy design."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import main  # noqa: E402


def main_diagnostic() -> None:
    model = json.loads((HERE / "model_result.json").read_text(encoding="utf8"))
    rows = json.loads((HERE / "physical_opportunities.json").read_text(encoding="utf8"))["rows"]
    means, scales, weights = (np.array(model[k]) for k in ("center", "scale", "weights"))
    result = Counter()
    for row in rows:
        if not row["train"]:
            continue
        f = row["features"]
        if f["item"] not in ("EGG", "MILK"):
            continue
        x = np.clip((np.array([f[k] for k in model["numeric_features"]]) - means) / scales, -5, 5)
        z = weights[0] + x @ weights[1:1+len(x)]
        z += weights[1+len(x)+model["products"].index(f["item"])]
        p = float(1 / (1 + np.exp(-np.clip(z, -30, 30))))
        if p < 0.3 or f["rival_ready_units"] < 3:
            continue
        item = f["item"]
        quantity = min(8, f["stock"])
        level = int(f["market_inventory"])
        batch = min(10, int(f["rival_ready_units"]))
        drop = sum(main._r37_market_price(item, level + j)
                   - main._r37_market_price(item, level + batch + j)
                   for j in range(quantity))
        result[(item, "all")] += 1
        result[(item, "positive")] += row["rival_before_own"]
        for floor in (0, 4, 8, 16, 24):
            if drop >= floor:
                result[(item, f"drop_ge_{floor}")] += 1
                result[(item, f"drop_ge_{floor}_positive")] += row["rival_before_own"]
    print(dict(sorted((f"{item}_{key}", value) for (item, key), value in result.items())))


if __name__ == "__main__":
    main_diagnostic()
