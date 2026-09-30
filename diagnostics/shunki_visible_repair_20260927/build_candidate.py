"""Add a narrow visible-weed worker repair to the frozen Shunki selector."""

from pathlib import Path
import hashlib


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "exp_shunki_later_lookup_20260927.py"
OUTPUT = ROOT / "exp_shunki_visible_repair_20260927.py"
EXPECTED = "68aad0908c38884aba856373088f1a6ba4a0423df2ee00edbec4c796f8e45fac"
actual = hashlib.sha256(BASE.read_bytes()).hexdigest()
if actual != EXPECTED:
    raise SystemExit(f"Base candidate changed: {actual}")
source = BASE.read_text(encoding="utf8")
tail = "def kaggle_shunki_later_lookup_entrypoint(observation, configuration=None):\n    return agent(observation, configuration)\n"
if not source.endswith(tail):
    raise SystemExit("Unexpected base candidate entrypoint")
extension = '''_ROUTE_AGENT = agent
_REPAIR_STATS = {"idle_weed_digs": 0, "blocked_work_digs": 0,
                 "replayed_work": 0, "repair_errors": 0}
_PENDING_WORK = {}

def _visible_repair_agent(observation, configuration=None):
    action = _ROUTE_AGENT(observation, configuration)
    try:
        step = int(_value(observation, "step", 0))
        if step == 0:
            _PENDING_WORK.clear()
            for key in _REPAIR_STATS:
                _REPAIR_STATS[key] = 0
        player = int(_value(observation, "player", 0))
        farms = _value(observation, "farms", []) or []
        farm = farms[player]
        board = _value(farm, "tiles", []) or []
        positions = [_value(farm, "farmer", None)] + list(_value(farm, "hands", []) or [])
        units = [list(action.get("farmer") or ["PASS"])]
        units += [list(a or ["PASS"]) for a in action.get("hands", [])]
        units += [["PASS"] for _ in range(max(0, len(positions) - len(units)))]
        units = units[:len(positions)]
        shops = list(_value(_value(observation, "town", {}), "unlocked_shops", []) or [])
        route = None
        for count in range(1, min(len(shops), 8) + 1):
            if step < 72 * count:
                break
            candidate = _DATA["route_map"].get("|".join(shops[:count]))
            if candidate is not None:
                route = candidate
        route_actions = _DATA["routes"].get(str(route)) if route is not None else None
        next_action = (route_actions[step + 1] if route_actions and step < 718
                       and (step + 1) % 72 != 0 else None)
        next_units = ([next_action.get("farmer") or ["PASS"]]
                      + list(next_action.get("hands") or [])) if next_action else []
        for idx, pos in enumerate(positions):
            if not isinstance(pos, (list, tuple)) or len(pos) < 2:
                continue
            x, y = int(pos[0]), int(pos[1])
            if not (0 <= y < len(board) and 0 <= x < len(board[y])):
                continue
            tile = board[y][x]
            weed = isinstance(tile, dict) and tile.get("kind") == "WEED"
            op = units[idx][0] if units[idx] else "PASS"
            key = (player, idx)
            pending = _PENDING_WORK.pop(key, None)
            if pending and not weed and pending[0] == (x, y) and op == "PASS":
                units[idx] = pending[1]
                _REPAIR_STATS["replayed_work"] += 1
            elif weed and op == "PASS":
                units[idx] = ["DIG"]
                _REPAIR_STATS["idle_weed_digs"] += 1
            elif weed and op in ("PLANT", "BUILD_COOP", "BUILD_PASTURE"):
                nxt = next_units[idx] if idx < len(next_units) else None
                if nxt and nxt[0] == "PASS":
                    _PENDING_WORK[key] = ((x, y), list(units[idx]))
                    units[idx] = ["DIG"]
                    _REPAIR_STATS["blocked_work_digs"] += 1
        revised = dict(action)
        revised["farmer"] = units[0]
        revised["hands"] = units[1:]
        return revised
    except Exception:
        _REPAIR_STATS["repair_errors"] += 1
        return action

agent = _visible_repair_agent
agent.telemetry = _REPAIR_STATS

def kaggle_shunki_visible_repair_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
OUTPUT.write_text(source[:-len(tail)] + extension, encoding="utf8")
print("base_sha256", actual)
print("candidate_sha256", hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
print("bytes", OUTPUT.stat().st_size)
