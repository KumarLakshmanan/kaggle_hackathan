import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN_PATH = ROOT / "main.py"
THOMAS_PATH = (
    ROOT
    / "kaggle_complete_agents_live_2026-09-22_page5_top100"
    / "100-thomastschinkel__kaggriculture-95-5-win-rate-via-replay-routing__7756dc86a48d.py"
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


main = load_module("inspect_main", MAIN_PATH)
thomas = load_module("inspect_thomas", THOMAS_PATH)


def action_key(action):
    return json.dumps(action, sort_keys=True, separators=(",", ":"), default=str)


main_routes = [(int(route), actions) for route, actions in main._ROUTES.items()]
main_keys = {
    route: [action_key(action) for action in actions]
    for route, actions in main_routes
}

print(f"main routes={len(main_routes)} lengths={sorted({len(actions) for _, actions in main_routes})}")
print(f"thomas schedules={len(thomas.SCHEDULES)} lengths={sorted({len(actions) for actions in thomas.SCHEDULES})}")

rows = []
for schedule_id, schedule in enumerate(thomas.SCHEDULES):
    schedule_keys = [action_key(action) for action in schedule]
    best = None
    for route, route_keys in main_keys.items():
        overlap = sum(
            left == right
            for left, right in zip(schedule_keys, route_keys)
        )
        comparable = min(len(schedule_keys), len(route_keys))
        row = (overlap, comparable, route)
        if best is None or row > best:
            best = row
    rows.append((schedule_id, len(schedule_keys), *best))

rows.sort(key=lambda row: (row[2], row[3], row[0]), reverse=True)
print("schedule_id schedule_len best_overlap comparable best_main_route")
for row in rows[:30]:
    print(" ".join(map(str, row)))

print("exact_prefix_matches")
for prefix in (1, 2, 5, 10, 24, 72, 144):
    matches = []
    for schedule_id, schedule in enumerate(thomas.SCHEDULES):
        schedule_keys = [action_key(action) for action in schedule]
        for route, route_keys in main_keys.items():
            if schedule_keys[:prefix] == route_keys[:prefix]:
                matches.append((schedule_id, route))
    print(prefix, len(matches), matches[:40])

