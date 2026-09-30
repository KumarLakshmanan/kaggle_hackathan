"""Embed frozen learned coefficients into a single-file isolated agent."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "main.py"
TARGET = ROOT / "exp_physical_milk_sale_20260927.py"
MODEL_PATH = HERE / "model_result.json"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"


def main() -> None:
    source = SOURCE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == EXPECTED
    model = json.loads(MODEL_PATH.read_text(encoding="utf8"))
    assert model["passes_predictive_gate"]
    public_model = {key: model[key] for key in
                    ("numeric_features", "products", "center", "scale", "weights")}
    tail = (HERE / "milk_tail.py").read_text(encoding="utf8")
    assert tail.count("__EMBEDDED_MODEL__") == 1
    tail = tail.replace("__EMBEDDED_MODEL__", repr(public_model))
    marker = "\n# Kaggle's file loader selects the last newly inserted callable in source"
    text = source.decode("utf8")
    assert text.count(marker) == 1
    # Preserve the source's original line endings; Windows text-mode writes
    # can double CR before LF and break backslash continuations in main.py.
    TARGET.write_bytes(text.replace(marker, "\n" + tail + marker).encode("utf8"))
    print(json.dumps({"main_sha256": EXPECTED,
                      "model_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
                      "candidate_sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(),
                      "path": str(TARGET)}, indent=2))


if __name__ == "__main__":
    main()
