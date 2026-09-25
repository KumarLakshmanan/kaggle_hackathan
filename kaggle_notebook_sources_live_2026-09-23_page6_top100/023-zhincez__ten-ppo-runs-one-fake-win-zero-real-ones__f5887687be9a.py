# Before: a constant that was true when it was written
NEUTRAL = 2

# After: derived from the grid, so it cannot drift out of sync when the grid changes
import numpy as np

LEVELS = np.array([0.80, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20, 1.40])
NEUTRAL = int((LEVELS == 1.0).argmax())
assert LEVELS[NEUTRAL] == 1.0, "no neutral action in the grid"

print(f"neutral index = {NEUTRAL}, multiplier = {LEVELS[NEUTRAL]}")

# The general check: any index into a table that encodes a MEANING should be derived from the
# table, and asserted. A hard-coded index is correct until someone edits the table, and then it
# is silently wrong in a direction that flatters whichever side it handicaps.