# Loader harness startup error — 2026-09-29

The initial operational launch stopped before the first native game in
`run(job, "direct")`, while hashing the opponent action tape. Python rejected
`json.dumps(..., sort=sort, ...)`: the standard parameter is `sort_keys`.

Native games executed: **0**. No candidate outcome was observed, no loader
parity receipt was produced, and no Kaggle upload was attempted. The shared
and package locks were released by their context managers.

The original checker, builder, plan, manifest and static freeze are preserved
in this directory. Root corrected only the keyword to `sort_keys=sort`, then
rebuilt the same six-seat/twelve-game scope with unchanged candidate and
criteria. The archived manifest hash is
`541f87f0426aba893cdcbd9125cf337fcd9ec2f3389d22884eff321fbe4db6e6`;
the archived freeze receipt hash is
`982f6937bad6597d9caefd5427a7edecf7ed0509721347a28331c9db432be914`.
