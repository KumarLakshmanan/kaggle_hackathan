"""Both-seat Kaggle file-loader parity for the isolated candidate."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "physical_sale_predictor_20260927"))
import file_parity as check  # noqa: E402

check.CANDIDATE = ROOT / "exp_wool_delivery_interrupt_20260927.py"
check.OUTPUT = HERE / "file_parity_seed0.json"
check.EXPECTED_LOADED = "kaggle_wool_delivery_entrypoint"


if __name__ == "__main__":
    check.main()
