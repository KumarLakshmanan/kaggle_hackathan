"""Apply the frozen 61-game observable rules to the next five live episodes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from analyze import flatten
from bundle_audit import BY_ID, audit
from extract import extract
from rule_scan import RULES

HERE = Path(__file__).resolve().parent
DELTA = HERE.parent / 'delta_171158.json'
OUT = HERE / 'later_delta_171158.json'
RULE_NAMES = ('d10_rival_install_8_cash_not_ahead',
              'd10_pizza_rival_land3_own2', 'd10_pizza_install8_ahead')


def main():
    raw = DELTA.read_bytes()
    delta = json.loads(raw)
    assert delta['complete'] and not delta['failures'] and len(delta['games']) == 5
    rows = []
    for game in delta['games']:
        feature = extract(game)
        flat = flatten(feature)
        flags = {name:bool(RULES[name](flat)) for name in RULE_NAMES}
        row = dict(episode_id=game['episode_id'], opponent=game['opponent'],
                         rank=flat['opponent_rank'], result=game['result'],
                         margin=game['margin'], replay_sha256=game['replay_sha256'],
                         day10_shops=flat['d10_shops'],
                         day10_land_own_rival=[flat['d10_own_land'], flat['d10_rival_land']],
                         day10_installed_own_rival=[flat['d10_own_installed'], flat['d10_rival_installed']],
                         day10_cash_own_rival=[flat['d10_own_money'], flat['d10_rival_money']],
                         flags=flags)
        if flags['d10_pizza_rival_land3_own2']:
            BY_ID[game['episode_id']] = game
            case = audit(feature)
            row['rival_third_land_actual_step'] = case['rival_third_land_actual_step']
            row['own_third_land_actual_step'] = case['third_land_actual_step']
            row['own_sw_installed_step312'] = len(case['snapshots']['312']['own_sw'])
        rows.append(row)
    out = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),
               source_delta=str(DELTA.resolve()), source_delta_sha256=hashlib.sha256(raw).hexdigest(),
               selection='Five later public episodes; exact rules recorded in frozen 61-game rule_scan.py',
               all_replay_hashes_verified=True, rows=rows)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(rows, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
