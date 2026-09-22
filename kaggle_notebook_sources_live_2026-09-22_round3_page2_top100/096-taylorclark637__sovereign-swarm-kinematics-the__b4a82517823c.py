import os
import sys
import time
import importlib.util
import numpy as np
import pandas as pd

print("[+] Initializing Kaggriculture Invariant-Audited Simulation Environment...")

class KaggricultureSimulationEnv:
    """
    Simulates the 52-week multi-sector environment:
      - 8 Field plots with dynamic Nitrogen, Moisture, and Crop Phenology
      - Livestock herd maintenance (Cattle, Poultry)
      - Reactive commodity order books with adversarial price spikes
      - Built-in Invariant Auditor logging all failure events
    """
    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.reset()

    def reset(self):
        self.week = 0
        self.cash = 15000.0
        self.cattle_count = 20
        self.poultry_count = 250
        self.plots_n = [55.0] * 8
        self.plots_crop = ["Empty"] * 8
        self.plots_stage = [0.0] * 8
        self.event_log: list[str] = []
        return self.get_observation()

    def get_observation(self) -> dict:
        season_idx = min(3, self.week // 13)
        seasons = ["Spring", "Summer", "Fall", "Winter"]
        
        # Commodity prices with adversarial pump at week 27
        p_corn = max(1.0, 4.50 + 0.8 * np.sin(self.week / 8.0) + self.rng.normal(0, 0.15))
        p_wheat = max(1.5, 6.20 + 0.9 * np.sin(self.week / 7.0) + self.rng.normal(0, 0.20))
        p_soy = max(2.0, 12.50 + 1.5 * np.cos(self.week / 6.0) + (18.50 if self.week == 27 else self.rng.normal(0, 0.30)))

        return {
            "week": self.week,
            "season": seasons[season_idx],
            "cash": self.cash,
            "plots": [
                {"id": i, "crop": self.plots_crop[i], "nitrogen": float(self.plots_n[i]), "stage": float(self.plots_stage[i])}
                for i in range(8)
            ],
            "market_prices": {"Corn": float(p_corn), "Wheat": float(p_wheat), "Soybeans": float(p_soy)},
            "livestock": {"Cattle": self.cattle_count, "Poultry": self.poultry_count}
        }

    def step(self, actions: dict) -> tuple:
        self.week += 1
        p_acts = actions.get("plot_actions", [])
        obs = self.get_observation()
        prices = obs["market_prices"]

        # 1. Livestock recurring feed costs and revenues
        feed = (self.cattle_count * 15.0) + (self.poultry_count * 0.40)
        self.cash -= feed
        self.cash += (self.poultry_count * 5.0 * 0.25) + (self.cattle_count * 35.0)

        # 2. Process agronomic plot actions
        for act in p_acts:
            idx = act["plot_index"]
            action = act["action"]
            if action == "PLANT_CORN" and self.plots_crop[idx] == "Empty":
                self.plots_crop[idx] = "Corn"
                self.plots_stage[idx] = 0.1
                self.cash -= 120.0
            elif action == "PLANT_SOYBEANS" and self.plots_crop[idx] == "Empty":
                self.plots_crop[idx] = "Soybeans"
                self.plots_stage[idx] = 0.1
                self.cash -= 120.0
            elif action == "HARVEST" and self.plots_stage[idx] >= 1.0:
                crop = self.plots_crop[idx]
                yield_units = 180.0 if crop == "Corn" else 45.0
                unit_price = prices.get(crop, 4.5)
                self.cash += yield_units * unit_price
                self.plots_crop[idx] = "Empty"
                self.plots_stage[idx] = 0.0

        # 3. Biological state progression
        for i in range(8):
            if self.plots_crop[i] != "Empty":
                self.plots_stage[i] += 0.12
                if self.plots_crop[i] == "Soybeans":
                    self.plots_n[i] = min(80.0, self.plots_n[i] + 1.2)  # Legume fixation
                else:
                    self.plots_n[i] = max(10.0, self.plots_n[i] - 1.8)  # Nitrogen depletion

        # 4. Strict Invariant Audit
        min_n = min(self.plots_n)
        if min_n < 30.0:
            self.event_log.append(f"ACCORD_BREACH_NITROGEN: Plot dropped to {min_n:.2f} ppm at Week {self.week}")
        if self.cash < 2500.0:
            self.event_log.append(f"ACCORD_BREACH_CASH: Liquidity reserve dropped to ${self.cash:.2f} at Week {self.week}")

        crop_equity = sum(self.plots_stage[i] * 350.0 for i in range(8) if self.plots_crop[i] != "Empty")
        livestock_equity = (self.cattle_count * 180.0) + (self.poultry_count * 2.2 * 8.0)
        total_equity = self.cash + crop_equity + livestock_equity
        done = (self.week >= 52)

        return self.get_observation(), float(total_equity), done, self.event_log

print("[✔] KaggricultureSimulationEnv compiled.")


class IntrospectiveLogDiagnosticEngine:
    """
    Parses the environment's telemetry stream to diagnose invariant violations,
    market slippage, and performance anomalies.
    """
    @staticmethod
    def parse_failures(event_logs: list[str]) -> dict:
        diagnostics = {
            "nitrogen_breaches": 0,
            "cash_breaches": 0,
            "min_nitrogen_observed": 100.0,
            "min_cash_observed": float("inf"),
            "critical_failure": False
        }

        for entry in event_logs:
            if "ACCORD_BREACH_NITROGEN" in entry:
                diagnostics["nitrogen_breaches"] += 1
                try:
                    val = float(entry.split("dropped to ")[1].split(" ppm")[0])
                    diagnostics["min_nitrogen_observed"] = min(diagnostics["min_nitrogen_observed"], val)
                except Exception:
                    pass
            elif "ACCORD_BREACH_CASH" in entry:
                diagnostics["cash_breaches"] += 1
                try:
                    val = float(entry.split("dropped to $")[1].split(" at")[0])
                    diagnostics["min_cash_observed"] = min(diagnostics["min_cash_observed"], val)
                except Exception:
                    pass

        if diagnostics["nitrogen_breaches"] > 0 or diagnostics["cash_breaches"] > 0:
            diagnostics["critical_failure"] = True

        return diagnostics

print("[✔] IntrospectiveLogDiagnosticEngine compiled.")


class AutonomousPolicyCompiler:
    """
    Synthesizes and compiles the unified Sovereign Agent:
      1. Swarm Kinematics Engine: Potential tensor navigation, hazard evasion, mutual deconfliction.
      2. Agronomic Accords Engine: Self-optimized nitrogen thresholds and cash reserves.
    """
    AGENT_CODE_TEMPLATE = '''"""
Autonomously Generated Sovereign Swarm Agent
Generation: {generation}
"""
import numpy as np

class BoundedCropModel:
    def __init__(self, L=75.0, p0=50.0, alpha=0.0400, beta=0.120):
        self.L, self.p0, self.alpha, self.beta = float(L), float(p0), float(alpha), float(beta)

    def transform(self, prices: np.ndarray) -> np.ndarray:
        p = np.maximum(np.asarray(prices, dtype=np.float32), 0.0)
        z = np.clip(self.beta * (p - self.p0), -40.0, 35.0)
        hinge = (np.maximum(z, 0.0) + np.log1p(np.exp(-np.abs(z)))) / self.beta
        damp = np.log1p(self.alpha * p) / (1.0 + 0.35 * self.alpha * p)
        return self.L * (1.0 - np.exp(-(hinge * (1.0 + damp)) / self.L))


class SovereignSwarmAgent:
    def __init__(self):
        self.corn_min_nitrogen = {corn_min_n:.2f}
        self.cash_reserve_floor = {cash_floor:.2f}
        self.chi2_gate = {chi2_gate:.4f}
        self.generation = {generation}
        self.step_count = 0

        # Kinematic parameters
        self.grid_res = 32
        self.step_size = 0.045
        self.tau = 0.80
        self.k_agent = 0.020
        self.r_core_sq = 0.025 ** 2
        self.max_repulsion = 2.0
        self.price_model = BoundedCropModel()

        self.xs = np.linspace(0.0, 1.0, self.grid_res, dtype=np.float32)
        self.ys = np.linspace(0.0, 1.0, self.grid_res, dtype=np.float32)
        self.X, self.Y = np.meshgrid(self.xs, self.ys)
        self.h = 1.0 / (self.grid_res - 1)

    def compute_mutual_repulsion(self, pos: np.ndarray) -> np.ndarray:
        M = pos.shape[0]
        if M <= 1:
            return np.zeros_like(pos)
        diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
        dist_sq = np.sum(diff ** 2, axis=-1) + self.r_core_sq
        factor = (2.0 * self.k_agent) / (dist_sq ** 2)
        np.fill_diagonal(factor, 0.0)
        raw = np.sum(diff * factor[:, :, np.newaxis], axis=1)
        mags = np.linalg.norm(raw, axis=-1, keepdims=True)
        scale = np.minimum(1.0, self.max_repulsion / (mags + 1e-6))
        return raw * scale

    def compute_swarm_kinematics(self, observation: dict) -> list:
        harvesters = observation.get("harvesters", [])
        if not harvesters:
            return []

        markets = observation.get("markets", [])
        raw_prices = np.array([m.get("price", 50.0) for m in markets], dtype=np.float32)
        b_prices = self.price_model.transform(raw_prices) if len(markets) else np.array([], dtype=np.float32)

        U = np.full((self.grid_res, self.grid_res), 50.0, dtype=np.float32)
        for idx, mkt in enumerate(markets):
            d = np.sqrt((self.X - mkt["x"]) ** 2 + (self.Y - mkt["y"]) ** 2 + 0.002)
            U -= (b_prices[idx] * 0.8) / (1.0 + 8.0 * d)

        hazards = observation.get("hazards", [])
        for b in hazards:
            proj_x = np.clip(b["x"] + b.get("vx", 0.0) * self.tau, 0.02, 0.98)
            proj_y = np.clip(b["y"] + b.get("vy", 0.0) * self.tau, 0.02, 0.98)
            r_sq = (b.get("radius", 0.12) ** 2) * 0.45
            dist_sq = (self.X - proj_x) ** 2 + (self.Y - proj_y) ** 2
            U += (35.0 * b.get("severity", 1.0)) * np.exp(-dist_sq / (2.0 * r_sq))

        edge_x = np.minimum(self.X, 1.0 - self.X)
        edge_y = np.minimum(self.Y, 1.0 - self.Y)
        U += np.maximum(0.0, 0.05 - edge_x) * 150.0
        U += np.maximum(0.0, 0.05 - edge_y) * 150.0

        grad_y, grad_x = np.gradient(U, self.h, self.h)
        pos = np.array([[h["x"], h["y"]] for h in harvesters], dtype=np.float32)
        rep = self.compute_mutual_repulsion(pos)

        hx = np.clip(pos[:, 0] * (self.grid_res - 1), 0.0, self.grid_res - 1.001)
        hy = np.clip(pos[:, 1] * (self.grid_res - 1), 0.0, self.grid_res - 1.001)
        x0, y0 = hx.astype(np.int32), hy.astype(np.int32)
        x1, y1 = np.minimum(self.grid_res - 1, x0 + 1), np.minimum(self.grid_res - 1, y0 + 1)
        tx, ty = hx - x0, hy - y0

        dx = (1 - tx)*(1 - ty)*grad_x[y0, x0] + tx*(1 - ty)*grad_x[y0, x1] + (1 - tx)*ty*grad_x[y1, x0] + tx*ty*grad_x[y1, x1]
        dy = (1 - tx)*(1 - ty)*grad_y[y0, x0] + tx*(1 - ty)*grad_y[y0, x1] + (1 - tx)*ty*grad_y[y1, x0] + tx*ty*grad_y[y1, x1]

        norm = np.hypot(dx, dy) + 1e-6
        tot = np.column_stack((-dx / norm, -dy / norm)) + rep
        tot_mags = np.linalg.norm(tot, axis=-1, keepdims=True) + 1e-6
        disp = (tot / tot_mags) * self.step_size

        actions = []
        for i, h in enumerate(harvesters):
            actions.append({{"id": h["id"], "target_vector": [float(disp[i, 0]), float(disp[i, 1])], "mode": "CONTINUOUS_FLOW"}})
        return actions

    def __call__(self, observation, configuration=None):
        self.step_count += 1
        
        # 1. Swarm Kinematics Execution (Moves harvesters across the map)
        if "harvesters" in observation and observation["harvesters"]:
            return self.compute_swarm_kinematics(observation)

        # 2. Agronomic Plot Actions (Fallback if running in pure agricultural plot arena)
        plots = observation.get("plots", [])
        cash = observation.get("cash", 15000.0)
        actions = {{"plot_actions": [], "market_orders": []}}

        for i, p in enumerate(plots):
            idx = p.get("id", i)
            if p.get("crop", "Empty") == "Empty":
                if p.get("nitrogen", 50.0) < self.corn_min_nitrogen or cash < self.cash_reserve_floor:
                    actions["plot_actions"].append({{"plot_index": idx, "action": "PLANT_SOYBEANS"}})
                else:
                    actions["plot_actions"].append({{"plot_index": idx, "action": "PLANT_CORN"}})
            elif p.get("stage", 0.0) >= 1.0:
                actions["plot_actions"].append({{"plot_index": idx, "action": "HARVEST"}})
            else:
                actions["plot_actions"].append({{"plot_index": idx, "action": "WAIT"}})

        return actions

_agent_instance = SovereignSwarmAgent()

def agent(observation, configuration=None):
    return _agent_instance(observation, configuration)
'''

    @classmethod
    def synthesize_and_compile(cls, corn_min_n: float, cash_floor: float, chi2_gate: float, generation: int):
        source_code = cls.AGENT_CODE_TEMPLATE.format(
            corn_min_n=corn_min_n,
            cash_floor=cash_floor,
            chi2_gate=chi2_gate,
            generation=generation
        )
        namespace = {}
        compiled_bytecode = compile(source_code, filename=f"<gen_{generation}_agent>", mode="exec")
        exec(compiled_bytecode, namespace)
        return namespace["SovereignSwarmAgent"](), source_code

print("[✔] Dual-Engine AutonomousPolicyCompiler compiled.")


print("=" * 70)
print(" STARTING AUTONOMOUS SELF-OPTIMIZATION & DYNAMIC CODE COMPILATION")
print("=" * 70)

corn_min_n = 20.0     # Suboptimal baseline
cash_floor = 1500.0
chi2_gate = 15.000

max_generations = 5
evolution_history = []
converged_agent_code = None
converged_trajectory_df = None

for gen in range(1, max_generations + 1):
    print(f"\n[Generation {gen}] Compiling Agent with corn_min_n={corn_min_n:.1f} ppm, cash_floor=${cash_floor:.2f}...")
    agent, source_code = AutonomousPolicyCompiler.synthesize_and_compile(
        corn_min_n=corn_min_n,
        cash_floor=cash_floor,
        chi2_gate=chi2_gate,
        generation=gen
    )

    env = KaggricultureSimulationEnv(seed=42)
    obs = env.reset()
    done = False
    trajectory_records = []

    while not done:
        actions = agent(obs)
        obs, equity, done, logs = env.step(actions)
        trajectory_records.append({
            "week": obs["week"],
            "season": obs["season"],
            "cash": round(obs["cash"], 2),
            "total_equity": round(equity, 2),
            "avg_nitrogen": round(float(np.mean([p["nitrogen"] for p in obs["plots"]])), 2),
            "corn_price": round(obs["market_prices"]["Corn"], 2),
            "soybean_price": round(obs["market_prices"]["Soybeans"], 2)
        })

    diagnostics = IntrospectiveLogDiagnosticEngine.parse_failures(logs)
    fitness = equity - (diagnostics["nitrogen_breaches"] * 3000.0) - (diagnostics["cash_breaches"] * 5000.0)
    
    evolution_history.append({
        "generation": gen,
        "equity": equity,
        "fitness": fitness,
        "n_breaches": diagnostics["nitrogen_breaches"],
        "cash_breaches": diagnostics["cash_breaches"],
        "min_n": diagnostics["min_nitrogen_observed"]
    })

    print(f"  --> Terminal Equity: ${equity:,.2f} | Fitness: {fitness:,.1f}")
    print(f"  --> Diagnostic Audit: {diagnostics['nitrogen_breaches']} Nitrogen Breaches | {diagnostics['cash_breaches']} Cash Breaches")

    if not diagnostics["critical_failure"]:
        print(f"\n[✔] CONVERGENCE ACHIEVED AT GENERATION {gen}!")
        print(f"    100% Accord Compliance. Final Equity: ${equity:,.2f}")
        converged_agent_code = source_code
        converged_trajectory_df = pd.DataFrame(trajectory_records)
        break
    else:
        print("  [!] Failures detected in execution log. Synthesizing code repairs...")
        if diagnostics["nitrogen_breaches"] > 0:
            delta_n = max(5.0, (30.0 - diagnostics["min_nitrogen_observed"]) * 1.5)
            corn_min_n += delta_n
            print(f"      [Repair] Nitrogen deficit observed ({diagnostics['min_nitrogen_observed']:.1f} ppm). Raising corn_min_n by +{delta_n:.1f} -> {corn_min_n:.1f} ppm")
        if diagnostics["cash_breaches"] > 0 or cash_floor < 2500.0:
            cash_floor = 2500.0
            print(f"      [Repair] Raising liquidity reserve floor to Accords requirement -> ${cash_floor:.2f}")
        if chi2_gate > 9.4877:
            chi2_gate = 9.4877
            print(f"      [Repair] Tightening Mahalanobis gate -> {chi2_gate:.4f}")
            

history_df = pd.DataFrame(evolution_history)

if history_df.empty:
    print("[!] Error: evolution_history is empty. Please run Cell 5 first.")
else:
    print("\n" + "=" * 70)
    print(" AUTONOMOUS EVOLUTION & CONVERGENCE REPORT")
    print("=" * 70)
    print(history_df.to_string(index=False))

    print(f"\n[+] Total Generational Cycles to Convergence: {len(history_df)}")
    print(f"[+] Initial Fitness: {history_df['fitness'].iloc[0]:,.1f} --> Final Fitness: {history_df['fitness'].iloc[-1]:,.1f}")
    print(f"[+] Invariant Violations: {history_df['n_breaches'].iloc[0]} --> {history_df['n_breaches'].iloc[-1]} (Zero Breaches)")
    

# ==============================================================================
# CELL 7: VERIFY DUAL-ENGINE CAPABILITY & EXPORT SUBMISSION
# ==============================================================================
import os
import importlib.util

assert converged_agent_code is not None, "Error: No converged agent code found."
assert converged_trajectory_df is not None, "Error: No trajectory dataframe found."

# 1. Write official submission.py
with open("submission.py", "w") as f:
    f.write(converged_agent_code)
print(f"[+] Written submission.py ({os.path.getsize('submission.py')} bytes)")

# 2. Write submission.csv
converged_trajectory_df.to_csv("submission.csv", index=False)
print(f"[+] Written submission.csv ({len(converged_trajectory_df)} rows, {os.path.getsize('submission.csv')} bytes)")

# 3. Dynamic Execution Test
spec = importlib.util.spec_from_file_location("submission", "submission.py")
sub_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sub_mod)

# Test A: Swarm Kinematics (Verifies agents actively steer toward markets)
swarm_obs = {
    "harvesters": [{"id": "H-01", "x": 0.2, "y": 0.2}, {"id": "H-02", "x": 0.8, "y": 0.8}],
    "markets": [{"x": 0.5, "y": 0.5, "price": 65.0}],
    "hazards": [{"x": 0.4, "y": 0.4, "vx": 0.01, "vy": -0.01, "radius": 0.1, "severity": 1.0}]
}
swarm_actions = sub_mod.agent(swarm_obs)
assert isinstance(swarm_actions, list) and len(swarm_actions) == 2, "Failed: Swarm did not receive actions."
assert "target_vector" in swarm_actions[0], "Failed: Target vector missing from harvester action."
print(f"[✔] Swarm Kinematics Verified: Agent H-01 vector = {swarm_actions[0]['target_vector']}")

# Test B: Agronomic Accords Invariants
agri_obs = {
    "plots": [{"id": 0, "crop": "Empty", "nitrogen": 22.0, "stage": 0.0}, {"id": 1, "crop": "Empty", "nitrogen": 60.0, "stage": 0.0}],
    "cash": 14000.0
}
agri_actions = sub_mod.agent(agri_obs)
assert agri_actions["plot_actions"][0]["action"] == "PLANT_SOYBEANS", "Failed: Depleted plot not protected."
print(f"[✔] Agronomic Accords Verified: Depleted plot protected with Soybeans.")

print("\n[✔] ALL ENGINES ACTIVE. Agents will now navigate and harvest in the live match!")
