# Later schedule feasibility — 2026-09-27

The existing catalogue contains 203 schedules; the known rejected
113445495 schedule was excluded. No games or candidate policies were run.

At each turn 216, 288, 360, 432, 504 and 576, **liminhai and Driz Lo have
only one exact compatible prefix**: source 113840386, which is already
their complete incumbent schedule. There is no alternate continuation
within this library for the diagnosed tomato deficit. Joseph Adamski has
five matching sources, all with identical future actions. Istinetz has two
alternatives at turns 216/288, but none after turn 360; it is a current win
and does not establish an intervention for the liminhai loss.

A separate passive check ignored only adjacent equal-quantity
BUY_PRODUCT/SELL round trips. That weaker condition finds 24 alternatives
at turn 144 for source 113840386, but still only the incumbent from turn
216 onward. This normalization does not establish cash or live-state
equivalence and was not used to qualify any candidate. The first ad hoc
normalization read encountered an empty market order; adding the existing
length guard fixed the diagnostic, without running or changing a policy.

**Reject the hypothesis that an existing compatible later continuation
can simply be selected to repair this loss.** A new physical schedule or
an earlier, independently validated complete route decision is needed.
No main.py change, promotion or upload. Preserve `audit.json` and
`normalized_feasibility.json`; these are feasibility evidence, not strength
validation.
