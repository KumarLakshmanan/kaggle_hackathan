"""Promote the tested V53 margin router into the single-file agent.

V53 embeds a separate rank-41 instance.  This guarded rewrite keeps the
current production file as a backup and never invokes Kaggle submission.
"""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
SOURCE = (
    ROOT
    / "kaggle_complete_agents_live_2026-09-22_top100"
    / "041-ahmedberatozer__kaggriculture-v51-lean-flock__ed66a54d71e6.py"
)
BACKUP = ROOT / "main_v52_before_v53_promotion_retry.py"
V52_MARKER = "# ===== V52 RANK41 RESCUE ROUTER (TESTED, PLAIN SOURCE) ====="
V53_MARKER = "# ===== V53 MARGIN RESCUE ROUTER (TESTED, PLAIN SOURCE) ====="


ROUTER = r'''

# ===== V53 MARGIN RESCUE ROUTER (TESTED, PLAIN SOURCE) =====
# V52 remains the default policy.  A separate rank-41 policy instance is selected
# only for refreshed public step-72 signatures with a positive score-margin
# result and no observed win-rate regression on the current top-50 panel.
import copy as _v53_copy

_V53_BASE_AGENT = agent
_V53_RANK41_NAMESPACE = {
    '__name__': '_embedded_kaggriculture_rank41_v53',
    '__file__': '<embedded-kaggriculture-rank41-v53>',
}
exec(compile(_V53_RANK41_SOURCE, '<embedded-kaggriculture-rank41-v53>', 'exec'),
     _V53_RANK41_NAMESPACE, _V53_RANK41_NAMESPACE)
_V53_RANK41_AGENT = _V53_RANK41_NAMESPACE['agent']
_V53_RANK41_SOURCE = None
_V53_LAST_STEP = {}
_V53_USE_RANK41 = {}


def _v53_counts(farm):
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


def _v53_signature(observation):
    player = int(observation.get('player', 0) or 0)
    shops = tuple((observation.get('town') or {}).get('unlocked_shops', []) or [])
    farms = list(observation.get('farms', []) or [])
    if len(farms) != 2 or len(shops) != 1:
        return None
    opponent = farms[1 - player]
    money = float(opponent.get('money', 0) or 0)
    return shops[0], tuple(sorted(_v53_counts(opponent).items())), int(round(money))


_V53_RANK41_RESERVE = {
    ('ICE_CREAM_SHOP', (('COW', 2), ('MELON', 9), ('SHEEP', 3), ('STRAWBERRY', 2), ('WHEAT', 6)), 36),
    ('PET_CAFE', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 139),
    ('YARN_STORE', (('COW', 2), ('MELON', 10), ('SHEEP', 2), ('WHEAT', 11)), 15),
    ('BAKERY', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 257),
    ('BRUNCH_SPOT', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 203),
    ('PIZZA_SHOP', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 274),
    ('SMOOTHIE_SHOP', (('CARROT', 4), ('COW', 3), ('MELON', 6), ('SHEEP', 2), ('STRAWBERRY', 2), ('WHEAT', 8)), 588),
    ('SMOOTHIE_SHOP', (('COW', 2), ('SHEEP', 3), ('STRAWBERRY', 2), ('WHEAT', 18)), 386),
    ('ICE_CREAM_SHOP', (('CARROT', 1), ('COW', 2), ('MELON', 2), ('SHEEP', 3), ('STRAWBERRY', 6), ('WHEAT', 11)), 143),
    ('ICE_CREAM_SHOP', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 221),
    ('ICE_CREAM_SHOP', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 206),
    ('PIZZA_SHOP', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 215),
    ('BRUNCH_SPOT', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 277),
    ('FARMERS_MARKET', (('COW', 2), ('MELON', 9), ('SHEEP', 3), ('STRAWBERRY', 1), ('WHEAT', 3)), 40),
    ('ICE_CREAM_SHOP', (('COW', 3), ('MELON', 13), ('SHEEP', 3), ('WHEAT', 6)), 8),
    ('FARMERS_MARKET', (('COW', 2), ('MELON', 12), ('SHEEP', 3), ('WHEAT', 8)), 33),
    ('BRUNCH_SPOT', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 274),
    ('SMOOTHIE_SHOP', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 168),
    ('PIZZA_SHOP', (('COW', 3), ('MELON', 12), ('PASTURE', 1), ('SHEEP', 2), ('WHEAT', 7)), 142),
    ('ICE_CREAM_SHOP', (('COW', 2), ('MELON', 8), ('SHEEP', 3), ('STRAWBERRY', 3), ('WHEAT', 8)), 153),
}


def _v53_use_rank41_for(observation):
    player = int(observation.get('player', 0) or 0)
    step = int(observation.get('step', -1) or -1)
    previous = _V53_LAST_STEP.get(player, -1)
    if step == 0 or step <= previous:
        _V53_USE_RANK41[player] = False
    _V53_LAST_STEP[player] = step
    if step == 72:
        _V53_USE_RANK41[player] = _v53_signature(observation) in _V53_RANK41_RESERVE
    return bool(_V53_USE_RANK41.get(player, False))


def agent(observation, configuration=None):
    base_action = _V53_BASE_AGENT(observation, configuration)
    try:
        rank41_action = _V53_RANK41_AGENT(observation, configuration)
        if _v53_use_rank41_for(observation):
            return _v53_copy.deepcopy(rank41_action)
    except Exception:
        pass
    return base_action


agent.telemetry = {
    'router': 'v53-v52-base-rank41-margin-rescue',
    'rank41_reserve_routes': len(_V53_RANK41_RESERVE),
}
'''


def main() -> None:
    current = MAIN.read_text(encoding="utf-8")
    if V53_MARKER in current:
        raise SystemExit("main.py already contains the V53 marker; refusing a second promotion")
    if V52_MARKER not in current or "_V52_RANK41_AGENT" not in current:
        raise SystemExit("expected the tested V52 production marker and embedded rank-41 source")
    source = SOURCE.read_text(encoding="utf-8")
    if "'''" in source:
        raise SystemExit("rank-41 source contains triple-single quotes; choose a safe delimiter")
    if BACKUP.exists():
        raise SystemExit(f"backup already exists: {BACKUP}")
    shutil.copy2(MAIN, BACKUP)
    block = "\n\n_V53_RANK41_SOURCE = r'''\n" + source + "\n'''\n" + ROUTER
    MAIN.write_text(current + block, encoding="utf-8", newline="\n")
    print(f"promoted={MAIN}")
    print(f"backup={BACKUP}")


if __name__ == "__main__":
    main()
