


import sys
sys.path.append("/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx")



import pandas as pd
from kaggriculture_df import Kaggriculture_df
from my_plot import sns_Hist
import ast
from numpy import astype
from kaggle_kaggriculture import convert, xy_plt_2d, xy_plt_2d_all, create_all_hands_feature, new_xy_plt_2d
import matplotlib.pyplot as plt
import seaborn as sns


df_st = (Kaggriculture_df("/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx/results/st_data/strong_rank1_score157577.0_p1.json", 1)).df

"""
df_st = (Kaggriculture_df("/content/strong_rank1_score157577.0_p1.json", 1)).df

"""


df_st

xy_plt_2d(df_st["farmer_x_y"])

xy_plt_2d_all(df_st, ["hands_list_1", "hands_list_2"], 1, 2)

cols_st = ["farmer_x_y"] + [f"hands_list_{i}" for i in range(1, 17)]
xy_plt_2d_all(df_st, cols_st, 3, 6)

df_st = create_all_hands_feature(df_st)

new_xy_plt_2d(df_st["all_hands"])
xy_plt_2d(df_st["farmer_x_y"])

df_st["unlocked_quadrants"].value_counts()

df_st_unlock = df_st[["step", "unlocked_quadrants"]].copy()
df_st_unlock["unlocked_quadrants"] = df_st_unlock["unlocked_quadrants"].astype(str)
sns_Hist(data=df_st_unlock, x="step", hue="unlocked_quadrants", figsize=(15,10), step=25, bins=720)

#1
def workers_action(df):
    """
    df作成

    """
    base_cols = ["step", "farmer_x_y", "farmer_action"]
    hands_list_cols = [f"hands_list_{i}" for i in range(1, 15)]
    hands_action_cols = [f"hands_action_list_{i}" for i in range(1, 15)]



    return df[["money"] + base_cols + hands_list_cols + hands_action_cols].copy()

#2
def workers_count_list (df):
    """
    df全員分の行動を出力する
    """
    print(df_st_action["farmer_action"].value_counts())
    for i in range(1, 15):
        col_name = f"hands_action_list_{i}"
        if col_name in df.columns:
            print(f"--- {col_name}  ---")
            print(df[col_name].value_counts())
            print()

#4
def my_action_2d_plt(df_xy, df_action, target_action, figsize=(6, 5)):
    """
    特定のアクションが実行された座標をヒートマップに変換：単体

    <df_xy>: 2D配列のSeries (例: df["farmer_x_y"])
    <df_action>: アクションのSeries (例: df["farmer_action"])
    <target_action>: 可視化したいアクションの文字列 (例: "WATER" や "FEED, WHEAT")
    <figsize>: グラフのサイズ設定
    """
    df = pd.DataFrame({
        "x_y": df_xy,
        "action": df_action
    })

    df_filtered = df[df["action"].astype(str).str.contains(target_action, na=False, regex=False)]

    df_filtered_xy = df_filtered["x_y"].apply(convert)
    df_plot = pd.DataFrame(df_filtered_xy.tolist(), columns=["x", "y"])
    df_plot = df_plot.dropna().astype(int)

    heatmap_data = pd.crosstab(df_plot['y'], df_plot['x'])

    grid_range = list(range(10))
    heatmap_data = heatmap_data.reindex(
        index=grid_range, columns=grid_range, fill_value=0
    )

    plt.figure(figsize=figsize)
    sns.heatmap(heatmap_data, annot=True, cmap="Blues", fmt="d")
    plt.title(f"Action: {target_action}")
    plt.show()
#5
def my_action_2d_plt_all(df_xy, df_action, target_actions, n_rows, n_cols):
    """
    複数のアクションをそれぞれのヒートマップに変換し、一気に描画する

    <df_xy>: 2D配列のSeries (例: df["farmer_x_y"])
    <df_action>: アクションのSeries (例: df["farmer_action"])
    <target_actions>: 可視化したいアクションのリスト (例: ["PLANT", "WATER", "HARVEST"])
    <n_rows>: 行の数
    <n_cols>: 列の数
    """
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 4))

    if n_rows * n_cols > 1:
        axes = axes.flatten()
    else:
        axes = [axes]

    grid_range = list(range(10))

    df = pd.DataFrame({
        "x_y": df_xy,
        "action": df_action
    })

    for i, action_str in enumerate(target_actions):
        ax = axes[i]

        df_filtered = df[df["action"].astype(str).str.contains(action_str, na=False, regex=False)]

        df_filtered_xy = df_filtered["x_y"].apply(convert)
        df_plot = pd.DataFrame(df_filtered_xy.tolist(), columns=["x", "y"])
        df_plot = df_plot.dropna().astype(int)

        if not df_plot.empty:
            heatmap_data = pd.crosstab(df_plot['y'], df_plot['x'])
            heatmap_data = heatmap_data.reindex(
                index=grid_range, columns=grid_range, fill_value=0
            )
        else:
            heatmap_data = pd.DataFrame(0, index=grid_range, columns=grid_range)
        ax.grid(False)
        sns.heatmap(heatmap_data, annot=True, cmap="Blues", fmt="d", ax=ax, cbar=False)
        ax.set_title(f"Action: {action_str}")

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.show()


df_st_action = workers_action(df_st)

df_st_action

df_st_action.columns

target_list = ["PICKUP", "DROP", "PLACE"]
my_action_2d_plt_all(df_st_action["farmer_x_y"], df_st_action["farmer_action"], target_list, 1, 3)

def ac_move(num):
    print(f"従業員{num}")
    target_list = ["PICKUP", "DROP", "PLACE"]
    my_action_2d_plt_all(df_st[f'hands_list_{num}'], df_st[f'hands_action_list_{num}'], target_list, 1, 3)

for i in range(1, 15):
    ac_move(i)

target_list = ["PLANT", "WATER", "HARVEST","FERTILIZE","DIG" ]
my_action_2d_plt_all(df_st_action["farmer_x_y"], df_st_action["farmer_action"], target_list, 2, 3)

def ac_agriculture(num):
    print(f"従業員{num}")
    target_list = ["PLANT", "WATER", "HARVEST","FERTILIZE","DIG" ]
    my_action_2d_plt_all(df_st[f'hands_list_{num}'], df_st[f'hands_action_list_{num}'], target_list, 2, 3)

for i in range(1, 15):
    ac_agriculture(i)

target_list = ["BUILD_COOP", "BUILD_PASTURE", "FEED","COLLECT_FERTILIZER","CARE" ]
my_action_2d_plt_all(df_st_action["farmer_x_y"], df_st_action["farmer_action"], target_list, 2, 3)

def ac_animal(num):
    print(f"従業員{num}")
    target_list = ["BUILD_COOP", "BUILD_PASTURE", "FEED","COLLECT_FERTILIZER","CARE" ]
    my_action_2d_plt_all(df_st[f'hands_list_{num}'], df_st[f'hands_action_list_{num}'], target_list, 2, 3)

for i in range(1, 15):
    ac_animal(i)

from matplotlib.animation import FuncAnimation
from IPython.display import HTML, display
import numpy as np

def route_animation(data):
    xy = np.array(data.tolist(), dtype=float)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(-0.5, 9.5)
    ax.set_ylim(9.5, -0.5)
    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    ax.set_aspect("equal")
    ax.grid()

    line, = ax.plot([], [], alpha=.5)
    point, = ax.plot([], [], "ro")

    def update(i):
        line.set_data(xy[:i, 0], xy[:i, 1])
        point.set_data([xy[i-1, 0]], [xy[i-1, 1]])
        return line, point

    ani = FuncAnimation(
        fig,
        update,
        frames=range(1, len(xy) + 1, 5),
        interval=250
    )

    plt.close(fig)
    return HTML(ani.to_jshtml())

display(route_animation(df_st["farmer_x_y"]))

display(route_animation(df_st["hands_list_1"]))

display(route_animation(df_st["hands_list_2"]))

display(route_animation(df_st["hands_list_3"]))

display(route_animation(df_st["hands_list_4"]))

display(route_animation(df_st["hands_list_5"]))

display(route_animation(df_st["hands_list_6"]))

display(route_animation(df_st["hands_list_7"]))

display(route_animation(df_st["hands_list_8"]))

display(route_animation(df_st["hands_list_9"]))

display(route_animation(df_st["hands_list_10"]))

display(route_animation(df_st["hands_list_11"]))

display(route_animation(df_st["hands_list_12"]))

display(route_animation(df_st["hands_list_13"]))

display(route_animation(df_st["hands_list_14"]))