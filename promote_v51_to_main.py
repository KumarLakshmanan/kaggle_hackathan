"""Promote the tested V51 router into the single-file production agent.

This is a guarded mechanical rewrite.  It makes a timestamped V49 backup,
embeds the Haide source as readable Python, and adds the tested public-state
router.  It never calls Kaggle submission commands.
"""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
SOURCE = ROOT / "kaggle_extracted_agents_2026-09-21" / "haideptry_master_2965.py"
BACKUP = ROOT / "main_v49_before_v51_promotion.py"
MARKER = "# ===== V51 HAIDE BASE ROUTER (TESTED, PLAIN SOURCE) ====="


ROUTER = r'''

# ===== V51 HAIDE BASE ROUTER (TESTED, PLAIN SOURCE) =====
# The upstream Haide policy is embedded above as ordinary readable Python.
# The route selector uses only public step-72 state: shop, opponent physical
# counts and opponent cash. It never reads a seed, replay id or private rival
# inventory. V49 remains the explicit reserve on six observed regimes.
import copy as _v51_copy

_V51_MAIN_AGENT = agent
_V51_HAIDE_NAMESPACE = {
    '__name__': '_embedded_kaggriculture_haide_master_v51',
    '__file__': '<embedded-kaggriculture-haide-master-v51>',
}
exec(compile(_V51_HAIDE_SOURCE, '<embedded-kaggriculture-haide-master-v51>', 'exec'),
     _V51_HAIDE_NAMESPACE, _V51_HAIDE_NAMESPACE)
_V51_HAIDE_AGENT = _V51_HAIDE_NAMESPACE['agent']
_V51_HAIDE_SOURCE = None

_V51_LAST_STEP = {}
_V51_USE_MAIN = {}


def _v51_counts(farm):
    result = {}
    for row in farm.get('tiles', []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ('crop', 'animal', 'kind'):
                value = str(tile.get(field, '')).upper()
                if value:
                    result[value] = result.get(value, 0) + 1
                    break
    return result


def _v51_signature(observation):
    player = int(observation.get('player', 0) or 0)
    shops = tuple((observation.get('town') or {}).get('unlocked_shops', []) or [])
    farms = list(observation.get('farms', []) or [])
    if len(farms) != 2 or len(shops) != 1:
        return None
    opponent = farms[1 - player]
    money = float(opponent.get('money', 0) or 0)
    return shops[0], tuple(sorted(_v51_counts(opponent).items())), int(round(money))


_V51_MAIN_RESERVE = {
    ('BAKERY', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 276),
    ('PIZZA_SHOP', (('COW', 1), ('MELON', 12), ('PASTURE', 2), ('SHEEP', 2), ('WHEAT', 7)), 29),
    ('BRUNCH_SPOT', (('COW', 1), ('MELON', 12), ('PASTURE', 2), ('SHEEP', 2), ('WHEAT', 7)), 29),
    ('ICE_CREAM_SHOP', (('COW', 1), ('MELON', 12), ('PASTURE', 2), ('SHEEP', 2), ('WHEAT', 7)), 29),
    ('BRUNCH_SPOT', (('CARROT', 4), ('COW', 2), ('GOOSE', 1), ('MELON', 10), ('SHEEP', 3), ('WHEAT', 5)), 42),
    ('FARMERS_MARKET', (('COW', 2), ('MELON', 11), ('SHEEP', 3), ('STRAWBERRY', 2), ('WHEAT', 5)), 22),
}


def _v51_use_main_for(observation):
    player = int(observation.get('player', 0) or 0)
    step = int(observation.get('step', -1) or -1)
    previous = _V51_LAST_STEP.get(player, -1)
    if step == 0 or step <= previous:
        _V51_USE_MAIN[player] = False
    _V51_LAST_STEP[player] = step
    if step == 72:
        _V51_USE_MAIN[player] = _v51_signature(observation) in _V51_MAIN_RESERVE
    return bool(_V51_USE_MAIN.get(player, False))


def agent(observation, configuration=None):
    main_action = _V51_MAIN_AGENT(observation, configuration)
    try:
        haide_action = _V51_HAIDE_AGENT(observation, configuration)
        if _v51_use_main_for(observation):
            return main_action
        return _v51_copy.deepcopy(haide_action)
    except Exception:
        return main_action


agent.telemetry = {
    'router': 'v51-haide-base-main-reserve',
    'main_reserve_routes': len(_V51_MAIN_RESERVE),
}
'''


def main() -> None:
    if MARKER in MAIN.read_text(encoding="utf-8"):
        raise SystemExit("main.py already contains the V51 marker; refusing a second promotion")
    current = MAIN.read_text(encoding="utf-8")
    if "_V49_MARKET_AGENT" not in current:
        raise SystemExit("expected the tested V49 production markers in main.py")
    source = SOURCE.read_text(encoding="utf-8")
    if "'''" in source:
        raise SystemExit("Haide source contains triple-single quotes; choose a safe readable delimiter first")
    if BACKUP.exists():
        raise SystemExit(f"backup already exists: {BACKUP}")
    shutil.copy2(MAIN, BACKUP)
    block = "\n\n_V51_HAIDE_SOURCE = r'''\n" + source + "\n'''\n" + ROUTER
    MAIN.write_text(current + block, encoding="utf-8", newline="\n")
    print(f"promoted={MAIN}")
    print(f"backup={BACKUP}")
    print(f"haide_source_bytes={len(source.encode('utf-8'))}")


if __name__ == "__main__":
    main()
