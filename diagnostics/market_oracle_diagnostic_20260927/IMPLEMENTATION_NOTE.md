# Parity harness correction

The first offline attempt stopped at turn23 of the first game. Cash,
shed, seeds and land matched exactly; its worker count comparison used
the immediate post-market count4 against the passive full-turn ledger's
post-midnight count0. The native engine retires hands and deposits carried
stock at each day boundary. This was a diagnostic phase-alignment error,
not a competition-agent failure or a changed market result.

Keep the incomplete `audit.json` attempt. The corrected `audit_v2.json`
run applies native automatic inventory deposits and worker retirement to
a separate parity-check copy on boundary turns. Its search still starts
from the exact pre-market state. The experiment plan, chosen games,
proposal search and candidate qualification remain unchanged. No complete
game is rerun and no policy file is modified by this correction.
