# FIX (bootstrap): plain `pip install kaggle-environments` resolves its full
# dependency graph against Kaggle's existing stack, causing pip to backtrack
# for a long time. `kaggriculture.py` only needs stdlib/jsonschema, so `--no-deps` skips that.
!pip install -q --no-deps "kaggle-environments>=1.32.2,<1.33"
!python -c "import jsonschema, requests" 2>/dev/null || pip install -q jsonschema requests

# Smoke-test: import + build the one env we use, so a missing dependency fails
# loudly here instead of silently inside Part 10's ImportError guard (which
# would otherwise just quietly flip HAVE_KAGGLE_ENV=False).
import kaggle_environments
from kaggle_environments import make as _smoke_make
_smoke_make("kaggriculture")
print(f"kaggle_environments {kaggle_environments.__version__} OK -- kaggriculture env registered")

import math

import numpy as np

from dataclasses import dataclass, field

from typing import Any, Optional

SEASON_DAYS = 30

TURNS_PER_DAY = 24

BOARD_SIZE = 10

TILES_PER_QUADRANT = 25

MAX_MARKET_ORDERS_PER_TURN = 10

TERMINAL_TURN_THRESHOLD = 700

CROP_INFO = {
    "WHEAT":      dict(seed_cost=10,  base_price=25,  first_yield=2,  max_yield_day=4,  max_yield=6, max_yield_unfert=4, ongoing=False),
    "CARROT":     dict(seed_cost=20,  base_price=35,  first_yield=2,  max_yield_day=3,  max_yield=4, max_yield_unfert=3, ongoing=False),
    "TOMATO":     dict(seed_cost=50,  base_price=60,  first_yield=8,  max_yield_day=8,  max_yield=4, ongoing=True, interval=1),
    "STRAWBERRY": dict(seed_cost=100, base_price=120, first_yield=10, max_yield_day=10, max_yield=4, ongoing=True, interval=2),
    "MELON":      dict(seed_cost=80,  base_price=250, first_yield=10, max_yield_day=12, max_yield=6, max_yield_unfert=6, ongoing=False),
}

_plant_maturities = sorted(v["max_yield_day"] for v in CROP_INFO.values())

PLANT_MATURITY_REF = _plant_maturities[len(_plant_maturities) // 2]

PLANT_MATURITY_SCALE = max(1.0, (max(_plant_maturities) - min(_plant_maturities)) / 2.0)

ANIMAL_INFO = {
    "GOOSE": dict(cost=300, product="EGG",  base_price=50,  first_yield=4, interval=1, max_held=4, structure="COOP"),
    "COW":   dict(cost=400, product="MILK", base_price=160, first_yield=8, interval=2, max_held=6, structure="PASTURE"),
    "SHEEP": dict(cost=500, product="WOOL", base_price=200, first_yield=6, interval=3, max_held=6, structure="PASTURE"),
}

MARKET_PARAMS = {
    "WHEAT":      dict(base=25,  I0=10000, T=400, below=("sqrt", 0.80),   above=("log", 0.20)),
    "CARROT":     dict(base=35,  I0=10000, T=450, below=("hinge", 1.00),  above=("sqrt", 0.70)),
    "TOMATO":     dict(base=60,  I0=10000, T=200, below=("hinge", 0.40),  above=("sqrt", 0.60)),
    "STRAWBERRY": dict(base=120, I0=10000, T=100, below=("sqrt", 0.70),   above=("linear", 1.60)),
    "MELON":      dict(base=250, I0=10000, T=300, below=("log", 0.20),    above=("sq", 3.60)),
    "EGG":        dict(base=50,  I0=10000, T=332, below=("hinge", 0.40),  above=("log", 0.20)),
    "MILK":       dict(base=160, I0=10000, T=122, below=("sqrt", 0.60),   above=("linear", 1.60)),
    "WOOL":       dict(base=200, I0=10000, T=105, below=("log", 0.20),    above=("sq", 3.20)),
    "FERTILIZER": dict(base=100, I0=10000, T=200, below=("linear", 0.40), above=("linear", 0.40)),
}

PRICE_RATIO_ITEMS = list(MARKET_PARAMS.keys())

CROP_ORDER = list(CROP_INFO.keys())

SHOP_DEMAND = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

TOWN_SHOP_UNLOCK_INTERVAL = 3

MAX_HANDS_SEARCH_CEILING = 100

DAY_PHASE_WINDOW = 3

N_DAY_PHASES = 10

_DAY_PHASE_BONUS = [0] * N_DAY_PHASES

def _day_phase_idx(day: int) -> int:
    idx = (max(day, 0)) // DAY_PHASE_WINDOW
    return min(idx, N_DAY_PHASES - 1)

import random as _ppo_random

PPO_FLOOR_FEATURE_NAMES = [
    "bias", "owned_tiles_norm", "n_quadrants_norm", "cash_ratio",
    "discretionary_cash_ratio", "mandatory_cost_ratio", "season_progress",
    "current_workers_norm", "servicing_saturation_norm", "backlog_ratio",
    "empty_tile_ratio",
    "mandatory_unsatisfied_ratio",
    "plant_feasibility_signal",
]

PPO_CAP_FEATURE_NAMES = [
    "bias", "owned_tiles_norm", "n_quadrants_norm", "cash_ratio",
    "season_progress", "current_workers_norm", "backlog_ratio",
]

PPO_FLOOR_MULT_MIN, PPO_FLOOR_MULT_MAX = 0.05, 0.50

PPO_CAP_MIN, PPO_CAP_MAX = 2, 12

PPO_MARGIN_MIN, PPO_MARGIN_MAX = 1.00, 1.50

PPO_STEEPNESS_MIN, PPO_STEEPNESS_MAX = 2.0, 10.0

PPO_UTIL_THRESH_MIN, PPO_UTIL_THRESH_MAX = 0.30, 0.95

PPO_HIRE_BATCH_MIN, PPO_HIRE_BATCH_MAX = 1, 6

PPO_MARGIN_FEATURE_NAMES = [
    "bias", "owned_tiles_norm", "n_quadrants_norm", "cash_ratio",
    "season_progress", "current_workers_norm", "servicing_saturation_norm",
    "backlog_ratio",
]

PPO_STEEPNESS_FEATURE_NAMES = [
    "bias", "cash_ratio", "discretionary_cash_ratio", "servicing_saturation_norm",
    "backlog_ratio", "season_progress",
]

PPO_UTIL_THRESH_FEATURE_NAMES = [
    "bias", "cash_ratio", "discretionary_cash_ratio", "n_quadrants_norm",
    "season_progress",
]

PPO_HIRE_BATCH_FEATURE_NAMES = [
    "bias", "cash_ratio", "discretionary_cash_ratio", "season_progress",
    "current_workers_norm",
]

PPO_IDLE_START_MIN, PPO_IDLE_START_MAX = 1.0, 4.0

PPO_IDLE_FULL_MIN, PPO_IDLE_FULL_MAX = 5.0, 14.0

PPO_IDLE_START_FEATURE_NAMES = [
    "bias", "cash_ratio", "discretionary_cash_ratio", "servicing_saturation_norm",
    "backlog_ratio", "season_progress",
]

PPO_IDLE_FULL_FEATURE_NAMES = [
    "bias", "cash_ratio", "discretionary_cash_ratio", "n_quadrants_norm",
    "season_progress",
]

PPO_UTIL_EXP_MIN, PPO_UTIL_EXP_MAX = 1.0, 6.0

PPO_UTIL_FLOOR_MIN, PPO_UTIL_FLOOR_MAX = 0.01, 0.50

PPO_UTIL_EXP_FEATURE_NAMES = [
    "bias", "cash_ratio", "discretionary_cash_ratio", "n_quadrants_norm",
    "backlog_ratio", "season_progress",
]

PPO_UTIL_FLOOR_FEATURE_NAMES = [
    "bias", "cash_ratio", "discretionary_cash_ratio", "n_quadrants_norm",
    "season_progress",
]

def _ppo_sigmoid(x):
    x = max(-30.0, min(30.0, x))
    return 1.0 / (1.0 + math.exp(-x))

def _ppo_inv_sigmoid(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1.0 - p))

class ReinforceFloorCapController:

    def __init__(self, lr=0.02, floor_std=0.15, cap_std=0.4, seed=0):
        self.enabled = False
        self.training = False
        self.lr = lr
        self.floor_std = floor_std   
        self.cap_std = cap_std       
        self._rng = _ppo_random.Random(seed)
        self.floor_w = {name: 0.0 for name in PPO_FLOOR_FEATURE_NAMES}
        target_floor_sig = (0.30 - PPO_FLOOR_MULT_MIN) / (PPO_FLOOR_MULT_MAX - PPO_FLOOR_MULT_MIN)
        self.floor_w["bias"] = _ppo_inv_sigmoid(target_floor_sig)

        self.cap_w = {name: 0.0 for name in PPO_CAP_FEATURE_NAMES}
        cap_sig_q1 = (3 - PPO_CAP_MIN) / (PPO_CAP_MAX - PPO_CAP_MIN)   
        cap_sig_q2 = (5 - PPO_CAP_MIN) / (PPO_CAP_MAX - PPO_CAP_MIN)   
        raw_q1 = _ppo_inv_sigmoid(cap_sig_q1)
        raw_q2 = _ppo_inv_sigmoid(cap_sig_q2)
        w_nq = (raw_q2 - raw_q1) / (1.0 / 3.0)
        self.cap_w["bias"] = raw_q1
        self.cap_w["n_quadrants_norm"] = w_nq

        self.enabled_stage2 = False
        self.margin_w = {name: 0.0 for name in PPO_MARGIN_FEATURE_NAMES}
        target_margin_sig = (1.15 - PPO_MARGIN_MIN) / (PPO_MARGIN_MAX - PPO_MARGIN_MIN)
        self.margin_w["bias"] = _ppo_inv_sigmoid(target_margin_sig)

        self.steepness_w = {name: 0.0 for name in PPO_STEEPNESS_FEATURE_NAMES}
        target_steep_sig = (6.0 - PPO_STEEPNESS_MIN) / (PPO_STEEPNESS_MAX - PPO_STEEPNESS_MIN)
        self.steepness_w["bias"] = _ppo_inv_sigmoid(target_steep_sig)

        self.threshold_w = {name: 0.0 for name in PPO_UTIL_THRESH_FEATURE_NAMES}
        target_thresh_sig = (0.55 - PPO_UTIL_THRESH_MIN) / (PPO_UTIL_THRESH_MAX - PPO_UTIL_THRESH_MIN)
        self.threshold_w["bias"] = _ppo_inv_sigmoid(target_thresh_sig)
        self.margin_std = 0.08
        self.steepness_std = 0.8
        self.threshold_std = 0.05

        self.idle_start_w = {name: 0.0 for name in PPO_IDLE_START_FEATURE_NAMES}
        target_idle_start_sig = (2.0 - PPO_IDLE_START_MIN) / (PPO_IDLE_START_MAX - PPO_IDLE_START_MIN)
        self.idle_start_w["bias"] = _ppo_inv_sigmoid(target_idle_start_sig)

        self.idle_full_w = {name: 0.0 for name in PPO_IDLE_FULL_FEATURE_NAMES}
        target_idle_full_sig = (8.0 - PPO_IDLE_FULL_MIN) / (PPO_IDLE_FULL_MAX - PPO_IDLE_FULL_MIN)
        self.idle_full_w["bias"] = _ppo_inv_sigmoid(target_idle_full_sig)
        self.idle_start_std = 0.3
        self.idle_full_std = 0.8
        self.util_exp_w = {name: 0.0 for name in PPO_UTIL_EXP_FEATURE_NAMES}
        target_util_exp_sig = (3.0 - PPO_UTIL_EXP_MIN) / (PPO_UTIL_EXP_MAX - PPO_UTIL_EXP_MIN)
        self.util_exp_w["bias"] = _ppo_inv_sigmoid(target_util_exp_sig)

        self.util_floor_w = {name: 0.0 for name in PPO_UTIL_FLOOR_FEATURE_NAMES}
        target_util_floor_sig = (0.05 - PPO_UTIL_FLOOR_MIN) / (PPO_UTIL_FLOOR_MAX - PPO_UTIL_FLOOR_MIN)
        self.util_floor_w["bias"] = _ppo_inv_sigmoid(target_util_floor_sig)
        self.util_exp_std = 0.4
        self.util_floor_std = 0.02

        self.hire_batch_w = {name: 0.0 for name in PPO_HIRE_BATCH_FEATURE_NAMES}
        target_hire_batch_sig = (1.3 - PPO_HIRE_BATCH_MIN) / (PPO_HIRE_BATCH_MAX - PPO_HIRE_BATCH_MIN)
        self.hire_batch_w["bias"] = _ppo_inv_sigmoid(target_hire_batch_sig)
        self.hire_batch_std = 0.5

        self._episode_trace = []   
        self._trace_index_by_key = {}   
        self._day_cache = {}       
        self._baseline = None       
        self._baseline_alpha = 0.2

        self._last_mandatory_unsatisfied_ratio = 0.0
        self._starvation_by_day = {}

        self.reward_horizon_days = 5
        self._local_baseline = None
        self._local_baseline_alpha = 0.2
        self._nw_history = {}   
        self.STARVATION_PENALTY_SCALE = 3000.0   

        # FIX (gate coverage): floorcap had no convergence diagnostic, so the
        # stage early-stop gate could never check it. Track per-head raw-mean
        # history to measure signal_std/noise_std like alpha/animal do.
        self._floor_mean_history = []
        self._cap_mean_history = []
        self._margin_mean_history = []
        self._steep_mean_history = []
        self._thresh_mean_history = []
        self._idle_start_mean_history = []
        self._idle_full_mean_history = []
        self._util_exp_mean_history = []
        self._util_floor_mean_history = []
        self._hire_batch_mean_history = []

    def reset_episode(self):
        self._episode_trace = []
        self._trace_index_by_key = {}
        self._day_cache = {}
        self._last_mandatory_unsatisfied_ratio = 0.0
        self._starvation_by_day = {}
        self._nw_history = {}

    def record_schedule_outcome(self, ws: "WorldState", schedule_plan: "SchedulePlan"):
        n_workers = 1 + len(ws.hands)
        n_unsatisfied = len(schedule_plan.mandatory_unsatisfied)
        raw_ratio = n_unsatisfied / max(1, n_workers * 3.0)
        self._last_mandatory_unsatisfied_ratio = math.tanh(raw_ratio)
        self._starvation_by_day.setdefault(ws.day, []).append(raw_ratio)

    def _record_net_worth(self, ws: "WorldState"):
        if ws.day not in self._nw_history:
            self._nw_history[ws.day] = _estimate_net_worth(ws)

    def _local_delta(self, decision_day: int) -> float:
        nw0 = self._nw_history.get(decision_day)
        if nw0 is None:
            return 0.0
        target_day = decision_day + self.reward_horizon_days
        candidate_days = [d for d in self._nw_history if d >= target_day]
        if candidate_days:
            nw1 = self._nw_history[min(candidate_days)]
        else:
            nw1 = self._nw_history[max(self._nw_history)]
        return nw1 - nw0

    def _avg_starvation(self, decision_day: int) -> float:
        obs = self._starvation_by_day.get(decision_day)
        if not obs:
            return 0.0
        return sum(obs) / len(obs)

    def _features(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                  discretionary_cash: float = None, mandatory_future_cost: float = None) -> dict:
        owned = 0
        for row in ws.tiles:
            for t in row:
                if t != "LOCKED":
                    owned += 1
        n_quadrants = max(1, getattr(ws, "n_quadrants", 1))
        current_workers = 1 + len(ws.hands)
        season_days = getattr(ws, "season_days", 30) or 30
        season_progress = min(1.0, ws.day / max(1, season_days))
        money = max(0.0, ws.money)
        cash_ratio = math.tanh(money / 2000.0)          

        if discretionary_cash is not None and discretionary_cash != float("inf"):
            discretionary_cash_ratio = math.tanh(max(0.0, discretionary_cash) / 2000.0)
        else:
            discretionary_proxy = max(0.0, money - RESERVE_MIN_OPERATING_CASH)
            discretionary_cash_ratio = math.tanh(discretionary_proxy / 2000.0)

        mandatory_cost_ratio = 0.0
        if mandatory_future_cost is not None:
            mandatory_cost_ratio = math.tanh(max(0.0, mandatory_future_cost) / 1000.0)

        if fa is not None:
            backlog_raw = (len(fa.need_water_tiles) + len(fa.ready_harvest_tiles)
                           + len(fa.hungry_animal_tiles) + len(fa.product_ready_tiles))
            backlog_ratio = math.tanh(backlog_raw / max(1.0, current_workers * 6.0))
            servicing_saturation_norm = math.tanh(backlog_raw / max(1, current_workers * 4.0))
            empty_tile_ratio = math.tanh(len(fa.empty_tiles) / 50.0)
        else:
            backlog_ratio = 0.0
            servicing_saturation_norm = math.tanh(owned / max(1, current_workers * 8.0))
            empty_tile_ratio = 0.0

        try:
            mem_ref = _PACING_CURRENT_MEM.get("mem")
        except NameError:
            mem_ref = None
        plant_feasibility = plant_feasibility_signal(ws, mem_ref) if mem_ref is not None else 0.0

        return {
            "bias": 1.0,
            "owned_tiles_norm": math.tanh(owned / 50.0),
            "n_quadrants_norm": (n_quadrants - 1) / 3.0,   
            "cash_ratio": cash_ratio,
            "discretionary_cash_ratio": discretionary_cash_ratio,
            "mandatory_cost_ratio": mandatory_cost_ratio,
            "season_progress": season_progress,
            "current_workers_norm": math.tanh(current_workers / 15.0),
            "servicing_saturation_norm": servicing_saturation_norm,
            "backlog_ratio": backlog_ratio,
            "empty_tile_ratio": empty_tile_ratio,
            "mandatory_unsatisfied_ratio": self._last_mandatory_unsatisfied_ratio,
            "plant_feasibility_signal": plant_feasibility,
            "day": ws.day,
        }

    def _linear(self, weights: dict, feats: dict, names: list) -> float:
        return sum(weights[n] * feats.get(n, 0.0) for n in names)

    def get_floor_mult(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                        discretionary_cash: float = None, mandatory_future_cost: float = None) -> float:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["floor_mult"]

    def get_cap_per_quadrant(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                              discretionary_cash: float = None, mandatory_future_cost: float = None) -> int:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["cap_per_quadrant"]

    def get_coverage_margin(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                             discretionary_cash: float = None, mandatory_future_cost: float = None) -> float:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["coverage_margin"]

    def get_throttle_steepness(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                                discretionary_cash: float = None, mandatory_future_cost: float = None) -> float:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["throttle_steepness"]

    def get_utilization_threshold(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                                   discretionary_cash: float = None, mandatory_future_cost: float = None) -> float:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["utilization_threshold"]

    def get_idle_cash_start(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                             discretionary_cash: float = None, mandatory_future_cost: float = None) -> float:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["idle_cash_start"]

    def get_idle_cash_full(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                            discretionary_cash: float = None, mandatory_future_cost: float = None) -> float:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["idle_cash_full"]

    def get_utilization_exponent(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                                  discretionary_cash: float = None, mandatory_future_cost: float = None) -> float:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["utilization_exponent"]

    def get_utilization_floor(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                               discretionary_cash: float = None, mandatory_future_cost: float = None) -> float:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["utilization_floor"]

    def get_hire_batch_cap(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                            discretionary_cash: float = None, mandatory_future_cost: float = None) -> int:
        self._maybe_decide_or_enrich(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
        return self._day_cache[self._cache_key(ws)]["hire_batch_cap"]

    def _cache_key(self, ws: "WorldState"):
        return (ws.day, getattr(ws, 'n_quadrants', 1), globals().get('_SIMULATING_FEASIBILITY', False))

    def _maybe_decide_or_enrich(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                                 discretionary_cash: float = None, mandatory_future_cost: float = None):
        self._record_net_worth(ws)
        cached = self._day_cache.get(self._cache_key(ws))
        already_has_fa = cached is not None and cached.get("has_fa", False)
        new_call_has_fa = fa is not None
        if cached is not None and (already_has_fa or not new_call_has_fa):
            return   
        self._decide_for_day(ws, fa=fa, discretionary_cash=discretionary_cash,
                              mandatory_future_cost=mandatory_future_cost)

    def _decide_for_day(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                         discretionary_cash: float = None, mandatory_future_cost: float = None):
        feats = self._features(ws, fa=fa, discretionary_cash=discretionary_cash,
                                mandatory_future_cost=mandatory_future_cost)
        raw_floor_mean = self._linear(self.floor_w, feats, PPO_FLOOR_FEATURE_NAMES)
        raw_cap_mean = self._linear(self.cap_w, feats, PPO_CAP_FEATURE_NAMES)

        if self.training:
            raw_floor = self._rng.gauss(raw_floor_mean, self.floor_std)
            raw_cap = self._rng.gauss(raw_cap_mean, self.cap_std)
        else:
            raw_floor, raw_cap = raw_floor_mean, raw_cap_mean   

        floor_sig = _ppo_sigmoid(raw_floor)
        cap_sig = _ppo_sigmoid(raw_cap)
        floor_mult = PPO_FLOOR_MULT_MIN + (PPO_FLOOR_MULT_MAX - PPO_FLOOR_MULT_MIN) * floor_sig
        cap_per_quadrant = int(round(PPO_CAP_MIN + (PPO_CAP_MAX - PPO_CAP_MIN) * cap_sig))
        cap_per_quadrant = max(PPO_CAP_MIN, min(PPO_CAP_MAX, cap_per_quadrant))
        raw_margin_mean = raw_steep_mean = raw_thresh_mean = None
        raw_margin = raw_steep = raw_thresh = None
        if self.enabled_stage2:
            raw_margin_mean = self._linear(self.margin_w, feats, PPO_MARGIN_FEATURE_NAMES)
            raw_steep_mean = self._linear(self.steepness_w, feats, PPO_STEEPNESS_FEATURE_NAMES)
            raw_thresh_mean = self._linear(self.threshold_w, feats, PPO_UTIL_THRESH_FEATURE_NAMES)
            if self.training:
                raw_margin = self._rng.gauss(raw_margin_mean, self.margin_std)
                raw_steep = self._rng.gauss(raw_steep_mean, self.steepness_std)
                raw_thresh = self._rng.gauss(raw_thresh_mean, self.threshold_std)
            else:
                raw_margin, raw_steep, raw_thresh = raw_margin_mean, raw_steep_mean, raw_thresh_mean
            coverage_margin = PPO_MARGIN_MIN + (PPO_MARGIN_MAX - PPO_MARGIN_MIN) * _ppo_sigmoid(raw_margin)
            throttle_steepness = PPO_STEEPNESS_MIN + (PPO_STEEPNESS_MAX - PPO_STEEPNESS_MIN) * _ppo_sigmoid(raw_steep)
            utilization_threshold = PPO_UTIL_THRESH_MIN + (PPO_UTIL_THRESH_MAX - PPO_UTIL_THRESH_MIN) * _ppo_sigmoid(raw_thresh)

            raw_idle_start_mean = self._linear(self.idle_start_w, feats, PPO_IDLE_START_FEATURE_NAMES)
            raw_idle_full_mean = self._linear(self.idle_full_w, feats, PPO_IDLE_FULL_FEATURE_NAMES)
            if self.training:
                raw_idle_start = self._rng.gauss(raw_idle_start_mean, self.idle_start_std)
                raw_idle_full = self._rng.gauss(raw_idle_full_mean, self.idle_full_std)
            else:
                raw_idle_start, raw_idle_full = raw_idle_start_mean, raw_idle_full_mean
            idle_cash_start = PPO_IDLE_START_MIN + (PPO_IDLE_START_MAX - PPO_IDLE_START_MIN) * _ppo_sigmoid(raw_idle_start)
            idle_cash_full = PPO_IDLE_FULL_MIN + (PPO_IDLE_FULL_MAX - PPO_IDLE_FULL_MIN) * _ppo_sigmoid(raw_idle_full)
            raw_util_exp_mean = self._linear(self.util_exp_w, feats, PPO_UTIL_EXP_FEATURE_NAMES)
            raw_util_floor_mean = self._linear(self.util_floor_w, feats, PPO_UTIL_FLOOR_FEATURE_NAMES)
            if self.training:
                raw_util_exp = self._rng.gauss(raw_util_exp_mean, self.util_exp_std)
                raw_util_floor = self._rng.gauss(raw_util_floor_mean, self.util_floor_std)
            else:
                raw_util_exp, raw_util_floor = raw_util_exp_mean, raw_util_floor_mean
            utilization_exponent = PPO_UTIL_EXP_MIN + (PPO_UTIL_EXP_MAX - PPO_UTIL_EXP_MIN) * _ppo_sigmoid(raw_util_exp)
            utilization_floor = PPO_UTIL_FLOOR_MIN + (PPO_UTIL_FLOOR_MAX - PPO_UTIL_FLOOR_MIN) * _ppo_sigmoid(raw_util_floor)

            raw_hire_batch_mean = self._linear(self.hire_batch_w, feats, PPO_HIRE_BATCH_FEATURE_NAMES)
            if self.training:
                raw_hire_batch = self._rng.gauss(raw_hire_batch_mean, self.hire_batch_std)
            else:
                raw_hire_batch = raw_hire_batch_mean
            hire_batch_cap = int(round(PPO_HIRE_BATCH_MIN + (PPO_HIRE_BATCH_MAX - PPO_HIRE_BATCH_MIN) * _ppo_sigmoid(raw_hire_batch)))
            hire_batch_cap = max(PPO_HIRE_BATCH_MIN, min(PPO_HIRE_BATCH_MAX, hire_batch_cap))
        else:
            coverage_margin, throttle_steepness, utilization_threshold = 1.15, 6.0, 0.85
            raw_idle_start_mean = raw_idle_full_mean = raw_idle_start = raw_idle_full = None
            idle_cash_start, idle_cash_full = 2.0, 8.0
            raw_util_exp_mean = raw_util_floor_mean = raw_util_exp = raw_util_floor = None
            utilization_exponent, utilization_floor = 3.0, 0.05
            raw_hire_batch_mean = raw_hire_batch = None
            hire_batch_cap = 1   

        self._day_cache[self._cache_key(ws)] = {"floor_mult": floor_mult, "cap_per_quadrant": cap_per_quadrant,
                                    "coverage_margin": coverage_margin,
                                    "throttle_steepness": throttle_steepness,
                                    "utilization_threshold": utilization_threshold,
                                    "idle_cash_start": idle_cash_start,
                                    "idle_cash_full": idle_cash_full,
                                    "utilization_exponent": utilization_exponent,
                                    "utilization_floor": utilization_floor,
                                    "hire_batch_cap": hire_batch_cap,
                                    "has_fa": fa is not None}

        if self.training and not globals().get('_SIMULATING_FEASIBILITY', False):
            self._floor_mean_history.append(raw_floor_mean)
            self._cap_mean_history.append(raw_cap_mean)
            if raw_margin_mean is not None:
                self._margin_mean_history.append(raw_margin_mean)
            if raw_steep_mean is not None:
                self._steep_mean_history.append(raw_steep_mean)
            if raw_thresh_mean is not None:
                self._thresh_mean_history.append(raw_thresh_mean)
            if raw_idle_start_mean is not None:
                self._idle_start_mean_history.append(raw_idle_start_mean)
            if raw_idle_full_mean is not None:
                self._idle_full_mean_history.append(raw_idle_full_mean)
            if raw_util_exp_mean is not None:
                self._util_exp_mean_history.append(raw_util_exp_mean)
            if raw_util_floor_mean is not None:
                self._util_floor_mean_history.append(raw_util_floor_mean)
            if raw_hire_batch_mean is not None:
                self._hire_batch_mean_history.append(raw_hire_batch_mean)
            trace_row = {
                "day": ws.day, "feats": feats,
                "raw_floor": raw_floor, "raw_floor_mean": raw_floor_mean,
                "raw_cap": raw_cap, "raw_cap_mean": raw_cap_mean,
                "floor_mult": floor_mult, "cap_per_quadrant": cap_per_quadrant,
                "raw_margin": raw_margin, "raw_margin_mean": raw_margin_mean,
                "raw_steep": raw_steep, "raw_steep_mean": raw_steep_mean,
                "raw_thresh": raw_thresh, "raw_thresh_mean": raw_thresh_mean,
                "coverage_margin": coverage_margin, "throttle_steepness": throttle_steepness,
                "utilization_threshold": utilization_threshold,
                "raw_idle_start": raw_idle_start, "raw_idle_start_mean": raw_idle_start_mean,
                "raw_idle_full": raw_idle_full, "raw_idle_full_mean": raw_idle_full_mean,
                "idle_cash_start": idle_cash_start, "idle_cash_full": idle_cash_full,
                "raw_util_exp": raw_util_exp, "raw_util_exp_mean": raw_util_exp_mean,
                "raw_util_floor": raw_util_floor, "raw_util_floor_mean": raw_util_floor_mean,
                "utilization_exponent": utilization_exponent, "utilization_floor": utilization_floor,
                "raw_hire_batch": raw_hire_batch, "raw_hire_batch_mean": raw_hire_batch_mean,
                "hire_batch_cap": hire_batch_cap,
            }
            cache_key = self._cache_key(ws)
            existing_idx = self._trace_index_by_key.get(cache_key)
            if existing_idx is not None:
                self._episode_trace[existing_idx] = trace_row
            else:
                self._trace_index_by_key[cache_key] = len(self._episode_trace)
                self._episode_trace.append(trace_row)

    def _convergence_diag(self, n_last: int = 30) -> dict:
        def _one(history, noise_std):
            if len(history) < 2:
                return None
            recent = history[-n_last:]
            signal_std = float(np.std(recent))
            return signal_std / noise_std if noise_std > 0 else float("inf")

        ratios = {
            "floor": _one(self._floor_mean_history, self.floor_std),
            "cap": _one(self._cap_mean_history, self.cap_std),
            "margin": _one(self._margin_mean_history, self.margin_std),
            "steepness": _one(self._steep_mean_history, self.steepness_std),
            "threshold": _one(self._thresh_mean_history, self.threshold_std),
            "idle_start": _one(self._idle_start_mean_history, self.idle_start_std),
            "idle_full": _one(self._idle_full_mean_history, self.idle_full_std),
            "util_exp": _one(self._util_exp_mean_history, self.util_exp_std),
            "util_floor": _one(self._util_floor_mean_history, self.util_floor_std),
            "hire_batch": _one(self._hire_batch_mean_history, self.hire_batch_std),
        }
        valid = {k: v for k, v in ratios.items() if v is not None}
        if not valid:
            return {"ratios": ratios, "worst_ratio": None, "converged": False,
                     "n_decisions_total": len(self._floor_mean_history)}
        worst_key = min(valid, key=valid.get)
        return {"ratios": ratios, "worst_ratio": valid[worst_key], "worst_head": worst_key,
                 "converged": valid[worst_key] >= 0.5, "n_decisions_total": len(self._floor_mean_history)}


    def update(self, episode_return: float, win_outcome: float = 0.0):
        if not self._episode_trace:
            return

        local_rewards = []
        for step in self._episode_trace:
            day = step["day"]
            delta = self._local_delta(day)
            penalty = self.STARVATION_PENALTY_SCALE * self._avg_starvation(day)
            local_rewards.append(delta - penalty)

        mean_reward = sum(local_rewards) / len(local_rewards)
        prev_baseline = self._local_baseline
        # FIX (baseline leakage): advantage must use the PRE-update baseline
        # (this episode's own mean_reward hasn't been blended in yet), or the
        # gradient is systematically damped by ~alpha (20%) every episode.
        baseline_for_advantage = prev_baseline if prev_baseline is not None else mean_reward
        self._local_baseline = ((1 - self._local_baseline_alpha) * prev_baseline
                                 + self._local_baseline_alpha * mean_reward) if prev_baseline is not None else mean_reward

        step_scale = 1.0 / max(1, len(self._episode_trace))   

        # FIX (reward metric, part 3): FloorCap had no win/loss signal before
        # -- purely local net-worth delta, which can rise from a generous seed
        # regardless of policy quality. Add the same fixed post-tanh nudge.
        win_term = RL_WIN_BONUS_REWARD * win_outcome

        for step, reward in zip(self._episode_trace, local_rewards):
            feats = step["feats"]
            advantage = reward - baseline_for_advantage
            adv_scaled = math.tanh(advantage / 5000.0) + win_term
            d_floor = (step["raw_floor"] - step["raw_floor_mean"]) / (self.floor_std ** 2)
            d_cap = (step["raw_cap"] - step["raw_cap_mean"]) / (self.cap_std ** 2)
            for name in PPO_FLOOR_FEATURE_NAMES:
                self.floor_w[name] += step_scale * self.lr * adv_scaled * d_floor * feats.get(name, 0.0)
            for name in PPO_CAP_FEATURE_NAMES:
                self.cap_w[name] += step_scale * self.lr * adv_scaled * d_cap * feats.get(name, 0.0)

            if self.enabled_stage2 and step.get("raw_margin") is not None:
                d_margin = (step["raw_margin"] - step["raw_margin_mean"]) / (self.margin_std ** 2)
                d_steep = (step["raw_steep"] - step["raw_steep_mean"]) / (self.steepness_std ** 2)
                d_thresh = (step["raw_thresh"] - step["raw_thresh_mean"]) / (self.threshold_std ** 2)
                for name in PPO_MARGIN_FEATURE_NAMES:
                    self.margin_w[name] += step_scale * self.lr * adv_scaled * d_margin * feats.get(name, 0.0)
                for name in PPO_STEEPNESS_FEATURE_NAMES:
                    self.steepness_w[name] += step_scale * self.lr * adv_scaled * d_steep * feats.get(name, 0.0)
                for name in PPO_UTIL_THRESH_FEATURE_NAMES:
                    self.threshold_w[name] += step_scale * self.lr * adv_scaled * d_thresh * feats.get(name, 0.0)
                if step.get("raw_idle_start") is not None:
                    d_idle_start = (step["raw_idle_start"] - step["raw_idle_start_mean"]) / (self.idle_start_std ** 2)
                    d_idle_full = (step["raw_idle_full"] - step["raw_idle_full_mean"]) / (self.idle_full_std ** 2)
                    for name in PPO_IDLE_START_FEATURE_NAMES:
                        self.idle_start_w[name] += step_scale * self.lr * adv_scaled * d_idle_start * feats.get(name, 0.0)
                    for name in PPO_IDLE_FULL_FEATURE_NAMES:
                        self.idle_full_w[name] += step_scale * self.lr * adv_scaled * d_idle_full * feats.get(name, 0.0)
                if step.get("raw_util_exp") is not None:
                    d_util_exp = (step["raw_util_exp"] - step["raw_util_exp_mean"]) / (self.util_exp_std ** 2)
                    d_util_floor = (step["raw_util_floor"] - step["raw_util_floor_mean"]) / (self.util_floor_std ** 2)
                    for name in PPO_UTIL_EXP_FEATURE_NAMES:
                        self.util_exp_w[name] += step_scale * self.lr * adv_scaled * d_util_exp * feats.get(name, 0.0)
                    for name in PPO_UTIL_FLOOR_FEATURE_NAMES:
                        self.util_floor_w[name] += step_scale * self.lr * adv_scaled * d_util_floor * feats.get(name, 0.0)

                if step.get("raw_hire_batch") is not None:
                    d_hire_batch = (step["raw_hire_batch"] - step["raw_hire_batch_mean"]) / (self.hire_batch_std ** 2)
                    for name in PPO_HIRE_BATCH_FEATURE_NAMES:
                        self.hire_batch_w[name] += step_scale * self.lr * adv_scaled * d_hire_batch * feats.get(name, 0.0)

    def format_day_breakdown(self, day: int) -> str:
        rows = [r for r in self._episode_trace if r["day"] == day]
        if not rows:
            return f"(no PPO decision recorded for day {day})"
        r = rows[-1]
        feats = r["feats"]
        lines = [f"DAY {day}", "", "FLOOR:"]
        for name in PPO_FLOOR_FEATURE_NAMES:
            if name == "bias":
                continue
            w = self.floor_w[name]
            lines.append(f"  {name:28s} x {w:+.4f} = {w * feats.get(name, 0.0):+.4f}")
        lines.append(f"  {'bias':28s}     = {self.floor_w['bias']:+.4f}")
        lines.append(f"  {'-'*45}")
        lines.append(f"  raw floor score (mean)       = {r['raw_floor_mean']:+.4f}")
        lines.append(f"  PPO floor_mult                = {r['floor_mult']:.4f}")
        lines.append("")
        lines.append("CAP:")
        for name in PPO_CAP_FEATURE_NAMES:
            if name == "bias":
                continue
            w = self.cap_w[name]
            lines.append(f"  {name:28s} x {w:+.4f} = {w * feats.get(name, 0.0):+.4f}")
        lines.append(f"  {'bias':28s}     = {self.cap_w['bias']:+.4f}")
        lines.append(f"  {'-'*45}")
        lines.append(f"  raw cap score (mean)         = {r['raw_cap_mean']:+.4f}")
        lines.append(f"  PPO cap_per_quadrant          = {r['cap_per_quadrant']}")
        return "\n".join(lines)

RL_FLOORCAP_CONTROLLER = ReinforceFloorCapController()

BOOTSTRAP_CROP = "WHEAT"

PPO_ALPHA_FEATURE_NAMES = [
    "bias", "season_progress", "cash_ratio", "discretionary_cash_ratio",
    "current_workers_norm", "n_plant_allowed_norm",

    "cash_velocity_norm",
    "established_crop_ratio",
    "ev_cost_ratio",
]

def _softmax(raws: dict) -> dict:
    m = max(raws.values())
    exps = {k: math.exp(v - m) for k, v in raws.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}

def _species_ev_cost_ratio(economic_value: float, cost: float) -> float:
    if cost <= 0:
        return 0.0
    return math.tanh((economic_value / cost) / 2.0)

def _apply_demand_exploration_floor(fractions: dict, ws: "WorldState", min_share: float = 0.10) -> dict:
    unlocked = list(getattr(ws, "unlocked_shops", ()) or ())
    remaining_days = getattr(ws, "remaining_days", SEASON_DAYS)

    def _crop_still_worth_forcing(c: str) -> bool:
        if remaining_days < crop_days_to_first_harvest(c):
            return False
        return _crop_net_economics(c, ws)["gate_open"]

    demanded_crops = {
        c for s in unlocked for c in SHOP_DEMAND.get(s, [])
        if c in fractions and _crop_still_worth_forcing(c)
    }
    if not demanded_crops:
        return fractions
    floored = dict(fractions)
    deficit = 0.0
    for crop in demanded_crops:
        if floored[crop] < min_share:
            deficit += min_share - floored[crop]
            floored[crop] = min_share
    if deficit <= 0:
        return floored
    donors = [c for c in floored if c not in demanded_crops or fractions[c] >= min_share]
    donor_total = sum(floored[c] for c in donors)
    if donor_total <= 0:
        return floored
    for c in donors:
        share = floored[c] / donor_total
        floored[c] = max(0.0, floored[c] - deficit * share)
    total = sum(floored.values())
    return {c: v / total for c, v in floored.items()} if total > 0 else floored

def _wheat_feed_reserve_forecast(ws: "WorldState", horizon_days: int = 10) -> float:
    total_animals = sum(ws.animal_counts.values())
    if total_animals <= 0:
        return 0.0
    days = max(1, min(horizon_days, max(1, ws.remaining_days)))
    return float(total_animals * days)

def _wheat_stock_available(ws: "WorldState") -> float:
    held = sum(inv.get("WHEAT", 0) for inv in ws.all_inventories) if ws.all_inventories \
        else ws.farmer_inventory.get("WHEAT", 0)
    return ws.shed.get("WHEAT", 0) + held

def _wheat_shop_demand_floor(ws: "WorldState", shop_min_share: float = 0.10) -> float:
    unlocked = list(getattr(ws, "unlocked_shops", ()) or ())
    remaining_days = getattr(ws, "remaining_days", SEASON_DAYS)
    wheat_demanded = any("WHEAT" in SHOP_DEMAND.get(s, []) for s in unlocked)
    if not wheat_demanded:
        return 0.0
    if remaining_days < crop_days_to_first_harvest("WHEAT"):
        return 0.0
    if not _crop_net_economics("WHEAT", ws)["gate_open"]:
        return 0.0
    return shop_min_share

def _apply_wheat_feed_cap(fractions: dict, ws: "WorldState", n_plant_allowed: int,
                           forecast_horizon_days: int = 10,
                           min_share: float = 0.05, max_share: float = 0.60) -> dict:
    if "WHEAT" not in fractions or n_plant_allowed <= 0:
        return fractions

    total_animals = sum(ws.animal_counts.values())
    if total_animals <= 0:
        feed_fraction = 0.0
    else:
        forecast_need = _wheat_feed_reserve_forecast(ws, forecast_horizon_days)
        stock_available = _wheat_stock_available(ws)
        deficit_units = max(0.0, forecast_need - stock_available)
        wheat_yield_per_tile = max(1.0, float(CROP_INFO["WHEAT"].get("max_yield", 1)))
        tiles_needed = deficit_units / wheat_yield_per_tile
        feed_fraction = tiles_needed / n_plant_allowed

    shop_floor = _wheat_shop_demand_floor(ws)
    if total_animals <= 0 and shop_floor <= 0.0:
        return fractions   

    cap = max(min_share, shop_floor, min(max_share, feed_fraction))

    current = fractions.get("WHEAT", 0.0)
    if current <= cap:
        return fractions   

    excess = current - cap
    floored = dict(fractions)
    floored["WHEAT"] = cap
    donors = [c for c in floored if c != "WHEAT"]
    donor_total = sum(floored[c] for c in donors)
    if donor_total <= 0:
        share = excess / max(1, len(donors))
        for c in donors:
            floored[c] = floored.get(c, 0.0) + share
    else:
        for c in donors:
            floored[c] += excess * (floored[c] / donor_total)
    total = sum(floored.values())
    return {c: v / total for c, v in floored.items()} if total > 0 else floored

def _largest_remainder_allocation(fractions: dict, n: int) -> dict:
    if n <= 0:
        return {c: 0 for c in fractions}
    raw = {c: f * n for c, f in fractions.items()}
    floors = {c: int(v) for c, v in raw.items()}
    remainder = n - sum(floors.values())
    if remainder > 0:
        order = sorted(fractions.keys(), key=lambda c: raw[c] - floors[c], reverse=True)
        for c in order[:remainder]:
            floors[c] += 1
    return floors

class ReinforceBootstrapAlphaController:

    ALPHA_HORIZON_MAX = 12   

    def __init__(self, lr=0.02, alpha_std=0.15, seed=0, alpha_std_min=0.03, alpha_std_decay_episodes=150):
        self.enabled = False
        self.training = False
        self.lr = lr
        # FIX (convergence speed): alpha_std was a fixed noise std, keeping
        # signal/noise stuck at 0.04-0.40 for thousands of decisions. Anneals it
        # to alpha_std_min over alpha_std_decay_episodes (mirrors entropy_coef decay).
        self.alpha_std = alpha_std
        self.alpha_std_start = alpha_std
        self.alpha_std_min = alpha_std_min
        self.alpha_std_decay_episodes = alpha_std_decay_episodes
        self._n_episodes_completed = 0
        self._rng = _ppo_random.Random(seed)

        self.crop_order = list(CROP_INFO.keys())   
        self.crop_w = {crop: {name: 0.0 for name in PPO_ALPHA_FEATURE_NAMES} for crop in self.crop_order}

        raw_day0 = _ppo_inv_sigmoid((0.85 - 0.0) / 1.0)
        raw_day6 = _ppo_inv_sigmoid((0.15 - 0.0) / 1.0)
        season_progress_day6 = 6.0 / 30.0
        w_season = (raw_day6 - raw_day0) / season_progress_day6
        self.crop_w["WHEAT"]["bias"] = raw_day0
        self.crop_w["WHEAT"]["season_progress"] = w_season

        EV_COST_RATIO_INIT_WEIGHT = 3.0
        for crop in self.crop_order:
            self.crop_w[crop]["ev_cost_ratio"] = EV_COST_RATIO_INIT_WEIGHT

        self._episode_trace = []
        self._day_cache = {}
        self._cash_history = {}
        self._mean_history = {crop: [] for crop in self.crop_order}   
        self._season_progress_history = {crop: [] for crop in self.crop_order}  # FIX (bug2): needed to detrend season_progress-driven variance

        # FIX: default OFF (was buggy/inconsistent local-delta path, see update())
        self.use_isolated_reward = False
        self.CROP_PRODUCT_KEYS = tuple(CROP_INFO.keys())
        self._crop_value_history = {crop: {} for crop in self.crop_order}   
        self._last_crop_shed_snapshot = {}   
        self._cumulative_crop_value = {crop: 0.0 for crop in self.crop_order}
        self._local_baseline = {crop: None for crop in self.crop_order}
        self._local_baseline_alpha = 0.2
        self._episode_return_baseline = None
        self._return_baseline_alpha = 0.05

    def reset_episode(self):
        self._episode_trace = []
        self._day_cache = {}
        self._cash_history = {}
        self._crop_value_history = {crop: {} for crop in self.crop_order}
        self._last_crop_shed_snapshot = {}
        self._cumulative_crop_value = {crop: 0.0 for crop in self.crop_order}

    def _record_crop_output(self, ws: "WorldState"):
        if ws.day in self._crop_value_history[self.crop_order[0]]:
            return
        shed = getattr(ws, "shed", {}) or {}
        for crop in self.CROP_PRODUCT_KEYS:
            qty = shed.get(crop, 0)
            last = self._last_crop_shed_snapshot.get(crop, 0)
            if qty > last:
                price = ws.prices.get(crop, CROP_INFO[crop]["base_price"])
                self._cumulative_crop_value[crop] += (qty - last) * price
            self._last_crop_shed_snapshot[crop] = qty
            self._crop_value_history[crop][ws.day] = self._cumulative_crop_value[crop]

    def _horizon_for_alpha(self, ws: "WorldState") -> int:
        ranked = evaluate_crop_options_for_tile(ws.prices)
        best_crop = ranked[0].crop if ranked else "WHEAT"
        horizon = max(crop_days_to_first_harvest("WHEAT"), crop_days_to_first_harvest(best_crop))
        return min(self.ALPHA_HORIZON_MAX, horizon)

    def _local_delta_crop_value(self, crop: str, decision_day: int, horizon_days: int) -> float:
        hist = self._crop_value_history[crop]
        v0 = hist.get(decision_day)
        if v0 is None:
            return 0.0
        target_day = decision_day + horizon_days
        candidate_days = [d for d in hist if d >= target_day]
        if candidate_days:
            v1 = hist[min(candidate_days)]
        else:
            latest_day = max(hist)
            v1 = hist[latest_day]
        return v1 - v0

    def _features(self, ws: "WorldState", crop: str, fa: "FarmAnalysis" = None,
                  discretionary_cash: float = None, n_plant_allowed: int = 0) -> dict:
        season_days = getattr(ws, "season_days", 30) or 30
        season_progress = min(1.0, ws.day / max(1, season_days))
        money = max(0.0, ws.money)
        cash_ratio = math.tanh(money / 2000.0)
        current_workers = 1 + len(ws.hands)

        if discretionary_cash is not None and discretionary_cash != float("inf"):
            discretionary_cash_ratio = math.tanh(max(0.0, discretionary_cash) / 2000.0)
        else:
            discretionary_cash_ratio = math.tanh(max(0.0, money - RESERVE_MIN_OPERATING_CASH) / 2000.0)
        self._cash_history[ws.day] = money
        lookback = 3
        past_day = ws.day - lookback
        if past_day in self._cash_history:
            velocity = (money - self._cash_history[past_day]) / lookback
            cash_velocity_norm = math.tanh(velocity / 500.0)
        else:
            cash_velocity_norm = 0.0

        established_crop_ratio = 0.0
        if fa is not None:
            owned = 0
            planted = 0
            for row in ws.tiles:
                for t in row:
                    if t == "LOCKED":
                        continue
                    owned += 1
                    if isinstance(t, dict) and t.get("crop"):
                        planted += 1
            established_crop_ratio = planted / max(1, owned)

        econ = _crop_net_economics(crop, ws)
        ev_cost_ratio = _species_ev_cost_ratio(econ["economic_value"], econ["seed_cost"])

        return {
            "bias": 1.0,
            "season_progress": season_progress,
            "cash_ratio": cash_ratio,
            "discretionary_cash_ratio": discretionary_cash_ratio,
            "current_workers_norm": math.tanh(current_workers / 15.0),
            "n_plant_allowed_norm": math.tanh(n_plant_allowed / 25.0),
            "cash_velocity_norm": cash_velocity_norm,
            "established_crop_ratio": established_crop_ratio,
            "ev_cost_ratio": ev_cost_ratio,
            "day": ws.day,
        }

    def _linear(self, weights: dict, feats: dict, names: list) -> float:
        return sum(weights[n] * feats.get(n, 0.0) for n in names)

    def get_crop_mix(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                      discretionary_cash: float = None, n_plant_allowed: int = 0) -> dict:
        self._record_crop_output(ws)
        key = (ws.day, globals().get('_SIMULATING_FEASIBILITY', False))
        cached = self._day_cache.get(key)
        already_has_fa = cached is not None and cached.get("has_fa", False)
        new_call_has_fa = fa is not None
        if cached is None or (not already_has_fa and new_call_has_fa):
            self._decide_for_day(ws, fa=fa, discretionary_cash=discretionary_cash,
                                  n_plant_allowed=n_plant_allowed)
        return self._day_cache[key]["fractions"]

    def get_alpha(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                  discretionary_cash: float = None, n_plant_allowed: int = 0) -> float:
        return self.get_crop_mix(ws, fa=fa, discretionary_cash=discretionary_cash,
                                  n_plant_allowed=n_plant_allowed).get("WHEAT", 0.0)

    def _decide_for_day(self, ws, fa=None, discretionary_cash=None, n_plant_allowed=0):
        feats_per_crop = {
            crop: self._features(ws, crop, fa=fa, discretionary_cash=discretionary_cash,
                                  n_plant_allowed=n_plant_allowed)
            for crop in self.crop_order
        }
        raw_means = {crop: self._linear(self.crop_w[crop], feats_per_crop[crop], PPO_ALPHA_FEATURE_NAMES)
                     for crop in self.crop_order}
        if self.training:
            raws = {crop: self._rng.gauss(raw_means[crop], self.alpha_std) for crop in self.crop_order}
        else:
            raws = dict(raw_means)
        fractions = _softmax(raws)

        key = (ws.day, globals().get('_SIMULATING_FEASIBILITY', False))
        self._day_cache[key] = {"fractions": fractions, "has_fa": fa is not None}
        if self.training and not globals().get('_SIMULATING_FEASIBILITY', False):
            self._episode_trace.append({
                "day": ws.day, "feats": feats_per_crop,
                "raws": raws, "raw_means": raw_means,
                "fractions": fractions, "horizon_days": self._horizon_for_alpha(ws),
            })
            for crop in self.crop_order:
                self._mean_history[crop].append(raw_means[crop])
                self._season_progress_history[crop].append(feats_per_crop[crop]["season_progress"])

    def _current_alpha_std(self) -> float:
        frac = min(1.0, self._n_episodes_completed / max(1, self.alpha_std_decay_episodes))
        return self.alpha_std_start + (self.alpha_std_min - self.alpha_std_start) * frac

    def update(self, episode_return: float, win_outcome: float = 0.0):
        # FIX: was switching per-crop between local-delta (buggy, misattributed)
        # and episode_return based on has_signal_by_crop -- now always uses
        # the consistent episode-level advantage unless use_isolated_reward=True.
        self._n_episodes_completed += 1
        self.alpha_std = self._current_alpha_std()
        if not self._episode_trace:
            return

        b = self._episode_return_baseline
        self._episode_return_baseline = ((1 - self._return_baseline_alpha) * b
                                          + self._return_baseline_alpha * episode_return) if b is not None else episode_return
        advantage = episode_return - (b if b is not None else episode_return)
        # FIX (reward metric, part 3): win_outcome was pre-baked into episode_return
        # before the tanh squash, so it got swamped on noisy stages. Now it's a
        # fixed term added AFTER the squash, same weight regardless of noise.
        win_term = RL_WIN_BONUS_REWARD * win_outcome
        adv_scaled_global = math.tanh(advantage / 5000.0) + win_term

        if self.use_isolated_reward:
            local_deltas_by_crop = {crop: [] for crop in self.crop_order}
            for step in self._episode_trace:
                for crop in self.crop_order:
                    local_deltas_by_crop[crop].append(
                        self._local_delta_crop_value(crop, step["day"], step["horizon_days"]))
            for crop in self.crop_order:
                deltas = local_deltas_by_crop[crop]
                mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
                base = self._local_baseline[crop]
                self._local_baseline[crop] = ((1 - self._local_baseline_alpha) * base
                                               + self._local_baseline_alpha * mean_delta) if base is not None else mean_delta

        step_scale = 1.0 / max(1, len(self._episode_trace))
        for step_idx, step in enumerate(self._episode_trace):
            for crop in self.crop_order:

                if self.use_isolated_reward:
                    crop_advantage = local_deltas_by_crop[crop][step_idx] - self._local_baseline[crop]
                    adv_scaled = math.tanh(crop_advantage / 500.0) + win_term
                else:
                    adv_scaled = adv_scaled_global
                feats = step["feats"][crop]
                d_raw = (step["raws"][crop] - step["raw_means"][crop]) / (self.alpha_std ** 2)
                for name in PPO_ALPHA_FEATURE_NAMES:
                    self.crop_w[crop][name] += step_scale * self.lr * adv_scaled * d_raw * feats.get(name, 0.0)

    def format_day_breakdown(self, day: int) -> str:
        rows = [r for r in self._episode_trace if r["day"] == day]
        if not rows:
            return f"(no crop-mix decision recorded for day {day})"
        r = rows[-1]
        lines = [f"DAY {day}", "", "CROP MIX (softmax fractions):"]
        for crop in self.crop_order:
            lines.append(f"  {crop:12s} fraction={r['fractions'][crop]:.3f}  raw_mean={r['raw_means'][crop]:+.4f}")
        lines.append(f"  {'-'*50}")
        for crop in self.crop_order:
            feats = r["feats"][crop]
            lines.append(f"  -- {crop} weights --")
            for name in PPO_ALPHA_FEATURE_NAMES:
                if name == "bias":
                    continue
                w = self.crop_w[crop][name]
                lines.append(f"    {name:26s} x {w:+.4f} = {w * feats.get(name, 0.0):+.4f}")
            lines.append(f"    {'bias':26s}     = {self.crop_w[crop]['bias']:+.4f}")
        return "\n".join(lines)

    def _convergence_diag(self, n_last: int = 30) -> dict:
        # FIX (bug2): WHEAT's raw_mean has a large deterministic season_progress term
        # baked in, so comparing raw signal_std across crops was apples-to-oranges.
        # Now regress out the season_progress trend first and measure residual std.
        ratios = {}
        for crop in self.crop_order:
            hist = self._mean_history[crop]
            xs = self._season_progress_history[crop]
            if len(hist) < 2:
                ratios[crop] = None
                continue
            recent = hist[-n_last:]
            recent_x = xs[-n_last:] if len(xs) >= len(hist) else xs[-len(recent):]
            n = len(recent)
            if n >= 2 and (max(recent_x) - min(recent_x)) > 1e-9:
                mean_x = sum(recent_x) / n
                mean_y = sum(recent) / n
                cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(recent_x, recent)) / n
                var_x = sum((x - mean_x) ** 2 for x in recent_x) / n
                slope = cov / var_x if var_x > 1e-12 else 0.0
                intercept = mean_y - slope * mean_x
                residuals = [y - (slope * x + intercept) for x, y in zip(recent_x, recent)]
            else:
                residuals = [y - (sum(recent) / n) for y in recent]
            signal_std = float(np.std(residuals))
            ratios[crop] = signal_std / self.alpha_std if self.alpha_std > 0 else float("inf")
        valid = {k: v for k, v in ratios.items() if v is not None}
        if not valid:
            return {"ratios": ratios, "worst_ratio": None, "converged": False,
                     "n_decisions_total": len(self._mean_history[self.crop_order[0]])}
        worst_key = min(valid, key=valid.get)
        return {"ratios": ratios, "worst_ratio": valid[worst_key], "worst_crop": worst_key,
                 "converged": valid[worst_key] >= 0.5,
                 "n_decisions_total": len(self._mean_history[self.crop_order[0]])}

RL_CROP_MIX_CONTROLLER = ReinforceBootstrapAlphaController()

class ReinforceAnimalController:

    def __init__(self, lr=0.08, base_units_std=0.3, horizon_std=0.5, seed=0):
        self.enabled = False
        self.training = False
        self.lr = lr
        self.base_units_std = base_units_std
        self.horizon_std = horizon_std
        self._rng = _ppo_random.Random(seed)

        self.feature_names = ["bias", "season_progress", "cash_ratio",
                               "n_quadrants_norm", "unit_cost_ratio", "existing_units_norm",
                               "ev_cost_ratio"]

        self.BASE_UNITS_MIN, self.BASE_UNITS_MAX = 1, 4     
        self.HORIZON_RELIEF_MIN, self.HORIZON_RELIEF_MAX = -5.0, 3.0   

        self.base_units_w = {name: 0.0 for name in self.feature_names}
        base_units_sig = (2 - self.BASE_UNITS_MIN) / (self.BASE_UNITS_MAX - self.BASE_UNITS_MIN)
        self.base_units_w["bias"] = _ppo_inv_sigmoid(max(1e-3, min(1 - 1e-3, base_units_sig)))
        self.base_units_w["ev_cost_ratio"] = 2.0

        self.horizon_w = {name: 0.0 for name in self.feature_names}
        horizon_sig = (0.0 - self.HORIZON_RELIEF_MIN) / (self.HORIZON_RELIEF_MAX - self.HORIZON_RELIEF_MIN)
        self.horizon_w["bias"] = _ppo_inv_sigmoid(max(1e-3, min(1 - 1e-3, horizon_sig)))
        self.enabled_idle = False
        self.idle_start_std = 0.2
        self.idle_per_extra_std = 0.2
        self.IDLE_START_MIN, self.IDLE_START_MAX = 2.0, 10.0      
        self.IDLE_PER_EXTRA_MIN, self.IDLE_PER_EXTRA_MAX = 2.0, 10.0   
        self.idle_start_w = {name: 0.0 for name in self.feature_names}
        idle_start_sig = (5.0 - self.IDLE_START_MIN) / (self.IDLE_START_MAX - self.IDLE_START_MIN)
        self.idle_start_w["bias"] = _ppo_inv_sigmoid(max(1e-3, min(1 - 1e-3, idle_start_sig)))

        self.idle_per_extra_w = {name: 0.0 for name in self.feature_names}
        idle_per_extra_sig = (5.0 - self.IDLE_PER_EXTRA_MIN) / (self.IDLE_PER_EXTRA_MAX - self.IDLE_PER_EXTRA_MIN)
        self.idle_per_extra_w["bias"] = _ppo_inv_sigmoid(max(1e-3, min(1 - 1e-3, idle_per_extra_sig)))

        self._episode_trace = []
        self._idle_episode_trace = []   
        self._day_cache = {}   
        self._idle_day_cache = {}   
        self._baseline = 0.0
        self._baseline_alpha = 0.2
        self._bu_mean_history = []   
        self._hz_mean_history = []
        self._start_mean_history = []
        self._extra_mean_history = []
        # FIX (batch confound): track samples-per-update so
        # _convergence_diag can correct for it -- signal_std shrinks
        # mechanically as batch size grows, regardless of true signal.
        self._bu_batch_history = []
        self._hz_batch_history = []
        self._idle_batch_history = []

        self.reward_horizon_days_default = 5   
        self._local_baseline = 0.0
        self._local_baseline_alpha = 0.2
        self._nw_history = {}   
        self._episode_return_baseline = None
        self._return_baseline_alpha = 0.05

        self.use_isolated_reward = True
        self.PRODUCT_KEYS = ("MILK", "EGG", "WOOL")
        self._product_history = {}       
        self._last_shed_snapshot = {}    
        self._cumulative_product_output = 0.0

        self.filter_to_purchased_only = True
        self._purchased_keys = set()   

    def reset_episode(self):
        self._episode_trace = []
        self._idle_episode_trace = []
        self._day_cache = {}
        self._idle_day_cache = {}
        self._nw_history = {}
        self._product_history = {}
        self._last_shed_snapshot = {}
        self._cumulative_product_output = 0.0
        self._purchased_keys = set()

    def mark_purchased(self, day: int, animal: str):
        self._purchased_keys.add((day, animal, globals().get('_SIMULATING_FEASIBILITY', False)))

    def _record_net_worth(self, ws: "WorldState"):
        if ws.day not in self._nw_history:
            self._nw_history[ws.day] = _estimate_net_worth(ws)

    def _record_product_output(self, ws: "WorldState"):
        if ws.day in self._product_history:
            return
        shed = getattr(ws, "shed", {}) or {}
        for product in self.PRODUCT_KEYS:
            qty = shed.get(product, 0)
            last = self._last_shed_snapshot.get(product, 0)
            if qty > last:
                self._cumulative_product_output += (qty - last)
            self._last_shed_snapshot[product] = qty
        self._product_history[ws.day] = self._cumulative_product_output

    def _features(self, ws: "WorldState", animal: str, unit_cost: float) -> dict:
        season_days = getattr(ws, "season_days", 30) or 30
        season_progress = min(1.0, ws.day / max(1, season_days))
        money = max(0.0, ws.money)
        cash_ratio = math.tanh(money / 2000.0)
        current_workers = 1 + len(ws.hands)
        n_quadrants = max(1, getattr(ws, "n_quadrants", 1))
        discretionary_cash = _discretionary_cash(ws)
        unit_cost_ratio = math.tanh(discretionary_cash / max(1.0, unit_cost))
        existing_units = ws.animal_counts.get(animal, 0)
        existing_units_norm = math.tanh(existing_units / 4.0)

        project_id = next((pid for pid, a in PROJECT_ANIMAL.items() if a == animal), None)
        econ = _animal_net_economics(project_id, ws) if project_id else None
        ev_cost_ratio = (_species_ev_cost_ratio(econ["economic_value"], econ["unit_cost"])
                          if econ else 0.0)

        feats = {
            "bias": 1.0,
            "season_progress": season_progress,
            "cash_ratio": cash_ratio,
            "current_workers_norm": math.tanh(current_workers / 10.0),
            "n_quadrants_norm": math.tanh(n_quadrants / 3.0),
            "unit_cost_ratio": unit_cost_ratio,
            "existing_units_norm": existing_units_norm,
            "ev_cost_ratio": ev_cost_ratio,
        }
        return {name: feats.get(name, 0.0) for name in self.feature_names}

    def _linear(self, w: dict, feats: dict) -> float:
        return sum(w.get(name, 0.0) * feats.get(name, 0.0) for name in self.feature_names)

    def get_decision(self, ws: "WorldState", animal: str, unit_cost: float):
        self._record_net_worth(ws)
        self._record_product_output(ws)
        key = (ws.day, animal, globals().get('_SIMULATING_FEASIBILITY', False))
        if key in self._day_cache:
            return self._day_cache[key]["base_units"], self._day_cache[key]["horizon_relief"]

        feats = self._features(ws, animal, unit_cost)
        raw_bu_mean = self._linear(self.base_units_w, feats)
        raw_hz_mean = self._linear(self.horizon_w, feats)
        if self.training:
            raw_bu = self._rng.gauss(raw_bu_mean, self.base_units_std)
            raw_hz = self._rng.gauss(raw_hz_mean, self.horizon_std)
        else:
            raw_bu, raw_hz = raw_bu_mean, raw_hz_mean

        bu_sig = _ppo_sigmoid(raw_bu)
        hz_sig = _ppo_sigmoid(raw_hz)
        base_units = int(round(self.BASE_UNITS_MIN + (self.BASE_UNITS_MAX - self.BASE_UNITS_MIN) * bu_sig))
        base_units = max(self.BASE_UNITS_MIN, min(self.BASE_UNITS_MAX, base_units))
        horizon_relief = self.HORIZON_RELIEF_MIN + (self.HORIZON_RELIEF_MAX - self.HORIZON_RELIEF_MIN) * hz_sig

        project_id = next((pid for pid, a in PROJECT_ANIMAL.items() if a == animal), None)
        mph = PROJECT_REGISTRY[project_id].min_profitable_horizon if project_id in PROJECT_REGISTRY else 0.0
        remaining_days = getattr(ws, "remaining_days", SEASON_DAYS)
        feas_at_min_relief = remaining_days >= max(0.0, mph + self.HORIZON_RELIEF_MIN)
        feas_at_max_relief = remaining_days >= max(0.0, mph + self.HORIZON_RELIEF_MAX)
        horizon_matters = (feas_at_min_relief != feas_at_max_relief)

        self._day_cache[key] = {"base_units": base_units, "horizon_relief": horizon_relief}
        if self.training and not globals().get('_SIMULATING_FEASIBILITY', False):
            self._episode_trace.append({
                "key": key, "feats": feats,
                "raw_bu": raw_bu, "raw_bu_mean": raw_bu_mean,
                "raw_hz": raw_hz, "raw_hz_mean": raw_hz_mean,
                "base_units": base_units, "horizon_relief": horizon_relief,
                "horizon_matters": horizon_matters,
            })
            self._bu_mean_history.append(raw_bu_mean)
            self._hz_mean_history.append(raw_hz_mean)
        return base_units, horizon_relief

    def get_idle_cash_params(self, ws: "WorldState", animal: str, unit_cost: float):
        self._record_net_worth(ws)
        self._record_product_output(ws)
        key = (ws.day, animal, globals().get('_SIMULATING_FEASIBILITY', False))
        if key in self._idle_day_cache:
            c = self._idle_day_cache[key]
            return c["idle_cash_start"], c["idle_cash_per_extra_unit"]

        feats = self._features(ws, animal, unit_cost)
        raw_start_mean = self._linear(self.idle_start_w, feats)
        raw_extra_mean = self._linear(self.idle_per_extra_w, feats)
        if self.training:
            raw_start = self._rng.gauss(raw_start_mean, self.idle_start_std)
            raw_extra = self._rng.gauss(raw_extra_mean, self.idle_per_extra_std)
        else:
            raw_start, raw_extra = raw_start_mean, raw_extra_mean

        start_sig = _ppo_sigmoid(raw_start)
        extra_sig = _ppo_sigmoid(raw_extra)
        idle_cash_start = self.IDLE_START_MIN + (self.IDLE_START_MAX - self.IDLE_START_MIN) * start_sig
        idle_cash_per_extra_unit = self.IDLE_PER_EXTRA_MIN + (
            self.IDLE_PER_EXTRA_MAX - self.IDLE_PER_EXTRA_MIN) * extra_sig

        self._idle_day_cache[key] = {"idle_cash_start": idle_cash_start,
                                      "idle_cash_per_extra_unit": idle_cash_per_extra_unit}
        if self.training and not globals().get('_SIMULATING_FEASIBILITY', False):
            self._idle_episode_trace.append({
                "key": key, "feats": feats,
                "raw_start": raw_start, "raw_start_mean": raw_start_mean,
                "raw_extra": raw_extra, "raw_extra_mean": raw_extra_mean,
                "idle_cash_start": idle_cash_start, "idle_cash_per_extra_unit": idle_cash_per_extra_unit,
            })
            self._start_mean_history.append(raw_start_mean)
            self._extra_mean_history.append(raw_extra_mean)
        return idle_cash_start, idle_cash_per_extra_unit

    ANIMAL_HORIZON_MAX = 15   

    def _horizon_for_animal(self, animal: str) -> int:
        info = ANIMAL_INFO.get(animal)
        if info is None:
            return self.reward_horizon_days_default
        horizon = info["first_yield"] + info["interval"]
        return min(horizon, self.ANIMAL_HORIZON_MAX)

    def _local_delta(self, decision_day: int, horizon_days: int) -> float:
        nw0 = self._nw_history.get(decision_day)
        if nw0 is None:
            return 0.0   
        target_day = decision_day + horizon_days
        candidate_days = [d for d in self._nw_history if d >= target_day]
        if candidate_days:
            nw1 = self._nw_history[min(candidate_days)]
        else:
            latest_day = max(self._nw_history)
            nw1 = self._nw_history[latest_day]
        return nw1 - nw0

    def update(self, episode_return: float, win_outcome: float = 0.0):
        if not self._episode_trace and not self._idle_episode_trace:
            return

        full_trace = self._episode_trace
        bu_trace = full_trace
        if self.filter_to_purchased_only:
            bu_trace = [s for s in full_trace if s["key"] in self._purchased_keys]
        hz_trace = [s for s in full_trace if s.get("horizon_matters", True)]
        # FIX (bug1 overcorrection): the purchased-only filter starved this head's
        # updates ~130x (ratio stuck at 0.16); reverting it since non-purchased days add variance, not bias.
        # hz_trace = [s for s in hz_trace if s["key"] in self._purchased_keys]

        idle_trace = self._idle_episode_trace
        if self.filter_to_purchased_only:
            idle_trace = [s for s in idle_trace if s["key"] in self._purchased_keys]

        # FIX (convergence-diag batch confound, part 2): record this
        # episode's batch size per head so _convergence_diag can rescale
        # signal_std by sqrt(avg_batch) -- see the note in __init__.
        self._bu_batch_history.append(len(bu_trace))
        self._hz_batch_history.append(len(hz_trace))
        self._idle_batch_history.append(len(idle_trace))

        if not bu_trace and not hz_trace and not idle_trace:
            return

        # episode-level baseline/advantage kept as fallback for when
        # use_isolated_reward is off (or local history is unavailable)
        b = self._episode_return_baseline
        self._episode_return_baseline = ((1 - self._return_baseline_alpha) * b
                                          + self._return_baseline_alpha * episode_return) if b is not None else episode_return
        episode_advantage = episode_return - (b if b is not None else episode_return)
        # FIX (reward metric, part 3): win_outcome is now its own argument
        # instead of pre-baked into episode_return, which shrank in relative
        # size as net_worth std grew across stages. Now a fixed post-squash term.
        win_term = RL_WIN_BONUS_REWARD * win_outcome
        episode_adv_scaled = math.tanh(episode_advantage / 5000.0) + win_term

        # FIX (broadcast credit assignment): update() broadcast the SAME whole-episode
        # advantage to every decision regardless of day. use_isolated_reward now
        # wires per-decision local advantage instead, same pattern as FloorCap/RateCap.
        LOCAL_ADV_SCALE = 5000.0
        prev_local_baseline = self._local_baseline
        # FIX (supersedes the isolated-reward patch's 85/15 blend, which existed
        # only because episode_adv_scaled was the sole win/loss path). Now win_term
        # is its own fixed-magnitude term, added on top of the full local component.

        def _local_adv_scaled(step):
            if not self.use_isolated_reward:
                return episode_adv_scaled
            day, animal = step["key"][0], step["key"][1]
            horizon = self._horizon_for_animal(animal)
            local_delta = self._local_delta(day, horizon)
            baseline_for_advantage = prev_local_baseline if prev_local_baseline is not None else local_delta
            local_component = math.tanh((local_delta - baseline_for_advantage) / LOCAL_ADV_SCALE)
            return local_component + win_term

        if self.use_isolated_reward:
            all_local_deltas = [self._local_delta(s["key"][0], self._horizon_for_animal(s["key"][1]))
                                 for s in (bu_trace + hz_trace + idle_trace)]
            mean_local_delta = sum(all_local_deltas) / len(all_local_deltas) if all_local_deltas else 0.0
            self._local_baseline = ((1 - self._local_baseline_alpha) * prev_local_baseline
                                     + self._local_baseline_alpha * mean_local_delta) \
                                    if prev_local_baseline is not None else mean_local_delta

        bu_step_scale = 1.0 / max(1, len(bu_trace))
        hz_step_scale = 1.0 / max(1, len(hz_trace))
        idle_step_scale = 1.0 / max(1, len(idle_trace))

        for step in bu_trace:
            feats = step["feats"]
            adv_scaled = _local_adv_scaled(step)
            d_bu = (step["raw_bu"] - step["raw_bu_mean"]) / (self.base_units_std ** 2)
            for name in self.feature_names:
                self.base_units_w[name] += bu_step_scale * self.lr * adv_scaled * d_bu * feats.get(name, 0.0)
        for step in hz_trace:
            feats = step["feats"]
            adv_scaled = _local_adv_scaled(step)
            d_hz = (step["raw_hz"] - step["raw_hz_mean"]) / (self.horizon_std ** 2)
            for name in self.feature_names:
                self.horizon_w[name] += hz_step_scale * self.lr * adv_scaled * d_hz * feats.get(name, 0.0)
        for step in idle_trace:
            feats = step["feats"]
            adv_scaled = _local_adv_scaled(step)
            d_start = (step["raw_start"] - step["raw_start_mean"]) / (self.idle_start_std ** 2)
            d_extra = (step["raw_extra"] - step["raw_extra_mean"]) / (self.idle_per_extra_std ** 2)
            for name in self.feature_names:
                self.idle_start_w[name] += idle_step_scale * self.lr * adv_scaled * d_start * feats.get(name, 0.0)
                self.idle_per_extra_w[name] += idle_step_scale * self.lr * adv_scaled * d_extra * feats.get(name, 0.0)

    def format_day_breakdown_idle(self, day: int, animal: str = None) -> str:
        rows = [r for r in self._idle_episode_trace if r["key"][0] == day
                and (animal is None or r["key"][1] == animal)]
        if not rows:
            return f"(no RL-Animal-2/idle_cash decision recorded for day {day})"
        r = rows[-1]
        feats = r["feats"]
        lines = [f"DAY {day} / {r['key'][1]}", "", "IDLE_CASH_START:"]
        for name in self.feature_names:
            if name == "bias":
                continue
            w = self.idle_start_w[name]
            lines.append(f"  {name:24s} x {w:+.4f} = {w * feats.get(name, 0.0):+.4f}")
        lines.append(f"  {'bias':24s}     = {self.idle_start_w['bias']:+.4f}")
        lines.append(f"  {'-'*41}")
        lines.append(f"  raw score (mean)      = {r['raw_start_mean']:+.4f}")
        lines.append(f"  idle_cash_start        = {r['idle_cash_start']:.4f}")
        lines.append("")
        lines.append("IDLE_CASH_PER_EXTRA_UNIT:")
        for name in self.feature_names:
            if name == "bias":
                continue
            w = self.idle_per_extra_w[name]
            lines.append(f"  {name:24s} x {w:+.4f} = {w * feats.get(name, 0.0):+.4f}")
        lines.append(f"  {'bias':24s}     = {self.idle_per_extra_w['bias']:+.4f}")
        lines.append(f"  {'-'*41}")
        lines.append(f"  raw score (mean)      = {r['raw_extra_mean']:+.4f}")
        lines.append(f"  idle_cash_per_extra_unit = {r['idle_cash_per_extra_unit']:.4f}")
        return "\n".join(lines)

    def _convergence_diag(self, n_last: int = 30) -> dict:
        # FIX (batch confound, part 3): signal_std shrinks purely because batch
        # size grew, not because signal weakened. Rescale by sqrt(avg_batch)
        # so ratios stay comparable across runs/heads with different batch sizes.
        def _one(history, noise_std, batch_history):
            if len(history) < 2:
                return None
            recent = history[-n_last:]
            signal_std = float(np.std(recent))
            avg_batch = (sum(batch_history) / len(batch_history)) if batch_history else 1.0
            signal_std *= math.sqrt(max(1.0, avg_batch))
            return signal_std / noise_std if noise_std > 0 else float("inf")

        ratios = {
            "base_units": _one(self._bu_mean_history, self.base_units_std, self._bu_batch_history),
            "horizon_relief": _one(self._hz_mean_history, self.horizon_std, self._hz_batch_history),
            "idle_cash_start": _one(self._start_mean_history, self.idle_start_std, self._idle_batch_history),
            "idle_cash_per_extra_unit": _one(self._extra_mean_history, self.idle_per_extra_std, self._idle_batch_history),
        }
        valid = {k: v for k, v in ratios.items() if v is not None}
        if not valid:
            return {"ratios": ratios, "worst_ratio": None, "converged": False,
                     "n_decisions_total": len(self._bu_mean_history)}
        worst_key = min(valid, key=valid.get)
        return {"ratios": ratios, "worst_ratio": valid[worst_key], "worst_head": worst_key,
                 "converged": valid[worst_key] >= 0.5, "n_decisions_total": len(self._bu_mean_history)}

RL_ANIMAL_CONTROLLER = ReinforceAnimalController()

PPO_STRUCT_CAP_MIN, PPO_STRUCT_CAP_MAX = 1, 4

PPO_ANIMAL_CAP_MIN, PPO_ANIMAL_CAP_MAX = 1, 6

PPO_PLANT_CAP_MIN, PPO_PLANT_CAP_MAX = 5, 30

PPO_RATE_FEATURE_NAMES = [
    "bias", "season_progress", "cash_ratio", "discretionary_cash_ratio",
    "current_workers_norm", "n_quadrants_norm",
]

class ReinforceRateCapController:

    def __init__(self, lr=0.02, struct_std=0.5, animal_std=0.6, plant_std=2.0, seed=0):
        self.enabled = False
        self.training = False
        self.enabled_animal = False
        self.enabled_plant = False
        self.lr = lr
        self.struct_std = struct_std
        self.animal_std = animal_std
        self.plant_std = plant_std
        self._rng = _ppo_random.Random(seed)
        self.struct_w = {name: 0.0 for name in PPO_RATE_FEATURE_NAMES}
        struct_sig = (2 - PPO_STRUCT_CAP_MIN) / (PPO_STRUCT_CAP_MAX - PPO_STRUCT_CAP_MIN)
        self.struct_w["bias"] = _ppo_inv_sigmoid(max(1e-3, min(1 - 1e-3, struct_sig)))

        self.animal_w = {name: 0.0 for name in PPO_RATE_FEATURE_NAMES}
        animal_sig = (2 - PPO_ANIMAL_CAP_MIN) / (PPO_ANIMAL_CAP_MAX - PPO_ANIMAL_CAP_MIN)
        self.animal_w["bias"] = _ppo_inv_sigmoid(max(1e-3, min(1 - 1e-3, animal_sig)))

        self.plant_w = {name: 0.0 for name in PPO_RATE_FEATURE_NAMES}
        plant_sig = (15 - PPO_PLANT_CAP_MIN) / (PPO_PLANT_CAP_MAX - PPO_PLANT_CAP_MIN)
        self.plant_w["bias"] = _ppo_inv_sigmoid(max(1e-3, min(1 - 1e-3, plant_sig)))

        self._episode_trace = []
        self._day_cache = {}          
        self._day_start_snapshot = {}  
        self._baseline = None
        self._baseline_alpha = 0.2
        self.reward_horizon_days = 5
        self._local_baseline = None
        self._local_baseline_alpha = 0.2
        self._nw_history = {}   

        # FIX (convergence gate coverage): rate-cap had no convergence
        # diagnostic; track per-head raw-mean history like alpha/animal do.
        self._struct_mean_history = []
        self._animal_mean_history = []
        self._plant_mean_history = []

    def reset_episode(self):
        self._episode_trace = []
        self._day_cache = {}
        self._day_start_snapshot = {}
        self._nw_history = {}

    def _record_net_worth(self, ws: "WorldState"):
        if ws.day not in self._nw_history:
            self._nw_history[ws.day] = _estimate_net_worth(ws)

    def _local_delta(self, decision_day: int) -> float:
        nw0 = self._nw_history.get(decision_day)
        if nw0 is None:
            return 0.0
        target_day = decision_day + self.reward_horizon_days
        candidate_days = [d for d in self._nw_history if d >= target_day]
        if candidate_days:
            nw1 = self._nw_history[min(candidate_days)]
        else:
            nw1 = self._nw_history[max(self._nw_history)]
        return nw1 - nw0

    def _features(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                  discretionary_cash: float = None) -> dict:
        season_days = getattr(ws, "season_days", 30) or 30
        season_progress = min(1.0, ws.day / max(1, season_days))
        money = max(0.0, ws.money)
        cash_ratio = math.tanh(money / 2000.0)
        current_workers = 1 + len(ws.hands)
        n_quadrants = max(1, getattr(ws, "n_quadrants", 1))
        if discretionary_cash is not None and discretionary_cash != float("inf"):
            discretionary_cash_ratio = math.tanh(max(0.0, discretionary_cash) / 2000.0)
        else:
            discretionary_cash_ratio = math.tanh(max(0.0, money - RESERVE_MIN_OPERATING_CASH) / 2000.0)
        return {
            "bias": 1.0,
            "season_progress": season_progress,
            "cash_ratio": cash_ratio,
            "discretionary_cash_ratio": discretionary_cash_ratio,
            "current_workers_norm": math.tanh(current_workers / 15.0),
            "n_quadrants_norm": (n_quadrants - 1) / 3.0,
            "day": ws.day,
        }

    def _linear(self, weights: dict, feats: dict) -> float:
        return sum(weights[n] * feats.get(n, 0.0) for n in PPO_RATE_FEATURE_NAMES)

    def _snapshot_counts(self, ws: "WorldState"):
        n_structures = ws.n_coop + ws.n_pasture
        n_animals = sum(ws.animal_counts.values())
        n_planted = sum(1 for row in ws.tiles for t in row
                         if isinstance(t, dict) and t.get("crop"))
        return (n_structures, n_animals, n_planted)

    def get_remaining_caps(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                            discretionary_cash: float = None):
        self._record_net_worth(ws)
        key = (ws.day, globals().get('_SIMULATING_FEASIBILITY', False))
        if key not in self._day_start_snapshot:
            self._day_start_snapshot[key] = self._snapshot_counts(ws)
            self._decide_for_day(ws, fa=fa, discretionary_cash=discretionary_cash)
        elif key not in self._day_cache:
            self._decide_for_day(ws, fa=fa, discretionary_cash=discretionary_cash)
        else:
            self._maybe_relief_for_quadrant_increase(ws, fa=fa, discretionary_cash=discretionary_cash)

        caps = self._day_cache[key]
        start = self._day_start_snapshot[key]
        cur = self._snapshot_counts(ws)
        built_today = max(0, cur[0] - start[0])
        bought_today = max(0, cur[1] - start[1])
        planted_today = max(0, cur[2] - start[2])
        remaining_structure = max(0, caps["structure_cap"] - built_today)
        remaining_animal = max(0, caps["animal_cap"] - bought_today)
        remaining_plant = max(0, caps["plant_cap"] - planted_today)
        return remaining_structure, remaining_animal, remaining_plant

    def _maybe_relief_for_quadrant_increase(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                                             discretionary_cash: float = None):
        key = (ws.day, globals().get('_SIMULATING_FEASIBILITY', False))
        caps = self._day_cache[key]
        last_nq = caps.get("decided_n_quadrants", 1)
        cur_nq = max(1, getattr(ws, "n_quadrants", 1))
        if cur_nq <= last_nq:
            return   

        feats = self._features(ws, fa=fa, discretionary_cash=discretionary_cash)
        raw_struct_mean = self._linear(self.struct_w, feats)
        raw_animal_mean = self._linear(self.animal_w, feats)
        raw_plant_mean = self._linear(self.plant_w, feats)
        new_structure_cap = int(round(PPO_STRUCT_CAP_MIN + (PPO_STRUCT_CAP_MAX - PPO_STRUCT_CAP_MIN) * _ppo_sigmoid(raw_struct_mean)))
        new_animal_cap = int(round(PPO_ANIMAL_CAP_MIN + (PPO_ANIMAL_CAP_MAX - PPO_ANIMAL_CAP_MIN) * _ppo_sigmoid(raw_animal_mean)))
        new_plant_cap = int(round(PPO_PLANT_CAP_MIN + (PPO_PLANT_CAP_MAX - PPO_PLANT_CAP_MIN) * _ppo_sigmoid(raw_plant_mean)))
        new_structure_cap = max(PPO_STRUCT_CAP_MIN, min(PPO_STRUCT_CAP_MAX, new_structure_cap))
        new_animal_cap = max(PPO_ANIMAL_CAP_MIN, min(PPO_ANIMAL_CAP_MAX, new_animal_cap))
        new_plant_cap = max(PPO_PLANT_CAP_MIN, min(PPO_PLANT_CAP_MAX, new_plant_cap))

        caps["structure_cap"] = max(caps["structure_cap"], new_structure_cap)
        caps["animal_cap"] = max(caps["animal_cap"], new_animal_cap)
        caps["plant_cap"] = max(caps["plant_cap"], new_plant_cap)
        caps["decided_n_quadrants"] = cur_nq

    def _decide_for_day(self, ws, fa=None, discretionary_cash=None):
        feats = self._features(ws, fa=fa, discretionary_cash=discretionary_cash)
        raw_struct_mean = self._linear(self.struct_w, feats)
        raw_animal_mean = self._linear(self.animal_w, feats)
        raw_plant_mean = self._linear(self.plant_w, feats)
        if self.training:
            raw_struct = self._rng.gauss(raw_struct_mean, self.struct_std)
            raw_animal = self._rng.gauss(raw_animal_mean, self.animal_std) if self.enabled_animal else raw_animal_mean
            raw_plant = self._rng.gauss(raw_plant_mean, self.plant_std) if self.enabled_plant else raw_plant_mean
        else:
            raw_struct, raw_animal, raw_plant = raw_struct_mean, raw_animal_mean, raw_plant_mean

        structure_cap = int(round(PPO_STRUCT_CAP_MIN + (PPO_STRUCT_CAP_MAX - PPO_STRUCT_CAP_MIN) * _ppo_sigmoid(raw_struct)))
        animal_cap = int(round(PPO_ANIMAL_CAP_MIN + (PPO_ANIMAL_CAP_MAX - PPO_ANIMAL_CAP_MIN) * _ppo_sigmoid(raw_animal)))
        plant_cap = int(round(PPO_PLANT_CAP_MIN + (PPO_PLANT_CAP_MAX - PPO_PLANT_CAP_MIN) * _ppo_sigmoid(raw_plant)))
        structure_cap = max(PPO_STRUCT_CAP_MIN, min(PPO_STRUCT_CAP_MAX, structure_cap))
        animal_cap = max(PPO_ANIMAL_CAP_MIN, min(PPO_ANIMAL_CAP_MAX, animal_cap))
        plant_cap = max(PPO_PLANT_CAP_MIN, min(PPO_PLANT_CAP_MAX, plant_cap))

        key = (ws.day, globals().get('_SIMULATING_FEASIBILITY', False))
        self._day_cache[key] = {"structure_cap": structure_cap, "animal_cap": animal_cap,
                                    "plant_cap": plant_cap,
                                    "decided_n_quadrants": max(1, getattr(ws, "n_quadrants", 1))}
        if self.training and not globals().get('_SIMULATING_FEASIBILITY', False):
            self._struct_mean_history.append(raw_struct_mean)
            if self.enabled_animal:
                self._animal_mean_history.append(raw_animal_mean)
            if self.enabled_plant:
                self._plant_mean_history.append(raw_plant_mean)
            entry = {
                "day": ws.day, "feats": feats,
                "raw_struct": raw_struct, "raw_struct_mean": raw_struct_mean,
                "structure_cap": structure_cap, "animal_cap": animal_cap, "plant_cap": plant_cap,
            }
            if self.enabled_animal:
                entry["raw_animal"] = raw_animal
                entry["raw_animal_mean"] = raw_animal_mean
            if self.enabled_plant:
                entry["raw_plant"] = raw_plant
                entry["raw_plant_mean"] = raw_plant_mean
            self._episode_trace.append(entry)

    def _convergence_diag(self, n_last: int = 30) -> dict:
        def _one(history, noise_std):
            if len(history) < 2:
                return None
            recent = history[-n_last:]
            signal_std = float(np.std(recent))
            return signal_std / noise_std if noise_std > 0 else float("inf")

        ratios = {
            "struct": _one(self._struct_mean_history, self.struct_std),
            "animal": _one(self._animal_mean_history, self.animal_std),
            "plant": _one(self._plant_mean_history, self.plant_std),
        }
        valid = {k: v for k, v in ratios.items() if v is not None}
        if not valid:
            return {"ratios": ratios, "worst_ratio": None, "converged": False,
                     "n_decisions_total": len(self._struct_mean_history)}
        worst_key = min(valid, key=valid.get)
        return {"ratios": ratios, "worst_ratio": valid[worst_key], "worst_head": worst_key,
                 "converged": valid[worst_key] >= 0.5, "n_decisions_total": len(self._struct_mean_history)}


    def update(self, episode_return: float, win_outcome: float = 0.0):
        if not self._episode_trace:
            return

        local_deltas = [self._local_delta(step["day"]) for step in self._episode_trace]
        mean_delta = sum(local_deltas) / len(local_deltas)
        prev_baseline = self._local_baseline
        # FIX (baseline leakage): same issue as FloorCap -- use PRE-update
        # baseline for advantage, not the one already blended with this
        # episode's own mean_delta.
        baseline_for_advantage = prev_baseline if prev_baseline is not None else mean_delta
        self._local_baseline = ((1 - self._local_baseline_alpha) * prev_baseline
                                 + self._local_baseline_alpha * mean_delta) if prev_baseline is not None else mean_delta

        step_scale = 1.0 / max(1, len(self._episode_trace))
        LOCAL_ADV_SCALE = 1000.0

        # FIX (reward metric, part 3): same as FloorCap -- RateCap had no
        # win/loss signal at all before. Fixed post-tanh nudge, seed-noise
        # independent.
        win_term = RL_WIN_BONUS_REWARD * win_outcome

        for step, delta in zip(self._episode_trace, local_deltas):
            feats = step["feats"]
            advantage = delta - baseline_for_advantage
            adv_scaled = math.tanh(advantage / LOCAL_ADV_SCALE) + win_term
            d_struct = (step["raw_struct"] - step["raw_struct_mean"]) / (self.struct_std ** 2)
            for name in PPO_RATE_FEATURE_NAMES:
                self.struct_w[name] += step_scale * self.lr * adv_scaled * d_struct * feats.get(name, 0.0)
            if "raw_animal" in step:
                d_animal = (step["raw_animal"] - step["raw_animal_mean"]) / (self.animal_std ** 2)
                for name in PPO_RATE_FEATURE_NAMES:
                    self.animal_w[name] += step_scale * self.lr * adv_scaled * d_animal * feats.get(name, 0.0)
            if "raw_plant" in step:
                d_plant = (step["raw_plant"] - step["raw_plant_mean"]) / (self.plant_std ** 2)
                for name in PPO_RATE_FEATURE_NAMES:
                    self.plant_w[name] += step_scale * self.lr * adv_scaled * d_plant * feats.get(name, 0.0)

RL_RATE_CONTROLLER = ReinforceRateCapController()

PPO_REORDER_BUFFER_MIN, PPO_REORDER_BUFFER_MAX = 0, 15

PPO_REORDER_FEATURE_NAMES = [
    "bias", "season_progress", "cash_ratio", "discretionary_cash_ratio",
    "current_workers_norm", "n_quadrants_norm", "fertilizable_tiles_norm",
]

class ReinforceReorderController:

    def __init__(self, lr=0.02, buffer_std=1.5, seed=0):
        self.enabled = False
        self.training = False
        self.lr = lr
        self.buffer_std = buffer_std
        self._rng = _ppo_random.Random(seed)

        self.buffer_w = {name: 0.0 for name in PPO_REORDER_FEATURE_NAMES}
        target_buffer_sig = (3 - PPO_REORDER_BUFFER_MIN) / (PPO_REORDER_BUFFER_MAX - PPO_REORDER_BUFFER_MIN)
        self.buffer_w["bias"] = _ppo_inv_sigmoid(max(1e-3, min(1 - 1e-3, target_buffer_sig)))

        self._episode_trace = []
        self._day_cache = {}
        self._baseline = None
        self._baseline_alpha = 0.2

        # FIX (convergence gate coverage): reorder had no convergence
        # diagnostic; track raw-mean history like alpha/animal do.
        self._buffer_mean_history = []

    def reset_episode(self):
        self._episode_trace = []
        self._day_cache = {}

    def _features(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                  discretionary_cash: float = None) -> dict:
        n_quadrants = max(1, getattr(ws, "n_quadrants", 1))
        current_workers = 1 + len(ws.hands)
        season_days = getattr(ws, "season_days", 30) or 30
        season_progress = min(1.0, ws.day / max(1, season_days))
        money = max(0.0, ws.money)
        cash_ratio = math.tanh(money / 2000.0)
        if discretionary_cash is not None and discretionary_cash != float("inf"):
            discretionary_cash_ratio = math.tanh(max(0.0, discretionary_cash) / 2000.0)
        else:
            discretionary_cash_ratio = math.tanh(max(0.0, money - RESERVE_MIN_OPERATING_CASH) / 2000.0)
        fertilizable_tiles_norm = math.tanh(len(fa.fertilizable_crop_tiles) / 10.0) if fa is not None else 0.0
        return {
            "bias": 1.0,
            "season_progress": season_progress,
            "cash_ratio": cash_ratio,
            "discretionary_cash_ratio": discretionary_cash_ratio,
            "current_workers_norm": math.tanh(current_workers / 15.0),
            "n_quadrants_norm": (n_quadrants - 1) / 3.0,
            "fertilizable_tiles_norm": fertilizable_tiles_norm,
        }

    def _linear(self, feats: dict) -> float:
        return sum(self.buffer_w[n] * feats.get(n, 0.0) for n in PPO_REORDER_FEATURE_NAMES)

    def get_fertilizer_reserve_target(self, ws: "WorldState", fa: "FarmAnalysis" = None,
                                       discretionary_cash: float = None) -> int:
        key = (ws.day, globals().get('_SIMULATING_FEASIBILITY', False))
        if key in self._day_cache:
            return self._day_cache[key]["buffer_target"]

        feats = self._features(ws, fa=fa, discretionary_cash=discretionary_cash)
        raw_mean = self._linear(feats)
        if self.training:
            raw = self._rng.gauss(raw_mean, self.buffer_std)
        else:
            raw = raw_mean
        sig = _ppo_sigmoid(raw)
        buffer_target = int(round(PPO_REORDER_BUFFER_MIN + (PPO_REORDER_BUFFER_MAX - PPO_REORDER_BUFFER_MIN) * sig))
        buffer_target = max(PPO_REORDER_BUFFER_MIN, min(PPO_REORDER_BUFFER_MAX, buffer_target))

        key = (ws.day, globals().get('_SIMULATING_FEASIBILITY', False))
        self._day_cache[key] = {"buffer_target": buffer_target}
        if self.training and not globals().get('_SIMULATING_FEASIBILITY', False):
            self._buffer_mean_history.append(raw_mean)
            self._episode_trace.append({
                "day": ws.day, "feats": feats,
                "raw": raw, "raw_mean": raw_mean, "buffer_target": buffer_target,
            })
        return buffer_target

    def _convergence_diag(self, n_last: int = 30) -> dict:
        if len(self._buffer_mean_history) < 2:
            return {"ratios": {"buffer": None}, "worst_ratio": None, "converged": False,
                     "n_decisions_total": len(self._buffer_mean_history)}
        recent = self._buffer_mean_history[-n_last:]
        signal_std = float(np.std(recent))
        ratio = signal_std / self.buffer_std if self.buffer_std > 0 else float("inf")
        return {"ratios": {"buffer": ratio}, "worst_ratio": ratio, "worst_head": "buffer",
                 "converged": ratio >= 0.5, "n_decisions_total": len(self._buffer_mean_history)}


    def update(self, episode_return: float, win_outcome: float = 0.0):
        if not self._episode_trace:
            return
        prev_baseline = self._baseline
        # FIX (baseline leakage): same bug as FloorCap/RateCap before their fix
        # -- advantage was computed against the JUST-updated self._baseline,
        # damping the gradient by ~alpha every episode. Use prev_baseline.
        baseline_for_advantage = prev_baseline if prev_baseline is not None else episode_return
        self._baseline = ((1 - self._baseline_alpha) * prev_baseline
                           + self._baseline_alpha * episode_return) if prev_baseline is not None else episode_return
        advantage = episode_return - baseline_for_advantage
        # FIX (reward metric, part 3): Reorder had no win/loss signal before
        # (episode_return was always plain net_worth). Same fixed post-tanh
        # nudge as every other controller now.
        win_term = RL_WIN_BONUS_REWARD * win_outcome
        adv_scaled = math.tanh(advantage / 5000.0) + win_term
        step_scale = 1.0 / max(1, len(self._episode_trace))
        for step in self._episode_trace:
            feats = step["feats"]
            d = (step["raw"] - step["raw_mean"]) / (self.buffer_std ** 2)
            for name in PPO_REORDER_FEATURE_NAMES:
                self.buffer_w[name] += step_scale * self.lr * adv_scaled * d * feats.get(name, 0.0)

    def format_day_breakdown(self, day: int) -> str:
        rows = [r for r in self._episode_trace if r["day"] == day]
        if not rows:
            return f"(no RL-Buffer decision recorded for day {day})"
        r = rows[-1]
        feats = r["feats"]
        lines = [f"DAY {day}", "", "FERTILIZER_RESERVE_TARGET:"]
        for name in PPO_REORDER_FEATURE_NAMES:
            if name == "bias":
                continue
            w = self.buffer_w[name]
            lines.append(f"  {name:24s} x {w:+.4f} = {w * feats.get(name, 0.0):+.4f}")
        lines.append(f"  {'bias':24s}     = {self.buffer_w['bias']:+.4f}")
        lines.append(f"  {'-'*41}")
        lines.append(f"  raw score (mean)      = {r['raw_mean']:+.4f}")
        lines.append(f"  buffer_target          = {r['buffer_target']}")
        return "\n".join(lines)

RL_REORDER_CONTROLLER = ReinforceReorderController()

def _hand_cap_for_quadrant(n_quadrants: int, day: int = None, ws: "WorldState" = None,
                            fa: "FarmAnalysis" = None, discretionary_cash: float = None,
                            mandatory_future_cost: float = None) -> int:
    if RL_FLOORCAP_CONTROLLER is not None and RL_FLOORCAP_CONTROLLER.enabled and ws is not None:
        return RL_FLOORCAP_CONTROLLER.get_cap_per_quadrant(ws, fa=fa, discretionary_cash=discretionary_cash,
                                                     mandatory_future_cost=mandatory_future_cost)
    base = 3 if n_quadrants <= 1 else (5 if n_quadrants == 2 else 7)
    if day is None:
        return base
    return base + _DAY_PHASE_BONUS[_day_phase_idx(day)]

RESERVE_MIN_OPERATING_CASH = 10.0

LABOR_COST_PER_TASK = 5.0

FEED_WHEAT_SELL_RESERVE = 3

FERTILIZER_SELL_RESERVE = 3

STRUCTURE_FOR_ANIMAL = {name: info["structure"] for name, info in ANIMAL_INFO.items()}

_HALF_BOARD = BOARD_SIZE // 2

SHED_ACCESS_TILES = ((_HALF_BOARD - 1, _HALF_BOARD - 1), (_HALF_BOARD, _HALF_BOARD - 1),
                      (_HALF_BOARD - 1, _HALF_BOARD), (_HALF_BOARD, _HALF_BOARD))

def _unlocked_shop_list(obs):
    town = obs.get("town", {}) if isinstance(obs, dict) else getattr(obs, "town", {})
    if isinstance(town, dict):
        return list(town.get("unlocked_shops", []))
    return list(getattr(town, "unlocked_shops", []) or [])

@dataclass(frozen=True)
class WorldState:
    day: int
    turn_in_episode: int
    remaining_days: int
    season_ending: bool
    is_terminal_phase: bool

    money: float

    tiles: tuple
    seeds: dict
    shed: dict
    n_quadrants: int
    farmer: tuple
    hands: tuple
    n_animals: int
    n_coop: int
    n_pasture: int
    animal_counts: dict   
    farmer_inventory: dict   

    prices: dict

    opp_money: float
    opp_land: int
    opp_animals: int

    unlocked_shops: tuple

    all_inventories: tuple = ()   
    raw_obs: Any = field(default=None, repr=False, compare=False)
    opp_crop_counts: dict = field(default_factory=dict)     
    opp_animal_counts: dict = field(default_factory=dict)   

def build_world_state(obs) -> WorldState:
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]

    day = obs["day"]
    turn_in_episode = obs.get("step", obs.get("turn", day * TURNS_PER_DAY))

    n_coop = sum(1 for row in me["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "COOP")
    n_pasture = sum(1 for row in me["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
    n_animals = sum(1 for row in me["tiles"] for t in row if isinstance(t, dict) and t.get("animal"))
    animal_counts: dict = {}
    for row in me["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                animal_counts[t["animal"]] = animal_counts.get(t["animal"], 0) + 1

    all_farms = obs["farms"]
    if isinstance(all_farms, dict):
        opp_indices = [p for p in all_farms.keys() if p != player]
    else:
        opp_indices = [p for p in range(len(all_farms)) if p != player]
    opp = all_farms[opp_indices[0]] if opp_indices else {}
    opp_money = opp.get("money", 0.0)
    opp_land = len(opp.get("unlocked_quadrants", []))
    opp_animals = (
        sum(1 for row in opp.get("tiles", []) for t in row if isinstance(t, dict) and t.get("animal"))
        if opp else 0
    )
    opp_crop_counts: dict = {}
    opp_animal_counts: dict = {}
    for row in opp.get("tiles", []):
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") == "PLANT" and t.get("crop"):
                opp_crop_counts[t["crop"]] = opp_crop_counts.get(t["crop"], 0) + 1
            if t.get("animal"):
                opp_animal_counts[t["animal"]] = opp_animal_counts.get(t["animal"], 0) + 1

    remaining_days = max(0, SEASON_DAYS - day)

    inventories = private.get("inventories", [])
    farmer_inventory = dict(inventories[0]) if inventories else {}
    all_inventories = tuple(dict(inv) for inv in inventories) if inventories else ()

    return WorldState(
        day=day,
        turn_in_episode=turn_in_episode,
        remaining_days=remaining_days,
        season_ending=remaining_days <= 2,
        is_terminal_phase=turn_in_episode >= TERMINAL_TURN_THRESHOLD,
        money=me["money"],
        tiles=tuple(tuple(row) for row in me["tiles"]),
        seeds=dict(private["seeds"]),
        shed=dict(private["shed"]),
        n_quadrants=len(me["unlocked_quadrants"]),
        farmer=tuple(me["farmer"]) if me.get("farmer") is not None else (0, 0),
        hands=tuple(me["hands"]),
        n_animals=n_animals,
        n_coop=n_coop,
        n_pasture=n_pasture,
        animal_counts=animal_counts,
        farmer_inventory=farmer_inventory,
        all_inventories=all_inventories,
        prices=dict(obs["market"]["prices"]),
        opp_money=opp_money,
        opp_land=opp_land,
        opp_animals=opp_animals,
        opp_crop_counts=opp_crop_counts,
        opp_animal_counts=opp_animal_counts,
        unlocked_shops=tuple(_unlocked_shop_list(obs)),
        raw_obs=obs,
    )

def crop_fsm_state(tile, current_day=None):
    crop = tile.get("crop")
    planted_day = tile.get("planted_day")
    info = CROP_INFO.get(crop, {})
    maturity_day = info.get("max_yield_day")

    is_mature = (
        current_day is not None and planted_day is not None and maturity_day is not None
        and current_day - planted_day >= maturity_day
    )
    if is_mature:
        return "READY_HARVEST"
    if not tile.get("watered_today"):
        return "NEED_WATER" if tile.get("consecutive_unwatered", 0) >= 1 else "PLANTED_UNWATERED"
    return "GROWING"

def animal_fsm_state(tile):
    if tile.get("yield_units", 0) > 0:
        return "PRODUCT_READY"
    if not tile.get("fed_today"):
        return "HUNGRY"
    if not tile.get("cared_today"):
        return "FED_UNCARED"
    return "CARED"

def weed_fsm_state(age_turns, threat_value=0.0):
    urgency = age_turns * (1.0 + threat_value / 100.0)
    return "HIGH_PRIORITY" if urgency >= 4.0 else "LOW_PRIORITY"

def _adjacent_crop_value(tiles, pos, prices):
    x, y = pos
    total = 0.0
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= ny < len(tiles) and 0 <= nx < len(tiles[ny]):
            t = tiles[ny][nx]
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                crop = t.get("crop")
                info = CROP_INFO.get(crop, {})
                total += prices.get(crop, info.get("base_price", 0))
    return total

@dataclass(frozen=True)
class FarmAnalysis:
    empty_tiles: tuple
    ready_harvest_tiles: tuple
    need_water_tiles: tuple
    growing_tiles: tuple

    hungry_animal_tiles: tuple
    product_ready_tiles: tuple
    cared_animal_tiles: tuple
    empty_animal_structure_tiles: tuple   

    weed_tiles_high: tuple
    weed_tiles_low: tuple

    idle_workers: tuple
    active_workers: tuple

    limbo_tiles: tuple

    fertilizer_ready_tiles: tuple = ()
    fertilizable_crop_tiles: tuple = ()

    counts: dict = field(default_factory=dict)

def build_farm_analysis(ws: WorldState, mem: dict) -> FarmAnalysis:
    empty_tiles = []
    ready_harvest, need_water, growing = [], [], []
    hungry, product_ready, cared = [], [], []
    weed_high, weed_low = [], []
    limbo = []
    empty_animal_structure = []   
    fertilizer_ready = []   
    fertilizable_crop = []  

    weed_age = mem.setdefault("weed_age", {})
    known_planted = mem.setdefault("own_planted_day", {})

    for y, row in enumerate(ws.tiles):
        for x, t in enumerate(row):
            pos = (x, y)
            if t is None:
                empty_tiles.append(pos)
                continue
            if not isinstance(t, dict):
                limbo.append(pos)
                continue

            kind = t.get("kind")

            if kind == "PLANT":
                planted_day = t.get("planted_day", known_planted.get(pos))
                if planted_day is not None:
                    known_planted[pos] = planted_day
                state = crop_fsm_state({**t, "planted_day": planted_day}, current_day=ws.day)
                crop = t.get("crop")
                if state == "READY_HARVEST":
                    ready_harvest.append((pos, crop))
                elif state == "NEED_WATER":
                    need_water.append((pos, crop))
                else:
                    growing.append((pos, crop))

                fertilized_until = t.get("fertilized_until_day", -1)
                if fertilized_until < ws.day + 2:
                    fertilizable_crop.append((pos, crop))

            elif kind in ("COOP", "PASTURE"):
                if "animal" not in t:
                    empty_animal_structure.append((pos, kind))
                    continue
                animal_type = t.get("animal")
                if not t.get("fed_today"):
                    hungry.append((pos, animal_type, t.get("consecutive_unfed", 0)))
                if t.get("yield_units", 0) > 0:
                    product = ANIMAL_INFO.get(animal_type, {}).get("product")
                    product_ready.append((pos, animal_type, product, t.get("yield_units", 0)))
                if t.get("fed_today") and not t.get("cared_today"):
                    cared.append((pos, animal_type))
                if t.get("fertilizer_available"):
                    fertilizer_ready.append((pos, animal_type))

            elif kind == "ANIMAL":
                state = animal_fsm_state(t)
                animal_type = t.get("animal_type")
                if state == "HUNGRY":
                    hungry.append((pos, animal_type, t.get("consecutive_unfed", 0)))
                elif state == "PRODUCT_READY":
                    product_ready.append((pos, animal_type, t.get("product"), t.get("yield_units", 0)))
                else:
                    cared.append((pos, animal_type))

            elif kind == "WEED":
                age = weed_age.get(pos, 0) + 1
                weed_age[pos] = age
                threat = _adjacent_crop_value(ws.tiles, pos, ws.prices)
                state = weed_fsm_state(age, threat)
                (weed_high if state == "HIGH_PRIORITY" else weed_low).append(pos)

            else:
                limbo.append(pos)

    live_weed_positions = set(weed_high) | set(weed_low)
    for pos in list(weed_age.keys()):
        if pos not in live_weed_positions:
            weed_age.pop(pos, None)

    n_workers = 1 + len(ws.hands)
    idle_workers = tuple(range(n_workers))
    active_workers = ()

    counts = {
        "empty_tiles": len(empty_tiles),
        "ready_harvest": len(ready_harvest),
        "need_water": len(need_water),
        "growing": len(growing),
        "hungry_animals": len(hungry),
        "product_ready": len(product_ready),
        "weed_high": len(weed_high),
        "weed_low": len(weed_low),
        "idle_workers": len(idle_workers),
        "limbo_tiles": len(limbo),
        "empty_animal_structure": len(empty_animal_structure),
    }

    return FarmAnalysis(
        empty_tiles=tuple(empty_tiles),
        ready_harvest_tiles=tuple(ready_harvest),
        need_water_tiles=tuple(need_water),
        growing_tiles=tuple(growing),
        hungry_animal_tiles=tuple(hungry),
        product_ready_tiles=tuple(product_ready),
        cared_animal_tiles=tuple(cared),
        empty_animal_structure_tiles=tuple(empty_animal_structure),
        weed_tiles_high=tuple(weed_high),
        weed_tiles_low=tuple(weed_low),
        idle_workers=idle_workers,
        active_workers=active_workers,
        limbo_tiles=tuple(limbo),
        fertilizer_ready_tiles=tuple(fertilizer_ready),
        fertilizable_crop_tiles=tuple(fertilizable_crop),
        counts=counts,
    )

@dataclass(frozen=True)
class ProjectStep:
    id: str                       
    action_type: str              
    prerequisites: tuple = ()     
    resource_requirements: dict = field(default_factory=dict)   
    cost: float = 0.0
    duration: int = 1             
    produces: dict = field(default_factory=dict)     
    unlocks: tuple = ()           

@dataclass(frozen=True)
class Project:
    id: str                       
    steps: tuple                  
    deadline: Optional[int] = None            
    min_profitable_horizon: int = 0           

    def step_by_id(self, step_id):
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

PROJECT_REGISTRY = {
    "GOOSE_ECONOMY": Project(
        id="GOOSE_ECONOMY",
        deadline=None,
        min_profitable_horizon=6,   
        steps=(
            ProjectStep(id="BUILD_COOP", action_type="BUILD_STRUCTURE",
                        prerequisites=(), resource_requirements={},
                        cost=150.0, duration=1, produces={"n_coop": 1}),
            ProjectStep(id="BUY_GOOSE", action_type="BUY_ANIMAL",
                        prerequisites=(), resource_requirements={"COOP": 1},
                        cost=ANIMAL_INFO["GOOSE"]["cost"], duration=1, produces={"shed.GOOSE": 1}),
            ProjectStep(id="PICKUP_GOOSE", action_type="PICKUP",
                        prerequisites=("BUY_GOOSE",), resource_requirements={},
                        cost=0.0, duration=1, produces={"inv.GOOSE": 1}),
            ProjectStep(id="PLACE_GOOSE", action_type="PLACE",
                        prerequisites=("PICKUP_GOOSE",), resource_requirements={"COOP": 1},
                        cost=0.0, duration=1, produces={"n_animals": 1}),
            ProjectStep(id="FEED_GOOSE", action_type="FEED_ANIMAL",
                        prerequisites=("PLACE_GOOSE",), resource_requirements={},
                        cost=0.0, duration=1, produces={}),
            ProjectStep(id="COLLECT_EGG", action_type="COLLECT_PRODUCT",
                        prerequisites=("FEED_GOOSE",), resource_requirements={},
                        cost=0.0, duration=1, produces={"shed.EGG": "+yield"}),
            ProjectStep(id="SELL_EGG", action_type="SELL_PRODUCT",
                        prerequisites=("COLLECT_EGG",), resource_requirements={},
                        cost=0.0, duration=1, produces={"money": "+revenue"}),
        ),
    ),
    "COW_ECONOMY": Project(
        id="COW_ECONOMY",
        deadline=None,
        min_profitable_horizon=10,
        steps=(
            ProjectStep(id="BUILD_PASTURE", action_type="BUILD_STRUCTURE",
                        prerequisites=(), resource_requirements={},
                        cost=200.0, duration=1, produces={"n_pasture": 1}),
            ProjectStep(id="BUY_COW", action_type="BUY_ANIMAL",
                        prerequisites=(), resource_requirements={"PASTURE": 1},
                        cost=ANIMAL_INFO["COW"]["cost"], duration=1, produces={"shed.COW": 1}),
            ProjectStep(id="PICKUP_COW", action_type="PICKUP",
                        prerequisites=("BUY_COW",), resource_requirements={},
                        cost=0.0, duration=1, produces={"inv.COW": 1}),
            ProjectStep(id="PLACE_COW", action_type="PLACE",
                        prerequisites=("PICKUP_COW",), resource_requirements={"PASTURE": 1},
                        cost=0.0, duration=1, produces={"n_animals": 1}),
            ProjectStep(id="FEED_COW", action_type="FEED_ANIMAL",
                        prerequisites=("PLACE_COW",), resource_requirements={}, cost=0.0, duration=1, produces={}),
            ProjectStep(id="COLLECT_MILK", action_type="COLLECT_PRODUCT",
                        prerequisites=("FEED_COW",), resource_requirements={}, cost=0.0, duration=1,
                        produces={"shed.MILK": "+yield"}),
            ProjectStep(id="SELL_MILK", action_type="SELL_PRODUCT",
                        prerequisites=("COLLECT_MILK",), resource_requirements={}, cost=0.0, duration=1,
                        produces={"money": "+revenue"}),
        ),
    ),
    "SHEEP_ECONOMY": Project(
        id="SHEEP_ECONOMY",
        deadline=None,
        min_profitable_horizon=12,   
        steps=(
            ProjectStep(id="BUILD_PASTURE_SHEEP", action_type="BUILD_STRUCTURE",
                        prerequisites=(), resource_requirements={},
                        cost=200.0, duration=1, produces={"n_pasture": 1}),
            ProjectStep(id="BUY_SHEEP", action_type="BUY_ANIMAL",
                        prerequisites=(), resource_requirements={"PASTURE": 1},
                        cost=ANIMAL_INFO["SHEEP"]["cost"], duration=1, produces={"shed.SHEEP": 1}),
            ProjectStep(id="PICKUP_SHEEP", action_type="PICKUP",
                        prerequisites=("BUY_SHEEP",), resource_requirements={},
                        cost=0.0, duration=1, produces={"inv.SHEEP": 1}),
            ProjectStep(id="PLACE_SHEEP", action_type="PLACE",
                        prerequisites=("PICKUP_SHEEP",), resource_requirements={"PASTURE": 1},
                        cost=0.0, duration=1, produces={"n_animals": 1}),
            ProjectStep(id="FEED_SHEEP", action_type="FEED_ANIMAL",
                        prerequisites=("PLACE_SHEEP",), resource_requirements={}, cost=0.0, duration=1, produces={}),
            ProjectStep(id="COLLECT_WOOL", action_type="COLLECT_PRODUCT",
                        prerequisites=("FEED_SHEEP",), resource_requirements={}, cost=0.0, duration=1,
                        produces={"shed.WOOL": "+yield"}),
            ProjectStep(id="SELL_WOOL", action_type="SELL_PRODUCT",
                        prerequisites=("COLLECT_WOOL",), resource_requirements={}, cost=0.0, duration=1,
                        produces={"money": "+revenue"}),
        ),
    ),
    "CROP_PROJECT": Project(
        id="CROP_PROJECT",
        deadline=None,
        min_profitable_horizon=1,
        steps=(
            ProjectStep(id="BUY_SEED", action_type="BUY_SEED", prerequisites=(),
                        resource_requirements={}, cost=0.0, duration=1, produces={}),
            ProjectStep(id="PLANT", action_type="PLANT", prerequisites=("BUY_SEED",),
                        resource_requirements={"EMPTY_TILE": 1}, cost=0.0, duration=1, produces={}),
            ProjectStep(id="WATER", action_type="WATER", prerequisites=("PLANT",),
                        resource_requirements={}, cost=0.0, duration=1, produces={}),
            ProjectStep(id="HARVEST", action_type="HARVEST", prerequisites=("WATER",),
                        resource_requirements={}, cost=0.0, duration=1, produces={}),
            ProjectStep(id="SELL", action_type="SELL_PRODUCT", prerequisites=("HARVEST",),
                        resource_requirements={}, cost=0.0, duration=1, produces={"money": "+revenue"}),
        ),
    ),
}

from collections import deque as _deque_diag_log
@dataclass(frozen=True)
class ProjectStepStatus:
    step_id: str
    status: str          
    missing_prerequisites: tuple = ()
    missing_resources: tuple = ()

@dataclass(frozen=True)
class ProjectStatus:
    project_id: str
    step_statuses: tuple            
    season_feasible: bool           
    active: bool                    

    def status_of(self, step_id):
        for s in self.step_statuses:
            if s.step_id == step_id:
                return s
        return None

    def next_unlocked_steps(self):
        return tuple(s.step_id for s in self.step_statuses if s.status == "UNLOCKED")

def _resource_available(req: dict, ws: WorldState) -> tuple:
    missing = []
    for resource, needed in req.items():
        if resource == "COOP" and (ws.n_coop - ws.animal_counts.get("GOOSE", 0)) < needed:
            missing.append(resource)
        elif resource == "PASTURE" and (ws.n_pasture - ws.animal_counts.get("COW", 0)
                                         - ws.animal_counts.get("SHEEP", 0)) < needed:
            missing.append(resource)
        elif resource == "EMPTY_TILE" and len(ws.tiles) == 0:
            pass
    return tuple(missing)

_CYCLICAL_ACTION_TYPES = ("PLANT", "WATER", "HARVEST", "COLLECT_PRODUCT", "SELL_PRODUCT", "FEED_ANIMAL",
                           "BUY_ANIMAL", "PICKUP", "PLACE")

def evaluate_project(project: Project, ws: WorldState, completed_step_ids: frozenset) -> ProjectStatus:
    step_by_id = {s.id: s for s in project.steps}
    statuses = []
    for step in project.steps:
        if step.id in completed_step_ids:
            statuses.append(ProjectStepStatus(step.id, "DONE"))
            continue

        missing_prereq = tuple(
            p for p in step.prerequisites
            if p not in completed_step_ids
            and step_by_id.get(p) is not None
            and step_by_id[p].action_type not in _CYCLICAL_ACTION_TYPES
        )
        if missing_prereq:
            statuses.append(ProjectStepStatus(step.id, "LOCKED_BY_PREREQUISITE", missing_prerequisites=missing_prereq))
            continue

        missing_res = _resource_available(step.resource_requirements, ws)
        if missing_res:
            statuses.append(ProjectStepStatus(step.id, "LOCKED_BY_RESOURCE", missing_resources=missing_res))
            continue

        statuses.append(ProjectStepStatus(step.id, "UNLOCKED"))

    effective_horizon = project.min_profitable_horizon
    if (RL_ANIMAL_CONTROLLER is not None and RL_ANIMAL_CONTROLLER.enabled
            and project.id in PROJECT_ANIMAL):
        animal = PROJECT_ANIMAL[project.id]
        info = ANIMAL_INFO.get(animal, {})
        structure_step = next((s for s in project.steps if s.action_type == "BUILD_STRUCTURE"), None)
        unit_cost = (structure_step.cost if structure_step else 0.0) + info.get("cost", 0.0)
        _, horizon_relief = RL_ANIMAL_CONTROLLER.get_decision(ws, animal, unit_cost)
        effective_horizon = max(0.0, project.min_profitable_horizon + horizon_relief)
    season_feasible = ws.remaining_days >= effective_horizon
    all_done = all(s.status == "DONE" for s in statuses)

    return ProjectStatus(
        project_id=project.id,
        step_statuses=tuple(statuses),
        season_feasible=season_feasible,
        active=season_feasible and not all_done,
    )

def infer_completed_steps(project: Project, ws: WorldState) -> frozenset:
    done = set()
    for step in project.steps:
        if step.id == "BUILD_COOP" and ws.n_coop >= _animal_target_units("GOOSE_ECONOMY", ws):
            done.add(step.id)
        elif step.id == "BUILD_PASTURE" and ws.n_pasture >= _animal_target_units("COW_ECONOMY", ws):
            done.add(step.id)
        elif step.id == "BUILD_PASTURE_SHEEP" and ws.n_pasture >= _animal_target_units("SHEEP_ECONOMY", ws):
            done.add(step.id)
        elif step.id == "BUY_GOOSE" and ws.animal_counts.get("GOOSE", 0) >= _animal_target_units("GOOSE_ECONOMY", ws):
            done.add(step.id)
        elif step.id == "BUY_COW" and ws.animal_counts.get("COW", 0) >= _animal_target_units("COW_ECONOMY", ws):
            done.add(step.id)
        elif step.id == "BUY_SHEEP" and ws.animal_counts.get("SHEEP", 0) >= _animal_target_units("SHEEP_ECONOMY", ws):
            done.add(step.id)
        elif step.id == "BUY_SEED":
            done.add(step.id)
    return frozenset(done)

def evaluate_all_projects(ws: WorldState, memory: dict) -> dict:
    ledger = memory.setdefault("completed_project_steps", {})
    result = {}
    for pid, project in PROJECT_REGISTRY.items():
        completed = frozenset(ledger.get(pid, set())) | infer_completed_steps(project, ws)
        result[pid] = evaluate_project(project, ws, completed)
    return result

@dataclass(frozen=True)
class Candidate:
    id: str                      
    project_id: str              
    step_id: str                 
    action_type: str
    target: Any = None           

    cost: float = 0.0
    expected_revenue: float = 0.0
    duration: int = 1
    deadline: Optional[int] = None

    financial_status: str = "UNKNOWN"   
    financially_blocked: bool = False
    meta: dict = field(default_factory=dict)   
    required_worker_index: Optional[int] = None

@dataclass(frozen=True)
class RejectedOpportunity:
    project_id: str
    step_id: str
    reason: str                  

@dataclass(frozen=True)
class CandidateBatch:
    candidates: tuple
    rejected: tuple              

def _financial_status(cost: float, discretionary_cash: float) -> str:
    return "AFFORDABLE" if cost <= discretionary_cash else "DEFER"

def _discretionary_cash(ws: WorldState, mandatory_future_cost: float = 0.0) -> float:
    return max(0.0, ws.money - mandatory_future_cost - RESERVE_MIN_OPERATING_CASH)

def _project_milestone_revenue_proxy(project_id: str, ws: WorldState) -> float:
    animal = PROJECT_ANIMAL.get(project_id)
    if animal is None or animal not in ANIMAL_INFO:
        return 0.0
    info = ANIMAL_INFO[animal]
    product = info["product"]
    price = ws.prices.get(product, info["base_price"])
    daily_yield = 1.0 / max(1, info["interval"])   
    daily_revenue = price * daily_yield
    horizon = max(0, ws.remaining_days)
    return daily_revenue * horizon

ANIMAL_BASE_UNITS_PER_SPECIES = 2

ANIMAL_MAX_UNITS_PER_SPECIES_CEILING = 12

ANIMAL_RAMP_UP_DAYS = 3

ANIMAL_IDLE_CASH_RATIO_START = 5.0

ANIMAL_IDLE_CASH_RATIO_PER_EXTRA_UNIT = 5.0

def _animal_gross_daily_revenue(animal: str, ws: WorldState) -> float:
    if animal is None or animal not in ANIMAL_INFO:
        return 0.0
    info = ANIMAL_INFO[animal]
    price = ws.prices.get(info["product"], info["base_price"])
    return price * (1.0 / max(1, info["interval"]))

ANIMAL_GATE_LOG = _deque_diag_log(maxlen=2000)
ANIMAL_CANDIDATE_LOG = _deque_diag_log(maxlen=2000)

ANIMAL_ACTIONS_PER_DAY = 2  

def _animal_net_economics(project_id: str, ws: WorldState) -> Optional[dict]:
    animal = PROJECT_ANIMAL.get(project_id)
    if animal is None or animal not in ANIMAL_INFO:
        return None
    info = ANIMAL_INFO[animal]
    product = info["product"]
    price = ws.prices.get(product, info["base_price"])
    daily_revenue = price * (1.0 / max(1, info["interval"]))
    useful_days = max(0, ws.remaining_days - ANIMAL_RAMP_UP_DAYS)

    project = PROJECT_REGISTRY.get(project_id)
    structure_step = next((s for s in project.steps if s.action_type == "BUILD_STRUCTURE"), None) if project else None
    structure_cost = structure_step.cost if structure_step else 0.0
    unit_cost = structure_cost + info["cost"]

    crop_ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
    best_crop_profit_per_day = max(0.0, crop_ranked[0].profit_per_day) if crop_ranked else 0.0
    worker_day_value_at_crop = best_crop_profit_per_day * LAND_UTILIZATION_TILES_PER_DAY
    crop_alternative_value = (ANIMAL_ACTIONS_PER_DAY / TURNS_PER_DAY) * worker_day_value_at_crop
    other_animal_alternative_value = max(
        (_animal_gross_daily_revenue(other, ws) for other in ANIMAL_INFO
         if other != animal and ws.animal_counts.get(other, 0) > 0),
        default=0.0)
    opportunity_cost_per_day = max(crop_alternative_value, other_animal_alternative_value)
    net_daily_value = daily_revenue - opportunity_cost_per_day

    economic_value = net_daily_value * useful_days - unit_cost
    payback_days = unit_cost / max(1e-6, net_daily_value) if net_daily_value > 0 else float("inf")
    horizon_days = ANIMAL_RAMP_UP_DAYS + useful_days   
    gate_open = not (useful_days <= 0 or daily_revenue <= 0 or economic_value <= 0
                      or net_daily_value <= 0 or payback_days > ws.remaining_days)
    return {
        "animal": animal, "project_id": project_id,
        "daily_revenue": daily_revenue,
        "crop_alternative_value": crop_alternative_value,
        "other_animal_alternative_value": other_animal_alternative_value,
        "opportunity_cost_per_day": opportunity_cost_per_day,
        "net_daily_value": net_daily_value,
        "unit_cost": unit_cost,
        "useful_days": useful_days,
        "horizon_days": horizon_days,
        "economic_value": economic_value,
        "payback_days": payback_days,
        "remaining_days": ws.remaining_days,
        "gate_open": gate_open,
        "reject_reason": (
            "OK" if gate_open else
            "useful_days<=0 or daily_revenue<=0" if (useful_days <= 0 or daily_revenue <= 0) else
            "net_daily_value<=0 (crop/other-animal opp.cost wins)" if net_daily_value <= 0 else
            "economic_value<=0" if economic_value <= 0 else
            "payback_days>remaining_days"
        ),
    }

def _animal_target_units(project_id: str, ws: WorldState) -> int:
    econ = _animal_net_economics(project_id, ws)
    if econ is None:
        return 0
    animal, unit_cost = econ["animal"], econ["unit_cost"]
    ANIMAL_GATE_LOG.append({"day": ws.day, **econ,
                             "marginal_profit_per_unit": econ["economic_value"]})   
    if not econ["gate_open"]:
        return 0

    discretionary_cash = _discretionary_cash(ws)
    cash_surplus_ratio = discretionary_cash / max(1.0, unit_cost)
    if RL_ANIMAL_CONTROLLER is not None and RL_ANIMAL_CONTROLLER.enabled:
        base_units, _ = RL_ANIMAL_CONTROLLER.get_decision(ws, animal, unit_cost)
    else:
        base_units = ANIMAL_BASE_UNITS_PER_SPECIES
    if RL_ANIMAL_CONTROLLER is not None and RL_ANIMAL_CONTROLLER.enabled_idle:
        idle_cash_start, idle_cash_per_extra_unit = RL_ANIMAL_CONTROLLER.get_idle_cash_params(
            ws, animal, unit_cost)
    else:
        idle_cash_start = ANIMAL_IDLE_CASH_RATIO_START
        idle_cash_per_extra_unit = ANIMAL_IDLE_CASH_RATIO_PER_EXTRA_UNIT
    if cash_surplus_ratio <= idle_cash_start:
        extra_units = 0
    else:
        extra_units = int((cash_surplus_ratio - idle_cash_start) // idle_cash_per_extra_unit)
    return min(ANIMAL_MAX_UNITS_PER_SPECIES_CEILING, base_units + extra_units)

ENABLE_SERVICING_THROTTLE = True  

def _servicing_saturation_ratio(ws: WorldState, discretionary_cash: float,
                                 mandatory_future_cost: float = 0.0,
                                 fa: "FarmAnalysis" = None) -> float:
    servicing_backlog = _estimate_daily_action_backlog(ws, discretionary_cash)["servicing"]
    if servicing_backlog <= 0:
        return 0.0

    current_n = 1 + len(ws.hands)
    physical_cap_n = 1 + _hand_cap_for_quadrant(ws.n_quadrants, ws.day, ws=ws, fa=fa,
                                                 discretionary_cash=discretionary_cash,
                                                 mandatory_future_cost=mandatory_future_cost) * max(1, ws.n_quadrants)
    max_n = min(1 + MAX_HANDS_SEARCH_CEILING, physical_cap_n)

    hours_elapsed_today = ws.turn_in_episode % TURNS_PER_DAY
    hours_remaining_today = max(1, TURNS_PER_DAY - hours_elapsed_today)
    fraction_of_day_left = hours_remaining_today / TURNS_PER_DAY
    throughput_per_worker_today = LAND_UTILIZATION_TILES_PER_DAY * fraction_of_day_left

    hires_today_est = len(ws.hands)
    real_cash_budget = max(0.0, ws.money - mandatory_future_cost)
    best_affordable_n = current_n
    for n in range(current_n, max_n + 1):
        new_hires = n - current_n
        cumulative_cost = sum(_fib_cost(hires_today_est + i) for i in range(new_hires))
        if cumulative_cost <= max(discretionary_cash, real_cash_budget):
            best_affordable_n = n
        else:
            break

    max_servicing_throughput = best_affordable_n * throughput_per_worker_today
    if max_servicing_throughput <= 0:
        return float("inf") if servicing_backlog > 0 else 0.0
    return servicing_backlog / max_servicing_throughput

def _plant_throttle_fraction(saturation_ratio: float, steepness: float = None) -> float:
    if saturation_ratio <= 1.0:
        return 1.0
    steep = steepness if steepness is not None else _PLANT_THROTTLE_STEEPNESS
    return math.exp(-steep * (saturation_ratio - 1.0))

_PLANT_THROTTLE_STEEPNESS = 6.0

def generate_candidates_for_project(project: Project, status: ProjectStatus, ws: WorldState,
                                     fa: FarmAnalysis, discretionary_cash: float,
                                     next_id, capacity_saturated: bool = False,
                                     saturation_ratio: float = 0.0) -> tuple:
    candidates = []
    rejected = []

    _SEASON_GATE_EXEMPT = ("FEED_ANIMAL", "COLLECT_PRODUCT", "SELL_PRODUCT", "PICKUP", "PLACE")
    if not status.season_feasible:
        for step in project.steps:
            if step.action_type in _SEASON_GATE_EXEMPT and ws.remaining_days > 0:
                continue   
            rejected.append(RejectedOpportunity(project.id, step.id, "SEASON_INFEASIBLE"))
        if not any(step.action_type in _SEASON_GATE_EXEMPT for step in project.steps) or ws.remaining_days <= 0:
            return candidates, rejected
        project = Project(id=project.id, steps=tuple(
            s for s in project.steps if s.action_type in _SEASON_GATE_EXEMPT
        ), deadline=project.deadline, min_profitable_horizon=project.min_profitable_horizon)

    for step in project.steps:
        step_status = status.status_of(step.id)

        if step_status.status == "DONE":
            continue  
        if step_status.status == "LOCKED_BY_PREREQUISITE":
            rejected.append(RejectedOpportunity(project.id, step.id, "LOCKED_BY_PREREQUISITE"))
            continue
        if step_status.status == "LOCKED_BY_RESOURCE":
            rejected.append(RejectedOpportunity(project.id, step.id, "LOCKED_BY_RESOURCE"))
            continue

        targets = []   
        if step.action_type == "PLANT":
            if not fa.empty_tiles:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            if RL_FLOORCAP_CONTROLLER is not None and RL_FLOORCAP_CONTROLLER.enabled and RL_FLOORCAP_CONTROLLER.enabled_stage2:
                _throttle_steep = RL_FLOORCAP_CONTROLLER.get_throttle_steepness(
                    ws, fa=fa, discretionary_cash=discretionary_cash)
            else:
                _throttle_steep = None
            plant_allow_fraction = _plant_throttle_fraction(saturation_ratio, steepness=_throttle_steep)
            n_plant_allowed = math.ceil(len(fa.empty_tiles) * plant_allow_fraction)
            if RL_RATE_CONTROLLER is not None and RL_RATE_CONTROLLER.enabled and RL_RATE_CONTROLLER.enabled_plant:
                _, _, _remaining_plant = RL_RATE_CONTROLLER.get_remaining_caps(
                    ws, fa=fa, discretionary_cash=discretionary_cash)
                n_plant_allowed = min(n_plant_allowed, _remaining_plant)
            crop_ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
            best_crop_eval = crop_ranked[0] if crop_ranked else None
            eval_by_crop = {e.crop: e for e in crop_ranked}
            n_animals_total = sum(ws.animal_counts.values())
            wheat_eval = eval_by_crop.get("WHEAT")
            if RL_CROP_MIX_CONTROLLER is not None and RL_CROP_MIX_CONTROLLER.enabled and crop_ranked:
                _fractions = RL_CROP_MIX_CONTROLLER.get_crop_mix(
                    ws, fa=fa, discretionary_cash=discretionary_cash, n_plant_allowed=n_plant_allowed)
                if RL_CROP_MIX_CONTROLLER.training:
                    _fractions = _apply_demand_exploration_floor(_fractions, ws)
                _fractions = _apply_wheat_feed_cap(_fractions, ws, n_plant_allowed)
                tile_counts = _largest_remainder_allocation(_fractions, n_plant_allowed)
            else:
                n_wheat_tiles = min(3, n_plant_allowed) if (n_animals_total > 0 and wheat_eval is not None) else 0
                tile_counts = {"WHEAT": n_wheat_tiles}
                remaining_after_wheat = max(0, n_plant_allowed - n_wheat_tiles)

                
                DIVERSIFICATION_BUDGET_FRACTION = 0.25   
                diversification_budget = min(remaining_after_wheat,
                                              max(0, int(n_plant_allowed * DIVERSIFICATION_BUDGET_FRACTION)))
                if diversification_budget > 0 and best_crop_eval is not None:
                    eligible = [e for e in crop_ranked
                                if e.crop not in ("WHEAT", best_crop_eval.crop)]
                    for e in eligible:
                        if diversification_budget <= 0:
                            break
                        econ = _crop_net_economics(e.crop, ws)
                        if not econ["gate_open"]:
                            continue
                        tile_counts[e.crop] = tile_counts.get(e.crop, 0) + 1
                        diversification_budget -= 1
                        remaining_after_wheat -= 1

                if best_crop_eval is not None:
                    tile_counts[best_crop_eval.crop] = tile_counts.get(best_crop_eval.crop, 0)                         + max(0, remaining_after_wheat)
            crop_assignment = []
            for crop, n in tile_counts.items():
                crop_assignment.extend([crop] * n)
            for i, pos in enumerate(fa.empty_tiles):
                if i >= n_plant_allowed:
                    rejected.append(RejectedOpportunity(project.id, step.id, "SERVICING_THROTTLED"))
                    continue
                assigned_crop = crop_assignment[i] if i < len(crop_assignment) else (
                    best_crop_eval.crop if best_crop_eval is not None else None)
                chosen_eval = eval_by_crop.get(assigned_crop) if assigned_crop else None
                if chosen_eval is None:
                    targets.append((pos, step.cost, 0.0, {}))
                    continue
                crop = chosen_eval.crop
                info = CROP_INFO[crop]
                seed_cost = info["seed_cost"]
                price = ws.prices.get(crop, info["base_price"])
                revenue = price * info.get("max_yield", 1)
                targets.append((pos, seed_cost, revenue, {
                    "crop": crop,
                    "profit_per_day": chosen_eval.profit_per_day,
                    "net_advantage": chosen_eval.net_advantage,
                }))
        elif step.action_type == "HARVEST":
            if not fa.ready_harvest_tiles:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            for pos, crop in fa.ready_harvest_tiles:
                info = CROP_INFO.get(crop, {})
                revenue_proxy = ws.prices.get(crop, info.get("base_price", 0.0)) * info.get("max_yield", 1)
                targets.append((pos, step.cost, revenue_proxy, {"crop": crop}))
        elif step.action_type == "WATER":
            if not fa.need_water_tiles:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            for pos, crop in fa.need_water_tiles:
                targets.append((pos, step.cost, 0.0, {"crop": crop}))
        elif step.action_type == "COLLECT_PRODUCT":
            if not fa.product_ready_tiles:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            for entry in fa.product_ready_tiles:
                pos = entry[0]
                targets.append((pos, step.cost, 0.0, {}))
        elif step.action_type == "SELL_PRODUCT":
            products_in_shed = [p for p in ws.shed if p in MARKET_PARAMS and ws.shed.get(p, 0) > 0]
            if not products_in_shed:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_INVENTORY_TO_SELL"))
                continue
            has_animals = ws.n_coop > 0 or ws.n_pasture > 0
            for product in products_in_shed:
                qty = ws.shed.get(product, 1)
                if product == "WHEAT" and has_animals:
                    qty = max(0, qty - FEED_WHEAT_SELL_RESERVE)
                    if qty <= 0:
                        continue
                if product == "FERTILIZER":
                    qty = max(0, qty - FERTILIZER_SELL_RESERVE)
                    if qty <= 0:
                        continue
                revenue = ws.prices.get(product, 0.0) * max(1, qty)
                targets.append((product, step.cost, revenue, {}))
        elif step.action_type == "FEED_ANIMAL":
            my_animal = PROJECT_ANIMAL.get(project.id)
            my_hungry_tiles = [(pos, at, cu) for pos, at, cu in fa.hungry_animal_tiles if at == my_animal]
            wheat_holders = [wi for wi, inv in enumerate(ws.all_inventories) if inv.get("WHEAT", 0) > 0]
            if not my_hungry_tiles or not wheat_holders:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            worker_positions = (ws.farmer,) + ws.hands
            for pos, animal_type, consecutive_unfed in my_hungry_tiles:
                wi = min(wheat_holders,
                         key=lambda w: abs((worker_positions[w] if w < len(worker_positions) else ws.farmer)[0] - pos[0])
                         + abs((worker_positions[w] if w < len(worker_positions) else ws.farmer)[1] - pos[1]))
                targets.append((pos, step.cost, 0.0,
                                 {"animal_type": animal_type, "required_worker_index": wi,
                                  "consecutive_unfed": consecutive_unfed}))
        elif step.action_type == "BUY_ANIMAL":
            animal = PROJECT_ANIMAL.get(project.id)
            needed_structure_kind = STRUCTURE_FOR_ANIMAL.get(animal)
            structure_count = ws.n_coop if needed_structure_kind == "COOP" else ws.n_pasture

            co_tenant_species = [name for name, info in ANIMAL_INFO.items()
                                  if info.get("structure") == needed_structure_kind]
            occupied_by_all = 0
            for sp in co_tenant_species:
                sp_held_in_workers = sum(inv.get(sp, 0) for inv in ws.all_inventories)
                sp_held = ws.shed.get(sp, 0) + sp_held_in_workers
                sp_on_tile = sum(1 for row in ws.tiles for t in row
                                  if isinstance(t, dict) and t.get("animal") == sp)
                occupied_by_all += sp_held + sp_on_tile
            held_in_workers = sum(inv.get(animal, 0) for inv in ws.all_inventories) if animal else 0
            held = (ws.shed.get(animal, 0) if animal else 0) + held_in_workers
            on_tile = sum(1 for row in ws.tiles for t in row
                          if isinstance(t, dict) and t.get("animal") == animal)
            free_slots = structure_count - occupied_by_all
            if animal is None or free_slots <= 0:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                ANIMAL_CANDIDATE_LOG.append({"day": ws.day, "animal": animal, "project_id": project.id,
                                              "structure_count": structure_count, "held": held, "on_tile": on_tile,
                                              "occupied_by_all": occupied_by_all, "free_slots": free_slots,
                                              "reject_reason": "NO_TARGET_AVAILABLE (no free structure slot)"})
                continue
            if capacity_saturated:
                rejected.append(RejectedOpportunity(project.id, step.id, "WORKFORCE_SATURATED"))
                ANIMAL_CANDIDATE_LOG.append({"day": ws.day, "animal": animal, "project_id": project.id,
                                              "structure_count": structure_count, "held": held, "on_tile": on_tile, "free_slots": free_slots,
                                              "reject_reason": "WORKFORCE_SATURATED (capacity_saturated hard block)"})
                continue
            if RL_RATE_CONTROLLER is not None and RL_RATE_CONTROLLER.enabled and RL_RATE_CONTROLLER.enabled_animal:
                _, _remaining_animal, _ = RL_RATE_CONTROLLER.get_remaining_caps(
                    ws, fa=fa, discretionary_cash=discretionary_cash)
                if _remaining_animal <= 0:
                    rejected.append(RejectedOpportunity(project.id, step.id, "RATE_CAPPED"))
                    ANIMAL_CANDIDATE_LOG.append({"day": ws.day, "animal": animal, "project_id": project.id,
                                                  "structure_count": structure_count, "held": held, "on_tile": on_tile, "free_slots": free_slots,
                                                  "reject_reason": "RATE_CAPPED"})
                    continue
            revenue = _project_milestone_revenue_proxy(project.id, ws)
            targets.append((None, step.cost, revenue, {}))
            ANIMAL_CANDIDATE_LOG.append({"day": ws.day, "animal": animal, "project_id": project.id,
                                          "structure_count": structure_count, "held": held, "on_tile": on_tile, "free_slots": free_slots,
                                          "reject_reason": "CANDIDATE_EMITTED"})
        elif step.action_type == "PICKUP":
            animal = PROJECT_ANIMAL.get(project.id)
            if animal is None or ws.shed.get(animal, 0) <= 0:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            pos = nearest_target(ws.farmer, list(SHED_ACCESS_TILES)) or SHED_ACCESS_TILES[0]
            targets.append((pos, step.cost, 0.0, {"animal_type": animal}))
        elif step.action_type == "PLACE":
            animal = PROJECT_ANIMAL.get(project.id)
            needed_structure = STRUCTURE_FOR_ANIMAL.get(animal)
            workers_holding = [wi for wi, inv in enumerate(ws.all_inventories)
                                if animal and inv.get(animal, 0) > 0]
            if animal is None or not workers_holding:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            matching_tiles = [pos for pos, kind in fa.empty_animal_structure_tiles if kind == needed_structure]
            if not matching_tiles:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            worker_positions = (ws.farmer,) + ws.hands
            used_tiles = set()
            for wi in workers_holding:
                remaining_tiles = [t for t in matching_tiles if t not in used_tiles] or matching_tiles
                w_pos = worker_positions[wi] if wi < len(worker_positions) else ws.farmer
                pos = nearest_target(w_pos, remaining_tiles)
                used_tiles.add(pos)
                targets.append((pos, step.cost, 0.0, {"animal_type": animal, "required_worker_index": wi}))
        elif step.action_type == "BUILD_STRUCTURE":
            if not fa.empty_tiles:
                rejected.append(RejectedOpportunity(project.id, step.id, "NO_TARGET_AVAILABLE"))
                continue
            if RL_RATE_CONTROLLER is not None and RL_RATE_CONTROLLER.enabled:
                _remaining_structure, _, _ = RL_RATE_CONTROLLER.get_remaining_caps(
                    ws, fa=fa, discretionary_cash=discretionary_cash)
                if _remaining_structure <= 0:
                    rejected.append(RejectedOpportunity(project.id, step.id, "RATE_CAPPED"))
                    continue
            pos = fa.empty_tiles[0]
            revenue = _project_milestone_revenue_proxy(project.id, ws)
            targets.append((pos, step.cost, revenue, {}))
        else:
            targets.append((None, step.cost, 0.0, {}))

        for target, cost, expected_revenue, meta in targets:
            status_label = _financial_status(cost, discretionary_cash)
            candidates.append(Candidate(
                id=next_id(),
                project_id=project.id,
                step_id=step.id,
                action_type=step.action_type,
                target=target,
                cost=cost,
                expected_revenue=expected_revenue,
                duration=step.duration,
                deadline=project.deadline,
                financial_status=status_label,
                financially_blocked=(status_label == "DEFER"),
                meta=meta,
                required_worker_index=meta.get("required_worker_index"),
            ))

    return candidates, rejected

def _hire_cost_estimate(ws: WorldState) -> float:
    n = len(ws.hands)
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return float(max(1, a))

def _fib_cost(n: int) -> float:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return float(a)

def _estimate_daily_action_backlog(ws: WorldState, discretionary_cash: float = float("inf")) -> dict:
    crop_ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
    cheapest_seed_cost = min((CROP_INFO[e.crop]["seed_cost"] for e in crop_ranked), default=None)
    if cheapest_seed_cost and cheapest_seed_cost > 0 and discretionary_cash != float("inf"):
        affordable_empty_tile_budget = max(0, int(discretionary_cash // cheapest_seed_cost))
    else:
        affordable_empty_tile_budget = None   

    mandatory = 0.0
    servicing = 0.0   
    optional = 0.0
    empty_tile_count = 0
    for row in ws.tiles:
        for t in row:
            if t is None:
                empty_tile_count += 1
                continue
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")
            if kind == "PLANT":
                planted_day = t.get("planted_day")
                crop = t.get("crop")
                info = CROP_INFO.get(crop, {})
                maturity_day = info.get("max_yield_day")
                is_mature = (planted_day is not None and maturity_day is not None
                             and ws.day - planted_day >= maturity_day)
                if is_mature:
                    mandatory += 1.0   
                    servicing += 1.0
                elif not t.get("watered_today"):
                    mandatory += 1.0  
                    servicing += 1.0
            elif kind in ("COOP", "PASTURE") and t.get("animal"):
                if not t.get("fed_today"):
                    mandatory += 1.0   
                    servicing += 1.0
                if not t.get("cared_today"):
                    optional += 1.0   
                if t.get("yield_units", 0) > 0:
                    mandatory += 1.0  
                    servicing += 1.0

    if affordable_empty_tile_budget is None:
        mandatory += empty_tile_count
    else:
        mandatory += min(empty_tile_count, affordable_empty_tile_budget)
    return {"mandatory": mandatory, "optional": optional, "servicing": servicing}

LAND_FLOOR_HANDS_PER_TILE = 0.30

def _land_scaled_floor(ws: WorldState, mult: float = None, fa: "FarmAnalysis" = None,
                        discretionary_cash: float = None, mandatory_future_cost: float = None) -> int:
    if mult is None:
        if RL_FLOORCAP_CONTROLLER is not None and RL_FLOORCAP_CONTROLLER.enabled:
            mult = RL_FLOORCAP_CONTROLLER.get_floor_mult(ws, fa=fa, discretionary_cash=discretionary_cash,
                                                  mandatory_future_cost=mandatory_future_cost)
        else:
            mult = LAND_FLOOR_HANDS_PER_TILE   
    owned = 0
    for row in ws.tiles:
        for t in row:
            if t != "LOCKED":
                owned += 1
    return max(1, math.ceil(owned * mult))

def compute_optimal_workforce(ws: WorldState, fa: FarmAnalysis, discretionary_cash: float,
                               mandatory_future_cost: float = 0.0) -> dict:
    current_n = 1 + len(ws.hands)
    hires_today_est = len(ws.hands)   
    physical_cap_n = 1 + _hand_cap_for_quadrant(ws.n_quadrants, ws.day, ws=ws, fa=fa,
                                                 discretionary_cash=discretionary_cash,
                                                 mandatory_future_cost=mandatory_future_cost) * max(1, ws.n_quadrants)
    max_n = min(1 + MAX_HANDS_SEARCH_CEILING, physical_cap_n)

    backlog_split = _estimate_daily_action_backlog(ws, discretionary_cash)
    backlog = backlog_split["mandatory"]
    optional_backlog = backlog_split["optional"]

    hours_elapsed_today = ws.turn_in_episode % TURNS_PER_DAY
    hours_remaining_today = max(1, TURNS_PER_DAY - hours_elapsed_today)
    fraction_of_day_left = hours_remaining_today / TURNS_PER_DAY

    crop_ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
    value_per_task = max(0.0, crop_ranked[0].profit_per_day) if crop_ranked else 0.0
    throughput_per_worker_today = LAND_UTILIZATION_TILES_PER_DAY * fraction_of_day_left

    if backlog <= 0:
        return {"target_n": current_n, "backlog": 0, "table": (),
                "reason": "NO_BACKLOG"}

    table = []
    feasible_n = None   
    best_coverage_n, best_coverage = current_n, -1.0   
    if RL_FLOORCAP_CONTROLLER is not None and RL_FLOORCAP_CONTROLLER.enabled and RL_FLOORCAP_CONTROLLER.enabled_stage2:
        COVERAGE_SAFETY_MARGIN = RL_FLOORCAP_CONTROLLER.get_coverage_margin(
            ws, fa=fa, discretionary_cash=discretionary_cash, mandatory_future_cost=mandatory_future_cost)
    else:
        COVERAGE_SAFETY_MARGIN = 1.15
    floor_n = min(1 + _land_scaled_floor(ws, fa=fa, discretionary_cash=discretionary_cash,
                                          mandatory_future_cost=mandatory_future_cost), max_n)
    real_cash_budget = max(0.0, ws.money - mandatory_future_cost)

    growth_backlog = backlog + optional_backlog

    for n in range(current_n, max_n + 1):
        new_hires = n - current_n
        cumulative_cost = sum(_fib_cost(hires_today_est + i) for i in range(new_hires))
        affordable = cumulative_cost <= discretionary_cash
        if not affordable and n <= floor_n:
            affordable = cumulative_cost <= real_cash_budget
        raw_throughput = n * throughput_per_worker_today   
        tasks_covered = min(float(backlog), raw_throughput)
        coverage_ratio = tasks_covered / backlog
        growth_tasks_covered = min(float(growth_backlog), raw_throughput)
        net = growth_tasks_covered * value_per_task - cumulative_cost
        table.append({"n": n, "cumulative_cost": cumulative_cost,
                       "coverage_ratio": coverage_ratio, "net": net, "affordable": affordable})
        if not affordable:
            break
        if coverage_ratio > best_coverage:
            best_coverage = coverage_ratio
            best_coverage_n = n
        if raw_throughput >= backlog * COVERAGE_SAFETY_MARGIN and feasible_n is None:
            feasible_n = n

    if feasible_n is None:
        best_n = best_coverage_n
    else:
        best_n = feasible_n
        for row in table:
            if row["n"] <= feasible_n or not row["affordable"]:
                continue
            prev_net = table[row["n"] - current_n - 1]["net"]
            if row["net"] > prev_net:
                best_n = row["n"]
            else:
                break

    return {"target_n": best_n, "backlog": backlog, "optional_backlog": optional_backlog, "table": tuple(table)}

def _hire_batch_cap(ws: WorldState, fa: "FarmAnalysis" = None, discretionary_cash: float = None,
                     mandatory_future_cost: float = None) -> int:
    if RL_FLOORCAP_CONTROLLER is not None and RL_FLOORCAP_CONTROLLER.enabled and RL_FLOORCAP_CONTROLLER.enabled_stage2:
        return RL_FLOORCAP_CONTROLLER.get_hire_batch_cap(ws, fa=fa, discretionary_cash=discretionary_cash,
                                                          mandatory_future_cost=mandatory_future_cost)
    return 1

def generate_hire_candidates(ws: WorldState, fa: FarmAnalysis, discretionary_cash: float, next_id,
                              mandatory_future_cost: float = 0.0) -> tuple:
    candidates = []
    rejected = []
    n_workers = 1 + len(ws.hands)
    hires_today_est = len(ws.hands)   

    if len(ws.hands) >= _hand_cap_for_quadrant(ws.n_quadrants, ws.day, ws=ws, fa=fa,
                                                discretionary_cash=discretionary_cash,
                                                mandatory_future_cost=mandatory_future_cost) * max(1, ws.n_quadrants):
        rejected.append(RejectedOpportunity("HIRE", "HIRE", "CAPACITY_FULL"))
        return candidates, rejected

    plan = compute_optimal_workforce(ws, fa, discretionary_cash, mandatory_future_cost)
    target_n = plan["target_n"]

    if n_workers >= target_n:
        rejected.append(RejectedOpportunity(
            "HIRE", "HIRE",
            "NO_BACKLOG" if plan.get("reason") == "NO_BACKLOG" else "TARGET_WORKFORCE_REACHED"))
        return candidates, rejected

    gap = target_n - n_workers
    batch_n = min(gap, _hire_batch_cap(ws, fa=fa, discretionary_cash=discretionary_cash,
                                        mandatory_future_cost=mandatory_future_cost))

    crop_ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
    best_profit_per_day = crop_ranked[0].profit_per_day if crop_ranked else 0.0
    hours_elapsed_today = ws.turn_in_episode % TURNS_PER_DAY
    hours_remaining_today = max(1, TURNS_PER_DAY - hours_elapsed_today)
    fraction_of_day_left = hours_remaining_today / TURNS_PER_DAY

    floor_n = 1 + _land_scaled_floor(ws, fa=fa, discretionary_cash=discretionary_cash,
                                      mandatory_future_cost=mandatory_future_cost)
    is_bootstrap_situation = (n_workers <= floor_n)

    remaining_backlog = float(plan["backlog"])
    cumulative_batch_cost = 0.0
    for i in range(batch_n):
        cost = _fib_cost(hires_today_est + i)   
        fillable_by_this_worker = min(LAND_UTILIZATION_TILES_PER_DAY * fraction_of_day_left,
                                       remaining_backlog)
        expected_value_today = max(0.0, best_profit_per_day) * fillable_by_this_worker
        remaining_backlog = max(0.0, remaining_backlog - fillable_by_this_worker)

        cumulative_batch_cost += cost
        is_bootstrap = is_bootstrap_situation and (n_workers + i) <= floor_n
        if is_bootstrap:
            bootstrap_cash = max(0.0, ws.money - mandatory_future_cost)
            status_label = _financial_status(cumulative_batch_cost, bootstrap_cash)
        else:
            status_label = _financial_status(cumulative_batch_cost, discretionary_cash)
        candidates.append(Candidate(
            id=next_id(),
            project_id="HIRE",
            step_id="HIRE",
            action_type="HIRE",
            target=None,
            cost=cost,
            expected_revenue=expected_value_today,
            duration=1,
            deadline=None,
            financial_status=status_label,
            financially_blocked=(status_label == "DEFER"),
            meta={"expected_value_today": expected_value_today, "target_n": target_n,
                  "backlog": plan["backlog"], "batch_index": i, "batch_n": batch_n,
                  "bootstrap_hire": is_bootstrap},
        ))
    return candidates, rejected

WEED_HIGH_PRIORITY_MULTIPLIER = 1.3

def generate_dig_candidates(ws: WorldState, fa: FarmAnalysis, next_id) -> tuple:
    candidates = []
    rejected = []

    if not fa.weed_tiles_high and not fa.weed_tiles_low:
        rejected.append(RejectedOpportunity("WEED_CLEANUP", "DIG", "NO_TARGET_AVAILABLE"))
        return candidates, rejected

    crop_ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
    if crop_ranked:
        best_crop = crop_ranked[0].crop
        info = CROP_INFO[best_crop]
        price = ws.prices.get(best_crop, info["base_price"])
        base_reclaim_value = max(0.0, price * info.get("max_yield", 1) - info["seed_cost"])
    else:
        base_reclaim_value = 0.0

    for pos in fa.weed_tiles_high:
        candidates.append(Candidate(
            id=next_id(), project_id="WEED_CLEANUP", step_id="DIG", action_type="DIG",
            target=pos, cost=0.0, expected_revenue=base_reclaim_value * WEED_HIGH_PRIORITY_MULTIPLIER,
            duration=1, deadline=None,
            financial_status="AFFORDABLE", financially_blocked=False,
            meta={"priority": "HIGH"},
        ))
    for pos in fa.weed_tiles_low:
        candidates.append(Candidate(
            id=next_id(), project_id="WEED_CLEANUP", step_id="DIG", action_type="DIG",
            target=pos, cost=0.0, expected_revenue=base_reclaim_value,
            duration=1, deadline=None,
            financial_status="AFFORDABLE", financially_blocked=False,
            meta={"priority": "LOW"},
        ))
    return candidates, rejected

LAND_COST_BY_OWNED_QUADRANTS = {1: 1000.0, 2: 2000.0, 3: 4000.0}

MAX_QUADRANTS = 4

LAND_UTILIZATION_TILES_PER_DAY = 2.0

def generate_buy_land_candidates(ws: WorldState, fa: FarmAnalysis, discretionary_cash: float, next_id) -> tuple:
    candidates = []
    rejected = []

    if ws.n_quadrants >= MAX_QUADRANTS:
        rejected.append(RejectedOpportunity("LAND_EXPANSION", "BUY_LAND", "CAPACITY_FULL"))
        return candidates, rejected

    cost = LAND_COST_BY_OWNED_QUADRANTS[ws.n_quadrants]
    crop_ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
    best_profit_per_day = crop_ranked[0].profit_per_day if crop_ranked else 0.0

    total_owned_tiles = TILES_PER_QUADRANT * ws.n_quadrants
    free_tiles = len(fa.empty_tiles)   
    occupied_fraction = 1.0 - (free_tiles / max(1, total_owned_tiles))

    if RL_FLOORCAP_CONTROLLER is not None and RL_FLOORCAP_CONTROLLER.enabled and RL_FLOORCAP_CONTROLLER.enabled_stage2:
        UTILIZATION_GATE_THRESHOLD = RL_FLOORCAP_CONTROLLER.get_utilization_threshold(
            ws, fa=fa, discretionary_cash=discretionary_cash)
        UTILIZATION_GATE_EXPONENT = RL_FLOORCAP_CONTROLLER.get_utilization_exponent(
            ws, fa=fa, discretionary_cash=discretionary_cash)
        UTILIZATION_GATE_FLOOR = RL_FLOORCAP_CONTROLLER.get_utilization_floor(
            ws, fa=fa, discretionary_cash=discretionary_cash)
    else:
        UTILIZATION_GATE_THRESHOLD = 0.55
        UTILIZATION_GATE_EXPONENT = 3.0
        UTILIZATION_GATE_FLOOR = 0.05
    if occupied_fraction >= UTILIZATION_GATE_THRESHOLD:
        utilization_factor = 1.0
    else:
        utilization_factor = max(UTILIZATION_GATE_FLOOR,
                                  (occupied_fraction / UTILIZATION_GATE_THRESHOLD) ** UTILIZATION_GATE_EXPONENT)

    if RL_FLOORCAP_CONTROLLER is not None and RL_FLOORCAP_CONTROLLER.enabled and RL_FLOORCAP_CONTROLLER.enabled_stage2:
        IDLE_CASH_RATIO_START = RL_FLOORCAP_CONTROLLER.get_idle_cash_start(
            ws, fa=fa, discretionary_cash=discretionary_cash)
        IDLE_CASH_RATIO_FULL = RL_FLOORCAP_CONTROLLER.get_idle_cash_full(
            ws, fa=fa, discretionary_cash=discretionary_cash)
    else:
        IDLE_CASH_RATIO_START = 2.0    
        IDLE_CASH_RATIO_FULL = 8.0     
    cash_surplus_ratio = discretionary_cash / max(1.0, cost)
    if cash_surplus_ratio <= IDLE_CASH_RATIO_START:
        idle_cash_relief = 0.0
    else:
        idle_cash_relief = min(
            1.0,
            (cash_surplus_ratio - IDLE_CASH_RATIO_START)
            / (IDLE_CASH_RATIO_FULL - IDLE_CASH_RATIO_START),
        )
    utilization_factor = max(utilization_factor, idle_cash_relief)

    daily_value_proxy = max(0.0, best_profit_per_day) * LAND_UTILIZATION_TILES_PER_DAY * utilization_factor
    expected_revenue = daily_value_proxy * max(0, ws.remaining_days)

    status_label = _financial_status(cost, discretionary_cash)
    candidates.append(Candidate(
        id=next_id(), project_id="LAND_EXPANSION", step_id="BUY_LAND", action_type="BUY_LAND",
        target=None, cost=cost, expected_revenue=expected_revenue, duration=1, deadline=None,
        financial_status=status_label, financially_blocked=(status_label == "DEFER"),
        meta={"daily_value_proxy": daily_value_proxy, "utilization_factor": utilization_factor},
    ))
    return candidates, rejected

from collections import deque as _deque_diag_log
def generate_feed_stock_candidates(ws: WorldState, fa: FarmAnalysis, discretionary_cash: float, next_id) -> tuple:
    candidates = []
    rejected = []

    held_wheat_total = ws.farmer_inventory.get("WHEAT", 0) if not ws.all_inventories else \
        sum(inv.get("WHEAT", 0) for inv in ws.all_inventories)
    any_worker_holds_wheat = held_wheat_total > 0 if ws.all_inventories else ws.farmer_inventory.get("WHEAT", 0) > 0
    n_hungry = len(fa.hungry_animal_tiles)

    reserve_needed = max(n_hungry * 5, 3) if (ws.n_coop > 0 or ws.n_pasture > 0) else 0
    stock_available = ws.shed.get("WHEAT", 0) + held_wheat_total

    if reserve_needed > 0 and stock_available < reserve_needed:
        price = ws.prices.get("WHEAT", CROP_INFO["WHEAT"]["base_price"])
        protected_revenue = 0.0
        for anim, cnt in ws.animal_counts.items():
            info = ANIMAL_INFO.get(anim)
            if not info or cnt <= 0:
                continue
            daily_rev = ws.prices.get(info["product"], info["base_price"]) * (1.0 / max(1, info["interval"]))
            protected_revenue += daily_rev * cnt * max(0, ws.remaining_days)
        status_label = _financial_status(price, discretionary_cash)
        candidates.append(Candidate(
            id=next_id(), project_id="FEED_STOCK", step_id="BUY_FEED_WHEAT", action_type="BUY_FEED_WHEAT",
            target=None, cost=price, expected_revenue=protected_revenue, duration=1, deadline=None,
            financial_status=status_label, financially_blocked=(status_label == "DEFER"),
            meta={"protected_revenue": protected_revenue},
        ))
    else:
        rejected.append(RejectedOpportunity("FEED_STOCK", "BUY_FEED_WHEAT", "RESERVE_ALREADY_SUFFICIENT"))

    if ws.shed.get("WHEAT", 0) > 0 and held_wheat_total < reserve_needed:
        pos = nearest_target(ws.farmer, list(SHED_ACCESS_TILES)) or SHED_ACCESS_TILES[0]
        candidates.append(Candidate(
            id=next_id(), project_id="FEED_STOCK", step_id="PICKUP_FEED_WHEAT", action_type="PICKUP_FEED_WHEAT",
            target=pos, cost=0.0, expected_revenue=0.0, duration=1, deadline=None,
            financial_status="OK", financially_blocked=False, meta={},
        ))
    else:
        rejected.append(RejectedOpportunity("FEED_STOCK", "PICKUP_FEED_WHEAT", "NO_TARGET_AVAILABLE"))

    return candidates, rejected

def generate_care_bonus_candidates(ws: WorldState, fa: FarmAnalysis, next_id) -> tuple:
    candidates = []
    rejected = []
    if not fa.cared_animal_tiles:
        rejected.append(RejectedOpportunity("CARE_BONUS", "CARE_BONUS", "NO_TARGET_AVAILABLE"))
        return candidates, rejected
    for pos, animal_type in fa.cared_animal_tiles:
        info = ANIMAL_INFO.get(animal_type, {})
        product = info.get("product")
        value_proxy = 0.25 * ws.prices.get(product, info.get("base_price", 0.0)) if product else 1.0
        candidates.append(Candidate(
            id=next_id(), project_id="CARE_BONUS", step_id="CARE_BONUS", action_type="CARE_BONUS",
            target=pos, cost=0.0, expected_revenue=value_proxy, duration=1, deadline=None,
            financial_status="AFFORDABLE", financially_blocked=False,
            meta={"animal_type": animal_type},
        ))
    return candidates, rejected

def generate_fertilizer_candidates(ws: WorldState, fa: FarmAnalysis, discretionary_cash: float, next_id) -> tuple:
    candidates = []
    rejected = []

    if fa.fertilizer_ready_tiles:
        for pos, animal_type in fa.fertilizer_ready_tiles:
            candidates.append(Candidate(
                id=next_id(), project_id="FERTILIZER_CYCLE", step_id="COLLECT_FERTILIZER",
                action_type="COLLECT_FERTILIZER", target=pos, cost=0.0,
                expected_revenue=0.5 * ws.prices.get("FERTILIZER", CROP_INFO.get("WHEAT", {}).get("base_price", 25.0)),
                duration=1, deadline=None, financial_status="AFFORDABLE", financially_blocked=False,
                meta={"animal_type": animal_type},
            ))
    else:
        rejected.append(RejectedOpportunity("FERTILIZER_CYCLE", "COLLECT_FERTILIZER", "NO_TARGET_AVAILABLE"))

    held_fertilizer_total = sum(inv.get("FERTILIZER", 0) for inv in ws.all_inventories) if ws.all_inventories \
        else ws.farmer_inventory.get("FERTILIZER", 0)
    fertilizer_holders = [wi for wi, inv in enumerate(ws.all_inventories) if inv.get("FERTILIZER", 0) > 0]

    if fa.fertilizable_crop_tiles and fertilizer_holders:
        worker_positions = (ws.farmer,) + ws.hands
        for pos, crop in fa.fertilizable_crop_tiles:
            wi = min(fertilizer_holders,
                     key=lambda w: abs((worker_positions[w] if w < len(worker_positions) else ws.farmer)[0] - pos[0])
                     + abs((worker_positions[w] if w < len(worker_positions) else ws.farmer)[1] - pos[1]))
            info = CROP_INFO.get(crop, {})
            price = ws.prices.get(crop, info.get("base_price", 0.0))
            value_proxy = price * 1.0
            candidates.append(Candidate(
                id=next_id(), project_id="FERTILIZER_CYCLE", step_id="FERTILIZE",
                action_type="FERTILIZE", target=pos, cost=0.0, expected_revenue=value_proxy,
                duration=1, deadline=None, financial_status="AFFORDABLE", financially_blocked=False,
                meta={"crop": crop, "required_worker_index": wi}, required_worker_index=wi,
            ))
    elif fa.fertilizable_crop_tiles and not fertilizer_holders:
        rejected.append(RejectedOpportunity("FERTILIZER_CYCLE", "FERTILIZE", "NO_TARGET_AVAILABLE"))

    if RL_REORDER_CONTROLLER is not None and RL_REORDER_CONTROLLER.enabled:
        reserve_needed = RL_REORDER_CONTROLLER.get_fertilizer_reserve_target(
            ws, fa=fa, discretionary_cash=discretionary_cash)
    else:
        reserve_needed = min(3, len(fa.fertilizable_crop_tiles))
    stock_available = ws.shed.get("FERTILIZER", 0) + held_fertilizer_total
    n_animal_tiles = sum(1 for row in ws.tiles for t in row
                          if isinstance(t, dict) and "animal" in t)
    expected_daily_fertilizer_supply = n_animal_tiles
    if reserve_needed > 0 and (stock_available + expected_daily_fertilizer_supply) < reserve_needed:
        price = ws.prices.get("FERTILIZER", 100.0)
        status_label = _financial_status(price, discretionary_cash)
        fertilizable_prices = [ws.prices.get(crop, CROP_INFO.get(crop, {}).get("base_price", 0.0))
                                for _, crop in fa.fertilizable_crop_tiles]
        if fertilizable_prices:
            representative_value = sum(fertilizable_prices) / len(fertilizable_prices)
        else:
            representative_value = ws.prices.get("WHEAT", CROP_INFO.get("WHEAT", {}).get("base_price", 25.0))
        candidates.append(Candidate(
            id=next_id(), project_id="FERTILIZER_CYCLE", step_id="BUY_FERTILIZER",
            action_type="BUY_FERTILIZER", target=None, cost=price, expected_revenue=representative_value,
            duration=1, deadline=None, financial_status=status_label,
            financially_blocked=(status_label == "DEFER"), meta={"representative_value": representative_value,
                                                                    "expected_daily_fertilizer_supply": expected_daily_fertilizer_supply},
        ))
    else:
        rejected.append(RejectedOpportunity("FERTILIZER_CYCLE", "BUY_FERTILIZER", "RESERVE_ALREADY_SUFFICIENT"))

    if ws.shed.get("FERTILIZER", 0) > 0 and held_fertilizer_total < reserve_needed:
        pos = nearest_target(ws.farmer, list(SHED_ACCESS_TILES)) or SHED_ACCESS_TILES[0]
        candidates.append(Candidate(
            id=next_id(), project_id="FERTILIZER_CYCLE", step_id="PICKUP_FERTILIZER",
            action_type="PICKUP_FERTILIZER", target=pos, cost=0.0,
            expected_revenue=0.25 * ws.prices.get("FERTILIZER", 100.0),
            duration=1, deadline=None, financial_status="AFFORDABLE", financially_blocked=False,
            meta={},
        ))
    else:
        rejected.append(RejectedOpportunity("FERTILIZER_CYCLE", "PICKUP_FERTILIZER", "NO_TARGET_AVAILABLE"))

    return candidates, rejected

def generate_drop_candidates(ws: WorldState, fa: FarmAnalysis, next_id) -> tuple:
    """OPTIONAL (not mandatory) candidate: move a worker's held inventory into the
    shed so it can be sold same-day, instead of sitting idle until the engine's
    end-of-day auto-flush (_drop_inventories_to_shed). Ground truth from the env
"""
    candidates = []
    rejected = []
    if not ws.all_inventories:
        rejected.append(RejectedOpportunity("DROP_INVENTORY", "DROP", "NO_TARGET_AVAILABLE"))
        return candidates, rejected

    worker_positions = (ws.farmer,) + ws.hands
    any_eligible = False
    for wi, inv in enumerate(ws.all_inventories):
        eligible = {item: qty for item, qty in inv.items()
                    if item not in ("WHEAT", "FERTILIZER") and qty > 0}
        if not eligible:
            continue
        any_eligible = True
        pos = worker_positions[wi] if wi < len(worker_positions) else ws.farmer
        drop_pos = nearest_target(pos, list(SHED_ACCESS_TILES)) or SHED_ACCESS_TILES[0]
        value_proxy = 0.1 * sum(
            qty * ws.prices.get(item, CROP_INFO.get(item, ANIMAL_INFO.get(item, {})).get("base_price", 0.0))
            for item, qty in eligible.items()
        )
        candidates.append(Candidate(
            id=next_id(), project_id="DROP_INVENTORY", step_id="DROP", action_type="DROP",
            target=drop_pos, cost=0.0, expected_revenue=value_proxy, duration=1, deadline=None,
            financial_status="AFFORDABLE", financially_blocked=False,
            meta={"held_items": eligible, "required_worker_index": wi}, required_worker_index=wi,
        ))
    if not any_eligible:
        rejected.append(RejectedOpportunity("DROP_INVENTORY", "DROP", "NO_TARGET_AVAILABLE"))
    return candidates, rejected

def generate_candidates(ws: WorldState, fa: FarmAnalysis, memory: dict,
                         mandatory_future_cost: float = 0.0) -> CandidateBatch:
    project_statuses = evaluate_all_projects(ws, memory)
    discretionary_cash = _discretionary_cash(ws, mandatory_future_cost)

    if ENABLE_SERVICING_THROTTLE:
        saturation_ratio = _servicing_saturation_ratio(ws, discretionary_cash, mandatory_future_cost, fa=fa)
        capacity_saturated = saturation_ratio > 1.0
    else:
        saturation_ratio = 0.0
        capacity_saturated = False

    counter = {"n": 0}

    def next_id():
        counter["n"] += 1
        return f"C{counter['n']:04d}"

    all_candidates = []
    all_rejected = []
    for pid, project in PROJECT_REGISTRY.items():
        if pid == "SHEEP_ECONOMY" and ws.n_quadrants <= 3:
            continue
        status = project_statuses[pid]
        cands, rej = generate_candidates_for_project(project, status, ws, fa, discretionary_cash, next_id,
                                                       capacity_saturated=capacity_saturated,
                                                       saturation_ratio=saturation_ratio)
        all_candidates.extend(cands)
        all_rejected.extend(rej)

    hire_cands, hire_rej = generate_hire_candidates(ws, fa, discretionary_cash, next_id, mandatory_future_cost)
    all_candidates.extend(hire_cands)
    all_rejected.extend(hire_rej)

    dig_cands, dig_rej = generate_dig_candidates(ws, fa, next_id)
    all_candidates.extend(dig_cands)
    all_rejected.extend(dig_rej)

    land_cands, land_rej = generate_buy_land_candidates(ws, fa, discretionary_cash, next_id)
    all_candidates.extend(land_cands)
    all_rejected.extend(land_rej)

    feed_cands, feed_rej = generate_feed_stock_candidates(ws, fa, discretionary_cash, next_id)
    all_candidates.extend(feed_cands)
    all_rejected.extend(feed_rej)

    care_cands, care_rej = generate_care_bonus_candidates(ws, fa, next_id)
    all_candidates.extend(care_cands)
    all_rejected.extend(care_rej)

    fert_cands, fert_rej = generate_fertilizer_candidates(ws, fa, discretionary_cash, next_id)
    all_candidates.extend(fert_cands)
    all_rejected.extend(fert_rej)

    drop_cands, drop_rej = generate_drop_candidates(ws, fa, next_id)
    all_candidates.extend(drop_cands)
    all_rejected.extend(drop_rej)

    return CandidateBatch(candidates=tuple(all_candidates), rejected=tuple(all_rejected))

@dataclass(frozen=True)
class InvestmentEvaluation:
    candidate_id: str
    cost: float
    expected_revenue: float
    expected_operating_cost: float

    expected_profit: float
    payback_days: float

    capital_efficiency: float     
    time_efficiency: float        
    risk: float                   

    accept: bool                  

def _effective_opex_per_task(ws: WorldState) -> float:
    marginal_hire_cost = _hire_cost_estimate(ws)
    opex_per_task = marginal_hire_cost / max(1.0, LAND_UTILIZATION_TILES_PER_DAY)
    return max(LABOR_COST_PER_TASK, opex_per_task)

def _step_operating_cost(step: ProjectStep, ws: Optional[WorldState] = None) -> float:
    if step.action_type in ("FEED_ANIMAL", "WATER", "COLLECT_PRODUCT"):
        return _effective_opex_per_task(ws) if ws is not None else LABOR_COST_PER_TASK
    return 0.0

def evaluate_investment(candidate: Candidate, project: Project, ws: WorldState) -> InvestmentEvaluation:
    step = project.step_by_id(candidate.step_id)
    operating_cost = _step_operating_cost(step, ws) if step else 0.0

    expected_profit = candidate.expected_revenue - candidate.cost - operating_cost

    revenue_steps = [s for s in project.steps if s.action_type == "SELL_PRODUCT"]
    if candidate.expected_revenue > 0:
        payback_days = candidate.cost / max(1e-6, candidate.expected_revenue)
    else:
        total_project_cost = sum(s.cost for s in project.steps)
        product_key = None
        for s in project.steps:
            if s.action_type == "SELL_PRODUCT":
                product_key = None  
        daily_revenue_proxy = max(1.0, ws.prices.get("EGG", 1.0) if "GOOSE" in project.id else
                                   ws.prices.get("MILK", 1.0) if "COW" in project.id else
                                   ws.prices.get("WHEAT", 1.0))
        payback_days = total_project_cost / daily_revenue_proxy if total_project_cost > 0 else 0.0

    capital_efficiency = expected_profit / candidate.cost if candidate.cost > 0 else expected_profit
    time_efficiency = expected_profit / max(1, candidate.duration)

    risk = 0.0 if ws.remaining_days <= 0 else min(1.0, payback_days / max(1, ws.remaining_days))

    accept = expected_profit > 0 and payback_days <= ws.remaining_days

    return InvestmentEvaluation(
        candidate_id=candidate.id,
        cost=candidate.cost,
        expected_revenue=candidate.expected_revenue,
        expected_operating_cost=operating_cost,
        expected_profit=expected_profit,
        payback_days=payback_days,
        capital_efficiency=capital_efficiency,
        time_efficiency=time_efficiency,
        risk=risk,
        accept=accept,
    )

def evaluate_animal_investment(candidate: Candidate, project: Project, ws: WorldState) -> InvestmentEvaluation:
    econ = _animal_net_economics(project.id, ws)
    if econ is None:
        return evaluate_investment(candidate, project, ws)
    economic_value = econ["economic_value"]
    payback_days = econ["payback_days"]
    capital_efficiency = economic_value / candidate.cost if candidate.cost > 0 else economic_value
    risk = 0.0 if ws.remaining_days <= 0 else min(1.0, payback_days / max(1, ws.remaining_days))
    accept = econ["gate_open"]
    return InvestmentEvaluation(
        candidate_id=candidate.id,
        cost=candidate.cost,
        expected_revenue=econ["net_daily_value"] * econ["useful_days"],   
        expected_operating_cost=econ["opportunity_cost_per_day"] * econ["useful_days"],
        expected_profit=economic_value,
        payback_days=payback_days,
        capital_efficiency=capital_efficiency,
        time_efficiency=economic_value / max(1, econ["horizon_days"]),
        risk=risk,
        accept=accept,
    )

def _crop_lifetime_value(crop: str, ws: WorldState) -> float:
    info = CROP_INFO[crop]
    price = ws.prices.get(crop, info["base_price"])
    seed_cost = info["seed_cost"]
    horizon_days = max(1, crop_economic_duration_days(crop))
    harvest_units = float(info.get("max_yield", 1))
    harvest_value = price * harvest_units
    worker_opportunity_cost = _effective_opex_per_task(ws) * horizon_days
    return harvest_value - seed_cost - worker_opportunity_cost

def evaluate_crop_investment(candidate: Candidate, project: Project, ws: WorldState) -> InvestmentEvaluation:
    crop = candidate.meta.get("crop") if candidate.meta else None
    if crop is None or crop not in CROP_INFO:
        return evaluate_investment(candidate, project, ws)
    econ = _crop_net_economics(crop, ws)
    CROP_GATE_LOG.append({"day": ws.day, **econ})
    economic_value = econ["economic_value"]
    payback_days = econ["payback_days"]
    capital_efficiency = economic_value / candidate.cost if candidate.cost > 0 else economic_value
    risk = 0.0 if ws.remaining_days <= 0 else min(1.0, payback_days / max(1, ws.remaining_days))
    accept = econ["gate_open"]
    return InvestmentEvaluation(
        candidate_id=candidate.id,
        cost=candidate.cost,
        expected_revenue=econ["harvest_value"],
        expected_operating_cost=econ["worker_opportunity_cost"] + econ["tile_opportunity_cost"],
        expected_profit=economic_value,
        payback_days=payback_days,
        capital_efficiency=capital_efficiency,
        time_efficiency=economic_value / max(1, econ["horizon_days"]),
        risk=risk,
        accept=accept,
    )

@dataclass(frozen=True)
class CropTileEvaluation:
    crop: str
    profit_per_day: float
    net_advantage: float          

def crop_economic_duration_days(crop: str) -> int:
    info = CROP_INFO[crop]
    if info.get("ongoing"):
        first_yield = info.get("first_yield", info.get("max_yield_day"))
        interval = info.get("interval", 0)
        max_yield = info.get("max_yield", 1)
        if interval > 0:
            return first_yield + (max_yield - 1) * interval
    return info["max_yield_day"]

def crop_profit_per_day(crop: str, prices: dict) -> float:
    info = CROP_INFO[crop]
    price = prices.get(crop, info["base_price"])
    revenue = price * info.get("max_yield", 1)
    profit = revenue - info["seed_cost"]
    duration = max(1, crop_economic_duration_days(crop))
    return profit / duration

def _tile_crop_demand_crash_multiplier(crop: str, ws: "WorldState") -> float:
    if crop not in CROP_INFO:
        return 1.0
    unlocked_instances = list(getattr(ws, "unlocked_shops", ()) or ())
    demand_count = sum(SHOP_DEMAND.get(s, []).count(crop) for s in unlocked_instances)
    demand_mult = min(3.0, 1.0 + 0.10 * demand_count)

    params = MARKET_PARAMS.get(crop, {})
    above_kind, above_coef = params.get("above", ("linear", 1.0))
    steepness = _ABOVE_STEEPNESS.get(above_kind, 1.0) * above_coef
    remaining_days = max(0, getattr(ws, "remaining_days", SEASON_DAYS))
    remaining_ratio = max(0.0, min(1.0, remaining_days / SEASON_DAYS))
    crash_mult = max(0.4, 1.0 - 0.20 * remaining_ratio * (steepness / _MAX_STEEPNESS))
    return demand_mult * crash_mult

def evaluate_crop_options_for_tile(prices: dict, candidate_crops=None,
                                    ws: Optional["WorldState"] = None) -> tuple:
    crops = candidate_crops or list(CROP_INFO.keys())
    per_day = {c: crop_profit_per_day(c, prices) for c in crops}
    if ws is not None:
        for c in list(per_day.keys()):
            per_day[c] *= _tile_crop_demand_crash_multiplier(c, ws)
    best = max(per_day.values()) if per_day else 0.0
    evals = [CropTileEvaluation(crop=c, profit_per_day=v, net_advantage=v - best) for c, v in per_day.items()]
    return tuple(sorted(evals, key=lambda e: e.profit_per_day, reverse=True))

CROP_GATE_LOG = _deque_diag_log(maxlen=2000)

def crop_days_to_first_harvest(crop: str) -> int:
    info = CROP_INFO[crop]
    if info.get("ongoing"):
        first_yield = info.get("first_yield", info.get("max_yield_day"))
        interval = info.get("interval", 0)
        return first_yield + interval   
    return info["max_yield_day"]

def _crop_harvest_units_at_first_harvest(crop: str) -> float:
    info = CROP_INFO[crop]
    return 2.0 if info.get("ongoing") else float(info.get("max_yield", 1))

_MARKOV_FORECAST_STATE = {"transition_matrices": {}, "transition_counts": {}, "mem": {}}

def set_markov_forecast_state(transition_matrices: dict, transition_counts: Optional[dict] = None,
                               mem: Optional[dict] = None) -> None:
    _MARKOV_FORECAST_STATE["transition_matrices"] = transition_matrices or {}
    _MARKOV_FORECAST_STATE["transition_counts"] = transition_counts or {}
    _MARKOV_FORECAST_STATE["mem"] = mem if mem is not None else {}

def _forecasted_crop_price(crop: str, ws: WorldState, horizon_days: int) -> float:
    matrix = _MARKOV_FORECAST_STATE["transition_matrices"].get(crop)
    current_price = ws.prices.get(crop, CROP_INFO[crop]["base_price"])
    if matrix is None:
        return current_price
    counts = _MARKOV_FORECAST_STATE["transition_counts"].get(crop, {})
    forecast = markov_forecast_market_prices(
        ws, _MARKOV_FORECAST_STATE["mem"], {crop: matrix}, {crop: counts},
        horizon=max(1, horizon_days))
    fc = forecast.get(crop)
    if fc is None:
        return current_price
    return fc.forecast_by_day_offset.get(horizon_days, current_price)

def _crop_net_economics(crop: str, ws: WorldState) -> dict:
    info = CROP_INFO[crop]
    seed_cost = info["seed_cost"]
    horizon_days = max(1, crop_days_to_first_harvest(crop))
    price = _forecasted_crop_price(crop, ws, horizon_days)
    harvest_units = _crop_harvest_units_at_first_harvest(crop)
    harvest_value = price * harvest_units

    worker_opportunity_cost = _effective_opex_per_task(ws) * horizon_days

    crop_ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
    best_alternative_crop_profit_per_day = max(
        (e.profit_per_day for e in crop_ranked if e.crop != crop), default=0.0)
    tile_opportunity_cost = max(0.0, best_alternative_crop_profit_per_day) * horizon_days   

    economic_value = harvest_value - seed_cost - worker_opportunity_cost
    net_daily_value = economic_value / horizon_days
    payback_days = seed_cost / max(1e-6, net_daily_value) if net_daily_value > 0 else float("inf")
    gate_open = not (economic_value <= 0 or ws.remaining_days <= 0
                      or horizon_days > ws.remaining_days)
    return {
        "crop": crop,
        "horizon_days": horizon_days,
        "harvest_units": harvest_units,
        "harvest_value": harvest_value,
        "seed_cost": seed_cost,
        "worker_opportunity_cost": worker_opportunity_cost,
        "tile_opportunity_cost": tile_opportunity_cost,
        "best_alternative_crop_profit_per_day": best_alternative_crop_profit_per_day,
        "economic_value": economic_value,
        "net_daily_value": net_daily_value,
        "payback_days": payback_days,
        "remaining_days": ws.remaining_days,
        "gate_open": gate_open,
        "reject_reason": (
            "OK" if gate_open else
            "economic_value<=0 (seed+opex+tile-opp.cost > harvest_value)" if economic_value <= 0 else
            "remaining_days<=0" if ws.remaining_days <= 0 else
            "horizon_days>remaining_days (no time for first harvest)"
        ),
    }

def evaluate_all_candidates(batch: CandidateBatch, ws: WorldState) -> dict:
    result = {}
    for c in batch.candidates:
        if c.project_id == "HIRE":
            expected_value_today = c.meta.get("expected_value_today", 0.0)
            expected_profit = expected_value_today - c.cost
            payback_fraction_of_day = c.cost / expected_value_today if expected_value_today > 0 else float("inf")
            result[c.id] = InvestmentEvaluation(
                candidate_id=c.id, cost=c.cost, expected_revenue=expected_value_today,
                expected_operating_cost=0.0, expected_profit=expected_profit,
                payback_days=payback_fraction_of_day,
                capital_efficiency=expected_profit / c.cost if c.cost > 0 else expected_profit,
                time_efficiency=expected_profit, risk=0.1,
                accept=(expected_profit > 0 and ws.remaining_days > 0
                        and payback_fraction_of_day <= 1.0),
            )
            continue
        if c.project_id == "WEED_CLEANUP":
            expected_profit = c.expected_revenue - c.cost
            result[c.id] = InvestmentEvaluation(
                candidate_id=c.id, cost=c.cost, expected_revenue=c.expected_revenue,
                expected_operating_cost=0.0, expected_profit=expected_profit,
                payback_days=0.0,
                capital_efficiency=expected_profit if c.cost == 0 else expected_profit / c.cost,
                time_efficiency=expected_profit / max(1, c.duration),
                risk=0.05,
                accept=True,
            )
            continue
        if c.project_id == "LAND_EXPANSION":
            expected_profit = c.expected_revenue - c.cost
            payback_days = c.cost / max(1e-6, c.meta.get("daily_value_proxy", 0.0))
            result[c.id] = InvestmentEvaluation(
                candidate_id=c.id, cost=c.cost, expected_revenue=c.expected_revenue,
                expected_operating_cost=0.0, expected_profit=expected_profit,
                payback_days=payback_days,
                capital_efficiency=expected_profit / c.cost if c.cost > 0 else expected_profit,
                time_efficiency=expected_profit / max(1, c.duration),
                risk=min(1.0, payback_days / max(1, ws.remaining_days)) if ws.remaining_days > 0 else 1.0,
                accept=expected_profit > 0 and payback_days <= ws.remaining_days,
            )
            continue
        if c.project_id == "FEED_STOCK":
            daily_value_proxy = max(50.0, ws.prices.get("MILK", 160.0), ws.prices.get("EGG", 50.0))
            expected_profit = daily_value_proxy - c.cost
            result[c.id] = InvestmentEvaluation(
                candidate_id=c.id, cost=c.cost, expected_revenue=daily_value_proxy,
                expected_operating_cost=0.0, expected_profit=expected_profit,
                payback_days=0.0,
                capital_efficiency=expected_profit if c.cost == 0 else expected_profit / c.cost,
                time_efficiency=expected_profit / max(1, c.duration),
                risk=0.05,
                accept=True,
            )
            continue
        if c.project_id == "DROP_INVENTORY":
            expected_profit = c.expected_revenue - c.cost
            result[c.id] = InvestmentEvaluation(
                candidate_id=c.id, cost=c.cost, expected_revenue=c.expected_revenue,
                expected_operating_cost=0.0, expected_profit=expected_profit,
                payback_days=0.0,
                capital_efficiency=expected_profit if c.cost == 0 else expected_profit / c.cost,
                time_efficiency=expected_profit / max(1, c.duration),
                risk=0.05,
                accept=True,
            )
            continue
        if c.project_id == "CARE_BONUS":
            expected_profit = c.expected_revenue - c.cost
            result[c.id] = InvestmentEvaluation(
                candidate_id=c.id, cost=c.cost, expected_revenue=c.expected_revenue,
                expected_operating_cost=0.0, expected_profit=expected_profit,
                payback_days=0.0,
                capital_efficiency=expected_profit if c.cost == 0 else expected_profit / c.cost,
                time_efficiency=expected_profit / max(1, c.duration),
                risk=0.05,
                accept=True,
            )
            continue
        if c.project_id == "FERTILIZER_CYCLE":
            expected_profit = c.expected_revenue - c.cost
            result[c.id] = InvestmentEvaluation(
                candidate_id=c.id, cost=c.cost, expected_revenue=c.expected_revenue,
                expected_operating_cost=0.0, expected_profit=expected_profit,
                payback_days=0.0,
                capital_efficiency=expected_profit if c.cost == 0 else expected_profit / c.cost,
                time_efficiency=expected_profit / max(1, c.duration),
                risk=0.1,
                accept=(c.cost == 0) or (expected_profit > 0),
            )
            continue
        project = PROJECT_REGISTRY[c.project_id]
        step = project.step_by_id(c.step_id)
        if step is not None and step.action_type == "BUY_ANIMAL" and c.project_id in PROJECT_ANIMAL:
            result[c.id] = evaluate_animal_investment(c, project, ws)
        elif step is not None and step.action_type == "PLANT":
            result[c.id] = evaluate_crop_investment(c, project, ws)
        else:
            result[c.id] = evaluate_investment(c, project, ws)
    return result

@dataclass(frozen=True)
class CapitalPlan:
    purchases: tuple              
    deferred: tuple                
    total_spending: float
    total_expected_income: float
    ending_cash: float
    reserve_remaining: float
    marginal_values: Optional[dict] = None
    scheduling_values: Optional[dict] = None

import dataclasses
import copy
import contextlib

SIM_MOVE_DELTA = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0), "PASS": (0, 0)}

def _sim_shed_access_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]

def _sim_clone_tile(tile):
    if isinstance(tile, dict):
        return dict(tile)
    return tile

def _sim_clone_tiles(tiles):
    return tuple(tuple(_sim_clone_tile(t) for t in row) for row in tiles)

def _sim_apply_task(tile, action_type, day):
    if action_type == "WATER" and isinstance(tile, dict):
        tile["watered_today"] = True
    elif action_type == "FERTILIZE" and isinstance(tile, dict):
        tile["fertilized_until_day"] = max(tile.get("fertilized_until_day", -1), day + 2)
    elif action_type == "HARVEST" and isinstance(tile, dict):
        tile["yield_units"] = 0
    elif action_type == "FEED_ANIMAL" and isinstance(tile, dict):
        tile["fed_today"] = True
    elif action_type == "CARE_BONUS" and isinstance(tile, dict):
        tile["cared_today"] = True

def _sim_step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    if tx > fx:
        return "EAST"
    if tx < fx:
        return "WEST"
    if ty > fy:
        return "SOUTH"
    if ty < fy:
        return "NORTH"
    return "PASS"

def _sim_move(pos, target):
    step = _sim_step_toward(pos, target)
    dx, dy = SIM_MOVE_DELTA[step]
    return (pos[0] + dx, pos[1] + dy)

def build_synthetic_worldstate(ws: WorldState, n_workers: int, extra_plant_positions=None):
    board_size = len(ws.tiles)
    tiles = [list(row) for row in _sim_clone_tiles(ws.tiles)]
    for pos in (extra_plant_positions or []):
        x, y = pos
        tiles[y][x] = dict(kind="PLANT", crop=BOOTSTRAP_CROP, planted_day=ws.day,
                            watered_today=False, consecutive_unwatered=1,
                            fertilized_until_day=-1, yield_units=0)
    access = _sim_shed_access_tiles(board_size)
    hands = list(ws.hands)
    while 1 + len(hands) < n_workers:
        hands.append(access[len(hands) % len(access)])
    hands = tuple(hands[:max(0, n_workers - 1)])
    return dataclasses.replace(ws, tiles=tuple(tuple(row) for row in tiles), hands=hands)

_SIMULATING_FEASIBILITY = False

@contextlib.contextmanager
def _feasibility_signal_reentrancy_guard():
    global _SIMULATING_FEASIBILITY
    prev_flag = _SIMULATING_FEASIBILITY
    _SIMULATING_FEASIBILITY = True
    try:
        yield
    finally:
        _SIMULATING_FEASIBILITY = prev_flag

@contextlib.contextmanager
def _sim_use_original_pipeline():
    global _SIMULATING_FEASIBILITY
    ns = globals()
    saved = {name: ns[name] for name in ("_plant_throttle_fraction", "compute_optimal_workforce")
             if name in ns}
    ns["_plant_throttle_fraction"] = _orig_plant_throttle_fraction
    ns["compute_optimal_workforce"] = _orig_compute_optimal_workforce
    prev_flag = _SIMULATING_FEASIBILITY
    _SIMULATING_FEASIBILITY = True
    try:
        yield
    finally:
        ns.update(saved)
        _SIMULATING_FEASIBILITY = prev_flag

def simulate_day_feasibility(ws: WorldState, mem: dict, n_workers: int,
                              extra_plant_positions=None, max_turns: int = 24) -> dict:
    with _sim_use_original_pipeline():
        return _simulate_day_feasibility_inner(ws, mem, n_workers, extra_plant_positions, max_turns)

def _simulate_day_feasibility_inner(ws: WorldState, mem: dict, n_workers: int,
                                     extra_plant_positions=None, max_turns: int = 24) -> dict:
    sim_ws = build_synthetic_worldstate(ws, n_workers, extra_plant_positions)
    sim_mem = copy.deepcopy({k: v for k, v in mem.items() if k not in ("pacing",)})

    fa0 = _orig_build_farm_analysis(sim_ws, sim_mem)
    batch0 = generate_candidates(sim_ws, fa0, sim_mem)
    tracked_keys = {(c.action_type, c.target) for c in batch0.candidates
                     if c.action_type in MANDATORY_ACTION_TYPES}
    done_keys = set()

    turns_used = 0
    for t in range(max_turns):
        if len(done_keys) >= len(tracked_keys):
            break
        fa = _orig_build_farm_analysis(sim_ws, sim_mem)
        batch = generate_candidates(sim_ws, fa, sim_mem)
        evaluations = evaluate_all_candidates(batch, sim_ws)
        plan = optimize_capital(batch, evaluations, sim_ws)
        schedule = schedule_workers(plan, evaluations, sim_ws)

        workers = [sim_ws.farmer] + list(sim_ws.hands)
        new_hands = list(sim_ws.hands)
        tiles = [list(row) for row in sim_ws.tiles]
        candidates_by_id = {c.id: c for c in plan.purchases}

        for a in schedule.assignments:
            if a.candidate_id is None:
                continue
            c = candidates_by_id.get(a.candidate_id)
            if c is None or not isinstance(c.target, tuple) or len(c.target) != 2:
                continue
            pos = workers[a.worker_index]
            if pos == c.target:
                x, y = c.target
                _sim_apply_task(tiles[y][x], c.action_type, sim_ws.day)
                key = (c.action_type, c.target)
                if key in tracked_keys:
                    done_keys.add(key)
            else:
                new_pos = _sim_move(pos, c.target)
                if a.worker_index == 0:
                    sim_ws = dataclasses.replace(sim_ws, farmer=new_pos)
                else:
                    new_hands[a.worker_index - 1] = new_pos

        sim_ws = dataclasses.replace(sim_ws, hands=tuple(new_hands),
                                      tiles=tuple(tuple(row) for row in tiles),
                                      turn_in_episode=sim_ws.turn_in_episode + 1)
        turns_used += 1

    return {
        "feasible": len(done_keys) >= len(tracked_keys),
        "tasks_total": len(tracked_keys),
        "tasks_done": len(done_keys),
        "turns_used": turns_used,
    }

WORKFORCE_MAX_EXTRA_HIRES_PER_DAY = 8
WORKFORCE_HIRE_SPEND_FRACTION = 0.5

def compute_optimal_workforce_v3(ws: WorldState, fa: "FarmAnalysis", mem: dict,
                                  discretionary_cash: float, mandatory_future_cost: float = 0.0) -> dict:
    pacing = _pacing_get_or_init(mem)
    current_n = 1 + len(ws.hands)
    remaining_turns = TURNS_PER_DAY - (ws.turn_in_episode % TURNS_PER_DAY)

    day_key = ws.day
    cache = pacing.get("wf_v3_day")
    if cache is not None and cache["day"] == day_key and cache["n"] == current_n:
        return cache["result"]

    sim_now = simulate_day_feasibility(ws, mem, current_n, max_turns=remaining_turns)

    backlog = max(0, sim_now["tasks_total"] - sim_now["tasks_done"])

    if sim_now["feasible"]:
        pacing["reduce_seed_signal"] = False
        result = {"target_n": current_n, "backlog": backlog, "feasible": True, "sim": sim_now}
        pacing["wf_v3_day"] = {"day": day_key, "n": current_n, "result": result}
        return result

    cash_available = max(0.0, ws.money - mandatory_future_cost - RESERVE_MIN_OPERATING_CASH)
    hire_spend_cap = cash_available * WORKFORCE_HIRE_SPEND_FRACTION
    with _feasibility_signal_reentrancy_guard():
        physical_cap_n = 1 + _hand_cap_for_quadrant(ws.n_quadrants, ws.day, ws=ws, fa=fa,
                                                     discretionary_cash=discretionary_cash,
                                                     mandatory_future_cost=mandatory_future_cost) * max(1, ws.n_quadrants)
    max_extra = min(WORKFORCE_MAX_EXTRA_HIRES_PER_DAY, max(0, physical_cap_n - current_n))

    cum_hire_cost = 0.0
    best = None
    for extra in range(1, max_extra + 1):
        cum_hire_cost += _fib_cost(len(ws.hands) + extra - 1)
        if cum_hire_cost > hire_spend_cap:
            break  
        if remaining_turns <= 0:
            break
        sim_k = simulate_day_feasibility(ws, mem, current_n + extra, max_turns=remaining_turns)
        if sim_k["feasible"]:
            best = (current_n + extra, sim_k)
            break

    if best is not None:
        pacing["reduce_seed_signal"] = False
        result = {"target_n": best[0], "backlog": backlog, "feasible": True, "sim": best[1]}
    else:
        pacing["reduce_seed_signal"] = True
        result = {"target_n": current_n, "backlog": backlog, "feasible": False, "sim": sim_now}

    pacing["wf_v3_day"] = {"day": day_key, "n": current_n, "result": result}
    return result

def can_afford_more_seeds(ws: WorldState, mem: dict, extra_positions: list) -> bool:
    current_n = 1 + len(ws.hands)
    remaining = TURNS_PER_DAY - (ws.turn_in_episode % TURNS_PER_DAY)
    sim = simulate_day_feasibility(ws, mem, current_n, extra_plant_positions=extra_positions,
                                    max_turns=remaining)
    return sim["feasible"]

print("Part 7f loaded: real-pipeline workforce feasibility simulator "
      "(compute_optimal_workforce_v3, can_afford_more_seeds).")

_SLACK_SIM_EXCLUDED_ACTION_TYPES = ("PLANT", "BUY_ANIMAL", "BUILD_STRUCTURE", "HIRE", "BUY_FEED_WHEAT")

def _sim_strip_new_commitments(batch: "CandidateBatch") -> "CandidateBatch":
    kept = tuple(c for c in batch.candidates if c.action_type not in _SLACK_SIM_EXCLUDED_ACTION_TYPES)
    return dataclasses.replace(batch, candidates=kept)

def _simulate_worker_slack(ws: WorldState, mem: dict, n_workers: int, max_turns: int = 24):
    _SIM_UNHANDLED_ACTION_TYPES = ("PICKUP_FEED_WHEAT", "BUY_FEED_WHEAT", "PICKUP", "PLACE",
                                    "COLLECT_FERTILIZER", "COLLECT_PRODUCT", "SELL_PRODUCT",
                                    "BUILD_STRUCTURE")

    with _sim_use_original_pipeline():
        sim_ws = build_synthetic_worldstate(ws, n_workers)
        sim_mem = copy.deepcopy({k: v for k, v in mem.items() if k not in ("pacing",)})
        busy_turns = [0] * n_workers
        resolved_steps = set()

        for t in range(max_turns):
            fa = _orig_build_farm_analysis(sim_ws, sim_mem)
            batch = generate_candidates(sim_ws, fa, sim_mem)
            batch = _sim_strip_new_commitments(batch)
            if resolved_steps:
                kept = tuple(c for c in batch.candidates
                             if (c.project_id, c.step_id) not in resolved_steps)
                batch = dataclasses.replace(batch, candidates=kept)
            evaluations = evaluate_all_candidates(batch, sim_ws)
            plan = optimize_capital(batch, evaluations, sim_ws)
            schedule = schedule_workers(plan, evaluations, sim_ws)

            workers = [sim_ws.farmer] + list(sim_ws.hands)
            new_hands = list(sim_ws.hands)
            tiles = [list(row) for row in sim_ws.tiles]
            candidates_by_id = {c.id: c for c in plan.purchases}

            for a in schedule.assignments:
                if a.candidate_id is None:
                    continue
                c = candidates_by_id.get(a.candidate_id)
                if c is None or not isinstance(c.target, tuple) or len(c.target) != 2:
                    continue
                if c.action_type in MANDATORY_ACTION_TYPES:
                    busy_turns[a.worker_index] += 1
                pos = workers[a.worker_index]
                if pos == c.target:
                    x, y = c.target
                    _sim_apply_task(tiles[y][x], c.action_type, sim_ws.day)
                    if c.action_type in _SIM_UNHANDLED_ACTION_TYPES:
                        resolved_steps.add((c.project_id, c.step_id))
                else:
                    new_pos = _sim_move(pos, c.target)
                    if a.worker_index == 0:
                        sim_ws = dataclasses.replace(sim_ws, farmer=new_pos)
                    else:
                        new_hands[a.worker_index - 1] = new_pos

            sim_ws = dataclasses.replace(sim_ws, hands=tuple(new_hands),
                                          tiles=tuple(tuple(row) for row in tiles),
                                          turn_in_episode=sim_ws.turn_in_episode + 1)

        idle_turns = [max_turns - b for b in busy_turns]
        final_positions = [sim_ws.farmer] + list(sim_ws.hands)
        return idle_turns, final_positions

def max_affordable_seeds_v2(ws: WorldState, mem: dict, candidate_positions: list) -> int:
    if not candidate_positions:
        return 0
    remaining = TURNS_PER_DAY - (ws.turn_in_episode % TURNS_PER_DAY)
    if remaining <= 0:
        return 0

    wf = compute_optimal_workforce_v3(ws, None, mem, ws.money)
    target_n = wf["target_n"]

    idle, pos = _simulate_worker_slack(ws, mem, target_n, max_turns=remaining)

    n_committed = 0
    for target in candidate_positions:
        best_wi = max(range(len(idle)), key=lambda i: idle[i])
        cost = abs(pos[best_wi][0] - target[0]) + abs(pos[best_wi][1] - target[1]) + 1
        if cost <= idle[best_wi]:
            idle[best_wi] -= cost
            pos[best_wi] = target
            n_committed += 1
        else:
            break
    return n_committed



from collections import deque as _deque_diag_log
PROJECT_MILESTONE_ACTION_TYPES = ("BUILD_STRUCTURE", "BUY_ANIMAL", "BUY_FEED_WHEAT", "HIRE")

from collections import deque as _deque_animal_log

ANIMAL_OPTIMIZE_LOG = _deque_animal_log(maxlen=5000)

def optimize_capital(batch: CandidateBatch, evaluations: dict, ws: WorldState,
                      mandatory_future_cost: float = 0.0,
                      strategy: Optional["StrategyConfig"] = None,
                      market_opportunity: Optional[dict] = None) -> CapitalPlan:
    strategy = strategy or DEFAULT_STRATEGY_CONFIG
    base_discretionary = _discretionary_cash(ws, mandatory_future_cost)
    discretionary = base_discretionary * max(0.0, min(1.0, strategy.investment_budget_fraction))

    affordable_candidates = [c for c in batch.candidates if c.financial_status == "AFFORDABLE" and c.cost > 0]
    zero_cost_candidates = [c for c in batch.candidates if c.cost == 0]  
    deferred_candidates = [c for c in batch.candidates if c.financial_status == "DEFER"]

    def _is_accepted(c: Candidate) -> bool:
        ev = evaluations.get(c.id)
        return ev is not None and ev.accept

    rejected_negative_ev = [c for c in affordable_candidates if not _is_accepted(c)]
    affordable_candidates = [c for c in affordable_candidates if _is_accepted(c)]
    deferred_candidates.extend(rejected_negative_ev)

    def marginal_value(c: Candidate) -> float:
        ev = evaluations.get(c.id)
        if ev is None:
            return 0.0
        return ev.expected_profit * _strategy_rank_multiplier(c, ev, strategy) \
            * _market_opportunity_multiplier(c, market_opportunity) \
            * _shop_demand_multiplier(c, ws, ev)

    def ratio(c: Candidate) -> float:
        return (marginal_value(c) / c.cost) if c.cost > 0 else marginal_value(c)

    milestone_candidates = [c for c in affordable_candidates if c.action_type in PROJECT_MILESTONE_ACTION_TYPES]
    optional_candidates = [c for c in affordable_candidates if c.action_type not in PROJECT_MILESTONE_ACTION_TYPES]

    milestone_ranked = sorted(milestone_candidates, key=ratio, reverse=True)
    optional_ranked = sorted(optional_candidates, key=ratio, reverse=True)

    real_cash_budget = max(0.0, ws.money - mandatory_future_cost)

    def _greedy_fill(milestone_list, optional_list, budget_cap):
        sel, sp, defer = [], 0.0, []
        for c in milestone_list:
            is_bootstrap = bool(c.meta.get("bootstrap_hire"))
            budget = real_cash_budget if is_bootstrap else budget_cap
            if sp + c.cost <= budget:
                sel.append(c)
                sp += c.cost  # FIX: always track real spend -- bootstrap hires draw
                              # from the SAME cash pool as everything else; budget_cap
                              # is always <= real_cash_budget by construction, so this
                              # can never make a later non-bootstrap check too strict.
            else:
                defer.append(c)
        for c in optional_list:
            if sp + c.cost <= budget_cap:
                sel.append(c)
                sp += c.cost
            else:
                defer.append(c)
        return sel, sp, defer

    alpha = strategy.animal_allocation_ratio
    if alpha is None:
        selected, spent, defer_new = _greedy_fill(milestone_ranked, optional_ranked, discretionary)
        deferred_candidates.extend(defer_new)
    else:
        alpha = max(0.0, min(1.0, alpha))
        animal_budget = alpha * discretionary
        crop_budget = (1.0 - alpha) * discretionary
        is_livestock = lambda c: _project_category(c.project_id) == "LIVESTOCK"
        m_animal = [c for c in milestone_ranked if is_livestock(c)]
        m_crop = [c for c in milestone_ranked if not is_livestock(c)]
        o_animal = [c for c in optional_ranked if is_livestock(c)]
        o_crop = [c for c in optional_ranked if not is_livestock(c)]
        sel_a, spent_a, defer_a = _greedy_fill(m_animal, o_animal, animal_budget)
        sel_c, spent_c, defer_c = _greedy_fill(m_crop, o_crop, crop_budget)
        selected = sel_a + sel_c
        spent = spent_a + spent_c
        deferred_candidates.extend(defer_a + defer_c)

    total_income = sum(evaluations[c.id].expected_revenue for c in selected + zero_cost_candidates if c.id in evaluations)

    _selected_ids = {c.id for c in selected}
    _rejected_negev_ids = {c.id for c in rejected_negative_ev}
    _deferred_ids = {c.id for c in deferred_candidates}
    for c in batch.candidates:
        if c.action_type != "BUY_ANIMAL":
            continue
        if c.id in _selected_ids:
            outcome = "SELECTED (purchased)"
            if RL_ANIMAL_CONTROLLER is not None:
                _animal_name = PROJECT_ANIMAL.get(c.project_id)
                if _animal_name:
                    RL_ANIMAL_CONTROLLER.mark_purchased(ws.day, _animal_name)
        elif c.id in _rejected_negev_ids:
            outcome = "REJECTED_NEGATIVE_EV"
        elif c.id in _deferred_ids:
            outcome = "DEFERRED (no budget)"
        elif c.financial_status == "DEFER":
            outcome = "DEFERRED (financial_status=DEFER, no budget upfront)"
        else:
            outcome = "UNKNOWN"
        ev = evaluations.get(c.id)
        ANIMAL_OPTIMIZE_LOG.append({
            "day": ws.day, "project_id": c.project_id, "cost": c.cost,
            "financial_status": c.financial_status,
            "expected_profit": ev.expected_profit if ev else None,
            "outcome": outcome,
        })

    marginal_values = {c.id: marginal_value(c) for c in selected}

    scheduling_values = {}
    for c in selected:
        if c.action_type == "PLANT" and "crop" in c.meta:
            scheduling_values[c.id] = _crop_lifetime_value(c.meta["crop"], ws)

    return CapitalPlan(
        purchases=tuple(selected + zero_cost_candidates),
        deferred=tuple(deferred_candidates),
        total_spending=spent,
        total_expected_income=total_income,
        ending_cash=ws.money - spent,
        reserve_remaining=discretionary - spent,
        marginal_values=marginal_values,
        scheduling_values=scheduling_values,
    )

MANDATORY_ACTION_TYPES = ("WATER", "HARVEST", "SELL_PRODUCT", "FEED_ANIMAL", "COLLECT_PRODUCT", "PICKUP", "PLACE",
                          "PICKUP_FEED_WHEAT", "BUILD_STRUCTURE", "CARE_BONUS",
                          "COLLECT_FERTILIZER", "FERTILIZE", "PICKUP_FERTILIZER")

@dataclass(frozen=True)
class WorkerAssignment:
    worker_index: int
    candidate_id: Optional[str]     
    is_mandatory: bool
    utility: float

@dataclass(frozen=True)
class SchedulePlan:
    assignments: tuple                    
    mandatory_unsatisfied: tuple          

def _worker_position(worker) -> tuple:
    if isinstance(worker, dict):
        return (worker.get("x", 0), worker.get("y", 0))
    return (worker[0], worker[1])

def _task_position(candidate: Candidate) -> Optional[tuple]:
    t = candidate.target
    if isinstance(t, tuple) and len(t) == 2 and all(isinstance(v, int) for v in t):
        return t
    return None

def _travel_cost(worker_pos: tuple, task_pos: Optional[tuple]) -> float:
    if task_pos is None:
        return 0.0
    return abs(worker_pos[0] - task_pos[0]) + abs(worker_pos[1] - task_pos[1])

def _task_utility(candidate: Candidate, evaluation, worker_pos: tuple,
                   marginal_values: Optional[dict] = None,
                   scheduling_values: Optional[dict] = None) -> float:
    if scheduling_values is not None and candidate.id in scheduling_values:
        task_value = scheduling_values[candidate.id]
    elif marginal_values is not None and candidate.id in marginal_values:
        task_value = marginal_values[candidate.id]
    else:
        task_value = evaluation.expected_profit if evaluation else 0.0
    pos = _task_position(candidate)
    travel = _travel_cost(worker_pos, pos)
    return task_value - travel

def schedule_workers(plan: CapitalPlan, evaluations: dict, ws: WorldState) -> SchedulePlan:
    workers = [ws.farmer] + list(ws.hands)
    n_workers = len(workers)

    mandatory = [c for c in plan.purchases
                 if c.action_type in MANDATORY_ACTION_TYPES and c.action_type not in MARKET_ACTION_TYPES]
    def _mandatory_priority(c):
        if c.action_type == "FEED_ANIMAL":
            return -10 - c.meta.get("consecutive_unfed", 0)
        if c.action_type == "PICKUP_FEED_WHEAT":
            return -5
        # CARE_BONUS was previously raised above WATER, but WATER has a
        # hard deadline (2 skips -> WEED). Fixed: fall back to 0 here;
        # stable sort + insertion order makes WATER win naturally.
        return 0
    mandatory.sort(key=_mandatory_priority)
    optional = [c for c in plan.purchases
                if c.action_type not in MANDATORY_ACTION_TYPES and c.action_type not in MARKET_ACTION_TYPES]

    assigned_worker_idx = set()
    assignments = {}
    mandatory_unsatisfied = []

    for c in mandatory:
        if c.required_worker_index is not None:
            wi = c.required_worker_index
            if wi >= n_workers or wi in assigned_worker_idx:
                mandatory_unsatisfied.append(c.id)
                continue
            u = _task_utility(c, evaluations.get(c.id), _worker_position(workers[wi]), plan.marginal_values, plan.scheduling_values)
            assignments[wi] = WorkerAssignment(wi, c.id, True, u)
            assigned_worker_idx.add(wi)
            continue

        best_w, best_u = None, None
        for wi in range(n_workers):
            if wi in assigned_worker_idx:
                continue
            u = _task_utility(c, evaluations.get(c.id), _worker_position(workers[wi]), plan.marginal_values, plan.scheduling_values)
            if best_u is None or u > best_u:
                best_w, best_u = wi, u
        if best_w is None:
            mandatory_unsatisfied.append(c.id)     
        else:
            assignments[best_w] = WorkerAssignment(best_w, c.id, True, best_u)
            assigned_worker_idx.add(best_w)

    remaining_workers = [wi for wi in range(n_workers) if wi not in assigned_worker_idx]
    if remaining_workers and optional:
        util_matrix = []
        for wi in remaining_workers:
            row = []
            for c in optional:
                if c.required_worker_index is not None and c.required_worker_index != wi:
                    row.append(-1e9)
                else:
                    row.append(_task_utility(c, evaluations.get(c.id), _worker_position(workers[wi]), plan.marginal_values, plan.scheduling_values))
            util_matrix.append(row)

        try:
            import numpy as np
            from scipy.optimize import linear_sum_assignment
            cost_matrix = -np.array(util_matrix, dtype=float)
            row_idx, col_idx = linear_sum_assignment(cost_matrix)
            matched_workers = set()
            for r, c_idx in zip(row_idx, col_idx):
                wi = remaining_workers[r]
                cand = optional[c_idx]
                u = util_matrix[r][c_idx]
                if u > 0:   
                    assignments[wi] = WorkerAssignment(wi, cand.id, False, u)
                    matched_workers.add(wi)
            for wi in remaining_workers:
                if wi not in matched_workers:
                    assignments[wi] = WorkerAssignment(wi, None, False, 0.0)
        except ImportError:
            used_tasks = set()
            for wi in remaining_workers:
                best_c, best_u = None, 0.0
                for ci, c in enumerate(optional):
                    if ci in used_tasks:
                        continue
                    if c.required_worker_index is not None and c.required_worker_index != wi:
                        continue
                    u = _task_utility(c, evaluations.get(c.id), _worker_position(workers[wi]), plan.marginal_values, plan.scheduling_values)
                    if u > best_u:
                        best_c, best_u = ci, u
                if best_c is not None:
                    assignments[wi] = WorkerAssignment(wi, optional[best_c].id, False, best_u)
                    used_tasks.add(best_c)
                else:
                    assignments[wi] = WorkerAssignment(wi, None, False, 0.0)
    else:
        for wi in remaining_workers:
            assignments[wi] = WorkerAssignment(wi, None, False, 0.0)

    final_assignments = tuple(assignments.get(wi, WorkerAssignment(wi, None, False, 0.0)) for wi in range(n_workers))
    return SchedulePlan(assignments=final_assignments, mandatory_unsatisfied=tuple(mandatory_unsatisfied))

def nearest_target(pos, targets):
    if not targets:
        return None
    fx, fy = pos
    return min(targets, key=lambda t: abs(t[0] - fx) + abs(t[1] - fy))

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    if tx > fx:
        return "EAST"
    if tx < fx:
        return "WEST"
    if ty > fy:
        return "SOUTH"
    if ty < fy:
        return "NORTH"
    return "PASS"

def move_toward(pos, target, reserved_tiles):
    fx, fy = pos
    tx, ty = target
    delta = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0), "PASS": (0, 0)}

    primary_step = _step_toward(pos, target)
    dx, dy = delta.get(primary_step, (0, 0))
    primary_next = (fx + dx, fy + dy)
    if primary_step != "PASS" and (primary_next not in reserved_tiles or primary_next == pos):
        reserved_tiles.add(primary_next)
        return primary_step, primary_next

    secondary_step = None
    if ty > fy:
        secondary_step = "SOUTH"
    elif ty < fy:
        secondary_step = "NORTH"
    elif tx > fx:
        secondary_step = "EAST"
    elif tx < fx:
        secondary_step = "WEST"

    if secondary_step is not None and secondary_step != primary_step:
        sdx, sdy = delta[secondary_step]
        secondary_next = (fx + sdx, fy + sdy)
        if secondary_next not in reserved_tiles or secondary_next == pos:
            reserved_tiles.add(secondary_next)
            return secondary_step, secondary_next

    reserved_tiles.add(pos)
    return "PASS", pos

PROJECT_ANIMAL = {"GOOSE_ECONOMY": "GOOSE", "COW_ECONOMY": "COW", "SHEEP_ECONOMY": "SHEEP"}

MARKET_ACTION_TYPES = ("SELL_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "BUY_LAND", "HIRE", "BUY_FEED_WHEAT",
                        "BUY_FERTILIZER")

ANIMAL_ENV_ACTION_LOG = _deque_diag_log(maxlen=2000)
_PHYSICAL_ACT_VOCAB = {
    "WATER": lambda c, ws: ["WATER"],
    "HARVEST": lambda c, ws: ["HARVEST"],
    "COLLECT_PRODUCT": lambda c, ws: ["HARVEST"],
    "CARE_BONUS": lambda c, ws: ["CARE"],
    "FERTILIZE": lambda c, ws: ["FERTILIZE"],
    "COLLECT_FERTILIZER": lambda c, ws: ["COLLECT_FERTILIZER"],
    "DROP": lambda c, ws: ["DROP"],
    "PICKUP_FERTILIZER": lambda c, ws: ["PICKUP", "FERTILIZER", 1],
    "FEED_ANIMAL": lambda c, ws: ["FEED"],
    "PLANT": lambda c, ws: ["PLANT", c.meta.get("crop") or _best_crop_fallback(ws)],
    "BUILD_STRUCTURE": lambda c, ws: ["BUILD_" + STRUCTURE_FOR_ANIMAL.get(
        PROJECT_ANIMAL.get(c.project_id, ""), "COOP")],
    "DIG": lambda c, ws: ["DIG"],
    "PICKUP": lambda c, ws: ["PICKUP", c.meta.get("animal_type") or PROJECT_ANIMAL.get(c.project_id, ""), 1],
    "PICKUP_FEED_WHEAT": lambda c, ws: ["PICKUP", "WHEAT", 1],
    "PLACE": lambda c, ws: ["PLACE", c.meta.get("animal_type") or PROJECT_ANIMAL.get(c.project_id, "")],
}

def _best_crop_fallback(ws: WorldState) -> str:
    ranked = evaluate_crop_options_for_tile(ws.prices, ws=ws)
    return ranked[0].crop if ranked else CROP_ORDER[0]

def _market_order_for(candidate: Candidate, ws: WorldState, sell_fractions: Optional[dict] = None):
    at = candidate.action_type
    if at == "SELL_PRODUCT":
        product = candidate.target
        qty = ws.shed.get(product, 0)
        if product == "WHEAT" and (ws.n_coop > 0 or ws.n_pasture > 0):
            qty = max(0, qty - FEED_WHEAT_SELL_RESERVE)
        if product == "FERTILIZER":
            qty = max(0, qty - FERTILIZER_SELL_RESERVE)
        fraction = (sell_fractions or {}).get(product, 1.0)
        qty = round(qty * fraction)
        if not product or qty <= 0:
            return None
        return ["SELL", product, qty]
    if at == "BUY_SEED":
        crop = candidate.meta.get("crop") or _best_crop_fallback(ws)
        return ["BUY_SEED", crop, 1]
    if at == "BUY_ANIMAL":
        animal = PROJECT_ANIMAL.get(candidate.project_id)
        if not animal:
            return None
        return ["BUY_ANIMAL", animal, 1]
    if at == "BUY_LAND":
        return ["BUY_LAND"]
    if at == "HIRE":
        return ["HIRE"]
    if at == "BUY_FEED_WHEAT":
        return ["BUY_PRODUCT", "WHEAT", 1]
    if at == "BUY_FERTILIZER":
        return ["BUY_PRODUCT", "FERTILIZER", 1]
    return None

def build_env_action(schedule_plan: SchedulePlan, batch: CandidateBatch, ws: WorldState, mem: dict,
                      capital_plan: Optional["CapitalPlan"] = None,
                      sell_fractions: Optional[dict] = None) -> dict:
    candidates_by_id = {c.id: c for c in batch.candidates}
    workers = [ws.farmer] + list(ws.hands)
    reserved_tiles = set()
    market_orders = []
    MARKET_ORDER_DROPPED_LOG = []   

    def _sell_candidate_value(c) -> float:
        product = c.target
        qty = ws.shed.get(product, 0)
        if product == "WHEAT" and (ws.n_coop > 0 or ws.n_pasture > 0):
            qty = max(0, qty - FEED_WHEAT_SELL_RESERVE)
        if product == "FERTILIZER":
            qty = max(0, qty - FERTILIZER_SELL_RESERVE)
        return ws.prices.get(product, 0.0) * max(0, qty)

    if capital_plan is not None:
        market_candidates_only = [c for c in capital_plan.purchases if c.action_type in MARKET_ACTION_TYPES]
        sell_candidates = sorted(
            [c for c in market_candidates_only if c.action_type == "SELL_PRODUCT"],
            key=_sell_candidate_value, reverse=True)
        prioritized_purchases = (
            sell_candidates
            + [c for c in market_candidates_only if c.action_type != "SELL_PRODUCT"]
            + [c for c in capital_plan.purchases if c.action_type not in MARKET_ACTION_TYPES]
        )
        for c in prioritized_purchases:
            if c.action_type == "BUY_ANIMAL":
                if len(market_orders) >= MAX_MARKET_ORDERS_PER_TURN:
                    ANIMAL_ENV_ACTION_LOG.append({"day": ws.day, "project_id": c.project_id,
                                                   "outcome": "DROPPED_MAX_MARKET_ORDERS_CAP"})
                else:
                    order = _market_order_for(c, ws, sell_fractions)
                    ANIMAL_ENV_ACTION_LOG.append({"day": ws.day, "project_id": c.project_id,
                                                   "outcome": "ENV_ORDER_BUILT" if order is not None else "MARKET_ORDER_FOR_RETURNED_NONE",
                                                   "order": order})
            if c.action_type in MARKET_ACTION_TYPES and len(market_orders) >= MAX_MARKET_ORDERS_PER_TURN:
                MARKET_ORDER_DROPPED_LOG.append({"day": ws.day, "action_type": c.action_type,
                                                  "project_id": c.project_id})
            if c.action_type in MARKET_ACTION_TYPES and len(market_orders) < MAX_MARKET_ORDERS_PER_TURN:
                order = _market_order_for(c, ws, sell_fractions)
                if order is not None:
                    market_orders.append(order)

    seeds_remaining = dict(ws.seeds)
    buy_seed_needed = {}   

    per_worker_act = {}
    for a in schedule_plan.assignments:
        wi = a.worker_index
        pos = _worker_position(workers[wi]) if wi < len(workers) else (0, 0)

        candidate = candidates_by_id.get(a.candidate_id) if a.candidate_id else None
        if candidate is None:
            reserved_tiles.add(pos)
            per_worker_act[wi] = ["PASS"]
            continue

        if candidate.action_type in MARKET_ACTION_TYPES:
            if not capital_plan:
                order = _market_order_for(candidate, ws, sell_fractions)
                if order is not None and len(market_orders) < MAX_MARKET_ORDERS_PER_TURN:
                    market_orders.append(order)
            reserved_tiles.add(pos)
            per_worker_act[wi] = ["PASS"]
            continue

        target_pos = _task_position(candidate)
        if target_pos is None:
            reserved_tiles.add(pos)
            per_worker_act[wi] = ["PASS"]
            continue

        if pos == target_pos:
            reserved_tiles.add(pos)
            if candidate.action_type == "PLANT":
                crop = candidate.meta.get("crop") or _best_crop_fallback(ws)
                if seeds_remaining.get(crop, 0) <= 0:
                    buy_seed_needed[crop] = buy_seed_needed.get(crop, 0) + 1
                    per_worker_act[wi] = ["PASS"]
                else:
                    seeds_remaining[crop] = seeds_remaining.get(crop, 0) - 1
                    per_worker_act[wi] = ["PLANT", crop]
            else:
                vocab_fn = _PHYSICAL_ACT_VOCAB.get(candidate.action_type)
                per_worker_act[wi] = list(vocab_fn(candidate, ws)) if vocab_fn else ["PASS"]
        else:
            step, _next_pos = move_toward(pos, target_pos, reserved_tiles)
            per_worker_act[wi] = [step]

    for crop, qty_needed in buy_seed_needed.items():
        if len(market_orders) >= MAX_MARKET_ORDERS_PER_TURN:
            break
        market_orders.append(["BUY_SEED", crop, qty_needed])

    farmer_act = per_worker_act.get(0, ["PASS"])
    hands_acts = [per_worker_act.get(i, ["PASS"]) for i in range(1, len(workers))]
    return {"farmer": farmer_act, "hands": hands_acts, "market": market_orders[:MAX_MARKET_ORDERS_PER_TURN]}

MARKET_STATE_LEVELS = ("LOW", "NORMAL", "HIGH")

MARKET_STATE_LOW_THRESHOLD = 0.8

MARKET_STATE_HIGH_THRESHOLD = 1.2

def classify_price_state(product: str, price: float) -> str:
    base = MARKET_PARAMS.get(product, {}).get("base")
    if not base:
        return "NORMAL"
    ratio = price / base
    if ratio < MARKET_STATE_LOW_THRESHOLD:
        return "LOW"
    if ratio > MARKET_STATE_HIGH_THRESHOLD:
        return "HIGH"
    return "NORMAL"

def log_market_state(ws: WorldState, mem: dict) -> None:
    log = mem.setdefault("market_state_log", {})   
    price_log = mem.setdefault("market_price_log", {})   
    last_logged_day = mem.get("_market_state_last_logged_day", -1)
    if ws.day == last_logged_day:
        return
    mem["_market_state_last_logged_day"] = ws.day
    for product, price in ws.prices.items():
        state = classify_price_state(product, price)
        log.setdefault(product, []).append(state)
        price_log.setdefault(product, []).append(price)


PACING_WINDOWS_TURNS = (6, 12, 18, 24)
PACING_WINDOW_WEIGHTS = {6: 0.40, 12: 0.30, 18: 0.20, 24: 0.10}
PACING_SIGNAL_TIERS = (0.0, 0.25, 0.5, 0.75, 1.0)
PACING_HISTORY_KEEP_TURNS = 30
PACING_HIRE_RESERVE_LOOKAHEAD = 3
PACING_STICKINESS_BONUS = 40.0
PACING_TARGET_RAMP_MIN_STEP = 1
PACING_TARGET_RAMP_MAX_STEP = 6

_PACING_CURRENT_MEM = {"mem": None}

def _pacing_get_or_init(mem: dict) -> dict:
    if "pacing" not in mem:
        mem["pacing"] = {
            "history": [],
            "smoothed_target_n": None,
            "worker_commitment": {},
            "last_turn": 0,
        }
    return mem["pacing"]

def _pacing_blend_signal(history: list, key_fn, turn: int) -> float:
    if not history:
        return 1.0
    acc, total_w = 0.0, 0.0
    for w in PACING_WINDOWS_TURNS:
        window_rows = [r for r in history if 0 <= turn - r["turn"] < w]
        if not window_rows:
            continue
        sig = sum(key_fn(r) for r in window_rows) / len(window_rows)
        sig = max(0.0, min(1.0, sig))
        wt = PACING_WINDOW_WEIGHTS[w]
        acc += wt * sig
        total_w += wt
    if total_w <= 0:
        return 1.0
    blended = acc / total_w
    return min(PACING_SIGNAL_TIERS, key=lambda t: abs(t - blended))

def _pacing_coverage_signal(row) -> float:
    return 1.0 - min(1.0, row["mandatory_unsatisfied"] / max(1.0, row["n_workers"] * 3.0))

def _pacing_afford_signal(row) -> float:
    return 1.0 if row["money"] > 0 else 0.0

_orig_build_farm_analysis = build_farm_analysis

def build_farm_analysis_paced(ws, mem):
    _PACING_CURRENT_MEM["mem"] = mem
    pacing = _pacing_get_or_init(mem)
    pacing["last_turn"] = ws.turn_in_episode
    return _orig_build_farm_analysis(ws, mem)

build_farm_analysis = build_farm_analysis_paced

_orig_record_schedule_outcome = RL_FLOORCAP_CONTROLLER.record_schedule_outcome

def _record_schedule_outcome_paced(ws, schedule_plan):
    _orig_record_schedule_outcome(ws, schedule_plan)
    mem = _PACING_CURRENT_MEM["mem"]
    if mem is None:
        return
    pacing = _pacing_get_or_init(mem)
    pacing["history"].append({
        "turn": ws.turn_in_episode,
        "n_workers": 1 + len(ws.hands),
        "mandatory_unsatisfied": len(schedule_plan.mandatory_unsatisfied),
        "money": ws.money,
    })
    cutoff = ws.turn_in_episode - PACING_HISTORY_KEEP_TURNS
    pacing["history"] = [r for r in pacing["history"] if r["turn"] >= cutoff]

RL_FLOORCAP_CONTROLLER.record_schedule_outcome = _record_schedule_outcome_paced

# DEAD CODE REMOVED: compute_optimal_workforce_paced()/_discretionary_cash_paced()
# (Pacing v1), disabled by Pacing v2 and unused -- removed. _orig_compute_optimal_workforce
# is still used later (Part 7g).
_orig_compute_optimal_workforce = compute_optimal_workforce

_orig_plant_throttle_fraction = _plant_throttle_fraction

def _plant_throttle_fraction_paced(saturation_ratio, steepness=None):
    base = _orig_plant_throttle_fraction(saturation_ratio, steepness=steepness)
    mem = _PACING_CURRENT_MEM["mem"]
    if mem is None or "pacing" not in mem:
        return base
    pacing = mem["pacing"]
    turn = pacing.get("last_turn", 0)
    coverage_signal = _pacing_blend_signal(pacing["history"], _pacing_coverage_signal, turn)
    afford_signal = _pacing_blend_signal(pacing["history"], _pacing_afford_signal, turn)
    combined = min(coverage_signal, afford_signal)
    return base * combined

_plant_throttle_fraction = _plant_throttle_fraction_paced

def _task_utility_sticky(candidate, evaluation, worker_pos, marginal_values, scheduling_values,
                          bonus: float = 0.0) -> float:
    return _task_utility(candidate, evaluation, worker_pos, marginal_values, scheduling_values) + bonus

def schedule_workers_paced(plan: CapitalPlan, evaluations: dict, ws: WorldState) -> SchedulePlan:
    mem = _PACING_CURRENT_MEM["mem"]
    commitment = {}
    if mem is not None:
        pacing = _pacing_get_or_init(mem)
        commitment = pacing.get("worker_commitment", {})

    workers = [ws.farmer] + list(ws.hands)
    n_workers = len(workers)

    mandatory = [c for c in plan.purchases
                 if c.action_type in MANDATORY_ACTION_TYPES and c.action_type not in MARKET_ACTION_TYPES]

    def _mandatory_priority(c):
        if c.action_type == "FEED_ANIMAL":
            return -10 - c.meta.get("consecutive_unfed", 0)
        if c.action_type == "PICKUP_FEED_WHEAT":
            return -5
        # CARE_BONUS has no deadline, so it must not outrank WATER (hard
        # 2-miss deadline). Falling back to 0 + stable-sort insertion
        # order is enough to break the tie correctly.
        return 0

    mandatory.sort(key=_mandatory_priority)
    optional = [c for c in plan.purchases
                if c.action_type not in MANDATORY_ACTION_TYPES and c.action_type not in MARKET_ACTION_TYPES]

    assigned_worker_idx = set()
    assignments = {}
    mandatory_unsatisfied = []

    def _bonus_for(wi, c):
        key = commitment.get(wi)
        return PACING_STICKINESS_BONUS if key is not None and key == (c.action_type, c.target) else 0.0

    for c in mandatory:
        if c.required_worker_index is not None:
            wi = c.required_worker_index
            if wi >= n_workers or wi in assigned_worker_idx:
                mandatory_unsatisfied.append(c.id)
                continue
            u = _task_utility_sticky(c, evaluations.get(c.id), _worker_position(workers[wi]),
                                      plan.marginal_values, plan.scheduling_values, _bonus_for(wi, c))
            assignments[wi] = WorkerAssignment(wi, c.id, True, u)
            assigned_worker_idx.add(wi)
            continue

        best_w, best_u = None, None
        for wi in range(n_workers):
            if wi in assigned_worker_idx:
                continue
            u = _task_utility_sticky(c, evaluations.get(c.id), _worker_position(workers[wi]),
                                      plan.marginal_values, plan.scheduling_values, _bonus_for(wi, c))
            if best_u is None or u > best_u:
                best_w, best_u = wi, u
        if best_w is None:
            mandatory_unsatisfied.append(c.id)
        else:
            assignments[best_w] = WorkerAssignment(best_w, c.id, True, best_u)
            assigned_worker_idx.add(best_w)

    remaining_workers = [wi for wi in range(n_workers) if wi not in assigned_worker_idx]
    if remaining_workers and optional:
        util_matrix = []
        for wi in remaining_workers:
            row = []
            for c in optional:
                if c.required_worker_index is not None and c.required_worker_index != wi:
                    row.append(-1e9)
                else:
                    row.append(_task_utility_sticky(c, evaluations.get(c.id), _worker_position(workers[wi]),
                                                      plan.marginal_values, plan.scheduling_values, _bonus_for(wi, c)))
            util_matrix.append(row)

        try:
            import numpy as np
            from scipy.optimize import linear_sum_assignment
            cost_matrix = -np.array(util_matrix, dtype=float)
            row_idx, col_idx = linear_sum_assignment(cost_matrix)
            matched_workers = set()
            for r, c_idx in zip(row_idx, col_idx):
                wi = remaining_workers[r]
                cand = optional[c_idx]
                u = util_matrix[r][c_idx]
                if u > 0:
                    assignments[wi] = WorkerAssignment(wi, cand.id, False, u)
                    matched_workers.add(wi)
            for wi in remaining_workers:
                if wi not in matched_workers:
                    assignments[wi] = WorkerAssignment(wi, None, False, 0.0)
        except ImportError:
            used_tasks = set()
            for wi in remaining_workers:
                best_c, best_u = None, 0.0
                for ci, c in enumerate(optional):
                    if ci in used_tasks:
                        continue
                    if c.required_worker_index is not None and c.required_worker_index != wi:
                        continue
                    u = _task_utility_sticky(c, evaluations.get(c.id), _worker_position(workers[wi]),
                                              plan.marginal_values, plan.scheduling_values, _bonus_for(wi, c))
                    if u > best_u:
                        best_c, best_u = ci, u
                if best_c is not None:
                    assignments[wi] = WorkerAssignment(wi, optional[best_c].id, False, best_u)
                    used_tasks.add(best_c)
                else:
                    assignments[wi] = WorkerAssignment(wi, None, False, 0.0)
    else:
        for wi in remaining_workers:
            assignments[wi] = WorkerAssignment(wi, None, False, 0.0)

    final_assignments = tuple(assignments.get(wi, WorkerAssignment(wi, None, False, 0.0)) for wi in range(n_workers))

    if mem is not None:
        candidates_by_id = {c.id: c for c in plan.purchases}
        new_commitment = {}
        for a in final_assignments:
            if not a.is_mandatory or a.candidate_id is None:
                continue
            c = candidates_by_id.get(a.candidate_id)
            if c is None:
                continue
            target_pos = _task_position(c)
            if target_pos is None:
                continue
            wpos = _worker_position(workers[a.worker_index])
            if wpos != target_pos:
                new_commitment[a.worker_index] = (c.action_type, c.target)
        pacing = _pacing_get_or_init(mem)
        pacing["worker_commitment"] = new_commitment

    return SchedulePlan(assignments=final_assignments, mandatory_unsatisfied=tuple(mandatory_unsatisfied))

schedule_workers = schedule_workers_paced

print("Pacing patch v2 loaded: worker-stickiness + multi-window PLANT gate only. "
      "target_n smoothing and hire cash-reserve (v1's patches #3/#4) are DISABLED -- "
      "traced to a wrong assumption (workforce persists across days; it actually "
      "resets to 1 every day in this game), which was corrupting the reserve calc "
      "and quietly starving PLANT/seed budget. See markdown cell above for the trace.")



ACTIONS_PER_TILE_DEFAULT = 2   

def simulate_worker_route_logged(worker_id, start_pos, task_positions, turns_available,
                                  actions_per_tile=ACTIONS_PER_TILE_DEFAULT, turn_offset=0):
    pos = start_pos
    remaining = list(task_positions)
    turn = turn_offset
    log = []
    while remaining:
        remaining.sort(key=lambda p: _travel_cost(pos, p))
        target = remaining[0]
        travel = _travel_cost(pos, target)
        step_cost = travel + actions_per_tile
        if (turn - turn_offset) + step_cost > turns_available:
            break
        cur = pos
        while cur != target:
            dx = (target[0] > cur[0]) - (target[0] < cur[0])
            dy = (target[1] > cur[1]) - (target[1] < cur[1]) if dx == 0 else 0
            nxt = (cur[0] + dx, cur[1] + dy) if dx != 0 else (cur[0], cur[1] + dy)
            log.append({"turn": turn, "worker": worker_id, "action": "MOVE", "position": nxt})
            turn += 1
            cur = nxt
        for _ in range(actions_per_tile):
            log.append({"turn": turn, "worker": worker_id, "action": "SERVICE", "position": target})
            turn += 1
        pos = target
        remaining.pop(0)
    return {
        "feasible": len(remaining) == 0,
        "turns_used": turn - turn_offset,
        "log": log,
        "remaining": remaining,
        "final_pos": pos,
    }

def _load_balanced_assignment(worker_positions, task_positions, turns_available, actions_per_tile):
    assigned = {i: [] for i in range(len(worker_positions))}
    projected_pos = list(worker_positions)
    projected_turns = [0] * len(worker_positions)

    remaining_tasks = list(task_positions)
    while remaining_tasks:
        best = None  
        for wi in range(len(worker_positions)):
            for ti, t in enumerate(remaining_tasks):
                travel = _travel_cost(projected_pos[wi], t)
                candidate_turns = projected_turns[wi] + travel + actions_per_tile
                if best is None or candidate_turns < best[2]:
                    best = (wi, ti, candidate_turns)
        wi, ti, new_turns = best
        t = remaining_tasks.pop(ti)
        assigned[wi].append(t)
        projected_pos[wi] = t
        projected_turns[wi] = new_turns
    return assigned

def simulate_workforce_routes_v2(worker_positions, task_positions, turns_available,
                                  actions_per_tile=ACTIONS_PER_TILE_DEFAULT):
    assignment = _load_balanced_assignment(worker_positions, task_positions,
                                            turns_available, actions_per_tile)
    results = {}
    all_feasible = True
    full_log = []
    for i, pos in enumerate(worker_positions):
        r = simulate_worker_route_logged(i, pos, assignment[i], turns_available, actions_per_tile)
        results[i] = r
        full_log.extend(r["log"])
        if not r["feasible"]:
            all_feasible = False
    full_log.sort(key=lambda e: (e["turn"], e["worker"]))
    return all_feasible, results, full_log

def compute_workforce_via_simulation_v2(existing_worker_positions, new_hire_spawn_positions,
                                         task_positions, turns_available, max_workers,
                                         actions_per_tile=ACTIONS_PER_TILE_DEFAULT):
    n_existing = len(existing_worker_positions)
    results, full_log = None, None
    for n in range(max(1, n_existing), max_workers + 1):
        extra_needed = n - n_existing
        positions = list(existing_worker_positions) + list(new_hire_spawn_positions[:extra_needed])
        feasible, results, full_log = simulate_workforce_routes_v2(
            positions, task_positions, turns_available, actions_per_tile)
        if feasible:
            return n, results, full_log, True
    return max_workers, results, full_log, False

def _mandatory_task_positions(ws) -> list:
    positions = []
    for x, row in enumerate(ws.tiles):
        for y, t in enumerate(row):
            if t is None:
                positions.append((x, y))  
                continue
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")
            if kind == "PLANT":
                planted_day = t.get("planted_day")
                crop = t.get("crop")
                info = CROP_INFO.get(crop, {})
                maturity_day = info.get("max_yield_day")
                is_mature = (planted_day is not None and maturity_day is not None
                             and ws.day - planted_day >= maturity_day)
                if is_mature or not t.get("watered_today"):
                    positions.append((x, y))
            elif kind in ("COOP", "PASTURE") and t.get("animal"):
                if not t.get("fed_today") or t.get("yield_units", 0) > 0:
                    positions.append((x, y))
    return positions

_orig_compute_optimal_workforce_sim = compute_optimal_workforce

def compute_optimal_workforce_simwired(ws, fa, discretionary_cash, mandatory_future_cost=0.0):
    current_n = 1 + len(ws.hands)
    hires_today_est = len(ws.hands)
    physical_cap_n = 1 + _hand_cap_for_quadrant(ws.n_quadrants, ws.day, ws=ws, fa=fa,
                                                 discretionary_cash=discretionary_cash,
                                                 mandatory_future_cost=mandatory_future_cost) * max(1, ws.n_quadrants)
    max_n = min(1 + MAX_HANDS_SEARCH_CEILING, physical_cap_n)

    task_positions = _mandatory_task_positions(ws)
    if not task_positions:
        return {"target_n": current_n, "backlog": 0, "table": (),
                "reason": "NO_BACKLOG", "seed_reduction_signal": 0.0}

    hours_elapsed_today = ws.turn_in_episode % TURNS_PER_DAY
    turns_available = max(1, TURNS_PER_DAY - hours_elapsed_today)

    existing_positions = [_worker_position(ws.farmer)] + [_worker_position(h) for h in ws.hands]
    spawn_pos = _worker_position(ws.farmer)
    new_hire_positions = [spawn_pos] * max(0, max_n - current_n)

    n_needed, sim_results, full_log, feasible_at_all = compute_workforce_via_simulation_v2(
        existing_positions, new_hire_positions, task_positions, turns_available, max_n)

    real_cash_budget = max(0.0, ws.money - mandatory_future_cost)
    n_affordable = current_n
    for n in range(current_n, n_needed + 1):
        new_hires = n - current_n
        cumulative_cost = sum(_fib_cost(hires_today_est + i) for i in range(new_hires))
        if cumulative_cost <= discretionary_cash or cumulative_cost <= real_cash_budget:
            n_affordable = n
        else:
            break

    target_n = min(n_needed, n_affordable)

    if n_needed <= n_affordable:
        seed_reduction_signal = 0.0 if feasible_at_all else 0.5  
    else:
        shortfall = (n_needed - n_affordable) / max(1, n_needed - current_n + 1)
        seed_reduction_signal = max(0.0, min(1.0, shortfall))

    return {
        "target_n": target_n,
        "target_n_sim_needed": n_needed,
        "target_n_affordable": n_affordable,
        "backlog": len(task_positions),
        "table": (),
        "reason": "SIMULATED",
        "seed_reduction_signal": seed_reduction_signal,
        "sim_log": full_log,   
        "sim_feasible_at_all": feasible_at_all,
    }

compute_optimal_workforce = compute_optimal_workforce_simwired

print("Workforce simulator v2 wired: compute_optimal_workforce now uses load-balanced "
      "route simulation (real positions, per-turn action log) instead of the flat "
      "LAND_UTILIZATION_TILES_PER_DAY rate. Adds `seed_reduction_signal` to the return "
      "dict for future strategy-controller/reward-shaping use (not yet consumed anywhere "
      "-- that wiring into default_strategy_controller/PPO reward is a separate step).")



_orig_compute_optimal_workforce_7d = compute_optimal_workforce

def compute_optimal_workforce_signal_cached(ws, fa, discretionary_cash, mandatory_future_cost=0.0):
    result = _orig_compute_optimal_workforce_7d(ws, fa, discretionary_cash, mandatory_future_cost)
    mem = _PACING_CURRENT_MEM["mem"]
    if mem is not None:
        pacing = _pacing_get_or_init(mem)
        pacing["last_seed_reduction_signal"] = result.get("seed_reduction_signal", 0.0)
    return result

compute_optimal_workforce = compute_optimal_workforce_signal_cached

_orig_plant_throttle_fraction_7d = _plant_throttle_fraction

def _plant_throttle_fraction_with_seed_signal(saturation_ratio, steepness=None):
    base = _orig_plant_throttle_fraction_7d(saturation_ratio, steepness=steepness)
    mem = _PACING_CURRENT_MEM["mem"]
    if mem is None or "pacing" not in mem:
        return base
    signal = mem["pacing"].get("last_seed_reduction_signal", 0.0)
    return base * (1.0 - signal)

_plant_throttle_fraction = _plant_throttle_fraction_with_seed_signal

print("Part 7d: seed_reduction_signal now wired into PLANT throttle "
      "(_plant_throttle_fraction *= (1 - seed_reduction_signal)).")




def build_farm_analysis_paced_v2(ws, mem):
    fa = _orig_build_farm_analysis(ws, mem)
    _PACING_CURRENT_MEM["mem"] = mem
    pacing = _pacing_get_or_init(mem)
    pacing["last_turn"] = ws.turn_in_episode
    pacing["last_ws"] = ws
    pacing["last_fa"] = fa
    return fa

build_farm_analysis = build_farm_analysis_paced_v2

compute_optimal_workforce = _orig_compute_optimal_workforce
_plant_throttle_fraction = _orig_plant_throttle_fraction

PLANT_FEASIBILITY_TEST_TILES = 5

def plant_feasibility_signal(ws: WorldState, mem: dict) -> float:
    if _SIMULATING_FEASIBILITY:
        return 0.0
    pacing = _pacing_get_or_init(mem)
    day_key = ws.day
    cached = pacing.get("_feasibility_signal_day")
    if cached is not None and cached[0] == day_key:
        return cached[1]
    fa = pacing.get("last_fa") or _orig_build_farm_analysis(ws, mem)
    if not fa.empty_tiles:
        signal = 1.0
    else:
        test_tiles = list(fa.empty_tiles)[:PLANT_FEASIBILITY_TEST_TILES]
        n_ok = max_affordable_seeds_v2(ws, mem, test_tiles)
        signal = n_ok / len(test_tiles)
    pacing["_feasibility_signal_day"] = (day_key, signal)
    return signal

print("Part 7g loaded (redesigned): HIRE/PLANT reverted to original formulas. "
      "Part 7f's simulator is now exposed as plant_feasibility_signal(), a "
      "once-per-day feature for RL_FLOORCAP_CONTROLLER -- not a live gate.")


TRANSITION_SMOOTHING_ALPHA = 0.5

def extract_transition_counts(state_sequence: list, states=MARKET_STATE_LEVELS) -> dict:
    counts = {i: {j: 0 for j in states} for i in states}
    for a, b in zip(state_sequence, state_sequence[1:]):
        if a in counts and b in counts[a]:
            counts[a][b] += 1
    return counts

def merge_transition_counts(*count_dicts, states=MARKET_STATE_LEVELS) -> dict:
    merged = {i: {j: 0 for j in states} for i in states}
    for cd in count_dicts:
        for i in cd:
            if i not in merged:
                continue
            for j in cd[i]:
                if j in merged[i]:
                    merged[i][j] += cd[i][j]
    return merged

def build_transition_matrix(counts: dict, alpha: float = TRANSITION_SMOOTHING_ALPHA,
                             states=MARKET_STATE_LEVELS) -> dict:
    n = len(states)
    matrix = {}
    for i in states:
        row_counts = counts.get(i, {j: 0 for j in states})
        total = sum(row_counts.get(j, 0) for j in states) + alpha * n
        matrix[i] = {j: (row_counts.get(j, 0) + alpha) / total for j in states}
    return matrix

def accumulate_transition_counts_from_episodes(mem_list: list, product: str,
                                                 states=MARKET_STATE_LEVELS) -> dict:
    per_episode_counts = []
    for mem in mem_list:
        seq = mem.get("market_state_log", {}).get(product)
        if seq:
            per_episode_counts.append(extract_transition_counts(seq, states=states))
    return merge_transition_counts(*per_episode_counts, states=states) if per_episode_counts \
        else {i: {j: 0 for j in states} for i in states}

MARKET_STATE_FALLBACK_RATIO = {"LOW": 0.65, "NORMAL": 1.0, "HIGH": 1.35}

MARKOV_CONFIDENCE_SATURATION_SAMPLES = 30.0

def _state_representative_prices(mem: dict, product: str, base: float,
                                   states=MARKET_STATE_LEVELS) -> dict:
    state_log = mem.get("market_state_log", {}).get(product, [])
    price_log = mem.get("market_price_log", {}).get(product, [])
    sums = {s: 0.0 for s in states}
    counts = {s: 0 for s in states}
    for s, p in zip(state_log, price_log):
        if s in sums:
            sums[s] += p
            counts[s] += 1
    result = {}
    for s in states:
        if counts[s] > 0:
            result[s] = sums[s] / counts[s]
        else:
            result[s] = MARKET_STATE_FALLBACK_RATIO.get(s, 1.0) * (base if base else 1.0)
    return result

def _one_hot_state_distribution(state: str, states=MARKET_STATE_LEVELS) -> dict:
    return {s: (1.0 if s == state else 0.0) for s in states}

def _step_distribution(dist: dict, matrix: dict, states=MARKET_STATE_LEVELS) -> dict:
    return {j: sum(dist.get(i, 0.0) * matrix[i][j] for i in states) for j in states}

def _row_total_count(counts: dict, state: str, states=MARKET_STATE_LEVELS) -> float:
    row = counts.get(state, {})
    return float(sum(row.get(j, 0) for j in states))

def markov_forecast_confidence(counts: dict, current_state: str, horizon_step: int) -> float:
    row_total = _row_total_count(counts, current_state)
    data_confidence = min(1.0, row_total / MARKOV_CONFIDENCE_SATURATION_SAMPLES)
    horizon_discount = max(0.2, 1.0 - 0.15 * horizon_step)
    return round(max(0.05, data_confidence * horizon_discount), 4)

def markov_forecast_market_prices(ws: WorldState, mem: dict, transition_matrices: dict,
                                   transition_counts: Optional[dict] = None,
                                   horizon: int = 3) -> dict:
    transition_counts = transition_counts or {}
    forecasts = {}
    for product, price in ws.prices.items():
        matrix = transition_matrices.get(product)
        if matrix is None:
            continue
        base = MARKET_PARAMS.get(product, {}).get("base", price)
        current_state = classify_price_state(product, price)
        rep_prices = _state_representative_prices(mem, product, base)
        counts = transition_counts.get(product, {})

        by_offset = {}
        confidences = []
        dist = _one_hot_state_distribution(current_state)
        for d in range(1, horizon + 1):
            dist = _step_distribution(dist, matrix)
            expected_price = sum(dist[s] * rep_prices[s] for s in MARKET_STATE_LEVELS)
            by_offset[d] = expected_price
            confidences.append(markov_forecast_confidence(counts, current_state, d))

        forecasts[product] = PriceForecast(
            product=product, current_price=price, forecast_by_day_offset=by_offset,
            confidence=confidences[0] if confidences else 0.2,   
        )
    return forecasts

def markov_forecast_market_prices_v2(ws: WorldState, mem: dict, transition_matrices: dict,
                                       return_matrices: dict,
                                       transition_counts: Optional[dict] = None,
                                       horizon: int = 3) -> dict:
    transition_counts = transition_counts or {}
    forecasts = {}
    for product, price in ws.prices.items():
        matrix = transition_matrices.get(product)
        ret_matrix = return_matrices.get(product)
        if matrix is None or ret_matrix is None:
            continue
        current_state = classify_price_state(product, price)
        counts = transition_counts.get(product, {})

        by_offset = {}
        confidences = []
        dist = _one_hot_state_distribution(current_state)
        price_d = price
        for d in range(1, horizon + 1):
            expected_return = sum(
                dist.get(i, 0.0) * sum(matrix[i][j] * ret_matrix[i][j] for j in MARKET_STATE_LEVELS)
                for i in MARKET_STATE_LEVELS
            )
            price_d = price_d * (1.0 + expected_return)
            by_offset[d] = price_d
            dist = _step_distribution(dist, matrix)
            confidences.append(markov_forecast_confidence(counts, current_state, d))

        forecasts[product] = PriceForecast(
            product=product, current_price=price, forecast_by_day_offset=by_offset,
            confidence=confidences[0] if confidences else 0.2,
        )
    return forecasts

def _log_loss_for_transition(matrix: dict, actual_from: str, actual_to: str,
                               eps: float = 1e-9) -> float:
    p = matrix.get(actual_from, {}).get(actual_to, eps)
    p = max(p, eps)
    return -math.log(p)

def _brier_score_for_transition(matrix: dict, actual_from: str, actual_to: str,
                                  states=MARKET_STATE_LEVELS) -> float:
    row = matrix.get(actual_from, {})
    return sum((row.get(j, 0.0) - (1.0 if j == actual_to else 0.0)) ** 2 for j in states)

def backtest_markov_calibration(holdout_sequences: list, matrix: dict,
                                  states=MARKET_STATE_LEVELS) -> dict:
    n = len(states)
    uniform_matrix = {i: {j: 1.0 / n for j in states} for i in states}
    persistence_matrix = {i: {j: (1.0 if j == i else 0.0) for j in states} for i in states}

    totals = {
        "matrix": {"log_loss": 0.0, "brier": 0.0},
        "uniform": {"log_loss": 0.0, "brier": 0.0},
        "persistence": {"log_loss": 0.0, "brier": 0.0},
    }
    n_transitions = 0
    for seq in holdout_sequences:
        for a, b in zip(seq, seq[1:]):
            if a not in states or b not in states:
                continue
            n_transitions += 1
            totals["matrix"]["log_loss"] += _log_loss_for_transition(matrix, a, b)
            totals["matrix"]["brier"] += _brier_score_for_transition(matrix, a, b, states=states)
            totals["uniform"]["log_loss"] += _log_loss_for_transition(uniform_matrix, a, b)
            totals["uniform"]["brier"] += _brier_score_for_transition(uniform_matrix, a, b, states=states)
            totals["persistence"]["log_loss"] += _log_loss_for_transition(persistence_matrix, a, b)
            totals["persistence"]["brier"] += _brier_score_for_transition(persistence_matrix, a, b, states=states)

    result = {"n_transitions": n_transitions}
    for key, agg in totals.items():
        if n_transitions > 0:
            result[f"{key}_log_loss"] = agg["log_loss"] / n_transitions
            result[f"{key}_brier"] = agg["brier"] / n_transitions
        else:
            result[f"{key}_log_loss"] = None
            result[f"{key}_brier"] = None
    if n_transitions > 0:
        result["beats_uniform"] = result["matrix_log_loss"] < result["uniform_log_loss"]
        result["beats_persistence"] = result["matrix_log_loss"] < result["persistence_log_loss"]
    else:
        result["beats_uniform"] = None
        result["beats_persistence"] = None
    return result

@dataclass(frozen=True)
class PriceForecast:
    product: str
    current_price: float
    forecast_by_day_offset: dict     
    confidence: float                

@dataclass(frozen=True)
class OpponentBelief:
    money_estimate: float
    land_estimate: int
    animal_estimate: int
    aggressiveness: float          
    uncertainty: float             

OPPONENT_BELIEF_WINDOW_DAYS = 10

OPPONENT_AGGRESSIVENESS_GROWTH_RATE = 0.05

def estimate_opponent_belief(ws: WorldState, mem: dict) -> OpponentBelief:
    last_logged_day = mem.get("_opp_belief_last_logged_day", -1)
    history = mem.setdefault("opp_money_history", [])
    if ws.day != last_logged_day:
        mem["_opp_belief_last_logged_day"] = ws.day
        history.append(ws.opp_money)
        if len(history) > OPPONENT_BELIEF_WINDOW_DAYS:
            history.pop(0)

    if len(history) >= 2:
        span_days = len(history) - 1
        baseline = max(1.0, abs(history[0]))   
        growth_rate_per_day = (history[-1] - history[0]) / baseline / span_days
        aggressiveness = max(0.0, min(1.0, growth_rate_per_day / OPPONENT_AGGRESSIVENESS_GROWTH_RATE))
    else:
        aggressiveness = 0.5   

    uncertainty = max(0.1, 1.0 - len(history) / OPPONENT_BELIEF_WINDOW_DAYS)

    return OpponentBelief(
        money_estimate=ws.opp_money,
        land_estimate=ws.opp_land,
        animal_estimate=ws.opp_animals,
        aggressiveness=aggressiveness,
        uncertainty=uncertainty,
    )

OPP_CROP_PRESSURE_NORM = 10

OPP_CROP_GROWTH_BONUS_MAX = 0.3

def estimate_opponent_crop_pressure(ws: WorldState, mem: dict) -> dict:
    history = mem.setdefault("opp_crop_count_history", {})   
    last_logged_day = mem.get("_opp_crop_pressure_last_logged_day", -1)
    if ws.day != last_logged_day:
        mem["_opp_crop_pressure_last_logged_day"] = ws.day
        for crop, count in ws.opp_crop_counts.items():
            h = history.setdefault(crop, [])
            h.append((ws.day, count))
            if len(h) > OPPONENT_BELIEF_WINDOW_DAYS:
                h.pop(0)

    pressure = {}
    for crop, h in history.items():
        if not h:
            continue
        current = h[-1][1]
        base = min(1.0, current / OPP_CROP_PRESSURE_NORM)
        growth_bonus = 0.0
        if len(h) >= 2:
            span_days = max(1, h[-1][0] - h[0][0])
            growth_rate_per_day = (h[-1][1] - h[0][1]) / span_days
            if growth_rate_per_day > 0:
                growth_bonus = min(OPP_CROP_GROWTH_BONUS_MAX,
                                    (growth_rate_per_day / OPP_CROP_PRESSURE_NORM) * OPP_CROP_GROWTH_BONUS_MAX * 10)
        pressure[crop] = min(1.0, base + growth_bonus)
    return pressure

SEASON_RAMP_START_DAY = 0

SEASON_RAMP_FULL_DAY = 10

def _season_progress_ramp(ws: WorldState) -> float:
    if ws.day <= SEASON_RAMP_START_DAY:
        return 0.0
    if ws.day >= SEASON_RAMP_FULL_DAY:
        return 1.0
    span = SEASON_RAMP_FULL_DAY - SEASON_RAMP_START_DAY
    linear = (ws.day - SEASON_RAMP_START_DAY) / span
    return linear * linear

def apply_market_intelligence(evaluations: dict, forecast: Optional[dict],
                               opponent_belief: Optional[OpponentBelief],
                               ws: Optional[WorldState] = None) -> dict:
    return evaluations

SELL_FRACTION_TIERS = tuple(round(x * 0.05, 2) for x in range(1, 21))

SELL_FRACTION_BY_PRICE_STATE = {"LOW": 0.4, "NORMAL": 0.6, "HIGH": 1.0}

SELL_FRACTION_TREND_THRESHOLD = 0.05

SELL_FRACTION_TREND_ADJ = 0.2

SELL_FRACTION_OPPONENT_ADJ_MAX = 0.2

def _snap_to_sell_tier(fraction: float) -> float:
    return min(SELL_FRACTION_TIERS, key=lambda t: abs(t - fraction))

def compute_sell_fraction(product: str, ws: WorldState,
                           forecast: Optional[dict] = None,
                           opponent_belief: Optional[OpponentBelief] = None,
                           opponent_crop_pressure: Optional[dict] = None) -> float:
    price_state = classify_price_state(product, ws.prices.get(product, 0.0))
    fraction = SELL_FRACTION_BY_PRICE_STATE[price_state]

    if forecast is not None and product in forecast:
        f = forecast[product]
        current = ws.prices.get(product, 0.0)
        future = f.forecast_by_day_offset.get(1, current)
        if current > 0:
            trend = (future - current) / current
            if trend > SELL_FRACTION_TREND_THRESHOLD:
                fraction -= SELL_FRACTION_TREND_ADJ * f.confidence   
            elif trend < -SELL_FRACTION_TREND_THRESHOLD:
                fraction += SELL_FRACTION_TREND_ADJ * f.confidence   

    if opponent_crop_pressure is not None and product in opponent_crop_pressure:
        fraction += SELL_FRACTION_OPPONENT_ADJ_MAX * opponent_crop_pressure[product]
    elif opponent_belief is not None:
        confidence = 1.0 - opponent_belief.uncertainty
        fraction += SELL_FRACTION_OPPONENT_ADJ_MAX * opponent_belief.aggressiveness * confidence

    fraction = max(0.05, min(1.0, fraction))
    return _snap_to_sell_tier(fraction)

def compute_sell_fractions(ws: WorldState, forecast: Optional[dict] = None,
                            opponent_belief: Optional[OpponentBelief] = None,
                            opponent_crop_pressure: Optional[dict] = None) -> dict:
    return {
        product: compute_sell_fraction(product, ws, forecast, opponent_belief, opponent_crop_pressure)
        for product in ws.shed if product in MARKET_PARAMS and ws.shed.get(product, 0) > 0
    }

@dataclass(frozen=True)
class StrategyConfig:
    investment_budget_fraction: float = 1.0   
    risk_aversion: float = 0.5                
    livestock_bias: float = 0.0               
    farming_bias: float = 0.0                 
    expansion_bias: float = 0.0               
    crop_bias: Optional[dict] = None           
    animal_bias: Optional[dict] = None         
    animal_allocation_ratio: Optional[float] = None

DEFAULT_STRATEGY_CONFIG = StrategyConfig()

def _project_category(project_id: str) -> str:
    if project_id in ("GOOSE_ECONOMY", "COW_ECONOMY", "SHEEP_ECONOMY"):
        return "LIVESTOCK"
    if project_id in ("CROP_PROJECT",):
        return "FARMING"
    if project_id in ("LAND_EXPANSION",):
        return "EXPANSION"
    return "OTHER"

OPPONENT_STRATEGY_BIAS_MAX = 0.4

OPPONENT_BUDGET_TIGHTEN_MAX = 0.95

def default_strategy_controller(ws: WorldState, opponent_belief: Optional[OpponentBelief] = None) -> StrategyConfig:
    if ws.remaining_days <= 3:
        risk_aversion, investment_budget_fraction = 0.9, 0.4      
    elif ws.remaining_days <= 8:
        risk_aversion, investment_budget_fraction = 0.6, 0.7
    else:
        risk_aversion, investment_budget_fraction = 0.3, 1.0

    farming_bias = 0.0
    livestock_bias = 0.0
    if opponent_belief is not None:
        ramp = _season_progress_ramp(ws)
        confidence = 1.0 - opponent_belief.uncertainty
        signal = opponent_belief.aggressiveness * confidence * ramp
        magnitude = OPPONENT_STRATEGY_BIAS_MAX * signal
        farming_bias, livestock_bias = magnitude, -magnitude

        tighten = 1.0 - OPPONENT_BUDGET_TIGHTEN_MAX * signal
        investment_budget_fraction = max(0.05, investment_budget_fraction * tighten)

    return StrategyConfig(
        investment_budget_fraction=investment_budget_fraction,
        risk_aversion=risk_aversion,
        livestock_bias=livestock_bias,
        farming_bias=farming_bias,
        expansion_bias=0.0,
    )

def _strategy_rank_multiplier(candidate: "Candidate", evaluation, strategy: StrategyConfig) -> float:
    category = _project_category(candidate.project_id)
    bias = strategy.livestock_bias if category == "LIVESTOCK" else \
        strategy.farming_bias if category == "FARMING" else \
        strategy.expansion_bias if category == "EXPANSION" else 0.0
    risk = evaluation.risk if evaluation is not None else 0.0
    risk_penalty = 1.0 - strategy.risk_aversion * risk
    prod_mult = 1.0
    if candidate.action_type == "PLANT":
        crop = candidate.meta.get("crop")
        if strategy.crop_bias is not None and crop in strategy.crop_bias:
            prod_mult = max(0.1, 1.0 + strategy.crop_bias[crop])
    animal_mult = 1.0
    if candidate.action_type == "BUY_ANIMAL":
        species = PROJECT_ANIMAL.get(candidate.project_id)
        if strategy.animal_bias is not None and species in strategy.animal_bias:
            animal_mult = max(0.1, 1.0 + strategy.animal_bias[species])
    return max(0.05, 1.0 + bias) * max(0.05, risk_penalty) * max(0.1, prod_mult) * max(0.1, animal_mult)

def _market_opportunity_multiplier(candidate: "Candidate", market_opportunity: Optional[dict],
                                    weight: float = 0.4) -> float:
    if market_opportunity is None:
        return 1.0
    crop = candidate.meta.get("crop")
    if crop is None or crop not in market_opportunity:
        return 1.0
    snapshots = market_opportunity[crop]
    if not snapshots:
        return 1.0
    target_offset = max(0, min(candidate.duration, len(snapshots) - 1))
    score = snapshots[target_offset].opportunity_score
    if score is None:
        return 1.0
    return max(0.3, 1.0 + weight * score)

_SHOP_DEMAND_COUNT = {}
for _shop, _items in SHOP_DEMAND.items():
    for _it in _items:
        _SHOP_DEMAND_COUNT[_it] = _SHOP_DEMAND_COUNT.get(_it, 0) + 1

_ABOVE_STEEPNESS = {"log": 0.2, "sqrt": 0.5, "linear": 1.0, "sq": 2.0}
_MAX_STEEPNESS = max(
    _ABOVE_STEEPNESS.get(p.get("above", ("linear", 1.0))[0], 1.0) * p.get("above", ("linear", 1.0))[1]
    for p in MARKET_PARAMS.values()
) or 1.0

TOWN_SHOP_SELL_INTERVAL = 4   

def _shop_demand_multiplier(candidate: "Candidate", ws: "WorldState",
                             ev: Optional["InvestmentEvaluation"] = None,
                             crash_cap: float = 0.20) -> float:
    crop = candidate.meta.get("crop")
    if crop is None or crop not in CROP_INFO:
        return 1.0

    unlocked_instances = list(getattr(ws, "unlocked_shops", ()) or ())
    demand_count = sum(SHOP_DEMAND.get(s, []).count(crop) for s in unlocked_instances)

    product = crop  
    price = (ws.prices or {}).get(product, CROP_INFO[crop].get("base_price", 0.0))
    remaining_days = max(0, getattr(ws, "remaining_days", SEASON_DAYS))
    horizon_days = max(1, min(candidate.duration, remaining_days))
    horizon_turns = horizon_days * TURNS_PER_DAY
    demand_pull_units = demand_count * (horizon_turns / TOWN_SHOP_SELL_INTERVAL)
    own_supply_units = CROP_INFO[crop].get("max_yield", 1)
    absorbed_units = min(demand_pull_units, own_supply_units)
    demand_bonus_dollars = absorbed_units * price

    base_profit = abs(ev.expected_profit) if (ev is not None and ev.expected_profit) else max(candidate.cost, 1.0)
    ratio = demand_bonus_dollars / base_profit
    demand_mult = 1.0 + 2.0 * math.tanh(ratio / 2.0)

    params = MARKET_PARAMS.get(crop, {})
    above_kind, above_coef = params.get("above", ("linear", 1.0))
    steepness = _ABOVE_STEEPNESS.get(above_kind, 1.0) * above_coef
    remaining_ratio = max(0.0, min(1.0, remaining_days / SEASON_DAYS))
    crash_mult = max(0.4, 1.0 - crash_cap * remaining_ratio * (steepness / _MAX_STEEPNESS))

    return demand_mult * crash_mult

try:
    import torch as _torch
    import torch.nn as _nn
    import torch.nn.functional as _F
    _TORCH_AVAILABLE = True
except ImportError as _e:
    _TORCH_AVAILABLE = False
    print(f"[warn] torch unavailable ({_e}); greedy/frozen-RL path is unaffected, "
          "but any Stage-1+ PPO cell will raise ImportError if run.")

_STRUCTURE_COST = {"COOP": 150.0, "PASTURE": 200.0}

def _estimate_land_value(n_quadrants: int) -> float:
    return sum(LAND_COST_BY_OWNED_QUADRANTS.get(q, 0.0) for q in range(1, n_quadrants))

def _estimate_net_worth(ws: WorldState) -> float:
    shed_value = sum(ws.shed.get(p, 0) * ws.prices.get(p, 0.0) for p in ws.shed)
    land_value = _estimate_land_value(ws.n_quadrants)
    structure_value = ws.n_coop * _STRUCTURE_COST["COOP"] + ws.n_pasture * _STRUCTURE_COST["PASTURE"]
    animal_value = sum(ws.animal_counts.get(sp, 0) * ANIMAL_INFO[sp]["cost"] for sp in ANIMAL_INFO)
    return ws.money + shed_value + land_value + structure_value + animal_value

def select_validated_transition_matrices(validation_results: dict,
                                          require_beats_persistence: bool = True) -> dict:
    selected = {}
    for product, r in validation_results.items():
        b = r["backtest"]
        if b["beats_uniform"] is not True:
            continue
        if require_beats_persistence and b["beats_persistence"] is not True:
            continue
        selected[product] = r["matrix"]
    return selected

def select_validated_transition_counts(validation_results: dict,
                                        require_beats_persistence: bool = True) -> dict:
    selected = {}
    for product, r in validation_results.items():
        b = r["backtest"]
        if b["beats_uniform"] is not True:
            continue
        if require_beats_persistence and b["beats_persistence"] is not True:
            continue
        selected[product] = r["counts"]
    return selected

def run_turn(ws: WorldState, mem: dict, strategy: Optional["StrategyConfig"] = None,
             transition_matrices: Optional[dict] = None,
             transition_counts: Optional[dict] = None,
             opponent_belief_input: Optional["OpponentBelief"] = None,
             use_sell_fraction: bool = False,
             return_matrices: Optional[dict] = None):
    log_market_state(ws, mem)   
    fa = build_farm_analysis(ws, mem)
    strategy = strategy or default_strategy_controller(ws, opponent_belief_input)
    _mandatory_backlog_tasks = _estimate_daily_action_backlog(ws, discretionary_cash=float("inf"))["mandatory"]
    mandatory_future_cost = _mandatory_backlog_tasks * LABOR_COST_PER_TASK
    batch = generate_candidates(ws, fa, mem, mandatory_future_cost=mandatory_future_cost)
    evaluations = evaluate_all_candidates(batch, ws)

    forecast = None
    if transition_matrices or opponent_belief_input is not None:
        if transition_matrices and return_matrices:
            forecast = markov_forecast_market_prices_v2(ws, mem, transition_matrices, return_matrices,
                                                          transition_counts)
        elif transition_matrices:
            forecast = markov_forecast_market_prices(ws, mem, transition_matrices, transition_counts)
        evaluations = apply_market_intelligence(evaluations, forecast, opponent_belief_input, ws=ws)

    sell_fractions = None
    if use_sell_fraction:
        opponent_crop_pressure = estimate_opponent_crop_pressure(ws, mem)
        sell_fractions = compute_sell_fractions(ws, forecast, opponent_belief_input, opponent_crop_pressure)

    capital_plan = optimize_capital(batch, evaluations, ws, strategy=strategy)
    schedule_plan = schedule_workers(capital_plan, evaluations, ws)
    if RL_FLOORCAP_CONTROLLER is not None:
        RL_FLOORCAP_CONTROLLER.record_schedule_outcome(ws, schedule_plan)
    env_action = build_env_action(schedule_plan, batch, ws, mem, capital_plan=capital_plan,
                                   sell_fractions=sell_fractions)
    return env_action, schedule_plan, capital_plan

def make_safe_agent(agent_fn):
    def safe_agent(obs, config=None):
        try:
            return agent_fn(obs, config)
        except Exception as e:
            import traceback
            print("=== V2 AGENT CRASHED ===")
            traceback.print_exc()
            try:
                farms = obs.get("farms", [])
                player = obs.get("player", 0)
                me = farms.get(player, {}) if isinstance(farms, dict) else farms[player]
                n_hands = len(me.get("hands", []))
            except Exception:
                n_hands = 0
            return {"farmer": ["PASS"], "hands": [["PASS"]] * n_hands, "market": []}
    if hasattr(agent_fn, "mem"):
        safe_agent.mem = agent_fn.mem
    return safe_agent

OPPONENT_MODES = ("off", "risk_only", "strategy_only", "both")

def make_agent(strategy_fn=None, safe=True, transition_matrices=None, use_opponent_belief=False,
                opponent_mode: str = "both", use_sell_fraction: bool = False,
                return_matrices=None):
    if opponent_mode not in OPPONENT_MODES:
        raise ValueError(f"opponent_mode must be one of {OPPONENT_MODES}, got {opponent_mode!r}")

    mem = {
        "weed_age": {},
        "own_planted_day": {},
        "completed_project_steps": {},
        "failure_count": {},
    }
    strat_fn = strategy_fn or default_strategy_controller

    def agent(obs, config=None):
        ws = build_world_state(obs)
        opponent_belief = estimate_opponent_belief(ws, mem) if use_opponent_belief else None
        strategy_belief = opponent_belief if opponent_mode in ("strategy_only", "both") else None
        risk_belief = opponent_belief if opponent_mode in ("risk_only", "both") else None

        strategy = strat_fn(ws) if strategy_fn else default_strategy_controller(ws, strategy_belief)
        env_action, _schedule_plan, _capital_plan = run_turn(
            ws, mem, strategy=strategy, transition_matrices=transition_matrices,
            opponent_belief_input=risk_belief, use_sell_fraction=use_sell_fraction,
            return_matrices=return_matrices,
        )
        return env_action

    agent.mem = mem   
    return make_safe_agent(agent) if safe else agent

import random as _random

try:
    from kaggle_environments import make as _kaggle_make
    HAVE_KAGGLE_ENV = True
except ImportError:
    HAVE_KAGGLE_ENV = False

N_EPISODES_DEFAULT = 10

EPISODE_STEPS_DEFAULT = SEASON_DAYS * TURNS_PER_DAY

def run_markov_self_play_validation(n_episodes=N_EPISODES_DEFAULT,
                                     episode_steps=EPISODE_STEPS_DEFAULT,
                                     products=None, verbose=True):
    if not HAVE_KAGGLE_ENV:
        raise RuntimeError(
            "kaggle_environments is not installed in this environment. Run "
            "`pip install kaggle_environments` first."
        )
    products = products or PRICE_RATIO_ITEMS

    episode_mems = []
    for ep in range(n_episodes):
        agent_a = make_agent(safe=True)
        agent_b = make_agent(safe=True)   
        seed = _random.randint(0, 10**6)
        env = _kaggle_make("kaggriculture",
                            configuration={"episodeSteps": episode_steps, "seed": seed},
                            debug=False)
        env.run([agent_a, agent_b])
        episode_mems.append(agent_a.mem)
        episode_mems.append(agent_b.mem)
        if verbose:
            print(f"self-play episode {ep:2d}/{n_episodes} done (seed={seed})")

    split_idx = (len(episode_mems) + 1) // 2
    train_mems, holdout_mems = episode_mems[:split_idx], episode_mems[split_idx:]

    results = {}
    for product in products:
        train_counts = accumulate_transition_counts_from_episodes(train_mems, product)
        matrix = build_transition_matrix(train_counts)
        holdout_sequences = [
            m.get("market_state_log", {}).get(product, []) for m in holdout_mems
        ]
        backtest = backtest_markov_calibration(holdout_sequences, matrix)
        results[product] = {
            "matrix": matrix, "counts": train_counts, "backtest": backtest,
            "train_episodes": len(train_mems), "holdout_episodes": len(holdout_mems),
        }
        if verbose:
            b = backtest
            status = "LOLOS" if (b["beats_uniform"] and b["beats_persistence"]) else \
                     ("SEBAGIAN" if b["beats_uniform"] or b["beats_persistence"] else "GAGAL")
            print(f"\n[{product}] n_transitions(holdout)={b['n_transitions']}")
            print(f"  matrix_log_loss={b['matrix_log_loss']!s:>8}  "
                  f"uniform={b['uniform_log_loss']!s:>8}  persistence={b['persistence_log_loss']!s:>8}")
            print(f"  beats_uniform={b['beats_uniform']}  beats_persistence={b['beats_persistence']}  -> {status}")

    if verbose:
        n_ready = sum(1 for r in results.values()
                      if r["backtest"]["beats_uniform"] and r["backtest"]["beats_persistence"])
        print(f"\n=== Markov validation summary ({len(products)} products) ===")
        print(f"products passing (beats uniform & persistence): {n_ready}/{len(products)}")
        print("Note: with few holdout transitions (few episodes), treat this as "
              "indicative, not final -- raise n_episodes before trusting a "
              "borderline product's matrix.")
    return results

SELL_STATE_DIM = 10

SELL_ACTION_GRID = SELL_FRACTION_TIERS

def build_sell_state(product: str, ws: WorldState,
                      forecast: Optional[dict] = None,
                      opponent_belief: Optional[OpponentBelief] = None,
                      opponent_crop_pressure: Optional[dict] = None) -> "np.ndarray":
    current_price = ws.prices.get(product, 0.0)
    price_state = classify_price_state(product, current_price)
    price_state_val = {"LOW": -1.0, "NORMAL": 0.0, "HIGH": 1.0}.get(price_state, 0.0)

    trend = 0.0
    confidence = 0.0
    if forecast is not None and product in forecast:
        f = forecast[product]
        future = f.forecast_by_day_offset.get(1, current_price)
        if current_price > 0:
            trend = math.tanh((future - current_price) / current_price)
        confidence = f.confidence

    if opponent_crop_pressure is not None and product in opponent_crop_pressure:
        opp_pressure = opponent_crop_pressure[product]
        opp_is_per_crop = 1.0
    elif opponent_belief is not None:
        opp_pressure = opponent_belief.aggressiveness * (1.0 - opponent_belief.uncertainty)
        opp_is_per_crop = 0.0
    else:
        opp_pressure = 0.0
        opp_is_per_crop = 0.0

    qty_shed = ws.shed.get(product, 0)
    base = MARKET_PARAMS.get(product, {}).get("base", 1) or 1

    return np.array([
        price_state_val,
        math.tanh((current_price / base) - 1.0),
        trend,
        confidence,
        opp_pressure,
        opp_is_per_crop,
        math.tanh(qty_shed / 50.0),
        ws.day / SEASON_DAYS,
        ws.remaining_days / SEASON_DAYS,
        math.tanh(ws.money / 2000.0),
    ], dtype=np.float32)

class SellFractionPolicy(_nn.Module):
    def __init__(self, state_dim, n_bins, hidden=64):
        super().__init__()
        self.trunk = _nn.Sequential(
            _nn.Linear(state_dim, hidden), _nn.ReLU(),
            _nn.Linear(hidden, hidden), _nn.ReLU(),
        )
        self.actor = _nn.Linear(hidden, n_bins)
        self.critic = _nn.Sequential(
            _nn.Linear(hidden, hidden // 2), _nn.ReLU(),
            _nn.Linear(hidden // 2, 1),
        )

    def forward(self, x):
        h = self.trunk(x)
        return self.actor(h), self.critic(h)

class PPOSellFractionController:

    def __init__(self, lr=3e-4, epsilon=0.2, batch_size=128, gamma=0.97, entropy_coef=0.02,
                 entropy_coef_min=0.002, entropy_decay_updates=300,
                 action_grid: Optional[tuple] = None, state_dim: Optional[int] = None):
        self.state_dim = state_dim or SELL_STATE_DIM
        self.epsilon = epsilon
        self.batch_size = batch_size
        self.gamma = gamma
        # FIX (entropy plateau, same cause as PPOStrategyController): entropy_coef
        # was a fixed constant, so the exploration bonus never tapered off no
        # matter how many episodes/updates ran. Mirrors that controller's decay.
        self.entropy_coef = entropy_coef
        self.entropy_coef_start = entropy_coef
        self.entropy_coef_min = entropy_coef_min
        self.entropy_decay_updates = entropy_decay_updates
        self.entropy_coef_history = []
        self.buffer = []
        self.entropy_history = []
        self.action_grid = tuple(action_grid) if action_grid is not None else SELL_ACTION_GRID
        n_bins = len(self.action_grid)
        self.policy = SellFractionPolicy(state_dim=self.state_dim, n_bins=n_bins)
        self.old_policy = SellFractionPolicy(state_dim=self.state_dim, n_bins=n_bins)
        self.old_policy.load_state_dict(self.policy.state_dict())
        self.optimizer = _torch.optim.Adam(self.policy.parameters(), lr=lr)

    def select(self, state: "np.ndarray", greedy: bool = False):
        with _torch.no_grad():
            st = _torch.from_numpy(state).unsqueeze(0)
            logits, value = self.old_policy(st)
            logits = logits.squeeze(0)
            dist = _torch.distributions.Categorical(logits=logits)
            action = logits.argmax() if greedy else dist.sample()
            log_prob = float(dist.log_prob(action).item())
        idx = int(action.item())
        return self.action_grid[idx], idx, log_prob, float(value.item())

    def record(self, state, action_idx, log_prob, value, reward, done):
        self.buffer.append(dict(state=state, action_idx=action_idx, log_prob=log_prob,
                                 value=value, reward=reward, done=done))
        if len(self.buffer) >= self.batch_size:
            self._update()
            self.buffer = []

    def _rewards_to_go(self):
        rtg, R = [], 0.0
        last = self.buffer[-1]
        if not last["done"]:
            with _torch.no_grad():
                st = _torch.from_numpy(last["state"]).unsqueeze(0)
                _, v = self.old_policy(st)
            R = float(v.item())
        for tr in reversed(self.buffer):
            if tr["done"]:
                R = 0.0
            R = tr["reward"] + self.gamma * R
            rtg.insert(0, R)
        return rtg

    def _current_entropy_coef(self) -> float:
        n_upd = len(self.entropy_history)
        frac = min(1.0, n_upd / max(1, self.entropy_decay_updates))
        return self.entropy_coef_start + (self.entropy_coef_min - self.entropy_coef_start) * frac

    def _update(self):
        self.entropy_coef = self._current_entropy_coef()
        self.entropy_coef_history.append(self.entropy_coef)
        rtg = self._rewards_to_go()

        states = _torch.from_numpy(np.stack([t["state"] for t in self.buffer]))
        actions = _torch.tensor([t["action_idx"] for t in self.buffer], dtype=_torch.long)
        old_log_probs = _torch.tensor([t["log_prob"] for t in self.buffer], dtype=_torch.float32)
        rewards_tensor = _torch.tensor(rtg, dtype=_torch.float32)

        with _torch.no_grad():
            _, values = self.old_policy(states)
        values = values.squeeze(-1)
        advantages = rewards_tensor - values
        if advantages.std() > 1e-6:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        for _ in range(4):
            logits, new_values = self.policy(states)
            dist = _torch.distributions.Categorical(logits=logits)
            log_probs = dist.log_prob(actions)
            ratio = _torch.exp(log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = _torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * advantages
            actor_loss = -_torch.min(surr1, surr2).mean()
            critic_loss = _F.mse_loss(new_values.squeeze(-1), rewards_tensor)
            entropy_mean = dist.entropy().mean()
            loss = actor_loss + 0.5 * critic_loss - self.entropy_coef * entropy_mean

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        self.old_policy.load_state_dict(self.policy.state_dict())
        self.entropy_history.append(float(entropy_mean.item()))

    def _entropy_convergence(self, n_last: int = 3, ratio_threshold: float = 0.9) -> dict:
        n_bins = len(self.action_grid)
        max_entropy = float(np.log(n_bins))
        if not self.entropy_history:
            return {"mean_entropy": None, "max_entropy": max_entropy, "ratio": None,
                    "converged": False, "n_updates_total": 0}
        recent = self.entropy_history[-n_last:]
        mean_ent = float(np.mean(recent))
        ratio = mean_ent / max_entropy if max_entropy > 0 else 0.0
        return {"mean_entropy": mean_ent, "max_entropy": max_entropy, "ratio": ratio,
                "converged": ratio < ratio_threshold, "n_updates_total": len(self.entropy_history)}

# FIX (opponent diversity): previously no stage call ever passed an
# explicit opponent_pool -- RL only ever faced 1 frozen baseline (overfit).
# Fix: 2 new opponent playstyles (different StrategyConfig bias) for variety.
TRAINING_WIN_BONUS_WEIGHT = 0.5   # FIX (reward metric): see run_training_episode / train_production_priority_v2

# FIX (reward metric, part 3): part-2's pre-squash win-bonus still got swamped
# by net_worth noise and conflated "won/lost" with "got a generous seed". Now
# win/loss is a fixed-magnitude term added AFTER each controller's tanh squash.
RL_WIN_BONUS_REWARD = TRAINING_WIN_BONUS_WEIGHT   # same +-0.5 scale as Strategy PPO, added post-tanh everywhere matches the /5000.0 used inside
                                                                       # ReinforceBootstrapAlphaController /
                                                                       # ReinforceAnimalController /
                                                                       # ReinforceReorderController .update()

def aggressive_livestock_strategy(ws: WorldState) -> StrategyConfig:
    # Same field-drop bug as other StrategyConfig spots in this notebook:
    # manually rebuilding only some fields silently resets the rest to
    # default. Fixed with dataclasses.replace for consistency.
    base = default_strategy_controller(ws, None)
    return dataclasses.replace(
        base,
        investment_budget_fraction=min(1.0, base.investment_budget_fraction * 1.15),
        risk_aversion=max(0.1, base.risk_aversion * 0.6),
        livestock_bias=0.4, farming_bias=-0.2,
    )

def conservative_farming_strategy(ws: WorldState) -> StrategyConfig:
    base = default_strategy_controller(ws, None)
    return dataclasses.replace(
        base,
        investment_budget_fraction=base.investment_budget_fraction * 0.7,
        risk_aversion=min(0.95, base.risk_aversion * 1.4),
        livestock_bias=-0.3, farming_bias=0.3,
    )

def build_opponent_pool():
    """Real opponent diversity for training: default baseline + an
    aggressive-livestock style + a conservative-farming style, all safe-wrapped.
    Pass this explicitly to every run_stage(...)/train_production_priority_v2(...)
"""
    return [
        make_agent(safe=True),
        make_agent(strategy_fn=aggressive_livestock_strategy, safe=True),
        make_agent(strategy_fn=conservative_farming_strategy, safe=True),
    ]


def run_turn_with_sell_fn(ws: WorldState, mem: dict, strategy: Optional["StrategyConfig"] = None,
                           transition_matrices: Optional[dict] = None,
                           transition_counts: Optional[dict] = None,
                           opponent_belief_input: Optional["OpponentBelief"] = None,
                           use_sell_fraction: bool = False, sell_fraction_fn=None,
                           return_matrices: Optional[dict] = None):
    log_market_state(ws, mem)
    fa = build_farm_analysis(ws, mem)
    strategy = strategy or default_strategy_controller(ws, opponent_belief_input)
    _mandatory_backlog_tasks = _estimate_daily_action_backlog(ws, discretionary_cash=float("inf"))["mandatory"]
    mandatory_future_cost = _mandatory_backlog_tasks * LABOR_COST_PER_TASK
    batch = generate_candidates(ws, fa, mem, mandatory_future_cost=mandatory_future_cost)
    evaluations = evaluate_all_candidates(batch, ws)

    forecast = None
    if transition_matrices or opponent_belief_input is not None:
        if transition_matrices and return_matrices:
            forecast = markov_forecast_market_prices_v2(ws, mem, transition_matrices, return_matrices,
                                                          transition_counts)
        elif transition_matrices:
            forecast = markov_forecast_market_prices(ws, mem, transition_matrices, transition_counts)
        evaluations = apply_market_intelligence(evaluations, forecast, opponent_belief_input, ws=ws)

    sell_fractions = None
    if use_sell_fraction:
        opponent_crop_pressure = estimate_opponent_crop_pressure(ws, mem)
        if sell_fraction_fn is not None:
            sell_fractions = sell_fraction_fn(ws, forecast, opponent_belief_input, opponent_crop_pressure)
        else:
            sell_fractions = compute_sell_fractions(ws, forecast, opponent_belief_input, opponent_crop_pressure)

    capital_plan = optimize_capital(batch, evaluations, ws, strategy=strategy)
    schedule_plan = schedule_workers(capital_plan, evaluations, ws)
    if RL_FLOORCAP_CONTROLLER is not None:
        RL_FLOORCAP_CONTROLLER.record_schedule_outcome(ws, schedule_plan)
    env_action = build_env_action(schedule_plan, batch, ws, mem, capital_plan=capital_plan,
                                   sell_fractions=sell_fractions)
    return env_action, schedule_plan, capital_plan

import math

import random as _random

from collections import deque as _deque

def _crop_growth_stats(ws: "WorldState") -> tuple:
    n_growing = 0
    days_to_harvest = []
    for t in ws.tiles:
        if not isinstance(t, dict):
            continue
        crop = t.get("crop")
        planted_day = t.get("planted_day")
        if crop is None or planted_day is None or crop not in CROP_INFO:
            continue
        maturity = CROP_INFO[crop].get("max_yield_day", PLANT_MATURITY_REF)
        remaining = maturity - (ws.day - planted_day)
        if remaining > 0:
            n_growing += 1
            days_to_harvest.append(remaining)
    avg_remaining = (sum(days_to_harvest) / len(days_to_harvest)) if days_to_harvest else 0.0
    avg_remaining_norm = math.tanh(avg_remaining / max(1.0, PLANT_MATURITY_REF))
    n_growing_norm = math.tanh(n_growing / 10.0)
    return n_growing_norm, avg_remaining_norm

def _crop_opportunity_stats(ws: "WorldState") -> tuple:
    margins = []
    speed_weighted = []
    for crop, info in CROP_INFO.items():
        base = info.get("base_price", 1.0)
        cur = ws.prices.get(crop, base)
        margin = (cur - base) / max(1.0, base)
        margins.append(margin)
        maturity = max(1.0, info.get("max_yield_day", PLANT_MATURITY_REF))
        speed_weighted.append(margin / maturity)
    best_margin = math.tanh(max(margins)) if margins else 0.0
    margin_spread = math.tanh((max(margins) - min(margins))) if margins else 0.0
    best_margin_speed = math.tanh(max(speed_weighted) * 5.0) if speed_weighted else 0.0
    return best_margin, margin_spread, best_margin_speed

def build_production_priority_state(ws: "WorldState", opponent_belief: Optional["OpponentBelief"] = None, mem: Optional[dict] = None) -> "np.ndarray":
    cash_norm = math.tanh(ws.money / 5000.0)
    shed_value = sum(ws.shed.get(p, 0) * ws.prices.get(p, CROP_INFO.get(p, {}).get("base_price", 0) if p in CROP_INFO else 0)
                      for p in ws.shed) if ws.shed else 0.0
    shed_value_norm = math.tanh(shed_value / 5000.0)
    remaining_frac = ws.remaining_days / max(1, SEASON_DAYS)
    season_progress = 1.0 - remaining_frac
    n_growing_norm, avg_remaining_norm = _crop_growth_stats(ws)

    price_signals = []
    for crop, info in CROP_INFO.items():
        base = info.get("base_price", 1.0)
        cur = ws.prices.get(crop, base)
        price_signals.append(math.tanh((cur - base) / max(1.0, base)))
    avg_price_signal = sum(price_signals) / len(price_signals) if price_signals else 0.0

    cash_vs_opp = math.tanh((ws.money - ws.opp_money) / 5000.0)

    opp_aggr = 0.0
    opp_conf = 0.0
    if opponent_belief is not None:
        opp_aggr = opponent_belief.aggressiveness
        opp_conf = 1.0 - opponent_belief.uncertainty

    is_terminal = 1.0 if ws.is_terminal_phase else 0.0

    return np.array([cash_norm, shed_value_norm, remaining_frac, season_progress,
                      n_growing_norm, avg_remaining_norm, avg_price_signal,
                      cash_vs_opp, opp_aggr * opp_conf, is_terminal], dtype=np.float32)

def build_production_priority_state_v2b(ws: "WorldState", opponent_belief: Optional["OpponentBelief"] = None, mem: Optional[dict] = None) -> "np.ndarray":
    base_state = build_production_priority_state(ws, opponent_belief)
    best_margin, margin_spread, best_margin_speed = _crop_opportunity_stats(ws)
    return np.concatenate([base_state, np.array([best_margin, margin_spread, best_margin_speed], dtype=np.float32)])

SHED_CAPACITY_DEFAULT = 100

def build_production_priority_state_v2c(ws: "WorldState", opponent_belief: Optional["OpponentBelief"] = None,
                                          mem: Optional[dict] = None,
                                          shed_capacity: int = SHED_CAPACITY_DEFAULT) -> "np.ndarray":
    base_state = build_production_priority_state_v2b(ws, opponent_belief)
    shed_units = sum(ws.shed.values()) if ws.shed else 0
    storage_ratio = min(1.0, shed_units / max(1, shed_capacity))
    return np.concatenate([base_state, np.array([storage_ratio], dtype=np.float32)])

PRODUCTION_PRIORITY_STATE_DIM_V1 = 10
PRODUCTION_PRIORITY_STATE_DIM_V2B = 13
PRODUCTION_PRIORITY_STATE_DIM_V2C = 14
PRODUCTION_PRIORITY_STATE_DIM_V2D = 18

def _opportunity_cost_stats_v2(ws: "WorldState") -> tuple:
    crop_speeds = []
    for crop, info in CROP_INFO.items():
        base = info.get("base_price", 1.0)
        cur = ws.prices.get(crop, base)
        margin = (cur - base) / max(1.0, base)
        maturity = max(1.0, info.get("max_yield_day", PLANT_MATURITY_REF))
        crop_speeds.append(margin / maturity)
    best_crop_speed_raw = max(crop_speeds) if crop_speeds else 0.0

    animal_speeds = []
    for species, info in ANIMAL_INFO.items():
        product = info.get("product")
        base = info.get("base_price", 1.0)
        cur = ws.prices.get(product, base)
        margin = (cur - base) / max(1.0, base)
        cycle_days = max(1.0, info.get("first_yield", PLANT_MATURITY_REF) + info.get("interval", 0))
        animal_speeds.append(margin / cycle_days)
    best_animal_speed_raw = max(animal_speeds) if animal_speeds else 0.0

    best_crop_speed = math.tanh(best_crop_speed_raw * 5.0)
    best_animal_speed = math.tanh(best_animal_speed_raw * 5.0)
    category_gap = math.tanh((best_crop_speed_raw - best_animal_speed_raw) * 5.0)
    return best_crop_speed, best_animal_speed, category_gap

def _opponent_market_pressure(ws: "WorldState") -> tuple:
    crop_margins = {}
    for crop, info in CROP_INFO.items():
        base = info.get("base_price", 1.0)
        cur = ws.prices.get(crop, base)
        crop_margins[crop] = (cur - base) / max(1.0, base)

    opp_counts = ws.opp_crop_counts or {}
    total_opp_tiles = sum(opp_counts.values())

    if not crop_margins or total_opp_tiles <= 0:
        opp_pressure_on_best = 0.0
    else:
        best_crop = max(crop_margins, key=crop_margins.get)
        opp_pressure_on_best = opp_counts.get(best_crop, 0) / total_opp_tiles

    own_counts = {}
    for t in ws.tiles:
        if isinstance(t, dict):
            c = t.get("crop")
            if c:
                own_counts[c] = own_counts.get(c, 0) + 1
    total_own_tiles = sum(own_counts.values())

    if total_own_tiles <= 0 or total_opp_tiles <= 0:
        crop_mix_overlap = 0.0
    else:
        crop_mix_overlap = sum(
            min(own_counts.get(c, 0) / total_own_tiles, opp_counts.get(c, 0) / total_opp_tiles)
            for c in set(own_counts) | set(opp_counts)
        )

    return opp_pressure_on_best, crop_mix_overlap

PRODUCTION_PRIORITY_V2D_HORIZON = 5

def make_production_priority_state_builder_v2d(transition_matrices: dict, transition_counts: Optional[dict] = None,
                                                 horizon: int = PRODUCTION_PRIORITY_V2D_HORIZON,
                                                 products: Optional[list] = None):
    products = products or list(transition_matrices.keys())
    transition_counts = transition_counts or {}

    def _builder(ws: "WorldState", opponent_belief: Optional["OpponentBelief"] = None,
                 mem: Optional[dict] = None) -> "np.ndarray":
        mem = mem if mem is not None else {}
        base_state = build_production_priority_state_v2c(ws, opponent_belief, mem)
        if not transition_matrices:
            return np.concatenate([base_state, np.zeros(4, dtype=np.float32)])

        forecasts = markov_forecast_market_prices(ws, mem, transition_matrices, transition_counts, horizon=horizon)
        r1s, r3s, r5s, confs = [], [], [], []
        for product in products:
            fc = forecasts.get(product)
            if fc is None:
                continue
            base_p = max(1e-6, fc.current_price)
            r1s.append((fc.forecast_by_day_offset.get(1, fc.current_price) - fc.current_price) / base_p)
            r3s.append((fc.forecast_by_day_offset.get(3, fc.current_price) - fc.current_price) / base_p)
            r5s.append((fc.forecast_by_day_offset.get(min(5, horizon), fc.current_price) - fc.current_price) / base_p)
            confs.append(fc.confidence)

        if not r1s:
            return np.concatenate([base_state, np.zeros(4, dtype=np.float32)])

        forecast_1d = math.tanh((sum(r1s) / len(r1s)) * 5.0)
        forecast_3d = math.tanh((sum(r3s) / len(r3s)) * 5.0)
        forecast_5d = math.tanh((sum(r5s) / len(r5s)) * 5.0)
        forecast_conf = sum(confs) / len(confs)
        return np.concatenate([base_state,
                                np.array([forecast_1d, forecast_3d, forecast_5d, forecast_conf], dtype=np.float32)])
    return _builder

PRODUCTION_PRIORITY_STATE_DIM_V2E = 23

def make_production_priority_state_builder_v2e(transition_matrices: dict, transition_counts: Optional[dict] = None,
                                                 horizon: int = PRODUCTION_PRIORITY_V2D_HORIZON,
                                                 products: Optional[list] = None):
    v2d_builder = make_production_priority_state_builder_v2d(transition_matrices, transition_counts, horizon, products)

    def _builder(ws: "WorldState", opponent_belief: Optional["OpponentBelief"] = None,
                 mem: Optional[dict] = None) -> "np.ndarray":
        v2d_state = v2d_builder(ws, opponent_belief, mem)
        best_crop_speed, best_animal_speed, category_gap = _opportunity_cost_stats_v2(ws)
        opp_pressure_on_best, crop_mix_overlap = _opponent_market_pressure(ws)
        return np.concatenate([v2d_state, np.array(
            [best_crop_speed, best_animal_speed, category_gap, opp_pressure_on_best, crop_mix_overlap],
            dtype=np.float32)])
    return _builder

PRODUCTION_PRIORITY_V2_GRIDS = {
    "risk_aversion": (0.2, 0.35, 0.5, 0.7, 0.9),
    "investment_budget_fraction": (0.4, 0.6, 0.8, 0.9, 1.0),
}

PRODUCTION_PRIORITY_V2_FIELDS = tuple(PRODUCTION_PRIORITY_V2_GRIDS.keys())

N_PRODUCTION_PRIORITY_V2_FIELDS = len(PRODUCTION_PRIORITY_V2_FIELDS)

N_PRODUCTION_PRIORITY_V2_BINS = 5

def production_priority_overrides_from_action(action_indices: tuple) -> dict:
    return {field: PRODUCTION_PRIORITY_V2_GRIDS[field][idx]
            for field, idx in zip(PRODUCTION_PRIORITY_V2_FIELDS, action_indices)}

class ProductionPriorityPolicyV2(_nn.Module):
    def __init__(self, state_dim: int, n_fields=N_PRODUCTION_PRIORITY_V2_FIELDS,
                 n_bins=N_PRODUCTION_PRIORITY_V2_BINS, hidden=64):
        super().__init__()
        self.trunk = _nn.Sequential(
            _nn.Linear(state_dim, hidden), _nn.ReLU(),
            _nn.Linear(hidden, hidden), _nn.ReLU(),
        )
        self.heads = _nn.ModuleList([_nn.Linear(hidden, n_bins) for _ in range(n_fields)])
        self.critic = _nn.Sequential(
            _nn.Linear(hidden, hidden // 2), _nn.ReLU(),
            _nn.Linear(hidden // 2, 1),
        )

    def forward(self, x):
        h = self.trunk(x)
        logits_per_head = [head(h) for head in self.heads]
        value = self.critic(h)
        return logits_per_head, value

class PPOProductionPriorityControllerV2:

    def __init__(self, state_dim: int, lr=3e-4, epsilon=0.2, batch_size=64, gamma=0.97, entropy_coef=0.03,
                 entropy_coef_min=0.003, entropy_decay_updates=300):
        self.state_dim = state_dim
        self.epsilon = epsilon
        self.batch_size = batch_size
        self.gamma = gamma
        # FIX (entropy plateau, same cause as strategy/sell controllers): this
        # controller was missed by the earlier audit and had the identical fixed
        # entropy_coef bug. Same linear decay pattern (min = 10%% of start).
        self.entropy_coef = entropy_coef
        self.entropy_coef_start = entropy_coef
        self.entropy_coef_min = entropy_coef_min
        self.entropy_decay_updates = entropy_decay_updates
        self.entropy_coef_history = []
        self.buffer = []
        self.entropy_history = []
        self.policy = ProductionPriorityPolicyV2(state_dim)
        self.old_policy = ProductionPriorityPolicyV2(state_dim)
        self.old_policy.load_state_dict(self.policy.state_dict())
        self.optimizer = _torch.optim.Adam(self.policy.parameters(), lr=lr)

    def select(self, state: "np.ndarray", greedy: bool = False):
        with _torch.no_grad():
            st = _torch.from_numpy(state).unsqueeze(0)
            logits_per_head, value = self.old_policy(st)
            action_indices = []
            log_prob_total = 0.0
            for logits in logits_per_head:
                logits = logits.squeeze(0)
                dist = _torch.distributions.Categorical(logits=logits)
                action = logits.argmax() if greedy else dist.sample()
                action_indices.append(int(action.item()))
                log_prob_total += float(dist.log_prob(action).item())
        overrides = production_priority_overrides_from_action(tuple(action_indices))
        return overrides, tuple(action_indices), log_prob_total, float(value.item())

    def record(self, state, action_indices, log_prob, value, reward, done):
        self.buffer.append((state, action_indices, log_prob, value, reward, done))
        if len(self.buffer) >= self.batch_size:
            self._update()

    def _current_entropy_coef(self) -> float:
        n_prior_updates = len(self.entropy_history)
        if self.entropy_decay_updates <= 0:
            return self.entropy_coef_min
        frac = min(1.0, n_prior_updates / self.entropy_decay_updates)
        return self.entropy_coef_start + (self.entropy_coef_min - self.entropy_coef_start) * frac

    def _update(self):
        if not self.buffer:
            return
        states = _torch.from_numpy(np.stack([b[0] for b in self.buffer]))
        actions = _torch.tensor([b[1] for b in self.buffer], dtype=_torch.long)   
        old_log_probs = _torch.tensor([b[2] for b in self.buffer], dtype=_torch.float32)
        last_bootstrap = 0.0 if self.buffer[-1][5] else self.buffer[-1][3]
        values_list = [b[3] for b in self.buffer] + [last_bootstrap]
        rewards = [b[4] for b in self.buffer]
        dones = [b[5] for b in self.buffer]
        advantages_list, returns_list = _compute_gae(rewards, values_list, dones, self.gamma, lam=0.95)
        advantages = _torch.tensor(advantages_list, dtype=_torch.float32)
        returns = _torch.tensor(returns_list, dtype=_torch.float32)
        if advantages.numel() > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        n = states.shape[0]
        idx_all = np.arange(n)
        last_entropy = None
        for _ in range(4):
            np.random.shuffle(idx_all)
            for start in range(0, n, 32):
                mb = idx_all[start:start + 32]
                mb_idx = _torch.from_numpy(mb).long()
                s = states[mb_idx]
                a = actions[mb_idx]          
                olp, adv, ret = old_log_probs[mb_idx], advantages[mb_idx], returns[mb_idx]

                logits_per_head, new_values = self.policy(s)
                new_log_probs = sum(
                    _torch.distributions.Categorical(logits=logits_per_head[f]).log_prob(a[:, f])
                    for f in range(N_PRODUCTION_PRIORITY_V2_FIELDS))
                entropy = sum(
                    _torch.distributions.Categorical(logits=logits_per_head[f]).entropy()
                    for f in range(N_PRODUCTION_PRIORITY_V2_FIELDS)).mean() / N_PRODUCTION_PRIORITY_V2_FIELDS
                ratio = _torch.exp(new_log_probs - olp)
                surr1 = ratio * adv
                surr2 = _torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * adv
                policy_loss = -_torch.min(surr1, surr2).mean()
                value_loss = _F.mse_loss(new_values.squeeze(-1), ret)
                current_entropy_coef = self._current_entropy_coef()
                self.entropy_coef = current_entropy_coef  # kept in sync for external inspection
                loss = policy_loss + 0.5 * value_loss - current_entropy_coef * entropy

                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                last_entropy = float(entropy.item())
        self.old_policy.load_state_dict(self.policy.state_dict())
        self.buffer = []
        if last_entropy is not None:
            self.entropy_history.append(last_entropy)
            self.entropy_coef_history.append(current_entropy_coef)

    def _entropy_convergence(self, n_last: int = 3, ratio_threshold: float = 0.9) -> dict:
        max_entropy = float(np.log(N_PRODUCTION_PRIORITY_V2_BINS))
        if not self.entropy_history:
            return {"mean_entropy": None, "max_entropy": max_entropy, "ratio": None,
                    "converged": False, "n_updates_total": 0}
        recent = self.entropy_history[-n_last:]
        mean_ent = float(np.mean(recent))
        ratio = mean_ent / max_entropy if max_entropy > 0 else 0.0
        return {"mean_entropy": mean_ent, "max_entropy": max_entropy, "ratio": ratio,
                "converged": ratio < ratio_threshold, "n_updates_total": len(self.entropy_history)}

def _compute_gae(rewards, values, dones, gamma, lam=0.95):
    T = len(rewards)
    advantages = [0.0] * T
    gae = 0.0
    for t in reversed(range(T)):
        next_value = 0.0 if dones[t] else values[t + 1]
        delta = rewards[t] + gamma * next_value - values[t]
        gae = delta + gamma * lam * (0.0 if dones[t] else gae)
        advantages[t] = gae
    returns = [advantages[t] + values[t] for t in range(T)]
    return advantages, returns

STAGE4C2_DEFAULT_HORIZON_TURNS = 2 * TURNS_PER_DAY

STAGE4C2_STATE_DIM = SELL_STATE_DIM + 1

def build_sell_state_4c(product: str, ws: WorldState,
                         forecast: Optional[dict] = None,
                         opponent_belief: Optional[OpponentBelief] = None,
                         opponent_crop_pressure: Optional[dict] = None) -> "np.ndarray":
    base_state = build_sell_state(product, ws, forecast, opponent_belief, opponent_crop_pressure)
    info = CROP_INFO.get(product)
    maturity = info.get("max_yield_day", PLANT_MATURITY_REF) if info is not None else PLANT_MATURITY_REF
    maturity_norm = math.tanh((maturity - PLANT_MATURITY_REF) / PLANT_MATURITY_SCALE)
    return np.concatenate([base_state, np.array([maturity_norm], dtype=np.float32)])

PRODUCTION_PRIORITY_PERSIST_TURNS = TURNS_PER_DAY

# DEAD CODE REMOVED: _stage4c2_product_horizon_turns_v2() -- orphaned after
# its caller (_run_one_episode_stage4c2_v7) was also dead code, removed.

def wrap_production_priority_v2_strategy_fn_persistent(controller: PPOProductionPriorityControllerV2,
                                                          state_builder, persist_turns: int, greedy: bool = True):
    held = {"cfg": None, "next_select_turn": -1}

    def strategy_fn(ws: WorldState, mem: Optional[dict] = None) -> StrategyConfig:
        if mem is not None:
            log_market_state(ws, mem)
        if ws.turn_in_episode >= held["next_select_turn"]:
            state = state_builder(ws, None, mem)
            overrides, _, _, _ = controller.select(state, greedy=greedy)
            b0_cfg = default_strategy_controller(ws, None)
            # BUG FIX (same class as elsewhere): manually re-listing fields
            # silently dropped animal_allocation_ratio. dataclasses.replace()
            # copies all fields, overriding only the intended ones.
            held["cfg"] = dataclasses.replace(
                b0_cfg,
                investment_budget_fraction=overrides.get("investment_budget_fraction", b0_cfg.investment_budget_fraction),
                risk_aversion=overrides.get("risk_aversion", b0_cfg.risk_aversion))
            held["next_select_turn"] = ws.turn_in_episode + persist_turns
        return held["cfg"]
    return strategy_fn

SELL_DECISION_PERSIST_TURNS = TURNS_PER_DAY

SELL_PPO_REWARD_HORIZON_TURNS = 3 * TURNS_PER_DAY
# FIX (Strategy PPO turn-vs-horizon credit mismatch): macro strategy dials only
# manifest over days, not the next turn -- crediting every turn was pure noise.
# Now holds the action for a full day and credits with the day's net-worth delta.
STRATEGY_PPO_HOLD_TURNS = TURNS_PER_DAY
# FIX (reward-scale mismatch from the hold-turns fix above): tanh(delta/200.0)
# was calibrated for a single-turn delta, now ~24x bigger per day -> saturated
# to +-1 almost always. Scale the divisor by the same factor to compensate.
STRATEGY_PPO_REWARD_SCALE = 200.0 * STRATEGY_PPO_HOLD_TURNS

def compute_sell_fractions_ppo_4c_persistent(ws: WorldState, controller, held_state: dict,
                                               persist_turns: int = SELL_DECISION_PERSIST_TURNS,
                                               forecast=None, opponent_belief=None,
                                               opponent_crop_pressure=None, greedy=True, record_fn=None) -> dict:
    fractions = {}
    for product in ws.shed:
        if product not in MARKET_PARAMS or ws.shed.get(product, 0) <= 0:
            continue
        h = held_state.get(product)
        if h is None or ws.turn_in_episode >= h["next_select_turn"]:
            state = build_sell_state_4c(product, ws, forecast, opponent_belief, opponent_crop_pressure)
            fraction, idx, log_prob, value = controller.select(state, greedy=greedy)
            h = dict(fraction=fraction, action_idx=idx, log_prob=log_prob, value=value, state=state,
                      next_select_turn=ws.turn_in_episode + persist_turns, is_new=True)
            held_state[product] = h
        else:
            h["is_new"] = False
        fractions[product] = h["fraction"] if h["is_new"] else 0.0
        if record_fn is not None and h["is_new"]:
            record_fn(product, h["state"], h["action_idx"], h["log_prob"], h["value"], h["fraction"])
    return fractions

SELL_ACTION_GRID_WITH_HOLD = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)

STAGE4C2_PCT_DELTA_CLIP = 0.5

STAGE4C2_PCT_REWARD_SCALE = 3.0

STAGE4C2_PCT_REWARD_CLIP = 3.0

def _stage4c2_pct_reward(delta: float) -> float:
    r = delta / STAGE4C2_PCT_REWARD_SCALE
    return max(-STAGE4C2_PCT_REWARD_CLIP, min(STAGE4C2_PCT_REWARD_CLIP, r))

def _stage4c2_incremental_reward_delta(qty_sold_actual: float, price_before: float, price_horizon: float) -> float:
    pct_delta = (price_before - price_horizon) / max(1.0, price_before)
    pct_delta = max(-STAGE4C2_PCT_DELTA_CLIP, min(STAGE4C2_PCT_DELTA_CLIP, pct_delta))
    return qty_sold_actual * pct_delta

# DEAD CODE REMOVED: _run_one_episode_stage4c2_v7() had zero call sites anywhere in the notebook (confirmed via a full-file reference scan) -- an orphaned episode-runner from an earlier Stage 4C iteration, superseded elsewhere without being deleted.


def _production_cycle_horizon_turns(ws: "WorldState") -> int:
    max_remaining = 0
    for t in ws.tiles:
        if not isinstance(t, dict):
            continue
        crop = t.get("crop")
        planted_day = t.get("planted_day")
        if crop is None or planted_day is None or crop not in CROP_INFO:
            continue
        maturity = CROP_INFO[crop].get("max_yield_day", PLANT_MATURITY_REF)
        remaining = maturity - (ws.day - planted_day)
        if remaining > max_remaining:
            max_remaining = remaining

    for species, count in (ws.animal_counts or {}).items():
        if count <= 0:
            continue
        info = ANIMAL_INFO.get(species)
        if info is None:
            continue
        cycle_days = info.get("first_yield", PLANT_MATURITY_REF) + info.get("interval", 0)
        if cycle_days > max_remaining:
            max_remaining = cycle_days

    horizon_days = max_remaining if max_remaining > 0 else PLANT_MATURITY_REF
    return max(1, int(horizon_days)) * TURNS_PER_DAY

def train_production_priority_v2(controller_4b, state_builder, n_episodes, episode_steps=None,
                                  opponent_pool=None, persist_turns=PRODUCTION_PRIORITY_PERSIST_TURNS,
                                  reward_scale=500.0, verbose=True,
                                  patience=None, window=3, min_delta=0.0,
                                  min_updates_for_early_stop=15, entropy_gate_ratio=0.9):
    import statistics as _stats_local   
    episode_steps = episode_steps or EPISODE_STEPS_DEFAULT
    opponent_pool = opponent_pool or [make_agent(safe=True)]
    returns = []
    best_trailing_mean = -float("inf")
    no_improve_checks = 0
    import time as _time_local   
    _stage_t0 = _time_local.time()
    converged_stop = False
    timed_out = False
    ep = -1
    while True:
        ep += 1
        if ep >= MAX_EPISODES_SAFETY:
            if verbose:
                print(f"  [4B-train] [!] hit absolute safety ceiling of {MAX_EPISODES_SAFETY} "
                      f"episodes -- stopping (should not normally happen)")
            break
        if time_budget_exceeded():
            if verbose:
                print(f"  [4B-train] [!] GLOBAL TIME BUDGET EXCEEDED mid-stage at ep {ep} -- "
                      f"stopping now. NOT converged, caller should not freeze this stage.")
            timed_out = True
            break
        _ep_t0 = _time_local.time()
        seed = _random.randint(0, 10 ** 6)
        opponent_path = opponent_pool[ep % len(opponent_pool)]
        mem = {"weed_age": {}, "own_planted_day": {}, "completed_project_steps": {}, "failure_count": {}}
        held = {"cfg": None, "next_select_turn": -1}
        held_sell = {}   
        pending = []

        def agent(obs, config=None, _mem=mem, _held=held, _held_sell=held_sell, _pending=pending):
            ws = build_world_state(obs)
            worth = _estimate_net_worth(ws)

            still_pending = []
            for tr in _pending:
                if ws.turn_in_episode >= tr["due_turn"]:
                    delta = worth - tr["worth_before"]
                    reward = math.tanh(delta / reward_scale)
                    controller_4b.record(tr["state"], tr["action_indices"], tr["log_prob"], tr["value"],
                                          reward, False)
                else:
                    still_pending.append(tr)
            _pending[:] = still_pending

            log_market_state(ws, _mem)
            if ws.turn_in_episode >= _held["next_select_turn"]:
                state = state_builder(ws, None, _mem)
                overrides, action_indices, log_prob, value = controller_4b.select(state, greedy=False)
                if STRATEGY_CONTROLLER.enabled:
                    base_state = build_strategy_state(ws, None)
                    base_cfg, _, _, _ = STRATEGY_CONTROLLER.select(base_state, greedy=True)
                else:
                    base_cfg = default_strategy_controller(ws, None)
                    # BUG FIX (same class as elsewhere): manually re-listing
                    # fields silently dropped animal_allocation_ratio. Fixed
                    # with dataclasses.replace() so all fields get copied.
                _held["cfg"] = dataclasses.replace(
                    base_cfg,
                    investment_budget_fraction=overrides.get("investment_budget_fraction",
                                                              base_cfg.investment_budget_fraction),
                    risk_aversion=overrides.get("risk_aversion", base_cfg.risk_aversion))
                horizon_turns = _production_cycle_horizon_turns(ws)
                _pending.append(dict(state=state, action_indices=action_indices, log_prob=log_prob,
                                      value=value, worth_before=worth,
                                      due_turn=ws.turn_in_episode + horizon_turns))
                _held["next_select_turn"] = ws.turn_in_episode + persist_turns

            if SELL_CONTROLLER.enabled:
                def _sell_fn(ws_, forecast, opponent_belief, opponent_crop_pressure, _hs=_held_sell):
                    return compute_sell_fractions_ppo_4c_persistent(
                        ws_, SELL_CONTROLLER, _hs, persist_turns=SELL_DECISION_PERSIST_TURNS,
                        forecast=forecast, opponent_belief=opponent_belief,
                        opponent_crop_pressure=opponent_crop_pressure, greedy=True)
                env_action, _, _ = run_turn_with_sell_fn(ws, _mem, strategy=_held["cfg"],
                                                          use_sell_fraction=True, sell_fraction_fn=_sell_fn)
            else:
                env_action, _, _ = run_turn(ws, _mem, strategy=_held["cfg"])
            return env_action

        env = _kaggle_make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=False)
        result = env.run([agent, opponent_path])
        final_ws = build_world_state(result[-1][0]["observation"])
        final_worth = _estimate_net_worth(final_ws)
        final_money = final_ws.money

        # FIX (reward metric): reward used to be pure tanh(delta_net_worth), which
        # could "win big" or "lose narrowly" without training directly toward
        # beating the opponent head-to-head. Add a symmetric win-bonus.
        opponent_final_ws = build_world_state(result[-1][1]["observation"])
        opponent_final_worth = _estimate_net_worth(opponent_final_ws)
        win_bonus = TRAINING_WIN_BONUS_WEIGHT * (1.0 if final_worth > opponent_final_worth else -1.0)

        for tr in pending:
            delta = final_worth - tr["worth_before"]
            reward = math.tanh(delta / reward_scale) + win_bonus
            controller_4b.record(tr["state"], tr["action_indices"], tr["log_prob"], tr["value"], reward, True)

        returns.append(final_worth)
        if verbose:
            print(f"  [4B-train] ep {ep:3d} | money={final_money:>10,.0f} | net_worth={final_worth:>10,.0f} | "
                  f"time={_time_local.time()-_ep_t0:.1f}s")

        if patience is None:
            if ep + 1 >= n_episodes:
                converged_stop = True
                break
            continue

        if patience is not None and len(returns) >= window:
            trailing_window = returns[-window:]
            trailing_mean = _stats_local.mean(trailing_window)
            trailing_std = _stats_local.pstdev(trailing_window) if len(trailing_window) > 1 else 0.0
            trailing_sem = trailing_std / (window ** 0.5)
            eff_min_delta = max(min_delta, SEM_K * trailing_sem)
            if trailing_mean > best_trailing_mean + eff_min_delta:
                best_trailing_mean = trailing_mean
                no_improve_checks = 0
            else:
                no_improve_checks += 1
            if no_improve_checks >= patience:
                # GATE (same rationale as run_stage): don't let early-stop fire
                # before controller_4b has had enough PPO updates to move off
                # its random init and differentiate its action distribution.
                ed = controller_4b._entropy_convergence()
                n_upd = ed["n_updates_total"]
                ratio = ed["ratio"]
                gate_blocked = False
                if n_upd < min_updates_for_early_stop:
                    gate_blocked = True
                    gate_reason = (f"n_updates_total={n_upd} < min_updates_for_early_stop="
                                   f"{min_updates_for_early_stop}")
                elif ratio is not None and ratio >= entropy_gate_ratio:
                    gate_blocked = True
                    gate_reason = (f"entropy_ratio={ratio:.2f} >= entropy_gate_ratio="
                                   f"{entropy_gate_ratio} (policy still near-uniform)")
                if gate_blocked:
                    if verbose and ep % 5 == 0:
                        print(f"  [4B-train] [early-stop gate] blocked at ep {ep}: {gate_reason} -- continuing")
                    no_improve_checks = patience - 1
                else:
                    if verbose:
                        print(f"  -> early stop at ep {ep} "
                              f"(trailing {window}-ep mean hasn't improved by >={eff_min_delta:,.0f} "
                              f"[floor min_delta={min_delta:,.0f}, {SEM_K}*SEM={SEM_K*trailing_sem:,.0f}] "
                              f"for {patience} checks, AND controller has converged)")
                    converged_stop = True
                    break
    if verbose:
        print(f"  [4B-train] TOTAL | episodes_run={len(returns)} (soft target was {n_episodes}) | "
              f"time={_time_local.time()-_stage_t0:.1f}s")
        ed = controller_4b._entropy_convergence()
        if ed["ratio"] is not None:
            warn = "  [!] NOT CONVERGED -- policy still near-uniform, treat results as noisy" \
                if not ed["converged"] else "  [ok] policy is sufficiently differentiated"
            print(f"  production_priority_ppo entropy_ratio={ed['ratio']:.2f} "
                  f"(mean_entropy={ed['mean_entropy']:.3f} / max={ed['max_entropy']:.3f}, "
                  f"n_updates={ed['n_updates_total']}){warn}")
        else:
            print("  production_priority_ppo entropy_diag: no update recorded yet (batch never filled)")
        if timed_out:
            print(f"  [4B-train] [!] STOPPED BY GLOBAL TIME BUDGET, NOT CONVERGED -- caller should "
                  f"NOT freeze this stage's controller into FROZEN_STAGE_AGENTS.")
    return {"returns": returns, "converged": converged_stop, "timed_out": timed_out}

def eval_production_priority_v2_vs_baseline(controller_4b, state_builder, eval_seeds, episode_steps=None,
                                             opponent_path=None, persist_turns=PRODUCTION_PRIORITY_PERSIST_TURNS):
    import time as _time_local   
    episode_steps = episode_steps or EPISODE_STEPS_DEFAULT
    make_opponent = (lambda: opponent_path) if opponent_path is not None else (lambda: make_agent(safe=True))
    b0_money, b4_money = [], []
    _eval_t0 = _time_local.time()
    for seed in eval_seeds:
        _seed_t0 = _time_local.time()
        agent0 = make_agent(safe=True)
        env0 = _kaggle_make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=False)
        r0 = env0.run([agent0, make_opponent()])
        b0_money.append(_estimate_net_worth(build_world_state(r0[-1][0]["observation"])))
        _b0_time = _time_local.time() - _seed_t0

        strategy_fn = wrap_production_priority_v2_strategy_fn_persistent(
            controller_4b, state_builder, persist_turns=persist_turns, greedy=True)
        mem = {"weed_age": {}, "own_planted_day": {}, "completed_project_steps": {}, "failure_count": {}}
        held_sell_eval = {}

        def agent4b(obs, config=None, _mem=mem, _sfn=strategy_fn, _hs=held_sell_eval):
            ws_ = build_world_state(obs)
            if SELL_CONTROLLER.enabled:
                def _sell_fn(ws__, forecast, opponent_belief, opponent_crop_pressure, _hs=_hs):
                    return compute_sell_fractions_ppo_4c_persistent(
                        ws__, SELL_CONTROLLER, _hs, persist_turns=SELL_DECISION_PERSIST_TURNS,
                        forecast=forecast, opponent_belief=opponent_belief,
                        opponent_crop_pressure=opponent_crop_pressure, greedy=True)
                env_action, _, _ = run_turn_with_sell_fn(ws_, _mem, strategy=_sfn(ws_, _mem),
                                                          use_sell_fraction=True, sell_fraction_fn=_sell_fn)
            else:
                env_action, _, _ = run_turn(ws_, _mem, strategy=_sfn(ws_, _mem))
            return env_action

        _b4_t0 = _time_local.time()
        env4 = _kaggle_make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=False)
        r4 = env4.run([agent4b, make_opponent()])
        b4_money.append(_estimate_net_worth(build_world_state(r4[-1][0]["observation"])))
        _b4_time = _time_local.time() - _b4_t0
        print(f"  [eval seed={seed}] baseline_game_time={_b0_time:.1f}s | "
              f"4b_game_time={_b4_time:.1f}s | seed_total={_time_local.time()-_seed_t0:.1f}s")
    print(f"  [eval] TOTAL | {len(eval_seeds)} seeds | time={_time_local.time()-_eval_t0:.1f}s")
    return b0_money, b4_money


import torch as _torch
import torch.nn as _nn
import torch.nn.functional as _F

STRATEGY_STATE_DIM = 13

STRATEGY_ACTION_GRIDS = {
    "investment_budget_fraction": (0.2, 0.4, 0.6, 0.8, 1.0),
    "risk_aversion": (0.0, 0.25, 0.5, 0.75, 1.0),
    "livestock_bias": (-1.0, -0.5, 0.0, 0.5, 1.0),
    "farming_bias": (-1.0, -0.5, 0.0, 0.5, 1.0),
    "expansion_bias": (-1.0, -0.5, 0.0, 0.5, 1.0),
    **{f"crop_bias__{c}": (-1.0, -0.5, 0.0, 0.5, 1.0) for c in CROP_ORDER},
    **{f"animal_bias__{a}": (-1.0, -0.5, 0.0, 0.5, 1.0) for a in ANIMAL_INFO},
}
STRATEGY_FIELDS = tuple(STRATEGY_ACTION_GRIDS.keys())   
N_STRATEGY_FIELDS = len(STRATEGY_FIELDS)
N_BINS_PER_FIELD = 5

def build_strategy_state(ws: WorldState, opponent_belief: Optional[OpponentBelief] = None) -> "np.ndarray":
    shed_value = sum(ws.shed.get(p, 0) * ws.prices.get(p, 0.0) for p in ws.shed)
    glut_vals = []
    for item, qty in ws.shed.items():
        if qty <= 0:
            continue
        base = MARKET_PARAMS.get(item, {}).get("base", 1)
        if base:
            glut_vals.append(ws.prices.get(item, base) / base)
    glut = (sum(glut_vals) / len(glut_vals)) if glut_vals else 1.0

    aggressiveness = opponent_belief.aggressiveness if opponent_belief is not None else 0.0
    uncertainty = opponent_belief.uncertainty if opponent_belief is not None else 1.0

    return np.array([
        math.tanh(ws.money / 2000.0),
        ws.day / SEASON_DAYS,
        ws.remaining_days / SEASON_DAYS,
        ws.n_quadrants / 4.0,
        min(1.0, ws.n_animals / 10.0),
        1.0 if ws.season_ending else 0.0,
        1.0 if ws.is_terminal_phase else 0.0,
        math.tanh(glut - 1.0),
        math.tanh(shed_value / 2000.0),
        aggressiveness,
        uncertainty,
        math.tanh(ws.opp_money / max(1.0, ws.money)),
        min(1.0, (ws.n_coop + ws.n_pasture) / 6.0),
    ], dtype=np.float32)

def strategy_config_from_action(action_indices: tuple) -> StrategyConfig:
    raw = {
        field: STRATEGY_ACTION_GRIDS[field][idx]
        for field, idx in zip(STRATEGY_FIELDS, action_indices)
    }
    kwargs = {}
    crop_bias = {}
    animal_bias = {}
    for field, value in raw.items():
        if field.startswith("crop_bias__"):
            crop_bias[field[len("crop_bias__"):]] = value
        elif field.startswith("animal_bias__"):
            animal_bias[field[len("animal_bias__"):]] = value
        else:
            kwargs[field] = value
    if crop_bias:
        kwargs["crop_bias"] = crop_bias
    if animal_bias:
        kwargs["animal_bias"] = animal_bias
    return StrategyConfig(**kwargs)

class StrategyPolicy(_nn.Module):
    def __init__(self, state_dim=STRATEGY_STATE_DIM, n_fields=N_STRATEGY_FIELDS,
                 n_bins=N_BINS_PER_FIELD, hidden=64):
        super().__init__()
        self.trunk = _nn.Sequential(
            _nn.Linear(state_dim, hidden), _nn.ReLU(),
            _nn.Linear(hidden, hidden), _nn.ReLU(),
        )
        self.heads = _nn.ModuleList([_nn.Linear(hidden, n_bins) for _ in range(n_fields)])
        self.critic = _nn.Sequential(
            _nn.Linear(hidden, hidden // 2), _nn.ReLU(),
            _nn.Linear(hidden // 2, 1),
        )

    def forward(self, x):
        h = self.trunk(x)
        logits_per_head = [head(h) for head in self.heads]   

        value = self.critic(h)
        return logits_per_head, value

class PPOStrategyController:

    def __init__(self, lr=3e-4, epsilon=0.2, batch_size=128, gamma=0.97, entropy_coef=0.02,
                 entropy_coef_min=0.002, entropy_decay_updates=300):
        self.epsilon = epsilon
        self.batch_size = batch_size
        self.gamma = gamma
        # FIX (entropy plateau): entropy_coef was fixed, so entropy_ratio stayed
        # stuck at ~0.95-1.00 even after 130 episodes/58 updates. Adds linear
        # decay to entropy_coef_min over entropy_decay_updates.
        self.entropy_coef = entropy_coef
        self.entropy_coef_start = entropy_coef
        self.entropy_coef_min = entropy_coef_min
        self.entropy_decay_updates = entropy_decay_updates
        self.entropy_coef_history = []
        self.buffer = []
        self.entropy_history = []
        self.enabled = False
        self.policy = StrategyPolicy()
        self.old_policy = StrategyPolicy()
        self.old_policy.load_state_dict(self.policy.state_dict())
        self.optimizer = _torch.optim.Adam(self.policy.parameters(), lr=lr)

    def _current_entropy_coef(self) -> float:
        n_prior_updates = len(self.entropy_history)
        if self.entropy_decay_updates <= 0:
            return self.entropy_coef_min
        frac = min(1.0, n_prior_updates / self.entropy_decay_updates)
        return self.entropy_coef_start + (self.entropy_coef_min - self.entropy_coef_start) * frac

    def select(self, state: "np.ndarray", greedy: bool = False):
        with _torch.no_grad():
            st = _torch.from_numpy(state).unsqueeze(0)
            logits_per_head, value = self.old_policy(st)
            action_indices = []
            log_prob_total = 0.0
            for logits in logits_per_head:
                logits = logits.squeeze(0)
                dist = _torch.distributions.Categorical(logits=logits)
                action = logits.argmax() if greedy else dist.sample()
                action_indices.append(int(action.item()))
                log_prob_total += float(dist.log_prob(action).item())
        cfg = strategy_config_from_action(tuple(action_indices))
        return cfg, tuple(action_indices), log_prob_total, float(value.item())

    def record(self, state, action_indices, log_prob, value, reward, done):
        self.buffer.append(dict(state=state, action_indices=action_indices, log_prob=log_prob,
                                 value=value, reward=reward, done=done))
        if len(self.buffer) >= self.batch_size:
            self._update()
            self.buffer = []

    def _rewards_to_go(self):
        rtg, R = [], 0.0
        last = self.buffer[-1]
        if not last["done"]:
            with _torch.no_grad():
                st = _torch.from_numpy(last["state"]).unsqueeze(0)
                _, v = self.old_policy(st)
            R = float(v.item())
        for tr in reversed(self.buffer):
            if tr["done"]:
                R = 0.0
            R = tr["reward"] + self.gamma * R
            rtg.insert(0, R)
        return rtg

    def _update(self):
        rtg = self._rewards_to_go()

        states = _torch.from_numpy(np.stack([t["state"] for t in self.buffer]))
        actions = _torch.tensor([t["action_indices"] for t in self.buffer], dtype=_torch.long)  
        old_log_probs = _torch.tensor([t["log_prob"] for t in self.buffer], dtype=_torch.float32)
        rewards_tensor = _torch.tensor(rtg, dtype=_torch.float32)

        with _torch.no_grad():
            _, values = self.old_policy(states)
        values = values.squeeze(-1)
        advantages = rewards_tensor - values
        if advantages.std() > 1e-6:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        for _ in range(4):
            logits_per_head, new_values = self.policy(states)
            log_probs_total = 0.0
            entropy_total = 0.0
            for head_idx, logits in enumerate(logits_per_head):
                dist = _torch.distributions.Categorical(logits=logits)
                log_probs_total = log_probs_total + dist.log_prob(actions[:, head_idx])
                entropy_total = entropy_total + dist.entropy()
            ratio = _torch.exp(log_probs_total - old_log_probs)
            surr1 = ratio * advantages
            surr2 = _torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * advantages
            actor_loss = -_torch.min(surr1, surr2).mean()
            critic_loss = _F.mse_loss(new_values.squeeze(-1), rewards_tensor)
            entropy_mean = (entropy_total / N_STRATEGY_FIELDS).mean()
            current_entropy_coef = self._current_entropy_coef()
            self.entropy_coef = current_entropy_coef  # kept in sync for external inspection
            loss = actor_loss + 0.5 * critic_loss - current_entropy_coef * entropy_mean

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        self.old_policy.load_state_dict(self.policy.state_dict())
        self.entropy_history.append(float(entropy_mean.item()))
        self.entropy_coef_history.append(current_entropy_coef)

    def _entropy_convergence(self, n_last: int = 3, ratio_threshold: float = 0.9) -> dict:
        max_entropy = float(np.log(N_BINS_PER_FIELD))
        if not self.entropy_history:
            return {"mean_entropy": None, "max_entropy": max_entropy, "ratio": None,
                    "converged": False, "n_updates_total": 0}
        recent = self.entropy_history[-n_last:]
        mean_ent = float(np.mean(recent))
        ratio = mean_ent / max_entropy if max_entropy > 0 else 0.0
        return {"mean_entropy": mean_ent, "max_entropy": max_entropy, "ratio": ratio,
                "converged": ratio < ratio_threshold, "n_updates_total": len(self.entropy_history)}


# DEAD CODE REMOVED: sell_fraction_from_action() and compute_sell_fractions_ppo()
# (non-persistent variant) had zero call sites -- superseded by
# compute_sell_fractions_ppo_4c_persistent(). build_sell_state() is still used.


import math, time, random as _random, statistics as _stats

# SEM-based early stopping: fixed min_delta in STAGE_CONFIG was hand-tuned and
# shrinks stage-over-stage while trailing std grows, making "no improvement"
# indistinguishable from noise. Threshold = max(min_delta, SEM_K*trailing_SEM).
SEM_K = 1.5
try:
    from kaggle_environments import make as _kaggle_make
    HAVE_KAGGLE_ENV = True
except ImportError:
    HAVE_KAGGLE_ENV = False

try:
    import psutil as _psutil
    import os as _os_mem
    def _process_mem_mb():
        return _psutil.Process(_os_mem.getpid()).memory_info().rss / 1e6
except ImportError:
    def _process_mem_mb():
        return float("nan")

STARTER_BOT_PATH_DEFAULT = "starter"

REINFORCE_CONTROLLERS = {
    "floorcap": RL_FLOORCAP_CONTROLLER,
    "alpha":    RL_CROP_MIX_CONTROLLER,
    "animal":   RL_ANIMAL_CONTROLLER,
    "rate":     RL_RATE_CONTROLLER,
    "reorder":  RL_REORDER_CONTROLLER,
}

STRATEGY_CONTROLLER = PPOStrategyController()
SELL_CONTROLLER = PPOSellFractionController(action_grid=SELL_ACTION_GRID_WITH_HOLD,
                                             state_dim=STAGE4C2_STATE_DIM)

_EVER_TRAINED_CONTROLLERS = set()   

# ---- GLOBAL TIME BUDGET: stop condition = convergence, not n_episodes (now
# a soft target). Only hard ceiling across the whole pipeline is a wall-clock
# deadline, so a Kaggle session can't run forever if something never converges. ----
GLOBAL_TRAINING_DEADLINE = None
MAX_EPISODES_SAFETY = 5000   # absolute sanity ceiling per stage; should never realistically trigger

def start_global_time_budget(hours=11.5):
    global GLOBAL_TRAINING_DEADLINE
    GLOBAL_TRAINING_DEADLINE = time.time() + hours * 3600
    print(f"[time budget] deadline set: {hours}h from now "
          f"({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(GLOBAL_TRAINING_DEADLINE))})")

def time_budget_remaining():
    if GLOBAL_TRAINING_DEADLINE is None:
        return float("inf")
    return GLOBAL_TRAINING_DEADLINE - time.time()

def time_budget_exceeded():
    return time_budget_remaining() <= 0

def set_stage_flags(active_reinforce, use_strategy_ppo, use_sell_ppo, rate_sub_flags=None):
    global _EVER_TRAINED_CONTROLLERS
    _EVER_TRAINED_CONTROLLERS |= set(active_reinforce)
    if "floorcap_stage2" in active_reinforce or "floorcap_stage2" in _EVER_TRAINED_CONTROLLERS:
        RL_FLOORCAP_CONTROLLER.enabled_stage2 = True
    for name, ctrl in REINFORCE_CONTROLLERS.items():
        if name in active_reinforce:
            ctrl.enabled = True
            ctrl.training = True
        elif name in _EVER_TRAINED_CONTROLLERS:
            ctrl.enabled = True    
            ctrl.training = False  
        else:
            ctrl.enabled = False
            ctrl.training = False
    if rate_sub_flags is not None:
        RL_RATE_CONTROLLER.enabled_animal = rate_sub_flags.get("animal", False)
        RL_RATE_CONTROLLER.enabled_plant = rate_sub_flags.get("plant", False)
        RL_ANIMAL_CONTROLLER.enabled_idle = rate_sub_flags.get("animal_idle", False)
    SELL_CONTROLLER.enabled = use_sell_ppo
    SELL_CONTROLLER.training = use_sell_ppo
    if use_strategy_ppo:
        STRATEGY_CONTROLLER.enabled = True
    return use_strategy_ppo

def run_training_episode(seed, episode_steps, opponent_path, use_strategy_ppo, use_sell_ppo,
                          strategy_frozen=False):
    mem = {"weed_age": {}, "own_planted_day": {}, "completed_project_steps": {}, "failure_count": {}}
    prev_strategy = {"state": None, "action_idx": None, "log_prob": None, "value": None, "worth": None, "cfg": None, "due_turn": -1}
    pending_sell = []
    held_state = {}

    for _ctrl in REINFORCE_CONTROLLERS.values():
        _ctrl.reset_episode()

    ANIMAL_OPTIMIZE_LOG.clear()
    ANIMAL_GATE_LOG.clear()
    ANIMAL_CANDIDATE_LOG.clear()
    CROP_GATE_LOG.clear()
    ANIMAL_ENV_ACTION_LOG.clear()

    def agent(obs, config=None):
        ws = build_world_state(obs)
        worth = _estimate_net_worth(ws)

        if use_strategy_ppo and strategy_frozen:
            state = build_strategy_state(ws, None)
            cfg, _, _, _ = STRATEGY_CONTROLLER.select(state, greedy=True)
        elif use_strategy_ppo:
            # FIX (turn-vs-horizon): keep using the held cfg until due_turn;
            # only resample + credit the deferred reward once the hold window
            # (STRATEGY_PPO_HOLD_TURNS) has elapsed.
            if prev_strategy["state"] is not None and ws.turn_in_episode < prev_strategy["due_turn"]:
                cfg = prev_strategy["cfg"]
            else:
                if prev_strategy["state"] is not None:
                    delta = worth - prev_strategy["worth"]
                    reward = math.tanh(delta / STRATEGY_PPO_REWARD_SCALE)  # FIX: rescaled for day-level hold
                    STRATEGY_CONTROLLER.record(prev_strategy["state"], prev_strategy["action_idx"],
                                                prev_strategy["log_prob"], prev_strategy["value"], reward, False)
                state = build_strategy_state(ws, None)
                cfg, action_idx, log_prob, value = STRATEGY_CONTROLLER.select(state, greedy=False)
                prev_strategy["state"], prev_strategy["action_idx"] = state, action_idx
                prev_strategy["log_prob"], prev_strategy["value"], prev_strategy["worth"] = log_prob, value, worth
                prev_strategy["cfg"] = cfg
                prev_strategy["due_turn"] = ws.turn_in_episode + STRATEGY_PPO_HOLD_TURNS
        else:
            cfg = default_strategy_controller(ws)

        if use_sell_ppo:
            if pending_sell:
                still_pending = []
                for tr in pending_sell:
                    if ws.turn_in_episode >= tr["due_turn"]:
                        price_after = ws.prices.get(tr["product"], tr["price_before"])
                        held_qty = tr["qty_before"] - round(tr["qty_before"] * tr["fraction"])
                        qty_sold = tr["qty_before"] - held_qty
                        local_delta = _stage4c2_incremental_reward_delta(
                            qty_sold, tr["price_before"], price_after)
                        reward = _stage4c2_pct_reward(local_delta)
                        SELL_CONTROLLER.record(tr["state"], tr["action_idx"], tr["log_prob"],
                                                tr["value"], reward, False)
                    else:
                        still_pending.append(tr)
                pending_sell[:] = still_pending

            def _record(product, state, idx, log_prob, value, fraction, _ws=ws):
                pending_sell.append(dict(product=product, state=state, action_idx=idx, log_prob=log_prob,
                                          value=value, fraction=fraction, qty_before=_ws.shed.get(product, 0),
                                          price_before=_ws.prices.get(product, 0.0),
                                          due_turn=_ws.turn_in_episode + SELL_PPO_REWARD_HORIZON_TURNS))
            sell_fn = lambda ws_, f, ob, ocp: compute_sell_fractions_ppo_4c_persistent(
                ws_, SELL_CONTROLLER, held_state, persist_turns=SELL_DECISION_PERSIST_TURNS,
                forecast=f, opponent_belief=ob, opponent_crop_pressure=ocp, greedy=False, record_fn=_record)
            env_action, _, _ = run_turn_with_sell_fn(ws, mem, strategy=cfg, use_sell_fraction=True,
                                                      sell_fraction_fn=sell_fn)
        else:
            env_action, _, _ = run_turn_with_sell_fn(ws, mem, strategy=cfg, use_sell_fraction=False)
        return env_action

    env = _kaggle_make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=False)
    result = env.run([agent, opponent_path])
    final_money = result[-1][0]["observation"]["farms"][0]["money"]
    final_ws = build_world_state(result[-1][0]["observation"])
    net_worth = _estimate_net_worth(final_ws)

    # FIX (reward metric): same as train_production_priority_v2 -- terminal
    # update used to be pure tanh(delta_own_money), ignoring win/loss.
    # Add a win-bonus from this episode's outcome for Strategy PPO too.
    opponent_final_ws = build_world_state(result[-1][1]["observation"])
    opponent_net_worth = _estimate_net_worth(opponent_final_ws)
    win_bonus = TRAINING_WIN_BONUS_WEIGHT * (1.0 if net_worth > opponent_net_worth else -1.0)
    del env, result, agent

    if use_strategy_ppo and not strategy_frozen and prev_strategy["state"] is not None:
        delta = net_worth - prev_strategy["worth"]  # DIAG-FIX: was final_money (cash-only) vs net_worth (cash+land+animals+shed) -- unit mismatch, saturated tanh to ~-1 almost every episode
        reward = math.tanh(delta / STRATEGY_PPO_REWARD_SCALE) + win_bonus  # FIX: rescaled for day-level hold
        STRATEGY_CONTROLLER.record(prev_strategy["state"], prev_strategy["action_idx"],
                                    prev_strategy["log_prob"], prev_strategy["value"], reward, True)
    if use_sell_ppo and pending_sell:
        # FIX (reward metric, part 4): pending sells past due_turn at episode end
        # used to get a flat 0.0, discarding local outcome and win/loss signal.
        # Compute the same local reward as mid-episode, then add win_bonus.
        for tr in pending_sell:
            price_after = final_ws.prices.get(tr["product"], tr["price_before"])
            held_qty = tr["qty_before"] - round(tr["qty_before"] * tr["fraction"])
            qty_sold = tr["qty_before"] - held_qty
            local_delta = _stage4c2_incremental_reward_delta(qty_sold, tr["price_before"], price_after)
            reward = _stage4c2_pct_reward(local_delta) + win_bonus
            SELL_CONTROLLER.record(tr["state"], tr["action_idx"], tr["log_prob"], tr["value"], reward, True)

    # FIX (reward metric, part 3): win_outcome now passed as its OWN argument
    # to every REINFORCE controller -- previously FloorCap/RateCap got no
    # win/loss signal, Alpha/Animal only got it pre-baked into raw net_worth.
    win_outcome = 1.0 if net_worth > opponent_net_worth else -1.0
    for ctrl in REINFORCE_CONTROLLERS.values():
        if ctrl.enabled and ctrl.training:
            ctrl.update(net_worth, win_outcome=win_outcome)

    return net_worth, final_money

def run_stage(stage_name, n_episodes, active_reinforce, use_strategy_ppo, use_sell_ppo,
              rate_sub_flags=None, episode_steps=None, opponent_pool=None,
              patience=None, min_delta=0.0, window=3, strategy_frozen=False,
              min_updates_for_early_stop=15, entropy_gate_ratio=0.9):
    if not HAVE_KAGGLE_ENV:
        raise RuntimeError(
            "kaggle_environments is not installed. Run "
            "`pip install kaggle_environments` before calling run_stage()."
        )
    episode_steps = episode_steps or EPISODE_STEPS_DEFAULT
    opponent_pool = opponent_pool or [make_agent(safe=True)]
    set_stage_flags(active_reinforce, use_strategy_ppo, use_sell_ppo, rate_sub_flags)

    print(f"\n{'='*70}\n{stage_name}\n{'='*70}")
    print(f"active REINFORCE controllers: {sorted(active_reinforce) or 'none'} | "
          f"PPO Strategy: {use_strategy_ppo}{' (frozen)' if strategy_frozen else ''} | "
          f"PPO Sell: {use_sell_ppo} | rate sub-flags: {rate_sub_flags}")
    if patience is not None:
        print(f"early stopping: patience={patience} window={window} min_delta={min_delta}")

    t0 = time.time()
    returns = []
    money_history = []
    best_trailing_mean = -float("inf")
    no_improve_checks = 0
    converged_stop = False
    timed_out = False
    ep = -1
    while True:
        ep += 1
        if ep >= MAX_EPISODES_SAFETY:
            print(f"  [!] hit absolute safety ceiling of {MAX_EPISODES_SAFETY} episodes -- stopping "
                  f"(this should not normally happen; check convergence gate / reward scale)")
            break
        if time_budget_exceeded():
            print(f"  [!] GLOBAL TIME BUDGET EXCEEDED mid-stage at ep {ep} -- stopping this stage now. "
                  f"It will NOT be frozen/used downstream (treated as not converged).")
            timed_out = True
            break
        _ep_t0 = time.time()
        seed = _random.randint(0, 10 ** 6)
        opponent_path = opponent_pool[ep % len(opponent_pool)]
        net_worth, money = run_training_episode(seed, episode_steps, opponent_path, use_strategy_ppo, use_sell_ppo,
                                                  strategy_frozen=strategy_frozen)
        returns.append(net_worth)
        money_history.append(money)
        if ep % 5 == 0:
            import gc as _gc_stage
            _gc_stage.collect()
        print(f"  ep {ep:3d} | money={money:>10,.0f} | net_worth={net_worth:>10,.0f} | "
              f"time={time.time()-_ep_t0:.1f}s | mem={_process_mem_mb():,.0f}MB")

        if patience is None:
            # no plateau/convergence gate configured at all -- only sane stopping
            # rule left is the soft n_episodes target (preserves old behavior for
            # any caller that doesn't pass patience=...).
            if ep + 1 >= n_episodes:
                converged_stop = True
                break
            continue

        if patience is not None and len(returns) >= window:
            trailing_window = returns[-window:]
            trailing_mean = _stats.mean(trailing_window)
            trailing_std = _stats.pstdev(trailing_window) if len(trailing_window) > 1 else 0.0
            trailing_sem = trailing_std / (window ** 0.5)
            eff_min_delta = max(min_delta, SEM_K * trailing_sem)
            if trailing_mean > best_trailing_mean + eff_min_delta:
                best_trailing_mean = trailing_mean
                no_improve_checks = 0
            else:
                no_improve_checks += 1
            if no_improve_checks >= patience:
                # GATE (bug: early-stop firing before policy learned anything):
                # trailing-mean plateau only means "converged" once the policy
                # has differentiated away from uniform. Checks both strategy/sell PPO.
                gate_blocked = False
                gate_reasons = []
                # PPO controllers: checked via entropy convergence (low ratio = converged).
                _ppo_controllers_to_check = []
                if use_strategy_ppo and not strategy_frozen:
                    _ppo_controllers_to_check.append(("strategy_ppo", STRATEGY_CONTROLLER))
                if use_sell_ppo:
                    _ppo_controllers_to_check.append(("sell_ppo", SELL_CONTROLLER))
                for cname, ctrl in _ppo_controllers_to_check:
                    ed = ctrl._entropy_convergence()
                    n_upd = ed["n_updates_total"]
                    ratio = ed["ratio"]
                    if n_upd < min_updates_for_early_stop:
                        gate_blocked = True
                        gate_reasons.append(f"{cname}: n_updates_total={n_upd} < "
                                             f"min_updates_for_early_stop={min_updates_for_early_stop}")
                    elif ratio is not None and ratio >= entropy_gate_ratio:
                        gate_blocked = True
                        gate_reasons.append(f"{cname}: entropy_ratio={ratio:.2f} >= "
                                             f"entropy_gate_ratio={entropy_gate_ratio} (still near-uniform)")

                # GATE COVERAGE FIX: floorcap/rate/reorder/alpha/animal were never
                # checked here, so a noisy plateau could freeze them unlearned. Now
                # every active REINFORCE controller is checked via _convergence_diag().
                _reinforce_controllers_to_check = []
                if RL_FLOORCAP_CONTROLLER.enabled:
                    _reinforce_controllers_to_check.append(("floorcap", RL_FLOORCAP_CONTROLLER))
                if RL_CROP_MIX_CONTROLLER.enabled:
                    _reinforce_controllers_to_check.append(("alpha", RL_CROP_MIX_CONTROLLER))
                if RL_ANIMAL_CONTROLLER.enabled:
                    _reinforce_controllers_to_check.append(("animal", RL_ANIMAL_CONTROLLER))
                if RL_RATE_CONTROLLER.enabled:
                    _reinforce_controllers_to_check.append(("rate", RL_RATE_CONTROLLER))
                if RL_REORDER_CONTROLLER.enabled:
                    _reinforce_controllers_to_check.append(("reorder", RL_REORDER_CONTROLLER))
                for cname, ctrl in _reinforce_controllers_to_check:
                    cd = ctrl._convergence_diag()
                    n_dec = cd["n_decisions_total"]
                    if n_dec < min_updates_for_early_stop:
                        gate_blocked = True
                        gate_reasons.append(f"{cname}: n_decisions_total={n_dec} < "
                                             f"min_updates_for_early_stop={min_updates_for_early_stop}")
                    elif not cd["converged"]:
                        wr = cd["worst_ratio"]
                        wr_str = f"{wr:.2f}" if wr is not None else "n/a"
                        gate_blocked = True
                        gate_reasons.append(f"{cname}: worst_head_ratio={wr_str} < 0.5 "
                                             f"(head={cd.get('worst_head') or cd.get('worst_crop')}, not converged)")
                gate_reason = "; ".join(gate_reasons)
                if gate_blocked:
                    if ep % 5 == 0:
                        print(f"  [early-stop gate] blocked at ep {ep}: {gate_reason} -- continuing")
                    no_improve_checks = patience - 1  # keep re-checking each subsequent episode
                else:
                    print(f"  -> early stop at ep {ep} "
                          f"(trailing {window}-ep mean hasn't improved by >={eff_min_delta:,.0f} "
                          f"[floor min_delta={min_delta:,.0f}, {SEM_K}*SEM={SEM_K*trailing_sem:,.0f}] "
                          f"for {patience} checks, AND all active controllers have converged)")
                    converged_stop = True
                    break

    if returns:
        print(f"{stage_name} DONE | episodes_run={len(returns)} (soft target was {n_episodes}) | "
              f"mean_money={_stats.mean(money_history):,.0f} std_money={_stats.pstdev(money_history):,.0f} | "
              f"mean_net_worth={_stats.mean(returns):,.0f} std_net_worth={_stats.pstdev(returns):,.0f} | "
              f"time={time.time()-t0:.1f}s")
    else:
        print(f"{stage_name} DONE | episodes_run=0 (soft target was {n_episodes}) | "
              f"stopped before completing a single episode | time={time.time()-t0:.1f}s")
    if use_strategy_ppo and not strategy_frozen:
        ed = STRATEGY_CONTROLLER._entropy_convergence()
        if ed["ratio"] is not None:
            warn = "  [!] NOT CONVERGED -- policy still near-uniform, treat results as noisy" \
                if not ed["converged"] else "  [ok] policy is sufficiently differentiated"
            print(f"  strategy_ppo entropy_ratio={ed['ratio']:.2f} (mean_entropy={ed['mean_entropy']:.3f} / "
                  f"max={ed['max_entropy']:.3f}, n_updates={ed['n_updates_total']}){warn}")
        else:
            print("  strategy_ppo entropy_diag: no update recorded yet (batch never filled)")
    elif use_strategy_ppo and strategy_frozen:
        print("  strategy_ppo: FROZEN this stage (greedy, not trained) -- entropy diag skipped")

    if use_sell_ppo:
        ed = SELL_CONTROLLER._entropy_convergence()
        if ed["ratio"] is not None:
            warn = "  [!] NOT CONVERGED -- policy still near-uniform, treat results as noisy" \
                if not ed["converged"] else "  [ok] policy is sufficiently differentiated"
            print(f"  sell_ppo entropy_ratio={ed['ratio']:.2f} (mean_entropy={ed['mean_entropy']:.3f} / "
                  f"max={ed['max_entropy']:.3f}, n_updates={ed['n_updates_total']}){warn}")
        else:
            print("  sell_ppo entropy_diag: no update recorded yet (batch never filled)")

    if "alpha" in active_reinforce:
        ad = RL_CROP_MIX_CONTROLLER._convergence_diag()
        if ad["worst_ratio"] is not None:
            warn = "  [!] NOT CONVERGED -- decisions still noise-dominated" \
                if not ad["converged"] else "  [ok] state-conditioned signal exceeds noise"
            print(f"  alpha_rl worst signal/noise_ratio={ad['worst_ratio']:.2f} "
                  f"(crop={ad['worst_crop']}, n_decisions_total={ad['n_decisions_total']}){warn}")
            print(f"    per-crop ratios: {ad['ratios']}")
        else:
            print("  alpha_rl diag: not enough decisions recorded yet")

    if "animal" in active_reinforce:
        nd = RL_ANIMAL_CONTROLLER._convergence_diag()
        if nd["worst_ratio"] is not None:
            warn = "  [!] NOT CONVERGED -- decisions still noise-dominated" \
                if not nd["converged"] else "  [ok] state-conditioned signal exceeds noise"
            print(f"  animal_rl worst signal/noise_ratio={nd['worst_ratio']:.2f} "
                  f"(head={nd['worst_head']}, n_decisions_total={nd['n_decisions_total']}){warn}")
            print(f"    per-head ratios: {nd['ratios']}")
        else:
            print("  animal_rl diag: not enough decisions recorded yet")

    if timed_out:
        print(f"  [!] STAGE STOPPED BY GLOBAL TIME BUDGET, NOT CONVERGED -- caller should NOT "
              f"freeze this stage's controllers into FROZEN_STAGE_AGENTS.")
    return {"returns": returns, "converged": converged_stop, "timed_out": timed_out}

def eval_agent_vs_agent(agent_a, agent_b, eval_seeds, episode_steps=None):
    """Generic head-to-head eval: any two self-contained (obs, config) ->
    action callables (a FROZEN_STAGE_AGENTS entry, make_agent(safe=True), or
    a freshly-built candidate snapshot), seat-swap NOT included here (caller
"""
    episode_steps = episode_steps or EPISODE_STEPS_DEFAULT
    net_worth_a, net_worth_b = [], []
    for seed in eval_seeds:
        env = _kaggle_make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=False)
        result = env.run([agent_a, agent_b])
        net_worth_a.append(_estimate_net_worth(build_world_state(result[-1][0]["observation"])))
        net_worth_b.append(_estimate_net_worth(build_world_state(result[-1][1]["observation"])))
        del env, result
    return net_worth_a, net_worth_b


def eval_agent_vs_baseline(agent_path, eval_seeds, episode_steps=None):
    """Backward-compat thin wrapper: agent vs a fresh rule-based baseline."""
    return eval_agent_vs_agent(agent_path, make_agent(safe=True), eval_seeds, episode_steps=episode_steps)


def get_reference_agent(reference_key):
    """'baseline' -> a fresh rule-based agent; any other key -> its frozen
    snapshot from FROZEN_STAGE_AGENTS (must already exist)."""
    if reference_key == "baseline":
        return make_agent(safe=True)
    return FROZEN_STAGE_AGENTS[reference_key]


def run_stage_curriculum(stage_key, stage_name, reference_key, run_kwargs, stage_config,
                          eval_seeds=(701, 702, 703, 704, 705), win_margin=0.0, max_attempts=15):
    """TWO gates, in order, per attempt:
    Gate 1 (convergence): run_stage() with real patience/window/min_delta
      from stage_config -- trains until ITS OWN plateau+diagnostic
    """
    reference_agent = get_reference_agent(reference_key)
    _FREEZE_ALLOWED_KEYS = {"active_reinforce", "use_strategy_ppo", "use_sell_ppo",
                             "rate_sub_flags", "production_priority_controller",
                             "production_state_builder", "production_persist_turns"}
    _freeze_kwargs = {k: v for k, v in run_kwargs.items() if k in _FREEZE_ALLOWED_KEYS}
    total_episodes_run = 0
    last_eval = None

    for attempt_i in range(1, max_attempts + 1):
        if time_budget_exceeded():
            print(f"  [{stage_name}] global time budget exhausted before attempt {attempt_i} -- "
                  f"stopping curriculum loop (not accepted)")
            return {"beats_reference": False, "timed_out": True,
                    "n_episodes_run": total_episodes_run, "n_attempts_run": attempt_i - 1,
                    "last_eval": last_eval}

        print(f"\n  [{stage_name}] -- GATE 1 (convergence), attempt {attempt_i}/{max_attempts} "
              f"(cumulative so far: {total_episodes_run} episodes) --")
        _attempt_result = run_stage(f"{stage_name} (attempt {attempt_i})",
                                     n_episodes=stage_config["n_episodes"],
                                     patience=stage_config["patience"], window=stage_config["window"],
                                     min_delta=stage_config["min_delta"], **run_kwargs)
        total_episodes_run += len(_attempt_result["returns"])
        if _attempt_result["timed_out"]:
            print(f"  [{stage_name}] time budget ran out mid-attempt {attempt_i} -- stopping (not accepted)")
            return {"beats_reference": False, "timed_out": True,
                    "n_episodes_run": total_episodes_run, "n_attempts_run": attempt_i,
                    "last_eval": last_eval}
        if not _attempt_result["converged"]:
            # shouldn't normally happen (run_stage only returns without
            # converged=True on a timeout, already handled above) -- but
            # guard anyway rather than silently proceeding to Gate 2.
            print(f"  [{stage_name}] GATE 1 FAILED (not converged) on attempt {attempt_i} -- retrying")
            continue
        print(f"  [{stage_name}] GATE 1 PASSED (converged) on attempt {attempt_i} -- proceeding to GATE 2")

        print(f"  [{stage_name}] -- GATE 2 (beat '{reference_key}'), attempt {attempt_i} --")
        candidate_agent = freeze_agent_snapshot(f"{stage_key}_candidate_attempt{attempt_i}", **_freeze_kwargs)
        net_worth_cand, net_worth_ref = eval_agent_vs_agent(candidate_agent, reference_agent, list(eval_seeds))
        deltas = [c - r for c, r in zip(net_worth_cand, net_worth_ref)]
        mean_delta = _stats.mean(deltas)
        mean_ref = _stats.mean(net_worth_ref)
        win_rate = sum(1 for d in deltas if d > 0) / len(deltas)
        last_eval = {"mean_delta": mean_delta, "win_rate": win_rate, "deltas": deltas,
                      "mean_candidate": _stats.mean(net_worth_cand), "mean_reference": mean_ref}
        threshold = win_margin * abs(mean_ref)
        passed = (mean_delta > threshold) and (win_rate >= 0.5)
        print(f"  [{stage_name}] GATE 2 eval vs '{reference_key}' "
              f"({len(eval_seeds)} seeds): candidate={last_eval['mean_candidate']:,.0f} "
              f"reference={mean_ref:,.0f} delta={mean_delta:+,.0f} win_rate={win_rate:.0%} "
              f"| {'PASS' if passed else 'not yet -- will keep training and re-check both gates'}")
        if passed:
            print(f"  [{stage_name}] BOTH GATES PASSED after {attempt_i} attempt(s) "
                  f"({total_episodes_run} total episodes) -- ACCEPTED.")
            return {"beats_reference": True, "timed_out": False,
                    "n_episodes_run": total_episodes_run, "n_attempts_run": attempt_i,
                    "last_eval": last_eval}

    print(f"  [{stage_name}] still hasn't beaten '{reference_key}' after {max_attempts} attempts "
          f"({total_episodes_run} episodes) -- giving up, NOT accepted.")
    return {"beats_reference": False, "timed_out": False,
            "n_episodes_run": total_episodes_run, "n_attempts_run": max_attempts, "last_eval": last_eval}


def run_stage_curriculum_4x(stage_key, stage_name, reference_key, controller, state_builder,
                             active_reinforce, use_strategy_ppo, use_sell_ppo, rate_sub_flags,
                             stage_config, eval_seeds=(701, 702, 703, 704, 705),
                             win_margin=0.0, max_attempts=15):
    """Same two-gate loop as run_stage_curriculum(), but for the
    production-priority stages (4A/4B): Gate 1 = train_production_priority_v2()
    with real patience/window/min_delta until ITS OWN convergence; Gate 2 = beat reference_key.
    """
    reference_agent = get_reference_agent(reference_key)
    total_episodes_run = 0
    last_eval = None

    for attempt_i in range(1, max_attempts + 1):
        if time_budget_exceeded():
            print(f"  [{stage_name}] global time budget exhausted before attempt {attempt_i} -- "
                  f"stopping curriculum loop (not accepted)")
            return {"beats_reference": False, "timed_out": True,
                    "n_episodes_run": total_episodes_run, "n_attempts_run": attempt_i - 1,
                    "last_eval": last_eval}

        print(f"\n  [{stage_name}] -- GATE 1 (convergence), attempt {attempt_i}/{max_attempts} "
              f"(cumulative so far: {total_episodes_run} episodes) --")
        _attempt_result = train_production_priority_v2(
            controller, state_builder, opponent_pool=[reference_agent],
            n_episodes=stage_config["n_episodes"], patience=stage_config["patience"],
            window=stage_config["window"], min_delta=stage_config["min_delta"], verbose=True)
        total_episodes_run += len(_attempt_result["returns"])
        if _attempt_result["timed_out"]:
            print(f"  [{stage_name}] time budget ran out mid-attempt {attempt_i} -- stopping (not accepted)")
            return {"beats_reference": False, "timed_out": True,
                    "n_episodes_run": total_episodes_run, "n_attempts_run": attempt_i,
                    "last_eval": last_eval}
        if not _attempt_result["converged"]:
            print(f"  [{stage_name}] GATE 1 FAILED (not converged) on attempt {attempt_i} -- retrying")
            continue
        print(f"  [{stage_name}] GATE 1 PASSED (converged) on attempt {attempt_i} -- proceeding to GATE 2")

        print(f"  [{stage_name}] -- GATE 2 (beat '{reference_key}'), attempt {attempt_i} --")
        candidate_agent = freeze_agent_snapshot(
            f"{stage_key}_candidate_attempt{attempt_i}", active_reinforce=active_reinforce,
            use_strategy_ppo=use_strategy_ppo, use_sell_ppo=use_sell_ppo,
            rate_sub_flags=rate_sub_flags, production_priority_controller=controller,
            production_state_builder=state_builder)
        net_worth_cand, net_worth_ref = eval_agent_vs_agent(candidate_agent, reference_agent, list(eval_seeds))
        deltas = [c - r for c, r in zip(net_worth_cand, net_worth_ref)]
        mean_delta = _stats.mean(deltas)
        mean_ref = _stats.mean(net_worth_ref)
        win_rate = sum(1 for d in deltas if d > 0) / len(deltas)
        last_eval = {"mean_delta": mean_delta, "win_rate": win_rate, "deltas": deltas,
                      "mean_candidate": _stats.mean(net_worth_cand), "mean_reference": mean_ref}
        threshold = win_margin * abs(mean_ref)
        passed = (mean_delta > threshold) and (win_rate >= 0.5)
        print(f"  [{stage_name}] GATE 2 eval vs '{reference_key}' "
              f"({len(eval_seeds)} seeds): candidate={last_eval['mean_candidate']:,.0f} "
              f"reference={mean_ref:,.0f} delta={mean_delta:+,.0f} win_rate={win_rate:.0%} "
              f"| {'PASS' if passed else 'not yet -- will keep training and re-check both gates'}")
        if passed:
            print(f"  [{stage_name}] BOTH GATES PASSED after {attempt_i} attempt(s) "
                  f"({total_episodes_run} total episodes) -- ACCEPTED.")
            return {"beats_reference": True, "timed_out": False,
                    "n_episodes_run": total_episodes_run, "n_attempts_run": attempt_i,
                    "last_eval": last_eval}

    print(f"  [{stage_name}] still hasn't beaten '{reference_key}' after {max_attempts} attempts "
          f"({total_episodes_run} episodes) -- giving up, NOT accepted.")
    return {"beats_reference": False, "timed_out": False,
            "n_episodes_run": total_episodes_run, "n_attempts_run": max_attempts, "last_eval": last_eval}


def run_baseline(n_episodes, episode_steps=None, opponent_pool=None):
    if not HAVE_KAGGLE_ENV:
        raise RuntimeError(
            "kaggle_environments is not installed. Run "
            "`pip install kaggle_environments` before calling run_baseline()."
        )
    episode_steps = episode_steps or EPISODE_STEPS_DEFAULT
    opponent_pool = opponent_pool or [make_agent(safe=True)]
    set_stage_flags(active_reinforce=(), use_strategy_ppo=False, use_sell_ppo=False)
    print(f"\n{'='*70}\nSTAGE 0 - BASELINE (all controllers OFF)\n{'='*70}")
    t0 = time.time()
    results = []
    for ep in range(n_episodes):
        _ep_t0 = time.time()
        seed = _random.randint(0, 10 ** 6)
        opponent_path = opponent_pool[ep % len(opponent_pool)]
        agent = make_agent(safe=True)
        env = _kaggle_make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=False)
        r = env.run([agent, opponent_path])
        money = r[-1][0]["observation"]["farms"][0]["money"]
        results.append(money)
        del env, r, agent
        ANIMAL_OPTIMIZE_LOG.clear()
        ANIMAL_GATE_LOG.clear()
        ANIMAL_CANDIDATE_LOG.clear()
        CROP_GATE_LOG.clear()
        ANIMAL_ENV_ACTION_LOG.clear()
        if ep % 5 == 0:
            import gc as _gc_baseline
            _gc_baseline.collect()
        print(f"  ep {ep:3d} | money={money:>10,.0f} | time={time.time()-_ep_t0:.1f}s | "
              f"mem={_process_mem_mb():,.0f}MB")
    print(f"STAGE 0 DONE | mean={_stats.mean(results):,.0f} std={_stats.pstdev(results):,.0f} "
          f"| time={time.time()-t0:.1f}s")
    return results


# FIX (opponent curriculum): every stage used to face the same static pool,
# risking overfit. Now each stage's controllers snapshot into FROZEN_STAGE_AGENTS;
# RL_*_CONTROLLER globals swap temporarily during a frozen opponent's turn.
import copy as _copy_stage_snapshot
import dataclasses as _dataclasses_stage_snapshot

_GLOBAL_CONTROLLER_NAMES = (
    "RL_FLOORCAP_CONTROLLER", "RL_CROP_MIX_CONTROLLER", "RL_ANIMAL_CONTROLLER",
    "RL_RATE_CONTROLLER", "RL_REORDER_CONTROLLER", "STRATEGY_CONTROLLER", "SELL_CONTROLLER",
)
_CONTROLLER_SHORT_NAME = {
    "RL_FLOORCAP_CONTROLLER": "floorcap", "RL_CROP_MIX_CONTROLLER": "alpha",
    "RL_ANIMAL_CONTROLLER": "animal", "RL_RATE_CONTROLLER": "rate",
    "RL_REORDER_CONTROLLER": "reorder",
}

FROZEN_STAGE_AGENTS = {}   # stage_key -> frozen opponent agent callable (cumulative registry)

def freeze_agent_snapshot(name, active_reinforce, use_strategy_ppo, use_sell_ppo,
                           rate_sub_flags=None, production_priority_controller=None,
                           production_state_builder=None, production_persist_turns=None):
    """Deep-copy every controller active as of the END of a training stage into
    an eval-mode (training=False) snapshot, and wrap it into a self-contained
    opponent agent usable in LATER stages' opponent_pool. See the module-level
"""
    frozen = {k: _copy_stage_snapshot.deepcopy(globals()[k]) for k in _GLOBAL_CONTROLLER_NAMES}
    for gname, short in _CONTROLLER_SHORT_NAME.items():
        ctrl = frozen[gname]
        ctrl.enabled = short in active_reinforce
        ctrl.training = False
    if rate_sub_flags is not None:
        frozen["RL_RATE_CONTROLLER"].enabled_animal = rate_sub_flags.get("animal", False)
        frozen["RL_RATE_CONTROLLER"].enabled_plant = rate_sub_flags.get("plant", False)
        frozen["RL_ANIMAL_CONTROLLER"].enabled_idle = rate_sub_flags.get("animal_idle", False)
    frozen["STRATEGY_CONTROLLER"].enabled = use_strategy_ppo
    frozen["SELL_CONTROLLER"].enabled = use_sell_ppo
    frozen["SELL_CONTROLLER"].training = False

    frozen_prod_ctrl = (_copy_stage_snapshot.deepcopy(production_priority_controller)
                         if production_priority_controller is not None else None)

    mem = {"weed_age": {}, "own_planted_day": {}, "completed_project_steps": {}, "failure_count": {}}
    held_state = {}
    held_prod = {"cfg": None, "next_select_turn": -1}

    def agent(obs, config=None):
        _live = {k: globals()[k] for k in _GLOBAL_CONTROLLER_NAMES}
        globals().update(frozen)
        try:
            ws = build_world_state(obs)

            if frozen_prod_ctrl is not None:
                if ws.turn_in_episode >= held_prod["next_select_turn"]:
                    state = production_state_builder(ws, None, mem)
                    overrides, _, _, _ = frozen_prod_ctrl.select(state, greedy=True)
                    if use_strategy_ppo:
                        base_state = build_strategy_state(ws, None)
                        base_cfg, _, _, _ = frozen["STRATEGY_CONTROLLER"].select(base_state, greedy=True)
                    else:
                        base_cfg = default_strategy_controller(ws, None)
                    # BUG FIX: manually re-listing fields used to drop
                    # animal_allocation_ratio. dataclasses.replace() copies
                    # all fields, overriding only the intended ones.
                    held_prod["cfg"] = _dataclasses_stage_snapshot.replace(
                        base_cfg,
                        investment_budget_fraction=overrides.get(
                            "investment_budget_fraction", base_cfg.investment_budget_fraction),
                        risk_aversion=overrides.get("risk_aversion", base_cfg.risk_aversion),
                    )
                    held_prod["next_select_turn"] = ws.turn_in_episode + \
                        (production_persist_turns or PRODUCTION_PRIORITY_PERSIST_TURNS)
                cfg = held_prod["cfg"]
            elif use_strategy_ppo:
                state = build_strategy_state(ws, None)
                cfg, _, _, _ = frozen["STRATEGY_CONTROLLER"].select(state, greedy=True)
            else:
                cfg = default_strategy_controller(ws, None)

            if use_sell_ppo:
                sell_fn = lambda ws_, f, ob, ocp: compute_sell_fractions_ppo_4c_persistent(
                    ws_, frozen["SELL_CONTROLLER"], held_state,
                    persist_turns=SELL_DECISION_PERSIST_TURNS,
                    forecast=f, opponent_belief=ob, opponent_crop_pressure=ocp, greedy=True)
                env_action, _, _ = run_turn_with_sell_fn(ws, mem, strategy=cfg, use_sell_fraction=True,
                                                          sell_fraction_fn=sell_fn)
            else:
                env_action, _, _ = run_turn_with_sell_fn(ws, mem, strategy=cfg, use_sell_fraction=False)
            return env_action
        finally:
            globals().update(_live)

    agent.mem = mem
    agent.__frozen_stage_name__ = name
    return make_safe_agent(agent)


def build_curriculum_opponent_pool(prior_stage_keys, batch_size=20):
    """Cumulative, BATCHED opponent pool: each stage in `prior_stage_keys`
    contributes a contiguous block of `batch_size` episodes (not shuffled
    per-episode), so opponent_pool[ep % len(pool)] -- as already used inside
"""
    pool = []
    for stage_key in prior_stage_keys:
        pool.extend([FROZEN_STAGE_AGENTS[stage_key]] * batch_size)
    return pool


# CHANGED: stopping condition is convergence, not n_episodes (now a soft
# target). Only hard ceiling is the wall-clock budget below -- if exceeded,
# discard the current (unconverged) stage and fall back to the last converged one.
STAGE_CONFIG = {
    "baseline": dict(n_episodes=15),
    "1":        dict(n_episodes=200, patience=20, window=12, min_delta=400),
    "2a":       dict(n_episodes=200, patience=22, window=13, min_delta=350),
    "2b":       dict(n_episodes=200, patience=22, window=13, min_delta=350),
    "2c":       dict(n_episodes=200, patience=18, window=12, min_delta=300),
    "3a":       dict(n_episodes=200, patience=22, window=15, min_delta=250),
    "3b":       dict(n_episodes=200, patience=26, window=18, min_delta=200),
    "3c":       dict(n_episodes=200, patience=28, window=20, min_delta=175),
}

run_baseline(STAGE_CONFIG["baseline"]["n_episodes"])

print(f"\n{'='*70}\nMarkov validation (early, feeds _crop_net_economics for ALL stages)\n{'='*70}")
STAGE_CONFIG["markov_validation"] = dict(n_episodes=10)
_stage4b_validation = run_markov_self_play_validation(
    n_episodes=STAGE_CONFIG["markov_validation"]["n_episodes"], verbose=False)
_stage4b_matrices = select_validated_transition_matrices(_stage4b_validation, require_beats_persistence=False)
_stage4b_counts = select_validated_transition_counts(_stage4b_validation, require_beats_persistence=False)
print(f"validated products (beats_uniform, persistence not required): {sorted(_stage4b_matrices.keys())}")
set_markov_forecast_state(_stage4b_matrices, _stage4b_counts)

FROZEN_STAGE_AGENTS["baseline"] = make_agent(safe=True)

# ---- start the 11.5h global clock now, right before the first RL stage ----
start_global_time_budget(hours=11.5)

LAST_CONVERGED_STAGE_KEY = "baseline"   # fallback anchor if every RL stage times out
PIPELINE_STOPPED_EARLY = False

# CHANGED (curriculum redesign): each stage's opponent -- during training AND
# for the pass/fail gate -- is now its single immediate predecessor, not a
# diluted multi-stage pool. A real run showed the diluted pool let later
_stage_specs = [
    ("1",  "STAGE 1 - Floor-Cap RL + PPO Strategy", "baseline",
     dict(active_reinforce={"floorcap"}, use_strategy_ppo=True, use_sell_ppo=False)),
    ("2a", "STAGE 2A - + Bootstrap Alpha RL only", "1",
     dict(active_reinforce={"floorcap", "alpha"}, use_strategy_ppo=True, use_sell_ppo=False,
          strategy_frozen=True)),
    ("2b", "STAGE 2B - + Animal RL", "2a",
     dict(active_reinforce={"floorcap", "alpha", "animal"}, use_strategy_ppo=True, use_sell_ppo=False,
          strategy_frozen=True)),
    ("2c", "STAGE 2C - + PPO Sell Fraction", "2b",
     dict(active_reinforce={"floorcap", "alpha", "animal"}, use_strategy_ppo=True, use_sell_ppo=True,
          strategy_frozen=True)),
    ("3a", "STAGE 3A - + Rate-Cap RL (Structure)", "2c",
     dict(active_reinforce={"floorcap", "alpha", "animal", "rate"}, use_strategy_ppo=True, use_sell_ppo=True,
          strategy_frozen=True, rate_sub_flags={"animal": False, "plant": False})),
    ("3b", "STAGE 3B - + Rate-Cap RL (Animal)", "3a",
     dict(active_reinforce={"floorcap", "alpha", "animal", "rate"}, use_strategy_ppo=True, use_sell_ppo=True,
          strategy_frozen=True, rate_sub_flags={"animal": True, "plant": False, "animal_idle": True})),
    ("3c", "STAGE 3C - + Rate-Cap RL (Plant) + Reorder RL", "3b",
     dict(active_reinforce={"floorcap", "alpha", "animal", "rate", "reorder"},
          use_strategy_ppo=True, use_sell_ppo=True, strategy_frozen=True,
          rate_sub_flags={"animal": True, "plant": True, "animal_idle": True})),
]

for _key, _name, _reference_key, _kwargs in _stage_specs:
    if time_budget_exceeded():
        print(f"\n[pipeline] global time budget already exhausted before {_name} -- "
              f"skipping remaining stages, falling back to '{LAST_CONVERGED_STAGE_KEY}'")
        PIPELINE_STOPPED_EARLY = True
        break
    _run_kwargs = dict(_kwargs)
    _run_kwargs["opponent_pool"] = [get_reference_agent(_reference_key)]
    _curr_result = run_stage_curriculum(
        _key, _name, _reference_key, _run_kwargs, STAGE_CONFIG[_key],
        eval_seeds=(701, 702, 703, 704, 705), win_margin=0.0, max_attempts=15)
    if not _curr_result["beats_reference"]:
        print(f"\n[pipeline] {_name} did NOT beat '{_reference_key}' "
              f"(timed_out={_curr_result['timed_out']}) -- discarding it, NOT freezing into "
              f"FROZEN_STAGE_AGENTS. Falling back to '{LAST_CONVERGED_STAGE_KEY}'.")
        PIPELINE_STOPPED_EARLY = True
        break
    _freeze_kwargs = {k: v for k, v in _kwargs.items() if k != "strategy_frozen"}
    FROZEN_STAGE_AGENTS[_key] = freeze_agent_snapshot(_key, **_freeze_kwargs)
    LAST_CONVERGED_STAGE_KEY = _key

print(f"\n[pipeline] stages B0-3C phase complete. LAST_CONVERGED_STAGE_KEY = "
      f"'{LAST_CONVERGED_STAGE_KEY}' | stopped_early={PIPELINE_STOPPED_EARLY} | "
      f"time_remaining={time_budget_remaining()/3600:.2f}h")
if not PIPELINE_STOPPED_EARLY:
    print("Continue with Stage 4A/4B in the next cells.")
else:
    print("Time budget exhausted -- Stage 4A/4B will be SKIPPED. Part 14c will use "
          f"FROZEN_STAGE_AGENTS['{LAST_CONVERGED_STAGE_KEY}'] as the RL side of the tournament.")


if PIPELINE_STOPPED_EARLY:
    print(f"\n{'='*70}\nSTAGE 4A - SKIPPED (time budget already exhausted after '{LAST_CONVERGED_STAGE_KEY}')\n{'='*70}")
else:
    print(f"\n{'='*70}\nSTAGE 4A - Production Leverage Gate (minimal V1 state)\n{'='*70}")
    CONTROLLER_4A = PPOProductionPriorityControllerV2(state_dim=PRODUCTION_PRIORITY_STATE_DIM_V1)

    # CHANGED: same curriculum-gate redesign as Stages 1-3C -- Stage 4A must
    # demonstrably beat its own reference (frozen Stage 3C, i.e.
    # LAST_CONVERGED_STAGE_KEY going in) in held-out eval, not just "stop
    STAGE_CONFIG["4a"] = dict(n_episodes=200, patience=28, window=20, min_delta=150)
    _stage4a_reference_key = LAST_CONVERGED_STAGE_KEY
    _stage4a_curr = run_stage_curriculum_4x(
        "4a", "STAGE 4A", _stage4a_reference_key, CONTROLLER_4A, build_production_priority_state,
        active_reinforce={"floorcap", "alpha", "animal", "rate", "reorder"},
        use_strategy_ppo=True, use_sell_ppo=True,
        rate_sub_flags={"animal": True, "plant": True, "animal_idle": True},
        stage_config=STAGE_CONFIG["4a"], eval_seeds=(601, 602, 603, 604, 605),
        win_margin=0.0, max_attempts=15)

    if not _stage4a_curr["beats_reference"]:
        print(f"\n[pipeline] STAGE 4A did NOT beat '{_stage4a_reference_key}' "
              f"(timed_out={_stage4a_curr['timed_out']}) -- discarding it, NOT freezing. "
              f"Falling back to '{LAST_CONVERGED_STAGE_KEY}'.")
        PIPELINE_STOPPED_EARLY = True
    else:
        FROZEN_STAGE_AGENTS["4a"] = freeze_agent_snapshot(
            "4a", active_reinforce={"floorcap", "alpha", "animal", "rate", "reorder"},
            use_strategy_ppo=True, use_sell_ppo=True,
            rate_sub_flags={"animal": True, "plant": True, "animal_idle": True},
            production_priority_controller=CONTROLLER_4A,
            production_state_builder=build_production_priority_state)
        LAST_CONVERGED_STAGE_KEY = "4a"
        _le = _stage4a_curr["last_eval"]
        print(f"\nSTAGE 4A ACCEPTED | beat '{_stage4a_reference_key}' by "
              f"{_le['mean_delta']:+,.0f} (win_rate={_le['win_rate']:.0%}) after "
              f"{_stage4a_curr['n_episodes_run']} episodes")

        if time_budget_exceeded():
            print(f"\n[pipeline] global time budget ran out right after Stage 4A -- "
                  f"skipping Stage 4B. Falling back to '{LAST_CONVERGED_STAGE_KEY}'.")
            PIPELINE_STOPPED_EARLY = True

    print(f"\n[pipeline] time_remaining={time_budget_remaining()/3600:.2f}h | "
          f"LAST_CONVERGED_STAGE_KEY='{LAST_CONVERGED_STAGE_KEY}' | stopped_early={PIPELINE_STOPPED_EARLY}")


if PIPELINE_STOPPED_EARLY:
    print(f"\n{'='*70}\nSTAGE 4B - SKIPPED (time budget already exhausted after '{LAST_CONVERGED_STAGE_KEY}')\n{'='*70}")
else:
    print(f"\n{'='*70}\nSTAGE 4B - Production-Priority PPO (refines Stage 1's dials)\n{'='*70}")
    STAGE4B_STATE_BUILDER = make_production_priority_state_builder_v2e(_stage4b_matrices, _stage4b_counts)
    CONTROLLER_4B = PPOProductionPriorityControllerV2(state_dim=PRODUCTION_PRIORITY_STATE_DIM_V2E)

    # CHANGED: same curriculum-gate redesign -- Stage 4B must beat its own
    # reference (frozen Stage 4A) in held-out eval before being accepted.
    STAGE_CONFIG["4b"] = dict(n_episodes=200, patience=28, window=20, min_delta=125)
    _stage4b_reference_key = LAST_CONVERGED_STAGE_KEY   # should be "4a" here
    _stage4b_curr = run_stage_curriculum_4x(
        "4b", "STAGE 4B", _stage4b_reference_key, CONTROLLER_4B, STAGE4B_STATE_BUILDER,
        active_reinforce={"floorcap", "alpha", "animal", "rate", "reorder"},
        use_strategy_ppo=True, use_sell_ppo=True,
        rate_sub_flags={"animal": True, "plant": True, "animal_idle": True},
        stage_config=STAGE_CONFIG["4b"], eval_seeds=(601, 602, 603, 604, 605),
        win_margin=0.0, max_attempts=15)

    if not _stage4b_curr["beats_reference"]:
        print(f"\n[pipeline] STAGE 4B did NOT beat '{_stage4b_reference_key}' "
              f"(timed_out={_stage4b_curr['timed_out']}) -- discarding it, NOT freezing. "
              f"Falling back to '{LAST_CONVERGED_STAGE_KEY}'.")
        PIPELINE_STOPPED_EARLY = True
    else:
        # NOTE: 4B is the terminal stage -- frozen here so Part 14c can treat it
        # uniformly with every earlier stage via FROZEN_STAGE_AGENTS, instead of
        # a hardcoded CONTROLLER_4B/STAGE4B_STATE_BUILDER special-case.
        FROZEN_STAGE_AGENTS["4b"] = freeze_agent_snapshot(
            "4b", active_reinforce={"floorcap", "alpha", "animal", "rate", "reorder"},
            use_strategy_ppo=True, use_sell_ppo=True,
            rate_sub_flags={"animal": True, "plant": True, "animal_idle": True},
            production_priority_controller=CONTROLLER_4B,
            production_state_builder=STAGE4B_STATE_BUILDER)
        LAST_CONVERGED_STAGE_KEY = "4b"
        _le = _stage4b_curr["last_eval"]
        print(f"\nSTAGE 4B ACCEPTED | beat '{_stage4b_reference_key}' by "
              f"{_le['mean_delta']:+,.0f} (win_rate={_le['win_rate']:.0%}) after "
              f"{_stage4b_curr['n_episodes_run']} episodes")
        print("\nALL STAGES COMPLETE (B0 -> 1 -> 2A -> 2B -> 2C -> 3A -> 3B -> 3C -> 4A -> 4B), "
              "each one having beaten its own predecessor.")

    print(f"\n[pipeline] time_remaining={time_budget_remaining()/3600:.2f}h | "
          f"LAST_CONVERGED_STAGE_KEY='{LAST_CONVERGED_STAGE_KEY}' | stopped_early={PIPELINE_STOPPED_EARLY}")


# CHANGED: RL side of the tournament now always comes from
# FROZEN_STAGE_AGENTS[LAST_CONVERGED_STAGE_KEY] -- the last stage that
# converged before the budget ran out. Replaces the old hardcoded 4B assumption.
print(f"\n[Part 14c] Building final agent from LAST_CONVERGED_STAGE_KEY = "
      f"'{LAST_CONVERGED_STAGE_KEY}'" + (" (pipeline stopped early -- time budget)"
      if PIPELINE_STOPPED_EARLY else " (full pipeline completed)"))
# NOTE: the tournament (8 games) and Part 15's export are NOT time-gated --
# they're mandatory final steps, so total wall-clock CAN exceed the 11.5h
# budget by a few minutes. Budget separately for a hard platform time limit.
print(f"[Part 14c] time_remaining in training budget was "
      f"{time_budget_remaining()/3600:.2f}h when training stopped; the tournament below "
      f"(8 games) and export will still run to completion regardless.")
if LAST_CONVERGED_STAGE_KEY == "baseline":
    print("  [!] NOT EVEN STAGE 1 CONVERGED before the time budget ran out -- there is no "
          "trained RL agent to submit. Falling back to the rule-based baseline itself.")

SELL_CONTROLLER.training = False   

def build_final_agent(controller_4b=None, state_builder_4b=None, safe=True):
    mem = {"weed_age": {}, "own_planted_day": {}, "completed_project_steps": {}, "failure_count": {}}
    held4b = {"cfg": None, "next_select_turn": -1}

    def agent(obs, config=None):
        ws = build_world_state(obs)

        if STRATEGY_CONTROLLER.enabled:
            state = build_strategy_state(ws, None)
            base_cfg, _, _, _ = STRATEGY_CONTROLLER.select(state, greedy=True)
        else:
            base_cfg = default_strategy_controller(ws, None)

        if controller_4b is not None and ws.turn_in_episode >= held4b["next_select_turn"]:
            state4b = state_builder_4b(ws, None, mem)
            overrides, _, _, _ = controller_4b.select(state4b, greedy=True)
            # BUG FIX (most critical -- what the real submission uses): manually
            # re-listing fields dropped animal_allocation_ratio to None here.
            # dataclasses.replace() copies all fields, overriding only intended ones.
            held4b["cfg"] = dataclasses.replace(
                base_cfg,
                investment_budget_fraction=overrides.get("investment_budget_fraction",
                                                          base_cfg.investment_budget_fraction),
                risk_aversion=overrides.get("risk_aversion", base_cfg.risk_aversion))
            held4b["next_select_turn"] = ws.turn_in_episode + PRODUCTION_PRIORITY_PERSIST_TURNS
        cfg = held4b["cfg"] if (controller_4b is not None and held4b["cfg"] is not None) else base_cfg

        if controller_4b is not None:
            log_market_state(ws, mem)   

        sell_fn = lambda ws_, f, ob, ocp: compute_sell_fractions_ppo_4c_persistent(
            ws_, SELL_CONTROLLER, {}, persist_turns=SELL_DECISION_PERSIST_TURNS,
            forecast=f, opponent_belief=ob, opponent_crop_pressure=ocp, greedy=True)
        env_action, _, _ = run_turn_with_sell_fn(ws, mem, strategy=cfg, use_sell_fraction=True,
                                                  sell_fraction_fn=sell_fn)
        return env_action

    return agent

# FIX (Bug G): the 5 RL controllers are global singletons -- run_turn() can't
# disable them per-agent, so the old "baseline" silently still used trained
# RL layers. Fix: snapshot+force-off all flags only during that seat's turn.
def _snapshot_rl_flags():
    return {
        "floorcap_enabled": RL_FLOORCAP_CONTROLLER.enabled,
        "floorcap_stage2": RL_FLOORCAP_CONTROLLER.enabled_stage2,
        "alpha_enabled": RL_CROP_MIX_CONTROLLER.enabled,
        "animal_enabled": RL_ANIMAL_CONTROLLER.enabled,
        "animal_idle": RL_ANIMAL_CONTROLLER.enabled_idle,
        "rate_enabled": RL_RATE_CONTROLLER.enabled,
        "rate_animal": RL_RATE_CONTROLLER.enabled_animal,
        "rate_plant": RL_RATE_CONTROLLER.enabled_plant,
        "reorder_enabled": RL_REORDER_CONTROLLER.enabled,
    }

def _apply_rl_flags(flags):
    RL_FLOORCAP_CONTROLLER.enabled = flags["floorcap_enabled"]
    RL_FLOORCAP_CONTROLLER.enabled_stage2 = flags["floorcap_stage2"]
    RL_CROP_MIX_CONTROLLER.enabled = flags["alpha_enabled"]
    RL_ANIMAL_CONTROLLER.enabled = flags["animal_enabled"]
    RL_ANIMAL_CONTROLLER.enabled_idle = flags["animal_idle"]
    RL_RATE_CONTROLLER.enabled = flags["rate_enabled"]
    RL_RATE_CONTROLLER.enabled_animal = flags["rate_animal"]
    RL_RATE_CONTROLLER.enabled_plant = flags["rate_plant"]
    RL_REORDER_CONTROLLER.enabled = flags["reorder_enabled"]

_ALL_RL_OFF_FLAGS = {k: False for k in _snapshot_rl_flags()}

def true_baseline_builder():
    inner = make_agent(safe=True)
    def agent(obs, config=None):
        ambient = _snapshot_rl_flags()
        _apply_rl_flags(_ALL_RL_OFF_FLAGS)
        try:
            return inner(obs, config)
        finally:
            _apply_rl_flags(ambient)
    return agent

print(f"\n{'='*70}\nFINAL BENCHMARK - RL (full stack) vs TRUE no-RL baseline, 2-round seat-swap\n{'='*70}")
_tourney_seeds = [910001, 910002, 910003, 910004]

def _play_and_score(seed, seat0_builder, seat1_builder):
    _game_t0 = time.time()
    env = _kaggle_make("kaggriculture",
                        configuration={"episodeSteps": EPISODE_STEPS_DEFAULT, "seed": seed},
                        debug=False)
    result = env.run([seat0_builder(), seat1_builder()])
    w0 = _estimate_net_worth(build_world_state(result[-1][0]["observation"]))
    w1 = _estimate_net_worth(build_world_state(result[-1][1]["observation"]))
    print(f"    [game seed={seed}] time={time.time()-_game_t0:.1f}s")
    return w0, w1

# NOTE: FROZEN_STAGE_AGENTS[key] is already a complete, self-contained agent
# callable (flag-swapping baked in) -- build_final_agent() is only needed at
# the terminal "4b" stage, kept for backward-compat/clarity.
if LAST_CONVERGED_STAGE_KEY == "baseline":
    rl_builder = lambda: make_agent(safe=True)   # no trained RL agent exists at all
else:
    rl_builder = lambda: FROZEN_STAGE_AGENTS[LAST_CONVERGED_STAGE_KEY]
base_builder = true_baseline_builder   # FIX (Bug G): now genuinely all-RL-off, not just top-3-PPO-off

_deltas = []  

_tourney_t0 = time.time()
print("Round 1: RL seat0 / Baseline seat1")
for seed in _tourney_seeds:
    w_rl, w_base = _play_and_score(seed, rl_builder, base_builder)
    _deltas.append(w_rl - w_base)
    print(f"  seed={seed:>7d} | RL={w_rl:>10,.0f} | Baseline={w_base:>10,.0f} | delta={w_rl - w_base:>+10,.0f}")

print("Round 2: Baseline seat0 / RL seat1 (seats swapped, same seeds)")
for seed in _tourney_seeds:
    w_base, w_rl = _play_and_score(seed, base_builder, rl_builder)
    _deltas.append(w_rl - w_base)
    print(f"  seed={seed:>7d} | Baseline={w_base:>10,.0f} | RL={w_rl:>10,.0f} | delta={w_rl - w_base:>+10,.0f}")
print(f"Tournament total time ({len(_tourney_seeds)*2} games) = {time.time()-_tourney_t0:.1f}s")

_mean_delta = _stats.mean(_deltas)
_win_rate = sum(1 for d in _deltas if d > 0) / len(_deltas)
print(f"\nCombined {len(_deltas)} games | mean delta (RL - Baseline) = {_mean_delta:+,.0f} | "
      f"win rate = {_win_rate:.0%}")

_mean_says_rl = _mean_delta > 0
_rate_says_rl = _win_rate > 0.55
_rate_says_base = _win_rate < 0.45

if _mean_says_rl and _rate_says_rl:
    TOURNAMENT_WINNER = "RL"
elif (not _mean_says_rl) and _rate_says_base:
    TOURNAMENT_WINNER = "BASELINE"
else:
    TOURNAMENT_WINNER = "INCONCLUSIVE"

print(f"TOURNAMENT_WINNER = '{TOURNAMENT_WINNER}'")
if TOURNAMENT_WINNER == "INCONCLUSIVE":
    print("  [!] Mean delta and win rate did not agree, or win rate was too close to 50/50 "
          "-- treat as noise. Part 15's export will refuse to run until this is resolved "
          "(e.g. more seeds, or investigate why the two signals disagree).")



# FIX: _INFERENCE_SOURCE used to be a stale hardcoded blob (missing many fixes).
# Now assembled from `In` (real kernel execution history) + auto-detected
# cutoff, so it's always byte-identical to the code that actually ran.
import base64, pickle, inspect, textwrap

def _find_inference_cutoff(cell_sources):
    markers = ("run_stage(", "run_baseline(", "_stage4a_returns", "_stage4b_returns",
               "STAGE_CONFIG = {", "STAGE_CONFIG={")
    for i, src in enumerate(cell_sources):
        for line in src.splitlines():
            if line.startswith(markers):
                return i
    raise RuntimeError(
        "Could not find the training-execution cutoff cell while assembling "
        "_INFERENCE_SOURCE -- the marker lines this looks for may have moved "
        "or been renamed. Fix _find_inference_cutoff's `markers` tuple rather "
        "than falling back to a hardcoded blob."
    )

def _strip_magics(src):
    return "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("!", "%")))

_ih_all = list(In)  # IPython's actual per-cell input log for this session
_cutoff = _find_inference_cutoff(_ih_all)
_INFERENCE_SOURCE = "\n\n".join(_strip_magics(c) for c in _ih_all[:_cutoff])

# Self-check: fail hard if an important fix is missing from the assembled result.
_REQUIRED_MARKERS = [
    "def generate_drop_candidates",
    "RL_WIN_BONUS_REWARD",
]
_missing = [m for m in _REQUIRED_MARKERS if m not in _INFERENCE_SOURCE]
if _missing:
    raise RuntimeError(
        f"_INFERENCE_SOURCE is missing expected fix(es): {_missing}. "
        "Something upstream of the cutoff cell changed or the cutoff detection "
        "picked the wrong cell -- do NOT export submission.py until this is "
        "resolved (that's exactly how the old frozen-blob bug shipped silently)."
    )

# BUG FIX: build_final_agent() was defined AFTER the cutoff so it never made
# it into _INFERENCE_SOURCE, and the old _LOAD_AND_AGENT_CODE never called it --
# Kaggle's get_last_callable() picked STAGE4B_STATE_BUILDER instead (wrong signature).
_BUILD_FINAL_AGENT_SOURCE = inspect.getsource(build_final_agent)
if "def build_final_agent" not in _BUILD_FINAL_AGENT_SOURCE:
    raise RuntimeError("inspect.getsource(build_final_agent) did not return the expected function.")
# Structural check: make sure the CARE_BONUS/WATER fix pattern never regresses.
if 'if c.action_type == "CARE_BONUS":' in _INFERENCE_SOURCE:
    raise RuntimeError(
        "_INFERENCE_SOURCE contains an explicit CARE_BONUS branch in "
        "_mandatory_priority again -- the fixed version relies on falling "
        "through to the default priority instead. Verify this is intentional "
        "and doesn't reintroduce the WATER-starvation bug before exporting."
    )
compile(_INFERENCE_SOURCE, "<assembled_inference_source>", "exec")  # syntax sanity check
print(f"_INFERENCE_SOURCE assembled from {_cutoff} live cells, {len(_INFERENCE_SOURCE):,} chars, "
      f"all required fix markers present.")


if "TOURNAMENT_WINNER" not in globals():
    raise RuntimeError(
        "TOURNAMENT_WINNER is not defined -- run Part 14c's tournament cell first. "
        "submission.py must not be generated before a winner is actually decided."
    )
if TOURNAMENT_WINNER == "INCONCLUSIVE":
    raise RuntimeError(
        "TOURNAMENT_WINNER = 'INCONCLUSIVE' -- Part 14c's mean-delta and win-rate "
        "signals did not agree (or win rate was too close to 50/50). Resolve this "
        "(e.g. more seeds) before exporting anything."
    )

if TOURNAMENT_WINNER == "RL":
    print("TOURNAMENT_WINNER = 'RL' -- exporting the full trained pipeline.")
    print(f"  RL side built from LAST_CONVERGED_STAGE_KEY = '{LAST_CONVERGED_STAGE_KEY}'")

    # CHANGED (fallback-aware export): only 4A/4B have a production-priority
    # controller. If the pipeline stopped earlier, build_final_agent(None, None)
    # already handles that correctly (falls back to STRATEGY_CONTROLLER's cfg).
    _prod_ctrl = None
    _prod_kind = None
    if LAST_CONVERGED_STAGE_KEY == "4b":
        _prod_ctrl, _prod_kind = CONTROLLER_4B, "stage4b"
    elif LAST_CONVERGED_STAGE_KEY == "4a":
        _prod_ctrl, _prod_kind = CONTROLLER_4A, "stage4a"

    _TRAINED_BUNDLE = {
        "floorcap": RL_FLOORCAP_CONTROLLER,
        "alpha": RL_CROP_MIX_CONTROLLER,
        "animal": RL_ANIMAL_CONTROLLER,
        "rate": RL_RATE_CONTROLLER,
        "reorder": RL_REORDER_CONTROLLER,
        "strategy": STRATEGY_CONTROLLER,
        "sell": SELL_CONTROLLER,
        "prod_controller": _prod_ctrl,
        "prod_kind": _prod_kind,
        "validated_matrices": _stage4b_matrices,
        "validated_counts": _stage4b_counts,
    }
    _bundle_b64 = base64.b64encode(pickle.dumps(_TRAINED_BUNDLE)).decode("ascii")

    _LOAD_AND_AGENT_CODE = f'''
    # ---- trained weights, loaded at import time (no training happens here) ----
    import pickle, base64 as _b64
    _bundle = pickle.loads(_b64.b64decode("{_bundle_b64}"))
    RL_FLOORCAP_CONTROLLER = _bundle["floorcap"]
    RL_CROP_MIX_CONTROLLER = _bundle["alpha"]
    RL_ANIMAL_CONTROLLER = _bundle["animal"]
    RL_RATE_CONTROLLER = _bundle["rate"]
    RL_REORDER_CONTROLLER = _bundle["reorder"]
    STRATEGY_CONTROLLER = _bundle["strategy"]
    SELL_CONTROLLER = _bundle["sell"]
    REINFORCE_CONTROLLERS = {{"floorcap": RL_FLOORCAP_CONTROLLER, "alpha": RL_CROP_MIX_CONTROLLER,
                             "animal": RL_ANIMAL_CONTROLLER, "rate": RL_RATE_CONTROLLER,
                             "reorder": RL_REORDER_CONTROLLER}}
    for _c in REINFORCE_CONTROLLERS.values():
        _c.enabled = True
        _c.training = False
    STRATEGY_CONTROLLER.enabled = True
    STRATEGY_CONTROLLER.training = False
    SELL_CONTROLLER.enabled = True
    SELL_CONTROLLER.training = False
    set_markov_forecast_state(_bundle["validated_matrices"], _bundle["validated_counts"])
    _PROD_CONTROLLER = _bundle["prod_controller"]
    _prod_kind = _bundle["prod_kind"]
    if _prod_kind == "stage4b":
        _PROD_STATE_BUILDER = make_production_priority_state_builder_v2e(
            _bundle["validated_matrices"], _bundle["validated_counts"])
    elif _prod_kind == "stage4a":
        _PROD_STATE_BUILDER = build_production_priority_state
    else:
        _PROD_STATE_BUILDER = None
    '''
    # BUG FIX: set_markov_forecast_state() was never called again in the export
    # -- _MARKOV_FORECAST_STATE stayed empty, forecast silently fell back to
    # spot prices (no crash, but the trained market model was wasted).

    # Bind agent as the LAST statement so get_last_callable() doesn't mistakenly
    # pick a helper variable instead.
    _FINAL_AGENT_CODE = (
        _BUILD_FINAL_AGENT_SOURCE
        + "\nagent = build_final_agent(_PROD_CONTROLLER, _PROD_STATE_BUILDER)\n"
    )

    # BUG FIX (critical): _LOAD_AND_AGENT_CODE was 4-space indented, pasted raw
    # at module top-level -- Python merged it as dead code inside the previous
    # function (which returned earlier), so CONTROLLER_4B never got defined.
    _LOAD_AND_AGENT_CODE = textwrap.dedent(_LOAD_AND_AGENT_CODE)

    _FULL_SUBMISSION = _INFERENCE_SOURCE + "\n\n" + _LOAD_AND_AGENT_CODE + "\n\n" + _FINAL_AGENT_CODE

    # Structural check: a real exec + Kaggle's actual get_last_callable().
    from kaggle_environments.agent import get_last_callable as _get_last_callable
    _loaded_agent = _get_last_callable(_FULL_SUBMISSION)
    _loaded_agent_name = getattr(_loaded_agent, "__name__", repr(_loaded_agent))
    if _loaded_agent_name != "agent":
        raise RuntimeError(
            f"get_last_callable() resolved to '{_loaded_agent_name}', not the "
            "expected 'agent' closure from build_final_agent(). Something in "
            "_LOAD_AND_AGENT_CODE/_FINAL_AGENT_CODE binds a callable AFTER "
            "`agent = build_final_agent(...)` -- do NOT export until fixed, "
            "this is exactly the bug that made the RL branch non-functional."
        )

    # Exec into its own namespace to check global state (not just the callable).
    _sub_ns = {}
    exec(compile(_FULL_SUBMISSION, "<submission_check>", "exec"), _sub_ns)
    if not _sub_ns.get("_MARKOV_FORECAST_STATE", {}).get("transition_matrices"):
        raise RuntimeError(
            "_MARKOV_FORECAST_STATE['transition_matrices'] is empty after loading "
            "the assembled submission.py -- set_markov_forecast_state(...) isn't "
            "being called (or the bundled matrices are empty). The trained "
            "market-forecast model would silently be unused; do NOT export until "
            "fixed."
        )

    with open("/kaggle/working/submission.py", "w") as f:
        f.write(_FULL_SUBMISSION)

    print(f"submission.py written: {len(_FULL_SUBMISSION):,} chars")
    print(f"Verified: get_last_callable() resolves to '{_loaded_agent_name}' (correct).")
    print("Verified: _MARKOV_FORECAST_STATE populated with "
          f"{len(_sub_ns['_MARKOV_FORECAST_STATE']['transition_matrices'])} crop(s).")
    print("Test it locally before submitting: from kaggle_environments import make; "
          "env = make('kaggriculture'); env.run(['/kaggle/working/submission.py', 'starter'])")

else:  # TOURNAMENT_WINNER == "BASELINE"
    print("TOURNAMENT_WINNER = 'BASELINE' -- the trained pipeline did not beat "
          "the rule-based baseline. Exporting the baseline agent instead (no "
          "trained weights to embed -- much smaller file).")
    _FULL_SUBMISSION = _INFERENCE_SOURCE + "\n\nagent = make_safe_agent(make_agent(safe=True))\n"
    with open("/kaggle/working/submission.py", "w") as f:
        f.write(_FULL_SUBMISSION)
    print(f"submission.py written (BASELINE): {len(_FULL_SUBMISSION):,} chars")
    print("Test it locally before submitting: from kaggle_environments import make; "
          "env = make('kaggriculture'); env.run(['/kaggle/working/submission.py', 'starter'])")

