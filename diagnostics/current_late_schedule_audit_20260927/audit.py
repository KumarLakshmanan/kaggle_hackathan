from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN_HASH = 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def intentions(actions):
    counts = Counter()
    def walk(value):
        if isinstance(value, list):
            if len(value) >= 2 and isinstance(value[0], str) and value[0] in ('PLANT', 'BUY_SEED'):
                counts[f'{value[0]}:{value[1]}'] += int(value[2]) if value[0] == 'BUY_SEED' else 1
            else:
                for child in value:
                    walk(child)
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)
    walk(actions)
    return dict(sorted(counts.items()))


if __name__ == '__main__':
    main_path = ROOT / 'main.py'
    assert hashlib.sha256(main_path.read_bytes()).hexdigest() == MAIN_HASH
    spec = importlib.util.spec_from_file_location('late_audit_c68', main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    catalogue = json.loads((ROOT / 'diagnostics/shunki_portfolio_20260927/route_manifest.json').read_text())['rows']
    histories = {r['episode_id']: r['reveals'] for r in json.loads((ROOT / 'diagnostics/shunki_portfolio_20260927/shop_sequences.json').read_text())['rows']}
    tapes, prefix_hashes = {}, {}
    checkpoints = list(range(216, 577, 72))
    for row in catalogue:
        eid = row['episode_id']
        if eid == 113445495:
            continue
        with gzip.open(row['route_path'], 'rt', encoding='utf8') as handle:
            actions = json.load(handle)['actions']
        assert digest(actions) == row['action_sha256']
        tapes[eid] = actions
        prefix_hashes[eid] = {step: digest(actions[:step]) for step in checkpoints}
    cohort = {g['episode_id']: g for g in json.loads((ROOT / 'diagnostics/disjoint_live_audit_20260927/cohort_1005.json').read_text())['games']}
    ledger = json.loads((ROOT / 'diagnostics/disjoint_live_top100_cash_20260927/ledger.json').read_text())
    assert ledger['complete']
    out = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), main_sha256=MAIN_HASH,
               plan_sha256=hashlib.sha256((HERE / 'PLAN.md').read_bytes()).hexdigest(),
               source_routes=len(tapes), independent_strength_evidence=False, games=[])
    for audited in ledger['games']:
        live = cohort[audited['episode_id']]
        raw = gzip.decompress(Path(live['replay_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == live['replay_sha256']
        replay = json.loads(raw)
        templates, observations = [], {}
        for step, frame in enumerate(replay['steps'][:719]):
            obs = dict(frame[0]['observation'])
            obs.update(frame[live['candidate_seat']]['observation'])
            templates.append(module._QUEUE_PARENT(obs, replay['configuration']))
            if step in checkpoints:
                observations[step] = obs
        rows = []
        for step in checkpoints:
            prefix = digest(templates[:step])
            compatible = []
            for eid, tape in tapes.items():
                if prefix_hashes[eid][step] != prefix:
                    continue
                differing = [t for t in range(step, 719) if templates[t] != tape[t]]
                compatible.append(dict(episode_id=eid, source_shops=histories[eid].get(str(step)),
                                       differing_future_turns=len(differing), first_difference=differing[0] if differing else None,
                                       intentions=intentions(tape[step:])))
            rows.append(dict(step=step, shops=observations[step]['town']['unlocked_shops'],
                             prefix_sha256=prefix, baseline_intentions=intentions(templates[step:]),
                             compatible=compatible))
        result=dict(episode_id=live['episode_id'], opponent=live['opponent'], checkpoints=rows)
        out['games'].append(result)
        print(live['opponent'], [(r['step'], len(r['compatible']), sum(c['differing_future_turns'] > 0 for c in r['compatible'])) for r in rows], flush=True)
    (HERE / 'audit.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
