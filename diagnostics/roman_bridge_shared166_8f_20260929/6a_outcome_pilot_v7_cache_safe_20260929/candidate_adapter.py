"""Static, reviewable Roman opening bridge for the hash-bound 6a pilot.

The layer is deliberately separate from the frozen parent and donor. The
caller supplies the exact 6a parent agent and a *raw donor schedule* callback
(for example, the shared166 route selector before its worker-indexed repair
transforms).  Do not pass the donor's fully transformed agent here: its
hire-recovery queues use donor hand indices and would need to be remapped too.

No module-level game state, simulator, Kaggle API, or file access is used.
"""
from copy import deepcopy


PARENT_SHA256 = "6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc"
PARENT_BASE_SHA256 = "7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2"
DONOR_SHA256 = "fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849"
PANEL_SHA256 = "bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795"
MATCHED_OPP_ACTION_TAPE_SHA256 = "18ba3ec92eec0ec7bab95498119eebae88e7ce0ca4571eba42ffbaeb9ddda4b1"
MATCHED_OPP_STEP1_ACTION_SHA256 = "48e7b680c2f75b6a1d838749d1289420710bd6fb05c27275c9f2c38ac26769ff"
ADAPTER_STEP1_ACTION_SHA256 = "22ab294d18251d7ce475cd29261d151a7301c3c6ff9eb32315832ed7aba9cb15"
_EXPECTED_RIVAL_FARM_KEYS = frozenset(
    {"farmer", "hands", "hires_today", "money", "tiles", "unlocked_quadrants"}
)
_EXPECTED_MARKET_KEYS = frozenset({"inventory", "prices"})

# One-based donor slot -> one-based actual slot.  The inverse below is used
# to arrange commands in the output action's actual-hand order.
DONOR_TO_ACTUAL = (4, 1, 2, 3, 5)
ACTUAL_TO_DONOR_ZERO_BASED = (1, 2, 3, 0, 4)
DONOR_SHARED_LAST_ACTION = 165
_EXPECTED_STEP1_SHED = {
    "CARROT": 0, "COW": 2, "EGG": 0, "FERTILIZER": 0, "GOOSE": 0,
    "MELON": 0, "MILK": 0, "SHEEP": 2, "STRAWBERRY": 0,
    "TOMATO": 0, "WHEAT": 6, "WOOL": 0,
}
_EXPECTED_SEEDS = {
    "CARROT": 0, "MELON": 0, "STRAWBERRY": 0, "TOMATO": 0, "WHEAT": 0,
}


def _farm_pair(observation):
    player = int(observation["player"])
    farms = observation["farms"]
    if player not in (0, 1) or len(farms) != 2:
        raise ValueError("expected a two-player Kaggriculture observation")
    return farms[player], farms[1 - player]


def _public_trigger(observation):
    """Exact saved-panel trigger: at step 1, rival has 3 hands at (4, 3)."""
    if int(observation.get("step", -1)) != 1:
        return False
    _, rival = _farm_pair(observation)
    return len(rival.get("hands", [])) == 3 and rival.get("farmer") == [4, 3]


def _expected_parent_opening_state(observation):
    """Guard the bridge against a changed or unaffordable parent opening."""
    own, _ = _farm_pair(observation)
    private = observation.get("private", {})
    shed = private.get("shed", {})
    return (
        own.get("farmer") == [4, 4]
        and len(own.get("hands", [])) == 4
        and int(own.get("hires_today", -1)) == 4
        and float(own.get("money", 0)) == 1088.0
        and shed == _EXPECTED_STEP1_SHED
        and private.get("seeds") == _EXPECTED_SEEDS
        and private.get("inventories") == [{}] * 5
    )


def _fifth_hire_action(observation):
    own, _ = _farm_pair(observation)
    return {
        "farmer": ["NORTH"],
        "hands": [["PASS"] for _ in own["hands"]],
        "market": [["HIRE"]],
    }


def _expected_step2_merge_state(observation):
    """Static prediction for observation step 2; native verification pending."""
    own, _ = _farm_pair(observation)
    private = observation.get("private", {})
    shed = private.get("shed", {})
    return (
        int(observation.get("step", -1)) == 2
        and own.get("farmer") == [4, 3]
        and own.get("hands") == [[5, 4], [4, 5], [5, 5], [4, 4], [4, 4]]
        and int(own.get("hires_today", -1)) == 5
        and float(own.get("money", 0)) == 1083.0
        and shed == _EXPECTED_STEP1_SHED
        and private.get("seeds") == _EXPECTED_SEEDS
        and private.get("inventories") == [{}] * 6
    )


def _expected_step2_public_state(observation, expected_snapshot):
    """Require the complete public rival farm and shared-market snapshot.

    The caller may inject only a snapshot predicted/verified after this
    adapter's exact step-1 action and the exact matched rival action. Historical
    parent snapshots are not valid substitutes because our market orders
    change at step 1.
    """
    if not _has_bound_step2_public_snapshot(expected_snapshot):
        return False
    _, rival = _farm_pair(observation)
    return (
        rival == expected_snapshot["rival_farm"]
        and observation.get("market") == expected_snapshot["market"]
    )


def _has_bound_step2_public_snapshot(expected_snapshot):
    """Validate a complete, provenance-bound future public snapshot.

    This runs before the step-1 hire, so absent or partial forecast data cannot
    spend the bridge cost. The actual values are compared again at step 2.
    A historical parent snapshot is invalid unless it was derived after this
    adapter action and the tagged opponent action.
    """
    if not isinstance(expected_snapshot, dict):
        return False
    rival_farm = expected_snapshot.get("rival_farm")
    market = expected_snapshot.get("market")
    if not isinstance(rival_farm, dict) or set(rival_farm) != _EXPECTED_RIVAL_FARM_KEYS:
        return False
    if not isinstance(market, dict) or set(market) != _EXPECTED_MARKET_KEYS:
        return False
    if not isinstance(market.get("inventory"), dict) or not isinstance(market.get("prices"), dict):
        return False
    if expected_snapshot.get("opponent_action_tape_sha256") != MATCHED_OPP_ACTION_TAPE_SHA256:
        return False
    if expected_snapshot.get("opponent_action_index") != 1:
        return False
    if expected_snapshot.get("opponent_action_sha256") != MATCHED_OPP_STEP1_ACTION_SHA256:
        return False
    if expected_snapshot.get("adapter_step") != 1:
        return False
    if expected_snapshot.get("adapter_action_sha256") != ADAPTER_STEP1_ACTION_SHA256:
        return False
    return True


def remap_donor_hands(action, actual_hand_count):
    """Return a copied raw donor action in actual hand-index order.

    The first five donor slots map to actual slots [4, 1, 2, 3, 5].  Any later
    hires are appended in matching order and therefore retain their indices.
    A shape mismatch fails closed by returning None; callers must not silently
    apply a donor schedule to a different worker count.
    """
    if actual_hand_count < 5:
        return None
    donor_hands = action.get("hands", [])
    if len(donor_hands) != actual_hand_count:
        return None
    actual_to_donor = list(ACTUAL_TO_DONOR_ZERO_BASED)
    actual_to_donor.extend(range(5, actual_hand_count))
    if len(actual_to_donor) != actual_hand_count:
        return None
    mapped = deepcopy(action)
    mapped["hands"] = [deepcopy(donor_hands[i]) for i in actual_to_donor]
    return mapped


def make_agent(parent_agent, donor_schedule_action, expected_step2_public=None):
    """Build a candidate wrapper without mutating either frozen source.

    Step 0 delegates unchanged to the supplied 6a parent. At step 1, the exact
    public trigger plus a private-state guard selects one NORTH move, four
    PASSes, and the fifth HIRE only when a complete step-2 public snapshot is
    injected with exact field keys and hashes for both adapter and rival
    actions. At step 2,
    both own merge state and the full public rival-farm and market snapshot
    must match before donor actions are used. The expected snapshot must
    account for the adapter's step-1 action and the exact
    matched opposing action tape; old parent snapshots are invalid.

    If the guarded opening state is absent, the parent remains in control. If
    an activated game's worker count disagrees with the donor schedule, return
    control to the frozen parent at that observation and on every later call.
    Never issue donor commands to a different worker count.
    """
    active = False
    bridge_failed = False
    telemetry = {
        "roman_parent_fallbacks": 0,
        "roman_fallback_step": -1,
        "roman_fallback_reason": "",
    }

    def fallback_to_parent(observation, configuration, step, reason):
        nonlocal active, bridge_failed
        active = False
        bridge_failed = True
        telemetry["roman_parent_fallbacks"] += 1
        telemetry["roman_fallback_step"] = int(step)
        telemetry["roman_fallback_reason"] = reason
        return parent_agent(observation, configuration)

    def agent(observation, configuration=None):
        nonlocal active, bridge_failed
        step = int(observation.get("step", -1))
        if step == 0:
            active = False
            bridge_failed = False
            telemetry.update({
                "roman_parent_fallbacks": 0,
                "roman_fallback_step": -1,
                "roman_fallback_reason": "",
            })
            return parent_agent(observation, configuration)
        if bridge_failed:
            return parent_agent(observation, configuration)
        if step == 1:
            if (
                _has_bound_step2_public_snapshot(expected_step2_public)
                and _public_trigger(observation)
                and _expected_parent_opening_state(observation)
            ):
                active = True
                return _fifth_hire_action(observation)
            active = False
            return parent_agent(observation, configuration)
        if not active:
            return parent_agent(observation, configuration)

        if step == 2 and (
            not _expected_step2_merge_state(observation)
            or not _expected_step2_public_state(observation, expected_step2_public)
        ):
            return fallback_to_parent(observation, configuration, step,
                                      "step2_snapshot_guard")
        own, _ = _farm_pair(observation)
        try:
            raw = donor_schedule_action(observation, configuration)
        except Exception:
            return fallback_to_parent(observation, configuration, step,
                                      "donor_action_exception")
        mapped = remap_donor_hands(raw, len(own.get("hands", [])))
        if mapped is not None:
            return mapped
        reason = ("donor_worker_count_below_minimum"
                  if len(own.get("hands", [])) < 5
                  else "donor_schedule_shape_mismatch")
        return fallback_to_parent(observation, configuration, step,
                                  reason)

    agent.telemetry = telemetry
    return agent
