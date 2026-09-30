import json
p='diagnostics/fresh90_leading_openings_20260930/static_day0_comparison.json'
d=json.load(open(p,encoding='utf-8'))
for row in d['records']:
    print(row['group'], 'rank',row['rank'], 'team',row.get('team'),'episode',row.get('episode_id'))
    print(' investment orders',row['day0']['investment_order_counts_by_type'])
    print(' investment units',row['day0']['investment_numeric_units_by_type_and_item'])
    print(' seed orders/units',row['day0']['seed_purchase_order_counts_by_crop'],row['day0']['seed_purchase_numeric_units_by_crop'])
    print(' plant commands',row['day0']['plant_command_counts_by_crop'])
    print(' all market order counts',row['day0']['market_order_counts_by_type'])
