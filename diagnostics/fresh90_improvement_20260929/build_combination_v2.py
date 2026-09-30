import ast
from datetime import datetime, timezone
import json
from run_panel import HERE, sha

source_path = HERE / 'candidate_fresh_combined_v1.py'
manifest = json.loads((HERE / 'combined_v1_manifest.json').read_text())
assert sha(source_path) == manifest['candidate_sha256'] == 'ef33a1b6e89f1214bffa7575ffcbb13053ef4054709cde4c52d76b74207a804a'
comparison = json.loads((HERE / 'combined_v1_public27_comparison.json').read_text())
assert len(comparison['lost_wins']) == 4 and not comparison['gained_wins']
rows = [json.loads(s) for s in (HERE / 'combined_v1_public27_jobs_results.jsonl').read_text().splitlines()]
losers = {(r['episode'], r['seat']) for r in comparison['lost_wins']}
assert {r['candidate_telemetry']['fresh_complete_pair'] for r in rows if (r['episode_id'], r['candidate_seat']) in losers} == {'YARN_STORE|SMOOTHIE_SHOP'}
old_rules = manifest['selected_rules']
rules = {k: v for k, v in old_rules.items() if k != 'YARN_STORE|SMOOTHIE_SHOP'}
assert len(rules) == 8
source = source_path.read_text(encoding='utf-8')
old_line = '_FRESH_COMPLETE_ROUTES = ' + repr(old_rules)
assert source.count(old_line) == 1
source = source.replace(old_line, '_FRESH_COMPLETE_ROUTES = ' + repr(rules))
ast.parse(source)
dest = HERE / 'candidate_fresh_combined_v2.py'
assert not dest.exists()
dest.write_text(source, encoding='utf-8', newline='\n')
result = manifest | dict(at_utc=datetime.now(timezone.utc).isoformat(), candidate=str(dest),
                         candidate_sha256=sha(dest), previous_candidate_sha256=sha(source_path),
                         selected_rules=rules, removed_rule='YARN_STORE|SMOOTHIE_SHOP',
                         public27_now_development=True, plan_sha256=sha(HERE / 'COMBINATION_V2_PLAN.md'),
                         rejection_evidence_sha256=sha(HERE / 'combined_v1_public27_comparison.json'))
(HERE / 'combined_v2_manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
