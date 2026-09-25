import json

# Sixteen public episodes: the rating of the agent they were recorded from, and the mean
# money difference against a fixed base tape over 4,000 games each.
RESULTS = json.loads('''[
 {
  "rating": 3074,
  "episode": 105654650,
  "diff": -22714.2
 },
 {
  "rating": 3074,
  "episode": 105664019,
  "diff": -25046.9
 },
 {
  "rating": 3040,
  "episode": 105384058,
  "diff": -28478.8
 },
 {
  "rating": 3039,
  "episode": 105534760,
  "diff": -29784.6
 },
 {
  "rating": 3006,
  "episode": 104682897,
  "diff": -41250.1
 },
 {
  "rating": 3005,
  "episode": 105491250,
  "diff": -4501.8
 },
 {
  "rating": 3003,
  "episode": 105623078,
  "diff": -4237.5
 },
 {
  "rating": 3003,
  "episode": 104680858,
  "diff": -85931.6
 },
 {
  "rating": 2998,
  "episode": 105423461,
  "diff": -23916.1
 },
 {
  "rating": 2993,
  "episode": 105423466,
  "diff": -16258.8
 },
 {
  "rating": 2983,
  "episode": 105433879,
  "diff": -1656.5
 },
 {
  "rating": 2982,
  "episode": 105423464,
  "diff": 1995.8
 },
 {
  "rating": 2977,
  "episode": 105119866,
  "diff": 13.4
 },
 {
  "rating": 2977,
  "episode": 105391568,
  "diff": -2990.0
 },
 {
  "rating": 2974,
  "episode": 104665310,
  "diff": -25884.2
 },
 {
  "rating": 2970,
  "episode": 104663138,
  "diff": -23889.7
 }
]''')

print(f"{'source rating':>13}  {'episode':>10}  {'mean money vs base':>19}")
for r in RESULTS:
    mark = '  <-- winner' if r['diff'] > 1000 else ''
    print(f"{r['rating']:>13}  {r['episode']:>10}  {r['diff']:>19,.0f}{mark}")

neg = sum(1 for r in RESULTS if r['diff'] < 0)
print(f"\nnegative: {neg} of {len(RESULTS)}")

def spearman(xs, ys):
    def ranked(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        out = [0] * len(v)
        for pos, i in enumerate(order):
            out[i] = pos + 1
        return out
    rx, ry = ranked(xs), ranked(ys)
    n = len(xs)
    mean = lambda v: sum(v) / len(v)
    cov = sum((rx[i] - mean(rx)) * (ry[i] - mean(ry)) for i in range(n))
    var = (sum((v - mean(rx)) ** 2 for v in rx) * sum((v - mean(ry)) ** 2 for v in ry)) ** 0.5
    return cov / var

ratings = [r['rating'] for r in RESULTS]
diffs = [r['diff'] for r in RESULTS]
print('Spearman rho between source rating and replay strength:', round(spearman(ratings, diffs), 3))

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7.5, 4.2))
colors = ['#0369a1' if d > 0 else '#94a3b8' for d in diffs]
ax.scatter(ratings, [d / 1000 for d in diffs], c=colors, s=70, zorder=3)
ax.axhline(0, color='#334155', linewidth=1)
ax.set_xlabel('rating of the agent the tape was recorded from')
ax.set_ylabel('mean money vs base, thousands')
ax.set_title('Higher-rated source, worse replay')
for spine in ('top', 'right'):
    ax.spines[spine].set_visible(False)
ax.grid(axis='y', alpha=0.25, zorder=0)
plt.tight_layout()
plt.show()