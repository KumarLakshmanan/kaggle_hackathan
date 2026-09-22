# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python Docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

# Input data files are available in the read-only "../input/" directory
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# You can write up to 20GB to the current directory (/kaggle/working/) that gets preserved as output when you create a version using "Save & Run All" 
# You can also write temporary files to /kaggle/temp/, but they won't be saved outside of the current session

# Use the kagglehub client library to attach Kaggle resources like competitions, datasets, and models to your session
# Learn more about kagglehub: https://github.com/Kaggle/kagglehub/blob/main/README.md

import kagglehub
# kagglehub.dataset_download('<owner>/<dataset-slug>')

from kaggle_environments import make

def my_agent(obs):
    return {
        "farmer": ["PASS"],
        "market": []
    }

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720},
    debug=True
)

env.run([my_agent, "starter"])

print("تم تشغيل المباراة بنجاح")



def my_agent(obs):
    step = obs.get("step", 0)

    # أول دورة: شراء بذور قمح
    if step == 0:
        return {
            "farmer": ["PASS"],
            "market": [["BUY_SEED", "WHEAT", 5]]
        }

    # باقي الدورات مؤقتاً
    return {
        "farmer": ["PLANT"],
        "market": []
    }

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720},
    debug=True
)

result = env.run([my_agent, "starter"])

final = env.steps[-1]

for i, player in enumerate(final):
    print(
        "Player:", i,
        "Reward:", player.reward,
        "Status:", player.status
    )

from kaggle_environments import make

def farm_agent(obs):
    return {
        "farmer": ["PASS"],
        "market": []
    }

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720},
    debug=True
)

result = env.run([farm_agent, "starter"])

print("تم تشغيل الوكيل بنجاح")
print("عدد الدورات:", len(env.steps))

def debug_agent(obs):
    print(obs)
    return {
        "farmer": ["PASS"],
        "market": []
    }

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 1},
    debug=True
)

env.run([debug_agent, "starter"])

from kaggle_environments import make


def farm_agent(obs):
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    tiles = farm["tiles"]
    x, y = farm["farmer"]

    seeds = private["seeds"]
    shed = private["shed"]
    money = farm["money"]

    market_orders = []

    # =====================================
    # 1. بيع المحاصيل الموجودة في المخزن
    # =====================================
    for item in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]:
        amount = shed.get(item, 0)

        if amount > 0:
            market_orders.append(["SELL", item, amount])

    # =====================================
    # 2. شراء بذور القمح
    # =====================================
    wheat_seeds = seeds.get("WHEAT", 0)

    if wheat_seeds < 3 and money >= 10:
        market_orders.append(
            ["BUY_SEED", "WHEAT", 3 - wheat_seeds]
        )

    # =====================================
    # 3. قراءة البلاطة الحالية
    # =====================================
    tile = tiles[y][x]

    # =====================================
    # 4. إذا توجد نبتة في مكان المزارع
    # =====================================
    if isinstance(tile, dict):

        if tile.get("kind") == "PLANT":

            # إذا جاهزة للحصاد
            planted_day = tile.get("planted_day", obs["day"])

            if obs["day"] - planted_day >= 2:
                return {
                    "farmer": ["HARVEST"],
                    "hands": [],
                    "market": market_orders
                }

            # إذا لم تُسقَ اليوم
            if not tile.get("watered_today", False):
                return {
                    "farmer": ["WATER"],
                    "hands": [],
                    "market": market_orders
                }

            return {
                "farmer": ["PASS"],
                "hands": [],
                "market": market_orders
            }

    # =====================================
    # 5. إذا الأرض فارغة ومعنا بذور
    # =====================================
    if tile is None and seeds.get("WHEAT", 0) > 0:
        return {
            "farmer": ["PLANT", "WHEAT"],
            "hands": [],
            "market": market_orders
        }

    # =====================================
    # 6. البحث عن أقرب أرض فارغة
    # =====================================
    targets = []

    for ty in range(len(tiles)):
        for tx in range(len(tiles[ty])):

            if tiles[ty][tx] is None:

                distance = abs(tx - x) + abs(ty - y)

                targets.append((distance, tx, ty))

    # =====================================
    # 7. التحرك نحو أقرب أرض
    # =====================================
    if targets:

        targets.sort()

        _, tx, ty = targets[0]

        if tx > x:
            return {
                "farmer": ["EAST"],
                "hands": [],
                "market": market_orders
            }

        if tx < x:
            return {
                "farmer": ["WEST"],
                "hands": [],
                "market": market_orders
            }

        if ty > y:
            return {
                "farmer": ["SOUTH"],
                "hands": [],
                "market": market_orders
            }

        if ty < y:
            return {
                "farmer": ["NORTH"],
                "hands": [],
                "market": market_orders
            }

    # =====================================
    # 8. لا يوجد شيء نفعله
    # =====================================
    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market_orders
    }


# ==========================================
# تشغيل مباراة كاملة 720 دورة
# ==========================================

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720},
    debug=True
)

result = env.run([
    farm_agent,
    "starter"
])

print("تمت المباراة!")
print("عدد الدورات:", len(env.steps))

# النتيجة النهائية
last_step = env.steps[-1]

for i, player in enumerate(last_step):
    print(
        "Player:", i,
        "| Reward:", player["reward"],
        "| Status:", player["status"]
    )

def farm_agent(obs):
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    tiles = farm["tiles"]
    x, y = farm["farmer"]
    money = farm["money"]
    seeds = private["seeds"]
    shed = private["shed"]

    day = obs["day"]
    prices = obs["market"]["prices"]

    market_orders = []

    # =====================================
    # بيع المحاصيل الموجودة
    # =====================================
    for item in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]:
        amount = shed.get(item, 0)

        if amount > 0:
            market_orders.append(["SELL", item, amount])

    # =====================================
    # شراء بذور حسب السعر
    # =====================================
    crop_prices = {
        "WHEAT": prices.get("WHEAT", 25),
        "CARROT": prices.get("CARROT", 35),
        "TOMATO": prices.get("TOMATO", 60),
        "STRAWBERRY": prices.get("STRAWBERRY", 120),
        "MELON": prices.get("MELON", 250)
    }

    # نختار أعلى محصول سعراً
    best_crop = max(crop_prices, key=crop_prices.get)

    # شراء بذور قليلة في البداية
    if seeds.get(best_crop, 0) < 3:
        seed_price = max(1, crop_prices[best_crop] // 2)

        if money >= seed_price * (3 - seeds.get(best_crop, 0)):
            market_orders.append([
                "BUY_SEED",
                best_crop,
                3 - seeds.get(best_crop, 0)
            ])

    # =====================================
    # البلاطة الحالية
    # =====================================
    tile = tiles[y][x]

    # =====================================
    # التعامل مع النبات
    # =====================================
    if isinstance(tile, dict):

        if tile.get("kind") == "PLANT":

            planted_day = tile.get(
                "planted_day",
                day
            )

            age = day - planted_day

            # حصاد
            if age >= 2:
                return {
                    "farmer": ["HARVEST"],
                    "hands": [],
                    "market": market_orders
                }

            # ري
            if not tile.get("watered_today", False):
                return {
                    "farmer": ["WATER"],
                    "hands": [],
                    "market": market_orders
                }

            return {
                "farmer": ["PASS"],
                "hands": [],
                "market": market_orders
            }

    # =====================================
    # الزراعة
    # =====================================
    if tile is None and seeds.get(best_crop, 0) > 0:
        return {
            "farmer": ["PLANT", best_crop],
            "hands": [],
            "market": market_orders
        }

    # =====================================
    # البحث عن أقرب أرض فارغة
    # =====================================
    targets = []

    for ty in range(len(tiles)):
        for tx in range(len(tiles[ty])):

            if tiles[ty][tx] is None:
                distance = abs(tx - x) + abs(ty - y)
                targets.append((distance, tx, ty))

    # =====================================
    # التحرك
    # =====================================
    if targets:

        targets.sort()

        _, tx, ty = targets[0]

        if tx > x:
            direction = "EAST"
        elif tx < x:
            direction = "WEST"
        elif ty > y:
            direction = "SOUTH"
        elif ty < y:
            direction = "NORTH"
        else:
            direction = "PASS"

        return {
            "farmer": [direction],
            "hands": [],
            "market": market_orders
        }

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market_orders
    }

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720},
    debug=True
)

result = env.run([
    farm_agent,
    "starter"
])

print("تمت المباراة!")
print("عدد الدورات:", len(env.steps))

last_step = env.steps[-1]

for i, player in enumerate(last_step):
    print(
        "Player:", i,
        "| Reward:", player["reward"],
        "| Status:", player["status"]
    )

import inspect
from kaggle_environments import make

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 1},
    debug=True
)

print(inspect.getsource(env.__class__))

from kaggle_environments import make


def farm_agent(obs):
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    x, y = farm["farmer"]
    tiles = farm["tiles"]
    seeds = private["seeds"]
    shed = private["shed"]
    money = farm["money"]

    market = []

    # ==========================================
    # شراء بذور الجزر
    # ==========================================
    carrot_seeds = seeds.get("CARROT", 0)

    if carrot_seeds < 5 and money >= 20:
        market.append([
            "BUY_SEED",
            "CARROT",
            5 - carrot_seeds
        ])

    # ==========================================
    # بيع المحاصيل الموجودة
    # ==========================================
    for crop in [
        "WHEAT",
        "CARROT",
        "TOMATO",
        "STRAWBERRY",
        "MELON"
    ]:
        amount = shed.get(crop, 0)

        if amount > 0:
            market.append([
                "SELL",
                crop,
                amount
            ])

    # ==========================================
    # البلاطة الحالية
    # ==========================================
    tile = tiles[y][x]

    # ==========================================
    # إذا كانت الأرض فارغة → ازرع
    # ==========================================
    if tile is None and carrot_seeds > 0:

        return {
            "farmer": ["PLANT", "CARROT"],
            "hands": [],
            "market": market
        }

    # ==========================================
    # إذا توجد نبتة
    # ==========================================
    if isinstance(tile, dict):

        if tile.get("kind") == "PLANT":

            crop = tile.get("crop")

            planted_day = tile.get(
                "planted_day",
                obs["day"]
            )

            age = obs["day"] - planted_day

            # الجزر يحصد بعد النمو
            if crop == "CARROT" and age >= 2:

                return {
                    "farmer": ["HARVEST"],
                    "hands": [],
                    "market": market
                }

            # ري النبات
            if not tile.get("watered_today", False):

                return {
                    "farmer": ["WATER"],
                    "hands": [],
                    "market": market
                }

    # ==========================================
    # البحث عن أقرب أرض فارغة
    # ==========================================
    targets = []

    for ty in range(5):
        for tx in range(5):

            if tiles[ty][tx] is None:

                distance = abs(tx - x) + abs(ty - y)

                targets.append(
                    (distance, tx, ty)
                )

    # ==========================================
    # التحرك
    # ==========================================
    if targets:

        targets.sort()

        _, tx, ty = targets[0]

        if tx > x:
            direction = "EAST"

        elif tx < x:
            direction = "WEST"

        elif ty > y:
            direction = "SOUTH"

        elif ty < y:
            direction = "NORTH"

        else:
            direction = "PASS"

        return {
            "farmer": [direction],
            "hands": [],
            "market": market
        }

    # ==========================================
    # لا يوجد عمل
    # ==========================================
    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }


# ==============================================
# تشغيل 720 دورة
# ==============================================

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 720
    },
    debug=True
)

result = env.run([
    farm_agent,
    "starter"
])

print("تمت المباراة!")
print("عدد الدورات:", len(env.steps))

final = env.steps[-1]

for i, player in enumerate(final):

    print(
        "Player:", i,
        "| Reward:", player["reward"],
        "| Status:", player["status"]
    )

from kaggle_environments import make

def farm_agent(obs):
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    tiles = farm["tiles"]
    x, y = farm["farmer"]
    money = farm["money"]

    seeds = private["seeds"]
    shed = private["shed"]

    day = obs["day"]
    prices = obs["market"]["prices"]

    market = []

    # ==========================================
    # بيع المحاصيل
    # ==========================================
    for crop in ["WHEAT", "CARROT", "TOMATO",
                 "STRAWBERRY", "MELON"]:

        amount = shed.get(crop, 0)

        if amount > 0:
            market.append(["SELL", crop, amount])

    # ==========================================
    # شراء بذور
    # نوزع رأس المال على عدة محاصيل
    # ==========================================

    crops = [
        ("WHEAT", 10),
        ("CARROT", 15),
        ("TOMATO", 25),
        ("STRAWBERRY", 50)
    ]

    for crop, limit in crops:

        current = seeds.get(crop, 0)

        if current < 2 and money >= limit:
            market.append([
                "BUY_SEED",
                crop,
                2 - current
            ])

    # ==========================================
    # الأرض الحالية
    # ==========================================

    tile = tiles[y][x]

    # ==========================================
    # نبات موجود
    # ==========================================

    if isinstance(tile, dict):

        if tile.get("kind") == "PLANT":

            crop = tile.get("crop")

            planted_day = tile.get(
                "planted_day",
                day
            )

            age = day - planted_day

            # حصاد
            if age >= 2:

                return {
                    "farmer": ["HARVEST"],
                    "hands": [],
                    "market": market
                }

            # ري
            if not tile.get(
                "watered_today",
                False
            ):

                return {
                    "farmer": ["WATER"],
                    "hands": [],
                    "market": market
                }

            return {
                "farmer": ["PASS"],
                "hands": [],
                "market": market
            }

    # ==========================================
    # اختيار البذرة المتوفرة
    # ==========================================

    chosen_crop = None

    for crop, _ in crops:

        if seeds.get(crop, 0) > 0:
            chosen_crop = crop
            break

    # ==========================================
    # زراعة
    # ==========================================

    if tile is None and chosen_crop:

        return {
            "farmer": [
                "PLANT",
                chosen_crop
            ],
            "hands": [],
            "market": market
        }

    # ==========================================
    # البحث عن الأرض الفارغة
    # ==========================================

    targets = []

    for ty in range(5):

        for tx in range(5):

            if tiles[ty][tx] is None:

                distance = (
                    abs(tx - x) +
                    abs(ty - y)
                )

                targets.append(
                    (distance, tx, ty)
                )

    # ==========================================
    # الحركة
    # ==========================================

    if targets:

        targets.sort()

        _, tx, ty = targets[0]

        if tx > x:
            direction = "EAST"

        elif tx < x:
            direction = "WEST"

        elif ty > y:
            direction = "SOUTH"

        elif ty < y:
            direction = "NORTH"

        else:
            direction = "PASS"

        return {
            "farmer": [direction],
            "hands": [],
            "market": market
        }

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }


# ==========================================
# المباراة
# ==========================================

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 720
    },
    debug=True
)

result = env.run([
    farm_agent,
    "starter"
])

print("تمت المباراة!")
print("عدد الدورات:", len(env.steps))

final = env.steps[-1]

for i, player in enumerate(final):

    print(
        "Player:", i,
        "| Reward:", player["reward"],
        "| Status:", player["status"]
    )

from kaggle_environments import make

def test_agent(obs):
    if obs["step"] == 0:
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", 1]]
        }

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": []
    }

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 3},
    debug=True
)

result = env.run([test_agent, "starter"])

for step in result:
    for player in step:
        if player.get("observation"):
            print(
                "STEP:",
                player["observation"].get("step"),
                "PRIVATE:",
                player["observation"].get("private")
            )

from kaggle_environments import make

def test_agent(obs):
    step = obs["step"]

    # الدورة 0: شراء بذرة
    if step == 0:
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", 1]]
        }

    # الدورة 1: زراعة القمح
    if step == 1:
        return {
            "farmer": ["PLANT", "WHEAT"],
            "hands": [],
            "market": []
        }

    # باقي الدورات لا نفعل شيئاً
    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": []
    }


env = make(
    "kaggriculture",
    configuration={"episodeSteps": 5},
    debug=True
)

result = env.run([test_agent, "starter"])

for step in result:
    for player in step:
        obs = player.get("observation")

        if obs and obs.get("player") == 0:
            x, y = obs["farms"][0]["farmer"]
            tile = obs["farms"][0]["tiles"][y][x]

            print(
                "STEP:", obs["step"],
                "| TILE:", tile
            )

from kaggle_environments import make


def farm_agent(obs):

    player = obs["player"]
    farm = obs["farms"][player]

    private = obs["private"]
    seeds = private["seeds"]
    shed = private["shed"]

    tiles = farm["tiles"]
    x, y = farm["farmer"]

    market = []

    # ==========================================
    # 1) بيع المحاصيل الموجودة
    # ==========================================

    for crop in [
        "WHEAT",
        "CARROT",
        "TOMATO",
        "STRAWBERRY",
        "MELON"
    ]:

        amount = shed.get(crop, 0)

        if amount > 0:
            market.append([
                "SELL",
                crop,
                amount
            ])

    # ==========================================
    # 2) شراء بذور القمح إذا لم توجد
    # ==========================================

    if seeds.get("WHEAT", 0) == 0:

        market.append([
            "BUY_SEED",
            "WHEAT",
            1
        ])

    # ==========================================
    # 3) معرفة البلاطة الحالية
    # ==========================================

    tile = tiles[y][x]

    # ==========================================
    # 4) إذا كانت هناك نبتة
    # ==========================================

    if isinstance(tile, dict) and tile.get("kind") == "PLANT":

        # إذا لم تُسقَ اليوم -> اسقها
        if not tile.get("watered_today", False):

            return {
                "farmer": ["WATER"],
                "hands": [],
                "market": market
            }

        # عمر النبات بالدورات
        age = obs["step"] - tile.get(
            "planted_day",
            obs["step"]
        )

        # نحصد بعد فترة نمو
        if age >= 24:

            return {
                "farmer": ["HARVEST"],
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": market
        }

    # ==========================================
    # 5) إذا الأرض فارغة وعندنا بذرة
    # ==========================================

    if tile is None and seeds.get("WHEAT", 0) > 0:

        return {
            "farmer": ["PLANT", "WHEAT"],
            "hands": [],
            "market": market
        }

    # ==========================================
    # 6) البحث عن أقرب أرض فارغة
    # ==========================================

    empty = []

    for ty in range(5):

        for tx in range(5):

            if tiles[ty][tx] is None:

                distance = (
                    abs(tx - x) +
                    abs(ty - y)
                )

                empty.append(
                    (distance, tx, ty)
                )

    # ==========================================
    # 7) التحرك
    # ==========================================

    if empty:

        empty.sort()

        _, tx, ty = empty[0]

        if tx > x:
            move = "EAST"

        elif tx < x:
            move = "WEST"

        elif ty > y:
            move = "SOUTH"

        elif ty < y:
            move = "NORTH"

        else:
            move = "PASS"

        return {
            "farmer": [move],
            "hands": [],
            "market": market
        }

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }


# ==========================================
# تشغيل المباراة
# ==========================================

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 720
    },
    debug=True
)

result = env.run([
    farm_agent,
    "starter"
])

print("تمت المباراة!")
print("عدد الدورات:", len(env.steps))

final = env.steps[-1]

for i, player in enumerate(final):

    print(
        f"Player: {i} | "
        f"Reward: {player['reward']} | "
        f"Status: {player['status']}"
    )

from kaggle_environments import make

def test_agent(obs):
    if obs["step"] == 0:
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", 1],
                       ["BUY", "FERTILIZER", 1]]
        }

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": []
    }

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 3},
    debug=True
)

result = env.run([test_agent, "starter"])

for step in result:
    for player in step:
        obs = player.get("observation")

        if obs and obs.get("player") == 0:
            print(
                "STEP:", obs["step"],
                "| SHED:", obs["private"]["shed"],
                "| SEEDS:", obs["private"]["seeds"]
            )

from pathlib import Path

base = Path("/kaggle/input/competitions/kaggriculture")

for file in base.glob("*.md"):
    print("\n" + "=" * 60)
    print(file.name)
    print("=" * 60)

    text = file.read_text(errors="ignore")

    lines = text.splitlines()

    for i, line in enumerate(lines):
        if "FERTILIZER" in line.upper():
            start = max(0, i - 5)
            end = min(len(lines), i + 8)

            for x in lines[start:end]:
                print(x)