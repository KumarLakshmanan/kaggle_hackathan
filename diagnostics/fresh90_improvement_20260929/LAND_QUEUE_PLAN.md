# Repair an unfunded, already-scheduled land order

Frozen before candidate games. Majkel's baseline trace requests SW land at
step242, eight coins short after the preceding WHEAT buy. Later sells in the
same queue would cover the existing2000-coin commitment. It is never retried;
workers subsequently plant/water locked SW tiles. This is a scheduling failure,
not a proposal to add a new land investment.

The isolated candidate retains exact cb76 and moves an existing BUY_LAND to
the end of its current queue only when exact native market forecasts show:
- the original order fails in both idle and mirrored-rival scenarios;
- the new order acquires exactly the next native quadrant in both scenarios;
- own shed, seeds, hands and hires_today are identical to their corresponding
  original forecast endpoints, and the rival's physical endpoint is unchanged;
- own end cash is no lower than original end cash minus the native land cost,
  and rival end cash does not increase in either scenario.

No additional order, hidden state, opponent identity or schedule is inserted.
Pilot: latest top20 ranks1,9,10,19, both seats (eight games). Require every
baseline win retained, both Majkel seats rescued and clean completion, before
expanding to all200 latest100 seats and fresh reacting games. If the guard
does not activate or the target stays lost, reject escalation. Existing
complete-route candidates remain separate. A later combined candidate would
need its own exact full-panel verification. No upload.
