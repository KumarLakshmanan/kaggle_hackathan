"""Replay recorded actions into exact native transitions to attribute cash.

No policy calls, candidate variants, reacting outcomes or new strength games.
Every candidate-visible physical/market state must equal its stored trace.
"""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import copy
import gzip
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.check import Box, extract, state_from_frames
from diagnostics.animal_liquidity_20260928.screen import read, write, sha
from diagnostics.animal_liquidity_20260928.mechanism import traces


def replay(fixture, seat, trace_path, expected):
    frames = traces(trace_path)
    original = json.loads(gzip.decompress(Path(fixture['source_replay_path']).read_bytes()))
    state = state_from_frames(original['steps'][0])
    env = Box(configuration=Box(**dict(original['configuration'], seed=None)), info={'seed':int(fixture['seed'])}, done=False)
    del original
    tape = json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    core, provenance = extract()
    commit, hire, land = core['_commit_unit'], core['_do_hire'], core['_do_buy_land']
    records = []
    current_step = 0

    def append(farm, op, item, quantity, delta):
        player = 0 if farm is state[0].observation.farms[0] else 1
        records.append(dict(step=current_step, player=player, role='own' if player==seat else 'rival',
                            operation=op, item=item, quantity=quantity, cash_delta=delta))

    def counted_commit(op,item,price,farm,private,market,shed_capacity=100):
        before = farm['money']
        success = commit(op,item,price,farm,private,market,shed_capacity)
        if success:
            append(farm,op,item,1,farm['money']-before)
        return success

    def counted_hire(farm,private,board_size,mult=1):
        before = farm['money']
        result = hire(farm,private,board_size,mult)
        if farm['money'] != before:
            append(farm,'HIRE','HAND',1,farm['money']-before)
        return result

    def counted_land(farm,board_size):
        before = farm['money']
        result = land(farm,board_size)
        if farm['money'] != before:
            append(farm,'BUY_LAND','LAND',1,farm['money']-before)
        return result

    core['_commit_unit'],core['_do_hire'],core['_do_buy_land'] = counted_commit,counted_hire,counted_land
    initial = [farm['money'] for farm in state[0].observation.farms]
    for current_step, frame in enumerate(frames):
        obs = state[seat].observation
        assert frame['step'] == current_step
        for name in ('farms','market','town','private','step','day','hour'):
            assert obs[name] == frame['observation'][name], (current_step,name)
        state[seat].action = copy.deepcopy(frame['action'])
        state[1-seat].action = copy.deepcopy(tape[current_step])
        core['interpreter'](state,env)
        for item in state:
            item.observation.step = current_step+1
    own,rival = state[seat].reward,state[1-seat].reward
    assert own == expected['candidate_reward'] and rival == expected['opponent_reward']
    summary = defaultdict(lambda:dict(quantity=0,cash_delta=0.))
    for item in records:
        key = '|'.join((item['role'],item['operation'],item['item']))
        summary[key]['quantity'] += item['quantity']
        summary[key]['cash_delta'] += item['cash_delta']
    for player in (0,1):
        assert initial[player] + sum(r['cash_delta'] for r in records if r['player']==player) == state[player].reward
    return dict(seat=seat, source_trace_sha256=sha(trace_path), own=own,rival=rival,
                complete_state_matches=719, summary=dict(sorted(summary.items())), ledger=records, provenance=provenance)


def main():
    pool = read(HERE/'pool.json');screen=read(HERE/'screen.json')
    fixture=pool['fixtures'][0]
    rows=[]
    for seat in (0,1):
        parent_path=ROOT/'diagnostics/observed_hire_recovery_20260928'/('integrated_live-114283577_seat'+str(seat)+'.jsonl.gz')
        candidate_path=HERE/('live-114283577_seat'+str(seat)+'.jsonl.gz')
        parent=next(r for r in pool['controls'] if r['rival']==fixture['fixture_id'] and r['candidate_seat']==seat)
        current=next(r for r in screen['games'] if r['fixture_id']==fixture['fixture_id'] and r['candidate_seat']==seat)
        old=replay(fixture,seat,parent_path,parent)
        new=replay(fixture,seat,candidate_path,current)
        changes={}
        for key in sorted(set(old['summary'])|set(new['summary'])):
            a=old['summary'].get(key,dict(quantity=0,cash_delta=0.))
            b=new['summary'].get(key,dict(quantity=0,cash_delta=0.))
            if a != b:
                changes[key]=dict(old=a,new=b,delta_quantity=b['quantity']-a['quantity'],delta_cash=b['cash_delta']-a['cash_delta'])
        rows.append(dict(seat=seat,parent=old,candidate=new,changes=changes))
    result=dict(recorded_action_replay_only=True,passed=True,games=rows,
                screen_sha256=sha(HERE/'screen.json'),helper_sha256=sha(__file__),
                completed_at_utc=datetime.now(timezone.utc).isoformat())
    write(HERE/'trade_ledger.json',result)
    print(json.dumps([dict(seat=r['seat'],changes=r['changes']) for r in rows],indent=2))


if __name__=='__main__':
    main()
