"""Fresh native block for the corrected, decision-aligned candidate."""

from pathlib import Path

import reactive_dev16

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
reactive_dev16.CANDIDATE = ROOT / "exp_physical_milk_sale_corrected_20260927.py"
reactive_dev16.CANDIDATE_HASH = "9d415fb73274fc9b6fe86ecf943b3c32961f4c158e06346e5d557d3e32d70960"
reactive_dev16.SEEDS = tuple(range(2624000, 2624016))
reactive_dev16.OUTPUT = HERE / "reactive_corrected_dev16.json"


if __name__ == "__main__":
    reactive_dev16.main()
