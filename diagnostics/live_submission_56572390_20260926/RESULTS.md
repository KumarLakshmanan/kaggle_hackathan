# Mirror24 live audit — 2026-09-26 17:09 UTC

The user-authorized submission 56572390 uploaded the exact current `main.py`
SHA-256 `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
The Kaggle file loader and seed-0 validation replay matched local self-play in
both seats; see `validation_parity.json` and
`../top10_goal_20260926/UPLOAD_56572390.md`.

`audit_latest_100.json` summarizes the latest 100 complete public replays of
this submission. There were **71 wins, 29 losses, zero draws**, with both
players `DONE` throughout. The median loss was 460 coins, the largest loss
4,462. The loss count by our seat was 13 in seat 0 and 16 in seat 1. Thirty-three
of the wins had no visible physical-mirror turn in the branch's eligible
window (turns 144–717). The other 38 wins and all 29 losses had at least one
such turn; the median exposed loss had 336 matched turns. These are observed
associations. The physical-match gate can open for many near-identical agents,
and exposure alone does not show which sale rule caused the final result.

At 17:09 UTC the latest submission's displayed public score was **2165.0**,
below the older corrected submission 56569042's **2221.0**. The read-only
17:07 leaderboard export (`../leaderboard_20260926_1707/kaggriculture.zip`)
ranked Lakshmanan R **876 / 2221.0**, versus rank 10 at **2881.7**. The team
rank reflects its higher scoring older submission; the newer policy has not
demonstrated a live rating improvement. Ratings vary with the opponent sample
and are not a controlled A/B comparison of the two sources.

**Decision:** retain the current source for analysis; no policy promotion or
new upload. The 29 close near-mirror losses warrant an isolated sale-policy
experiment with both-seat original-shop checks and fresh reactive games. The
fresh September 26 top-100 panel remains 66/100 positive paired routes and
does not satisfy the requested all-100 outcome.

At 17:54 UTC, after more live scoring, submission 56572390 displayed 2168.3
and older submission 56569042 displayed 2206.8. The new leaderboard export
(`../leaderboard_20260926_1754/kaggriculture.zip`) ranked the team **927 /
2206.8**, versus rank 10 at **2888.7**. This later status supersedes the
17:07 rating snapshot above; the 100-game replay audit remains the frozen
sample described there.

## Terminal inventory check — 2026-09-26 18:08 UTC

`terminal_inventory_audit.py` read the original public replay of each of the
29 losses in this frozen audit. After the last settled action, **none had any
goods in our shed or worker inventories** (`terminal_inventory_losses.json`).
The installed engine ends the match at step 718 and does not clear those
inventories at termination, so a final extra `SELL` of already stored goods
cannot rescue these particular losses. This says nothing about earlier sale
timing, unharvested farm output, or what a different endgame would have
produced. **Decision:** reject a terminal stored-cargo-only fix for this live
loss panel; preserve the current agent and continue earlier-turn diagnosis.
