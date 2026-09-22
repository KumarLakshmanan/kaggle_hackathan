import os
import gc
import json
import time
import resource

import pandas as pd
import pyarrow.parquet as pq
import pyarrow.dataset as ds
import matplotlib.pyplot as plt


def find_kaggle_input_file(filename):
    for root, _dirs, files in os.walk("/kaggle/input"):
        if filename in files:
            return os.path.join(root, filename)
    raise FileNotFoundError(f"Could not find '{filename}' under /kaggle/input.")


REPLAYS_PATH = find_kaggle_input_file("replays.parquet")
EPISODES_PATH = find_kaggle_input_file("episodes.csv")
AGENTS_PATH = find_kaggle_input_file("agents.csv")
TEAMS_PATH = find_kaggle_input_file("teams.csv")

def pick_top_ladder_game(episodes_csv_path, teams_csv_path, replays_path, top_n=5):
    """Pick the highest-banking ladder (non-self-play) game that actually has a stored replay.

    Only ever reads the tiny `episode_id` column of the parquet to probe for existence — never
    the multi-GB `replay_json` column. Self-contained: pandas + pyarrow.dataset only.
    """
    episodes = pd.read_csv(episodes_csv_path)
    ladder = episodes[episodes["type"] == "EPISODE_TYPE_PUBLIC"].copy()  # drop self-play checks
    ladder["max_bank"] = ladder[["bank_0", "bank_1"]].max(axis=1)
    candidates = ladder.sort_values("max_bank", ascending=False).head(top_n)

    teams_lookup = pd.read_csv(teams_csv_path).set_index("team_id")["team_name"].to_dict()

    def team_label(team_id):
        team_id = int(team_id)
        return teams_lookup.get(team_id, f"Team {team_id}")  # ~half of team_ids aren't named

    dataset = ds.dataset(replays_path)
    for _, row in candidates.iterrows():
        eid = int(row["episode_id"])
        probe = dataset.scanner(
            columns=["episode_id"], filter=ds.field("episode_id") == eid, batch_size=1
        ).head(1)
        if probe.num_rows > 0:
            return {
                "episode_id": eid,
                "bank_0": int(row["bank_0"]), "bank_1": int(row["bank_1"]),
                "team_0": int(row["team_0"]), "team_1": int(row["team_1"]),
                "team_0_name": team_label(row["team_0"]),
                "team_1_name": team_label(row["team_1"]),
            }
    raise RuntimeError(f"None of the top {top_n} ladder games by bank had a stored replay.")

def load_replay(episode_id, replays_path):
    """Pull exactly one replay out of the multi-GB parquet by filtering on `episode_id`.

    Returns (replay_dict, elapsed_seconds, peak_rss_mb). No dependencies beyond pyarrow/pandas.
    """
    t0 = time.time()
    scanner = ds.dataset(replays_path).scanner(
        filter=ds.field("episode_id") == int(episode_id), batch_size=1
    )
    batch = scanner.head(1)
    if batch.num_rows == 0:
        raise ValueError(f"episode_id {episode_id} not found in {replays_path}")
    raw = batch.column("replay_json")[0].as_py()
    if isinstance(raw, bytes):  # the CDN has served both str and bytes historically
        raw = raw.decode("utf-8")
    replay = json.loads(raw)
    elapsed = time.time() - t0
    peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KB -> MB on Linux
    return replay, elapsed, peak_rss_mb

def replay_frames(replay):
    """Turn one parsed replay into three tidy DataFrames: actions, banks, market.

    Does not assume which seat carries the shared observation (day/hour/market/farms) — it
    checks both seats at runtime and reads from whichever one actually has it. Does not assume
    the replay ran the full 720 steps: it iterates whatever `steps` the replay contains.
    """
    steps = replay["steps"]
    shared_keys = ["day", "hour", "market", "farms"]
    probe = steps[0]
    if all(k in probe[0]["observation"] for k in shared_keys):
        shared_seat = 0
    elif all(k in probe[1]["observation"] for k in shared_keys):
        shared_seat = 1
    else:
        raise ValueError("Neither seat's observation carries the expected shared fields.")

    action_rows, bank_rows, market_rows = [], [], []
    for t, step in enumerate(steps):
        shared_obs = step[shared_seat]["observation"]
        day, hour = shared_obs["day"], shared_obs["hour"]

        for seat_idx in range(len(step)):
            act = step[seat_idx]["action"]
            action_rows.append({
                "step": t, "day": day, "hour": hour, "seat": seat_idx,
                "farmer_action": act.get("farmer"),
                "hand_actions": act.get("hands"),
                "market_orders": act.get("market"),
            })

        for seat_idx, farm in enumerate(shared_obs["farms"]):
            bank_rows.append({"step": t, "day": day, "hour": hour, "seat": seat_idx, "money": farm["money"]})

        market = shared_obs["market"]
        for product, price in market["prices"].items():
            market_rows.append({
                "step": t, "day": day, "hour": hour, "product": product,
                "price": price, "inventory": market["inventory"].get(product),
            })

    actions = pd.DataFrame(action_rows)
    banks = pd.DataFrame(bank_rows)
    market_df = pd.DataFrame(market_rows)
    return actions, banks, market_df

game = pick_top_ladder_game(EPISODES_PATH, TEAMS_PATH, REPLAYS_PATH)
print(f"Chosen episode: {game['episode_id']}")
print(f"  seat 0: {game['team_0_name']} (team {game['team_0']}) -> bank {game['bank_0']}")
print(f"  seat 1: {game['team_1_name']} (team {game['team_1']}) -> bank {game['bank_1']}")

replay, load_seconds, peak_rss_mb = load_replay(game["episode_id"], REPLAYS_PATH)
print(f"load_replay(): {load_seconds:.1f}s, peak RSS so far: {peak_rss_mb:.0f} MB, "
      f"{len(replay['steps'])} steps parsed")

# Free, independent correctness check: does the replay's own final money match the ground truth
# in episodes.csv and agents.csv? Run live, not assumed.
last_obs = replay["steps"][-1][0]["observation"]
final_money = {i: int(round(f["money"])) for i, f in enumerate(last_obs["farms"])}

agents = pd.read_csv(AGENTS_PATH)
final_bank = (
    agents[agents["episode_id"] == game["episode_id"]].set_index("agent_index")["final_bank"]
)

assert final_money[0] == game["bank_0"] == int(final_bank.loc[0])
assert final_money[1] == game["bank_1"] == int(final_bank.loc[1])
print(f"PASS: replay final money {final_money[0]}/{final_money[1]} == episodes.csv bank_0/bank_1 "
      f"== agents.csv final_bank, for episode {game['episode_id']}")

actions, banks, market = replay_frames(replay)
del replay
gc.collect()  # the parsed JSON was several hundred MB; keep only the tidy tables from here on
actions.head()

file_size_gb = os.path.getsize(REPLAYS_PATH) / 1e9
pf = pq.ParquetFile(REPLAYS_PATH)
n_row_groups = pf.metadata.num_row_groups
n_rows = pf.metadata.num_rows
json_col_idx = pf.schema_arrow.names.index("replay_json")

total_compressed = sum(
    pf.metadata.row_group(i).column(json_col_idx).total_compressed_size for i in range(n_row_groups)
)
total_uncompressed = sum(
    pf.metadata.row_group(i).column(json_col_idx).total_uncompressed_size for i in range(n_row_groups)
)

print(f"replays.parquet on disk: {file_size_gb:.2f} GB")
print(f"row groups: {n_row_groups:,}  |  rows: {n_rows:,}  |  rows/group: {n_rows / n_row_groups:.1f}")
print(f"replay_json column — compressed: {total_compressed / 1e9:.2f} GB, "
      f"uncompressed: {total_uncompressed / 1e9:.2f} GB "
      f"({total_uncompressed / total_compressed:.0f}x compression)")
print(f"mean replay size: {total_uncompressed / n_rows / 1e6:.1f} MB of raw JSON")
print(f"A plain pd.read_parquet() on this column tries to hold ~{total_uncompressed / 1e9:.1f} GB "
      "of decompressed JSON text in RAM before a single json.loads() runs. Row groups are small "
      f"(~{n_rows / n_row_groups:.0f} rows each), which is exactly what makes a single targeted "
      "read cheap instead.")

episodes_all = pd.read_csv(EPISODES_PATH)
n_public = (episodes_all["type"] == "EPISODE_TYPE_PUBLIC").sum()
n_validation = (episodes_all["type"] == "EPISODE_TYPE_VALIDATION").sum()

teams_lookup = pd.read_csv(TEAMS_PATH).set_index("team_id")["team_name"].to_dict()
seen_team_ids = pd.unique(episodes_all[["team_0", "team_1"]].values.ravel())
named_share = sum(int(t) in teams_lookup for t in seen_team_ids) / len(seen_team_ids)

print(f"episodes.csv: {n_public:,} ladder games, {n_validation:,} self-play checks filtered out")
print(f"teams.csv names {named_share:.0%} of the {len(seen_team_ids):,} distinct teams that "
      "appear in episodes.csv — the fallback (Team <id>) is what covers the rest")
print(f"Selected: episode {game['episode_id']}, "
      f"seat 0 = {game['team_0_name']!r}, seat 1 = {game['team_1_name']!r}")

print(f"load_replay(): {load_seconds:.1f}s wall time, {peak_rss_mb:.0f} MB peak RSS")
print(f"final money: seat 0 = {final_money[0]}, seat 1 = {final_money[1]} "
      f"(matches episodes.csv and agents.csv — PASS, asserted above)")

banks.head()

market.head()

fig, ax = plt.subplots(figsize=(9, 4.5))
for seat, label in [(0, f"seat 0 — {game['team_0_name']}"), (1, f"seat 1 — {game['team_1_name']}")]:
    seat_df = banks[banks["seat"] == seat]
    x = seat_df["day"] + seat_df["hour"] / 24
    ax.plot(x, seat_df["money"], label=label)
ax.set_xlabel("In-game day")
ax.set_ylabel("Money (bank)")
ax.set_title(f"Bank curve — episode {game['episode_id']}")
ax.legend()
plt.tight_layout()
plt.show()

print(f"This run: {load_seconds:.1f}s to load one replay, {peak_rss_mb:.0f} MB peak RSS, "
      f"{len(actions):,} action rows / {len(banks):,} bank rows / {len(market):,} market rows "
      f"from episode {game['episode_id']} ({actions['step'].max() + 1} steps).")