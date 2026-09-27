"""Second independent 16-seed native block for the same frozen candidate."""

from pathlib import Path
import reactive_mirror_straw24_fresh as screen

screen.SEEDS = tuple(range(2611800, 2611816))
screen.OUTPUT = Path(__file__).with_name("reactive_mirror_straw24_fresh2.json")

if __name__ == "__main__":
    screen.main()
