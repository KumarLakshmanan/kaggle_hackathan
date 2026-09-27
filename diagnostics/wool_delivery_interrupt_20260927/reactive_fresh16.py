"""Frozen fresh native block for the isolated wool delivery interrupt."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "physical_sale_predictor_20260927"))
import reactive_dev16 as bench  # noqa: E402

bench.CANDIDATE = ROOT / "exp_wool_delivery_interrupt_20260927.py"
bench.CANDIDATE_HASH = "33b630564791fe4ee274d8f88e090b138abaf7d82ed1439d02355b211fca4779"
bench.SEEDS = tuple(range(2625000, 2625016))
bench.OUTPUT = HERE / "reactive_fresh16.json"


if __name__ == "__main__":
    bench.main()
