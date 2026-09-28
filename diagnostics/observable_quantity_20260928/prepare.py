"""Make the separate quantity experiment; preserve the rejected order study."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'observable_queue_20260928'
source=(PREVIOUS/'layer.py').read_text(encoding='utf-8')
assert hashlib.sha256((PREVIOUS/'layer.py').read_bytes()).hexdigest()=='5ee1f476c593f22519a1367b2e59e87b7cc3bb6cc3f747c29989ae493f5e4c11'
start=source.index('    proposals, seen = [],')
end=source.index('    if not proposals:',start)
replacement='''    proposals = []
    for item in ("WHEAT", "FERTILIZER"):
        buys = [i for i,o in enumerate(orders) if len(o)>=3 and o[:2]==["BUY_PRODUCT",item] and o[2]>0]
        sells = [i for i,o in enumerate(orders) if len(o)>=3 and o[:2]==["SELL",item] and o[2]>0]
        if not buys or not sells:
            continue
        bi, si = buys[0], sells[0]
        for delta in (4,12,24,-4,-12,-24):
            if min(orders[bi][2],orders[si][2])+delta<1 or max(orders[bi][2],orders[si][2])+delta>100:
                continue
            proposed = [list(o) for o in orders]
            proposed[bi][2] += delta
            proposed[si][2] += delta
            proposals.append(proposed)
'''
source=source[:start]+replacement+source[end:]
source=source.replace('_flow_reorder','_flow_quantity').replace('kaggle_observable_queue_entrypoint','kaggle_observable_quantity_entrypoint')
source=source.replace('Reorder current orders with uncertainty over observable past rival flow.',
                      'Compare balanced quantities with uncertainty over observable past rival flow.')
assert not (HERE/'layer.py').exists()
compile(source,str(HERE/'layer.py'),'exec')
(HERE/'layer.py').write_text(source,encoding='utf-8')
for name in ('build.py','screen.py'):
    target=HERE/name
    assert not target.exists()
    target.write_bytes((PREVIOUS/name).read_bytes())
(HERE/'source_provenance.json').write_text(json.dumps(dict(
    source_layer_sha256=hashlib.sha256((PREVIOUS/'layer.py').read_bytes()).hexdigest(),
    change='Replace only proposal generator with frozen balanced quantity deltas; same forecasts and guards.',
    resulting_layer_sha256=hashlib.sha256((HERE/'layer.py').read_bytes()).hexdigest()),indent=2),encoding='utf-8')
print('Quantity layer prepared; rejected reorder layer unchanged.')
