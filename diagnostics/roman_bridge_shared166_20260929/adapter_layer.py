"""Static, reviewable Roman opening bridge; not yet qualified for play.

The layer is deliberately separate from both frozen source candidates.  The
caller supplies the exact 7b parent agent and a *raw donor schedule* callback
(for example, the shared166 route selector before its worker-indexed repair
transforms).  Do not pass the donor's fully transformed agent here: its
hire-recovery queues use donor hand indices and would need to be remapped too.

No module-level game state, simulator, Kaggle API, or file access is used.
"""
from copy import deepcopy


PARENT_SHA256 = "7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2"
DONOR_SHA256 = "fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849"
PANEL_SHA256 = "bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795"

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


def make_agent(parent_agent, donor_schedule_action):
    """Build a candidate wrapper without mutating either frozen source.

    Step 0 delegates unchanged to the exact parent.  At step 1, the exact
    public trigger plus a private-state guard selects one NORTH move, four
    PASSes, and the fifth HIRE.  From step 2 onward, it uses the donor's raw
    route action with commands reordered for the actual hand indices.

    If the guarded opening state is absent, the parent remains in control.  If
    an activated game's worker count disagrees with the donor schedule, return
    a legal all-PASS action rather than issue commands to the wrong workers;
    this fail-closed path is a diagnostic safeguard, not promotion evidence.
    """
    active = False
    bridge_failed = False

    def pass_action(observation):
        own, _ = _farm_pair(observation)
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in own.get("hands", [])],
            "market": [],
        }

    def agent(observation, configuration=None):
        nonlocal active, bridge_failed
        step = int(observation.get("step", -1))
        if step == 0:
            active = False
            bridge_failed = False
            return parent_agent(observation, configuration)
        if bridge_failed:
            return pass_action(observation)
        if step == 1:
            if _public_trigger(observation) and _expected_parent_opening_state(observation):
                active = True
                return _fifth_hire_action(observation)
            active = False
            return parent_agent(observation, configuration)
        if not active:
            return parent_agent(observation, configuration)

        if step == 2 and not _expected_step2_merge_state(observation):
            bridge_failed = True
            return pass_action(observation)
        own, _ = _farm_pair(observation)
        raw = donor_schedule_action(observation, configuration)
        mapped = remap_donor_hands(raw, len(own.get("hands", [])))
        if mapped is not None:
            return mapped
        bridge_failed = True
        return pass_action(observation)

    return agent
