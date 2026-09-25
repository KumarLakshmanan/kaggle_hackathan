# Predeclared same-turn market-order exposure test

Date: 2026-09-25. Frozen submitted `main.py` SHA-256:
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.

GPT-6 Pro suggested a narrowly guarded swap of an existing premium-product SELL
with the single independent, price-insensitive order immediately ahead of it.
The potential mechanism is a better price or earlier market slot in a
simultaneous-action contest. This is a hypothesis, not a demonstrated rule.
No source code, credentials, opponent names, or personal data were shared in
the consultation; the user authorized the aggregate-only brief.

First run a **read-only syntactic upper-bound exposure scan** on the 24 frozen
actual public matches. An eligible syntactic pair is a positive-quantity
premium SELL immediately after BUY_SEED, HIRE, or another SELL, with the same
product sold only once in our queue, quoted price >1, and no WHEAT or
FERTILIZER product trade. Report each preceding-order category separately and
count distinct episodes, turns and the 11 loss episodes. Since the scan does
not prove stock, funding, or transaction effects, its count is only an upper
bound. Stop if fewer than three distinct close-loss episodes have such an
exposure; do not relax the rule after seeing results.

Only if the scan passes: validate projected post-unit stock, independent
funding of fixed-price orders, no sale-credit dependencies, and original-shop
receipts at the first eligible event. Candidate changes must preserve order
set, quantities, production, and queue length, swap no more than one adjacent
pair per turn, and use only current observation plus our own action. Predeclare
selected loss and winning controls before benchmarking. A local fixed-tape
gain is not sufficient for promotion: require executed own-receipt improvement,
original-shop and reactive tests, a full historical top-50 panel, no
regressions/timeouts, and then fresh independent games. No Kaggle submission
is authorized by this experiment.

## Exposure result — no safe intervention in this sample

`market_swap_exposure.py` inspected all 24 actual public replays with the
pre-action observation and the emitted `main.py` market queue. A corrected
scan found **209** positive-quantity premium SELLs immediately after another
SELL, spanning **all 24** episodes, including all eight close losses. The
initial scan incorrectly skipped seat-1 replay observations because Kaggle's
download omits their explicit `step` key. The corrected script derives turn
index from the replay row and no longer filters those games. It found **zero** after a
BUY_SEED or HIRE. Using the submitted policy's post-unit-action shed projector
and all preceding sale requests, **none** of the 209 earlier SELLs was
provably inert. Thus the strict treatment has **zero eligible events in zero
episodes**, including zero close losses. The prior frontloading and no-op
compaction layers appear to have already removed this opening in these games.

Do not implement the strict swap or reinterpret an active SELL as
price-insensitive to manufacture a treatment. Comparing the order of two
active premium sales would be a separate, price-sensitive H6 experiment with
its own hypothesis and predeclared controls. No `main.py` edit or Kaggle
submission followed this failed exposure test.

An independent, read-only active-sale upper screen in
`active_sell_swap_bound.py` modeled same-turn receipts from the actual market
engine's per-unit lockstep rules. Of 202 narrower premium-premium adjacent
tests, 184 had baseline projected stock and market inventory exactly match
the public replay; 18 were excluded as untrusted. Even an oracle that chose
every locally positive swap using the rival's recorded simultaneous action
gained only **337** own sale-receipt coins summed over those 184 isolated
tests across 24 games; the 11 losses contributed only **108**. The largest
isolated sum on a lost game was 49 coins versus a 4,003-coin deficit. These
isolated gains are not additive if swaps overlap, and they do not include
future market adaptation. The result makes active-sale adjacent swapping a
low-leverage lead, not a policy ready for promotion.
