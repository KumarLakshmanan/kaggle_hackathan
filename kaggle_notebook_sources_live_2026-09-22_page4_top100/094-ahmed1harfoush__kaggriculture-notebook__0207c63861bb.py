import warnings
warnings.filterwarnings('ignore')
import time, json, os, sys
from collections import defaultdict

try:
    from kaggle_environments import make
    print('kaggle-environments ready')
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'kaggle-environments'])
    from kaggle_environments import make
    print('kaggle-environments installed')

# Verify environment
env = make('kaggriculture', configuration={'episodeSteps': 10}, debug=True)
env.run(['random', 'random'])
print('Environment OK!')

def run_episode(agent1, agent2, seed=None, debug=True, steps=720):
    config = {'episodeSteps': steps}
    if seed is not None:
        config['seed'] = seed
    env = make('kaggriculture', configuration=config, debug=debug)
    env.run([agent1, agent2])
    final = env.steps[-1]
    return {
        'p0_reward': float(final[0].reward),
        'p1_reward': float(final[1].reward),
        'p0_status': str(final[0].status),
        'winner': 0 if float(final[0].reward) > float(final[1].reward) else (1 if float(final[1].reward) > float(final[0].reward) else -1),
    }

def evaluate_agent(agent, opponents, num_games=5):
    results = {}
    for opp_name, opp_agent in opponents.items():
        wins, losses, ties = 0, 0, 0
        moneys, opp_moneys = [], []
        for seed in range(1, num_games + 1):
            r = run_episode(agent, opp_agent, seed=seed)
            moneys.append(r['p0_reward'])
            opp_moneys.append(r['p1_reward'])
            if r['winner'] == 0: wins += 1
            elif r['winner'] == 1: losses += 1
            else: ties += 1
        results[opp_name] = {
            'wins': wins, 'losses': losses, 'ties': ties,
            'win_rate': wins / num_games,
            'avg_money': sum(moneys) / len(moneys),
            'avg_opp': sum(opp_moneys) / len(opp_moneys),
            'min_money': min(moneys), 'max_money': max(moneys),
        }
    return results

def print_results(results):
    print(f'{"Opponent":>10s} {"W":>3s} {"L":>3s} {"T":>3s} {"Win%":>6s} {"Avg$":>8s} {"vs Opp":>8s} {"Min$":>8s} {"Max$":>8s}')
    print('-' * 70)
    for opp, r in results.items():
        print(f'{opp:>10s} {r["wins"]:3d} {r["losses"]:3d} {r["ties"]:3d} {r["win_rate"]:5.0%} {r["avg_money"]:8.0f} {r["avg_opp"]:8.0f} {r["min_money"]:8.0f} {r["max_money"]:8.0f}')

print('Framework ready.')

import importlib.util
spec = importlib.util.spec_from_file_location('main', 'main.py')
agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_module)
our_agent = agent_module.agent
print('Agent v2.3 loaded:', our_agent.__name__)

opponents = {'random': 'random', 'pass': 'pass', 'starter': 'starter'}
print('Running benchmarks (5 seeds each)...')
t0 = time.time()
results = evaluate_agent(our_agent, opponents)
t1 = time.time()
print(f'Completed in {t1-t0:.1f}s\n')
print_results(results)

print('Self-play tests:')
for seed in [1, 2, 42]:
    r = run_episode(our_agent, our_agent, seed=seed)
    p0, p1 = int(r['p0_reward']), int(r['p1_reward'])
    print(f'  Seed {seed}: P0=${p0} P1=${p1} Winner=P{r["winner"]}')

from main import calc_price, MARKET_PARAMS, MARKET_I0

test_cases = {
    'WHEAT': (25, 45, 20, 19),
    'CARROT': (35, 70, 10, 1),
    'TOMATO': (60, 84, 24, 9),
    'STRAWBERRY': (120, 204, 1, 1),
    'MELON': (250, 300, 1, 1),
    'EGG': (50, 70, 40, 39),
    'MILK': (160, 256, 1, 1),
    'WOOL': (200, 240, 1, 1),
    'FERTILIZER': (100, 140, 60, 20),
}

all_pass = True
for item, (base, p_low, p_high, p_high2) in test_cases.items():
    T = MARKET_PARAMS[item]['T']
    al = calc_price(item, MARKET_I0 - T)
    ah = calc_price(item, MARKET_I0 + T)
    ah2 = calc_price(item, MARKET_I0 + 2*T)
    ok = al == p_low and ah == p_high and ah2 == p_high2
    if not ok: all_pass = False
    print(f'{item:>12s}: P(low)=${al:3d} P(high)=${ah:3d} P(2x)=${ah2:3d}  [{"PASS" if ok else "FAIL"}]')

print(f'\nAll checks: {"PASS" if all_pass else "FAIL"}')

with open('strategy_parameters.json') as f:
    params = json.load(f)
print(json.dumps(params, indent=2))

import tarfile

assert os.path.exists('main.py'), 'main.py not found!'
print(f'main.py: {os.path.getsize("main.py")} bytes')

with tarfile.open('agent_bundle.tar.gz', 'w:gz') as tar:
    tar.add('main.py')
print(f'agent_bundle.tar.gz: {os.path.getsize("agent_bundle.tar.gz")} bytes')

# Final validation
r = run_episode(our_agent, 'random', seed=99)
print(f'\nValidation: Agent=${int(r["p0_reward"])} vs Random=${int(r["p1_reward"])} [{r["p0_status"]}]')

print('\n' + '='*50)
print('KAGGRICULTURE AGENT v2.3 READY FOR SUBMISSION')
print('='*50)
print('\nSubmit with:')
print('  kaggle competitions submit kaggriculture -f main.py -m "v2.3"')