# Preparation finding — before any outcomes

Three frozen branches use a one-shop fallback because their exact two-shop
key is absent: BRUNCH/SMOOTHIE, PIZZA/FARMERS and PIZZA/ICE. Replacing only
existing keys would leave those variants inert. The layer therefore inserts
the exact two-shop key as well as replacing every existing descendant.
This implements the already declared branch intervention without changing
the first-shop route or unrelated branches. The pool builder verifies the
map after import, raw first-144-action compatibility, and every variant's
actual step-144 telemetry. No variant outcomes have run.
