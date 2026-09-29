# Future cached diagnostic helper

The completed reader audit supplies a104-fixture cache with exact initial
frames/configuration and verified compressed/decompressed source hashes.
Create a separate copy of fast_game.py that changes only replay loading:
verify the entire cache hash and the original compressed replay hash, then
deep-copy the bound initial frame/configuration. Keep the policy calls,
native transitions, tape checks, telemetry, timing and cleanup unchanged.
Existing frozen helpers and live runs are untouched.

Before using this helper for future strategy research, reproduce exact
32e299fe against Yaroslav in both seats and compare all719 observation/action
records with its completed original-loader traces, plus terminal rewards,
telemetry and statuses with the verified native100 receipt. These two runs
are engineering parity, not new evidence of strategy strength. Freeze the
copy's hash and original/cache bindings before these checks. Any mismatch
rejects this helper until a separately recorded repair/recheck.
