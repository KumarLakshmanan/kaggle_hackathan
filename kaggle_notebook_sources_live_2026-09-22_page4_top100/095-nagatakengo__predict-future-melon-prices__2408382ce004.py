#!unzip /content/df_all_data_final.zip

import sys
sys.path.append("/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx")

import pandas as pd
df = pd.read_csv('/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx/df_all_data_final/df_all_data_final.csv')

def df_cl(df):
    df_test = df [["id",
                   "step",
                   "day",
                   "money",
                   "hands_n",
                   "hires_today",
                   "unlocked_quadrants",
                   "tiles",
                   "private_shed",
                   "private_seeds",
                   "market_inv",
                   "market_prices",
                   "market_action"
                   ]].copy()
    return df_test

df_all = df_cl(df)

print(f"df_allの列: {df_all.columns}")
print("")
print(f"df_allの欠損値: {df_all.isnull().values.any()}")
print("")
print(f"df_allの行と列: {df_all.shape[0]}行  {df_all.shape[1]}列")




import ast


def df_cl(df, lookbacks=(12, 24, 48)):
    """
    df作成
    """
    df_res = df.copy()

    # 試合ID
    df_res["game_id"] = df_res["step"].eq(0).cumsum()


    current_price = df_res["market_prices"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    market_stock = df_res["market_inv"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    market_actions = df_res["market_action"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    private_shed = df_res["private_shed"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    # shed内のMELON量
    df_res["amount_in_shed"] = private_shed.apply(
        lambda x: x.get("MELON", 0)
    )

    # 現在のMELON価格
    df_res["current_price"] = current_price.str["MELON"]

    # MELON市場在庫
    df_res["market_stock"] = market_stock.str["MELON"]


    # 現在ターンのMELON SELL量
    def extract_melon_sell(actions):

        total = 0

        for order in actions:
            if (
                isinstance(order, (list, tuple))
                and len(order) >= 3
                and order[0] == "SELL"
                and order[1] == "MELON"
            ):
                total += int(order[2])

        return total


    df_res["melon_sell"] = market_actions.apply(
        extract_melon_sell
    )


    # 過去特徴量
    for k in lookbacks:

        # kターン前のMELON価格
        price_k_ago = (
            df_res
            .groupby("game_id")["current_price"]
            .shift(k)
        )

        # kターン前のMELON市場在庫
        stock_k_ago = (
            df_res
            .groupby("game_id")["market_stock"]
            .shift(k)
        )

        # 過去kターンの価格変化
        df_res[f"Past_price_changes_{k}"] = (
            df_res["current_price"]
            - price_k_ago
        )

        # 過去kターンの市場在庫変化
        df_res[f"Past_inv_changes_{k}"] = (
            df_res["market_stock"]
            - stock_k_ago
        )

        # 過去kターンの自分のMELON SELL合計
        df_res[f"Past_SELL_{k}"] = (
            df_res
            .groupby("game_id")["melon_sell"]
            .transform(
                lambda s:
                s.shift(1)
                .rolling(
                    window=k,
                    min_periods=k
                )
                .sum()
            )
        )

    # 未来kターンのMELON最高価格
    for k in lookbacks:

        df_res[f"future_max_price_{k}"] = (
            df_res
            .groupby("game_id")["current_price"]
            .transform(
                lambda s:
                s.shift(-1)
                .iloc[::-1]
                .rolling(
                    window=k,
                    min_periods=k
                )
                .max()
                .iloc[::-1]
            )
        )


    df_res = df_res.drop(columns=["day",
                                  "money",
                                  "hands_n",
                                  "hires_today",
                                  "unlocked_quadrants",
                                  "tiles",
                                  "private_shed",
                                  "private_seeds",
                                  "market_inv",
                                  "market_prices",
                                  "market_action",
                                  "id",
                                  "melon_sell"

                                  ])
    df_res = df_res.dropna().reset_index(drop=True) #欠損値削除

    return df_res


df_12 = df_cl(df_all, lookbacks=(12,))

df_12.columns

print(df_12.isna().sum())

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor
import numpy as np
import pandas as pd




df_12 = df_cl(df_all, lookbacks=(12,))

game_ids = df_12["game_id"].unique()

train_ids, test_ids = train_test_split(
    game_ids,
    test_size=0.2,
    random_state=42
)

def split_xy(df, train_ids, test_ids, k):

    train_df = df[df["game_id"].isin(train_ids)].copy()
    test_df = df[df["game_id"].isin(test_ids)].copy()

    target = f"future_max_price_{k}"

    x_train = train_df.drop(
        columns=["game_id", target]
    )

    y_train = train_df[target]


    x_test = test_df.drop(
        columns=["game_id", target]
    )

    y_test = test_df[target]

    return x_train, x_test, y_train, y_test



x_train_12, x_test_12, y_train_12, y_test_12 = split_xy(
    df_12, train_ids, test_ids, 12
)


#---------------------
# DecisionTree
#---------------------

dt = DecisionTreeRegressor(
    random_state=42
)

dt.fit(x_train_12, y_train_12)
pred_dt = dt.predict(x_test_12)

mae_dt = mean_absolute_error(y_test_12, pred_dt)
rmse_dt = np.sqrt(mean_squared_error(y_test_12, pred_dt))

print("DecisionTree")
print("MAE :", mae_dt)
print("RMSE :", rmse_dt)
print("")

#---------------------
#GBM
#---------------------

gbm = GradientBoostingRegressor(
    random_state=42
)

gbm.fit(x_train_12, y_train_12)

pred_gbm = gbm.predict(x_test_12)

mae_gbm = mean_absolute_error(y_test_12, pred_gbm)
rmse_gbm = np.sqrt(mean_squared_error(y_test_12, pred_gbm))

print("GBM")
print("MAE :", mae_gbm)
print("RMSE:", rmse_gbm)
print("")

#---------------------
# XGBoost
#---------------------

xgb = XGBRegressor(
    random_state=42
)

xgb.fit(x_train_12, y_train_12)

pred_xgb = xgb.predict(x_test_12)

mae_xgb = mean_absolute_error(y_test_12, pred_xgb)
rmse_xgb = np.sqrt(mean_squared_error(y_test_12, pred_xgb))

print("XGBoost")
print("MAE :", mae_xgb)
print("RMSE:", rmse_xgb)
print("")

!pip install m2cgen

import m2cgen as m2c

code = m2c.export_to_python(dt)
#print(code)  深すぎ！！！！