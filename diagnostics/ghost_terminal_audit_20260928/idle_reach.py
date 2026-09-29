"""Optimistic reachability after each unit's last planned non-PASS action."""
from pathlib import Path
import copy
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928 import native_core as core


def main():
    result = []
    for seat in (0, 1):
        with gzip.open(HERE / ('seat' + str(seat) + '.jsonl.gz'), 'rt', encoding='utf-8') as f:
            frames = {r['step']: r for r in map(json.loads, f) if r['step'] >= 696}
        farm = frames[718]['observation']['farms'][seat]
        reach = []
        for unit in range(1 + len(farm['hands'])):
            def command(step):
                action = frames[step]['action']
                return action['farmer'] if unit == 0 else action.get('hands', [])[unit - 1]
            last = max(step for step in frames if command(step)[0] != 'PASS')
            start = last + 1
            if start > 718: continue
            obs = frames[start]['observation']
            own = obs['farms'][seat]
            position = own['farmer'] if unit == 0 else own['hands'][unit - 1]
            opportunities = []
            for y, row in enumerate(own['tiles']):
                for x, tile in enumerate(row):
                    if not isinstance(tile, dict): continue
                    distance = abs(position[0] - x) + abs(position[1] - y)
                    home = min(abs(x - sx) + abs(y - sy) for sx, sy in core._shed_access_tiles(10))
                    needed = distance + 1 + home + 1
                    if needed > 719 - start: continue
                    for op in ('HARVEST', 'COLLECT_FERTILIZER'):
                        test_farm = copy.deepcopy(own)
                        private = copy.deepcopy(obs['private'])
                        before = dict(private['inventories'][unit])
                        if unit == 0: test_farm['farmer'] = [x, y]
                        else: test_farm['hands'][unit - 1] = [x, y]
                        core._apply_unit_action(test_farm, private, unit, [op], 10, 29, 24, 100)
                        added = {k: v - before.get(k, 0) for k, v in private['inventories'][unit].items()
                                 if v > before.get(k, 0)}
                        if added:
                            opportunities.append(dict(target=[x, y], operation=op, products=added,
                                                      optimistic_required_actions=needed))
            reach.append(dict(unit=unit, start=start, available_actions=719 - start,
                              position=position, optimistic_opportunities=opportunities))
        final = frames[718]
        obs = copy.deepcopy(final['observation'])
        own = obs['farms'][seat]
        private = obs['private']
        action = final['action']
        for unit, cmd in enumerate([action['farmer'], *action['hands']]):
            core._apply_unit_action(own, private, unit, cmd, 10, 29, 24, 100)
        sold = {o[1]: o[2] for o in action['market'] if o[0] == 'SELL'}
        bags = [{k: v for k, v in bag.items() if v} for bag in private['inventories']]
        stock = {k: v for k, v in private['shed'].items() if v}
        result.append(dict(seat=seat, idle_windows=reach, bags_after_final_unit_actions=bags,
                           shed_after_final_unit_actions=stock, final_sale_quantities=sold,
                           quantities_exact=stock == sold, total_final_stock=sum(stock.values())))
    report = dict(diagnostic_only=True, seat_results=result,
                  audit_sha256=hashlib.sha256((HERE / 'audit.json').read_bytes()).hexdigest(),
                  helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (HERE / 'idle_reach.json').open('x', encoding='utf-8') as out:
        json.dump(report, out, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
