"""Native two-seat mechanism smoke for the half-base quote variant."""

from pathlib import Path
import smoke_latched as smoke


smoke.CANDIDATE = smoke.ROOT / "exp_mirror_stock_frontload_halfbase_20260927.py"
smoke.CANDIDATE_HASH = "e9517daebe5523879c5096839570af04619135fc7f5a7fb7e6446ab1c367ca68"
smoke.OUTPUT = Path(__file__).resolve().with_name("smoke_halfbase.json")


if __name__ == "__main__":
    smoke.main()
