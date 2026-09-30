"""Focused scheduler mechanics tests against Kaggriculture 1.32.7."""

from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from kaggle_environments import __version__ as KAGGLE_ENVIRONMENTS_VERSION
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine


ROOT = Path(__file__).resolve().parent
CANDIDATE_PATH = ROOT / "candidate.py"
ECONOMICS_PATH = ROOT / "economics.py"


class _FallbackEconomicsLoader:
    """Keep scheduler tests runnable while the separately owned sidecar is absent."""

    def create_module(self, spec):
        return types.ModuleType(spec.name)

    def exec_module(self, module):
        # These cases pin jobs directly and do not test investment scoring.
        module.investment_values = lambda observation, configuration, counts: {}
        module.price = lambda item, inventory, params: engine.market_price(
            item, inventory, params)


def _load_candidate():
    module_name = "_dynamic_planner_scheduler_under_test"
    spec = importlib.util.spec_from_file_location(module_name, CANDIDATE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    if ECONOMICS_PATH.exists():
        spec.loader.exec_module(module)
    else:
        # candidate.py loads its adjacent economics.py with spec_from_file_location.
        # Substitute only that missing sidecar; use the real file automatically once
        # the economics task creates it.
        original = importlib.util.spec_from_file_location

        def with_test_sidecar(name, location, *args, **kwargs):
            if name == module_name + "_economics":
                return importlib.machinery.ModuleSpec(
                    name, _FallbackEconomicsLoader())
            return original(name, location, *args, **kwargs)

        with patch.object(importlib.util, "spec_from_file_location", with_test_sidecar):
            spec.loader.exec_module(module)
    return module


candidate = _load_candidate()


def _new_env(step: int = 3):
    """Create the installed engine's real state and place it at a test turn."""
    env = make("kaggriculture", configuration={"seed": 7, "episodeSteps": 720}, debug=True)
    obs = env.state[0].observation
    obs["step"] = step
    obs["day"] = step // 24
    obs["hour"] = step % 24
    return env, obs, obs["farms"][0], obs["private"]


def _workers(farm, private, positions):
    farm["farmer"] = list(positions[0])
    farm["hands"] = [list(pos) for pos in positions[1:]]
    # Model already-hired hands in this focused mid-day state. No HIRE action is
    # being tested, so preserve all other farm and private-state fields as-is.
    farm["hires_today"] = len(positions) - 1
    private["inventories"] = [{} for _ in positions]


def _pass_action():
    return {"farmer": ["PASS"], "hands": [], "market": []}


def _apply_turn(env, action):
    env.step([action, _pass_action()])
    return env.state[0].observation


class SchedulerEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if KAGGLE_ENVIRONMENTS_VERSION != "1.32.7":
            raise AssertionError(
                f"expected Kaggriculture engine 1.32.7, got {KAGGLE_ENVIRONMENTS_VERSION}")

    def _planner_with_jobs(self, obs, jobs):
        planner = candidate.Planner(obs, {"episodeSteps": 720, "turnsPerDay": 24})
        # Initialize today's state first; then pin the jobs under test so test
        # outcomes do not depend on economics or project-ranking heuristics.
        planner.read(obs)
        planner.jobs = jobs
        return planner

    def test_seed_purchase_is_not_used_until_next_turn_and_plant_is_atomic(self):
        env, obs, farm, private = _new_env(step=3)
        positions = [(3, 3), (4, 3)]
        _workers(farm, private, positions)
        private["seeds"]["WHEAT"] = 0
        jobs = {
            idx: {"kind": "invest", "target": pos, "item": "WHEAT", "value": 0}
            for idx, pos in enumerate(positions)
        }
        planner = self._planner_with_jobs(obs, jobs)

        request = planner.run(obs)
        self.assertEqual(request["farmer"], ["PASS"])
        self.assertEqual(request["hands"], [["PASS"]])
        self.assertIn(["BUY_SEED", "WHEAT", 2], request["market"])

        # Unit actions precede market orders: neither plot is planted on the
        # purchase turn, and the newly purchased seeds become available after it.
        obs = _apply_turn(env, request)
        farm = obs["farms"][0]
        self.assertIsNone(farm["tiles"][3][3])
        self.assertIsNone(farm["tiles"][3][4])
        self.assertEqual(obs["private"]["seeds"]["WHEAT"], 2)

        plant = planner.run(obs)
        self.assertEqual(plant["farmer"], ["PLANT", "WHEAT"])
        self.assertEqual(plant["hands"], [["PLANT", "WHEAT"]])
        self.assertFalse(any(order[:2] == ["BUY_SEED", "WHEAT"] for order in plant["market"]))
        obs = _apply_turn(env, plant)
        farm = obs["farms"][0]
        self.assertEqual(farm["tiles"][3][3]["crop"], "WHEAT")
        self.assertEqual(farm["tiles"][3][4]["crop"], "WHEAT")
        self.assertEqual(obs["private"]["seeds"]["WHEAT"], 0)

        # The engine rejects an over-request atomically rather than planting a
        # prefix, which makes the scheduler's shared seed accounting important.
        farm["tiles"][3][3] = None
        farm["tiles"][3][4] = None
        obs["private"]["seeds"]["WHEAT"] = 1
        env.step([
            {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]], "market": []},
            _pass_action(),
        ])
        farm = env.state[0].observation["farms"][0]
        self.assertIsNone(farm["tiles"][3][3])
        self.assertIsNone(farm["tiles"][3][4])
        self.assertEqual(env.state[0].observation["private"]["seeds"]["WHEAT"], 1)

    def test_shared_shed_pickup_is_reserved_across_workers(self):
        env, obs, farm, private = _new_env(step=3)
        positions = [(4, 4), (5, 4)]  # both are engine-valid shed-access tiles
        _workers(farm, private, positions)
        private["shed"]["WHEAT"] = 1
        farm["tiles"][3][3] = engine._new_animal("GOOSE", 0)
        farm["tiles"][2][3] = engine._new_animal("GOOSE", 0)
        jobs = {
            0: {"kind": "service", "target": (3, 3), "item": "GOOSE",
                "ops": ["FEED", "CARE"], "value": 10},
            1: {"kind": "service", "target": (3, 2), "item": "GOOSE",
                "ops": ["FEED", "CARE"], "value": 10},
        }
        planner = self._planner_with_jobs(obs, jobs)

        action = planner.run(obs)
        self.assertEqual(action["farmer"], ["PICKUP", "WHEAT", 1])
        self.assertEqual(action["hands"], [["PASS"]])
        obs = _apply_turn(env, action)
        farm = obs["farms"][0]
        inventories = obs["private"]["inventories"]
        self.assertEqual(inventories[0].get("WHEAT"), 1)
        self.assertNotIn("WHEAT", inventories[1])
        self.assertEqual(obs["private"]["shed"]["WHEAT"], 2)  # market replenished it
        self.assertFalse(farm["tiles"][3][3]["fed_today"])
        self.assertFalse(farm["tiles"][2][3]["fed_today"])

    def test_final_last_step_deposits_then_sells_in_the_same_engine_turn(self):
        env, obs, farm, private = _new_env(step=718)
        _workers(farm, private, [(4, 4)])
        private["inventories"] = [{"CARROT": 3}]
        before_money = farm["money"]
        planner = candidate.Planner(obs, {"episodeSteps": 720, "turnsPerDay": 24})

        action = planner.run(obs)
        self.assertEqual(action["farmer"], ["DROP"])
        self.assertIn(["SELL", "CARROT", 3], action["market"])
        obs = _apply_turn(env, action)
        farm = obs["farms"][0]
        self.assertEqual(obs["private"]["inventories"][0], {})
        self.assertEqual(obs["private"]["shed"].get("CARROT", 0), 0)
        self.assertGreater(farm["money"], before_money)
        self.assertEqual(env.state[0].status, "DONE")

    def test_crop_harvest_waits_for_engine_minimum_age_then_harvests(self):
        # At age 1, annual wheat has its planting-day unit but remains
        # unharvestable: the scheduler waters it and leaves the plant in place.
        env, obs, farm, private = _new_env(step=27)  # day 1, hour 3
        target = (3, 3)
        _workers(farm, private, [target])
        farm["tiles"][target[1]][target[0]] = engine._new_plant("WHEAT", 0, 24)
        planner = candidate.Planner(obs, {"episodeSteps": 720, "turnsPerDay": 24})
        planner.read(obs)
        planner.jobs = {0: planner.service_job(target, farm["tiles"][3][3])}

        action = planner.run(obs)
        self.assertNotEqual(action["farmer"], ["HARVEST"])
        obs = _apply_turn(env, action)
        farm = obs["farms"][0]
        self.assertEqual(farm["tiles"][3][3]["kind"], "PLANT")
        self.assertNotIn("WHEAT", obs["private"]["inventories"][0])

        # At the engine's first eligible age with a mature yield, harvest is
        # emitted and the engine transfers all units to worker cargo.
        env, obs, farm, private = _new_env(step=51)  # day 2, hour 3
        _workers(farm, private, [target])
        ripe = engine._new_plant("WHEAT", 0, 24)
        ripe["yield_units"] = engine.CROPS["WHEAT"]["max_yield"]
        ripe["watered_today"] = True
        ripe["consecutive_unwatered"] = 0
        farm["tiles"][3][3] = ripe
        planner = candidate.Planner(obs, {"episodeSteps": 720, "turnsPerDay": 24})
        planner.read(obs)
        planner.jobs = {0: planner.service_job(target, ripe)}

        action = planner.run(obs)
        self.assertEqual(action["farmer"], ["HARVEST"])
        obs = _apply_turn(env, action)
        farm = obs["farms"][0]
        self.assertIsNone(farm["tiles"][3][3])
        self.assertEqual(obs["private"]["inventories"][0]["WHEAT"], 6)

    def test_feed_never_emits_without_wheat_and_market_supplies_it(self):
        env, obs, farm, private = _new_env(step=3)
        target = (3, 3)
        _workers(farm, private, [target])
        farm["tiles"][3][3] = engine._new_animal("GOOSE", 0)
        private["shed"]["WHEAT"] = 0
        planner = candidate.Planner(obs, {"episodeSteps": 720, "turnsPerDay": 24})
        planner.read(obs)
        planner.jobs = {0: {"kind": "service", "target": target, "item": "GOOSE",
                            "ops": ["FEED", "CARE"], "value": 10}}

        action = planner.run(obs)
        self.assertNotEqual(action["farmer"], ["FEED"])
        self.assertIn(["BUY_PRODUCT", "WHEAT", 1], action["market"])
        obs = _apply_turn(env, action)
        farm = obs["farms"][0]
        self.assertFalse(farm["tiles"][3][3]["fed_today"])
        self.assertEqual(obs["private"]["shed"]["WHEAT"], 1)
        self.assertNotIn("WHEAT", obs["private"]["inventories"][0])


if __name__ == "__main__":
    unittest.main()
