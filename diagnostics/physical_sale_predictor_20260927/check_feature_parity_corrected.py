"""Compare corrected decision-time features with the rebuilt candidate."""

from pathlib import Path

import check_feature_parity

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
check_feature_parity.CANDIDATE = ROOT / "exp_physical_milk_sale_corrected_20260927.py"
check_feature_parity.DATA = HERE / "physical_opportunities_corrected.json"
check_feature_parity.ACTION_OFFSET = 1


if __name__ == "__main__":
    check_feature_parity.main()
