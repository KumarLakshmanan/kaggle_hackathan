
import matplotlib.pyplot as plt

# The actual real score history from our submissions
submissions = ['Baseline 535', 'Phase 3', 'Phase 4b_sub1', 'Phase 4b_sub2', 'Phase 6']
real_scores = [535, 600, 330.9, 348.0, 504.7]

plt.figure(figsize=(8, 4))
plt.plot(submissions, real_scores, marker='o', color='crimson', linewidth=2)
plt.title("Actual Kaggle Score History (The Struggle)")
plt.ylabel("Kaggle LB Score")
plt.grid(True, linestyle='--')
plt.show()



from IPython.display import Code

diff_snippet = """
-    urgent_tasks.append({"pos": (x, y), "action": ["FEED"], "var": task_var})
+    if available_wheat > 0:
+        available_wheat -= 1
+        urgent_tasks.append({"pos": (x, y), "action": ["FEED"], "var": task_var})
+    else:
+        print(f"[Skipped] FEED task skipped for {animal} at {x},{y} - Missing WHEAT. Generating PICKUP.")
+        if wheat_in_shed > 0:
+            pickup_tasks.append({"pos": tuple((4,4)), "action": ["PICKUP", "WHEAT", 1], "var": task_var})
+            wheat_in_shed -= 1
"""
Code(data=diff_snippet, language='diff')



import pandas as pd
from IPython.display import display

# Static reproduction of our real submission ledger to guarantee reproducibility
ledger_data = [
    {
        'date': '2026-08-20',
        'phase_name': 'Phase 9_Final_Integration',
        'local_win_rate_vs_standard_pool': '0.0',
        'hypothesis_if_mismatch': 'Newsvendor failed because adversarial opponent supply manifests as negative demand shutting down production. Real-Options failed by delaying compounding growth. Combined WR is 0%.'
    }
]
newsvendor_row = pd.DataFrame(ledger_data)
display(newsvendor_row)



# Static reproduction of the ladder drift evidence from our real submission ledger
drift_data = [
    {
        'date': '2026-08-24T17:32:07Z',
        'phase_name': 'Phase 4b Baseline',
        'file_hash_of_submitted_main_py': '6aa570386dc689a0254eca1bcb8ccae6e525e41ff0b953992f5351b71ea19d34',
        'one_line_description_of_change': 'Re-evaluation of 535 baseline against fixed opponent pool (FAILED CI)',
        'local_win_rate_vs_standard_pool': '0.0'
    }
]
drift_evidence = pd.DataFrame(drift_data)
display(drift_evidence)



shadow_price_snippet = """
    res = scipy.optimize.linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
    
    if res.success and hasattr(res, 'ineqlin') and hasattr(res.ineqlin, 'marginals'):
        marg_money = abs(res.ineqlin.marginals[0])
        marg_land = abs(res.ineqlin.marginals[1])
        marg_turn = abs(res.ineqlin.marginals[2])
    else:
        marg_money, marg_land, marg_turn = 1.0, 100.0, 5.0
        
    return marg_money, marg_land, marg_turn
"""
Code(data=shadow_price_snippet, language='python')



ledger_p6 = [
    {
        'phase_name': 'Phase 6_opp_cost',
        'one_line_description_of_change': 'Phase 6 Opportunity Cost Hungarian Scheduler',
        'local_win_rate_vs_standard_pool': '0.780',
        'hypothesis_if_mismatch': 'Local win rate of 78% did not translate to Kaggle LB over 600. Agent may be too sensitive to market crashes or missing a Kaggle-specific mechanic.'
    }
]
display(pd.DataFrame(ledger_p6))



cournot_snippet = """
    # 2. Cournot Best-Response Production Targeting
    Q_opp = forecast_opponent_supply(obs, player_id, day, horizon=3)
    best_q = get_best_response_quantities(obs, Q_opp, liquidation_mode=liquidation_mode)
"""
Code(data=cournot_snippet, language='python')



ledger_p12 = [
    {
        'phase_name': 'Phase 12_Deterministic_Cournot',
        'one_line_description_of_change': 'Removed stochastic bandit draw and hard-selected Cournot best-response mode',
        'local_win_rate_vs_standard_pool': '80/80 vs standard pool'
    }
]
display(pd.DataFrame(ledger_p12))



bandit_snippet = """
    for episode_id in episode_ids:
        try:
            mode = infer_mode_from_logs(episode_id, args.agent_index)
            replay_path = ensure_replay(episode_id, args.replay_dir)
            won, ours, theirs = infer_outcome(replay_path, args.agent_index)
            
            # Update the Bayesian posterior for this strategy arm based on live Kaggle result
            main.update_bandit_result(state["arms"], mode, won)
            
            print(f"{episode_id}: mode={mode} won={won} ours={ours:.1f} theirs={theirs:.1f}")
        except Exception as exc:
            print(f"{episode_id}: skipped ({exc})")
"""
Code(data=bandit_snippet, language='python')



ledger_p11 = [
    {
        'phase_name': 'Phase 11_Bandit_Response_Selector',
        'one_line_description_of_change': 'Thompson-sampling selector over Cournot/workload/throttled/aggressive response modes',
        'hypothesis_if_mismatch': 'Designed for leaderboard drift; update bandit_state.json from completed Kaggle episodes before resubmits'
    }
]
display(pd.DataFrame(ledger_p11))
