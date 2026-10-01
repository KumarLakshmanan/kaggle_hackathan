"""Episode-group separated saved-outcome fitting; never reads rival private data."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from .value import features


def train(manifest, output):
    jobs = json.loads(Path(manifest).read_text())
    episodes = {int(j['entry']['episode_id']): j['entry']['replay_path'] for j in jobs}
    rows = []; sources = []
    for episode, path in sorted(episodes.items()):
        data = gzip.decompress(Path(path).read_bytes()); replay = json.loads(data)
        sources.append({'episode': episode, 'sha256': hashlib.sha256(data).hexdigest(), 'split': 'holdout' if episode%5 == 0 else 'train'})
        final = replay['rewards']
        for step in range(72, min(719, len(replay['steps'])), 72):
            for seat in (0, 1):
                obs = replay['steps'][step][seat]['observation']
                if not obs or 'private' not in obs: continue
                # Only this seat's observation is input. Rewards are targets only.
                margin = obs['farms'][seat]['money']-obs['farms'][1-seat]['money']
                end = final[seat]-final[1-seat]
                rows.append((episode, features(obs), (end-margin)/100000., 1. if end > 0 else .5 if end == 0 else 0., margin/100000., end/100000.))
        del data, replay
    x = np.asarray([r[1] for r in rows], dtype=float); tail = np.asarray([r[2] for r in rows]); y = np.asarray([r[3] for r in rows])
    train_mask = np.asarray([r[0]%5 != 0 for r in rows]); hold = ~train_mask
    means = x[train_mask].mean(axis=0); scales = x[train_mask].std(axis=0); scales[scales < 1e-8] = 1.
    # Retain intercept as one; centering it would remove it.
    means[0] = 0.; scales[0] = 1.; z = (x-means)/scales
    penalty = np.eye(z.shape[1])*25.; penalty[0, 0] = .01
    weights = np.linalg.solve(z[train_mask].T@z[train_mask]+penalty, z[train_mask].T@tail[train_mask])
    w = np.zeros(z.shape[1])
    for _ in range(35):
        probability = 1/(1+np.exp(-np.clip(z[train_mask]@w, -30, 30)))
        grad = z[train_mask].T@(probability-y[train_mask])+penalty@w
        h = z[train_mask].T@(z[train_mask]*(probability*(1-probability))[:, None])+penalty
        delta = np.linalg.solve(h, grad); w -= delta
        if np.linalg.norm(delta) < 1e-6: break
    prediction = z[hold]@weights; errors = prediction-tail[hold]
    p = 1/(1+np.exp(-np.clip(z[hold]@w, -30, 30)))
    cash = np.asarray([r[4] for r in rows]); cash_p = 1/(1+np.exp(-np.clip(cash[hold]*5, -30, 30)))
    rmse = float(np.sqrt(np.mean(errors**2))*100000.)
    baseline_rmse = float(np.sqrt(np.mean(tail[hold]**2))*100000.)
    brier = float(np.mean((p-y[hold])**2)); baseline_brier = float(np.mean((cash_p-y[hold])**2))
    accepted = rmse < baseline_rmse and brier < baseline_brier
    result = {'version': 2, 'accepted': bool(accepted), 'feature_count': z.shape[1], 'means': means.tolist(), 'scales': scales.tolist(),
        'margin_weights': weights.tolist(), 'win_weights': w.tolist(), 'holdout_rmse': rmse,
        'holdout_mae': float(np.mean(abs(errors))*100000.), 'cash_only_rmse': baseline_rmse,
        'holdout_brier': brier, 'cash_only_brier': baseline_brier, 'holdout_samples': int(hold.sum()),
        'train_samples': int(train_mask.sum()), 'train_episodes': sorted({r[0] for r in rows if r[0]%5}),
        'holdout_episodes': sorted({r[0] for r in rows if not r[0]%5}),
        'max_standardized_feature': float(max(6., np.quantile(abs(z[train_mask, 1:]), .999))),
        'sources': sources, 'split': 'episode_id modulo 5 == 0 is holdout',
        'decision': 'Enable estimated tail with holdout uncertainty.' if accepted else 'Disable fitted inference; retain diagnostic fit only.',
        'scope': 'Correlated older public episodes; heldout model error does not establish live strength or probability calibration.'}
    Path(output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    return {k:v for k,v in result.items() if k not in ('sources', 'means', 'scales', 'margin_weights', 'win_weights', 'train_episodes', 'holdout_episodes')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--manifest', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args(); print(json.dumps(train(args.manifest, args.output), indent=2))
