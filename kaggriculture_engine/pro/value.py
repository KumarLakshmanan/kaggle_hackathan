"""Small stdlib inference model; all features are available to one player."""
import math
from .. import native_core as core
from .scheduler import counts


def features(obs):
    seat = int(obs['player']); own = obs['farms'][seat]; rival = obs['farms'][1-seat]
    a, b = counts(own), counts(rival); remaining = max(0., (30-int(obs['day']))/30.)
    values = [1., remaining, remaining*remaining,
              (own['money']-rival['money'])/100000., own['money']/100000., rival['money']/100000.,
              (len(own['hands'])-len(rival['hands']))/10.,
              (len(own['unlocked_quadrants'])-len(rival['unlocked_quadrants']))/4.]
    for item in list(core.CROPS)+list(core.ANIMALS):
        values.extend([(a[item]-b[item])/100., remaining*(a[item]-b[item])/100.])
    for item in core.PRODUCTS:
        price = obs['market']['prices'][item]
        values.extend([(obs['market']['inventory'][item]-10000)/1000., price/500.,
            (obs['private']['shed'].get(item, 0)+sum(pack.get(item, 0) for pack in obs['private']['inventories']))*price/100000.])
    values.append(sum(obs['private']['seeds'].get(c, 0)*s['seed'] for c, s in core.CROPS.items())/100000.)
    for farm in (own, rival):
        ready = 0.
        for row in farm['tiles']:
            for tile in row:
                if isinstance(tile, dict):
                    item = tile.get('crop') or core.ANIMALS.get(tile.get('animal'), {}).get('product')
                    if item: ready += tile.get('yield_units', 0)*obs['market']['prices'][item]
        values.append(ready/100000.)
    return values


def estimate(obs, model):
    seat = int(obs['player']); margin = obs['farms'][seat]['money']-obs['farms'][1-seat]['money']
    x = features(obs)
    if int(obs['step']) >= 719:
        return {'margin': margin, 'uncertainty': 0., 'win_points': 1. if margin > 0 else .5 if margin == 0 else 0., 'scope': 'terminal cash'}
    if not model or not model.get('accepted'):
        return {'margin': margin, 'uncertainty': 100000., 'win_points': None, 'scope': 'cash only; fitted model disabled'}
    standardized = [(v-m)/s for v, m, s in zip(x, model['means'], model['scales'])]
    tail = sum(v*w for v, w in zip(standardized, model['margin_weights']))*100000.
    logit = max(-30., min(30., sum(v*w for v, w in zip(standardized, model['win_weights']))))
    outlier = max([abs(v) for v in standardized[1:]] or [0]) > model['max_standardized_feature']
    return {'margin': margin+tail, 'uncertainty': model['holdout_rmse']*(2 if outlier else 1),
            'win_points': 1/(1+math.exp(-logit)) if not outlier else None,
            'scope': 'held-out fitted estimate; not a calibrated live win probability', 'out_of_distribution': outlier}
