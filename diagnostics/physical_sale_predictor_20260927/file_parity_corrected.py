"""Both-seat Kaggle loader parity for decision-aligned source."""

from pathlib import Path

import file_parity

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
file_parity.CANDIDATE = ROOT / "exp_physical_milk_sale_corrected_20260927.py"
file_parity.OUTPUT = HERE / "file_parity_corrected_seed0.json"


if __name__ == "__main__":
    file_parity.main()
