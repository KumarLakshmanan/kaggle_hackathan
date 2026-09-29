"""Cross-check new367 decision prefixes against previously verified8dde traces."""
from pathlib import Path
import gzip
import json
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


source = HERE / 'matched_features72.json'
features = read(source); assert features['complete'] and features['prefix_count'] == 208
by_key = {(r['fixture_id'], r['candidate_seat']): r for r in features['rows']}
audit_path = ROOT / 'diagnostics/residual_execution_20260928/audit.json'
assert sha(audit_path) == '74e4e6e4d1d26b16348c0026f139db14e625fa74ad5e57be66ee366fbbde572a'
rows = []
for entry in read(audit_path)['rows']:
    game = entry['game']; trace = Path(game['trace_path'])
    assert sha(trace) == game['trace_sha256']
    with gzip.open(trace, 'rt', encoding='utf-8') as stream:
        for line in stream:
            frame = json.loads(line)
            if frame['step'] == 72: break
        else: raise AssertionError('Missing observation72')
    obs = frame['observation']; seat = game['candidate_seat']; row = by_key[(game['fixture_id'], seat)]
    expected = dict(own_farm=obs['farms'][seat], rival_farm=obs['farms'][1-seat], own_private=obs['private'],
                    market=obs['market'], revealed_shops=obs['town']['unlocked_shops'])
    mismatches = [key for key, value in expected.items() if row[key] != value]
    rows.append(dict(fixture_id=game['fixture_id'], seat=seat, prior_source_sha256=game['candidate_sha256'],
                     trace_sha256=game['trace_sha256'], mismatched_fields=mismatches, passed=not mismatches))
assert len(rows) == 42
result = dict(complete=True, passed=all(r['passed'] for r in rows), compared_prefixes=42,
              matched_features_sha256=sha(source), prior_audit_sha256=sha(audit_path), helper_sha256=sha(__file__),
              created_at_utc=datetime.now(timezone.utc).isoformat(), diagnostic_only=True, rows=rows)
with (HERE / 'feature_parity.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
assert result['passed']
