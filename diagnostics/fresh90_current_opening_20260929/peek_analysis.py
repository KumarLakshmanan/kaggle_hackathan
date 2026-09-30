import json
p='diagnostics/fresh90_current_opening_20260929/family_analysis.json'
d=json.load(open(p,encoding='utf-8'))
for i,f in enumerate(d['all_multi_tape_families'],1):
 print(i, 'ranks=',f['member_ranks'],'best=',f['best_rank'],'shared_until=',f['maximum_shared_prefix_checkpoint'],'shop_history=',f['shop_histories'])
print('top20 uniqueness documented?', 'top20' in d)
