# Public physical-state rival-sale predictor — 2026-09-26

The earlier multi-product sale-race model used only product counts, cash,
price and inventory history and failed its 61-episode holdout AUC gate
(0.654 versus 0.70). This is a **new, prospective temporal test** of whether
public harvest readiness and worker positions add useful sale-timing signal.
The 100 completed games already used for that model become development data.
At the 20:25 UTC read-only episode listing, 19 IDs were absent from the old
audit, but three were older backfilled games. One further game completed
during collection. Before reading any new replay labels, freeze the **17
public IDs newer than the maximum old-audit episode ID (113772923)** from
the 20:27 UTC listing as the untouched temporal holdout. The three older
backfills are excluded. Save exact IDs and source hashes before reading
replay labels. No Kaggle submission is made.

Use the same one-per-own-stock-batch opportunity and label definition as the
earlier extractor: own shed stock ≥3, no same-item sale/buy/pickup action and
a free market slot, next recorded own sale within 24 turns; positive if the
rival sells the same item within 12 turns and before our next sale. Use
future actions **only for offline labels and opportunity selection**, never
as deployable features. The later policy would need to forecast its own sale
from its own tape.

Keep the earlier numeric features and product one-hot encoding. Add only
current public-state features: rival ready yield units/tiles for this item,
rival workers on its ready tiles, closest worker-to-ready-tile distance,
rival workers on any producer tile for this item, rival workers near the
central shed, and closest ready-tile-to-shed distance. All distances are
Manhattan and clipped at ten; absent ready tiles use ten. No rival private
inventory, episode ID, team name, seed, future shop, future action or replay
outcome is a model feature.

Before fitting, require at least 100 positive opportunities in the new
temporal holdout across at least 10 episodes and at least two products with
10 positives each. If this passes, fit exactly one L2 logistic model:
standardize numeric columns using the 100 development episodes only, clip
to [-5,5], item one-hot columns, bias, unweighted cross-entropy, ridge 0.01
excluding bias, full-batch Adam 1,000 steps at learning rate 0.05. Require
holdout AUC ≥0.70 and top-quartile precision ≥1.4 times holdout prevalence.
Only a passing predictor earns an isolated action-rule design and native
both-seat/original-shop/reactive testing. It cannot by itself justify a
`main.py` edit or Kaggle upload.

## Frozen action pilot after the predictive gate passed

The held-out AUC was 0.835 and top-quartile lift 2.889, meeting both model
gates. Development-only score diagnostics showed the strongest actionable
price signal for milk: among 100 old games, 34 opportunities had model
probability ≥0.30, at least three visible rival ready milk units, and a
modeled eight-unit post-rival receipt drop of at least 16 coins; 14 were
positive race events. Egg had nearly zero comparable price impact.

Build one isolated single-file candidate from the frozen `main.py` and frozen
model coefficients. After the parent action, only on turns 144–717, consider
MILK if current shed stock ≥3, the parent has a free market slot and no
non-SELL market orders or same-item pickup/sale, the own existing route tape
has a positive MILK sale later **on this same day and within 24 turns**, and
this stock batch has not already been advanced. Require model probability
≥0.30, at least three visible rival ready milk units, and a quoted receipt
drop ≥16 coins for selling up to eight units after a rival batch of up to
ten ready units. Append one SELL MILK order of at most the current stock,
projected post-unit stock, next own planned quantity, and eight units.
Block repeats until that own planned sale. All features and the branch use
only current/prior observations and the policy's own route tape. Do not
modify purchases, workers, route choices, or other products.

Run seed-0 both-seat file-path/direct-call parity, then native seeds
2623000–2623015 with control `main.py` and candidate each versus reacting
`main.py`, both seats, original shops. Require all DONE, no branch errors,
at least four activated paired seeds, positive aggregate own-cash and
paired-margin deltas over activated seeds, at least two-thirds activated
paired seeds with positive margin delta, and no activated paired seed below
−5,000 margin delta. If fewer than four seed pairs activate, reject as too
narrow for promotion. Passing development would require an untouched second
native block plus fixed-route regression before any `main.py` edit.

## Replay-frame correction before a fresh second pilot

Native event tracing exposed an indexing error: Kaggle replay frame `t`
contains observation `t` and the action that produced it (turn `t-1`).
The first extractor had paired observation `t` with that prior action, while
the deployed wrapper paired it with its current parent action. The first
candidate's native terminal-cash comparison remains real, but its claimed
offline/deployed feature parity only tested the incorrectly paired rows.

Before a new native test, rebuild all old/new opportunities with observation
frame `t` and current action from frame `t+1`; use future rival actions for
labels only. Keep the same feature list, logistic family, data gate and
action-rule thresholds. The corrected 100/17 episode data gate passes with
708/112 positives; the refit reaches 0.844 AUC and 2.964 top-quartile lift
on the same temporal holdout. Because this holdout was already evaluated
once, treat this as a bug-correction check, not a new independent model
confirmation. Embed the corrected coefficients in a new isolated source,
verify corrected feature and file-loader parity, and run **new native seeds
2624000–2624015** under exactly the original action gate. A pass would still
need independent model data and a further native block before promotion.
