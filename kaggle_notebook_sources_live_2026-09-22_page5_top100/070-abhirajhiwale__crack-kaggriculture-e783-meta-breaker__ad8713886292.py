from pathlib import Path
import json
print("E783 findings notebook")
print("Production policy: replay-safe, standard-library-only")

summary = {"episodes": 177, "wins": 88, "losses": 89, "ties": 0}
summary["decided_win_rate"] = summary["wins"] / (summary["wins"] + summary["losses"])
summary

# Local validation commands
# python sandbox/contract_test.py submission_e783.tar.gz --episodes 2
# python sandbox/run_match.py candidate.py baseline.py --seed-start 1900001 --n 50 --csv results.csv
print("Do not submit until contract, runtime, both-seat, and unseen-seed gates pass.")