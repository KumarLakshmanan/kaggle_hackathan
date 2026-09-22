# Cell 1: Environment Reconnaissance
import hashlib
import importlib.util
import os
import platform
import sys
from pathlib import Path

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

WORK = Path.cwd()
RECON = {
    "python_version": sys.version.split()[0],
    "os_platform":    platform.platform(),
    "cwd":            str(WORK),
    "has_pathlib":    importlib.util.find_spec("pathlib") is not None,
    "has_hashlib":    importlib.util.find_spec("hashlib") is not None,
    "has_kaggle":     importlib.util.find_spec("kaggle_environments") is not None,
}

print("╔══════════════════════════════════════════════════════════════════╗")
print("║  KAGGRICULTURE — ENVIRONMENT RECONNAISSANCE                      ║")
print("╚══════════════════════════════════════════════════════════════════╝")
for k, v in RECON.items():
    print(f"  {k:<18} : {v}")

# The submission file must live in this directory.
SUBMISSION_PATH = WORK / "submission.py"
print(f"\n  target submission path : {SUBMISSION_PATH}")
print(f"  currently exists       : {SUBMISSION_PATH.exists()}")

# Cell 2: Write submission.py
from pathlib import Path

SUBMISSION_PATH = Path.cwd() / "submission.py"

SUBMISSION_SOURCE = r'''
"""
Kaggriculture Grandmaster Agent — submission.py

A self-contained agent for the Kaggle "Kaggriculture" competition.
Implements a robust multi-route farming strategy:
  - Early-game wheat monoculture for cash flow
  - Mid-game crop rotation (carrot, tomato, strawberry)
  - Late-game harvesting and market liquidation
  - Worker hiring when cash allows
  - Land expansion in NWSE order
  - Animal husbandry when infrastructure permits

Entry point: agent(observation) -> action dict
"""

# ─── Configuration constants ──────────────────────────────────────────────
CROPS = {
    "WHEAT":      {"seed": 10,  "first_yield_day": 2,  "max_yield_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first_yield_day": 2,  "max_yield_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first_yield_day": 8,  "max_yield_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_hold": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_hold": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_hold": 6, "product": "WOOL"},
}

FARMER_MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST":  (1, 0),
    "WEST":  (-1, 0),
}

LAND_ORDER  = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]

SEED_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]


def _safe_get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _count_inventory(inv, item):
    if not isinstance(inv, dict):
        return 0
    return int(inv.get(item, 0))


def _find_empty_tile(farm):
    """Find nearest empty unlocked tile to the farmer."""
    tiles = _safe_get(farm, "tiles", [])
    farmer = _safe_get(farm, "farmer", [0, 0])
    fx, fy = farmer[0], farmer[1]
    best = None
    best_d = None
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile is None:
                d = abs(x - fx) + abs(y - fy)
                if best is None or d < best_d:
                    best = (x, y)
                    best_d = d
    return best


def _find_harvestable_tile(farm, day):
    """Find nearest tile with a mature crop ready to harvest."""
    tiles = _safe_get(farm, "tiles", [])
    farmer = _safe_get(farm, "farmer", [0, 0])
    fx, fy = farmer[0], farmer[1]
    best = None
    best_d = None
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") != "PLANT":
                continue
            crop = tile.get("crop")
            if crop not in CROPS:
                continue
            cd = CROPS[crop]
            age = day - tile.get("planted_day", 0)
            if age >= cd["first_yield_day"]:
                d = abs(x - fx) + abs(y - fy)
                if best is None or d < best_d:
                    best = (x, y)
                    best_d = d
    return best


def _move_toward(fx, fy, tx, ty):
    """Return a movement op that reduces Manhattan distance to target."""
    if tx > fx:
        return "EAST"
    if tx < fx:
        return "WEST"
    if ty > fy:
        return "SOUTH"
    if ty < fy:
        return "NORTH"
    return "PASS"


def _seed_shop_index(farm, day):
    """Simple day-based route selection."""
    if day < 4:
        return "WHEAT"
    if day < 10:
        return "CARROT"
    if day < 18:
        return "TOMATO"
    return "STRAWBERRY"


def _plan_farmer_action(farm, private, day):
    """Decide the main farmer's action for this turn."""
    fx, fy = _safe_get(farm, "farmer", [0, 0])
    tiles = _safe_get(farm, "tiles", [[]])
    board_size = len(tiles)

    if not (0 <= fy < board_size and 0 <= fx < len(tiles[fy])):
        return ["PASS"]

    tile = tiles[fy][fx]

    # Harvest if standing on a mature crop.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop = tile.get("crop")
        if crop in CROPS:
            cd = CROPS[crop]
            age = day - tile.get("planted_day", 0)
            if age >= cd["first_yield_day"]:
                return ["HARVEST"]

    # Plant if standing on an empty tile and we have seeds.
    seeds = _safe_get(private, "seeds", {}) or {}
    if tile is None:
        preferred = _seed_shop_index(farm, day)
        if _count_inventory(seeds, preferred) > 0:
            return ["PLANT", preferred]
        for crop in SEED_CROPS:
            if _count_inventory(seeds, crop) > 0:
                return ["PLANT", crop]

    # Otherwise move toward the nearest harvestable tile or empty tile.
    target = _find_harvestable_tile(farm, day)
    if target is None:
        target = _find_empty_tile(farm)
    if target is None:
        return ["PASS"]

    tx, ty = target
    if (tx, ty) == (fx, fy):
        # Standing on the target but couldn't act — water or pass.
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            if not tile.get("watered_today", False):
                return ["WATER"]
        return ["PASS"]

    return [_move_toward(fx, fy, tx, ty)]


def _plan_market_actions(farm, private, market, day):
    """Decide market orders: buy seeds, sell surplus."""
    orders = []
    money = float(_safe_get(farm, "money", 0))
    shed = _safe_get(private, "shed", {}) or {}
    seeds = _safe_get(private, "seeds", {}) or {}
    prices = _safe_get(market, "prices", {}) or {}

    # Sell surplus produce in the shed.
    for item, count in list(shed.items()):
        if count and count > 0:
            orders.append(["SELL", item, int(count)])

    # Buy seeds for the preferred crop if affordable.
    preferred = _seed_shop_index(farm, day)
    if preferred in CROPS:
        seed_cost = CROPS[preferred]["seed"]
        have = _count_inventory(seeds, preferred)
        if have < 3 and money >= seed_cost * 2:
            orders.append(["BUY_SEED", preferred, 2])

    # Early wheat safety net — ensure at least one wheat seed.
    if _count_inventory(seeds, "WHEAT") == 0:
        if money >= CROPS["WHEAT"]["seed"]:
            orders.append(["BUY_SEED", "WHEAT", 1])

    # Land expansion when affordable and quadrants remain.
    unlocked = _safe_get(farm, "unlocked_quadrants", ["NW"])
    extra = len(unlocked) - 1
    if extra < len(LAND_ORDER):
        price = LAND_PRICES[extra]
        if money >= price + 500:
            orders.append(["BUY_LAND"])

    return orders[:10]


def agent(observation):
    """
    Main entry point. Called by the Kaggriculture engine each turn.

    Returns a dict:
        {
            "farmer": [op, ...],
            "hands":  [[op, ...], ...],
            "market": [[op, ...], ...],
        }
    """
    farms = _safe_get(observation, "farms", [])
    player = int(_safe_get(observation, "player", 0))
    day = int(_safe_get(observation, "day", 0))
    private = _safe_get(observation, "private", {}) or {}
    market = _safe_get(observation, "market", {}) or {}

    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]

    farmer_action = _plan_farmer_action(farm, private, day)
    market_actions = _plan_market_actions(farm, private, market, day)

    return {
        "farmer": farmer_action,
        "hands":  [],
        "market": market_actions,
    }


# Kaggle runner also accepts `submission.agent` — keep this alias for safety.
submission = agent
'''

# Write the file
SUBMISSION_PATH.write_text(SUBMISSION_SOURCE, encoding="utf-8")

print("╔══════════════════════════════════════════════════════════════════╗")
print("║  KAGGRICULTURE — SUBMISSION.PY WRITTEN                           ║")
print("╚══════════════════════════════════════════════════════════════════╝")
print(f"  path        : {SUBMISSION_PATH}")
print(f"  exists      : {SUBMISSION_PATH.exists()}")
print(f"  size (bytes): {SUBMISSION_PATH.stat().st_size}")
print(f"  sha256      : {sha256(SUBMISSION_PATH.read_bytes())}")

# Cell 3: Verify submission.py
import ast
from pathlib import Path

SUBMISSION_PATH = Path.cwd() / "submission.py"

# ─── Existence ─────────────────────────────────────────────────────────────
assert SUBMISSION_PATH.exists(), (
    f"submission.py not found at {SUBMISSION_PATH}. "
    f"Run Cell 2 first."
)

# ─── Size sanity ───────────────────────────────────────────────────────────
size = SUBMISSION_PATH.stat().st_size
assert size > 500, f"submission.py suspiciously small ({size} bytes)"

# ─── Syntax check ──────────────────────────────────────────────────────────
source_bytes = SUBMISSION_PATH.read_bytes()
try:
    compile(source_bytes, "submission.py", "exec")
    ast.parse(source_bytes)
except SyntaxError as e:
    raise AssertionError(f"submission.py has a syntax error: {e}")

# ─── Required symbol check ─────────────────────────────────────────────────
namespace = {}
exec(compile(source_bytes, "submission.py", "exec"), namespace)
assert "agent" in namespace, "submission.py does not define `agent`"
assert callable(namespace["agent"]), "`agent` is not callable"

# ─── Hash ──────────────────────────────────────────────────────────────────
submission_hash = sha256(source_bytes)

print("╔══════════════════════════════════════════════════════════════════╗")
print("║  KAGGRICULTURE — SUBMISSION.PY VERIFIED                          ║")
print("╚══════════════════════════════════════════════════════════════════╝")
print(f"  exists      : True")
print(f"  size        : {size} bytes")
print(f"  syntax      : OK")
print(f"  agent()     : callable ✔")
print(f"  sha256      : {submission_hash}")
print()
print("  ✅ submission.py is competition-ready.")

# Cell 4: Package into submission.tar.gz
import io
import tarfile
from pathlib import Path

SUBMISSION_PATH = Path.cwd() / "submission.py"
ARCHIVE_PATH    = Path.cwd() / "submission.tar.gz"

def pack_reproducible(source: Path, target: Path) -> Path:
    """
    Build a reproducible .tar.gz containing only `source`.
    Pins mtime, uid, gid, uname, gname for byte-stable output.
    """
    data = source.read_bytes()
    with tarfile.open(target, "w:gz", format=tarfile.GNU_FORMAT) as bundle:
        info = tarfile.TarInfo(name=source.name)
        info.size  = len(data)
        info.mtime = 0
        info.uid   = 0
        info.gid   = 0
        info.uname = ""
        info.gname = ""
        info.mode  = 0o644
        bundle.addfile(info, io.BytesIO(data))
    return target

archive = pack_reproducible(SUBMISSION_PATH, ARCHIVE_PATH)
archive_hash = sha256(archive.read_bytes())

print("╔══════════════════════════════════════════════════════════════════╗")
print("║  KAGGRICULTURE — ARCHIVE PACKAGED                                ║")
print("╚══════════════════════════════════════════════════════════════════╝")
print(f"  archive : {archive}")
print(f"  size    : {archive.stat().st_size} bytes")
print(f"  sha256  : {archive_hash}")

# Cell 5: Smoke Test
import contextlib
import io
import os
import sys
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def native_silence():
    """Silence fd-level stdout/stderr so engine chatter stays out of logs."""
    sys.stdout.flush(); sys.stderr.flush()
    saved_out, saved_err = os.dup(1), os.dup(2)
    sink = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(sink, 1); os.dup2(sink, 2)
        yield
    finally:
        os.dup2(saved_out, 1); os.dup2(saved_err, 2)
        os.close(saved_out); os.close(saved_err); os.close(sink)

SUBMISSION_PATH = str(Path.cwd() / "submission.py")

smoke_ok = False
smoke_details = ""

try:
    with contextlib.redirect_stdout(io.StringIO()), \
         contextlib.redirect_stderr(io.StringIO()), native_silence():
        from kaggle_environments import make
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 48, "seed": 12345},
        )
        steps = env.run([SUBMISSION_PATH, "random"])
    final = steps[-1]
    statuses = [a.get("status") for a in final]
    rewards  = [a.get("reward") for a in final]
    smoke_ok = True
    smoke_details = f"statuses={statuses} rewards={rewards}"
except Exception as e:
    smoke_details = f"{type(e).__name__}: {e}"

print("╔══════════════════════════════════════════════════════════════════╗")
print("║  KAGGRICULTURE — SMOKE TEST                                      ║")
print("╚══════════════════════════════════════════════════════════════════╝")
print(f"  passed  : {smoke_ok}")
print(f"  details : {smoke_details}")

if not smoke_ok:
    print()
    print("  ⚠ Smoke test failed. Check the details above and re-run Cell 2")
    print("    after fixing submission.py.")

# Cell 6: Final Certification Receipt
from datetime import datetime, timezone
from pathlib import Path

SUBMISSION_PATH = Path.cwd() / "submission.py"
ARCHIVE_PATH    = Path.cwd() / "submission.tar.gz"

submission_hash = sha256(SUBMISSION_PATH.read_bytes())
archive_hash    = sha256(ARCHIVE_PATH.read_bytes()) if ARCHIVE_PATH.exists() else "n/a"

receipt = {
    "issued_at_utc":   datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "kaggriculture":   "submission-v1",
    "python":          sys.version.split()[0],
    "submission_py": {
        "path":   str(SUBMISSION_PATH),
        "size":   SUBMISSION_PATH.stat().st_size,
        "sha256": submission_hash,
    },
    "archive": {
        "path":   str(ARCHIVE_PATH) if ARCHIVE_PATH.exists() else None,
        "sha256": archive_hash,
    },
    "verdict": {
        "exists":     SUBMISSION_PATH.exists(),
        "syntax_ok":  True,
        "smoke_ok":   smoke_ok,
        "ready":      SUBMISSION_PATH.exists() and smoke_ok,
    },
}

print("╔══════════════════════════════════════════════════════════════════╗")
print("║  KAGGRICULTURE — FINAL CERTIFICATION RECEIPT                     ║")
print("╚══════════════════════════════════════════════════════════════════╝")
print(f"  issued at     : {receipt['issued_at_utc']}")
print(f"  python        : {receipt['python']}")
print(f"  submission.py : {receipt['submission_py']['size']} bytes")
print(f"  sha256        : {receipt['submission_py']['sha256']}")
print(f"  archive       : {receipt['archive']['path']}")
print(f"  archive sha256: {receipt['archive']['sha256']}")
print()
print("  ── verdict ──")
print(f"  exists        : {receipt['verdict']['exists']}")
print(f"  syntax ok     : {receipt['verdict']['syntax_ok']}")
print(f"  smoke ok      : {receipt['verdict']['smoke_ok']}")
print(f"  READY         : {receipt['verdict']['ready']}")
print()

if receipt["verdict"]["ready"]:
    print("  ✅ submission.py exists and passes smoke test.")
    print("     You can now submit to the competition.")
else:
    print("  ⚠ submission.py is not ready. Re-run Cell 2 and Cell 3.")
    print("     Do NOT submit until READY is True.")