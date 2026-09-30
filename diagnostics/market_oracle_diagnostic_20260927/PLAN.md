# Offline market-order opportunity diagnostic

2026-09-27. Use all four games in the frozen10:05 top-100 live cash audit,
including its three wins and one loss. Do not select turns by final outcome.
This is an offline perfect-information diagnostic, never a submission agent.
The opponent's actual action and private stock are available only in the
reconstructed completed-game trace and must not enter deployed policy code.

For every recorded turn, apply both actual players' physical commands to
the full recorded pre-turn state using installed native engine functions
and its atomic PLANT guard. Replay the original market orders and require
both final cash balances, sheds, seeds, worker counts and unlocked land
to match the passive trace's post-turn ledger. Stop on any parity mismatch.

On each turn with at least two own orders, search at most two passes of
moving an existing SELL or BUY_PRODUCT earlier (at most48 unique
proposals per pass). Hold the actual opponent queue and both starting
private states fixed. Require identical both-player post-market resource
signatures and no own-cash loss; maximize immediate relative-cash gain.
Keep every result, including zero opportunities.

Report the available improvement found at the factual states and its
distribution across turns. Summing these one-turn changes is **not** a
counterfactual full-game result, a global optimum, a deployable forecast,
or evidence of independent policy strength. It indicates whether trade
ordering alone has a material local opportunity worth modeling. The
running3bd candidate and its frozen gates remain unchanged.
