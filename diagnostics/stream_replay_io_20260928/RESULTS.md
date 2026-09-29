# Replay input audit results

The separate bounded-memory loader passes fourteen valid synthetic
chunk/order cases, six malformed-input checks and wrong-hash rejection.
Escaped delimiters, Unicode, numeric boundaries and trailing whitespace
are covered.

One real replay (live-114211346,33,198,891 decompressed bytes) produces
exactly the same configuration, initial two-player frame,720-frame count
and raw SHA as the original complete JSON loader. Its streaming text buffer
peaks at63,729 characters with4KiB chunks.

The immutable cache covers104 fixtures and102 unique replays. Every
decompressed byte was hashed and matched its frozen manifest. The complete
initial-state cache is2,056,362 bytes; the largest undecoded text buffer
across the audit is140,593 characters. This is buffer size, not total
process memory. Cache SHA:
`f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968`.

**Decision: accept the reader/cache for explicitly bound future diagnostic
helpers.** No running helper, input manifest, competition candidate or
policy outcome was changed. Frozen experiments retain their original
loader; full-framework and file-loader policy verification remain separate.

The separately frozen cached-helper study also passes both full719-record
observation/action comparisons against32e Yaroslav's original-loader traces,
plus exact native terminal rewards, statuses and complete telemetry. The
copied helper changes only initial replay loading and verifies the original
compressed input on every call. Accept it for future explicitly bound
development experiments. These two engineering repetitions are not new
strategy evidence. See cached_helper_manifest.json and
cached_helper_parity.json for the exact bindings and receipts.
