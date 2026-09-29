"""Summarize existing public state traces without new strategy outcomes."""
from pathlib import Path
from collections import Counter
import gzip
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def farm_summary(farm):
    plants = Counter(); animals = Counter()
    for row in farm['tiles']:
        for tile in row:
            if isinstance(tile, dict):
                if tile.get('crop'): plants[tile['crop']] += 1
                if tile.get('animal'): animals[tile['animal']] += 1
    return dict(money=farm['money'], plants=dict(plants), animals=dict(animals),
                land=farm['unlocked_quadrants'], workers=len(farm['hands']))


audit_path = ROOT / 'diagnostics/residual_execution_20260928/audit.json'
audit = read(audit_path)
assert sha(audit_path) == '74e4e6e4d1d26b16348c0026f139db14e625fa74ad5e57be66ee366fbbde572a'
pool = read(HERE / 'pool.json'); target_ids = set(sum(pool['target_ids'].values(), [])); rows = []
for item in audit['rows']:
    game = item['game']
    if game['fixture_id'] not in target_ids or game['candidate_seat'] != 0: continue
    trace = Path(game['trace_path']); assert sha(trace) == game['trace_sha256']
    summaries = []
    with gzip.open(trace, 'rt', encoding='utf-8') as stream:
        for line in stream:
            frame = json.loads(line)
            if frame['step'] not in (72, 144, 240, 360, 480, 600, 718): continue
            obs = frame['observation']; own, rival = obs['farms']
            summaries.append(dict(step=frame['step'], own=farm_summary(own), rival=farm_summary(rival),
                                  cash_margin=own['money'] - rival['money'], shops=obs['town']['unlocked_shops']))
    rows.append(dict(fixture_id=game['fixture_id'], team=game['team'], source_sha256=game['source_sha256'],
                     terminal_margin=game['margin'], trace_sha256=game['trace_sha256'], observations=summaries))
assert len(rows) == 16
result = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), diagnostic_only=True,
              source_note='Existing native-parity 8dde traces. The later367 repair does not activate on these16 cases; this does not count as new validation.',
              audit_sha256=sha(audit_path), helper_sha256=sha(__file__), rows=rows)
with (HERE / 'mechanism_inventory.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
for row in rows:
    early = next(r for r in row['observations'] if r['step'] == 240)
    late = next(r for r in row['observations'] if r['step'] == 600)
    print(row['team'], 'day10', early['cash_margin'], 'day25', late['cash_margin'],
          'day10 animals', early['own']['animals'], early['rival']['animals'], flush=True)
