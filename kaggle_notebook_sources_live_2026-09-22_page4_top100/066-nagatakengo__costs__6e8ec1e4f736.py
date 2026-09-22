#!unzip -qo /content/output_re.zip -d /data


import sys
sys.path.append("/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx")



import pandas as pd
from kaggriculture_df import Kaggriculture_df
from my_plot import sns_line, sns_line_smooth, sns_2_line_smooth, sns_Hist
import ast
from numpy import astype
from kaggle_kaggriculture import convert, xy_plt_2d, xy_plt_2d_all, create_all_hands_feature, new_xy_plt_2d
import matplotlib.pyplot as plt
import seaborn as sns


df_st = (Kaggriculture_df("/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx/results/st_data/strong_rank1_score157577.0_p1.json", 1)).df
df_be = (Kaggriculture_df("/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx/results/be_data_5/beginner_rank1_score83174.0_p1.json",1)).df

"""
df_st = (Kaggriculture_df("/data/st_data/strong_rank1_score157577.0_p1.json", 1)).df
df_be = (Kaggriculture_df("/data/be_data/beginner_rank1_score99661.0_p1.json",1)).df
"""

df_st.columns

def Changespersonnel(df):
    df = df[["step","day","hands_n","money","hires_today"]].copy()
    return df


df_st_day = Changespersonnel(df_st)
df_be_day = Changespersonnel(df_be)

df_st_day

print("上位1%:労働者の人数")
sns_line_smooth(df_st_day, x='day', y="hands_n", figsize=(15, 5), step=1)

def cost(df):
    df = df[["step","day","money", "market_action","market_prices"]].copy()

    prices_df = df["market_prices"].apply(pd.Series)
    prices_df = prices_df.rename(columns=lambda x: f"market_prices_{x}")
    df = pd.concat([df, prices_df], axis=1)

    seed_prices = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
    animal_prices = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
    land_prices = [1000, 2000, 4000]


    def get_fib(n):
        if n <= 1: return 1
        a, b = 1, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    costs = []


    current_day = -1
    hires_today = 0
    lands_bought = 0


    for idx, row in df.iterrows():

        if row["day"] != current_day:
            hires_today = 0
            current_day = row["day"]

        total_cost = 0
        actions = row["market_action"]

        if isinstance(actions, list):
            if len(actions) > 0 and isinstance(actions[0], str):
                actions = [actions]

            for action in actions:
                if not isinstance(action, list) or len(action) == 0:
                    continue

                act_type = action[0]

                if act_type == "BUY_SEED" and len(action) == 3:
                    crop = action[1]
                    n = action[2]
                    if crop in seed_prices:
                        total_cost += seed_prices[crop] * n

                elif act_type == "BUY_PRODUCT" and len(action) == 3:
                    item = action[1]
                    n = action[2]
                    price_col = f"market_prices_{item}"
                    if price_col in row:
                        total_cost += row[price_col] * n

                elif act_type == "BUY_ANIMAL" and len(action) == 3:
                    animal = action[1]
                    n = action[2]
                    if animal in animal_prices:
                        total_cost += animal_prices[animal] * n

                elif act_type == "SELL" and len(action) == 3:
                    item = action[1]
                    n = action[2]
                    price_col = f"market_prices_{item}"
                    if price_col in row:

                        total_cost -= row[price_col] * n

                elif act_type == "HIRE":

                    total_cost += get_fib(hires_today)
                    hires_today += 1

                elif act_type == "BUY_LAND":
                    if lands_bought < len(land_prices):
                        total_cost += land_prices[lands_bought]
                        lands_bought += 1

        costs.append(total_cost)

    df["market_action_cost"] = costs
    return df
df_st_cost = cost(df_st)
df_be_cost = cost(df_be)

df_st_cost

df_st_cost["market_action_cost"].min()

df_st_cost["market_action_cost"].max()

def cost_plot(df,col,y):
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df, x=col, y=y)
    plt.ylim(-10000, 5000)
    plt.grid(True)
    plt.show()

cost_plot(df_st_cost,"step", 'market_action_cost')

sns_line(df_st_cost, x='step', y="market_prices_CARROT", figsize=(10,5), step=50,)

sns_line(df_st_cost, x='step', y="market_prices_EGG", figsize=(10,5), step=50,)

sns_line(df_st_cost, x='step', y="market_prices_FERTILIZER", figsize=(10,5), step=50,)

sns_line(df_st_cost, x='step', y="market_prices_MELON", figsize=(10,5), step=50,)

sns_line(df_st_cost, x='step', y="market_prices_MILK", figsize=(10,5), step=50,)

sns_line(df_st_cost, x='step', y="market_prices_STRAWBERRY", figsize=(10,5), step=50,)

sns_line(df_st_cost, x='step', y="market_prices_TOMATO", figsize=(10,5), step=50,)

sns_line(df_st_cost, x='step', y="market_prices_WHEAT", figsize=(10,5), step=50,)

sns_line(df_st_cost, x='step', y="market_prices_WOOL", figsize=(10,5), step=50,)

sns_line_smooth(df_st_cost, x='day', y="money", figsize=(10, 5), step=1,ylim=(0, 150000))