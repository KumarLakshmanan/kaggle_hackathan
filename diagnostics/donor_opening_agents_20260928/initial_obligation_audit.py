"""Low-memory first-use and single-worker timing audit; no benchmark games."""
from collections import defaultdict
from pathlib import Path
import copy
import importlib.util
import json
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build import SOURCE,SOURCE_SHA,sha,read,write


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def obligations(actions):
    uses=defaultdict(list)
    for step,action in enumerate(actions[:24]):
        for worker,command in enumerate([action['farmer'],*action['hands']]):
            if len(command)>1 and command[0] in ('PICKUP','PLANT'):
                uses[command[0]+':'+command[1]].append(dict(step=step,worker=worker,quantity=command[2] if len(command)>2 else 1))
    return dict(first_action=actions[0],second_action=actions[1],first_day_uses=dict(uses))


def main():
    pool=read(HERE/'pool.json');assert sha(SOURCE)==SOURCE_SHA
    source=module(SOURCE,'static_source_obligations')
    data={'source':obligations(source._DATA['opening'])}
    for version,arm in pool['arms'].items():
        assert sha(arm['candidate'])==arm['candidate_sha256']
        mod=module(arm['candidate'],'static_'+version);actions=mod._DONOR_ROUTES[mod._DONOR_DEFAULT]
        data[version]=obligations(actions)
        if version=='shared151':donor151=mod; donor151_actions=actions
    spawn=source._QUEUE_ENGINE['_spawn_hand']
    early=dict(farmer=[4,4],hands=[])
    for _ in range(4):early['hands'].append(spawn(early,10))
    source_positions=copy.deepcopy(early['hands'])
    donor151_positions=copy.deepcopy(early);donor151_positions['hands'].append(spawn(donor151_positions,10))
    early['farmer']=[4,3];early['hands'].append(spawn(early,10))
    normal=dict(farmer=[4,3],hands=[])
    for _ in range(5):normal['hands'].append(spawn(normal,10))
    unused=list(range(5));mapping=[]
    for pos in normal['hands']:
        index=next(i for i in unused if early['hands'][i]==pos);unused.remove(index);mapping.append(index+1)
    assert mapping==[4,1,2,3,5]
    farm={'farmer':[4,4],'hands':copy.deepcopy(donor151_positions['hands']),'tiles':[[None for _ in range(10)] for _ in range(10)],'unlocked_quadrants':['NW'],'money':3000}
    private={'shed':{'SHEEP':1,'WHEAT':1},'seeds':{},'inventories':[{} for _ in range(6)]}
    old_farm,old_private=copy.deepcopy(farm),copy.deepcopy(private)
    new_farm,new_private=copy.deepcopy(farm),copy.deepcopy(private)
    apply=source._PLANT_CORE['_apply_unit_action'];rows=[]
    for step in range(1,9):
        old=donor151_actions[step]['hands'][4]
        new=['PASS'] if step==1 else donor151_actions[step-1]['hands'][4]
        apply(old_farm,old_private,5,old,10,0,24,100)
        apply(new_farm,new_private,5,new,10,0,24,100)
        rows.append(dict(step=step,original=old,delayed=new,original_position=copy.deepcopy(old_farm['hands'][4]),delayed_position=copy.deepcopy(new_farm['hands'][4]),original_inventory=copy.deepcopy(old_private['inventories'][5]),delayed_inventory=copy.deepcopy(new_private['inventories'][5])))
    assert donor151_actions[8]['hands'][4]==['DROP']
    assert old_farm==new_farm and old_private==new_private
    result=dict(static_feasibility_only=True,benchmark_games_run=0,primitive_unit_action_calls=16,
                source_sha256=SOURCE_SHA,pool_sha256=sha(HERE/'pool.json'),helper_sha256=sha(__file__),
                obligations=data,
                source_four_hand_positions=source_positions,
                shared151_five_hand_positions=donor151_positions['hands'],
                shared150_166_original_positions=normal['hands'],
                shared150_166_early_four_plus_late_fifth_positions=early['hands'],
                donor_to_actual_hand_index_mapping=mapping,
                shared151_delayed_fifth_hand=dict(rows=rows,end_of_step8_farm_private_equal=True,
                    omitted_original_command='DROP at8, with an empty inventory',
                    limitation='Isolated unit timing comparison assumes the fifth hand spawns at the verified cell, the third sheep is funded by market1, and its wheat is available. Other units, market funding, crop RNG and complete games were not simulated.'),
                conclusion='A common purchase of two cows/two sheep/four hands and deferred seeds has a physically coherent path to all four openings only with explicit branch procurement, donor hand permutation and shared151 fifth-hand catch-up. Economic feasibility against reacting opponents remains unproven.')
    output=HERE/'initial_obligations.json';assert not output.exists();write(output,result)
    print('Verified hand permutation',mapping,'and delayed fifth-hand exact state at end8; no benchmark games')


if __name__=='__main__':main()
