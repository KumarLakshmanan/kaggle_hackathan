"""Add absent-worker and initial plant-death counts to the completed audit."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.check import sha

audit = json.loads((HERE / 'audit.json').read_text(encoding='utf-8'))
assert audit['complete'] and audit['native_parity']
results = []
for entry in audit['rows']:
    meta = entry['game']; seat = meta['candidate_seat']
    assert sha(meta['trace_path']) == meta['trace_sha256']
    with gzip.open(meta['trace_path'], 'rt', encoding='utf-8') as f:
        rows = [json.loads(line) for line in f]
    missing = Counter(); examples = []; hire_failures = []; deaths = []
    for step, row in enumerate(rows):
        own = row['observation']['farms'][seat]
        for i, command in enumerate(row['action'].get('hands', [])):
            if i >= len(own['hands']) and command and command[0] != 'PASS':
                missing[command[0]] += 1
                if len(examples) < 12:
                    examples.append(dict(step=step, hand=i, command=command, hands_present=len(own['hands'])))
        if step == 718:
            continue
        future = rows[step+1]['observation']['farms'][seat]
        hires = sum(order == ['HIRE'] for order in row['action'].get('market', []))
        if hires and step % 24 != 23:
            added = len(future['hands']) - len(own['hands'])
            if added < hires:
                hire_failures.append(dict(step=step, requested=hires, hired=added, money_before=own['money'],
                                          money_after=future['money'], market=row['action'].get('market', [])))
        for y, tiles in enumerate(own['tiles']):
            for x, tile in enumerate(tiles):
                next_tile = future['tiles'][y][x]
                if isinstance(tile, dict) and tile.get('kind') == 'PLANT' and isinstance(next_tile, dict) and next_tile.get('kind') == 'WEED':
                    if tile['max_lifespan_step'] < 0 or step < tile['max_lifespan_step']:
                        deaths.append(dict(step=step, x=x, y=y, tile=tile))
    item = dict(fixture_id=meta['fixture_id'], team=meta['team'], seat=seat, margin=meta['margin'],
                absent_nonpass_commands=dict(missing), examples=examples, hire_failures=hire_failures,
                before_expiry_plant_deaths=deaths, present_worker_noops=entry['analysis']['nochange_counts'])
    results.append(item)
    if seat == 0:
        print(meta['team'], meta['margin'], 'absent',sum(missing.values()), 'hires',hire_failures, 'premature deaths',len(deaths))
report = dict(complete=True, diagnostic_only=True, audit_sha256=sha(HERE / 'audit.json'), helper_sha256=sha(__file__),
               completed_at_utc=datetime.now(timezone.utc).isoformat(), rows=results)
with (HERE / 'execution_summary.json').open('x', encoding='utf-8') as out:
    json.dump(report, out, indent=2)
