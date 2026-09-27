# Can public history predict the next strawberry sale race? Frozen 2026-09-26 19:17 UTC

The simple latched stock sale failed reactive promotion. Exact Haide traces
show the causal distinction: frontloading helps if the rival sells before
our scheduled sale, but can hurt own cash if our scheduled sale would have
come first at a better quote. The rival's future orders and private shed are
unavailable to a live agent. Before making another policy candidate, test
whether public observation history contains a useful signal.

Use the current submission's 100 downloaded **live public replays**. Freeze
the prior 29-loss plus ten-close-win cohort as development episodes and the
other 61 as an episode-disjoint diagnostic holdout. From each replay, collect
at most one opportunity per observed own strawberry-stock batch: from step
480 onward, after 24 consecutive observed physical-mirror turns since step
144, the farms' tiles differ but farmer/hands positions still match, shed
stock is at least four, current visible strawberry quote is at least 60,
and incumbent action has no strawberry SELL, BUY_PRODUCT or strawberry
PICKUP and fewer than ten market orders. Rearm only after own stock falls
below four or an own strawberry sale. This matches the rejected candidate's
decision boundary without firing repeated correlated turns from one batch.

Label whether the **actual rival** sells strawberry before our next sale
within the next 24 turns. The label uses future replay actions only during
offline analysis. Features must be available to a live agent at that turn:
step/hour, observed stock and quote, 1/4/12-turn public quote changes,
1/4-turn public inventory changes, time since our own last strawberry sale,
time since a positive public inventory jump, public strawberry plant counts,
hands count, unlocked strawberry-demand shop count, and current order count.
No rival private shed, episode ID, seed, team, future shop or future action
may enter a feature.

Fit one fixed L2 logistic classifier on the development episodes only,
standardizing features from training statistics. Evaluate once on the other
61 episodes. Require at least 20 positive holdout opportunities, holdout
pairwise AUC at least 0.70, and precision among the top predicted quartile
at least 1.4 times the holdout base prevalence to justify a policy test.
Otherwise reject this predictor path for now. Even a pass is **predictive
diagnosis only**; a new candidate would still need native both-seat,
original-shop, reactive and top-100 regression testing. No `main.py`
edit or Kaggle upload is authorized.
