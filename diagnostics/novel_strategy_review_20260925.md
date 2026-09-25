# Novel intervention review — 2026-09-25

## Decision

No credible, evidence-supported intervention distinct from the already
rejected crop swaps, sale timing, fertilizer, hire caps, and route-9 switches
was found in this review. Do not change `main.py` on this evidence.

## Candidate screened (rejected for zero exposure)

The only narrowly testable gap found was a possible cap-aware refinement to
the existing economic feed filter `_r85_feed` in `main.py`. The installed
Kaggriculture 1.32.7 engine's `_daily_refresh_animals` increments animal yield
even when unfed, but caps held yield at the species maximum. Feeding also
resets the consecutive-unfed counter and makes pending care bonus eligible;
so merely seeing a full animal is not enough to skip feed.

**Exact hook:** inside `_r85_feed`, after resolving the current `FEED` command,
animal tile and actor inventory, before the existing `_r88_feed_bonus_cost`
price comparison.

**Strict proposed activation predicate:** the standard 10x10/24-turn engine;
the current action is `FEED` for an observed animal with carried WHEAT;
`consecutive_unfed == 0` and `fed_today` is false; this next dawn is that
animal's scheduled production dawn; the engine-exact fed and unfed projected
yields are equal because both hit `max_held`,
`min(cap, yield_units + 1 + pending_care_bonus) == min(cap, yield_units + 1)`;
there is no same-tile `CARE` or later same-day `FEED` that would erase the
expected saving; and `_r86_next_feed` confirms that the current policy will
feed that animal the following day. In that narrow case, replace this `FEED`
with `PASS`; do not suppress the future feed.

**Predicted cash mechanism:** preserve one WHEAT unit per activation while
keeping the next-day feed plan intact. This is not automatically one coin of
terminal-score gain: it helps only if the saved unit later avoids a purchase or
gets sold, and can be lost to warehouse overflow or a changed execution path.
The candidate must therefore be measured on final own cash, not inferred from
theoretical feed cost or gross sales.

**Exposure result:** a read-only scan of the 24 actual public episodes for
submission 56530281 (11 losses; local replay action aligned to the prior
observation) found **zero** turns satisfying even the core cap/no-next-yield,
current-feed, and safe-next-day-feed conditions. Adding the stricter CARE,
duplicate-feed, and wheat-delivery safeguards cannot increase that count.
This makes an A/B on the supplied live-loss set uninformative, so no treatment
was run. Current agent already has an economic feed gate; there is no evidence
that this proposed refinement addresses any observed loss.

## If future data exposes this case

Use a hash-pinned wrapper around `main.py`; alter only qualifying `FEED` to
`PASS`. First run the same seeds, both seats, with the same opponent actions
and shop path, then rerun with native shop RNG and at least four independent
reactive seeds in both seats. Log trigger count, animals escaped, WHEAT bought
or sold, own and rival terminal cash, margin and status. Require nonzero
activation across at least five independent seeds and both seats; no animal
escapes or invalid actions; positive mean own-cash and paired-margin change;
at least two previously lost routes rescued; no control win reversed; and no
regression against reactive controls. Fail and discard if any safety condition
breaks, the gain is only rival-cash movement, or the win-count/own-cash gate
does not pass.

## Scope / safety

Read `agent.md`, the live-loss cash audit, current agent wrappers and the
installed engine implementation. No production source was changed. `main.py`
remains byte-for-byte unchanged by this review; no Kaggle submission occurred.
