"""Refit frozen model family on decision-aligned replay frames."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_sale_predictor_20260927 import fit_model  # noqa: E402

fit_model.INPUT = HERE / "physical_opportunities_corrected.json"
fit_model.OUTPUT = HERE / "model_result_corrected.json"
fit_model.PREDICTIONS = HERE / "holdout_predictions_corrected.json"


if __name__ == "__main__":
    fit_model.main()
