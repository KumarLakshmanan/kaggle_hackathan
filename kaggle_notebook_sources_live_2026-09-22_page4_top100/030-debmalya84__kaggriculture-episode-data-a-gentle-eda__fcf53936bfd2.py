import glob, json, os, random
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

# Auto-discover whatever episode dataset is attached (no hardcoded
# dates, so this keeps working as the daily datasets roll).
def episode_files():
    hits = []
    for root in glob.glob('/kaggle/input/*'):
        js = glob.glob(os.path.join(root, '**', '*.json'), recursive=True)
        hits += [p for p in js if os.path.basename(p)[:-5].isdigit()]
    return sorted(set(hits))

FILES = episode_files()
print(f'{len(FILES)} episode replays found across attached datasets')
if not FILES:
    print('No episode files attached. Add a kaggriculture-episodes-<date>',
          'dataset via Add Input -> Datasets, then re-run.')
random.seed(0)
SAMPLE = random.sample(FILES, min(60, len(FILES)))


def load(p):
    with open(p) as f: return json.load(f)

def final_banks(r):
    last = (r.get('steps') or [[]])[-1]
    return [s.get('reward') or 0 for s in last]

if FILES:
    ex = load(FILES[0])
    print('steps:', len(ex.get('steps') or []))
    print('final banks:', final_banks(ex))
    obs0 = ex['steps'][1][0]['observation']
    print('observation keys:', list(obs0.keys()))
    print('market products:', list((obs0.get('market') or {}).get('prices', {}).keys()))


banks = []
for p in SAMPLE:
    try:
        b = final_banks(load(p))
        if len(b) == 2: banks.append(b)
    except Exception: pass
banks = np.array(banks) if banks else np.zeros((0,2))
if len(banks):
    plt.figure(figsize=(8,3))
    plt.hist(banks.flatten(), bins=30, color='#4C78A8')
    plt.xlabel('final bank'); plt.ylabel('players')
    plt.title(f'Final-bank distribution ({len(banks)} games)')
    plt.tight_layout(); plt.show()
    print(f'median {np.median(banks):,.0f}, top decile {np.percentile(banks,90):,.0f}')


PRODUCTS = ['STRAWBERRY','MELON','MILK','WOOL','WHEAT']
def price_trace(p):
    r = load(p); out = {k: [] for k in PRODUCTS}
    for s in r['steps'][::24]:
        pr = (s[0].get('observation') or {}).get('market', {}).get('prices', {})
        for k in PRODUCTS: out[k].append(pr.get(k, np.nan))
    return out

agg = {k: [] for k in PRODUCTS}
for p in SAMPLE[:30]:
    try:
        tr = price_trace(p)
        for k in PRODUCTS:
            if len(tr[k]) >= 30: agg[k].append(tr[k][:30])
    except Exception: pass
plt.figure(figsize=(9,4))
for k in PRODUCTS:
    if agg[k]: plt.plot(np.nanmean(agg[k], axis=0), label=k)
plt.legend(); plt.xlabel('day'); plt.ylabel('mean price')
plt.title('Average market price by day'); plt.tight_layout(); plt.show()


vol = np.zeros(30)
for p in SAMPLE:
    try:
        r = load(p)
        for i in range(1, len(r['steps'])):
            day = i // 24
            if day >= 30: break
            for seat in (0,1):
                for o in (r['steps'][i][seat].get('action') or {}).get('market', []):
                    if isinstance(o, list) and len(o) >= 3 and o[0]=='SELL':
                        vol[day] += max(0, int(o[2] or 0))
    except Exception: pass
plt.figure(figsize=(9,3))
plt.bar(range(30), vol, color='#54A24B')
plt.xlabel('day'); plt.ylabel('total units sold (sample)')
plt.title('Sell volume by day (all players, sampled)')
plt.tight_layout(); plt.show()


from collections import defaultdict
by_dir = defaultdict(list)
for p in FILES: by_dir[os.path.basename(os.path.dirname(p))].append(p)
days = sorted(by_dir)
print('attached day-datasets:', days)
if len(days) >= 2:
    plt.figure(figsize=(9,4))
    for d in days[:2]:
        tr = []
        for p in by_dir[d][:20]:
            try:
                t = price_trace(p)['STRAWBERRY']
                if len(t) >= 29: tr.append(t[:29])
            except Exception: pass
        if tr: plt.plot(np.nanmean(tr, axis=0), label=d)
    plt.legend(); plt.xlabel('day'); plt.ylabel('mean STRAWBERRY price')
    plt.title('Strawberry price by day, per attached dataset')
    plt.tight_layout(); plt.show()
else:
    print('Attach a second day-dataset to compare eras.')
