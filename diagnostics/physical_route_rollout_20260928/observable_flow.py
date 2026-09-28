"""Past net trade from legal observations; no rival private state or actions."""
import copy
from . import native_core as core


def post_worker_private(observation, action, configuration):
    """Apply our known physical commands up to (but excluding) the market."""
    player=int(observation['player'])
    farm=copy.deepcopy(observation['farms'][player])
    private=copy.deepcopy(observation['private'])
    units=[action.get('farmer',['PASS']),*action.get('hands',[])]
    demand={}
    for unit in units:
        if isinstance(unit,list) and len(unit)>=2 and unit[0]=='PLANT':
            demand[unit[1]]=demand.get(unit[1],0)+1
    blocked={crop for crop,count in demand.items() if count>private['seeds'].get(crop,0)}
    cfg=configuration or {}
    day=int(observation['step'])//int(cfg.get('turnsPerDay',24))
    for index,unit in enumerate(units):
        if isinstance(unit,list) and len(unit)>=2 and unit[0]=='PLANT' and unit[1] in blocked:
            unit=['PASS']
        core._apply_unit_action(farm,private,index,unit,int(cfg.get('boardSize',10)),day,
                               int(cfg.get('turnsPerDay',24)),int(cfg.get('shedCapacity',100)))
    return private


def infer_rival_net_sales(previous_observation, own_action, observation, configuration=None):
    cfg=configuration or {}
    step=int(previous_observation['step'])
    assert int(observation['step'])==step+1
    assert observation['player']==previous_observation['player']
    if (step+1)%int(cfg.get('turnsPerDay',24))==0:
        return None
    before_market=post_worker_private(previous_observation,own_action,cfg)['shed']
    consumption={item:0 for item in core.PRODUCTS}
    if step%max(1,int(cfg.get('townShopSellInterval',4)))==0:
        for shop in previous_observation['town']['unlocked_shops']:
            items=core.SHOPS[shop]
            for item in items:consumption[item]+=2 if len(items)==1 else 1
    if step%max(1,int(cfg.get('townCenterSellInterval',24)))==0:
        for item in core.TOWN_CENTER_PRODUCTS:consumption[item]+=1
    result={}
    old_market=previous_observation['market']
    for item in core.PRODUCTS:
        before=old_market['inventory'][item]
        after=observation['market']['inventory'][item]+consumption[item]
        upper=(before+before_market.get(item,0)+int(cfg.get('shedCapacity',100))
               if item in ('WHEAT','FERTILIZER') else max(before,after))
        if core.market_price(item,upper,old_market.get('params'))<=1:
            result[item]=None
        else:
            result[item]=after-before+observation['private']['shed'].get(item,0)-before_market.get(item,0)
    return result
