"""Remove two route overrides implicated by V1's failed native confirmation."""
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
from build import HERE, ROOT, BASE, BASE_SHA, sha, load


def main():
    parent = HERE / 'candidate_v1.py'
    assert sha(parent) == '2c02f9f9898dc393f8798f1d51a3a4c26a4bf1ddf862770ef66be159d61d6e13'
    assert sha(BASE) == BASE_SHA
    source = parent.read_text(encoding='utf-8')
    lines = source.splitlines(keepends=True)
    edits = []
    removed = {'_POOL_REPLACEMENTS': ('YARN_STORE|FARMERS_MARKET', 113349962),
               '_LOSS_POOL_REPLACEMENTS': ('FARMERS_MARKET|PIZZA_SHOP', 113372534)}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in removed:
                pair, expected = removed[target.id]
                value = ast.literal_eval(node.value)
                assert value.pop(pair) == expected
                edits.append((node.lineno - 1, node.end_lineno,
                              target.id + ' = ' + repr(value) + '\n'))
    assert len(edits) == 2
    for start, end, text in sorted(edits, reverse=True):
        lines[start:end] = [text]
    destination = HERE / 'candidate_v2.py'
    assert not destination.exists()
    destination.write_text(''.join(lines), encoding='utf-8', newline='\n')
    old, new = load(BASE, 'repair_base_v2'), load(destination, 'repair_candidate_v2')
    assert old._DATA['opening'] == new._DATA['opening']
    for pair, _ in removed.values():
        for key, route in old._DATA['route_map'].items():
            if key == pair or key.startswith(pair + '|'):
                assert new._DATA['route_map'][key] == route, key
    manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
                    candidate=str(destination), candidate_sha256=sha(destination),
                    source=str(parent), source_sha256=sha(parent),
                    baseline=str(BASE), baseline_sha256=BASE_SHA,
                    plan_sha256=sha(HERE / 'PLAN_V2.md'),
                    removed_route_pairs=[v[0] for v in removed.values()],
                    original_route_maps_verified=True,
                    root_main_sha256=sha(ROOT / 'main.py'))
    (HERE / 'manifest_v2.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
