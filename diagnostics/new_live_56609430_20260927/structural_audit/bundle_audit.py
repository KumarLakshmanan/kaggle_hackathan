"""Inspect actual third-land timing and worker obligations for risk-flagged games."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FEATURES = json.loads((HERE / 'features.json').read_text(encoding='utf8'))
COHORT = json.loads((HERE.parent / 'cohort_165306.json').read_text(encoding='utf8'))
BY_ID = {g['episode_id']: g for g in COHORT['games']}


def installed_in_quadrant(farm, quadrant):
    points = []
    for y, row in enumerate(farm['tiles']):
        for x, tile in enumerate(row):
            if quadrant == 'SW' and not (x < 5 and y >= 5):
                continue
            if quadrant == 'SE' and not (x >= 5 and y >= 5):
                continue
            if isinstance(tile, dict) and (tile.get('crop') or tile.get('animal')):
                points.append((x, y, tile.get('crop') or tile.get('animal')))
    return points


def selected(row):
    p = row['periods']['240']
    return (p['rival_public']['installed'] - p['own']['installed'] >= 8
            and p['rival_public']['money'] <= p['own']['money'])


def audit(row):
    game = BY_ID[row['episode_id']]
    raw = gzip.decompress(Path(game['replay_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == game['replay_sha256']
    replay = json.loads(raw)
    seat = row['candidate_seat']
    opponent = 1 - seat
    steps = replay['steps']
    requested = []
    actual = None
    rival_actual = None
    for step in range(1, 241):
        if len(steps[step][seat]['observation']['farms'][opponent]['unlocked_quadrants']) >= 3:
            rival_actual = step
            break
    for step in range(241, 720):
        action = steps[step][seat].get('action') or {}
        if any(order and order[0] == 'BUY_LAND' for order in action.get('market') or []):
            requested.append(dict(step=step, pre_cash=steps[step - 1][seat]['observation']['farms'][seat]['money'],
                                  post_cash=steps[step][seat]['observation']['farms'][seat]['money']))
        if actual is None and len(steps[step][seat]['observation']['farms'][seat]['unlocked_quadrants']) >= 3:
            actual = step
    p = row['periods']['240']
    shops = p['shops']
    at = {}
    for step in (240, 264, 288, 312, 336, 360, 408):
        own_farm = steps[step][seat]['observation']['farms'][seat]
        rival_farm = steps[step][seat]['observation']['farms'][opponent]
        at[str(step)] = dict(own_money=own_farm['money'], rival_money=rival_farm['money'],
                             own_land=len(own_farm['unlocked_quadrants']),
                             rival_land=len(rival_farm['unlocked_quadrants']),
                             own_sw=installed_in_quadrant(own_farm, 'SW'),
                             own_se=installed_in_quadrant(own_farm, 'SE'))
    next_day_market = []
    for step in range(241, 265):
        action = steps[step][seat].get('action') or {}
        for order in action.get('market') or []:
            if order and order[0] in ('BUY_LAND', 'BUY_ANIMAL', 'BUY_SEED', 'BUY_PRODUCT', 'HIRE'):
                next_day_market.append(dict(step=step, order=order))
    return dict(episode_id=row['episode_id'], opponent=row['opponent'], opponent_rank=row['opponent_rank'],
                result=row['result'], margin=row['margin'], shops=shops, pizza=('PIZZA_SHOP' in shops),
                d10_own_money=p['own']['money'], d10_rival_money=p['rival_public']['money'],
                d10_own_installed=p['own']['installed'], d10_rival_installed=p['rival_public']['installed'],
                d10_own_land=p['own']['land'], d10_rival_land=p['rival_public']['land'],
                d10_own_previous_day_productive=p['own_actions']['previous_day_hand_productive'],
                d10_rival_previous_day_productive=p['rival_actions_diagnostic']['previous_day_hand_productive'],
                third_land_first_request=requested[0] if requested else None,
                third_land_actual_step=actual, rival_third_land_actual_step=rival_actual,
                buy_land_requests=requested,
                next_day_purchase_hire_requests=next_day_market, snapshots=at)


def main():
    rows = [audit(row) for row in FEATURES['rows'] if selected(row)]
    assert len(rows) == 12
    out = dict(audited_at_utc=datetime.now(timezone.utc).isoformat(),
               selection='Day10 rival installed >= own+8 and rival money <= own; 8 losses + 4 wins',
               cases=rows)
    (HERE / 'bundle_cases.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    for row in rows:
        print(json.dumps({k: row[k] for k in ('episode_id', 'opponent', 'result', 'pizza',
                                             'd10_own_money', 'd10_rival_money',
                                             'd10_own_installed', 'd10_rival_installed',
                                             'd10_own_land', 'd10_rival_land',
                                             'third_land_actual_step')}, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
