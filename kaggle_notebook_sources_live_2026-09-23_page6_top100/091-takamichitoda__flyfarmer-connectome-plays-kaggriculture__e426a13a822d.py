import os, sys, json, shutil, time, collections
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

import glob
hits = glob.glob("/kaggle/input/**/neurons.csv", recursive=True)
DATA = os.path.dirname(hits[0]) if hits else os.path.abspath(os.path.join(os.getcwd(), "..", "dataset"))  # fallback for local runs
print("DATA =", DATA)
sys.path.insert(0, DATA)
os.environ["FLY_WEIGHTS"] = os.path.join(DATA, "brain_weights.npz")

# Official evaluation uses kaggle-environments==1.32.7; the Kaggle image may ship an older one, so pin it
import importlib.metadata as im
try:
    ver = im.version("kaggle-environments")
except im.PackageNotFoundError:
    ver = None
if ver != "1.32.7":
    print("pinning kaggle-environments 1.32.7 (was", ver, ")")
    os.system(f"{sys.executable} -m pip install -q kaggle-environments==1.32.7")
import kaggle_environments
from kaggle_environments import make
print("kaggle_environments", kaggle_environments.__version__)

from IPython.display import Video, Image, display
mp4 = os.path.join(DATA, "flyfarmer.mp4")
if os.path.exists(mp4):
    display(Video(mp4, embed=True, width=960, html_attributes="controls autoplay loop muted"))
else:
    print("video not found in", DATA)

# Still frame at the moment the escape reflex (Giant Fiber) fires
still = os.path.join(DATA, "flyfarmer_escape.png")
display(Image(still, width=960)) if os.path.exists(still) else None

neurons = pd.read_csv(f"{DATA}/neurons.csv"); edges = pd.read_csv(f"{DATA}/edges.csv")
meta = json.load(open(f"{DATA}/meta.json"))
print(f"{len(neurons)} neurons, {len(edges)} edges  (dataset: {meta['dataset']}, extracted {meta['extracted_at']})")
display(neurons.groupby(["role", "somaSide"]).size().unstack(fill_value=0))
display(neurons.groupby("role").consensusNt.value_counts().unstack(fill_value=0))
print("descending types:", sorted(neurons[neurons.role=="descending"].type.unique()))

import main
brain = main.FlyBrain()
print("W shape", brain.W.shape, " nnz", np.count_nonzero(brain.W),
      " excitatory", int((brain.W>0).sum()), " inhibitory", int((brain.W<0).sum()))

# Pure stimulus response: drive left only / right only / looming for 60 steps and watch L/R descending activity
fig, axes = plt.subplots(1, 3, figsize=(13, 3.2), sharey=True)
for ax, (name, stim) in zip(axes, {"LEFT": (1,0,0), "RIGHT": (0,1,0), "LOOMING": (0,0,1)}.items()):
    b = main.FlyBrain(steps_per_turn=1); L, R = [], []
    for _ in range(60):
        b.step(*stim); ro = b.readout(); L.append(ro["L"]); R.append(ro["R"])
    ax.plot(L, color="#2a78d6", lw=2, label="DN left"); ax.plot(R, color="#eb6834", lw=2, label="DN right")
    ax.set_title(f"stimulus = {name}"); ax.set_xlabel("sim step"); ax.grid(alpha=.2)
axes[0].set_ylabel("descending activity"); axes[0].legend(frameon=False)
plt.tight_layout(); plt.show()

trace = []
brain = main.FlyBrain()
env = make("kaggriculture", configuration={"seed": 17})
t0 = time.time(); env.run([main.make_agent(brain, trace), "starter"])
last = env.steps[-1]
print(f"FlyFarmer {last[0].observation['farms'][0]['money']:.0f}  vs  starter {last[1].observation['farms'][1]['money']:.0f}   ({time.time()-t0:.1f}s, errors={sum(s[0].status=='ERROR' for s in env.steps)})")
tr = pd.DataFrame(trace)
print("sell turns", int(tr.sell.sum()), " escape turns", int(tr.escape.sum()))
print("crop choice:", tr.crop.value_counts().to_dict())

fig, axes = plt.subplots(4, 1, figsize=(13, 9), sharex=True)
axes[0].plot(tr.step, tr.left,  color="#2a78d6", lw=1.5, label="left visual field (farm chores)")
axes[0].plot(tr.step, tr.right, color="#eb6834", lw=1.5, label="right visual field (market)")
axes[0].plot(tr.step, tr.looming, color="#eda100", lw=1.5, label="looming (weeds, money gap)")
axes[0].set_ylabel("stimulus"); axes[0].legend(frameon=False, ncol=3, loc="upper right")
axes[1].plot(tr.step, tr.L, color="#2a78d6", lw=1.5, label="DN left"); axes[1].plot(tr.step, tr.R, color="#eb6834", lw=1.5, label="DN right")
axes[1].plot(tr.step, tr.gf, color="#1baf7a", lw=1.5, label="DNp01 Giant Fiber")
axes[1].set_ylabel("descending"); axes[1].legend(frameon=False, ncol=3, loc="upper right")
axes[2].fill_between(tr.step, 0, tr.sell.astype(int), color="#eb6834", alpha=.5, step="mid", label="SELL mode")
axes[2].fill_between(tr.step, 0, tr.escape.astype(int)*0.5, color="#eda100", alpha=.8, step="mid", label="escape reflex")
axes[2].set_ylabel("decision"); axes[2].set_yticks([]); axes[2].legend(frameon=False, ncol=2, loc="upper right")
axes[3].plot(tr.step, tr.money, color="#1baf7a", lw=2); axes[3].set_ylabel("bank"); axes[3].set_xlabel("turn (24 / day)")
for ax in axes: ax.grid(alpha=.2)
for d in range(0, 720, 24*5): axes[3].axvline(d, color="gray", lw=.5, alpha=.4)
plt.tight_layout(); plt.show()

res = pd.DataFrame(json.load(open(f"{DATA}/results.json")))
res["sell_frac"] = res.sell_turns/720; res["escape_frac"] = res.escape_turns/720
summary = res.groupby("variant").agg(bank=("me","mean"), bank_sd=("me","std"), win=("win","mean"),
                                     sell_frac=("sell_frac","mean"), escape_frac=("escape_frac","mean")).round(2)
order = ["connectome","shuffled_w","silence_DNp01","silence_all_DN","nobrain_sell","nobrain_hoard"]
summary = summary.loc[order]
display(summary)
display(res.pivot_table(index="variant", columns="opponent", values="me", aggfunc="mean").loc[order].round(0))

fig, ax = plt.subplots(figsize=(9, 3.6))
y = np.arange(len(order))
ax.barh(y, summary.bank, xerr=summary.bank_sd, color=["#2a78d6" if v=="connectome" else "#9aa3ad" for v in order], height=.6, capsize=3)
ax.set_yticks(y); ax.set_yticklabels(order); ax.invert_yaxis(); ax.set_xlabel("final bank (mean ± sd over 36 games)")
for i, v in enumerate(summary.bank): ax.text(v + 150, i, f"{v:,.0f}", va="center", fontsize=9)
ax.grid(axis="x", alpha=.2); ax.spines[["top","right"]].set_visible(False)
plt.tight_layout(); plt.show()

OUT = "/kaggle/working" if os.path.exists("/kaggle/working") else "."
for f in ["main.py", "brain_weights.npz"]:
    shutil.copy(f"{DATA}/{f}", os.path.join(OUT, f))
os.system(f"cd {OUT} && tar -czf submission.tar.gz main.py brain_weights.npz && ls -la submission.tar.gz")

# Smoke test through the submission path (exec from file, both seats)
for seat in (0, 1):
    env = make("kaggriculture", configuration={"seed": 3})
    players = [os.path.join(OUT, "main.py"), "starter"] if seat == 0 else ["starter", os.path.join(OUT, "main.py")]
    env.run(players)
    me = env.steps[-1][seat].observation["farms"][seat]["money"]
    errs = sum(s[seat].status == "ERROR" for s in env.steps)
    print(f"seat {seat}: bank {me:.0f}, errors {errs}")