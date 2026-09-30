# Wheat purchase hypothesis — development only

Candidate `f21e0cfd...` completed both seats against the fresh DECEM replay:
76,499 versus 154,973 coins, margin -78,474 in each seat. It added six wheat
units over three turns with zero recorded exceptions. The base margin was
-82,192; neither game became a win.

The stock projection used the wrong shed-access geometry (Manhattan
neighbors instead of the engine's four inner-corner tiles). Do not promote
or treat these bytes as validated. Preserve the v0 artifact and result.

Further native tracing found the workers expected to harvest feed wheat
on LOCKED land. HIRE ignores extra arguments and always creates an empty
inventory. The next experiment should address the failed land purchase
before spending more effort on this downstream procurement patch.

Decision: stop this v0 candidate; no main edit or upload.
