"""Flatten public day-6/day-10 signals and summarize loss/win distributions."""
import csv
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ITEMS = ('CARROT', 'MELON', 'STRAWBERRY', 'TOMATO', 'WHEAT', 'COW', 'SHEEP', 'GOOSE')
PRODUCTS = ('CARROT', 'EGG', 'FERTILIZER', 'MELON', 'MILK', 'STRAWBERRY', 'TOMATO', 'WHEAT', 'WOOL')
SHOP_TYPES = ('BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'PET_CAFE',
              'PIZZA_SHOP', 'SMOOTHIE_SHOP', 'YARN_STORE')


def count(farm, item):
    return farm['animals' if item in ('COW', 'SHEEP', 'GOOSE') else 'crops'].get(item, 0)


def flatten(row):
    flat = dict(episode_id=row['episode_id'], opponent=row['opponent'], opponent_rank=row['opponent_rank'],
                result=row['result'], margin=row['margin'], seed=row['seed'], seat=row['candidate_seat'])
    for step, label in ((144, 'd6'), (240, 'd10')):
        period = row['periods'][str(step)]
        own, rival = period['own'], period['rival_public']
        flat[f'{label}_shops'] = '|'.join(period['shops'])
        for shop in SHOP_TYPES:
            flat[f'{label}_shop_{shop}'] = period['shops'].count(shop)
        for field in ('money', 'land', 'installed'):
            flat[f'{label}_own_{field}'] = own[field]
            flat[f'{label}_rival_{field}'] = rival[field]
            flat[f'{label}_rival_minus_own_{field}'] = rival[field] - own[field]
        for item in ITEMS:
            flat[f'{label}_own_{item}'] = count(own, item)
            flat[f'{label}_rival_{item}'] = count(rival, item)
            flat[f'{label}_rival_minus_own_{item}'] = count(rival, item) - count(own, item)
        for product in PRODUCTS:
            flat[f'{label}_price_{product}'] = period['market_prices'].get(product)
            flat[f'{label}_inventory_{product}'] = period['market_inventory'].get(product)
            flat[f'{label}_own_shed_{product}'] = own['shed'].get(product, 0)
            flat[f'{label}_own_carried_{product}'] = own['carried'].get(product, 0)
            flat[f'{label}_own_sell_requested_{product}'] = period['own_actions']['sold_requested_cumulative'].get(product, 0)
            flat[f'{label}_rival_sell_requested_{product}'] = period['rival_actions_diagnostic']['sold_requested_cumulative'].get(product, 0)
        for side, actions in (('own', period['own_actions']), ('rival', period['rival_actions_diagnostic'])):
            for field in ('previous_day_hand_nonpass', 'previous_day_hand_productive', 'previous_day_hand_moves'):
                flat[f'{label}_{side}_{field}'] = actions[field]
            for order in ('HIRE', 'BUY_LAND', 'BUY_ANIMAL', 'BUY_SEED', 'BUY_PRODUCT', 'SELL'):
                flat[f'{label}_{side}_prevday_{order}'] = actions['previous_day_market'].get(order, 0)
    for product in PRODUCTS:
        flat[f'd6_to_d10_price_change_{product}'] = flat[f'd10_price_{product}'] - flat[f'd6_price_{product}']
        flat[f'd6_to_d10_inventory_change_{product}'] = flat[f'd10_inventory_{product}'] - flat[f'd6_inventory_{product}']
    for side in ('own', 'rival'):
        for field in ('money', 'land', 'installed', *ITEMS):
            flat[f'd6_to_d10_{side}_{field}_growth'] = flat[f'd10_{side}_{field}'] - flat[f'd6_{side}_{field}']
    return flat


def median(rows, name):
    return statistics.median(float(r[name]) for r in rows)


def main():
    features = json.loads((HERE / 'features.json').read_text(encoding='utf8'))
    flat = [flatten(row) for row in features['rows']]
    with (HERE / 'flat.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    by_group = {}
    for label, rows in [('all', flat), ('rank_le_200', [r for r in flat if r['opponent_rank'] <= 200])]:
        wins, losses = [r for r in rows if r['result'] == 'win'], [r for r in rows if r['result'] == 'loss']
        names = [
            'd6_rival_minus_own_money', 'd10_rival_minus_own_money',
            'd6_rival_minus_own_installed', 'd10_rival_minus_own_installed',
            'd6_rival_MELON', 'd10_rival_MELON', 'd10_rival_STRAWBERRY', 'd10_rival_TOMATO',
            'd6_own_money', 'd10_own_money', 'd10_rival_money',
            'd6_own_installed', 'd6_rival_installed',
            'd10_own_installed', 'd10_rival_installed',
            'd6_own_COW', 'd10_own_COW', 'd10_rival_COW',
            'd6_own_SHEEP', 'd10_own_SHEEP', 'd10_rival_SHEEP',
            'd10_own_GOOSE', 'd10_rival_GOOSE',
            'd6_own_previous_day_hand_productive', 'd10_own_previous_day_hand_productive',
            'd10_rival_previous_day_hand_productive',
            'd10_own_prevday_HIRE', 'd10_rival_prevday_HIRE',
            'd6_to_d10_price_change_MELON', 'd6_to_d10_price_change_MILK',
            'd6_to_d10_price_change_STRAWBERRY', 'd6_to_d10_price_change_WOOL',
            'd6_to_d10_price_change_TOMATO',
            'd6_to_d10_inventory_change_MELON', 'd6_to_d10_inventory_change_MILK',
            'd6_to_d10_inventory_change_TOMATO',
        ]
        by_group[label] = dict(wins=len(wins), losses=len(losses),
                               metrics={name: dict(loss_median=median(losses, name), win_median=median(wins, name)) for name in names})
    (HERE / 'feature_summary.json').write_text(json.dumps(by_group, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(by_group, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
