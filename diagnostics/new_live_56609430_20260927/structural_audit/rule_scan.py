"""Exploratory, mechanism-limited observable trigger coverage scan."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
with (HERE / 'flat.csv').open(encoding='utf-8-sig', newline='') as stream:
    ROWS = list(csv.DictReader(stream))


def n(row, name):
    return float(row[name])


RULES = {
    # Day 6: visible rival commitments and funding. These precede our second land commitment.
    'd6_pizza_visible': lambda r: 'PIZZA_SHOP' in r['d6_shops'],
    'd6_rival_melon_12': lambda r: n(r, 'd6_rival_MELON') >= 12,
    'd6_rival_cash_300_below': lambda r: n(r, 'd6_rival_minus_own_money') <= -300,
    'd6_rival_install_4_ahead': lambda r: n(r, 'd6_rival_minus_own_installed') >= 4,
    'd6_rival_cow_2_ahead': lambda r: n(r, 'd6_rival_minus_own_COW') >= 2,
    # Day 10: visible extra footprint, animal commitment, and cash available to answer it.
    'd10_pizza_visible': lambda r: 'PIZZA_SHOP' in r['d10_shops'],
    'd10_pizza_rival_land3_own2': lambda r: 'PIZZA_SHOP' in r['d10_shops'] and n(r, 'd10_rival_land') >= 3 and n(r, 'd10_own_land') <= 2,
    'd10_pizza_install8_ahead': lambda r: 'PIZZA_SHOP' in r['d10_shops'] and n(r, 'd10_rival_minus_own_installed') >= 8,
    'd10_rival_land_3_own_2': lambda r: n(r, 'd10_rival_land') >= 3 and n(r, 'd10_own_land') <= 2,
    'd10_rival_install_8_ahead': lambda r: n(r, 'd10_rival_minus_own_installed') >= 8,
    'd10_rival_install_10_ahead': lambda r: n(r, 'd10_rival_minus_own_installed') >= 10,
    'd10_rival_install_12_ahead': lambda r: n(r, 'd10_rival_minus_own_installed') >= 12,
    'd10_rival_cow_2_ahead': lambda r: n(r, 'd10_rival_minus_own_COW') >= 2,
    'd10_rival_strawberry_5_ahead': lambda r: n(r, 'd10_rival_minus_own_STRAWBERRY') >= 5,
    'd10_rival_cash_1000_ahead': lambda r: n(r, 'd10_rival_minus_own_money') >= 1000,
    'd10_rival_install_8_cash_not_ahead': lambda r: n(r, 'd10_rival_minus_own_installed') >= 8 and n(r, 'd10_rival_minus_own_money') <= 0,
    'd10_rival_land_3_cash_not_ahead': lambda r: n(r, 'd10_rival_land') >= 3 and n(r, 'd10_own_land') <= 2 and n(r, 'd10_rival_minus_own_money') <= 0,
    'd10_rival_install_8_own_cash_2500': lambda r: n(r, 'd10_rival_minus_own_installed') >= 8 and n(r, 'd10_own_money') >= 2500,
    'd10_rival_install_8_milk_price_down': lambda r: n(r, 'd10_rival_minus_own_installed') >= 8 and n(r, 'd6_to_d10_price_change_MILK') < 0,
}


def main():
    assert len(ROWS) == 61 and sum(r['result'] == 'loss' for r in ROWS) == 19
    out = []
    for name, rule in RULES.items():
        flagged = [r for r in ROWS if rule(r)]
        tp = [r for r in flagged if r['result'] == 'loss']
        fp = [r for r in flagged if r['result'] == 'win']
        strong_fp = [r for r in fp if n(r, 'opponent_rank') <= 200]
        out.append(dict(rule=name, loss_coverage=len(tp), false_positives=len(fp),
                        strong_rank_false_positives=len(strong_fp),
                        precision=len(tp) / len(flagged) if flagged else None,
                        loss_ids=[int(r['episode_id']) for r in tp],
                        win_ids=[int(r['episode_id']) for r in fp],
                        win_opponents=[r['opponent'] for r in fp],
                        flagged_shops=[dict(episode_id=int(r['episode_id']), result=r['result'],
                                            shops=r['d10_shops'] if name.startswith('d10') else r['d6_shops'])
                                       for r in flagged]))
    (HERE / 'rule_scan.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps([{k: v for k, v in row.items() if k not in ('loss_ids','win_ids','win_opponents','flagged_shops')}
                      for row in out], ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
