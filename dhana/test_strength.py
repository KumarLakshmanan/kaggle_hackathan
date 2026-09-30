"""Fast invariant tests for the new overlay; no third-party dependencies."""
import copy
import ast
import unittest
from pathlib import Path


OVERLAY = Path(__file__).with_name("market_overlay.py").read_text(encoding="utf-8")


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.action = {"farmer": ["PASS"], "hands": [], "market": []}
        self.ns = {"agent": lambda obs, cfg=None: self.action}
        exec(compile(OVERLAY, "market_overlay.py", "exec"), self.ns)
        farm = {"money": 10, "farmer": [0, 0], "hands": [],
                "tiles": [[{"animal": "COW", "yield_units": 2, "cared_today": True}]]}
        self.obs = {"step": 100, "player": 0, "farms": [farm, {"money": 20}],
                    "private": {"shed": {}, "inventories": [{}]}}

    def test_opening_preserves_inventory_and_tail(self):
        self.ns["DHANA_OPENING_QUANTITY"] = 11
        self.obs["step"] = 0
        self.action["market"] = [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 15], ["BUY_SEED", "WHEAT", 1]]
        before = copy.deepcopy(self.action)
        result = self.ns["agent"](self.obs)
        self.assertEqual(result["market"], [["BUY_PRODUCT", "WHEAT", 11], ["SELL", "WHEAT", 6], ["BUY_SEED", "WHEAT", 1]])
        self.assertEqual(self.action, before)

    def test_unrecognized_opening_unchanged(self):
        self.obs["step"] = 0
        self.action["market"] = [["BUY_PRODUCT", "WHEAT", 5]]
        self.assertIs(self.ns["agent"](self.obs), self.action)

    def test_redundant_care_harvests_without_mutation(self):
        self.action["farmer"] = ["CARE"]
        before = copy.deepcopy((self.obs, self.action))
        self.assertEqual(self.ns["agent"](self.obs)["farmer"], ["HARVEST"])
        self.assertEqual((self.obs, self.action), before)
        self.assertEqual(self.ns["_DHANA_STATS"]["idle_recoveries"], 1)

    def test_useful_commands_never_replaced(self):
        self.obs["farms"][0]["tiles"][0][0]["cared_today"] = False
        for command in (["CARE"], ["MOVE", "E"], ["FEED"], ["WATER"], ["HARVEST"]):
            self.action["farmer"] = command
            self.assertIs(self.ns["agent"](self.obs), self.action)

    def test_no_change_when_ahead_or_equal(self):
        for cash in (20, 21):
            self.obs["farms"][0]["money"] = cash
            self.assertIs(self.ns["agent"](self.obs), self.action)

    def test_phase_and_stock_guards(self):
        for step in (0, 71, 672, 718):
            self.obs["step"] = step
            self.assertIs(self.ns["agent"](self.obs), self.action)
        self.obs["step"] = 100
        self.obs["private"]["shed"] = {"WHEAT": 76}
        self.assertIs(self.ns["agent"](self.obs), self.action)

    def test_fertilizer_is_collected_only_when_available(self):
        tile = self.obs["farms"][0]["tiles"][0][0]
        tile["yield_units"] = 0
        self.assertIs(self.ns["agent"](self.obs), self.action)
        tile["fertilizer_available"] = True
        self.assertEqual(self.ns["agent"](self.obs)["farmer"], ["COLLECT_FERTILIZER"])

    def test_nonrenewable_crops_not_harvested_early(self):
        self.obs["farms"][0]["tiles"][0][0] = {"crop": "MELON", "yield_units": 10}
        self.assertIs(self.ns["agent"](self.obs), self.action)

    def test_two_idle_workers_do_not_claim_same_tile(self):
        self.obs["farms"][0]["hands"] = [[0, 0]]
        self.action["hands"] = [["PASS"]]
        result = self.ns["agent"](self.obs)
        self.assertEqual(result["farmer"], ["HARVEST"])
        self.assertEqual(result["hands"], [["PASS"]])

    def test_optional_overlay_error_falls_back(self):
        self.obs["farms"][0]["tiles"] = []
        self.assertIs(self.ns["agent"](self.obs), self.action)
        self.assertEqual(self.ns["_DHANA_STATS"]["overlay_errors"], 1)

    def test_new_episode_resets_telemetry(self):
        self.ns["agent"](self.obs)
        self.obs["step"] = 0
        self.ns["agent"](self.obs)
        self.assertEqual(self.ns["_DHANA_STATS"], {"idle_recoveries": 0, "overlay_errors": 0})

    def test_conservative_opening_default(self):
        self.assertEqual(self.ns["DHANA_OPENING_QUANTITY"], 15)


class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(Path(__file__).with_name("candidate.py").read_text(encoding="utf-8"))
        cls.functions = {}
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.name != "agent":
                continue
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            for version, key in ((51, "_V51_MAIN_AGENT"), (52, "_V52_BASE_AGENT")):
                if key in names:
                    cls.functions[version] = compile(ast.Module(body=[node], type_ignores=[]), "controller", "exec")
        assert set(cls.functions) == {51, 52}

    def controller(self, version, selected, fail=False):
        calls = []
        alternate_action = {"market": [["SELL", "WHEAT", 1]]}
        def base(obs, cfg):
            calls.append("base")
            return {"market": []}
        def alternate(obs, cfg):
            calls.append("alternate")
            if fail:
                raise ValueError("test failure")
            return alternate_action
        if version == 51:
            ns = {"_v51_use_main_for": lambda obs: selected, "_V51_MAIN_AGENT": base,
                  "_V51_HAIDE_AGENT": alternate, "_v51_copy": copy}
        else:
            ns = {"_v52_use_rank41_for": lambda obs: selected, "_V52_BASE_AGENT": base,
                  "_V52_RANK41_AGENT": alternate, "_v52_copy": copy}
        exec(self.functions[version], ns)
        return ns["agent"], calls, alternate_action

    def test_prefix_warms_both_controllers(self):
        for version in (51, 52):
            for selected in (False, True):
                agent, calls, _ = self.controller(version, selected)
                agent({"step": 72})
                self.assertEqual(calls, ["base", "alternate"])

    def test_only_selected_controller_runs_after_prefix(self):
        for version in (51, 52):
            for selected in (False, True):
                agent, calls, _ = self.controller(version, selected)
                agent({"step": 73})
                use_alternate = (not selected) if version == 51 else selected
                self.assertEqual(calls, ["alternate" if use_alternate else "base"])

    def test_alternate_failure_falls_back(self):
        for version in (51, 52):
            selected = version == 52
            for step in (10, 73):
                agent, calls, _ = self.controller(version, selected, fail=True)
                self.assertEqual(agent({"step": step}), {"market": []})
                self.assertEqual(set(calls), {"alternate", "base"})

    def test_alternate_actions_are_detached(self):
        for version in (51, 52):
            agent, _, stored = self.controller(version, version == 52)
            result = agent({"step": 73})
            result["market"][0][2] = 999
            self.assertEqual(stored["market"][0][2], 1)


if __name__ == "__main__":
    unittest.main()
