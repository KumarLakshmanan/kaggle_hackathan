"""Freeze timing for the exploratory six-case Pizza/land risk marker."""
from datetime import datetime, timezone
import json

from bundle_audit import HERE, FEATURES, audit


def selected(row):
    p = row['periods']['240']
    return ('PIZZA_SHOP' in p['shops'] and p['rival_public']['land'] >= 3
            and p['own']['land'] <= 2)


def main():
    cases = [audit(row) for row in FEATURES['rows'] if selected(row)]
    assert len(cases) == 6 and all(case['result'] == 'loss' for case in cases)
    out = dict(audited_at_utc=datetime.now(timezone.utc).isoformat(),
               selection='At step240, Pizza among first three shops; rival land >=3 and own land <=2',
               cases=cases)
    (HERE / 'pizza_timing.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps([dict(episode_id=c['episode_id'], rival_land3=c['rival_third_land_actual_step'],
                           own_land3=c['third_land_actual_step'], own_sw312=len(c['snapshots']['312']['own_sw']))
                      for c in cases]), flush=True)


if __name__ == '__main__':
    main()
