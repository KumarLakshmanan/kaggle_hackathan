"""Embed decision-aligned coefficients without modifying the first pilot."""

from pathlib import Path

import build_candidate

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
build_candidate.MODEL_PATH = HERE / "model_result_corrected.json"
build_candidate.TARGET = ROOT / "exp_physical_milk_sale_corrected_20260927.py"


if __name__ == "__main__":
    build_candidate.main()
