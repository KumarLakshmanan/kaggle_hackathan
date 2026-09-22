# The Market, End to End — setup. Works on Kaggle with Internet ON (first run upgrades the engine).
import contextlib, io, subprocess, sys
from importlib import metadata
def _ok():
    try: return tuple(int(x) for x in metadata.version("kaggle-environments").split(".")[:3]) >= (1,32,4)
    except Exception: return False
if not _ok():
    subprocess.run([sys.executable,"-m","pip","install","-q","--progress-bar","off","-U",
                    "kaggle-environments>=1.32.4"], check=True, capture_output=True)
import numpy as np, matplotlib.pyplot as plt
import logging; logging.disable(logging.INFO)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments.envs.kaggriculture.kaggriculture import (
        MARKET_PARAMS, MARKET_I0, market_price, PRODUCTS, SHOPS, TOWN_CENTER_DEMAND_SCHEDULE)
logging.disable(logging.NOTSET)

# Warm-paper theme (calm background, recessive grid, one warm accent per product).
PAGE, SURF = "#f7f7f3", "#fcfcfb"; INK, INK2, MUTE = "#14140f", "#52514e", "#8a8880"
GRID, AXIS, WARN = "#e6e5dd", "#c3c2b7", "#d03b3b"
PROD_C = {"STRAWBERRY":"#2a78d6","MILK":"#eb6834","WOOL":"#1baf7a","MELON":"#eda100",
          "WHEAT":"#4a3aa7","CARROT":"#e34948","TOMATO":"#008300","EGG":"#8a8880","FERTILIZER":"#e87ba4"}
plt.rcParams.update({"figure.dpi":120,"font.size":11,"font.family":"DejaVu Sans",
    "axes.titlesize":12.5,"axes.titleweight":"bold","axes.titlecolor":INK,"text.color":INK,
    "axes.labelcolor":INK2,"axes.labelsize":10.5,"xtick.color":MUTE,"ytick.color":MUTE,
    "xtick.labelsize":9.5,"ytick.labelsize":9.5,"axes.spines.top":False,"axes.spines.right":False,
    "axes.edgecolor":AXIS,"axes.linewidth":1.0,"figure.facecolor":PAGE,"axes.facecolor":SURF,
    "axes.grid":True,"grid.color":GRID,"grid.linewidth":1.0,"grid.alpha":1.0})
TPD, SHOP_INT, CENTER_INT = 24, 4, 12   # engine defaults: 24 turns/day, shop every 4, town-centre every 12

def shop_demand_pd():
    d = {p:0 for p in PRODUCTS}
    for shop, prods in SHOPS.items():
        mult = 2 if len(prods)==1 else 1          # single-product shops consume 2x
        for p in prods: d[p] += mult*(TPD//SHOP_INT)
    return d
def center_amount(day):
    for thr, amt in TOWN_CENTER_DEMAND_SCHEDULE:
        if day >= thr: return amt
    return 0
def total_demand_pd(day):
    s = shop_demand_pd()
    return {p: s[p] + (center_amount(day)*(TPD//CENTER_INT) if p!="FERTILIZER" else 0) for p in PRODUCTS}

ORDER = ["MELON","WOOL","MILK","STRAWBERRY","FERTILIZER","TOMATO","CARROT","EGG","WHEAT"]
def spread_labels(ax, items_y, x, dx=0, gap=None):        # anti-collision for right-edge direct labels
    ylim = ax.get_ylim(); gap = gap or (ylim[1]-ylim[0])*0.052
    items_y = sorted(items_y, key=lambda t: t[0])
    for i in range(1,len(items_y)):
        if items_y[i][0]-items_y[i-1][0] < gap:
            items_y[i] = (items_y[i-1][0]+gap, items_y[i][1], items_y[i][2])
    for y,name,c in items_y: ax.text(x+dx, y, name, color=c, fontsize=9, va="center", weight="bold")
print("engine ready — market params for", len(PRODUCTS), "resources loaded")

# Section 1 — the price function, dissected
fig,(axA,axB) = plt.subplots(1,2,figsize=(11,4.0))
x = np.linspace(0,1,200)
shapes = {"log":np.log1p(x*9)/np.log1p(9), "sqrt":np.sqrt(x), "linear":x, "sq":x**2}
sh_c = {"log":"#1baf7a","sqrt":"#2a78d6","linear":MUTE,"sq":WARN}
lbl_y = {"log":0.96,"sqrt":0.82,"linear":0.55,"sq":0.20}
for name,y in shapes.items():
    axA.plot(x,y,lw=2.6,color=sh_c[name])
    axA.text(1.02,lbl_y[name],name,color=sh_c[name],fontsize=11,va="center",weight="bold")
axA.set_title("Vocabulary: how each shape bends"); axA.set_xlim(0,1.18); axA.set_ylim(0,1.02)
axA.set_xlabel("distance from resting inventory  (0 \u2192 T)"); axA.set_ylabel("share of the target move")
span = np.arange(-320,321,4); it="MELON"; p=MARKET_PARAMS[it]
axB.plot(span,[market_price(it,MARKET_I0+int(d)) for d in span],lw=2.6,color=PROD_C[it])
axB.axvline(0,color=AXIS,lw=1.0); axB.axhline(p["base"],color=MUTE,lw=.8,ls=":")
axB.axhline(1,color=WARN,lw=1.0,ls=(0,(4,4)),alpha=.6)
axB.text(-300,p["base"]+8,f"below I0: '{p['below_func']}' \u2192 gentle rise (scarcity)",fontsize=9,color=INK2)
axB.text(15,42,f"above I0: '{p['above_func']}' \u2192 hard crash (glut)",fontsize=9,color=WARN,weight="bold")
axB.text(-312,6,"$1 floor",fontsize=8,color=WARN,alpha=.8)
axB.set_title(f"One curve, two rules \u2014 {it.title()} (base ${p['base']})")
axB.set_xlabel("units net-sold into market  (0 = resting I0)"); axB.set_ylabel("price $")
fig.suptitle("Anatomy of the price function:  price(inv) = base \u00b1 amp\u00b7shape(|inv \u2212 I0|)",fontsize=13,weight="bold")
fig.tight_layout(rect=[0,0,1,0.94]); plt.show()

# Section 1b — the whole family: how each market crashes
fig,ax = plt.subplots(figsize=(10,5.2)); N=180; ks=np.arange(0,N+1); labs=[]
for it in ORDER:
    ys=[market_price(it,MARKET_I0+int(k)) for k in ks]
    ax.plot(ks,ys,lw=2.4,color=PROD_C[it]); labs.append((ys[-1], it.title(), PROD_C[it]))
ax.axhline(1,color=WARN,lw=1.0,ls=(0,(4,4)),alpha=.6); ax.text(N-2,6,"$1 floor",color=WARN,fontsize=8,ha="right",alpha=.8)
ax.set_xlim(0,N+15); ax.set_ylim(0,260); spread_labels(ax,labs,N,dx=2)
ax.set_title("How each market crashes: price of the k-th unit sold in one go")
ax.set_xlabel("units sold in one go (from resting I0)"); ax.set_ylabel("price of that unit, $")
fig.tight_layout(); plt.show()

# Section 1b — both sides, normalized (scarcity vs glut on one scale)
fig,ax = plt.subplots(figsize=(10,5.2)); XMIN,XMAX=-150,180; offs=np.arange(XMIN,XMAX+1,2); labs=[]
for it in ORDER:
    base=MARKET_PARAMS[it]["base"]
    ys=[market_price(it,MARKET_I0+int(o))/base*100 for o in offs]
    ax.plot(offs,ys,lw=2.2,color=PROD_C[it]); labs.append((ys[-1], it.title(), PROD_C[it]))
ax.axvline(0,color=AXIS,lw=1.1); ax.axhline(100,color=MUTE,lw=.8,ls=":")
ax.text(3,6,"I0 (base = 100%)",color=MUTE,fontsize=8)
ax.set_xlim(XMIN,XMAX+34); ax.set_ylim(0,220); spread_labels(ax,labs,XMAX,dx=3)
ax.set_title("Both sides, normalized: scarcity lifts price, glut crashes it")
ax.set_xlabel("◄ scarcity        inventory offset from I0        glut ►"); ax.set_ylabel("price, % of base")
fig.tight_layout(); plt.show()

# Section 2 — recovery: the town heals a glutted market
watch, day, DUMP, NDAYS = ["WOOL","MELON","STRAWBERRY","MILK"], 15, 100, 40
dem = total_demand_pd(day)
fig,axes = plt.subplots(2,2,figsize=(10.5,6.6),sharex=True)
for ax,it in zip(axes.flat,watch):
    base, drain = MARKET_PARAMS[it]["base"], max(1,total_demand_pd(day)[it])
    inv, series, rec = MARKET_I0+DUMP, [market_price(it,MARKET_I0+DUMP)], None
    for d in range(1,NDAYS+1):
        inv = max(MARKET_I0, inv-drain); series.append(market_price(it,inv))
        if rec is None and series[-1] >= base-1: rec = d
    ax.plot(range(len(series)),series,lw=2.6,color=PROD_C[it]); ax.axhline(base,color=MUTE,lw=.7,ls=":")
    ax.fill_between(range(len(series)),series,base,color=PROD_C[it],alpha=.10)
    ax.set_title(f"{it.title()}  \u2014 town eats {drain}/day",fontsize=11,color=PROD_C[it])
    ax.text(.96,.08,(f"back to base in ~{rec} days" if rec else f"still glutted after {NDAYS} days"),
            transform=ax.transAxes,ha="right",fontsize=9.5,color=INK,weight="bold"); ax.set_xlim(0,NDAYS)
for ax in axes[:,0]: ax.set_ylabel("price $")
for ax in axes[-1]: ax.set_xlabel("days after dumping a full shed (100 units)")
fig.suptitle("Recovery: the town heals each market at a different speed (dump a full shed, mid-season)",fontsize=13,weight="bold")
fig.tight_layout(rect=[0,0,1,0.95]); plt.show()

# Section 3 — the buy-side, and the new shed-cap gate (1.32.4)
fig,(axA,axB) = plt.subplots(1,2,figsize=(11,4.0),gridspec_kw={"width_ratios":[1.25,1]})
span = np.arange(-400,401,5)
for it in ["WHEAT","FERTILIZER"]:
    ys=[market_price(it,MARKET_I0+int(d)) for d in span]; axA.plot(span,ys,lw=2.6,color=PROD_C[it])
    axA.text(span[0]-6, ys[0], it.title(), color=PROD_C[it],fontsize=9.5,va="center",ha="right",weight="bold")
axA.axvline(0,color=AXIS,lw=1.0); axA.set_xlim(-470,410)
axA.set_title("The buy-side: only WHEAT & FERTILIZER are buyable")
axA.set_xlabel("units net-sold into market"); axA.set_ylabel("price $")
axA.text(.5,-.22,"buy quoted post-buy, sell pre-sell \u2192 an immediate round-trip nets ~0",
         transform=axA.transAxes,ha="center",fontsize=9,color=MUTE)
axB.axis("off"); axB.add_patch(plt.Rectangle((0.05,0.32),0.9,0.48,fc="#f4f1ea",ec="#cfc8b8"))
for i in range(10): axB.add_patch(plt.Rectangle((0.08+i*0.086,0.36),0.078,0.40,fc="#C99700",ec="white"))
axB.text(0.5,0.87,"shed FULL (100/100)",ha="center",fontsize=12,weight="bold",color=INK)
axB.text(0.5,0.18,"1.32.4: BUY_PRODUCT / BUY_SEED \u2192 FAIL when the shed is full\n(you cannot stockpile feed at capacity \u2014 new this patch)",
         ha="center",fontsize=9.5,color="#C0392B")
axB.set_title("New engine gate (1.32.4)")
fig.tight_layout(); plt.show()

# Section 4 — season appetite: how much the town removes, per product
fig,ax = plt.subplots(figsize=(10,4.8)); days=list(range(0,30)); shopd=shop_demand_pd(); finals=[]
for it in PRODUCTS:
    if it=="FERTILIZER": continue
    cum=0; ys=[]
    for d in days: cum += shopd[it] + center_amount(d)*(TPD//CENTER_INT); ys.append(cum)
    lw = 2.8 if it in ("WHEAT","STRAWBERRY","MELON") else 1.8
    ax.plot(days,ys,lw=lw,color=PROD_C[it]); finals.append([ys[-1],it,PROD_C[it]])
finals.sort(); gap=45
for i in range(1,len(finals)):
    if finals[i][0]-finals[i-1][0] < gap: finals[i][0] = finals[i-1][0]+gap
for y,it,c in finals: ax.text(29.5,y,it.title(),color=c,fontsize=9.5,va="center",weight="bold")
for mark,lbl in ((10,"town \u00d72"),(20,"town \u00d74")):
    ax.axvline(mark,color="#b9ae95",lw=1.1,ls=":"); ax.text(mark+.2,ax.get_ylim()[1]*.03,lbl,fontsize=8.5,color=MUTE)
ax.text(1,ax.get_ylim()[1]*.9,"MELON has no shop \u2014 only the town centre eats it",fontsize=10,color=PROD_C["MELON"],weight="bold")
ax.set_title("Season appetite: cumulative town demand per product (full shop unlock)")
ax.set_xlabel("day"); ax.set_ylabel("cumulative units the town removes"); ax.set_xlim(0,34)
fig.tight_layout(); plt.show()