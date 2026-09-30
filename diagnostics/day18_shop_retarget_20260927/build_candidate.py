"""Make a day-18 route-family retarget candidate, preserving main.py."""

from pathlib import Path
import hashlib


ROOT = Path(__file__).resolve().parents[2]
source_path = ROOT / "main.py"
target_path = ROOT / "exp_day18_shop_retarget_20260927.py"
source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
expected_hash = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
if source_hash != expected_hash:
    raise SystemExit(f"main.py changed: {source_hash}; expected {expected_hash}")
source = source_path.read_text(encoding="utf-8")
marker = "\n# Kaggle's file loader selects the last newly inserted callable in source"
if source.count(marker) != 1:
    raise SystemExit("Unique final Kaggle entrypoint marker not found")
extension = '''
# Isolated day-18 route-family retarget experiment. The tapes are identical
# through the commitment step, including market orders and worker movement.
_D18_PARENT_ROUTER = _IMPL.chassis.router
_D18_FAMILY = {k for k, tape in _IMPL.chassis.routes.items()
               if tape[:432] == _IMPL.chassis.routes[105][:432]}
assert _D18_FAMILY == {105, 108, 120, 121, 122, 124, 125}
_D18_REPORT = dict(eligible=0, activated=0, insufficient_shops=0, errors=0)

def _d18_retarget_router(observation, step, state):
    if step == 0:
        for key in _D18_REPORT:
            _D18_REPORT[key] = 0
    route = _D18_PARENT_ROUTER(observation, step, state)
    if step == 432 and route in _D18_FAMILY:
        _D18_REPORT['eligible'] += 1
        try:
            shops = list((observation.get('town') or {}).get('unlocked_shops') or [])
            if len(shops) < 4:
                _D18_REPORT['insufficient_shops'] += 1
            else:
                late_pair = tuple(shops[-2:])
                next_route = _R108_SHOP_ROUTES.get(late_pair)
                if next_route in _D18_FAMILY and next_route != route:
                    state['route'] = next_route
                    route = next_route
                    _D18_REPORT['activated'] += 1
        except Exception:
            _D18_REPORT['errors'] += 1
    return route

_IMPL.chassis.router = _d18_retarget_router
agent.telemetry = _D18_REPORT

'''
target_path.write_text(source.replace(marker, "\n" + extension + marker), encoding="utf-8")
print(f"source_sha256={source_hash}")
print(f"candidate_sha256={hashlib.sha256(target_path.read_bytes()).hexdigest()}")
print(f"compatible_routes={sorted([105,108,120,121,122,124,125])}")
