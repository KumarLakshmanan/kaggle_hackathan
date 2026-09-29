# Bounded-memory replay input — 28 September 2026

Two replay decompressions in the donor study raised MemoryError while the
host was near its virtual-memory limit. Preserve every frozen running
helper and candidate. This separate engineering study changes input loading
only and provides no new policy outcome or strength evidence.

Parse the gzip JSON incrementally with Python's standard JSON decoder,
retaining the configuration and first recorded two-player frame. Decode and
discard each later frame. Hash every decompressed byte, including trailing
whitespace, and require the frozen manifest hash. Limit the undecoded buffer
to16 MiB so a malformed giant value fails explicitly. Validate the root
object, unique keys, complete steps array, frame count, EOF and configuration.

Verify with synthetic chunk boundaries, escaped strings, Unicode, trailing
data and wrong-hash rejection. Then compare one real complete replay with
the ordinary loader when memory permits, checking exact configuration,
initial frame, total frames and raw SHA. Generate an immutable input cache
for the104 local fixtures, deduplicating source paths; each item records the
compressed file hash, decompressed hash, initial frame and configuration.
This is an input/provenance audit, not another simulation or policy test.

Do not replace helpers used by existing frozen experiments. A future plan
may explicitly bind this loader/cache after verification. Existing jobs
continue with their original loader and reduced concurrency.
