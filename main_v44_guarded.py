"""V44 guarded controller built around the validated V43 action books.

This is the local promotion candidate for the Kaggriculture submission.  The
V43 farm tapes remain the control policy; V44 adds only changes that are easy
to audit and that can be ablated independently:

* a public-observation route selector for the two known continuation points;
* hand-count/action-shape validation;
* bounded exception recovery with per-seat telemetry; and
* an optional, explicitly selected terminal liquidation overlay.

The terminal overlay is disabled by default while it is being benchmarked.
Set ``V44_MODE`` to ``terminal_collision``, ``terminal_value``, or
``terminal_existing`` for the corresponding ablation.  ``V44_ROUTE_MODE``
may be set to ``control`` to run the unmodified V43 route selector.
"""

from __future__ import annotations

import copy
import math
import os
from collections import Counter
from typing import Any

import main as _base
from v19_terminal import apply_overlay as _apply_terminal_overlay
from v23.state_encoder import get as _get
from v43 import sparse_router as _router


_MODE = str(os.environ.get("V44_MODE", "guarded")).strip().lower()
_ROUTE_MODE = str(os.environ.get("V44_ROUTE_MODE", "refined")).strip().lower()
_RESIDUAL_SHOP = str(os.environ.get("V44_RESIDUAL_SHOP", "")).strip().upper()
_RESIDUAL_GATE = str(os.environ.get("V44_RESIDUAL_GATE", "strict")).strip().lower()

# ``main`` constructs the bundled router in a shared module namespace.  The
# benchmark loads several candidate modules in one worker, so keeping a route
# selector assigned at module scope leaks one candidate's selector/state into
# the next game.  Capture the clean selector once, then install the desired
# selector only for the duration of this candidate's policy call.
if not hasattr(_base, "_V44_ORIGINAL_SELECTED_ROUTE"):
    _base._V44_ORIGINAL_SELECTED_ROUTE = _router.selected_route
_ORIGINAL_SELECTED_ROUTE = _base._V44_ORIGINAL_SELECTED_ROUTE

_RESIDUAL = None
if _RESIDUAL_SHOP:
    # This is an ablation switch while we validate the dynamic market
    # controller.  It is deliberately opt-in because the V43 control remains
    # the promotion baseline until the residual survives holdout testing.
    import kaggle_public_v58_agent as _kaito

    _RESIDUAL = _kaito._v51_build_policy(
        copy.deepcopy(_base._V43_ROUTES["default"]),
        _kaito._V54_CONFIG,
    )


def _number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _count(farm: dict[str, Any], name: str) -> int:
    """Count publicly visible farm features without using private inventory."""
    wanted = str(name).upper()
    diagnostic_counts = farm.get("counts", {}) or {}
    if diagnostic_counts:
        return int(_number(diagnostic_counts.get(wanted, 0)))

    total = 0
    for row in farm.get("tiles", []) or []:
        cells = row if isinstance(row, list) else [row]
        for tile in cells:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    total += value == wanted
                    break
    return total


def _opponent(obs: Any) -> dict[str, Any]:
    player = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    farms = list(_get(obs, "farms", []) or [])
    if len(farms) == 2:
        return farms[1 - player] or {}
    return {}


_CHOICE = {0: "default", 1: "default"}
_LAST_ROUTE_STEP = {0: -1, 1: -1}
_PENDING_BRANCH = {0: None, 1: None}
_RESIDUAL_ELIGIBLE = {0: False, 1: False}


def _control_selector(obs: Any, config: Any) -> str:
    """Stable copy of the original V43 selector.

    Candidate modules are reloaded several times inside a benchmark worker;
    capturing a mutable function from a previous candidate would otherwise
    nest route selectors across games.
    """
    step = int(_get(obs, "step", 0) or 0)
    town = _get(obs, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])
    yarn_first_start = int(getattr(config, "yarn_first_start", 88) or 88)
    yarn_second_start = int(getattr(config, "yarn_second_start", 153) or 153)
    if shops and shops[0] == "YARN_STORE" and step >= yarn_first_start:
        return "yarn_first"
    if (
        len(shops) >= 2
        and shops[0] != "YARN_STORE"
        and shops[1] == "YARN_STORE"
        and step >= yarn_second_start
    ):
        return "yarn_second"
    return "default"


_CONTROL_SELECTOR = _control_selector


def _select_refined_route(obs: Any, config: Any) -> str:
    """Select only from public branch evidence, then keep the choice fixed.

    The branch choices are intentionally made once.  Re-evaluating the route
    every turn would mix stateful action tapes and is materially riskier than
    a guarded continuation decision.
    """
    step = int(_get(obs, "step", 0) or 0)
    seat = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    if step == 0 or step < _LAST_ROUTE_STEP[seat]:
        _CHOICE[seat] = "default"
        _PENDING_BRANCH[seat] = None
        _RESIDUAL_ELIGIBLE[seat] = False
    _LAST_ROUTE_STEP[seat] = step

    choice = _CHOICE[seat]
    town = _get(obs, "town", {}) or {}
    shops = [str(value) for value in (_get(town, "unlocked_shops", []) or [])]
    opponent = _opponent(obs)
    hands = len(opponent.get("hands", []) or [])

    # The first continuation is resolved at the first action-book boundary.
    # These features are public farm composition/capital signals; no opponent
    # shed or inventory is inspected.
    if step == 88 and choice == "default" and shops:
        first = shops[0]
        strawberry = _count(opponent, "STRAWBERRY")
        melon = _count(opponent, "MELON")
        wheat = _count(opponent, "WHEAT")
        cow = _count(opponent, "COW")
        sheep = _count(opponent, "SHEEP")
        money = _number(opponent.get("money"))

        if first == "YARN_STORE":
            # A high-wool/capital opening has two empirically distinct
            # continuations.  Keep the conservative V43 yarn-first default
            # unless the public portfolio matches the validated suffix.
            if hands >= 6 and (
                (
                    strawberry == 2
                    and melon == 12
                    and wheat == 6
                    and cow == 2
                    and sheep == 3
                )
                or (
                    wheat >= 7
                    and melon >= 11
                    and cow >= 3
                    and sheep <= 2
                )
            ):
                choice = "yarn_second"
            else:
                choice = "yarn_first"
        elif first == "PET_CAFE":
            # Only the higher-capacity PET family has enough public evidence
            # for the optional suffix.  Five-hand PET remains on control.
            if hands >= 6 and (
                (
                    strawberry == 2
                    and melon == 12
                    and wheat == 6
                    and cow == 2
                    and sheep == 3
                    and money >= 300
                )
                or (strawberry >= 5 and wheat <= 3)
                or (
                    _count(opponent, "PASTURE") >= 1
                    and cow == 1
                    and money < 100
                )
            ):
                choice = "yarn_first"
        elif first == "FARMERS_MARKET":
            if hands >= 6 and (
                (
                    strawberry == 2
                    and melon == 12
                    and wheat == 6
                    and cow == 2
                    and sheep == 3
                )
                or (
                    strawberry == 4
                    and melon == 11
                    and wheat == 4
                    and cow == 2
                    and sheep == 3
                )
            ):
                choice = "yarn_first"
            elif wheat >= 7 and melon >= 12 and cow >= 3 and sheep <= 2:
                if hands >= 6:
                    choice = "yarn_second"

    _CHOICE[seat] = choice
    return choice if choice != "default" else _CONTROL_SELECTOR(obs, config)


_TELEMETRY = {
    "calls": 0,
    "exceptions": 0,
    "shape_repairs": 0,
    "terminal_overlays": 0,
    "residual_errors": 0,
    "last_exception": "",
}
_LAST_VALID: dict[int, dict[str, Any] | None] = {0: None, 1: None}
_LAST_STEP: dict[int, int] = {0: -1, 1: -1}


def _pass_action(obs: Any) -> dict[str, Any]:
    player = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    farms = list(_get(obs, "farms", []) or [])
    farm = farms[player] if player < len(farms) else {}
    hands = list(_get(farm, "hands", []) or [])
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in hands],
        "market": [],
    }


def _align_and_validate(action: Any, obs: Any, configuration: Any) -> dict[str, Any]:
    """Preserve a good action while enforcing the engine's shape limits."""
    if not isinstance(action, dict):
        action = _pass_action(obs)
    else:
        action = copy.deepcopy(action)

    player = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    farms = list(_get(obs, "farms", []) or [])
    farm = farms[player] if player < len(farms) else {}
    expected_hands = len(farm.get("hands", []) or [])

    farmer = action.get("farmer")
    if not isinstance(farmer, (list, tuple)) or not farmer:
        farmer = ["PASS"]
        _TELEMETRY["shape_repairs"] += 1
    action["farmer"] = list(farmer)

    hands = action.get("hands")
    if not isinstance(hands, (list, tuple)):
        hands = []
        _TELEMETRY["shape_repairs"] += 1
    aligned_hands = []
    for hand in list(hands)[:expected_hands]:
        if isinstance(hand, (list, tuple)) and hand:
            aligned_hands.append(list(hand))
        else:
            aligned_hands.append(["PASS"])
            _TELEMETRY["shape_repairs"] += 1
    while len(aligned_hands) < expected_hands:
        aligned_hands.append(["PASS"])
        _TELEMETRY["shape_repairs"] += 1
    action["hands"] = aligned_hands

    raw_market = action.get("market")
    if not isinstance(raw_market, (list, tuple)):
        raw_market = []
        _TELEMETRY["shape_repairs"] += 1

    clean_market: list[list[Any]] = []
    max_orders = int(_get(configuration, "maxMarketOrdersPerTurn", 10) or 10)
    max_orders = max(0, min(max_orders, 10))
    sized_ops = {"BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "SELL"}
    for raw_order in list(raw_market)[:max_orders]:
        if not isinstance(raw_order, (list, tuple)) or not raw_order:
            _TELEMETRY["shape_repairs"] += 1
            continue
        order = list(raw_order)
        op = str(order[0])
        if op in sized_ops:
            if len(order) < 3:
                _TELEMETRY["shape_repairs"] += 1
                continue
            try:
                quantity = int(order[2])
            except (TypeError, ValueError):
                _TELEMETRY["shape_repairs"] += 1
                continue
            if quantity <= 0:
                _TELEMETRY["shape_repairs"] += 1
                continue
            order[2] = quantity
        elif op in {"HIRE", "BUY_LAND"}:
            order = [op]
        clean_market.append(order)
    action["market"] = clean_market
    return action


def _recover(obs: Any) -> dict[str, Any]:
    """Use the last known unit plan, but never repeat capital orders."""
    seat = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    previous = _LAST_VALID.get(seat)
    if not isinstance(previous, dict):
        return _pass_action(obs)
    recovered = copy.deepcopy(previous)
    recovered["market"] = [
        order
        for order in list(recovered.get("market", []) or [])
        if isinstance(order, list) and order and order[0] == "SELL"
    ]
    return recovered


def agent(obs: Any, configuration: Any = None) -> dict[str, Any]:
    seat = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    step = int(_get(obs, "step", 0) or 0)
    if step == 0 or step < _LAST_STEP[seat]:
        _LAST_VALID[seat] = None
        _RESIDUAL_ELIGIBLE[seat] = False
    _LAST_STEP[seat] = step
    _TELEMETRY["calls"] += 1

    previous_selector = _router.selected_route
    _router.selected_route = (
        _select_refined_route
        if _ROUTE_MODE != "control"
        else _ORIGINAL_SELECTED_ROUTE
    )
    try:
        # Call the policy directly so V44 can distinguish a real exception
        # from the control policy's broad PASS fallback.
        raw = _base._V43_POLICY(obs, configuration)
        if _RESIDUAL is not None:
            shops = list(
                _get(_get(obs, "town", {}) or {}, "unlocked_shops", []) or []
            )
            opponent = _opponent(obs)

            # ``broad`` is retained as an explicit ablation.  The default
            # promotion gate is decided once at step 88 from public state so
            # a later hand expansion cannot silently switch strategies.
            if _RESIDUAL_GATE != "broad" and step == 88:
                first_shop = str(shops[0]).upper() if shops else ""
                opponent_money = _number(opponent.get("money"))
                opponent_hands = len(opponent.get("hands", []) or [])
                _RESIDUAL_ELIGIBLE[seat] = bool(
                    first_shop == _RESIDUAL_SHOP
                    and opponent_hands >= 8
                    and opponent_money >= 400.0
                    and _count(opponent, "MELON") >= 10
                    and _count(opponent, "WHEAT") >= 6
                )

            # Keep the residual synchronized from turn 0: its stateful hybrid
            # needs the complete prefix.  It can take over only if the fixed
            # public gate passed, so warming it does not broaden the policy.
            try:
                relevant_shop = bool(
                    shops and str(shops[0]).upper() == _RESIDUAL_SHOP
                )
                residual = _RESIDUAL(obs, configuration)
                if _RESIDUAL_GATE == "broad":
                    broad_eligible = bool(
                        step >= 72
                        and relevant_shop
                        and len(opponent.get("hands", []) or []) >= 6
                    )
                    if broad_eligible:
                        raw = residual
                elif step >= 88 and relevant_shop and _RESIDUAL_ELIGIBLE[seat]:
                    raw = residual
            except Exception:
                _TELEMETRY["residual_errors"] += 1
        action = _align_and_validate(raw, obs, configuration)
    except Exception as exc:  # competition-safe last line of defence
        _TELEMETRY["exceptions"] += 1
        _TELEMETRY["last_exception"] = f"{type(exc).__name__}: {exc}"
        action = _align_and_validate(_recover(obs), obs, configuration)
    finally:
        _router.selected_route = previous_selector

    if _MODE in {
        "terminal_existing",
        "terminal_value",
        "terminal_collision",
        "late_collision",
        "late_clone_collision",
    }:
        before = copy.deepcopy(action)
        overlay_mode = _MODE
        action = _apply_terminal_overlay(obs, action, overlay_mode)
        action = _align_and_validate(action, obs, configuration)
        if action != before:
            _TELEMETRY["terminal_overlays"] += 1

    validated = copy.deepcopy(action)
    _LAST_VALID[seat] = validated
    return action


def _kaggle_submission_entrypoint(obs: Any, configuration: Any = None):
    return agent(obs, configuration)
