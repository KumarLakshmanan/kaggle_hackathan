"""Extract day-6/day-10 state and prior-day execution from all 61 live replays."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COHORT = HERE.parent / 'cohort_165306.json'
STEPS = (144, 240)
PRODUCTIVE = {'PLANT', 'PLACE', 'HARVEST', 'FEED', 'CARE', 'WATER', 'PICKUP', 'DROP',
              'COLLECT_FERTILIZER', 'REMOVE_WEED'}
MOVE = {'NORTH', 'SOUTH', 'EAST', 'WEST'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def farm_state(farm):
    crops, animals, kinds = Counter(), Counter(), Counter()
    for row in farm['tiles']:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kind = tile.get('kind')
            if kind:
                kinds[kind] += 1
            if tile.get('crop'):
                crops[tile['crop']] += 1
            if tile.get('animal'):
                animals[tile['animal']] += 1
    return dict(money=float(farm['money']), land=len(farm['unlocked_quadrants']),
                land_names=farm['unlocked_quadrants'], hands=len(farm['hands']),
                crops=dict(crops), animals=dict(animals), tile_kinds=dict(kinds),
                installed=sum(crops.values()) + sum(animals.values()))


def action_summary(frames, seat, stop):
    # The action stored at frame t has produced that frame's observation.
    rows = [frame[seat].get('action') or {} for frame in frames[1:stop + 1]]
    daily = rows[-24:]
    commands = Counter()
    market = Counter()
    sold = Counter()
    bought = Counter()
    for action in daily:
        farmer = action.get('farmer') or ['PASS']
        commands['farmer_' + str(farmer[0])] += 1
        for hand in action.get('hands') or []:
            if hand:
                commands['hands_' + str(hand[0])] += 1
        for order in action.get('market') or []:
            if order:
                market[str(order[0])] += 1
    for action in rows:
        for order in action.get('market') or []:
            if not order:
                continue
            if order[0] == 'SELL' and len(order) >= 3:
                sold[str(order[1])] += int(order[2])
            elif str(order[0]).startswith('BUY_') and len(order) >= 3:
                bought[str(order[1])] += int(order[2])
    hand_nonpass = sum(v for k, v in commands.items() if k.startswith('hands_') and k != 'hands_PASS')
    hand_productive = sum(v for k, v in commands.items() if k.split('_', 1)[0] == 'hands'
                          and k.split('_', 1)[1] in PRODUCTIVE)
    hand_moves = sum(v for k, v in commands.items() if k.startswith('hands_') and k[6:] in MOVE)
    return dict(previous_day_commands=dict(commands), previous_day_market=dict(market),
                previous_day_hand_nonpass=hand_nonpass,
                previous_day_hand_productive=hand_productive,
                previous_day_hand_moves=hand_moves,
                sold_requested_cumulative=dict(sold), bought_requested_cumulative=dict(bought))


def extract(game):
    raw = gzip.decompress(Path(game['replay_path']).read_bytes())
    assert sha(raw) == game['replay_sha256'], game['episode_id']
    replay = json.loads(raw)
    assert replay['module_version'] == '1.32.7'
    assert len(replay['steps']) == 720 and replay['statuses'] == ['DONE', 'DONE']
    seat = game['candidate_seat']
    rival = 1 - seat
    assert replay['info']['TeamNames'][seat] == 'Lakshmanan R'
    assert replay['info']['TeamNames'][rival] == game['opponent']
    periods = {}
    for stop in STEPS:
        own_obs = replay['steps'][stop][seat]['observation']
        rival_obs = replay['steps'][stop][rival]['observation']
        assert int(own_obs['day']) == stop // 24 and int(own_obs['hour']) == 0
        if 'step' in own_obs:
            assert int(own_obs['step']) == stop
        assert own_obs['town'] == rival_obs['town'] and own_obs['market'] == rival_obs['market']
        own = farm_state(own_obs['farms'][seat])
        opponent = farm_state(own_obs['farms'][rival])
        own['shed'] = own_obs['private']['shed']
        own['carried'] = dict(sum((Counter(inv) for inv in own_obs['private']['inventories']), Counter()))
        periods[str(stop)] = dict(day=int(own_obs['day']), shops=own_obs['town']['unlocked_shops'],
                                  market_prices=own_obs['market']['prices'],
                                  market_inventory=own_obs['market']['inventory'],
                                  own=own, rival_public=opponent,
                                  rival_private_oracle=dict(shed=rival_obs['private']['shed']),
                                  own_actions=action_summary(replay['steps'], seat, stop),
                                  rival_actions_diagnostic=action_summary(replay['steps'], rival, stop))
    ranks = game['opponent_snapshot_ranks']
    assert len(ranks) == 1
    return dict(episode_id=game['episode_id'], opponent=game['opponent'],
                opponent_rank=int(ranks[0]['rank']), result=game['result'],
                margin=game['margin'], seed=game['seed'], candidate_seat=seat,
                replay_sha256=game['replay_sha256'], periods=periods)


def main():
    cohort_raw = COHORT.read_bytes()
    cohort = json.loads(cohort_raw)
    assert cohort['complete'] and len(cohort['games']) == 61 and cohort['wins'] == 42 and cohort['losses'] == 19
    rows = []
    target = HERE / 'features.json'
    assert not target.exists()
    for game in cohort['games']:
        rows.append(extract(game))
        if len(rows) % 10 == 0 or len(rows) == len(cohort['games']):
            print(json.dumps(dict(extracted=len(rows), total=len(cohort['games']))), flush=True)
    out = dict(extracted_at_utc=datetime.now(timezone.utc).isoformat(), cohort_path=str(COHORT.resolve()),
               cohort_sha256=sha(cohort_raw), source_replays_verified=len(rows),
               engine_version='1.32.7', snapshot_steps=list(STEPS),
               own_observable_fields=['own farm money/tiles/land', 'own private shed/carried stock',
                                      'rival public farm money/tiles/land', 'shared shops/prices/inventory'],
               diagnostic_only_fields=['rival private shed', 'rival historical action requests'],
               rows=rows)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(dict(path=str(target), episodes=len(rows), losses=sum(r['result'] == 'loss' for r in rows))), flush=True)


if __name__ == '__main__':
    main()
