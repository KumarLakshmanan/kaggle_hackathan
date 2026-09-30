# Plain-text extraction, 2026-09-24. No strategy changes.
# Source: Oleg Melnik / olegmelnik, Kaggriculture v26 Seat Portfolio.
# https://www.kaggle.com/code/olegmelnik/kaggriculture-v26-seat-portfolio
# Notebook: kaggriculture-v26-seat-portfolio.ipynb
# Notebook SHA-256:
# bcd93a9472662b729711b119f1ba37efe20db7f5772bf4166a2ddb7786d20dae
# Extraction: zero-based cell 11, _AGENT_B85_PARTS, decoded statically.
# Original artifact: 32,232 bytes; SHA-256:
# 7996bed506ca5ade5663a58a9af5789a329b3f426dcd9787062ad98f22b07bb8
#
# Upstream attribution retained from notebook cells 1 and 10:
# - Yubo WANG: public observed complete route used for engine seat 0.
#   Submission 55376568; episode 91352435; source seat 1.
#   https://www.kaggle.com/competitions/kaggriculture/episodes/91352435
#   Action SHA-256:
#   839c64edcc99feb17cdaaccef865fe1431e1e07e4267651b790bf361c49b79cc
# - Gbining: public observed complete route used for engine seat 1.
#   Submission 55376531; episode 91351520; source seat 1.
#   https://www.kaggle.com/competitions/kaggriculture/episodes/91351520
#   Action SHA-256:
#   7d184e460284ae83992bbcf59aa730b6a55d1aa6c833d9710ce74b6ab622d4a2
# - The upstream notebook (history: Kaito v22 Price Impact) contributes
#   the seat portfolio, chronological protocol, WEED transaction repair,
#   and SELL-slot controller. These observed routes are not hidden-source
#   recovery or newly invented farm plans.
# - This derivative only expands encoded data to readable Python literals
#   and removes the now-unused base64/json/zlib imports. Controller source
#   and route values are preserved. No independent game evaluation was run.
#
# Runtime dependencies: Python standard library copy and math only.
# No runtime compression, decoding, dynamic code loading, or file access.
# Notebook packaging, plotting, imports of the generated artifact, and smoke
# tests were NOT executed or included.
#
# Upstream caveats (cells 6, 9, 10):
# The 24/25 result is a notebook-reported fixed-replay test, not a Kaggle
# score or an independently reproduced result for this derivative.
# Its fresh panel omitted the Seb/HIRE6 family and included a -10,939 loss
# to Gbining in candidate seat 0 (episode 91360601).
# Research engine: 1.32.6. Adaptation to other configurations is unverified.
# Preserved implementation limitations: default configuration=None chooses
# legacy demand; market parameters are fixed; route step clamps at 718;
# weed repair covers BUILD_PASTURE and PLANT only; broad errors return PASS.
# The caller must start games at step 0 (or use a fresh module per game).
# Global weed-repair state is maintained separately per engine seat.
#
"""v26 seat-aware current-meta portfolio for Kaggriculture.

Each engine seat receives one independently validated complete 719-action
backbone.  Routes are never spliced mid-game and opponent identity is unused.
Runtime feedback is limited to actor-local WEED repair and ordering existing
SELL slots by official price impact plus bounded current Town demand.
"""
import copy
import math


_SEAT0_ACTIONS = [
    # Step 0 (day 0, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_ANIMAL', 'COW', 1],
                ['BUY_ANIMAL', 'SHEEP', 4], ['BUY_SEED', 'WHEAT', 5], ['BUY_SEED', 'MELON', 5],
                ['BUY_PRODUCT', 'WHEAT', 5]]},
    # Step 1 (day 0, hour 1).
    {'farmer': ['PICKUP', 'COW', 1],
     'hands': [['WEST'], ['WEST'], ['PASS'], ['PICKUP', 'SHEEP', 4]],
     'market': []},
    # Step 2 (day 0, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['NORTH'], ['NORTH'], ['PASS'], ['PICKUP', 'WHEAT', 4]],
     'market': []},
    # Step 3 (day 0, hour 3).
    {'farmer': ['WEST'], 'hands': [['NORTH'], ['NORTH'], ['PASS'], ['BUILD_PASTURE']], 'market': []},
    # Step 4 (day 0, hour 4).
    {'farmer': ['BUILD_PASTURE'],
     'hands': [['NORTH'], ['NORTH'], ['PASS'], ['PLACE', 'SHEEP']],
     'market': []},
    # Step 5 (day 0, hour 5).
    {'farmer': ['PLACE', 'COW'],
     'hands': [['PLANT', 'MELON'], ['NORTH'], ['PASS'], ['FEED', 'WHEAT']],
     'market': []},
    # Step 6 (day 0, hour 6).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['WATER'], ['NORTH'], ['PASS'], ['CARE']], 'market': []},
    # Step 7 (day 0, hour 7).
    {'farmer': ['CARE'], 'hands': [['NORTH'], ['PLANT', 'WHEAT'], ['PASS'], ['NORTH']], 'market': []},
    # Step 8 (day 0, hour 8).
    {'farmer': ['PASS'],
     'hands': [['PLANT', 'WHEAT'], ['WATER'], ['PASS'], ['BUILD_PASTURE']],
     'market': []},
    # Step 9 (day 0, hour 9).
    {'farmer': ['PASS'], 'hands': [['WATER'], ['WEST'], ['PASS'], ['PLACE', 'SHEEP']], 'market': []},
    # Step 10 (day 0, hour 10).
    {'farmer': ['PASS'],
     'hands': [['WEST'], ['PLANT', 'WHEAT'], ['PASS'], ['FEED', 'WHEAT']],
     'market': []},
    # Step 11 (day 0, hour 11).
    {'farmer': ['PASS'], 'hands': [['SOUTH'], ['WATER'], ['PASS'], ['CARE']], 'market': []},
    # Step 12 (day 0, hour 12).
    {'farmer': ['PASS'], 'hands': [['PLANT', 'MELON'], ['WEST'], ['PASS'], ['NORTH']], 'market': []},
    # Step 13 (day 0, hour 13).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PLANT', 'WHEAT'], ['PASS'], ['BUILD_PASTURE']],
     'market': []},
    # Step 14 (day 0, hour 14).
    {'farmer': ['PASS'], 'hands': [['WEST'], ['WATER'], ['PASS'], ['PLACE', 'SHEEP']], 'market': []},
    # Step 15 (day 0, hour 15).
    {'farmer': ['PASS'],
     'hands': [['PLANT', 'MELON'], ['WEST'], ['PASS'], ['FEED', 'WHEAT']],
     'market': []},
    # Step 16 (day 0, hour 16).
    {'farmer': ['PASS'], 'hands': [['WATER'], ['PLANT', 'WHEAT'], ['PASS'], ['CARE']], 'market': []},
    # Step 17 (day 0, hour 17).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['PASS'], ['WEST']], 'market': []},
    # Step 18 (day 0, hour 18).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['SOUTH'], ['PASS'], ['SOUTH']], 'market': []},
    # Step 19 (day 0, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PLANT', 'MELON'], ['PASS'], ['BUILD_PASTURE']],
     'market': []},
    # Step 20 (day 0, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['PASS'], ['PLACE', 'SHEEP']], 'market': []},
    # Step 21 (day 0, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['EAST'], ['PASS'], ['FEED', 'WHEAT']], 'market': []},
    # Step 22 (day 0, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PLANT', 'MELON'], ['PASS'], ['CARE']], 'market': []},
    # Step 23 (day 0, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['PASS'], ['PASS']], 'market': []},
    # Step 24 (day 1, hour 0).
    {'farmer': ['PASS'], 'hands': [], 'market': [['HIRE']]},
    # Step 25 (day 1, hour 1).
    {'farmer': ['CARE'], 'hands': [['WEST']], 'market': []},
    # Step 26 (day 1, hour 2).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['NORTH']], 'market': []},
    # Step 27 (day 1, hour 3).
    {'farmer': ['WEST'], 'hands': [['CARE']], 'market': []},
    # Step 28 (day 1, hour 4).
    {'farmer': ['CARE'], 'hands': [['COLLECT_FERTILIZER']], 'market': []},
    # Step 29 (day 1, hour 5).
    {'farmer': ['NORTH'], 'hands': [['NORTH']], 'market': []},
    # Step 30 (day 1, hour 6).
    {'farmer': ['CARE'], 'hands': [['CARE']], 'market': []},
    # Step 31 (day 1, hour 7).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['COLLECT_FERTILIZER']], 'market': []},
    # Step 32 (day 1, hour 8).
    {'farmer': ['SOUTH'], 'hands': [['WEST']], 'market': []},
    # Step 33 (day 1, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['SOUTH']], 'market': []},
    # Step 34 (day 1, hour 10).
    {'farmer': ['PASS'], 'hands': [['SOUTH']], 'market': []},
    # Step 35 (day 1, hour 11).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 36 (day 1, hour 12).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 37 (day 1, hour 13).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 38 (day 1, hour 14).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 39 (day 1, hour 15).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 40 (day 1, hour 16).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 41 (day 1, hour 17).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 42 (day 1, hour 18).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 43 (day 1, hour 19).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 44 (day 1, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 45 (day 1, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 46 (day 1, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 47 (day 1, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 48 (day 2, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 6]]},
    # Step 49 (day 2, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 1], 'hands': [['WEST'], ['NORTH']], 'market': []},
    # Step 50 (day 2, hour 2).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['PICKUP', 'WHEAT', 4], ['NORTH']], 'market': []},
    # Step 51 (day 2, hour 3).
    {'farmer': ['CARE'], 'hands': [['NORTH'], ['NORTH']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 52 (day 2, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['FEED', 'WHEAT'], ['NORTH']], 'market': []},
    # Step 53 (day 2, hour 5).
    {'farmer': ['WEST'], 'hands': [['CARE'], ['WATER']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 54 (day 2, hour 6).
    {'farmer': ['NORTH'], 'hands': [['COLLECT_FERTILIZER'], ['NORTH']], 'market': []},
    # Step 55 (day 2, hour 7).
    {'farmer': ['NORTH'], 'hands': [['NORTH'], ['WATER']], 'market': []},
    # Step 56 (day 2, hour 8).
    {'farmer': ['NORTH'], 'hands': [['FEED', 'WHEAT'], ['WEST']], 'market': []},
    # Step 57 (day 2, hour 9).
    {'farmer': ['WATER'], 'hands': [['CARE'], ['WATER']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 58 (day 2, hour 10).
    {'farmer': ['WEST'], 'hands': [['COLLECT_FERTILIZER'], ['WEST']], 'market': []},
    # Step 59 (day 2, hour 11).
    {'farmer': ['WATER'], 'hands': [['WEST'], ['WATER']], 'market': []},
    # Step 60 (day 2, hour 12).
    {'farmer': ['WEST'], 'hands': [['SOUTH'], ['WEST']], 'market': []},
    # Step 61 (day 2, hour 13).
    {'farmer': ['WATER'], 'hands': [['FEED', 'WHEAT'], ['WATER']], 'market': []},
    # Step 62 (day 2, hour 14).
    {'farmer': ['WEST'], 'hands': [['CARE'], ['WEST']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 63 (day 2, hour 15).
    {'farmer': ['WATER'], 'hands': [['COLLECT_FERTILIZER'], ['WATER']], 'market': []},
    # Step 64 (day 2, hour 16).
    {'farmer': ['PASS'], 'hands': [['SOUTH'], ['PASS']], 'market': []},
    # Step 65 (day 2, hour 17).
    {'farmer': ['PASS'], 'hands': [['FEED', 'WHEAT'], ['PASS']], 'market': []},
    # Step 66 (day 2, hour 18).
    {'farmer': ['PASS'], 'hands': [['CARE'], ['PASS']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 67 (day 2, hour 19).
    {'farmer': ['PASS'], 'hands': [['COLLECT_FERTILIZER'], ['PASS']], 'market': []},
    # Step 68 (day 2, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS']], 'market': []},
    # Step 69 (day 2, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS']], 'market': []},
    # Step 70 (day 2, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS']], 'market': []},
    # Step 71 (day 2, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS']], 'market': []},
    # Step 72 (day 3, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_SEED', 'WHEAT', 1],
                ['BUY_SEED', 'STRAWBERRY', 3]]},
    # Step 73 (day 3, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 1], 'hands': [['WEST'], ['WEST'], ['WEST']], 'market': []},
    # Step 74 (day 3, hour 2).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['NORTH']], 'market': []},
    # Step 75 (day 3, hour 3).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 76 (day 3, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH']], 'market': []},
    # Step 77 (day 3, hour 5).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['PLANT', 'STRAWBERRY'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 78 (day 3, hour 6).
    {'farmer': ['CARE'], 'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH']], 'market': []},
    # Step 79 (day 3, hour 7).
    {'farmer': ['NORTH'], 'hands': [['NORTH'], ['WEST'], ['WATER']], 'market': []},
    # Step 80 (day 3, hour 8).
    {'farmer': ['CARE'], 'hands': [['FEED', 'WHEAT'], ['PLANT', 'STRAWBERRY'], ['WEST']], 'market': []},
    # Step 81 (day 3, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WATER'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 82 (day 3, hour 10).
    {'farmer': ['SOUTH'], 'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['WEST']], 'market': []},
    # Step 83 (day 3, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['PLANT', 'STRAWBERRY'], ['WEST']],
     'market': []},
    # Step 84 (day 3, hour 12).
    {'farmer': ['NORTH'], 'hands': [['SOUTH'], ['WATER'], ['SOUTH']], 'market': []},
    # Step 85 (day 3, hour 13).
    {'farmer': ['NORTH'], 'hands': [['FEED', 'WHEAT'], ['NORTH'], ['SOUTH']], 'market': []},
    # Step 86 (day 3, hour 14).
    {'farmer': ['NORTH'],
     'hands': [['SOUTH'], ['NORTH'], ['PLANT', 'WHEAT']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 87 (day 3, hour 15).
    {'farmer': ['NORTH'], 'hands': [['FEED', 'WHEAT'], ['WATER'], ['WATER']], 'market': []},
    # Step 88 (day 3, hour 16).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['WEST'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 89 (day 3, hour 17).
    {'farmer': ['WEST'], 'hands': [['PASS'], ['WATER'], ['PASS']], 'market': []},
    # Step 90 (day 3, hour 18).
    {'farmer': ['WATER'], 'hands': [['PASS'], ['EAST'], ['PASS']], 'market': []},
    # Step 91 (day 3, hour 19).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 92 (day 3, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 93 (day 3, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 94 (day 3, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 95 (day 3, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 96 (day 4, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 97 (day 4, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['WEST'], ['NORTH'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 5]]},
    # Step 98 (day 4, hour 2).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['NORTH']], 'market': []},
    # Step 99 (day 4, hour 3).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 100 (day 4, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH']], 'market': []},
    # Step 101 (day 4, hour 5).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 102 (day 4, hour 6).
    {'farmer': ['WEST'], 'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['NORTH']], 'market': []},
    # Step 103 (day 4, hour 7).
    {'farmer': ['WEST'], 'hands': [['NORTH'], ['WATER'], ['WATER']], 'market': []},
    # Step 104 (day 4, hour 8).
    {'farmer': ['WEST'], 'hands': [['FEED', 'WHEAT'], ['WEST'], ['HARVEST']], 'market': []},
    # Step 105 (day 4, hour 9).
    {'farmer': ['NORTH'], 'hands': [['CARE'], ['WATER'], ['PLANT', 'WHEAT']], 'market': []},
    # Step 106 (day 4, hour 10).
    {'farmer': ['NORTH'], 'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['WATER']], 'market': []},
    # Step 107 (day 4, hour 11).
    {'farmer': ['NORTH'], 'hands': [['WEST'], ['WATER'], ['WEST']], 'market': []},
    # Step 108 (day 4, hour 12).
    {'farmer': ['WATER'], 'hands': [['SOUTH'], ['WEST'], ['WATER']], 'market': []},
    # Step 109 (day 4, hour 13).
    {'farmer': ['EAST'], 'hands': [['FEED', 'WHEAT'], ['NORTH'], ['HARVEST']], 'market': []},
    # Step 110 (day 4, hour 14).
    {'farmer': ['NORTH'], 'hands': [['CARE'], ['WATER'], ['PLANT', 'WHEAT']], 'market': []},
    # Step 111 (day 4, hour 15).
    {'farmer': ['WATER'], 'hands': [['COLLECT_FERTILIZER'], ['HARVEST'], ['WATER']], 'market': []},
    # Step 112 (day 4, hour 16).
    {'farmer': ['HARVEST'], 'hands': [['SOUTH'], ['PLANT', 'WHEAT'], ['WEST']], 'market': []},
    # Step 113 (day 4, hour 17).
    {'farmer': ['PASS'], 'hands': [['FEED', 'WHEAT'], ['WATER'], ['WATER']], 'market': []},
    # Step 114 (day 4, hour 18).
    {'farmer': ['PASS'], 'hands': [['CARE'], ['EAST'], ['HARVEST']], 'market': []},
    # Step 115 (day 4, hour 19).
    {'farmer': ['PASS'],
     'hands': [['COLLECT_FERTILIZER'], ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 116 (day 4, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['WATER']], 'market': []},
    # Step 117 (day 4, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 118 (day 4, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 119 (day 4, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 120 (day 5, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WHEAT', 17], ['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_ANIMAL', 'COW', 1], ['BUY_SEED', 'WHEAT', 1], ['BUY_SEED', 'STRAWBERRY', 4]]},
    # Step 121 (day 5, hour 1).
    {'farmer': ['PICKUP', 'COW', 1],
     'hands': [['WEST'], ['WEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 122 (day 5, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['WEST']],
     'market': []},
    # Step 123 (day 5, hour 3).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['NORTH'], ['NORTH'], ['WEST']], 'market': []},
    # Step 124 (day 5, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 125 (day 5, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 126 (day 5, hour 6).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['PLANT', 'STRAWBERRY']],
     'market': []},
    # Step 127 (day 5, hour 7).
    {'farmer': ['WEST'], 'hands': [['NORTH'], ['WATER'], ['WATER']], 'market': []},
    # Step 128 (day 5, hour 8).
    {'farmer': ['BUILD_PASTURE'], 'hands': [['FEED', 'WHEAT'], ['WEST'], ['WEST']], 'market': []},
    # Step 129 (day 5, hour 9).
    {'farmer': ['PLACE', 'COW'],
     'hands': [['CARE'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 130 (day 5, hour 10).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 131 (day 5, hour 11).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 132 (day 5, hour 12).
    {'farmer': ['EAST'], 'hands': [['SOUTH'], ['EAST'], ['EAST']], 'market': []},
    # Step 133 (day 5, hour 13).
    {'farmer': ['CARE'], 'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['EAST']], 'market': []},
    # Step 134 (day 5, hour 14).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['PLANT', 'STRAWBERRY'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 135 (day 5, hour 15).
    {'farmer': ['PASS'], 'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['PASS']], 'market': []},
    # Step 136 (day 5, hour 16).
    {'farmer': ['PASS'], 'hands': [['SOUTH'], ['EAST'], ['PASS']], 'market': []},
    # Step 137 (day 5, hour 17).
    {'farmer': ['PASS'], 'hands': [['FEED', 'WHEAT'], ['PLANT', 'STRAWBERRY'], ['PASS']], 'market': []},
    # Step 138 (day 5, hour 18).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 139 (day 5, hour 19).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WEST'], ['PASS']], 'market': []},
    # Step 140 (day 5, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WEST'], ['PASS']], 'market': []},
    # Step 141 (day 5, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['SOUTH'], ['PASS']], 'market': []},
    # Step 142 (day 5, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PLANT', 'STRAWBERRY'], ['PASS']], 'market': []},
    # Step 143 (day 5, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['PASS']], 'market': []},
    # Step 144 (day 6, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 145 (day 6, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 3], 'hands': [['WEST'], ['NORTH'], ['WEST']], 'market': []},
    # Step 146 (day 6, hour 2).
    {'farmer': ['HARVEST'], 'hands': [['PICKUP', 'WHEAT', 3], ['NORTH'], ['WEST']], 'market': []},
    # Step 147 (day 6, hour 3).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['NORTH'], ['NORTH'], ['WEST']], 'market': []},
    # Step 148 (day 6, hour 4).
    {'farmer': ['CARE'],
     'hands': [['HARVEST'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 149 (day 6, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['FEED', 'WHEAT'], ['WATER'], ['WEST']], 'market': []},
    # Step 150 (day 6, hour 6).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 151 (day 6, hour 7).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH']], 'market': []},
    # Step 152 (day 6, hour 8).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 153 (day 6, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['HARVEST'], ['WATER'], ['WATER']], 'market': []},
    # Step 154 (day 6, hour 10).
    {'farmer': ['WEST'], 'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH']], 'market': []},
    # Step 155 (day 6, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 156 (day 6, hour 12).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 157 (day 6, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['WEST'], ['WATER'], ['WATER']], 'market': []},
    # Step 158 (day 6, hour 14).
    {'farmer': ['EAST'], 'hands': [['SOUTH'], ['SOUTH'], ['EAST']], 'market': []},
    # Step 159 (day 6, hour 15).
    {'farmer': ['EAST'], 'hands': [['HARVEST'], ['WATER'], ['EAST']], 'market': []},
    # Step 160 (day 6, hour 16).
    {'farmer': ['DROP'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['EAST']],
     'market': [['SELL', 'WOOL', 5], ['SELL', 'FERTILIZER', 3], ['BUY_LAND']]},
    # Step 161 (day 6, hour 17).
    {'farmer': ['EAST'],
     'hands': [['CARE'], ['EAST'], ['EAST']],
     'market': [['HIRE'], ['BUY_ANIMAL', 'COW', 2], ['BUY_SEED', 'WHEAT', 1],
                ['BUY_SEED', 'STRAWBERRY', 2], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 162 (day 6, hour 18).
    {'farmer': ['PICKUP', 'COW', 2],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['EAST'], ['EAST']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 163 (day 6, hour 19).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['EAST'], ['WEST'], ['EAST'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 164 (day 6, hour 20).
    {'farmer': ['BUILD_PASTURE'],
     'hands': [['EAST'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['BUILD_PASTURE']],
     'market': []},
    # Step 165 (day 6, hour 21).
    {'farmer': ['PLACE', 'COW'], 'hands': [['NORTH'], ['PASS'], ['WATER'], ['EAST']], 'market': []},
    # Step 166 (day 6, hour 22).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['NORTH'], ['PASS'], ['EAST'], ['EAST']], 'market': []},
    # Step 167 (day 6, hour 23).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['PASS'], ['PLANT', 'STRAWBERRY'], ['NORTH']],
     'market': []},
    # Step 168 (day 7, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 15], ['SELL', 'FERTILIZER', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_ANIMAL', 'COW', 2]]},
    # Step 169 (day 7, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'COW', 3], ['WEST'], ['EAST'], ['PICKUP', 'WHEAT', 4], ['NORTH'], ['NORTH'],
               ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 3], ['BUY_SEED', 'STRAWBERRY', 10], ['BUY_PRODUCT', 'WHEAT', 4]]},
    # Step 170 (day 7, hour 2).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['NORTH'], ['NORTH'], ['NORTH'], ['NORTH'],
               ['NORTH']],
     'market': []},
    # Step 171 (day 7, hour 3).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'],
               ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 172 (day 7, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['NORTH'], ['NORTH'], ['CARE'], ['PLANT', 'STRAWBERRY'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 173 (day 7, hour 5).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['WATER'], ['NORTH']],
     'market': []},
    # Step 174 (day 7, hour 6).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['PLANT', 'STRAWBERRY'], ['NORTH'], ['EAST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 175 (day 7, hour 7).
    {'farmer': ['CARE'],
     'hands': [['BUILD_PASTURE'], ['WATER'], ['WATER'], ['FEED', 'WHEAT'], ['SOUTH'], ['WATER'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 176 (day 7, hour 8).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['PLACE', 'COW'], ['WEST'], ['EAST'], ['CARE'], ['PLANT', 'STRAWBERRY'], ['WEST'],
               ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 177 (day 7, hour 9).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['WATER'], ['WATER']],
     'market': []},
    # Step 178 (day 7, hour 10).
    {'farmer': ['NORTH'],
     'hands': [['CARE'], ['SOUTH'], ['WATER'], ['WEST'], ['EAST'], ['WEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 179 (day 7, hour 11).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['SOUTH'], ['PLANT', 'STRAWBERRY'], ['WATER'],
               ['WATER']],
     'market': []},
    # Step 180 (day 7, hour 12).
    {'farmer': ['WEST'],
     'hands': [['BUILD_PASTURE'], ['WEST'], ['PLANT', 'STRAWBERRY'], ['FEED', 'WHEAT'], ['WATER'],
               ['WEST'], ['EAST']],
     'market': []},
    # Step 181 (day 7, hour 13).
    {'farmer': ['SOUTH'],
     'hands': [['PLACE', 'COW'], ['WATER'], ['WATER'], ['CARE'], ['EAST'], ['WATER'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 182 (day 7, hour 14).
    {'farmer': ['WATER'],
     'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['EAST'], ['COLLECT_FERTILIZER'], ['PLANT', 'STRAWBERRY'],
               ['SOUTH'], ['EAST']],
     'market': []},
    # Step 183 (day 7, hour 15).
    {'farmer': ['EAST'],
     'hands': [['CARE'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['WEST'], ['WATER'], ['WATER'],
               ['PLANT', 'WHEAT']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 184 (day 7, hour 16).
    {'farmer': ['CARE'],
     'hands': [['EAST'], ['EAST'], ['WATER'], ['SOUTH'], ['WEST'], ['HARVEST'], ['WATER']],
     'market': []},
    # Step 185 (day 7, hour 17).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['SOUTH'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['PLANT', 'WHEAT'],
               ['EAST']],
     'market': []},
    # Step 186 (day 7, hour 18).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['NORTH'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['NORTH'], ['WATER'], ['EAST']],
     'market': []},
    # Step 187 (day 7, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PLACE', 'COW'], ['NORTH'], ['WATER'], ['PASS'], ['DIG'], ['NORTH'], ['EAST']],
     'market': []},
    # Step 188 (day 7, hour 20).
    {'farmer': ['PASS'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['SOUTH'], ['PASS'], ['PLANT', 'WHEAT'], ['NORTH'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 189 (day 7, hour 21).
    {'farmer': ['PASS'],
     'hands': [['CARE'], ['WATER'], ['SOUTH'], ['PASS'], ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 190 (day 7, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 191 (day 7, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 192 (day 8, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 7], ['SELL', 'WHEAT', 2], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['BUY_ANIMAL', 'COW', 2], ['BUY_SEED', 'WHEAT', 3]]},
    # Step 193 (day 8, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['EAST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'COW', 2], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 5], ['BUY_SEED', 'STRAWBERRY', 2], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 194 (day 8, hour 2).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['WEST'], ['PICKUP', 'WHEAT', 2], ['NORTH']],
     'market': []},
    # Step 195 (day 8, hour 3).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['NORTH'], ['NORTH'], ['HARVEST'], ['EAST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 196 (day 8, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 197 (day 8, hour 5).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WATER'], ['NORTH'], ['CARE'], ['BUILD_PASTURE'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 198 (day 8, hour 6).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['PLACE', 'COW'],
               ['WATER']],
     'market': []},
    # Step 199 (day 8, hour 7).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WATER'], ['WATER'], ['NORTH'], ['FEED', 'WHEAT'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 200 (day 8, hour 8).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['EAST'], ['FEED', 'WHEAT'], ['CARE'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 201 (day 8, hour 9).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['CARE'], ['EAST'], ['WATER']],
     'market': []},
    # Step 202 (day 8, hour 10).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 203 (day 8, hour 11).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WATER'], ['SOUTH'], ['EAST'], ['BUILD_PASTURE'], ['WATER']],
     'market': []},
    # Step 204 (day 8, hour 12).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['SOUTH'], ['NORTH'], ['PLACE', 'COW'], ['HARVEST']],
     'market': []},
    # Step 205 (day 8, hour 13).
    {'farmer': ['WATER'],
     'hands': [['EAST'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 206 (day 8, hour 14).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['NORTH'], ['PLANT', 'STRAWBERRY'], ['CARE'], ['CARE'], ['WATER']],
     'market': []},
    # Step 207 (day 8, hour 15).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 208 (day 8, hour 16).
    {'farmer': ['SOUTH'],
     'hands': [['FEED', 'WHEAT'], ['HARVEST'], ['EAST'], ['WEST'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': []},
    # Step 209 (day 8, hour 17).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['PLANT', 'WHEAT'], ['PLANT', 'STRAWBERRY'], ['WEST'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 210 (day 8, hour 18).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['SOUTH'], ['EAST'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 211 (day 8, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['EAST'], ['NORTH'], ['SOUTH'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': []},
    # Step 212 (day 8, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PLANT', 'WHEAT'], ['FEED', 'WHEAT'], ['WATER'], ['PASS']],
     'market': []},
    # Step 213 (day 8, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['HARVEST'], ['WATER'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 214 (day 8, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PLANT', 'WHEAT'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 215 (day 8, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 216 (day 9, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 10], ['SELL', 'WHEAT', 13], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 217 (day 9, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WEST'], ['NORTH'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['NORTH'], ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 218 (day 9, hour 2).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['HARVEST'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 219 (day 9, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'],
               ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 220 (day 9, hour 4).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['NORTH'], ['CARE'], ['CARE'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 221 (day 9, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['NORTH']],
     'market': []},
    # Step 222 (day 9, hour 6).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'], ['WATER']],
     'market': []},
    # Step 223 (day 9, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WATER'], ['WATER'], ['HARVEST'], ['FEED', 'WHEAT'], ['WATER'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 224 (day 9, hour 8).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['EAST'], ['FEED', 'WHEAT'], ['CARE'], ['WEST'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 225 (day 9, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WATER'], ['SOUTH'], ['CARE'], ['COLLECT_FERTILIZER'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 226 (day 9, hour 10).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['EAST'], ['WEST'], ['WATER']],
     'market': []},
    # Step 227 (day 9, hour 11).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['NORTH'], ['SOUTH'], ['WATER'], ['EAST']],
     'market': []},
    # Step 228 (day 9, hour 12).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['EAST'], ['EAST'], ['HARVEST'], ['FEED', 'WHEAT'], ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 229 (day 9, hour 13).
    {'farmer': ['WATER'],
     'hands': [['EAST'], ['SOUTH'], ['EAST'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'], ['EAST']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 230 (day 9, hour 14).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['SOUTH'], ['NORTH'], ['CARE'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 231 (day 9, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['COLLECT_FERTILIZER'], ['EAST'], ['SOUTH'], ['SOUTH']],
     'market': []},
    # Step 232 (day 9, hour 16).
    {'farmer': ['WATER'],
     'hands': [['WATER'], ['WEST'], ['SOUTH'], ['WEST'], ['SOUTH'], ['WATER'], ['WATER']],
     'market': []},
    # Step 233 (day 9, hour 17).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['HARVEST'], ['SOUTH']],
     'market': []},
    # Step 234 (day 9, hour 18).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['HARVEST'], ['CARE'], ['PLANT', 'WHEAT'], ['PASS']],
     'market': []},
    # Step 235 (day 9, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['PASS']],
     'market': []},
    # Step 236 (day 9, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['CARE'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 237 (day 9, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 238 (day 9, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 239 (day 9, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 240 (day 10, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 16], ['SELL', 'WHEAT', 2], ['BUY_LAND'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 241 (day 10, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_SEED', 'MELON', 9], ['BUY_SEED', 'STRAWBERRY', 7]]},
    # Step 242 (day 10, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['SOUTH'], ['WEST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['NORTH'], ['EAST'], ['WEST'], ['WEST'],
               ['NORTH'], ['NORTH'], ['WEST']],
     'market': [['BUY_SEED', 'MELON', 1]]},
    # Step 243 (day 10, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['PLANT', 'STRAWBERRY'], ['WEST'], ['NORTH'], ['NORTH'], ['WEST'],
               ['WEST'], ['NORTH'], ['EAST'], ['NORTH'], ['WEST'], ['NORTH'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 244 (day 10, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WATER'], ['WEST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'], ['WEST'],
               ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 245 (day 10, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['SOUTH'], ['WEST'], ['CARE'], ['CARE'], ['SOUTH'], ['WEST'],
               ['WATER'], ['WATER'], ['NORTH'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 246 (day 10, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['PLANT', 'STRAWBERRY'], ['WEST'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['PLANT', 'STRAWBERRY'], ['NORTH'], ['HARVEST'], ['EAST'],
               ['NORTH'], ['WEST'], ['WATER'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 247 (day 10, hour 7).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['SOUTH'], ['NORTH'], ['NORTH'], ['WATER'], ['NORTH'],
               ['PLANT', 'MELON'], ['WATER'], ['WATER'], ['NORTH'], ['WEST'], ['EAST'], ['NORTH']],
     'market': []},
    # Step 248 (day 10, hour 8).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WEST'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WEST'], ['NORTH'],
               ['WATER'], ['EAST'], ['HARVEST'], ['NORTH'], ['WATER'], ['EAST'], ['WATER']],
     'market': []},
    # Step 249 (day 10, hour 9).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['PLANT', 'STRAWBERRY'], ['PLANT', 'STRAWBERRY'], ['CARE'],
               ['CARE'], ['PLANT', 'STRAWBERRY'], ['NORTH'], ['SOUTH'], ['WATER'], ['PLANT', 'MELON'],
               ['NORTH'], ['WEST'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 250 (day 10, hour 10).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['WATER'], ['SOUTH'], ['SOUTH'], ['WATER'], ['NORTH'], ['WATER'], ['EAST'],
               ['PLANT', 'MELON']],
     'market': []},
    # Step 251 (day 10, hour 11).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['SOUTH'], ['SOUTH'], ['WEST'], ['EAST'], ['EAST'], ['HARVEST'], ['SOUTH'],
               ['WATER'], ['EAST'], ['WATER'], ['WEST'], ['WATER'], ['WATER']],
     'market': []},
    # Step 252 (day 10, hour 12).
    {'farmer': ['PLANT', 'MELON'],
     'hands': [['SOUTH'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['SOUTH'], ['SOUTH'], ['SOUTH'],
               ['PLANT', 'MELON'], ['DROP'], ['WEST'], ['SOUTH'], ['HARVEST'], ['WATER'], ['WEST'],
               ['EAST']],
     'market': [['SELL', 'MELON', 6], ['BUY_SEED', 'MELON', 4], ['BUY_SEED', 'STRAWBERRY', 9],
                ['BUY_PRODUCT', 'WHEAT', 4]]},
    # Step 253 (day 10, hour 13).
    {'farmer': ['WATER'],
     'hands': [['PLANT', 'MELON'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['FEED', 'WHEAT'],
               ['FEED', 'WHEAT'], ['PLANT', 'STRAWBERRY'], ['WATER'], ['EAST'], ['WATER'], ['SOUTH'],
               ['PLANT', 'MELON'], ['WEST'], ['SOUTH'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 4]]},
    # Step 254 (day 10, hour 14).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['EAST'], ['WATER'], ['CARE'], ['CARE'], ['WATER'], ['EAST'], ['EAST'],
               ['WEST'], ['SOUTH'], ['WATER'], ['WATER'], ['SOUTH'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 255 (day 10, hour 15).
    {'farmer': ['PLANT', 'MELON'],
     'hands': [['WEST'], ['PLANT', 'STRAWBERRY'], ['EAST'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'], ['NORTH'], ['WEST'], ['DROP'], ['EAST'],
               ['SOUTH'], ['SOUTH'], ['SOUTH']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 256 (day 10, hour 16).
    {'farmer': ['WATER'],
     'hands': [['PLANT', 'MELON'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['SOUTH'], ['EAST'],
               ['PLANT', 'STRAWBERRY'], ['EAST'], ['NORTH'], ['NORTH'], ['WEST'], ['EAST'], ['SOUTH'],
               ['SOUTH'], ['SOUTH']],
     'market': []},
    # Step 257 (day 10, hour 17).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['SOUTH'], ['WATER'], ['HARVEST'], ['SOUTH'], ['WATER'], ['SOUTH'], ['NORTH'],
               ['NORTH'], ['CARE'], ['EAST'], ['WATER'], ['CARE'], ['DROP']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 258 (day 10, hour 18).
    {'farmer': ['PLANT', 'MELON'],
     'hands': [['SOUTH'], ['PLANT', 'STRAWBERRY'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['EAST'], ['SOUTH'], ['NORTH'], ['NORTH'], ['COLLECT_FERTILIZER'], ['EAST'], ['PASS'],
               ['COLLECT_FERTILIZER'], ['PASS']],
     'market': []},
    # Step 259 (day 10, hour 19).
    {'farmer': ['WATER'],
     'hands': [['PLANT', 'MELON'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['PASS'],
               ['PLANT', 'STRAWBERRY'], ['SOUTH'], ['WATER'], ['NORTH'], ['PASS'], ['SOUTH'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 260 (day 10, hour 20).
    {'farmer': ['SOUTH'],
     'hands': [['WATER'], ['PASS'], ['WATER'], ['PASS'], ['PASS'], ['WATER'], ['DROP'], ['PASS'],
               ['PASS'], ['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 261 (day 10, hour 21).
    {'farmer': ['PLANT', 'MELON'],
     'hands': [['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 262 (day 10, hour 22).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['PASS'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['DROP'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'MELON', 6], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 263 (day 10, hour 23).
    {'farmer': ['EAST'],
     'hands': [['PASS'], ['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 264 (day 11, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 265 (day 11, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': [['HIRE']]},
    # Step 266 (day 11, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WEST'], ['EAST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['NORTH'], ['WEST'], ['NORTH'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 3]]},
    # Step 267 (day 11, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'], ['NORTH'],
               ['NORTH'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 268 (day 11, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['SOUTH'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WEST'],
               ['NORTH'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 269 (day 11, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['PLANT', 'MELON'], ['NORTH'], ['CARE'], ['CARE'], ['WEST'],
               ['NORTH'], ['WATER'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 270 (day 11, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['NORTH'], ['NORTH'], ['WEST'], ['EAST'], ['WATER']],
     'market': []},
    # Step 271 (day 11, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['EAST'], ['NORTH'], ['NORTH'], ['NORTH'], ['WATER'],
               ['WATER'], ['WATER'], ['WEST']],
     'market': []},
    # Step 272 (day 11, hour 8).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['PLANT', 'MELON'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'],
               ['HARVEST'], ['WEST'], ['EAST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 273 (day 11, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['CARE'], ['CARE'], ['WATER'],
               ['PLANT', 'WHEAT'], ['WATER'], ['WATER'], ['WEST']],
     'market': []},
    # Step 274 (day 11, hour 10).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WEST'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['HARVEST'], ['WATER'], ['WEST'], ['EAST'], ['WATER']],
     'market': []},
    # Step 275 (day 11, hour 11).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['EAST'], ['HARVEST'], ['WEST'], ['EAST'], ['PLANT', 'WHEAT'], ['EAST'],
               ['SOUTH'], ['WATER'], ['SOUTH']],
     'market': []},
    # Step 276 (day 11, hour 12).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['EAST'], ['PLANT', 'WHEAT'], ['SOUTH'], ['SOUTH'], ['WATER'], ['EAST'],
               ['SOUTH'], ['EAST'], ['WATER']],
     'market': []},
    # Step 277 (day 11, hour 13).
    {'farmer': ['EAST'],
     'hands': [['EAST'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'],
               ['SOUTH'], ['EAST'], ['WATER'], ['EAST']],
     'market': []},
    # Step 278 (day 11, hour 14).
    {'farmer': ['EAST'],
     'hands': [['WATER'], ['NORTH'], ['EAST'], ['CARE'], ['CARE'], ['NORTH'], ['SOUTH'], ['EAST'],
               ['NORTH'], ['EAST']],
     'market': []},
    # Step 279 (day 11, hour 15).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['COLLECT_FERTILIZER'], ['WATER'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['SOUTH'], ['EAST'], ['WATER'], ['EAST']],
     'market': []},
    # Step 280 (day 11, hour 16).
    {'farmer': ['CARE'],
     'hands': [['WATER'], ['EAST'], ['HARVEST'], ['WEST'], ['EAST'], ['EAST'], ['WATER'], ['NORTH'],
               ['SOUTH'], ['PASS']],
     'market': []},
    # Step 281 (day 11, hour 17).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['EAST'], ['PLANT', 'WHEAT'], ['SOUTH'], ['SOUTH'], ['WATER'], ['EAST'],
               ['NORTH'], ['SOUTH'], ['PASS']],
     'market': []},
    # Step 282 (day 11, hour 18).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['EAST'],
               ['WATER'], ['NORTH'], ['WATER'], ['PASS']],
     'market': []},
    # Step 283 (day 11, hour 19).
    {'farmer': ['PASS'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['EAST'], ['PASS'], ['CARE'], ['WATER'], ['EAST'],
               ['NORTH'], ['PASS'], ['PASS']],
     'market': []},
    # Step 284 (day 11, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['NORTH'], ['SOUTH'], ['PASS'], ['PASS'], ['EAST'], ['WATER'], ['WATER'],
               ['PASS'], ['PASS']],
     'market': []},
    # Step 285 (day 11, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['EAST'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': []},
    # Step 286 (day 11, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WATER'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': []},
    # Step 287 (day 11, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': []},
    # Step 288 (day 12, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 12], ['SELL', 'WHEAT', 10], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 289 (day 12, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['BUY_ANIMAL', 'COW', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 290 (day 12, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['EAST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['PICKUP', 'FERTILIZER', 1], ['WEST'],
               ['PICKUP', 'FERTILIZER', 2], ['EAST'], ['WEST'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 8]]},
    # Step 291 (day 12, hour 3).
    {'farmer': ['HARVEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['EAST'], ['NORTH'], ['NORTH'], ['WEST'], ['WEST'],
               ['NORTH'], ['EAST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 292 (day 12, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WATER'], ['NORTH'], ['HARVEST'], ['FEED', 'WHEAT'], ['NORTH'], ['WEST'],
               ['NORTH'], ['EAST'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 293 (day 12, hour 5).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['CARE'], ['NORTH'],
               ['WEST'], ['NORTH'], ['WATER'], ['WATER'], ['NORTH']],
     'market': [['BUY_SEED', 'STRAWBERRY', 1], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 294 (day 12, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['CARE'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WEST'],
               ['WATER'], ['EAST'], ['EAST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 295 (day 12, hour 7).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['NORTH'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WEST'], ['WATER'], ['SOUTH'], ['NORTH']],
     'market': []},
    # Step 296 (day 12, hour 8).
    {'farmer': ['HARVEST'],
     'hands': [['CARE'], ['SOUTH'], ['PLANT', 'WHEAT'], ['NORTH'], ['FEED', 'WHEAT'], ['WATER'],
               ['SOUTH'], ['WATER'], ['WEST'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 297 (day 12, hour 9).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['HARVEST'], ['CARE'], ['WEST'], ['WATER'],
               ['WEST'], ['WEST'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 298 (day 12, hour 10).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['EAST'], ['EAST'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['SOUTH'], ['WATER'], ['WEST'], ['EAST'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 299 (day 12, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['WATER'], ['WATER'], ['CARE'], ['EAST'], ['NORTH'], ['WATER'], ['WEST'],
               ['NORTH'], ['WATER'], ['WATER']],
     'market': []},
    # Step 300 (day 12, hour 12).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['SOUTH'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['NORTH'], ['EAST'],
               ['WATER'], ['NORTH'], ['SOUTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 301 (day 12, hour 13).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['WEST'], ['WATER'], ['PLANT', 'WHEAT'], ['WEST'], ['FEED', 'WHEAT'], ['WATER'],
               ['WATER'], ['WEST'], ['NORTH'], ['WATER'], ['WATER']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 302 (day 12, hour 14).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['SOUTH'], ['WATER'], ['SOUTH'], ['CARE'], ['HARVEST'], ['SOUTH'], ['WATER'],
               ['NORTH'], ['WEST'], ['HARVEST']],
     'market': []},
    # Step 303 (day 12, hour 15).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['WATER'], ['EAST'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['PLANT', 'WHEAT'],
               ['WATER'], ['EAST'], ['WATER'], ['WATER'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 304 (day 12, hour 16).
    {'farmer': ['SOUTH'],
     'hands': [['NORTH'], ['SOUTH'], ['WATER'], ['FEED', 'WHEAT'], ['EAST'], ['WATER'], ['WEST'],
               ['SOUTH'], ['PASS'], ['EAST'], ['WATER']],
     'market': []},
    # Step 305 (day 12, hour 17).
    {'farmer': ['SOUTH'],
     'hands': [['WATER'], ['WATER'], ['HARVEST'], ['CARE'], ['SOUTH'], ['WEST'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['PASS'], ['EAST'], ['WEST']],
     'market': []},
    # Step 306 (day 12, hour 18).
    {'farmer': ['SOUTH'],
     'hands': [['PASS'], ['WEST'], ['PLANT', 'WHEAT'], ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'],
               ['WATER'], ['SOUTH'], ['WATER'], ['PASS'], ['WEST'], ['WATER']],
     'market': []},
    # Step 307 (day 12, hour 19).
    {'farmer': ['SOUTH'],
     'hands': [['PASS'], ['WATER'], ['WATER'], ['PASS'], ['CARE'], ['HARVEST'], ['WATER'], ['EAST'],
               ['PASS'], ['SOUTH'], ['HARVEST']],
     'market': []},
    # Step 308 (day 12, hour 20).
    {'farmer': ['SOUTH'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['EAST'], ['COLLECT_FERTILIZER'], ['PLANT', 'WHEAT'],
               ['EAST'], ['FERTILIZE', 'FERTILIZER'], ['PASS'], ['PASS'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 309 (day 12, hour 21).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['SOUTH'], ['PASS'], ['WATER'], ['WATER'], ['WATER'],
               ['PASS'], ['PASS'], ['WATER']],
     'market': []},
    # Step 310 (day 12, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['DROP'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': [['SELL', 'WOOL', 12]]},
    # Step 311 (day 12, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': []},
    # Step 312 (day 13, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WHEAT', 25], ['SELL', 'FERTILIZER', 9], ['SELL', 'WOOL', 4],
                ['SELL', 'MILK', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 313 (day 13, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 314 (day 13, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WEST'], ['NORTH'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['EAST'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 315 (day 13, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH'], ['NORTH'], ['NORTH'],
               ['WEST']],
     'market': []},
    # Step 316 (day 13, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['SOUTH'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'],
               ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 317 (day 13, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['CARE'], ['CARE'], ['NORTH'], ['NORTH'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 318 (day 13, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WEST'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['HARVEST'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 319 (day 13, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'], ['WATER'],
               ['WATER']],
     'market': []},
    # Step 320 (day 13, hour 8).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WEST'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['HARVEST'],
               ['EAST'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 321 (day 13, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['EAST'], ['CARE'], ['CARE'], ['EAST'], ['WATER'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 322 (day 13, hour 10).
    {'farmer': ['EAST'],
     'hands': [['EAST'], ['NORTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['EAST'],
               ['NORTH'], ['WEST']],
     'market': []},
    # Step 323 (day 13, hour 11).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['NORTH'], ['SOUTH'], ['WEST'], ['EAST'], ['EAST'], ['WATER'], ['WATER']],
     'market': []},
    # Step 324 (day 13, hour 12).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['NORTH'], ['WATER'], ['SOUTH'], ['SOUTH'], ['EAST'], ['EAST'], ['NORTH']],
     'market': []},
    # Step 325 (day 13, hour 13).
    {'farmer': ['EAST'],
     'hands': [['WATER'], ['WATER'], ['EAST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['EAST'],
               ['WATER'], ['NORTH']],
     'market': []},
    # Step 326 (day 13, hour 14).
    {'farmer': ['EAST'],
     'hands': [['EAST'], ['EAST'], ['EAST'], ['CARE'], ['CARE'], ['SOUTH'], ['EAST'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 327 (day 13, hour 15).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['EAST'], ['EAST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['SOUTH'],
               ['WATER'], ['HARVEST']],
     'market': []},
    # Step 328 (day 13, hour 16).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['SOUTH'], ['WATER'], ['WEST'], ['EAST'], ['CARE'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 329 (day 13, hour 17).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['SOUTH'], ['PASS'], ['SOUTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['SOUTH']],
     'market': []},
    # Step 330 (day 13, hour 18).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['CARE'], ['PASS'], ['HARVEST'], ['FEED', 'WHEAT'], ['PASS'], ['PASS'],
               ['WATER']],
     'market': []},
    # Step 331 (day 13, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['FEED', 'WHEAT'], ['PASS'], ['PASS'],
               ['PASS'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 332 (day 13, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 333 (day 13, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WATER']],
     'market': []},
    # Step 334 (day 13, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 335 (day 13, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 336 (day 14, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 12], ['SELL', 'STRAWBERRY', 6],
                ['SELL', 'WHEAT', 4], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 337 (day 14, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 338 (day 14, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['WEST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['PICKUP', 'FERTILIZER', 2], ['WEST'],
               ['PICKUP', 'FERTILIZER', 2], ['EAST'], ['WEST']],
     'market': []},
    # Step 339 (day 14, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['WEST'], ['NORTH'], ['HARVEST'], ['WEST'], ['WEST'], ['NORTH'],
               ['EAST'], ['WEST']],
     'market': []},
    # Step 340 (day 14, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['WEST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WEST'],
               ['NORTH'], ['NORTH'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 341 (day 14, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WEST'], ['WEST'], ['CARE'], ['CARE'], ['WEST'], ['NORTH'], ['NORTH'],
               ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 342 (day 14, hour 6).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['NORTH'], ['NORTH'], ['WATER'], ['EAST'], ['EAST']],
     'market': []},
    # Step 343 (day 14, hour 7).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['EAST'], ['WATER'], ['NORTH'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'],
               ['NORTH'], ['NORTH'], ['WATER'], ['SOUTH']],
     'market': []},
    # Step 344 (day 14, hour 8).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['SOUTH'], ['SOUTH'], ['SOUTH'], ['FEED', 'WHEAT'], ['NORTH'], ['WATER'], ['NORTH'],
               ['WATER'], ['EAST'], ['SOUTH']],
     'market': []},
    # Step 345 (day 14, hour 9).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['WATER'], ['CARE'], ['FEED', 'WHEAT'], ['WEST'],
               ['WATER'], ['WEST'], ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 346 (day 14, hour 10).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['EAST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['CARE'],
               ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['SOUTH'], ['SOUTH'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 347 (day 14, hour 11).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['WATER'], ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 348 (day 14, hour 12).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['SOUTH'], ['EAST'], ['SOUTH'], ['EAST'], ['NORTH'], ['WEST'], ['SOUTH'],
               ['WEST'], ['SOUTH']],
     'market': []},
    # Step 349 (day 14, hour 13).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['FEED', 'WHEAT'], ['SOUTH'], ['NORTH'], ['WATER'],
               ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 350 (day 14, hour 14).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['SOUTH'], ['SOUTH'], ['CARE'], ['FEED', 'WHEAT'], ['WATER'], ['WEST'],
               ['WEST'], ['WEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 351 (day 14, hour 15).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['CARE'], ['NORTH'], ['WATER'],
               ['SOUTH'], ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 352 (day 14, hour 16).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['SOUTH'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['WATER'], ['SOUTH'],
               ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['EAST']],
     'market': []},
    # Step 353 (day 14, hour 17).
    {'farmer': ['WATER'],
     'hands': [['WATER'], ['WATER'], ['WATER'], ['HARVEST'], ['EAST'], ['EAST'], ['EAST'], ['WATER'],
               ['NORTH'], ['EAST']],
     'market': []},
    # Step 354 (day 14, hour 18).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['WEST'], ['SOUTH'], ['FEED', 'WHEAT'], ['SOUTH'], ['PASS'], ['SOUTH'],
               ['WEST'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 355 (day 14, hour 19).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['CARE'], ['FEED', 'WHEAT'], ['PASS'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 356 (day 14, hour 20).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['WEST'], ['EAST'], ['COLLECT_FERTILIZER'], ['CARE'], ['PASS'], ['PASS'],
               ['WATER'], ['WATER'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 357 (day 14, hour 21).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 358 (day 14, hour 22).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 359 (day 14, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 360 (day 15, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 9], ['SELL', 'FERTILIZER', 8], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 361 (day 15, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 362 (day 15, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'WHEAT', 2], ['WEST'], ['NORTH'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['NORTH'], ['WEST'], ['PICKUP', 'FERTILIZER', 1]],
     'market': [['BUY_SEED', 'WHEAT', 4]]},
    # Step 363 (day 15, hour 3).
    {'farmer': ['HARVEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'], ['NORTH'],
               ['NORTH'], ['EAST']],
     'market': []},
    # Step 364 (day 15, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['SOUTH'], ['NORTH'], ['NORTH'], ['HARVEST'], ['WEST'], ['NORTH'], ['NORTH'],
               ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 365 (day 15, hour 5).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['HARVEST'], ['FEED', 'WHEAT'], ['WEST'],
               ['NORTH'], ['HARVEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 366 (day 15, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WEST'], ['WATER'], ['FEED', 'WHEAT'], ['CARE'], ['NORTH'], ['NORTH'],
               ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 367 (day 15, hour 7).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['WATER'], ['EAST'], ['CARE'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'],
               ['SOUTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 368 (day 15, hour 8).
    {'farmer': ['HARVEST'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['WATER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'],
               ['HARVEST'], ['HARVEST'], ['NORTH']],
     'market': []},
    # Step 369 (day 15, hour 9).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['EAST'], ['EAST'], ['WEST'], ['HARVEST'], ['NORTH'], ['PLANT', 'WHEAT'],
               ['WEST'], ['FERTILIZE', 'FERTILIZER']],
     'market': []},
    # Step 370 (day 15, hour 10).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['WATER'],
               ['WATER'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 371 (day 15, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['NORTH'], ['EAST'], ['HARVEST'], ['CARE'], ['HARVEST'], ['EAST'],
               ['HARVEST'], ['EAST']],
     'market': []},
    # Step 372 (day 15, hour 12).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'],
               ['PLANT', 'WHEAT'], ['EAST'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 373 (day 15, hour 13).
    {'farmer': ['SOUTH'],
     'hands': [['WATER'], ['NORTH'], ['EAST'], ['CARE'], ['EAST'], ['WATER'], ['SOUTH'], ['NORTH'],
               ['HARVEST']],
     'market': []},
    # Step 374 (day 15, hour 14).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['NORTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['WEST'], ['EAST'], ['SOUTH'],
               ['NORTH'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 375 (day 15, hour 15).
    {'farmer': ['CARE'],
     'hands': [['WATER'], ['NORTH'], ['NORTH'], ['WEST'], ['SOUTH'], ['HARVEST'], ['SOUTH'], ['NORTH'],
               ['WATER']],
     'market': []},
    # Step 376 (day 15, hour 16).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['NORTH'], ['WATER'], ['SOUTH'], ['SOUTH'], ['EAST'], ['WATER'], ['WATER'],
               ['EAST']],
     'market': []},
    # Step 377 (day 15, hour 17).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['WATER'], ['SOUTH'], ['HARVEST'], ['DROP'], ['HARVEST'], ['EAST'], ['WEST'],
               ['WATER']],
     'market': [['SELL', 'MILK', 12], ['SELL', 'FERTILIZER', 1]]},
    # Step 378 (day 15, hour 18).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['WEST'], ['PASS'], ['FEED', 'WHEAT'], ['PICKUP', 'WHEAT', 2], ['WEST'],
               ['WATER'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 379 (day 15, hour 19).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['WATER'], ['PASS'], ['COLLECT_FERTILIZER'], ['EAST'], ['EAST'], ['EAST'],
               ['EAST'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 380 (day 15, hour 20).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['PASS'], ['PASS'], ['WEST'], ['NORTH'], ['EAST'], ['WATER'], ['EAST'],
               ['WATER']],
     'market': []},
    # Step 381 (day 15, hour 21).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['PASS'], ['PASS'], ['NORTH'], ['FEED', 'WHEAT'], ['EAST'], ['PASS'],
               ['WATER'], ['PASS']],
     'market': []},
    # Step 382 (day 15, hour 22).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['PASS'], ['PASS'], ['HARVEST'], ['CARE'], ['SOUTH'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': []},
    # Step 383 (day 15, hour 23).
    {'farmer': ['CARE'],
     'hands': [['HARVEST'], ['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': []},
    # Step 384 (day 16, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 16], ['SELL', 'MILK', 9], ['SELL', 'STRAWBERRY', 12],
                ['SELL', 'FERTILIZER', 9], ['SELL', 'WHEAT', 10], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE']]},
    # Step 385 (day 16, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['BUY_SEED', 'WHEAT', 3]]},
    # Step 386 (day 16, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['NORTH'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['EAST'], ['PICKUP', 'FERTILIZER', 3],
               ['PICKUP', 'FERTILIZER', 4], ['WEST'], ['WEST'], ['NORTH'], ['PICKUP', 'FERTILIZER', 5],
               ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 5], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 387 (day 16, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['PICKUP', 'FERTILIZER', 1], ['NORTH'], ['HARVEST'], ['WEST'],
               ['EAST'], ['WEST'], ['EAST'], ['WEST'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 388 (day 16, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['EAST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WEST'],
               ['NORTH'], ['NORTH'], ['EAST'], ['WEST'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 389 (day 16, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WEST'], ['NORTH'], ['CARE'], ['CARE'], ['WATER'], ['NORTH'], ['NORTH'],
               ['EAST'], ['WEST'], ['NORTH'], ['WATER'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 390 (day 16, hour 6).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['WATER'],
               ['WATER'], ['NORTH'], ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['NORTH']],
     'market': []},
    # Step 391 (day 16, hour 7).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['EAST'], ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['EAST'], ['SOUTH'],
               ['HARVEST'], ['WATER'], ['EAST'], ['SOUTH'], ['NORTH'], ['WATER'], ['WATER'],
               ['WATER']],
     'market': []},
    # Step 392 (day 16, hour 8).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['PLANT', 'WHEAT'], ['WEST'], ['WATER'], ['WATER'], ['NORTH'], ['WEST'], ['EAST'],
               ['HARVEST']],
     'market': []},
    # Step 393 (day 16, hour 9).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WATER'], ['EAST'], ['CARE'], ['CARE'], ['WATER'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['SOUTH'], ['NORTH'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 394 (day 16, hour 10).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['EAST'], ['EAST'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['EAST'], ['WEST'], ['WATER'], ['NORTH'], ['WATER'], ['WATER'],
               ['SOUTH'], ['WATER'], ['WATER']],
     'market': []},
    # Step 395 (day 16, hour 11).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['WATER'], ['SOUTH'], ['WEST'], ['NORTH'], ['WATER'], ['NORTH'], ['WEST'],
               ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['HARVEST'], ['SOUTH'], ['EAST'], ['WEST']],
     'market': []},
    # Step 396 (day 16, hour 12).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['SOUTH'], ['WATER'], ['SOUTH'], ['HARVEST'], ['SOUTH'], ['NORTH'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WATER'], ['PLANT', 'WHEAT'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER']],
     'market': []},
    # Step 397 (day 16, hour 13).
    {'farmer': ['WEST'],
     'hands': [['SOUTH'], ['WATER'], ['HARVEST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WATER'],
               ['NORTH'], ['WATER'], ['NORTH'], ['SOUTH'], ['WATER'], ['WEST'], ['WATER'],
               ['HARVEST']],
     'market': []},
    # Step 398 (day 16, hour 14).
    {'farmer': ['WATER'],
     'hands': [['SOUTH'], ['SOUTH'], ['PLANT', 'WHEAT'], ['CARE'], ['CARE'], ['WEST'], ['HARVEST'],
               ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WEST'], ['WATER'], ['SOUTH'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 399 (day 16, hour 15).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['EAST'], ['WATER'], ['WATER'], ['WEST'], ['WATER'], ['WEST'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER']],
     'market': []},
    # Step 400 (day 16, hour 16).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['SOUTH'], ['EAST'], ['SOUTH'], ['EAST'], ['EAST'], ['EAST'], ['WEST'],
               ['NORTH'], ['WATER'], ['HARVEST'], ['WATER'], ['WATER'], ['PASS']],
     'market': []},
    # Step 401 (day 16, hour 17).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['WATER'], ['WATER'], ['HARVEST'], ['SOUTH'], ['EAST'], ['SOUTH'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['PLANT', 'WHEAT'], ['SOUTH'], ['EAST'],
               ['PASS']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 402 (day 16, hour 18).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['WEST'], ['HARVEST'], ['FEED', 'WHEAT'], ['HARVEST'], ['WEST'], ['WATER'],
               ['SOUTH'], ['WATER'], ['WATER'], ['WATER'], ['HARVEST'], ['FERTILIZE', 'FERTILIZER'],
               ['PASS']],
     'market': []},
    # Step 403 (day 16, hour 19).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['WATER'], ['PLANT', 'WHEAT'], ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'],
               ['SOUTH'], ['PASS'], ['PASS'], ['WEST'], ['EAST'], ['WEST'], ['PASS'], ['WATER'],
               ['PASS']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 404 (day 16, hour 20).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['WATER'], ['PASS'], ['CARE'], ['PASS'], ['PASS'], ['PASS'],
               ['SOUTH'], ['WATER'], ['WATER'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 405 (day 16, hour 21).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'],
               ['PASS'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['HARVEST'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': []},
    # Step 406 (day 16, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PLANT', 'WHEAT'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 407 (day 16, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 408 (day 17, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 18], ['SELL', 'STRAWBERRY', 4], ['SELL', 'WHEAT', 25], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 409 (day 17, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 410 (day 17, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['NORTH'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['WEST']],
     'market': []},
    # Step 411 (day 17, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['PICKUP', 'FERTILIZER', 2], ['NORTH'], ['NORTH'], ['WEST'],
               ['WEST'], ['WEST']],
     'market': []},
    # Step 412 (day 17, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['EAST'], ['NORTH'], ['FEED', 'WHEAT'], ['HARVEST'], ['SOUTH'], ['WEST'],
               ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 413 (day 17, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['NORTH'], ['CARE'], ['FEED', 'WHEAT'], ['WATER'],
               ['WEST'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 414 (day 17, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['NORTH'], ['NORTH'], ['COLLECT_FERTILIZER'], ['CARE'], ['WEST'], ['WEST'],
               ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 415 (day 17, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['NORTH'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['NORTH'], ['EAST']],
     'market': []},
    # Step 416 (day 17, hour 8).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['HARVEST'], ['WATER'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['NORTH'],
               ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 417 (day 17, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['EAST'], ['EAST'], ['CARE'], ['HARVEST'], ['WATER'], ['NORTH'],
               ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 418 (day 17, hour 10).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['EAST'], ['WATER'], ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'], ['WEST'],
               ['WATER'], ['HARVEST']],
     'market': []},
    # Step 419 (day 17, hour 11).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['NORTH'], ['EAST'], ['WEST'], ['CARE'], ['WATER'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 420 (day 17, hour 12).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['NORTH'], ['WATER'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['WATER'],
               ['HARVEST']],
     'market': []},
    # Step 421 (day 17, hour 13).
    {'farmer': ['SOUTH'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['FEED', 'WHEAT'], ['EAST'], ['WATER'], ['EAST'],
               ['WEST']],
     'market': []},
    # Step 422 (day 17, hour 14).
    {'farmer': ['CARE'],
     'hands': [['HARVEST'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'], ['WATER'],
               ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 423 (day 17, hour 15).
    {'farmer': ['HARVEST'],
     'hands': [['EAST'], ['SOUTH'], ['SOUTH'], ['WEST'], ['FEED', 'WHEAT'], ['EAST'], ['EAST'],
               ['SOUTH']],
     'market': []},
    # Step 424 (day 17, hour 16).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['HARVEST'], ['SOUTH'], ['SOUTH'], ['SOUTH'], ['CARE'], ['NORTH'], ['WATER'],
               ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 425 (day 17, hour 17).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['SOUTH'], ['SOUTH'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['EAST'], ['WEST']],
     'market': []},
    # Step 426 (day 17, hour 18).
    {'farmer': ['HARVEST'],
     'hands': [['HARVEST'], ['SOUTH'], ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['EAST'], ['EAST'],
               ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 427 (day 17, hour 19).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['CARE'], ['WATER'], ['WEST'], ['SOUTH'], ['WATER'], ['EAST'], ['HARVEST']],
     'market': []},
    # Step 428 (day 17, hour 20).
    {'farmer': ['PASS'],
     'hands': [['HARVEST'], ['COLLECT_FERTILIZER'], ['EAST'], ['HARVEST'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['WATER'], ['PLANT', 'WHEAT']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 429 (day 17, hour 21).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['PASS'], ['PASS'], ['WATER'],
               ['PASS'], ['EAST']],
     'market': []},
    # Step 430 (day 17, hour 22).
    {'farmer': ['WEST'],
     'hands': [['HARVEST'], ['NORTH'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['EAST']],
     'market': []},
    # Step 431 (day 17, hour 23).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['HARVEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['EAST']],
     'market': []},
    # Step 432 (day 18, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 28], ['SELL', 'MILK', 9], ['SELL', 'FERTILIZER', 9],
                ['SELL', 'WHEAT', 4], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 433 (day 18, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_ANIMAL', 'COW', 1],
                ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 434 (day 18, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['EAST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['WEST'], ['PICKUP', 'FERTILIZER', 4], ['NORTH'],
               ['WEST'], ['EAST'], ['WEST']],
     'market': []},
    # Step 435 (day 18, hour 3).
    {'farmer': ['HARVEST'],
     'hands': [['NORTH'], ['WEST'], ['NORTH'], ['NORTH'], ['HARVEST'], ['WATER'], ['NORTH'], ['WEST'],
               ['NORTH'], ['WEST'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 436 (day 18, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['NORTH'], ['HARVEST'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['NORTH'], ['WEST'], ['NORTH'], ['SOUTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 437 (day 18, hour 5).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'], ['NORTH'],
               ['NORTH'], ['WATER'], ['SOUTH'], ['NORTH'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 438 (day 18, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['CARE'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['WATER'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 439 (day 18, hour 7).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WEST'], ['WATER'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['WATER'],
               ['WATER'], ['SOUTH'], ['WEST'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 440 (day 18, hour 8).
    {'farmer': ['HARVEST'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['EAST'], ['NORTH'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['WEST'], ['WEST'], ['WATER'], ['WATER'], ['HARVEST'], ['WEST']],
     'market': []},
    # Step 441 (day 18, hour 9).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WEST'], ['WATER'], ['HARVEST'], ['CARE'], ['WATER'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['WEST'], ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 442 (day 18, hour 10).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['EAST'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'],
               ['EAST'], ['WEST'], ['WATER'], ['WATER'], ['WATER'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 443 (day 18, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['EAST'], ['WATER'], ['CARE'], ['NORTH'], ['WATER'], ['WATER'], ['SOUTH'],
               ['SOUTH'], ['SOUTH'], ['EAST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 444 (day 18, hour 12).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['SOUTH'], ['EAST'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['SOUTH'], ['WEST'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WATER'], ['EAST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 5]]},
    # Step 445 (day 18, hour 13).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['WEST'], ['FEED', 'WHEAT'], ['WATER'], ['WATER'],
               ['WATER'], ['EAST'], ['EAST'], ['WATER'], ['EAST']],
     'market': [['SELL', 'WHEAT', 5]]},
    # Step 446 (day 18, hour 14).
    {'farmer': ['CARE'],
     'hands': [['WATER'], ['EAST'], ['NORTH'], ['SOUTH'], ['CARE'], ['WEST'], ['WEST'], ['WEST'],
               ['WATER'], ['WATER'], ['EAST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 447 (day 18, hour 15).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['WATER'], ['WATER'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['EAST'], ['WATER'], ['EAST']],
     'market': []},
    # Step 448 (day 18, hour 16).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['EAST'], ['HARVEST'], ['FEED', 'WHEAT'], ['EAST'], ['WEST'], ['SOUTH'],
               ['WATER'], ['WATER'], ['WATER'], ['SOUTH'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 449 (day 18, hour 17).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['WATER'], ['SOUTH'], ['CARE'], ['SOUTH'], ['WEST'], ['WATER'], ['NORTH'],
               ['SOUTH'], ['SOUTH'], ['SOUTH'], ['PASS']],
     'market': [['SELL', 'WHEAT', 1], ['SELL', 'WHEAT', 1]]},
    # Step 450 (day 18, hour 18).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['PASS'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['WEST'], ['PASS'],
               ['NORTH'], ['HARVEST'], ['WATER'], ['WATER'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 451 (day 18, hour 19).
    {'farmer': ['SOUTH'],
     'hands': [['WATER'], ['PASS'], ['WATER'], ['PASS'], ['FEED', 'WHEAT'], ['NORTH'], ['PASS'],
               ['NORTH'], ['WEST'], ['WEST'], ['HARVEST'], ['PASS']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 452 (day 18, hour 20).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['PASS'], ['HARVEST'], ['PASS'], ['CARE'], ['NORTH'], ['PASS'], ['PASS'],
               ['HARVEST'], ['WATER'], ['PASS'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 453 (day 18, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'], ['WEST'],
               ['WEST'], ['PASS'], ['PASS']],
     'market': [['SELL', 'WHEAT', 2]]},
    # Step 454 (day 18, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['PASS'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 455 (day 18, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['DROP'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'MILK', 9], ['SELL', 'WHEAT', 2]]},
    # Step 456 (day 19, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 16], ['SELL', 'STRAWBERRY', 12], ['SELL', 'MILK', 3],
                ['SELL', 'FERTILIZER', 8], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 457 (day 19, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 458 (day 19, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['NORTH'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['PICKUP', 'FERTILIZER', 6], ['NORTH'], ['WEST'],
               ['PICKUP', 'FERTILIZER', 1], ['PICKUP', 'FERTILIZER', 5], ['WEST'], ['WEST'],
               ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 4]]},
    # Step 459 (day 19, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['PICKUP', 'FERTILIZER', 5], ['NORTH'], ['NORTH'],
               ['SOUTH'], ['NORTH'], ['NORTH'], ['EAST'], ['WEST'], ['WEST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 460 (day 19, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WATER'], ['WEST'], ['FEED', 'WHEAT'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['NORTH'], ['EAST'], ['WEST'], ['WEST'],
               ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 461 (day 19, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['WEST'], ['CARE'], ['FEED', 'WHEAT'], ['WATER'],
               ['NORTH'], ['HARVEST'], ['EAST'], ['WEST'], ['WEST'], ['NORTH'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 462 (day 19, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'], ['CARE'], ['SOUTH'], ['NORTH'],
               ['DIG'], ['WATER'], ['WEST'], ['WEST'], ['HARVEST'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 463 (day 19, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['WEST'], ['WEST'], ['NORTH'], ['COLLECT_FERTILIZER'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['PLANT', 'WHEAT'], ['EAST'], ['SOUTH'],
               ['NORTH'], ['DIG'], ['HARVEST']],
     'market': []},
    # Step 464 (day 19, hour 8).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['NORTH'], ['WATER'],
               ['HARVEST'], ['WATER'], ['WATER'], ['SOUTH'], ['NORTH'], ['PLANT', 'WHEAT'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 465 (day 19, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WEST'], ['SOUTH'], ['CARE'], ['HARVEST'], ['WEST'], ['PLANT', 'WHEAT'],
               ['WEST'], ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 466 (day 19, hour 10).
    {'farmer': ['EAST'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['SOUTH'], ['WEST'], ['WATER'], ['NORTH'],
               ['WEST'], ['EAST']],
     'market': []},
    # Step 467 (day 19, hour 11).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['SOUTH'], ['SOUTH'], ['WEST'], ['CARE'], ['WATER'], ['EAST'], ['HARVEST'],
               ['WEST'], ['SOUTH'], ['NORTH'], ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 468 (day 19, hour 12).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['COLLECT_FERTILIZER'],
               ['SOUTH'], ['EAST'], ['WEST'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['WATER'],
               ['DIG'], ['SOUTH']],
     'market': []},
    # Step 469 (day 19, hour 13).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['EAST'], ['WATER'], ['FEED', 'WHEAT'], ['EAST'], ['FERTILIZE', 'FERTILIZER'],
               ['WATER'], ['SOUTH'], ['NORTH'], ['WATER'], ['EAST'], ['PLANT', 'WHEAT'], ['HARVEST']],
     'market': []},
    # Step 470 (day 19, hour 14).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['EAST'], ['EAST'], ['CARE'], ['SOUTH'], ['WATER'], ['HARVEST'], ['HARVEST'],
               ['NORTH'], ['EAST'], ['WATER'], ['WATER'], ['WEST']],
     'market': []},
    # Step 471 (day 19, hour 15).
    {'farmer': ['WATER'],
     'hands': [['EAST'], ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['FEED', 'WHEAT'], ['EAST'], ['PLANT', 'WHEAT'], ['WEST'], ['NORTH'],
               ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['WEST'], ['HARVEST']],
     'market': []},
    # Step 472 (day 19, hour 16).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['EAST'], ['WATER'], ['WEST'], ['CARE'], ['FERTILIZE', 'FERTILIZER'],
               ['WATER'], ['HARVEST'], ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WATER'], ['WATER'],
               ['WEST']],
     'market': []},
    # Step 473 (day 19, hour 17).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['SOUTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['WATER'], ['EAST'],
               ['NORTH'], ['WATER'], ['SOUTH'], ['EAST'], ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 474 (day 19, hour 18).
    {'farmer': ['WEST'],
     'hands': [['HARVEST'], ['SOUTH'], ['FERTILIZE', 'FERTILIZER'], ['HARVEST'], ['SOUTH'], ['SOUTH'],
               ['WATER'], ['NORTH'], ['EAST'], ['FERTILIZE', 'FERTILIZER'], ['WATER'],
               ['PLANT', 'WHEAT'], ['EAST']],
     'market': []},
    # Step 475 (day 19, hour 19).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['SOUTH'], ['WATER'], ['FEED', 'WHEAT'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER'], ['HARVEST'], ['NORTH'], ['EAST'], ['WATER'], ['EAST'],
               ['WATER'], ['PASS']],
     'market': []},
    # Step 476 (day 19, hour 20).
    {'farmer': ['WEST'],
     'hands': [['HARVEST'], ['SOUTH'], ['SOUTH'], ['CARE'], ['WEST'], ['WATER'], ['PLANT', 'WHEAT'],
               ['NORTH'], ['EAST'], ['WEST'], ['WATER'], ['EAST'], ['WEST']],
     'market': []},
    # Step 477 (day 19, hour 21).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['COLLECT_FERTILIZER'], ['DROP'],
               ['PASS'], ['WATER'], ['WATER'], ['PASS'], ['FERTILIZE', 'FERTILIZER'], ['PASS'],
               ['SOUTH'], ['SOUTH']],
     'market': [['SELL', 'MILK', 11]]},
    # Step 478 (day 19, hour 22).
    {'farmer': ['PASS'],
     'hands': [['HARVEST'], ['PASS'], ['WATER'], ['PASS'], ['EAST'], ['PASS'], ['EAST'], ['PASS'],
               ['PASS'], ['WATER'], ['PASS'], ['HARVEST'], ['SOUTH']],
     'market': []},
    # Step 479 (day 19, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['EAST'], ['PASS'], ['CARE'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER']],
     'market': []},
    # Step 480 (day 20, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 34], ['SELL', 'MILK', 3], ['SELL', 'WHEAT', 12], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 481 (day 20, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_SEED', 'WHEAT', 45], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 482 (day 20, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['WEST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['WEST'], ['PICKUP', 'FERTILIZER', 5],
               ['WEST'], ['WEST'], ['NORTH'], ['PICKUP', 'FERTILIZER', 5], ['WEST']],
     'market': []},
    # Step 483 (day 20, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['HARVEST'], ['WEST'], ['NORTH'], ['HARVEST'], ['WATER'], ['WEST'], ['WEST'],
               ['NORTH'], ['WEST'], ['WEST'], ['NORTH'], ['EAST'], ['SOUTH']],
     'market': []},
    # Step 484 (day 20, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['PLANT', 'WHEAT'], ['WEST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['HARVEST'], ['WEST'], ['NORTH'], ['NORTH'], ['WATER'], ['NORTH'], ['NORTH'], ['EAST'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 485 (day 20, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WATER'], ['WEST'], ['CARE'], ['CARE'], ['PLANT', 'WHEAT'], ['WEST'],
               ['WATER'], ['NORTH'], ['HARVEST'], ['NORTH'], ['WATER'], ['NORTH'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 486 (day 20, hour 6).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['DROP'], ['WATER'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['WEST'], ['WEST'], ['FERTILIZE', 'FERTILIZER'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['HARVEST'], ['NORTH'], ['PLANT', 'WHEAT']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 487 (day 20, hour 7).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WEST'], ['HARVEST'], ['NORTH'], ['EAST'], ['EAST'], ['WATER'], ['WATER'],
               ['WATER'], ['WATER'], ['NORTH'], ['PLANT', 'WHEAT'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 488 (day 20, hour 8).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['PLANT', 'WHEAT'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['DROP'], ['HARVEST'], ['SOUTH'], ['EAST'], ['EAST'], ['WATER'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['EAST']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 489 (day 20, hour 9).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['NORTH'], ['WATER'], ['CARE'], ['CARE'], ['WEST'], ['PLANT', 'WHEAT'],
               ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['HARVEST'], ['SOUTH'], ['WATER'],
               ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 4]]},
    # Step 490 (day 20, hour 10).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['EAST'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['WEST'], ['WATER'], ['WEST'], ['WATER'], ['DROP'],
               ['PLANT', 'WHEAT'], ['SOUTH'], ['EAST'], ['DROP']],
     'market': [['SELL', 'MELON', 12]]},
    # Step 491 (day 20, hour 11).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['NORTH'], ['EAST'], ['WEST'], ['NORTH'], ['WEST'], ['EAST'], ['WATER'],
               ['SOUTH'], ['WEST'], ['WATER'], ['SOUTH'], ['FERTILIZE', 'FERTILIZER'], ['EAST']],
     'market': []},
    # Step 492 (day 20, hour 12).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['NORTH'], ['EAST'], ['SOUTH'], ['HARVEST'], ['WEST'], ['EAST'], ['NORTH'],
               ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['EAST'], ['DROP'], ['WATER'], ['EAST']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 493 (day 20, hour 13).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['WATER'], ['DROP'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'], ['EAST'],
               ['NORTH'], ['WATER'], ['SOUTH'], ['SOUTH'], ['NORTH'], ['EAST'], ['NORTH']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 494 (day 20, hour 14).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['HARVEST'], ['SOUTH'], ['CARE'], ['CARE'], ['WATER'], ['EAST'], ['NORTH'],
               ['EAST'], ['WATER'], ['SOUTH'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 495 (day 20, hour 15).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['PLANT', 'WHEAT'], ['HARVEST'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['HARVEST'], ['DROP'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'],
               ['WEST'], ['SOUTH'], ['NORTH'], ['WATER'], ['NORTH']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 496 (day 20, hour 16).
    {'farmer': ['HARVEST'],
     'hands': [['NORTH'], ['WATER'], ['SOUTH'], ['SOUTH'], ['EAST'], ['PLANT', 'WHEAT'], ['EAST'],
               ['WATER'], ['WATER'], ['WATER'], ['DROP'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 497 (day 20, hour 17).
    {'farmer': ['PLANT', 'WHEAT'],
     'hands': [['WATER'], ['EAST'], ['HARVEST'], ['HARVEST'], ['SOUTH'], ['WATER'], ['EAST'],
               ['HARVEST'], ['EAST'], ['SOUTH'], ['WEST'], ['WATER'], ['FERTILIZE', 'FERTILIZER'],
               ['NORTH']],
     'market': []},
    # Step 498 (day 20, hour 18).
    {'farmer': ['WATER'],
     'hands': [['HARVEST'], ['EAST'], ['WEST'], ['FEED', 'WHEAT'], ['HARVEST'], ['EAST'], ['EAST'],
               ['PLANT', 'WHEAT'], ['FERTILIZE', 'FERTILIZER'], ['HARVEST'], ['NORTH'], ['HARVEST'],
               ['WATER'], ['HARVEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 499 (day 20, hour 19).
    {'farmer': ['EAST'],
     'hands': [['PLANT', 'WHEAT'], ['SOUTH'], ['HARVEST'], ['CARE'], ['WEST'], ['EAST'], ['NORTH'],
               ['WATER'], ['WATER'], ['WEST'], ['NORTH'], ['PLANT', 'WHEAT'], ['SOUTH'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 500 (day 20, hour 20).
    {'farmer': ['EAST'],
     'hands': [['WATER'], ['SOUTH'], ['WEST'], ['COLLECT_FERTILIZER'], ['WEST'], ['EAST'], ['NORTH'],
               ['EAST'], ['EAST'], ['HARVEST'], ['NORTH'], ['WATER'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 501 (day 20, hour 21).
    {'farmer': ['EAST'],
     'hands': [['EAST'], ['SOUTH'], ['HARVEST'], ['PASS'], ['DROP'], ['EAST'], ['WATER'], ['WATER'],
               ['WATER'], ['SOUTH'], ['NORTH'], ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['WEST']],
     'market': [['SELL', 'MILK', 9], ['SELL', 'WHEAT', 1]]},
    # Step 502 (day 20, hour 22).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['DROP'], ['SOUTH'], ['PASS'], ['EAST'], ['NORTH'], ['HARVEST'], ['HARVEST'],
               ['SOUTH'], ['HARVEST'], ['WATER'], ['WEST'], ['PASS'], ['WEST']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 503 (day 20, hour 23).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['PASS'], ['EAST'], ['PASS'], ['EAST'], ['DROP'], ['PLANT', 'WHEAT'], ['PASS'],
               ['WATER'], ['EAST'], ['HARVEST'], ['WEST'], ['PASS'], ['WATER']],
     'market': [['SELL', 'MELON', 6], ['BUY_SEED', 'WHEAT', 2]]},
    # Step 504 (day 21, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 16], ['SELL', 'MELON', 12], ['SELL', 'WHEAT', 20],
                ['SELL', 'MILK', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 505 (day 21, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_SEED', 'WHEAT', 2],
                ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 506 (day 21, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'COW', 1], ['PICKUP', 'FERTILIZER', 1], ['NORTH'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['WEST'], ['PICKUP', 'COW', 1],
               ['PICKUP', 'FERTILIZER', 2], ['WEST'], ['WEST'], ['WEST']],
     'market': []},
    # Step 507 (day 21, hour 3).
    {'farmer': ['HARVEST'],
     'hands': [['PICKUP', 'WHEAT', 3], ['SOUTH'], ['NORTH'], ['NORTH'], ['NORTH'], ['WATER'], ['WEST'],
               ['PICKUP', 'WHEAT', 1], ['EAST'], ['WEST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 508 (day 21, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['NORTH'], ['NORTH'], ['HARVEST'], ['SOUTH'], ['WEST'],
               ['WEST'], ['EAST'], ['SOUTH'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 509 (day 21, hour 5).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['SOUTH'], ['NORTH'], ['HARVEST'], ['FEED', 'WHEAT'], ['WATER'], ['SOUTH'],
               ['NORTH'], ['EAST'], ['WATER'], ['NORTH'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 510 (day 21, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['FEED', 'WHEAT'], ['CARE'], ['WEST'],
               ['SOUTH'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['HARVEST'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 511 (day 21, hour 7).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['HARVEST'], ['WATER'], ['CARE'], ['COLLECT_FERTILIZER'], ['WATER'], ['SOUTH'],
               ['NORTH'], ['WATER'], ['PLANT', 'WHEAT'], ['NORTH'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 2], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 512 (day 21, hour 8).
    {'farmer': ['HARVEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['EAST'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WEST'],
               ['WATER'], ['NORTH'], ['HARVEST'], ['WATER'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 513 (day 21, hour 9).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WATER'], ['WATER'], ['WEST'], ['HARVEST'], ['WATER'], ['HARVEST'],
               ['BUILD_PASTURE'], ['NORTH'], ['NORTH'], ['NORTH'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 514 (day 21, hour 10).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['HARVEST'], ['EAST'], ['SOUTH'], ['FEED', 'WHEAT'], ['WEST'],
               ['WEST'], ['PLACE', 'COW'], ['DIG'], ['NORTH'], ['DIG'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 515 (day 21, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['SOUTH'], ['WATER'], ['HARVEST'], ['CARE'], ['WATER'], ['WATER'],
               ['FEED', 'WHEAT'], ['PLANT', 'WHEAT'], ['NORTH'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 516 (day 21, hour 12).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['FEED', 'WHEAT'],
               ['COLLECT_FERTILIZER'], ['WEST'], ['HARVEST'], ['CARE'], ['WATER'], ['HARVEST'],
               ['WATER'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 517 (day 21, hour 13).
    {'farmer': ['SOUTH'],
     'hands': [['DIG'], ['WATER'], ['WATER'], ['CARE'], ['EAST'], ['WATER'], ['WEST'], ['EAST'],
               ['EAST'], ['DIG'], ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 518 (day 21, hour 14).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['BUILD_PASTURE'], ['EAST'], ['EAST'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'],
               ['WATER'], ['EAST'], ['SOUTH'], ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT'], ['HARVEST']],
     'market': []},
    # Step 519 (day 21, hour 15).
    {'farmer': ['CARE'],
     'hands': [['PLACE', 'COW'], ['WATER'], ['HARVEST'], ['WEST'], ['WEST'], ['NORTH'], ['SOUTH'],
               ['SOUTH'], ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WATER'], ['PLANT', 'WHEAT']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 520 (day 21, hour 16).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['FEED', 'WHEAT'], ['HARVEST'], ['SOUTH'], ['SOUTH'], ['SOUTH'], ['WATER'], ['WATER'],
               ['HARVEST'], ['WATER'], ['WEST'], ['WEST'], ['WATER']],
     'market': []},
    # Step 521 (day 21, hour 17).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WEST'], ['HARVEST'], ['HARVEST'], ['DROP'], ['HARVEST'], ['HARVEST'],
               ['EAST'], ['HARVEST'], ['SOUTH'], ['SOUTH'], ['EAST']],
     'market': [['SELL', 'MILK', 6]]},
    # Step 522 (day 21, hour 18).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['EAST'], ['WEST'], ['EAST'], ['PICKUP', 'WHEAT', 2], ['PLANT', 'WHEAT'],
               ['EAST'], ['HARVEST'], ['NORTH'], ['HARVEST'], ['SOUTH'], ['HARVEST']],
     'market': []},
    # Step 523 (day 21, hour 19).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['NORTH'], ['HARVEST'], ['EAST'], ['EAST'], ['WATER'], ['WATER'], ['EAST'],
               ['DIG'], ['EAST'], ['PASS'], ['DIG']],
     'market': []},
    # Step 524 (day 21, hour 20).
    {'farmer': ['PASS'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['SOUTH'], ['DROP'], ['NORTH'], ['PASS'], ['HARVEST'],
               ['HARVEST'], ['PLANT', 'WHEAT'], ['EAST'], ['PASS'], ['PLANT', 'WHEAT']],
     'market': [['SELL', 'WOOL', 8], ['SELL', 'MILK', 3]]},
    # Step 525 (day 21, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['NORTH'], ['WEST'], ['WEST'], ['FEED', 'WHEAT'], ['PASS'], ['EAST'],
               ['SOUTH'], ['WATER'], ['EAST'], ['PASS'], ['WATER']],
     'market': []},
    # Step 526 (day 21, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['NORTH'], ['WEST'], ['WEST'], ['EAST'], ['PASS'], ['WATER'], ['HARVEST'],
               ['PASS'], ['DROP'], ['PASS'], ['PASS']],
     'market': [['SELL', 'STRAWBERRY', 4], ['SELL', 'MELON', 6]]},
    # Step 527 (day 21, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['DROP'], ['WEST'], ['PASS'], ['SOUTH'], ['PASS'], ['HARVEST'], ['WEST'],
               ['PASS'], ['WEST'], ['PASS'], ['PASS']],
     'market': [['SELL', 'STRAWBERRY', 6]]},
    # Step 528 (day 22, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 30], ['SELL', 'WOOL', 8], ['SELL', 'FERTILIZER', 5],
                ['SELL', 'WHEAT', 1], ['SELL', 'MELON', 6], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE']]},
    # Step 529 (day 22, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 530 (day 22, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['EAST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['EAST'], ['NORTH'], ['NORTH'], ['WEST'], ['WEST']],
     'market': []},
    # Step 531 (day 22, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['NORTH'], ['WEST'], ['HARVEST'], ['HARVEST'], ['EAST'], ['NORTH'],
               ['NORTH'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 532 (day 22, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['NORTH'], ['HARVEST'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['EAST'], ['NORTH'], ['NORTH'], ['SOUTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 533 (day 22, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['CARE'], ['HARVEST'], ['NORTH'],
               ['WATER'], ['WATER'], ['SOUTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 534 (day 22, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['CARE'], ['COLLECT_FERTILIZER'],
               ['SOUTH'], ['HARVEST'], ['WEST'], ['EAST'], ['HARVEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 535 (day 22, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['WEST'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['NORTH'], ['HARVEST'],
               ['EAST'], ['SOUTH'], ['WATER'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 536 (day 22, hour 8).
    {'farmer': ['CARE'],
     'hands': [['SOUTH'], ['WATER'], ['EAST'], ['NORTH'], ['NORTH'], ['SOUTH'], ['HARVEST'], ['WATER'],
               ['EAST'], ['HARVEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 537 (day 22, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['HARVEST'], ['WEST'], ['WEST'], ['SOUTH'], ['WEST'], ['WEST']],
     'market': []},
    # Step 538 (day 22, hour 10).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WATER'], ['WATER'], ['CARE'], ['CARE'], ['WEST'], ['WEST'], ['WATER'],
               ['WATER'], ['HARVEST'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 539 (day 22, hour 11).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['NORTH'], ['WEST'], ['WEST'], ['WEST'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 540 (day 22, hour 12).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['EAST'], ['EAST'], ['NORTH'], ['WEST'], ['WATER'],
               ['NORTH'], ['HARVEST'], ['WEST']],
     'market': []},
    # Step 541 (day 22, hour 13).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['EAST'], ['EAST'], ['NORTH'], ['SOUTH'], ['NORTH'], ['NORTH'], ['WEST'],
               ['NORTH'], ['EAST'], ['WATER']],
     'market': []},
    # Step 542 (day 22, hour 14).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['EAST'], ['WATER'], ['FEED', 'WHEAT'], ['HARVEST'], ['WATER'], ['NORTH'],
               ['WATER'], ['HARVEST'], ['HARVEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 543 (day 22, hour 15).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['EAST'], ['NORTH'], ['CARE'], ['FEED', 'WHEAT'], ['SOUTH'], ['NORTH'],
               ['EAST'], ['DIG'], ['EAST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 544 (day 22, hour 16).
    {'farmer': ['EAST'],
     'hands': [['WATER'], ['SOUTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['CARE'], ['HARVEST'],
               ['NORTH'], ['SOUTH'], ['PLANT', 'WHEAT'], ['HARVEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 545 (day 22, hour 17).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['SOUTH'], ['SOUTH'], ['WEST'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'],
               ['SOUTH'], ['WATER'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 546 (day 22, hour 18).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['HARVEST'], ['SOUTH'], ['NORTH'], ['EAST'], ['NORTH'], ['WEST'], ['DIG'],
               ['EAST'], ['HARVEST'], ['NORTH']],
     'market': []},
    # Step 547 (day 22, hour 19).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['SOUTH'], ['HARVEST'], ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['WEST'],
               ['PLANT', 'WHEAT'], ['WATER'], ['EAST'], ['WATER']],
     'market': []},
    # Step 548 (day 22, hour 20).
    {'farmer': ['NORTH'],
     'hands': [['HARVEST'], ['HARVEST'], ['WEST'], ['FEED', 'WHEAT'], ['CARE'], ['DROP'], ['CARE'],
               ['WATER'], ['EAST'], ['EAST'], ['PASS']],
     'market': [['SELL', 'STRAWBERRY', 10], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 549 (day 22, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WEST'], ['PASS'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['PASS'],
               ['PASS'], ['PASS'], ['WATER'], ['NORTH'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 550 (day 22, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['NORTH'], ['PASS']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 551 (day 22, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['HARVEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['NORTH'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 552 (day 23, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 33], ['SELL', 'MILK', 9], ['SELL', 'FERTILIZER', 13],
                ['SELL', 'WHEAT', 1], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 553 (day 23, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 554 (day 23, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'WHEAT', 3], ['PICKUP', 'FERTILIZER', 5], ['WEST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 3], ['PICKUP', 'FERTILIZER', 6], ['EAST'], ['WEST'], ['EAST'],
               ['PICKUP', 'FERTILIZER', 4], ['EAST'], ['WEST'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 555 (day 23, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['WEST'], ['NORTH'], ['NORTH'], ['SOUTH'], ['EAST'],
               ['WEST'], ['EAST'], ['WEST'], ['EAST'], ['NORTH'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 556 (day 23, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WEST'], ['WEST'], ['FEED', 'WHEAT'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['NORTH'], ['EAST'], ['SOUTH'], ['NORTH'],
               ['NORTH'], ['NORTH'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 557 (day 23, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['SOUTH'], ['NORTH'], ['CARE'], ['FEED', 'WHEAT'], ['WATER'],
               ['NORTH'], ['WATER'], ['WATER'], ['SOUTH'], ['NORTH'], ['WATER'], ['HARVEST'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 558 (day 23, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['SOUTH'], ['NORTH'], ['COLLECT_FERTILIZER'], ['CARE'], ['SOUTH'], ['NORTH'],
               ['WEST'], ['NORTH'], ['SOUTH'], ['NORTH'], ['HARVEST'], ['DIG'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 559 (day 23, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['NORTH'], ['COLLECT_FERTILIZER'],
               ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['WATER'], ['WATER'], ['SOUTH'], ['NORTH'],
               ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 560 (day 23, hour 8).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['WATER'], ['FEED', 'WHEAT'], ['NORTH'], ['WATER'],
               ['HARVEST'], ['WEST'], ['EAST'], ['WATER'], ['NORTH'], ['WATER'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 561 (day 23, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WEST'], ['HARVEST'], ['CARE'], ['HARVEST'], ['WEST'], ['DIG'], ['WATER'],
               ['WATER'], ['WEST'], ['WATER'], ['NORTH'], ['EAST'], ['WATER']],
     'market': []},
    # Step 562 (day 23, hour 10).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['FERTILIZE', 'FERTILIZER'], ['PLANT', 'WHEAT'],
               ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'], ['FERTILIZE', 'FERTILIZER'],
               ['PLANT', 'WHEAT'], ['EAST'], ['SOUTH'], ['WEST'], ['HARVEST'], ['WATER'], ['SOUTH'],
               ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 563 (day 23, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['WEST'], ['CARE'], ['WATER'], ['WATER'], ['NORTH'],
               ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['PLANT', 'WHEAT'], ['WEST'], ['HARVEST'],
               ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 564 (day 23, hour 12).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['SOUTH'],
               ['EAST'], ['NORTH'], ['NORTH'], ['WATER'], ['WATER'], ['WATER'], ['DIG'], ['SOUTH']],
     'market': []},
    # Step 565 (day 23, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['FEED', 'WHEAT'], ['EAST'],
               ['FERTILIZE', 'FERTILIZER'], ['HARVEST'], ['NORTH'], ['NORTH'], ['WEST'], ['EAST'],
               ['EAST'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': []},
    # Step 566 (day 23, hour 14).
    {'farmer': ['EAST'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['HARVEST'], ['CARE'], ['SOUTH'], ['WATER'], ['DIG'],
               ['WATER'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['EAST'], ['WATER'],
               ['EAST']],
     'market': []},
    # Step 567 (day 23, hour 15).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['EAST'], ['PLANT', 'WHEAT'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'],
               ['PLANT', 'WHEAT'], ['EAST'], ['NORTH'], ['WATER'], ['HARVEST'], ['WATER'], ['EAST'],
               ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 568 (day 23, hour 16).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['NORTH'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WATER'], ['HARVEST'], ['HARVEST'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['HARVEST'], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 569 (day 23, hour 17).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['WATER'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['WATER'], ['EAST'],
               ['WEST'], ['DIG'], ['NORTH'], ['WATER'], ['WATER'], ['DIG'], ['WATER']],
     'market': []},
    # Step 570 (day 23, hour 18).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['SOUTH'], ['WATER'], ['NORTH'], ['CARE'], ['SOUTH'], ['SOUTH'], ['WEST'],
               ['PLANT', 'WHEAT'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['EAST'], ['PLANT', 'WHEAT'],
               ['EAST']],
     'market': []},
    # Step 571 (day 23, hour 19).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['FERTILIZE', 'FERTILIZER'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['COLLECT_FERTILIZER'], ['FERTILIZE', 'FERTILIZER'], ['HARVEST'], ['WATER'], ['WATER'],
               ['WATER'], ['SOUTH'], ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 572 (day 23, hour 20).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['WATER'], ['PLANT', 'WHEAT'], ['CARE'], ['PASS'], ['WATER'], ['DIG'],
               ['EAST'], ['WEST'], ['NORTH'], ['HARVEST'], ['HARVEST'], ['WEST'], ['SOUTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 573 (day 23, hour 21).
    {'farmer': ['PASS'],
     'hands': [['WEST'], ['PASS'], ['WATER'], ['COLLECT_FERTILIZER'], ['WEST'], ['PASS'],
               ['PLANT', 'WHEAT'], ['SOUTH'], ['SOUTH'], ['FERTILIZE', 'FERTILIZER'], ['DIG'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['PASS']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 574 (day 23, hour 22).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['NORTH'], ['PASS'], ['DROP'], ['PASS'], ['WATER'], ['WATER'],
               ['SOUTH'], ['WATER'], ['PLANT', 'WHEAT'], ['WATER'], ['HARVEST'], ['PASS']],
     'market': [['SELL', 'MILK', 11]]},
    # Step 575 (day 23, hour 23).
    {'farmer': ['PASS'],
     'hands': [['DIG'], ['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['HARVEST'], ['PASS'], ['WATER'], ['EAST'], ['PASS'], ['PASS']],
     'market': []},
    # Step 576 (day 24, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 22], ['SELL', 'WHEAT', 20], ['SELL', 'FERTILIZER', 2], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 577 (day 24, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'FERTILIZER', 2], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 578 (day 24, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['EAST'], ['PICKUP', 'WHEAT', 3], ['WEST'], ['WEST'],
               ['WEST']],
     'market': []},
    # Step 579 (day 24, hour 3).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['HARVEST'], ['NORTH'], ['NORTH'], ['HARVEST'], ['HARVEST'], ['NORTH'],
               ['HARVEST'], ['WEST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 580 (day 24, hour 4).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['PLANT', 'WHEAT'], ['NORTH'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['SOUTH'], ['NORTH'], ['FEED', 'WHEAT'], ['WEST'], ['WATER'], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 581 (day 24, hour 5).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WATER'], ['NORTH'], ['FEED', 'WHEAT'], ['CARE'], ['HARVEST'], ['NORTH'],
               ['CARE'], ['WEST'], ['HARVEST'], ['NORTH']],
     'market': []},
    # Step 582 (day 24, hour 6).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['NORTH'], ['CARE'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['NORTH'], ['COLLECT_FERTILIZER'], ['WATER'], ['PLANT', 'WHEAT'], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 583 (day 24, hour 7).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['HARVEST'],
               ['NORTH'], ['WEST'], ['NORTH'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 584 (day 24, hour 8).
    {'farmer': ['WEST'],
     'hands': [['SOUTH'], ['HARVEST'], ['HARVEST'], ['NORTH'], ['NORTH'], ['WEST'], ['WATER'],
               ['HARVEST'], ['NORTH'], ['WEST'], ['WATER']],
     'market': []},
    # Step 585 (day 24, hour 9).
    {'farmer': ['SOUTH'],
     'hands': [['FEED', 'WHEAT'], ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT'], ['HARVEST'],
               ['FEED', 'WHEAT'], ['HARVEST'], ['EAST'], ['FEED', 'WHEAT'], ['NORTH'], ['WATER'],
               ['HARVEST']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 586 (day 24, hour 10).
    {'farmer': ['SOUTH'],
     'hands': [['CARE'], ['WATER'], ['WATER'], ['FEED', 'WHEAT'], ['CARE'], ['EAST'], ['EAST'],
               ['CARE'], ['WATER'], ['HARVEST'], ['PLANT', 'WHEAT']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 587 (day 24, hour 11).
    {'farmer': ['SOUTH'],
     'hands': [['COLLECT_FERTILIZER'], ['SOUTH'], ['WEST'], ['CARE'], ['COLLECT_FERTILIZER'], ['SOUTH'],
               ['SOUTH'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 588 (day 24, hour 12).
    {'farmer': ['HARVEST'],
     'hands': [['WEST'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'], ['EAST'], ['HARVEST'], ['SOUTH'],
               ['EAST'], ['PLANT', 'WHEAT'], ['WATER'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 589 (day 24, hour 13).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['HARVEST'], ['NORTH'], ['WEST'], ['WEST'], ['EAST'], ['SOUTH'], ['DROP'],
               ['WATER'], ['WEST'], ['SOUTH']],
     'market': [['SELL', 'WOOL', 4], ['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 2]]},
    # Step 590 (day 24, hour 14).
    {'farmer': ['HARVEST'],
     'hands': [['WEST'], ['PLANT', 'WHEAT'], ['WATER'], ['SOUTH'], ['SOUTH'], ['HARVEST'], ['SOUTH'],
               ['PICKUP', 'WHEAT', 1], ['WEST'], ['WATER'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 591 (day 24, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['EAST'], ['WEST'], ['HARVEST'], ['SOUTH'], ['SOUTH'], ['HARVEST'], ['WEST'],
               ['WATER'], ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 592 (day 24, hour 16).
    {'farmer': ['HARVEST'],
     'hands': [['SOUTH'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['DROP'], ['HARVEST'], ['DIG'],
               ['NORTH'], ['HARVEST'], ['EAST'], ['PLANT', 'WHEAT']],
     'market': [['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 2], ['BUY_SEED', 'WHEAT', 2]]},
    # Step 593 (day 24, hour 17).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['DROP'], ['SOUTH'], ['CARE'], ['PICKUP', 'WHEAT', 2], ['PASS'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['PLANT', 'WHEAT'], ['EAST'], ['WATER']],
     'market': [['SELL', 'FERTILIZER', 1], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 594 (day 24, hour 18).
    {'farmer': ['HARVEST'],
     'hands': [['WATER'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['EAST'], ['NORTH'], ['WATER'],
               ['NORTH'], ['WATER'], ['EAST'], ['WEST']],
     'market': []},
    # Step 595 (day 24, hour 19).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['SOUTH'], ['SOUTH'], ['WEST'], ['NORTH'], ['NORTH'], ['EAST'], ['NORTH'],
               ['NORTH'], ['EAST'], ['WATER']],
     'market': []},
    # Step 596 (day 24, hour 20).
    {'farmer': ['HARVEST'],
     'hands': [['WATER'], ['WATER'], ['WATER'], ['WATER'], ['HARVEST'], ['NORTH'], ['HARVEST'],
               ['FEED', 'WHEAT'], ['WATER'], ['DROP'], ['HARVEST']],
     'market': [['SELL', 'WHEAT', 12]]},
    # Step 597 (day 24, hour 21).
    {'farmer': ['SOUTH'],
     'hands': [['PASS'], ['WEST'], ['WEST'], ['WEST'], ['WEST'], ['NORTH'], ['DIG'], ['CARE'],
               ['HARVEST'], ['WEST'], ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 598 (day 24, hour 22).
    {'farmer': ['HARVEST'],
     'hands': [['PASS'], ['WEST'], ['WATER'], ['WEST'], ['SOUTH'], ['DROP'], ['PLANT', 'WHEAT'],
               ['COLLECT_FERTILIZER'], ['PLANT', 'WHEAT'], ['WEST'], ['EAST']],
     'market': [['SELL', 'STRAWBERRY', 14], ['SELL', 'FERTILIZER', 1], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 599 (day 24, hour 23).
    {'farmer': ['WEST'],
     'hands': [['PASS'], ['WEST'], ['PASS'], ['SOUTH'], ['DROP'], ['PASS'], ['WATER'], ['PASS'],
               ['WATER'], ['WEST'], ['SOUTH']],
     'market': [['SELL', 'MILK', 3], ['SELL', 'WHEAT', 2]]},
    # Step 600 (day 25, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 16], ['SELL', 'WOOL', 12], ['SELL', 'WHEAT', 28],
                ['SELL', 'FERTILIZER', 7], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 601 (day 25, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 602 (day 25, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'WHEAT', 3], ['PICKUP', 'FERTILIZER', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 3], ['SOUTH'], ['EAST'], ['WEST'], ['NORTH'], ['WEST'], ['WEST'],
               ['WEST']],
     'market': []},
    # Step 603 (day 25, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['WEST'], ['NORTH'], ['NORTH'], ['WATER'], ['EAST'],
               ['NORTH'], ['NORTH'], ['WEST'], ['WEST'], ['WEST']],
     'market': []},
    # Step 604 (day 25, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WEST'], ['WEST'], ['NORTH'], ['HARVEST'], ['SOUTH'], ['EAST'], ['NORTH'],
               ['NORTH'], ['SOUTH'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 605 (day 25, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['WATER'], ['NORTH'], ['WATER'], ['WATER'], ['WATER'], ['WEST'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 606 (day 25, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['WEST'], ['SOUTH'], ['CARE'], ['CARE'], ['WEST'], ['NORTH'], ['WEST'],
               ['NORTH'], ['HARVEST'], ['WEST'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 607 (day 25, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['SOUTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['WATER'], ['WATER'], ['WATER'], ['PLANT', 'WHEAT'], ['NORTH'],
               ['PLANT', 'WHEAT']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 608 (day 25, hour 8).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['DIG'], ['WEST'], ['WEST'], ['NORTH'], ['SOUTH'], ['HARVEST'],
               ['WEST'], ['EAST'], ['WATER'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 609 (day 25, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['PLANT', 'WHEAT'], ['WATER'], ['NORTH'], ['HARVEST'], ['WATER'],
               ['PLANT', 'WHEAT'], ['WATER'], ['EAST'], ['WEST'], ['WATER'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 610 (day 25, hour 10).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['EAST'],
               ['WATER'], ['WEST'], ['WATER'], ['WATER'], ['HARVEST'], ['WATER']],
     'market': []},
    # Step 611 (day 25, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['SOUTH'], ['WATER'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'], ['EAST'],
               ['WATER'], ['SOUTH'], ['HARVEST'], ['PLANT', 'WHEAT'], ['HARVEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 612 (day 25, hour 12).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['SOUTH'], ['CARE'], ['COLLECT_FERTILIZER'], ['SOUTH'],
               ['WATER'], ['EAST'], ['WATER'], ['PLANT', 'WHEAT'], ['WATER'], ['PLANT', 'WHEAT']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 613 (day 25, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['SOUTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['HARVEST'],
               ['NORTH'], ['EAST'], ['WATER'], ['EAST'], ['WATER']],
     'market': []},
    # Step 614 (day 25, hour 14).
    {'farmer': ['SOUTH'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['EAST'], ['WEST'], ['SOUTH'], ['WEST'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['WATER'], ['WEST'], ['EAST'], ['SOUTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 615 (day 25, hour 15).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['WEST'], ['HARVEST'], ['WATER'], ['SOUTH'], ['SOUTH'], ['WATER'], ['WATER'], ['WATER'],
               ['WEST'], ['NORTH'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 616 (day 25, hour 16).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['EAST'], ['EAST'], ['SOUTH'], ['HARVEST'], ['WEST'], ['NORTH'], ['HARVEST'],
               ['SOUTH'], ['PLANT', 'WHEAT'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 617 (day 25, hour 17).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['EAST'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['WATER'], ['WATER'],
               ['PLANT', 'WHEAT'], ['WATER'], ['WATER'], ['NORTH'], ['PLANT', 'WHEAT']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 618 (day 25, hour 18).
    {'farmer': ['WEST'],
     'hands': [['DIG'], ['EAST'], ['WEST'], ['SOUTH'], ['CARE'], ['WEST'], ['NORTH'], ['WATER'],
               ['WEST'], ['EAST'], ['WATER'], ['WATER']],
     'market': []},
    # Step 619 (day 25, hour 19).
    {'farmer': ['CARE'],
     'hands': [['PLANT', 'WHEAT'], ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['HARVEST'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['PASS'], ['WATER'], ['EAST'], ['HARVEST'],
               ['PASS']],
     'market': []},
    # Step 620 (day 25, hour 20).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WATER'], ['HARVEST'], ['HARVEST'], ['FEED', 'WHEAT'], ['WEST'], ['PASS'], ['NORTH'],
               ['PASS'], ['NORTH'], ['PASS'], ['PLANT', 'WHEAT'], ['PASS']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 621 (day 25, hour 21).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['PASS'], ['PASS'], ['PASS'], ['DROP'], ['PASS'], ['WATER'], ['PASS'],
               ['NORTH'], ['PASS'], ['WATER'], ['PASS']],
     'market': [['SELL', 'MILK', 9], ['SELL', 'FERTILIZER', 2]]},
    # Step 622 (day 25, hour 22).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WEST'], ['PASS'],
               ['WATER'], ['PASS'], ['SOUTH'], ['PASS']],
     'market': []},
    # Step 623 (day 25, hour 23).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WATER'], ['PASS'],
               ['PASS'], ['PASS'], ['PLANT', 'WHEAT'], ['PASS']],
     'market': []},
    # Step 624 (day 26, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 6], ['SELL', 'MILK', 5], ['SELL', 'WHEAT', 26],
                ['SELL', 'FERTILIZER', 10], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE']]},
    # Step 625 (day 26, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_SEED', 'WHEAT', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 626 (day 26, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'WHEAT', 2], ['WATER'], ['WEST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['WEST'], ['NORTH'], ['EAST'], ['WEST'], ['WEST'],
               ['WEST'], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 627 (day 26, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['WEST'], ['WEST'], ['HARVEST'], ['HARVEST'], ['WEST'], ['NORTH'],
               ['EAST'], ['SOUTH'], ['WEST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 628 (day 26, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['WEST'], ['HARVEST'], ['FEED', 'WHEAT'], ['DIG'],
               ['WEST'], ['NORTH'], ['EAST'], ['SOUTH'], ['WEST'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 629 (day 26, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WEST'], ['SOUTH'], ['FEED', 'WHEAT'], ['CARE'], ['PLANT', 'WHEAT'], ['WEST'],
               ['WATER'], ['WATER'], ['HARVEST'], ['WEST'], ['WATER'], ['WATER']],
     'market': [['SELL', 'FERTILIZER', 1], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 630 (day 26, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['SOUTH'], ['CARE'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['SOUTH'], ['NORTH'], ['EAST'], ['DIG'], ['WEST'], ['HARVEST'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 631 (day 26, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['WEST'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['NORTH'], ['SOUTH'], ['SOUTH'],
               ['WATER'], ['WATER'], ['PLANT', 'WHEAT'], ['SOUTH'], ['PLANT', 'WHEAT'], ['SOUTH']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 632 (day 26, hour 8).
    {'farmer': ['CARE'],
     'hands': [['SOUTH'], ['WATER'], ['DIG'], ['NORTH'], ['NORTH'], ['HARVEST'], ['HARVEST'], ['WEST'],
               ['WEST'], ['WATER'], ['SOUTH'], ['WATER'], ['WATER']],
     'market': []},
    # Step 633 (day 26, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['PLANT', 'WHEAT'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['DIG'], ['DIG'], ['SOUTH'], ['WEST'], ['SOUTH'], ['HARVEST'], ['EAST'], ['EAST']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 634 (day 26, hour 10).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['EAST'], ['WATER'], ['CARE'], ['CARE'], ['PLANT', 'WHEAT'],
               ['PLANT', 'WHEAT'], ['WATER'], ['WEST'], ['HARVEST'], ['DIG'], ['NORTH'], ['EAST']],
     'market': [['SELL', 'FERTILIZER', 2]]},
    # Step 635 (day 26, hour 11).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['SOUTH'], ['SOUTH'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['WEST'], ['NORTH'], ['DIG'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['DIG']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 636 (day 26, hour 12).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['WATER'], ['HARVEST'], ['EAST'], ['EAST'], ['SOUTH'], ['SOUTH'], ['WEST'],
               ['NORTH'], ['PLANT', 'WHEAT'], ['WATER'], ['WATER'], ['PLANT', 'WHEAT']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 637 (day 26, hour 13).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['DIG'], ['NORTH'], ['SOUTH'], ['HARVEST'], ['HARVEST'], ['WATER'],
               ['NORTH'], ['WATER'], ['SOUTH'], ['EAST'], ['WATER']],
     'market': []},
    # Step 638 (day 26, hour 14).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['WEST'], ['PLANT', 'WHEAT'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['DIG'],
               ['DIG'], ['WEST'], ['NORTH'], ['EAST'], ['HARVEST'], ['WATER'], ['WEST']],
     'market': [['SELL', 'FERTILIZER', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 639 (day 26, hour 15).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['WEST'], ['WATER'], ['CARE'], ['CARE'], ['PLANT', 'WHEAT'],
               ['PLANT', 'WHEAT'], ['WATER'], ['WATER'], ['SOUTH'], ['DIG'], ['WEST'], ['SOUTH']],
     'market': [['SELL', 'FERTILIZER', 2], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 640 (day 26, hour 16).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['SOUTH'], ['EAST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['WATER'], ['NORTH'], ['HARVEST'], ['HARVEST'], ['PLANT', 'WHEAT'], ['NORTH'],
               ['CARE']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 641 (day 26, hour 17).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['SOUTH'], ['SOUTH'], ['WEST'], ['EAST'], ['PASS'], ['EAST'], ['WATER'],
               ['PLANT', 'WHEAT'], ['DIG'], ['WATER'], ['DIG'], ['COLLECT_FERTILIZER']],
     'market': []},
    # Step 642 (day 26, hour 18).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['SOUTH'], ['HARVEST'], ['NORTH'], ['FEED', 'WHEAT'], ['PASS'], ['SOUTH'],
               ['SOUTH'], ['WATER'], ['PLANT', 'WHEAT'], ['EAST'], ['PLANT', 'WHEAT'], ['NORTH']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 643 (day 26, hour 19).
    {'farmer': ['WATER'],
     'hands': [['EAST'], ['HARVEST'], ['DIG'], ['NORTH'], ['NORTH'], ['PASS'], ['HARVEST'], ['SOUTH'],
               ['EAST'], ['WATER'], ['SOUTH'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 644 (day 26, hour 20).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['DIG'], ['PLANT', 'WHEAT'], ['FEED', 'WHEAT'], ['WATER'], ['PASS'], ['DIG'],
               ['WATER'], ['EAST'], ['PASS'], ['HARVEST'], ['PASS'], ['WATER']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 645 (day 26, hour 21).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['PLANT', 'WHEAT'], ['WATER'], ['CARE'], ['EAST'], ['PASS'],
               ['PLANT', 'WHEAT'], ['PASS'], ['EAST'], ['PASS'], ['DIG'], ['PASS'], ['EAST']],
     'market': [['SELL', 'FERTILIZER', 2]]},
    # Step 646 (day 26, hour 22).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['WATER'], ['PASS'], ['COLLECT_FERTILIZER'], ['NORTH'], ['PASS'], ['WATER'],
               ['PASS'], ['WATER'], ['PASS'], ['PLANT', 'WHEAT'], ['PASS'], ['EAST']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 647 (day 26, hour 23).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['PASS'], ['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['WATER'], ['PASS'], ['WATER']],
     'market': []},
    # Step 648 (day 27, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 32], ['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 13],
                ['SELL', 'WHEAT', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 649 (day 27, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 650 (day 27, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['PICKUP', 'WHEAT', 3], ['WEST'], ['EAST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 3], ['WEST'], ['EAST'], ['PICKUP', 'WHEAT', 3], ['NORTH'],
               ['WEST']],
     'market': []},
    # Step 651 (day 27, hour 3).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['HARVEST'], ['NORTH'], ['WEST'], ['EAST'],
               ['NORTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 652 (day 27, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['COLLECT_FERTILIZER'], ['SOUTH'], ['NORTH'], ['FEED', 'WHEAT'], ['HARVEST'], ['NORTH'],
               ['NORTH'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 653 (day 27, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WATER'], ['NORTH'], ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'], ['NORTH'],
               ['NORTH'], ['HARVEST'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 654 (day 27, hour 6).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['WEST'], ['NORTH'], ['NORTH'], ['CARE'], ['WATER'], ['NORTH'],
               ['FEED', 'WHEAT'], ['HARVEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 655 (day 27, hour 7).
    {'farmer': ['NORTH'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['WATER'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['WATER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['HARVEST']],
     'market': []},
    # Step 656 (day 27, hour 8).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['EAST'], ['FEED', 'WHEAT'], ['NORTH'], ['WATER'],
               ['HARVEST'], ['WEST'], ['WATER'], ['WEST']],
     'market': []},
    # Step 657 (day 27, hour 9).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['WATER'], ['EAST'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['WEST'], ['NORTH'],
               ['SOUTH'], ['HARVEST'], ['WATER']],
     'market': []},
    # Step 658 (day 27, hour 10).
    {'farmer': ['WATER'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['EAST'], ['WEST'], ['FEED', 'WHEAT'], ['WATER'],
               ['WATER'], ['HARVEST'], ['EAST'], ['HARVEST']],
     'market': []},
    # Step 659 (day 27, hour 11).
    {'farmer': ['NORTH'],
     'hands': [['CARE'], ['WATER'], ['SOUTH'], ['NORTH'], ['CARE'], ['SOUTH'], ['HARVEST'],
               ['FEED', 'WHEAT'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 660 (day 27, hour 12).
    {'farmer': ['WATER'],
     'hands': [['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['NORTH'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['NORTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 661 (day 27, hour 13).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WATER'], ['HARVEST'], ['NORTH'], ['EAST'], ['EAST'], ['WATER'], ['WEST'],
               ['WATER'], ['HARVEST']],
     'market': []},
    # Step 662 (day 27, hour 14).
    {'farmer': ['SOUTH'],
     'hands': [['WATER'], ['EAST'], ['SOUTH'], ['FEED', 'WHEAT'], ['SOUTH'], ['NORTH'], ['HARVEST'],
               ['SOUTH'], ['HARVEST'], ['WEST']],
     'market': []},
    # Step 663 (day 27, hour 15).
    {'farmer': ['WATER'],
     'hands': [['SOUTH'], ['WATER'], ['WATER'], ['CARE'], ['SOUTH'], ['NORTH'], ['EAST'], ['HARVEST'],
               ['EAST'], ['WATER']],
     'market': []},
    # Step 664 (day 27, hour 16).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['EAST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['NORTH'],
               ['WATER'], ['FEED', 'WHEAT'], ['EAST'], ['HARVEST']],
     'market': []},
    # Step 665 (day 27, hour 17).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['WATER'], ['NORTH'], ['WEST'], ['WEST'], ['NORTH'], ['HARVEST'], ['CARE'],
               ['EAST'], ['NORTH']],
     'market': []},
    # Step 666 (day 27, hour 18).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['EAST'], ['NORTH'], ['WEST'], ['DROP'], ['WATER'], ['SOUTH'], ['EAST'],
               ['SOUTH'], ['WATER']],
     'market': [['SELL', 'MILK', 9], ['SELL', 'FERTILIZER', 2]]},
    # Step 667 (day 27, hour 19).
    {'farmer': ['SOUTH'],
     'hands': [['CARE'], ['WATER'], ['WATER'], ['PASS'], ['PICKUP', 'WHEAT', 1], ['SOUTH'], ['WATER'],
               ['EAST'], ['SOUTH'], ['NORTH']],
     'market': []},
    # Step 668 (day 27, hour 20).
    {'farmer': ['SOUTH'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['HARVEST'], ['PASS'], ['EAST'], ['WATER'],
               ['HARVEST'], ['DROP'], ['WATER'], ['WATER']],
     'market': [['SELL', 'WOOL', 8], ['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 2]]},
    # Step 669 (day 27, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['FEED', 'WHEAT'], ['PASS'], ['EAST'], ['WEST'],
               ['PASS'], ['PASS']],
     'market': []},
    # Step 670 (day 27, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WATER'], ['WEST'],
               ['PASS'], ['PASS']],
     'market': []},
    # Step 671 (day 27, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['HARVEST'],
               ['COLLECT_FERTILIZER'], ['PASS'], ['PASS']],
     'market': []},
    # Step 672 (day 28, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 8], ['SELL', 'WHEAT', 51], ['SELL', 'FERTILIZER', 9], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 673 (day 28, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 674 (day 28, hour 2).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['PICKUP', 'WHEAT', 1], ['WATER'], ['WEST'], ['PICKUP', 'WHEAT', 2],
               ['PICKUP', 'WHEAT', 3], ['SOUTH'], ['EAST'], ['WEST'], ['WEST'], ['WEST']],
     'market': []},
    # Step 675 (day 28, hour 3).
    {'farmer': ['NORTH'],
     'hands': [['HARVEST'], ['HARVEST'], ['WEST'], ['WEST'], ['NORTH'], ['WATER'], ['NORTH'], ['WEST'],
               ['NORTH'], ['WEST']],
     'market': []},
    # Step 676 (day 28, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['WEST'], ['HARVEST'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['NORTH'], ['WEST'], ['NORTH'], ['SOUTH']],
     'market': []},
    # Step 677 (day 28, hour 5).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WATER'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['NORTH'], ['WATER'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 678 (day 28, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['FEED', 'WHEAT'], ['HARVEST'], ['SOUTH'], ['WEST'], ['NORTH'], ['WEST'], ['NORTH'],
               ['EAST'], ['WATER'], ['WEST']],
     'market': []},
    # Step 679 (day 28, hour 7).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['WATER'], ['NORTH'], ['NORTH'], ['HARVEST'], ['WEST']],
     'market': []},
    # Step 680 (day 28, hour 8).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['SOUTH'],
               ['WATER'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 681 (day 28, hour 9).
    {'farmer': ['WEST'],
     'hands': [['DROP'], ['HARVEST'], ['WATER'], ['EAST'], ['EAST'], ['WATER'], ['EAST'], ['NORTH'],
               ['WATER'], ['WATER']],
     'market': [['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 2]]},
    # Step 682 (day 28, hour 10).
    {'farmer': ['WATER'],
     'hands': [['EAST'], ['WEST'], ['WEST'], ['EAST'], ['SOUTH'], ['EAST'], ['EAST'], ['WATER'],
               ['HARVEST'], ['EAST']],
     'market': []},
    # Step 683 (day 28, hour 11).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['NORTH'], ['HARVEST'], ['WATER'], ['SOUTH'], ['WEST'],
               ['WEST'], ['SOUTH']],
     'market': []},
    # Step 684 (day 28, hour 12).
    {'farmer': ['SOUTH'],
     'hands': [['NORTH'], ['HARVEST'], ['SOUTH'], ['NORTH'], ['COLLECT_FERTILIZER'], ['SOUTH'],
               ['SOUTH'], ['WATER'], ['SOUTH'], ['SOUTH']],
     'market': []},
    # Step 685 (day 28, hour 13).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['EAST'], ['WATER'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['WATER'],
               ['HARVEST'], ['WATER'], ['SOUTH']],
     'market': []},
    # Step 686 (day 28, hour 14).
    {'farmer': ['SOUTH'],
     'hands': [['WATER'], ['EAST'], ['EAST'], ['WEST'], ['FEED', 'WHEAT'], ['WEST'], ['SOUTH'],
               ['WEST'], ['HARVEST'], ['WATER']],
     'market': []},
    # Step 687 (day 28, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['SOUTH'], ['EAST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['WATER'], ['SOUTH'],
               ['WATER'], ['WEST'], ['SOUTH']],
     'market': []},
    # Step 688 (day 28, hour 16).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['NORTH'], ['WEST'], ['WEST'], ['WATER'], ['HARVEST'],
               ['NORTH'], ['WATER']],
     'market': []},
    # Step 689 (day 28, hour 17).
    {'farmer': ['SOUTH'],
     'hands': [['SOUTH'], ['HARVEST'], ['SOUTH'], ['FEED', 'WHEAT'], ['WEST'], ['WATER'], ['HARVEST'],
               ['NORTH'], ['WATER'], ['WEST']],
     'market': []},
    # Step 690 (day 28, hour 18).
    {'farmer': ['SOUTH'],
     'hands': [['SOUTH'], ['WEST'], ['WEST'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['PASS'], ['EAST'],
               ['WATER'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 691 (day 28, hour 19).
    {'farmer': ['WATER'],
     'hands': [['WATER'], ['WEST'], ['WEST'], ['EAST'], ['DROP'], ['PASS'], ['WATER'], ['HARVEST'],
               ['WEST'], ['NORTH']],
     'market': [['SELL', 'MILK', 5], ['SELL', 'FERTILIZER', 4]]},
    # Step 692 (day 28, hour 20).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['WATER'], ['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['HARVEST'], ['EAST'],
               ['SOUTH'], ['NORTH']],
     'market': []},
    # Step 693 (day 28, hour 21).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['WEST'], ['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['NORTH'], ['WATER'],
               ['SOUTH'], ['WATER']],
     'market': []},
    # Step 694 (day 28, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['SOUTH'], ['PASS']],
     'market': []},
    # Step 695 (day 28, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['WATER'], ['PASS']],
     'market': []},
    # Step 696 (day 29, hour 0).
    {'farmer': ['EAST'],
     'hands': [],
     'market': [['SELL', 'WHEAT', 61], ['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 7], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 697 (day 29, hour 1).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['WEST'], ['NORTH'], ['WEST'], ['EAST'], ['SOUTH'], ['WEST']],
     'market': [['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 698 (day 29, hour 2).
    {'farmer': ['HARVEST'],
     'hands': [['EAST'], ['NORTH'], ['NORTH'], ['WEST'], ['HARVEST'], ['WATER'], ['WEST'], ['WEST'],
               ['WEST'], ['WEST']],
     'market': []},
    # Step 699 (day 29, hour 3).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['NORTH'], ['NORTH'], ['HARVEST'], ['EAST'], ['HARVEST'], ['WEST'], ['WEST'],
               ['SOUTH'], ['WEST']],
     'market': []},
    # Step 700 (day 29, hour 4).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['NORTH'], ['HARVEST'], ['NORTH'], ['EAST'], ['SOUTH'], ['SOUTH'], ['WEST'],
               ['WEST'], ['WEST']],
     'market': []},
    # Step 701 (day 29, hour 5).
    {'farmer': ['HARVEST'],
     'hands': [['NORTH'], ['NORTH'], ['EAST'], ['WATER'], ['NORTH'], ['WATER'], ['WATER'], ['WATER'],
               ['SOUTH'], ['NORTH']],
     'market': []},
    # Step 702 (day 29, hour 6).
    {'farmer': ['EAST'],
     'hands': [['WATER'], ['NORTH'], ['NORTH'], ['HARVEST'], ['WATER'], ['HARVEST'], ['HARVEST'],
               ['HARVEST'], ['WATER'], ['WATER']],
     'market': []},
    # Step 703 (day 29, hour 7).
    {'farmer': ['HARVEST'],
     'hands': [['HARVEST'], ['HARVEST'], ['NORTH'], ['WEST'], ['EAST'], ['SOUTH'], ['WEST'], ['WEST'],
               ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 704 (day 29, hour 8).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['WEST'], ['WATER'], ['WEST'], ['WATER'], ['WATER'], ['WATER'], ['WATER'],
               ['WEST'], ['NORTH']],
     'market': []},
    # Step 705 (day 29, hour 9).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['WATER'], ['HARVEST'], ['WATER'], ['HARVEST'], ['HARVEST'], ['HARVEST'],
               ['HARVEST'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 706 (day 29, hour 10).
    {'farmer': ['HARVEST'],
     'hands': [['WEST'], ['HARVEST'], ['WEST'], ['HARVEST'], ['WEST'], ['WEST'], ['WEST'], ['SOUTH'],
               ['HARVEST'], ['NORTH']],
     'market': []},
    # Step 707 (day 29, hour 11).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['EAST'], ['SOUTH'], ['EAST'], ['WEST'], ['WATER'], ['WATER'], ['WATER'],
               ['WEST'], ['WATER']],
     'market': []},
    # Step 708 (day 29, hour 12).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'], ['COLLECT_FERTILIZER'],
               ['HARVEST'], ['HARVEST'], ['HARVEST'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 709 (day 29, hour 13).
    {'farmer': ['SOUTH'],
     'hands': [['HARVEST'], ['EAST'], ['COLLECT_FERTILIZER'], ['EAST'], ['WEST'], ['WEST'], ['SOUTH'],
               ['EAST'], ['HARVEST'], ['EAST']],
     'market': []},
    # Step 710 (day 29, hour 14).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['SOUTH'], ['WEST'], ['COLLECT_FERTILIZER'], ['WEST'], ['WATER'], ['WATER'],
               ['EAST'], ['EAST'], ['EAST']],
     'market': []},
    # Step 711 (day 29, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['SOUTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['EAST'], ['COLLECT_FERTILIZER'],
               ['HARVEST'], ['HARVEST'], ['NORTH'], ['EAST'], ['EAST']],
     'market': []},
    # Step 712 (day 29, hour 16).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['SOUTH'], ['SOUTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'], ['EAST'],
               ['COLLECT_FERTILIZER'], ['EAST'], ['SOUTH']],
     'market': []},
    # Step 713 (day 29, hour 17).
    {'farmer': ['WEST'],
     'hands': [['SOUTH'], ['SOUTH'], ['SOUTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['EAST'], ['EAST'],
               ['EAST'], ['NORTH'], ['SOUTH']],
     'market': []},
    # Step 714 (day 29, hour 18).
    {'farmer': ['DROP'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['DROP'], ['DROP'], ['DROP'], ['NORTH'],
               ['EAST'], ['EAST'], ['NORTH'], ['SOUTH']],
     'market': [['SELL', 'MILK', 18], ['SELL', 'FERTILIZER', 9], ['SELL', 'WHEAT', 22]]},
    # Step 715 (day 29, hour 19).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['DROP'], ['PASS'], ['PASS'], ['PASS'], ['NORTH'], ['EAST'], ['DROP'],
               ['DROP'], ['SOUTH']],
     'market': [['SELL', 'MILK', 6], ['SELL', 'WHEAT', 24], ['SELL', 'FERTILIZER', 3],
                ['SELL', 'FERTILIZER', 14]]},
    # Step 716 (day 29, hour 20).
    {'farmer': ['PASS'],
     'hands': [['DROP'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['NORTH'], ['NORTH'], ['PASS'],
               ['PASS'], ['DROP']],
     'market': [['SELL', 'FERTILIZER', 1], ['SELL', 'WHEAT', 15]]},
    # Step 717 (day 29, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['DROP'], ['NORTH'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': [['SELL', 'WHEAT', 15]]},
    # Step 718 (day 29, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['DROP'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': [['SELL', 'WHEAT', 15]]},
]
_SEAT1_ACTIONS = [
    # Step 0 (day 0, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['BUY_PRODUCT', 'WHEAT', 5], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_ANIMAL', 'COW', 1], ['BUY_ANIMAL', 'SHEEP', 4], ['BUY_SEED', 'WHEAT', 5],
                ['BUY_SEED', 'MELON', 5]]},
    # Step 1 (day 0, hour 1).
    {'farmer': ['PICKUP', 'COW', 1],
     'hands': [['WEST'], ['WEST'], ['PASS'], ['PICKUP', 'SHEEP', 4], ['PASS']],
     'market': []},
    # Step 2 (day 0, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['NORTH'], ['NORTH'], ['PASS'], ['PICKUP', 'WHEAT', 4], ['PASS']],
     'market': []},
    # Step 3 (day 0, hour 3).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['NORTH'], ['PASS'], ['BUILD_PASTURE'], ['PASS']],
     'market': []},
    # Step 4 (day 0, hour 4).
    {'farmer': ['BUILD_PASTURE'],
     'hands': [['NORTH'], ['NORTH'], ['PASS'], ['PLACE', 'SHEEP'], ['PASS']],
     'market': []},
    # Step 5 (day 0, hour 5).
    {'farmer': ['PLACE', 'COW'],
     'hands': [['PLANT', 'MELON'], ['NORTH'], ['PASS'], ['FEED', 'WHEAT'], ['PASS']],
     'market': []},
    # Step 6 (day 0, hour 6).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['WATER'], ['NORTH'], ['PASS'], ['CARE'], ['PASS']],
     'market': []},
    # Step 7 (day 0, hour 7).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['PLANT', 'WHEAT'], ['PASS'], ['NORTH'], ['PASS']],
     'market': []},
    # Step 8 (day 0, hour 8).
    {'farmer': ['PASS'],
     'hands': [['PLANT', 'WHEAT'], ['WATER'], ['PASS'], ['BUILD_PASTURE'], ['PASS']],
     'market': []},
    # Step 9 (day 0, hour 9).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['WEST'], ['PASS'], ['PLACE', 'SHEEP'], ['PASS']],
     'market': []},
    # Step 10 (day 0, hour 10).
    {'farmer': ['PASS'],
     'hands': [['WEST'], ['PLANT', 'WHEAT'], ['PASS'], ['FEED', 'WHEAT'], ['PASS']],
     'market': []},
    # Step 11 (day 0, hour 11).
    {'farmer': ['PASS'], 'hands': [['SOUTH'], ['WATER'], ['PASS'], ['CARE'], ['PASS']], 'market': []},
    # Step 12 (day 0, hour 12).
    {'farmer': ['PASS'],
     'hands': [['PLANT', 'MELON'], ['WEST'], ['PASS'], ['NORTH'], ['PASS']],
     'market': []},
    # Step 13 (day 0, hour 13).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PLANT', 'WHEAT'], ['PASS'], ['BUILD_PASTURE'], ['PASS']],
     'market': []},
    # Step 14 (day 0, hour 14).
    {'farmer': ['PASS'],
     'hands': [['WEST'], ['WATER'], ['PASS'], ['PLACE', 'SHEEP'], ['PASS']],
     'market': []},
    # Step 15 (day 0, hour 15).
    {'farmer': ['PASS'],
     'hands': [['PLANT', 'MELON'], ['WEST'], ['PASS'], ['FEED', 'WHEAT'], ['PASS']],
     'market': []},
    # Step 16 (day 0, hour 16).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PLANT', 'WHEAT'], ['PASS'], ['CARE'], ['PASS']],
     'market': []},
    # Step 17 (day 0, hour 17).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['PASS'], ['WEST'], ['PASS']], 'market': []},
    # Step 18 (day 0, hour 18).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['SOUTH'], ['PASS'], ['SOUTH'], ['PASS']], 'market': []},
    # Step 19 (day 0, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PLANT', 'MELON'], ['PASS'], ['BUILD_PASTURE'], ['PASS']],
     'market': []},
    # Step 20 (day 0, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PASS'], ['PLACE', 'SHEEP'], ['PASS']],
     'market': []},
    # Step 21 (day 0, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['EAST'], ['PASS'], ['FEED', 'WHEAT'], ['PASS']],
     'market': []},
    # Step 22 (day 0, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PLANT', 'MELON'], ['PASS'], ['CARE'], ['PASS']],
     'market': []},
    # Step 23 (day 0, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 24 (day 1, hour 0).
    {'farmer': ['PASS'], 'hands': [], 'market': [['HIRE']]},
    # Step 25 (day 1, hour 1).
    {'farmer': ['CARE'], 'hands': [['WEST']], 'market': []},
    # Step 26 (day 1, hour 2).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['NORTH']], 'market': []},
    # Step 27 (day 1, hour 3).
    {'farmer': ['WEST'], 'hands': [['CARE']], 'market': []},
    # Step 28 (day 1, hour 4).
    {'farmer': ['CARE'], 'hands': [['COLLECT_FERTILIZER']], 'market': []},
    # Step 29 (day 1, hour 5).
    {'farmer': ['NORTH'], 'hands': [['NORTH']], 'market': []},
    # Step 30 (day 1, hour 6).
    {'farmer': ['CARE'], 'hands': [['CARE']], 'market': []},
    # Step 31 (day 1, hour 7).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['COLLECT_FERTILIZER']], 'market': []},
    # Step 32 (day 1, hour 8).
    {'farmer': ['SOUTH'], 'hands': [['WEST']], 'market': []},
    # Step 33 (day 1, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['SOUTH']], 'market': []},
    # Step 34 (day 1, hour 10).
    {'farmer': ['PASS'], 'hands': [['SOUTH']], 'market': []},
    # Step 35 (day 1, hour 11).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 36 (day 1, hour 12).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 37 (day 1, hour 13).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 38 (day 1, hour 14).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 39 (day 1, hour 15).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 40 (day 1, hour 16).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 41 (day 1, hour 17).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 42 (day 1, hour 18).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 43 (day 1, hour 19).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 44 (day 1, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 45 (day 1, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 46 (day 1, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 47 (day 1, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS']], 'market': []},
    # Step 48 (day 2, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 6]]},
    # Step 49 (day 2, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 1], 'hands': [['WEST'], ['NORTH']], 'market': []},
    # Step 50 (day 2, hour 2).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['PICKUP', 'WHEAT', 4], ['NORTH']], 'market': []},
    # Step 51 (day 2, hour 3).
    {'farmer': ['CARE'], 'hands': [['NORTH'], ['NORTH']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 52 (day 2, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['FEED', 'WHEAT'], ['NORTH']], 'market': []},
    # Step 53 (day 2, hour 5).
    {'farmer': ['WEST'], 'hands': [['CARE'], ['WATER']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 54 (day 2, hour 6).
    {'farmer': ['NORTH'], 'hands': [['COLLECT_FERTILIZER'], ['NORTH']], 'market': []},
    # Step 55 (day 2, hour 7).
    {'farmer': ['NORTH'], 'hands': [['NORTH'], ['WATER']], 'market': []},
    # Step 56 (day 2, hour 8).
    {'farmer': ['NORTH'], 'hands': [['FEED', 'WHEAT'], ['WEST']], 'market': []},
    # Step 57 (day 2, hour 9).
    {'farmer': ['WATER'], 'hands': [['CARE'], ['WATER']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 58 (day 2, hour 10).
    {'farmer': ['WEST'], 'hands': [['COLLECT_FERTILIZER'], ['WEST']], 'market': []},
    # Step 59 (day 2, hour 11).
    {'farmer': ['WATER'], 'hands': [['WEST'], ['WATER']], 'market': []},
    # Step 60 (day 2, hour 12).
    {'farmer': ['WEST'], 'hands': [['SOUTH'], ['WEST']], 'market': []},
    # Step 61 (day 2, hour 13).
    {'farmer': ['WATER'], 'hands': [['FEED', 'WHEAT'], ['WATER']], 'market': []},
    # Step 62 (day 2, hour 14).
    {'farmer': ['WEST'], 'hands': [['CARE'], ['WEST']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 63 (day 2, hour 15).
    {'farmer': ['WATER'], 'hands': [['COLLECT_FERTILIZER'], ['WATER']], 'market': []},
    # Step 64 (day 2, hour 16).
    {'farmer': ['PASS'], 'hands': [['SOUTH'], ['PASS']], 'market': []},
    # Step 65 (day 2, hour 17).
    {'farmer': ['PASS'], 'hands': [['FEED', 'WHEAT'], ['PASS']], 'market': []},
    # Step 66 (day 2, hour 18).
    {'farmer': ['PASS'], 'hands': [['CARE'], ['PASS']], 'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 67 (day 2, hour 19).
    {'farmer': ['PASS'], 'hands': [['COLLECT_FERTILIZER'], ['PASS']], 'market': []},
    # Step 68 (day 2, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS']], 'market': []},
    # Step 69 (day 2, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS']], 'market': []},
    # Step 70 (day 2, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS']], 'market': []},
    # Step 71 (day 2, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS']], 'market': []},
    # Step 72 (day 3, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_SEED', 'WHEAT', 1],
                ['BUY_SEED', 'STRAWBERRY', 3]]},
    # Step 73 (day 3, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 1], 'hands': [['WEST'], ['WEST'], ['WEST']], 'market': []},
    # Step 74 (day 3, hour 2).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['NORTH']], 'market': []},
    # Step 75 (day 3, hour 3).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 76 (day 3, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH']], 'market': []},
    # Step 77 (day 3, hour 5).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['PLANT', 'STRAWBERRY'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 78 (day 3, hour 6).
    {'farmer': ['CARE'], 'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH']], 'market': []},
    # Step 79 (day 3, hour 7).
    {'farmer': ['NORTH'], 'hands': [['NORTH'], ['WEST'], ['WATER']], 'market': []},
    # Step 80 (day 3, hour 8).
    {'farmer': ['CARE'], 'hands': [['FEED', 'WHEAT'], ['PLANT', 'STRAWBERRY'], ['WEST']], 'market': []},
    # Step 81 (day 3, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WATER'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 82 (day 3, hour 10).
    {'farmer': ['SOUTH'], 'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['WEST']], 'market': []},
    # Step 83 (day 3, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['PLANT', 'STRAWBERRY'], ['WEST']],
     'market': []},
    # Step 84 (day 3, hour 12).
    {'farmer': ['NORTH'], 'hands': [['SOUTH'], ['WATER'], ['SOUTH']], 'market': []},
    # Step 85 (day 3, hour 13).
    {'farmer': ['NORTH'], 'hands': [['FEED', 'WHEAT'], ['NORTH'], ['SOUTH']], 'market': []},
    # Step 86 (day 3, hour 14).
    {'farmer': ['NORTH'],
     'hands': [['SOUTH'], ['NORTH'], ['PLANT', 'WHEAT']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 87 (day 3, hour 15).
    {'farmer': ['NORTH'], 'hands': [['FEED', 'WHEAT'], ['WATER'], ['WATER']], 'market': []},
    # Step 88 (day 3, hour 16).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['WEST'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 89 (day 3, hour 17).
    {'farmer': ['WEST'], 'hands': [['PASS'], ['WATER'], ['PASS']], 'market': []},
    # Step 90 (day 3, hour 18).
    {'farmer': ['WATER'], 'hands': [['PASS'], ['EAST'], ['PASS']], 'market': []},
    # Step 91 (day 3, hour 19).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 92 (day 3, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 93 (day 3, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 94 (day 3, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 95 (day 3, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 96 (day 4, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 97 (day 4, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['WEST'], ['NORTH'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 5]]},
    # Step 98 (day 4, hour 2).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['NORTH']], 'market': []},
    # Step 99 (day 4, hour 3).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 100 (day 4, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH']], 'market': []},
    # Step 101 (day 4, hour 5).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 102 (day 4, hour 6).
    {'farmer': ['WEST'], 'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['NORTH']], 'market': []},
    # Step 103 (day 4, hour 7).
    {'farmer': ['WEST'], 'hands': [['NORTH'], ['WATER'], ['WATER']], 'market': []},
    # Step 104 (day 4, hour 8).
    {'farmer': ['WEST'], 'hands': [['FEED', 'WHEAT'], ['WEST'], ['HARVEST']], 'market': []},
    # Step 105 (day 4, hour 9).
    {'farmer': ['NORTH'], 'hands': [['CARE'], ['WATER'], ['PLANT', 'WHEAT']], 'market': []},
    # Step 106 (day 4, hour 10).
    {'farmer': ['NORTH'], 'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['WATER']], 'market': []},
    # Step 107 (day 4, hour 11).
    {'farmer': ['NORTH'], 'hands': [['WEST'], ['WATER'], ['WEST']], 'market': []},
    # Step 108 (day 4, hour 12).
    {'farmer': ['WATER'], 'hands': [['SOUTH'], ['WEST'], ['WATER']], 'market': []},
    # Step 109 (day 4, hour 13).
    {'farmer': ['EAST'], 'hands': [['FEED', 'WHEAT'], ['NORTH'], ['HARVEST']], 'market': []},
    # Step 110 (day 4, hour 14).
    {'farmer': ['NORTH'], 'hands': [['CARE'], ['WATER'], ['PLANT', 'WHEAT']], 'market': []},
    # Step 111 (day 4, hour 15).
    {'farmer': ['WATER'], 'hands': [['COLLECT_FERTILIZER'], ['HARVEST'], ['WATER']], 'market': []},
    # Step 112 (day 4, hour 16).
    {'farmer': ['HARVEST'], 'hands': [['SOUTH'], ['PLANT', 'WHEAT'], ['WEST']], 'market': []},
    # Step 113 (day 4, hour 17).
    {'farmer': ['PASS'], 'hands': [['FEED', 'WHEAT'], ['WATER'], ['WATER']], 'market': []},
    # Step 114 (day 4, hour 18).
    {'farmer': ['PASS'], 'hands': [['CARE'], ['EAST'], ['HARVEST']], 'market': []},
    # Step 115 (day 4, hour 19).
    {'farmer': ['PASS'],
     'hands': [['COLLECT_FERTILIZER'], ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 116 (day 4, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['WATER']], 'market': []},
    # Step 117 (day 4, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 118 (day 4, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 119 (day 4, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PASS'], ['PASS']], 'market': []},
    # Step 120 (day 5, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WHEAT', 17], ['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_ANIMAL', 'COW', 1], ['BUY_SEED', 'WHEAT', 1], ['BUY_SEED', 'STRAWBERRY', 4]]},
    # Step 121 (day 5, hour 1).
    {'farmer': ['PICKUP', 'COW', 1],
     'hands': [['WEST'], ['WEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 122 (day 5, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['WEST']],
     'market': []},
    # Step 123 (day 5, hour 3).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['NORTH'], ['NORTH'], ['WEST']], 'market': []},
    # Step 124 (day 5, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 125 (day 5, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 126 (day 5, hour 6).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['PLANT', 'STRAWBERRY']],
     'market': []},
    # Step 127 (day 5, hour 7).
    {'farmer': ['WEST'], 'hands': [['NORTH'], ['WATER'], ['WATER']], 'market': []},
    # Step 128 (day 5, hour 8).
    {'farmer': ['BUILD_PASTURE'], 'hands': [['FEED', 'WHEAT'], ['WEST'], ['WEST']], 'market': []},
    # Step 129 (day 5, hour 9).
    {'farmer': ['PLACE', 'COW'],
     'hands': [['CARE'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 130 (day 5, hour 10).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 131 (day 5, hour 11).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 132 (day 5, hour 12).
    {'farmer': ['EAST'], 'hands': [['SOUTH'], ['EAST'], ['EAST']], 'market': []},
    # Step 133 (day 5, hour 13).
    {'farmer': ['CARE'], 'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['EAST']], 'market': []},
    # Step 134 (day 5, hour 14).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['PLANT', 'STRAWBERRY'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 135 (day 5, hour 15).
    {'farmer': ['PASS'], 'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['PASS']], 'market': []},
    # Step 136 (day 5, hour 16).
    {'farmer': ['PASS'], 'hands': [['SOUTH'], ['EAST'], ['PASS']], 'market': []},
    # Step 137 (day 5, hour 17).
    {'farmer': ['PASS'], 'hands': [['FEED', 'WHEAT'], ['PLANT', 'STRAWBERRY'], ['PASS']], 'market': []},
    # Step 138 (day 5, hour 18).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 139 (day 5, hour 19).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WEST'], ['PASS']], 'market': []},
    # Step 140 (day 5, hour 20).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WEST'], ['PASS']], 'market': []},
    # Step 141 (day 5, hour 21).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['SOUTH'], ['PASS']], 'market': []},
    # Step 142 (day 5, hour 22).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['PLANT', 'STRAWBERRY'], ['PASS']], 'market': []},
    # Step 143 (day 5, hour 23).
    {'farmer': ['PASS'], 'hands': [['PASS'], ['WATER'], ['PASS']], 'market': []},
    # Step 144 (day 6, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 145 (day 6, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 3], 'hands': [['WEST'], ['NORTH'], ['WEST']], 'market': []},
    # Step 146 (day 6, hour 2).
    {'farmer': ['HARVEST'], 'hands': [['PICKUP', 'WHEAT', 3], ['NORTH'], ['WEST']], 'market': []},
    # Step 147 (day 6, hour 3).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['NORTH'], ['NORTH'], ['WEST']], 'market': []},
    # Step 148 (day 6, hour 4).
    {'farmer': ['CARE'],
     'hands': [['HARVEST'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 149 (day 6, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['FEED', 'WHEAT'], ['WATER'], ['WEST']], 'market': []},
    # Step 150 (day 6, hour 6).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 151 (day 6, hour 7).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH']], 'market': []},
    # Step 152 (day 6, hour 8).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 153 (day 6, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['HARVEST'], ['WATER'], ['WATER']], 'market': []},
    # Step 154 (day 6, hour 10).
    {'farmer': ['WEST'], 'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH']], 'market': []},
    # Step 155 (day 6, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 156 (day 6, hour 12).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 157 (day 6, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'], 'hands': [['WEST'], ['WATER'], ['WATER']], 'market': []},
    # Step 158 (day 6, hour 14).
    {'farmer': ['EAST'], 'hands': [['SOUTH'], ['SOUTH'], ['EAST']], 'market': []},
    # Step 159 (day 6, hour 15).
    {'farmer': ['EAST'], 'hands': [['HARVEST'], ['WATER'], ['EAST']], 'market': []},
    # Step 160 (day 6, hour 16).
    {'farmer': ['DROP'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['EAST']],
     'market': [['SELL', 'WOOL', 5], ['SELL', 'FERTILIZER', 3], ['BUY_LAND']]},
    # Step 161 (day 6, hour 17).
    {'farmer': ['EAST'],
     'hands': [['CARE'], ['EAST'], ['EAST']],
     'market': [['HIRE'], ['BUY_ANIMAL', 'COW', 2], ['BUY_SEED', 'WHEAT', 1],
                ['BUY_SEED', 'STRAWBERRY', 3], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 162 (day 6, hour 18).
    {'farmer': ['PICKUP', 'COW', 2],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['EAST'], ['EAST']],
     'market': []},
    # Step 163 (day 6, hour 19).
    {'farmer': ['PICKUP', 'WHEAT', 2], 'hands': [['EAST'], ['WEST'], ['EAST'], ['EAST']], 'market': []},
    # Step 164 (day 6, hour 20).
    {'farmer': ['BUILD_PASTURE'],
     'hands': [['EAST'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['BUILD_PASTURE']],
     'market': []},
    # Step 165 (day 6, hour 21).
    {'farmer': ['PLACE', 'COW'], 'hands': [['NORTH'], ['PASS'], ['WATER'], ['EAST']], 'market': []},
    # Step 166 (day 6, hour 22).
    {'farmer': ['FEED', 'WHEAT'], 'hands': [['NORTH'], ['PASS'], ['EAST'], ['EAST']], 'market': []},
    # Step 167 (day 6, hour 23).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['PASS'], ['PLANT', 'STRAWBERRY'], ['NORTH']],
     'market': []},
    # Step 168 (day 7, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 15], ['SELL', 'FERTILIZER', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_ANIMAL', 'COW', 2]]},
    # Step 169 (day 7, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'COW', 3], ['WEST'], ['EAST'], ['PICKUP', 'WHEAT', 4], ['NORTH'], ['NORTH'],
               ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 3], ['BUY_SEED', 'STRAWBERRY', 9], ['BUY_PRODUCT', 'WHEAT', 5]]},
    # Step 170 (day 7, hour 2).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['NORTH'], ['NORTH'], ['NORTH'], ['NORTH'],
               ['NORTH']],
     'market': []},
    # Step 171 (day 7, hour 3).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'],
               ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 172 (day 7, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['NORTH'], ['NORTH'], ['CARE'], ['PLANT', 'STRAWBERRY'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 173 (day 7, hour 5).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['WATER'], ['NORTH']],
     'market': []},
    # Step 174 (day 7, hour 6).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['PLANT', 'STRAWBERRY'], ['NORTH'], ['EAST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 175 (day 7, hour 7).
    {'farmer': ['CARE'],
     'hands': [['BUILD_PASTURE'], ['WATER'], ['WATER'], ['FEED', 'WHEAT'], ['SOUTH'], ['WATER'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 176 (day 7, hour 8).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['PLACE', 'COW'], ['WEST'], ['EAST'], ['CARE'], ['PLANT', 'STRAWBERRY'], ['WEST'],
               ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 177 (day 7, hour 9).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['WATER'], ['WATER']],
     'market': []},
    # Step 178 (day 7, hour 10).
    {'farmer': ['NORTH'],
     'hands': [['CARE'], ['SOUTH'], ['WATER'], ['WEST'], ['EAST'], ['WEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 179 (day 7, hour 11).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['SOUTH'], ['PLANT', 'STRAWBERRY'], ['WATER'],
               ['WATER']],
     'market': []},
    # Step 180 (day 7, hour 12).
    {'farmer': ['WEST'],
     'hands': [['BUILD_PASTURE'], ['WEST'], ['PLANT', 'STRAWBERRY'], ['FEED', 'WHEAT'], ['WATER'],
               ['WEST'], ['EAST']],
     'market': []},
    # Step 181 (day 7, hour 13).
    {'farmer': ['SOUTH'],
     'hands': [['PLACE', 'COW'], ['WATER'], ['WATER'], ['CARE'], ['EAST'], ['WATER'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 182 (day 7, hour 14).
    {'farmer': ['WATER'],
     'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['EAST'], ['COLLECT_FERTILIZER'], ['PLANT', 'STRAWBERRY'],
               ['SOUTH'], ['EAST']],
     'market': []},
    # Step 183 (day 7, hour 15).
    {'farmer': ['EAST'],
     'hands': [['CARE'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['WEST'], ['WATER'], ['WATER'],
               ['PLANT', 'WHEAT']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 184 (day 7, hour 16).
    {'farmer': ['CARE'],
     'hands': [['EAST'], ['EAST'], ['WATER'], ['SOUTH'], ['WEST'], ['HARVEST'], ['WATER']],
     'market': []},
    # Step 185 (day 7, hour 17).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['SOUTH'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['PLANT', 'WHEAT'],
               ['EAST']],
     'market': []},
    # Step 186 (day 7, hour 18).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['NORTH'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['NORTH'], ['WATER'], ['EAST']],
     'market': []},
    # Step 187 (day 7, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PLACE', 'COW'], ['NORTH'], ['WATER'], ['PASS'], ['DIG'], ['NORTH'], ['EAST']],
     'market': []},
    # Step 188 (day 7, hour 20).
    {'farmer': ['PASS'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['SOUTH'], ['PASS'], ['PLANT', 'WHEAT'], ['NORTH'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 189 (day 7, hour 21).
    {'farmer': ['PASS'],
     'hands': [['CARE'], ['WATER'], ['SOUTH'], ['PASS'], ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 190 (day 7, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 191 (day 7, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 192 (day 8, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 7], ['SELL', 'WHEAT', 2], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['BUY_ANIMAL', 'COW', 2], ['BUY_SEED', 'WHEAT', 3]]},
    # Step 193 (day 8, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 4], ['NORTH'], ['EAST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'COW', 2], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 5], ['BUY_SEED', 'STRAWBERRY', 2], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 194 (day 8, hour 2).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['WEST'], ['PICKUP', 'WHEAT', 2], ['NORTH']],
     'market': []},
    # Step 195 (day 8, hour 3).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['NORTH'], ['NORTH'], ['HARVEST'], ['EAST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 196 (day 8, hour 4).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 197 (day 8, hour 5).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WATER'], ['NORTH'], ['CARE'], ['BUILD_PASTURE'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 198 (day 8, hour 6).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['PLACE', 'COW'],
               ['WATER']],
     'market': []},
    # Step 199 (day 8, hour 7).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['WATER'], ['WATER'], ['NORTH'], ['FEED', 'WHEAT'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 200 (day 8, hour 8).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['EAST'], ['FEED', 'WHEAT'], ['CARE'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 201 (day 8, hour 9).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['CARE'], ['EAST'], ['WATER']],
     'market': []},
    # Step 202 (day 8, hour 10).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 203 (day 8, hour 11).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WATER'], ['SOUTH'], ['EAST'], ['BUILD_PASTURE'], ['WATER']],
     'market': []},
    # Step 204 (day 8, hour 12).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['SOUTH'], ['NORTH'], ['PLACE', 'COW'], ['HARVEST']],
     'market': []},
    # Step 205 (day 8, hour 13).
    {'farmer': ['WATER'],
     'hands': [['EAST'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 206 (day 8, hour 14).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['NORTH'], ['PLANT', 'STRAWBERRY'], ['CARE'], ['CARE'], ['WATER']],
     'market': []},
    # Step 207 (day 8, hour 15).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 208 (day 8, hour 16).
    {'farmer': ['SOUTH'],
     'hands': [['FEED', 'WHEAT'], ['HARVEST'], ['EAST'], ['WEST'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': []},
    # Step 209 (day 8, hour 17).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['PLANT', 'WHEAT'], ['PLANT', 'STRAWBERRY'], ['WEST'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 210 (day 8, hour 18).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['SOUTH'], ['EAST'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 211 (day 8, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['EAST'], ['NORTH'], ['SOUTH'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': []},
    # Step 212 (day 8, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PLANT', 'WHEAT'], ['FEED', 'WHEAT'], ['WATER'], ['PASS']],
     'market': []},
    # Step 213 (day 8, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['HARVEST'], ['WATER'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 214 (day 8, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PLANT', 'WHEAT'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 215 (day 8, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 216 (day 9, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 10], ['SELL', 'WHEAT', 13], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 217 (day 9, hour 1).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['WEST'], ['NORTH'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['NORTH'], ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 218 (day 9, hour 2).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['HARVEST'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 219 (day 9, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'],
               ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 220 (day 9, hour 4).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['NORTH'], ['CARE'], ['CARE'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 221 (day 9, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['NORTH']],
     'market': []},
    # Step 222 (day 9, hour 6).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'], ['WATER']],
     'market': []},
    # Step 223 (day 9, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['WATER'], ['WATER'], ['HARVEST'], ['FEED', 'WHEAT'], ['WATER'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 224 (day 9, hour 8).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['EAST'], ['FEED', 'WHEAT'], ['CARE'], ['WEST'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 225 (day 9, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WATER'], ['SOUTH'], ['CARE'], ['COLLECT_FERTILIZER'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 226 (day 9, hour 10).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['EAST'], ['WEST'], ['WATER']],
     'market': []},
    # Step 227 (day 9, hour 11).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['NORTH'], ['SOUTH'], ['WATER'], ['EAST']],
     'market': []},
    # Step 228 (day 9, hour 12).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['EAST'], ['EAST'], ['HARVEST'], ['FEED', 'WHEAT'], ['WEST'], ['WATER']],
     'market': []},
    # Step 229 (day 9, hour 13).
    {'farmer': ['WATER'],
     'hands': [['EAST'], ['SOUTH'], ['EAST'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 230 (day 9, hour 14).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['SOUTH'], ['NORTH'], ['CARE'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 231 (day 9, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['COLLECT_FERTILIZER'], ['EAST'], ['SOUTH'], ['SOUTH']],
     'market': []},
    # Step 232 (day 9, hour 16).
    {'farmer': ['WATER'],
     'hands': [['WATER'], ['WEST'], ['SOUTH'], ['WEST'], ['SOUTH'], ['WATER'], ['WATER']],
     'market': []},
    # Step 233 (day 9, hour 17).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['HARVEST'], ['SOUTH']],
     'market': []},
    # Step 234 (day 9, hour 18).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['HARVEST'], ['CARE'], ['PLANT', 'WHEAT'], ['PASS']],
     'market': []},
    # Step 235 (day 9, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['PASS']],
     'market': []},
    # Step 236 (day 9, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['CARE'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 237 (day 9, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 238 (day 9, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 239 (day 9, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 240 (day 10, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 16], ['SELL', 'WHEAT', 2], ['BUY_LAND'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 241 (day 10, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_ANIMAL', 'COW', 1], ['BUY_SEED', 'MELON', 9], ['BUY_SEED', 'STRAWBERRY', 6]]},
    # Step 242 (day 10, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'COW', 1], ['WEST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['WEST'], ['NORTH'], ['EAST'], ['WEST'], ['WEST'],
               ['NORTH'], ['WEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 243 (day 10, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['PICKUP', 'WHEAT', 1], ['WEST'], ['NORTH'], ['NORTH'], ['SOUTH'],
               ['WEST'], ['NORTH'], ['EAST'], ['WEST'], ['WEST'], ['NORTH'], ['WEST'], ['WEST']],
     'market': []},
    # Step 244 (day 10, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['BUILD_PASTURE'], ['WEST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['PLANT', 'STRAWBERRY'], ['WEST'], ['NORTH'], ['NORTH'], ['SOUTH'], ['WEST'], ['NORTH'],
               ['NORTH'], ['NORTH']],
     'market': []},
    # Step 245 (day 10, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['PLACE', 'COW'], ['WEST'], ['CARE'], ['CARE'], ['WATER'],
               ['WEST'], ['WATER'], ['WATER'], ['SOUTH'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 246 (day 10, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['FEED', 'WHEAT'], ['WEST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WEST'], ['NORTH'], ['HARVEST'], ['EAST'], ['PLANT', 'STRAWBERRY'], ['WEST'], ['WATER'],
               ['NORTH'], ['NORTH']],
     'market': []},
    # Step 247 (day 10, hour 7).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['CARE'], ['SOUTH'], ['NORTH'], ['NORTH'], ['PLANT', 'STRAWBERRY'],
               ['NORTH'], ['PLANT', 'MELON'], ['WATER'], ['WATER'], ['NORTH'], ['WEST'], ['WATER'],
               ['NORTH']],
     'market': []},
    # Step 248 (day 10, hour 8).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['EAST'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WATER'],
               ['NORTH'], ['WATER'], ['EAST'], ['WEST'], ['NORTH'], ['WATER'], ['HARVEST'], ['WATER']],
     'market': []},
    # Step 249 (day 10, hour 9).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['PLANT', 'STRAWBERRY'], ['CARE'], ['CARE'],
               ['SOUTH'], ['NORTH'], ['SOUTH'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['NORTH'], ['WEST'],
               ['PLANT', 'MELON'], ['HARVEST']],
     'market': []},
    # Step 250 (day 10, hour 10).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['NORTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['PLANT', 'STRAWBERRY'], ['WATER'], ['SOUTH'], ['SOUTH'], ['WATER'], ['NORTH'],
               ['WATER'], ['WATER'], ['PLANT', 'MELON']],
     'market': []},
    # Step 251 (day 10, hour 11).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['NORTH'], ['SOUTH'], ['WEST'], ['EAST'], ['PASS'], ['HARVEST'], ['SOUTH'],
               ['WATER'], ['EAST'], ['WATER'], ['WEST'], ['EAST'], ['WATER']],
     'market': []},
    # Step 252 (day 10, hour 12).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['NORTH'], ['PASS'], ['SOUTH'], ['SOUTH'], ['EAST'], ['PLANT', 'MELON'],
               ['DROP'], ['WEST'], ['SOUTH'], ['HARVEST'], ['WATER'], ['SOUTH'], ['EAST']],
     'market': [['SELL', 'MELON', 6], ['BUY_SEED', 'MELON', 5], ['BUY_SEED', 'STRAWBERRY', 9],
                ['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 253 (day 10, hour 13).
    {'farmer': ['PLANT', 'MELON'],
     'hands': [['WEST'], ['NORTH'], ['PLANT', 'STRAWBERRY'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['PLANT', 'STRAWBERRY'], ['WATER'], ['EAST'], ['WATER'], ['PLANT', 'STRAWBERRY'],
               ['PLANT', 'MELON'], ['WEST'], ['SOUTH'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 6]]},
    # Step 254 (day 10, hour 14).
    {'farmer': ['WATER'],
     'hands': [['SOUTH'], ['WATER'], ['WATER'], ['CARE'], ['CARE'], ['WATER'], ['EAST'], ['EAST'],
               ['WEST'], ['WATER'], ['WATER'], ['WATER'], ['SOUTH'], ['SOUTH']],
     'market': []},
    # Step 255 (day 10, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['PLANT', 'MELON'], ['EAST'], ['EAST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['SOUTH'], ['EAST'], ['NORTH'], ['WEST'], ['SOUTH'], ['EAST'], ['SOUTH'], ['DROP'],
               ['SOUTH']],
     'market': [['SELL', 'MELON', 6], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 256 (day 10, hour 16).
    {'farmer': ['PLANT', 'MELON'],
     'hands': [['WATER'], ['EAST'], ['PLANT', 'STRAWBERRY'], ['SOUTH'], ['EAST'],
               ['PLANT', 'STRAWBERRY'], ['EAST'], ['NORTH'], ['NORTH'], ['PLANT', 'STRAWBERRY'],
               ['EAST'], ['SOUTH'], ['WEST'], ['SOUTH']],
     'market': []},
    # Step 257 (day 10, hour 17).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['WATER'], ['WATER'], ['HARVEST'], ['SOUTH'], ['WATER'], ['SOUTH'], ['NORTH'],
               ['NORTH'], ['WATER'], ['EAST'], ['WATER'], ['CARE'], ['DROP']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 258 (day 10, hour 18).
    {'farmer': ['EAST'],
     'hands': [['PLANT', 'MELON'], ['EAST'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['PASS'],
               ['SOUTH'], ['NORTH'], ['NORTH'], ['EAST'], ['EAST'], ['PASS'], ['COLLECT_FERTILIZER'],
               ['PASS']],
     'market': []},
    # Step 259 (day 10, hour 19).
    {'farmer': ['PLANT', 'MELON'],
     'hands': [['WATER'], ['WATER'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['CARE'], ['PASS'], ['SOUTH'],
               ['WATER'], ['NORTH'], ['PLANT', 'STRAWBERRY'], ['SOUTH'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 260 (day 10, hour 20).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['PASS'], ['WATER'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['DROP'],
               ['PASS'], ['PASS'], ['WATER'], ['SOUTH'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 261 (day 10, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PLANT', 'MELON'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['BUY_SEED', 'STRAWBERRY', 2]]},
    # Step 262 (day 10, hour 22).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PASS'], ['PLANT', 'STRAWBERRY'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['DROP'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 263 (day 10, hour 23).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['WATER'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 264 (day 11, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 265 (day 11, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': [['HIRE']]},
    # Step 266 (day 11, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['EAST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['NORTH'], ['WEST'], ['NORTH'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 4]]},
    # Step 267 (day 11, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'],
               ['NORTH'], ['NORTH'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 268 (day 11, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['CARE'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['NORTH'], ['NORTH'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 269 (day 11, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['CARE'], ['CARE'],
               ['PLANT', 'STRAWBERRY'], ['NORTH'], ['WATER'], ['WATER'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 270 (day 11, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WEST'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['NORTH'], ['WEST'], ['EAST'], ['NORTH']],
     'market': []},
    # Step 271 (day 11, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['EAST'], ['NORTH'], ['NORTH'], ['WEST'], ['WATER'],
               ['WATER'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 272 (day 11, hour 8).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['NORTH'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['PLANT', 'STRAWBERRY'], ['HARVEST'], ['WEST'], ['EAST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 273 (day 11, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['NORTH'], ['CARE'], ['CARE'], ['WATER'],
               ['PLANT', 'WHEAT'], ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 274 (day 11, hour 10).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WEST'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['WATER'], ['SOUTH'], ['EAST'], ['HARVEST']],
     'market': []},
    # Step 275 (day 11, hour 11).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WEST'], ['HARVEST'], ['WEST'], ['EAST'], ['PLANT', 'MELON'], ['EAST'],
               ['WATER'], ['WATER'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 276 (day 11, hour 12).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['PLANT', 'WHEAT'], ['SOUTH'], ['SOUTH'], ['WATER'], ['EAST'],
               ['WEST'], ['EAST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 277 (day 11, hour 13).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['EAST'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['EAST'],
               ['SOUTH'], ['SOUTH'], ['WATER'], ['NORTH']],
     'market': [['SELL', 'WHEAT', 3]]},
    # Step 278 (day 11, hour 14).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['EAST'], ['EAST'], ['CARE'], ['CARE'], ['EAST'], ['SOUTH'], ['WATER'],
               ['NORTH'], ['NORTH']],
     'market': []},
    # Step 279 (day 11, hour 15).
    {'farmer': ['WATER'],
     'hands': [['WATER'], ['SOUTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['NORTH'], ['SOUTH'], ['EAST'], ['WATER'], ['WATER']],
     'market': []},
    # Step 280 (day 11, hour 16).
    {'farmer': ['EAST'],
     'hands': [['EAST'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['WEST'], ['EAST'], ['PASS'], ['WATER'],
               ['PASS'], ['SOUTH'], ['EAST']],
     'market': []},
    # Step 281 (day 11, hour 17).
    {'farmer': ['CARE'],
     'hands': [['WATER'], ['PASS'], ['PLANT', 'WHEAT'], ['SOUTH'], ['SOUTH'], ['PASS'], ['EAST'],
               ['PASS'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 282 (day 11, hour 18).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['PASS'],
               ['WATER'], ['PASS'], ['PASS'], ['EAST']],
     'market': []},
    # Step 283 (day 11, hour 19).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PASS'], ['EAST'], ['PASS'], ['CARE'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['WATER']],
     'market': []},
    # Step 284 (day 11, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['EAST']],
     'market': []},
    # Step 285 (day 11, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['WATER']],
     'market': []},
    # Step 286 (day 11, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['EAST']],
     'market': []},
    # Step 287 (day 11, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['WATER']],
     'market': []},
    # Step 288 (day 12, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 13], ['SELL', 'WHEAT', 10], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 289 (day 12, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_ANIMAL', 'SHEEP', 2],
                ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 290 (day 12, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['EAST'], ['PICKUP', 'FERTILIZER', 2], ['EAST'],
               ['WEST'], ['WEST'], ['PICKUP', 'FERTILIZER', 1]],
     'market': [['BUY_SEED', 'WHEAT', 8]]},
    # Step 291 (day 12, hour 3).
    {'farmer': ['HARVEST'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'], ['NORTH'], ['NORTH'], ['WATER'],
               ['EAST'], ['NORTH'], ['EAST'], ['WEST'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 292 (day 12, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['CARE'], ['SOUTH'], ['HARVEST'], ['FEED', 'WHEAT'], ['SOUTH'], ['NORTH'],
               ['NORTH'], ['EAST'], ['WATER'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 293 (day 12, hour 5).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['FEED', 'WHEAT'], ['CARE'],
               ['WATER'], ['NORTH'], ['NORTH'], ['WATER'], ['WEST'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 294 (day 12, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WEST'], ['WATER'], ['CARE'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'],
               ['WATER'], ['EAST'], ['WATER'], ['NORTH'], ['FERTILIZE', 'FERTILIZER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 295 (day 12, hour 7).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['WEST'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'],
               ['HARVEST'], ['WEST'], ['WATER'], ['WEST'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 296 (day 12, hour 8).
    {'farmer': ['HARVEST'],
     'hands': [['CARE'], ['WEST'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['PLANT', 'WHEAT'], ['WATER'], ['WEST'], ['WATER'], ['WATER'], ['WEST']],
     'market': []},
    # Step 297 (day 12, hour 9).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['WATER'], ['HARVEST'], ['CARE'], ['WATER'], ['WATER'],
               ['WEST'], ['WEST'], ['EAST'], ['HARVEST'], ['WEST']],
     'market': []},
    # Step 298 (day 12, hour 10).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['NORTH'], ['WEST'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['EAST'], ['WATER'], ['WEST'], ['EAST'], ['PLANT', 'WHEAT'], ['NORTH']],
     'market': []},
    # Step 299 (day 12, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['NORTH'], ['WATER'], ['CARE'], ['EAST'], ['WATER'], ['WATER'], ['WEST'],
               ['NORTH'], ['SOUTH'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 300 (day 12, hour 12).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WATER'], ['NORTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['SOUTH'],
               ['HARVEST'], ['WATER'], ['NORTH'], ['SOUTH'], ['WEST'], ['WATER']],
     'market': []},
    # Step 301 (day 12, hour 13).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['EAST'], ['WATER'], ['WEST'], ['FEED', 'WHEAT'], ['PASS'],
               ['PLANT', 'WHEAT'], ['WEST'], ['NORTH'], ['WATER'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 302 (day 12, hour 14).
    {'farmer': ['CARE'],
     'hands': [['WATER'], ['SOUTH'], ['WEST'], ['SOUTH'], ['CARE'], ['SOUTH'], ['WATER'], ['WATER'],
               ['NORTH'], ['EAST'], ['HARVEST'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 303 (day 12, hour 15).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['PASS'], ['SOUTH'], ['WATER'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['WATER'], ['EAST'],
               ['EAST'], ['PASS'], ['SOUTH'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': []},
    # Step 304 (day 12, hour 16).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['SOUTH'], ['SOUTH'], ['EAST'], ['EAST'], ['EAST'], ['WATER'], ['SOUTH'],
               ['WEST'], ['EAST'], ['WATER'], ['WEST']],
     'market': []},
    # Step 305 (day 12, hour 17).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['SOUTH'], ['WATER'], ['SOUTH'], ['SOUTH'], ['WATER'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['SOUTH'], ['WEST'], ['WATER']],
     'market': []},
    # Step 306 (day 12, hour 18).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['SOUTH'], ['SOUTH'], ['DROP'], ['FEED', 'WHEAT'], ['PASS'],
               ['PLANT', 'WHEAT'], ['WATER'], ['WEST'], ['PASS'], ['WATER'], ['HARVEST']],
     'market': [['SELL', 'WOOL', 12]]},
    # Step 307 (day 12, hour 19).
    {'farmer': ['SOUTH'],
     'hands': [['SOUTH'], ['SOUTH'], ['WATER'], ['PICKUP', 'WHEAT', 1], ['CARE'], ['PASS'], ['WATER'],
               ['EAST'], ['PASS'], ['PASS'], ['HARVEST'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 308 (day 12, hour 20).
    {'farmer': ['SOUTH'],
     'hands': [['SOUTH'], ['WATER'], ['EAST'], ['WEST'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'],
               ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['PASS'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 309 (day 12, hour 21).
    {'farmer': ['WATER'],
     'hands': [['SOUTH'], ['PASS'], ['EAST'], ['NORTH'], ['PASS'], ['PASS'], ['PASS'], ['WATER'],
               ['SOUTH'], ['PASS'], ['WATER'], ['PASS']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 310 (day 12, hour 22).
    {'farmer': ['PASS'],
     'hands': [['CARE'], ['PASS'], ['PASS'], ['FEED', 'WHEAT'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['SOUTH'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 311 (day 12, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 312 (day 13, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 4], ['SELL', 'WHEAT', 25], ['SELL', 'FERTILIZER', 10],
                ['SELL', 'MILK', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 313 (day 13, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 314 (day 13, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['EAST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['WEST'], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 315 (day 13, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'],
               ['WEST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 316 (day 13, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['CARE'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 317 (day 13, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['CARE'], ['CARE'], ['WATER'],
               ['NORTH'], ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 318 (day 13, hour 6).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['EAST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['NORTH'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 319 (day 13, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['WATER'], ['NORTH'], ['NORTH'], ['WATER'], ['HARVEST'],
               ['WATER'], ['WATER']],
     'market': []},
    # Step 320 (day 13, hour 8).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['EAST'], ['EAST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WEST'], ['WEST'],
               ['SOUTH'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 321 (day 13, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'], ['CARE'], ['CARE'], ['WATER'], ['HARVEST'],
               ['WATER'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 322 (day 13, hour 10).
    {'farmer': ['EAST'],
     'hands': [['EAST'], ['NORTH'], ['NORTH'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['EAST'],
               ['WEST'], ['WEST'], ['SOUTH']],
     'market': []},
    # Step 323 (day 13, hour 11).
    {'farmer': ['EAST'],
     'hands': [['EAST'], ['NORTH'], ['WATER'], ['WEST'], ['EAST'], ['EAST'], ['WEST'], ['WATER'],
               ['WATER']],
     'market': []},
    # Step 324 (day 13, hour 12).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['SOUTH'], ['SOUTH'], ['NORTH'], ['WATER'], ['NORTH'],
               ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 4]]},
    # Step 325 (day 13, hour 13).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['EAST'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'],
               ['EAST'], ['EAST'], ['EAST']],
     'market': [['SELL', 'WHEAT', 4]]},
    # Step 326 (day 13, hour 14).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['EAST'], ['EAST'], ['CARE'], ['CARE'], ['CARE'], ['EAST'], ['NORTH'],
               ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 327 (day 13, hour 15).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['HARVEST'], ['SOUTH'], ['HARVEST'], ['NORTH']],
     'market': []},
    # Step 328 (day 13, hour 16).
    {'farmer': ['NORTH'],
     'hands': [['PASS'], ['PASS'], ['SOUTH'], ['WEST'], ['EAST'], ['COLLECT_FERTILIZER'], ['PASS'],
               ['WEST'], ['WATER']],
     'market': []},
    # Step 329 (day 13, hour 17).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['PASS'], ['WEST'], ['SOUTH'], ['SOUTH'], ['PASS'], ['PASS'], ['SOUTH'],
               ['PASS']],
     'market': [['BUY_SEED', 'STRAWBERRY', 1]]},
    # Step 330 (day 13, hour 18).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['PASS'], ['PASS'],
               ['WATER'], ['PASS']],
     'market': []},
    # Step 331 (day 13, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['CARE'], ['PASS'], ['PASS'], ['HARVEST'],
               ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 332 (day 13, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'],
               ['PLANT', 'WHEAT'], ['PASS']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 333 (day 13, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WATER'],
               ['PASS']],
     'market': []},
    # Step 334 (day 13, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': []},
    # Step 335 (day 13, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': []},
    # Step 336 (day 14, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'FERTILIZER', 13], ['SELL', 'STRAWBERRY', 6], ['SELL', 'MILK', 6],
                ['SELL', 'WHEAT', 4], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 337 (day 14, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 338 (day 14, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['EAST'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['PICKUP', 'FERTILIZER', 2],
               ['PICKUP', 'FERTILIZER', 2], ['WEST'], ['WEST']],
     'market': []},
    # Step 339 (day 14, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['FEED', 'WHEAT'], ['EAST'], ['NORTH'], ['HARVEST'], ['WATER'], ['SOUTH'],
               ['NORTH'], ['WEST'], ['WEST'], ['WEST']],
     'market': []},
    # Step 340 (day 14, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['CARE'], ['NORTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['SOUTH'], ['NORTH'], ['WEST'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 341 (day 14, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['COLLECT_FERTILIZER'], ['NORTH'], ['CARE'], ['CARE'], ['WATER'], ['SOUTH'],
               ['NORTH'], ['WEST'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 342 (day 14, hour 6).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['WATER'], ['WEST'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 343 (day 14, hour 7).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['NORTH'], ['EAST'], ['NORTH'], ['NORTH'], ['WATER'], ['WEST'], ['NORTH'],
               ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 344 (day 14, hour 8).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['SOUTH'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['NORTH'], ['SOUTH'], ['WEST'],
               ['WATER'], ['WATER'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 345 (day 14, hour 9).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['EAST'], ['CARE'], ['FEED', 'WHEAT'], ['WATER'],
               ['WATER'], ['WEST'], ['WEST'], ['EAST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 346 (day 14, hour 10).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['NORTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['CARE'], ['WEST'], ['WEST'],
               ['SOUTH'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 347 (day 14, hour 11).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['SOUTH'], ['WEST'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['WATER'], ['WATER'], ['WATER'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 348 (day 14, hour 12).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['SOUTH'], ['EAST'], ['SOUTH'], ['NORTH'], ['SOUTH'],
               ['NORTH'], ['SOUTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 4]]},
    # Step 349 (day 14, hour 13).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['EAST'], ['WEST'], ['FEED', 'WHEAT'], ['SOUTH'], ['PASS'], ['WATER'],
               ['WATER'], ['NORTH'], ['WATER'], ['WATER']],
     'market': [['SELL', 'WHEAT', 4]]},
    # Step 350 (day 14, hour 14).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['EAST'], ['WATER'], ['CARE'], ['FEED', 'WHEAT'], ['SOUTH'], ['WEST'],
               ['WEST'], ['WATER'], ['EAST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 351 (day 14, hour 15).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'], ['CARE'], ['WATER'], ['WATER'],
               ['SOUTH'], ['NORTH'], ['SOUTH'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 352 (day 14, hour 16).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['EAST'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['WEST'], ['SOUTH'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['EAST'], ['SOUTH']],
     'market': []},
    # Step 353 (day 14, hour 17).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['WATER'], ['EAST'], ['HARVEST'], ['EAST'], ['WATER'], ['WATER'], ['WATER'],
               ['EAST'], ['SOUTH'], ['EAST']],
     'market': []},
    # Step 354 (day 14, hour 18).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['CARE'], ['FEED', 'WHEAT'], ['SOUTH'], ['WEST'], ['SOUTH'],
               ['WEST'], ['PASS'], ['WATER'], ['SOUTH']],
     'market': []},
    # Step 355 (day 14, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['CARE'], ['FEED', 'WHEAT'], ['WATER'],
               ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['PASS'], ['PASS'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 356 (day 14, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'], ['PASS'],
               ['WATER'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 357 (day 14, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 358 (day 14, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 359 (day 14, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 360 (day 15, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 9], ['SELL', 'FERTILIZER', 9], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 361 (day 15, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 362 (day 15, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 3],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['NORTH'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['NORTH'], ['WEST'], ['PICKUP', 'FERTILIZER', 1],
               ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 4]]},
    # Step 363 (day 15, hour 3).
    {'farmer': ['HARVEST'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['NORTH'], ['WEST'],
               ['NORTH'], ['NORTH'], ['EAST'], ['WEST']],
     'market': []},
    # Step 364 (day 15, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['CARE'], ['NORTH'], ['NORTH'], ['HARVEST'], ['SOUTH'], ['NORTH'], ['NORTH'],
               ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 365 (day 15, hour 5).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['HARVEST'],
               ['FEED', 'WHEAT'], ['WATER'], ['NORTH'], ['HARVEST'], ['NORTH'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 366 (day 15, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['CARE'], ['WEST'], ['NORTH'],
               ['WEST'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 367 (day 15, hour 7).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['NORTH'], ['EAST'], ['CARE'], ['COLLECT_FERTILIZER'], ['WATER'], ['WATER'],
               ['SOUTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 368 (day 15, hour 8).
    {'farmer': ['HARVEST'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WEST'],
               ['HARVEST'], ['HARVEST'], ['NORTH'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 369 (day 15, hour 9).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['NORTH'], ['EAST'], ['WEST'], ['HARVEST'], ['WATER'], ['PLANT', 'WHEAT'],
               ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['NORTH']],
     'market': [['SELL', 'WHEAT', 3]]},
    # Step 370 (day 15, hour 10).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['EAST'],
               ['WATER'], ['SOUTH'], ['WATER'], ['WATER']],
     'market': []},
    # Step 371 (day 15, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['HARVEST'], ['CARE'], ['EAST'], ['EAST'], ['HARVEST'],
               ['EAST'], ['HARVEST']],
     'market': []},
    # Step 372 (day 15, hour 12).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WEST'], ['WATER'], ['FEED', 'WHEAT'], ['SOUTH'], ['NORTH'], ['EAST'],
               ['NORTH'], ['WATER'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 373 (day 15, hour 13).
    {'farmer': ['SOUTH'],
     'hands': [['WATER'], ['WATER'], ['EAST'], ['CARE'], ['SOUTH'], ['NORTH'], ['SOUTH'], ['NORTH'],
               ['HARVEST'], ['WATER']],
     'market': []},
    # Step 374 (day 15, hour 14).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['EAST'], ['WATER'], ['COLLECT_FERTILIZER'], ['DROP'], ['CARE'], ['SOUTH'],
               ['NORTH'], ['PLANT', 'WHEAT'], ['EAST']],
     'market': [['SELL', 'MILK', 12]]},
    # Step 375 (day 15, hour 15).
    {'farmer': ['CARE'],
     'hands': [['WATER'], ['EAST'], ['NORTH'], ['WEST'], ['PICKUP', 'WHEAT', 2], ['HARVEST'], ['SOUTH'],
               ['NORTH'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 376 (day 15, hour 16).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['EAST'], ['WATER'], ['SOUTH'], ['NORTH'], ['EAST'], ['WATER'], ['WATER'],
               ['EAST'], ['EAST']],
     'market': []},
    # Step 377 (day 15, hour 17).
    {'farmer': ['EAST'],
     'hands': [['WATER'], ['SOUTH'], ['SOUTH'], ['FEED', 'WHEAT'], ['NORTH'], ['EAST'], ['EAST'],
               ['WEST'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 378 (day 15, hour 18).
    {'farmer': ['DROP'],
     'hands': [['WEST'], ['SOUTH'], ['PASS'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['EAST'],
               ['WATER'], ['WATER'], ['HARVEST'], ['WEST']],
     'market': [['SELL', 'WOOL', 8], ['SELL', 'FERTILIZER', 3]]},
    # Step 379 (day 15, hour 19).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['SOUTH'], ['PASS'], ['WEST'], ['EAST'], ['EAST'], ['EAST'], ['EAST'],
               ['PLANT', 'WHEAT'], ['SOUTH']],
     'market': []},
    # Step 380 (day 15, hour 20).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['CARE'], ['PASS'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['EAST'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 381 (day 15, hour 21).
    {'farmer': ['CARE'],
     'hands': [['SOUTH'], ['COLLECT_FERTILIZER'], ['PASS'], ['HARVEST'], ['FEED', 'WHEAT'], ['PASS'],
               ['PASS'], ['WATER'], ['PASS'], ['WEST']],
     'market': []},
    # Step 382 (day 15, hour 22).
    {'farmer': ['HARVEST'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['SOUTH'], ['WEST'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': []},
    # Step 383 (day 15, hour 23).
    {'farmer': ['WEST'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['FEED', 'WHEAT'], ['DROP'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': [['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 1]]},
    # Step 384 (day 16, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 8], ['SELL', 'STRAWBERRY', 14], ['SELL', 'MILK', 6],
                ['SELL', 'FERTILIZER', 8], ['SELL', 'WHEAT', 9], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE']]},
    # Step 385 (day 16, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['BUY_SEED', 'WHEAT', 3]]},
    # Step 386 (day 16, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 2],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['NORTH'], ['PICKUP', 'WHEAT', 4],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['EAST'], ['PICKUP', 'FERTILIZER', 3],
               ['PICKUP', 'FERTILIZER', 4], ['WEST'], ['WEST'], ['NORTH'], ['PICKUP', 'FERTILIZER', 5],
               ['SOUTH']],
     'market': [['BUY_SEED', 'WHEAT', 5], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 387 (day 16, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['FEED', 'WHEAT'], ['PICKUP', 'FERTILIZER', 1], ['NORTH'], ['HARVEST'],
               ['WATER'], ['EAST'], ['WEST'], ['EAST'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH'],
               ['SOUTH']],
     'market': []},
    # Step 388 (day 16, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['CARE'], ['EAST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['NORTH'], ['NORTH'], ['EAST'], ['WATER'], ['NORTH'], ['NORTH'], ['NORTH'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 389 (day 16, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['COLLECT_FERTILIZER'], ['NORTH'], ['CARE'], ['CARE'], ['WATER'], ['NORTH'],
               ['NORTH'], ['EAST'], ['WEST'], ['NORTH'], ['WATER'], ['NORTH'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 390 (day 16, hour 6).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WEST'], ['NORTH'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['WATER'],
               ['WATER'], ['NORTH'], ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['WEST']],
     'market': []},
    # Step 391 (day 16, hour 7).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['EAST'], ['WATER'],
               ['HARVEST'], ['WATER'], ['EAST'], ['WEST'], ['NORTH'], ['WEST'], ['WATER'], ['WEST']],
     'market': []},
    # Step 392 (day 16, hour 8).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['WATER'], ['WATER'], ['WATER'], ['SOUTH'], ['EAST'],
               ['WATER']],
     'market': []},
    # Step 393 (day 16, hour 9).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['NORTH'], ['EAST'], ['CARE'], ['CARE'], ['WATER'], ['WATER'], ['WATER'],
               ['NORTH'], ['EAST'], ['HARVEST'], ['SOUTH'], ['FERTILIZE', 'FERTILIZER'], ['WEST']],
     'market': []},
    # Step 394 (day 16, hour 10).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['EAST'], ['COLLECT_FERTILIZER'],
               ['COLLECT_FERTILIZER'], ['WEST'], ['WEST'], ['WEST'], ['NORTH'], ['EAST'],
               ['PLANT', 'WHEAT'], ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 395 (day 16, hour 11).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['NORTH'], ['SOUTH'], ['WEST'], ['NORTH'], ['WATER'], ['NORTH'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['WATER'], ['WEST'], ['EAST'], ['NORTH']],
     'market': []},
    # Step 396 (day 16, hour 12).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['NORTH'], ['WATER'], ['SOUTH'], ['HARVEST'], ['SOUTH'], ['NORTH'], ['WEST'],
               ['WATER'], ['SOUTH'], ['WEST'], ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['WATER']],
     'market': []},
    # Step 397 (day 16, hour 13).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['WATER'], ['HARVEST'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['PASS'],
               ['NORTH'], ['WATER'], ['NORTH'], ['WATER'], ['WATER'], ['WEST'], ['WATER'], ['WEST']],
     'market': []},
    # Step 398 (day 16, hour 14).
    {'farmer': ['WATER'],
     'hands': [['WATER'], ['HARVEST'], ['PLANT', 'WHEAT'], ['CARE'], ['CARE'], ['SOUTH'], ['HARVEST'],
               ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['HARVEST'], ['SOUTH'], ['SOUTH'],
               ['WATER']],
     'market': []},
    # Step 399 (day 16, hour 15).
    {'farmer': ['EAST'],
     'hands': [['EAST'], ['PLANT', 'WHEAT'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WATER'], ['EAST'], ['WATER'], ['WATER'], ['SOUTH'], ['PLANT', 'WHEAT'], ['NORTH'],
               ['FERTILIZE', 'FERTILIZER'], ['SOUTH']],
     'market': []},
    # Step 400 (day 16, hour 16).
    {'farmer': ['NORTH'],
     'hands': [['SOUTH'], ['WATER'], ['EAST'], ['SOUTH'], ['EAST'], ['WEST'], ['EAST'], ['EAST'],
               ['NORTH'], ['EAST'], ['WATER'], ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 401 (day 16, hour 17).
    {'farmer': ['NORTH'],
     'hands': [['SOUTH'], ['WEST'], ['WATER'], ['HARVEST'], ['SOUTH'], ['WATER'], ['SOUTH'], ['SOUTH'],
               ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['WEST'], ['PASS'], ['EAST'], ['SOUTH']],
     'market': []},
    # Step 402 (day 16, hour 18).
    {'farmer': ['WATER'],
     'hands': [['CARE'], ['WATER'], ['HARVEST'], ['FEED', 'WHEAT'], ['HARVEST'], ['WEST'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WATER'], ['WEST'], ['PASS'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER']],
     'market': []},
    # Step 403 (day 16, hour 19).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['HARVEST'], ['PLANT', 'WHEAT'], ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'],
               ['WATER'], ['PASS'], ['EAST'], ['WEST'], ['PASS'], ['WEST'], ['PASS'], ['WATER'],
               ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 404 (day 16, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PLANT', 'WHEAT'], ['WATER'], ['PASS'], ['CARE'], ['PASS'], ['PASS'],
               ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['PASS'], ['WATER'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 405 (day 16, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['PASS'],
               ['PASS'], ['FERTILIZE', 'FERTILIZER'], ['PASS'], ['HARVEST'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': []},
    # Step 406 (day 16, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WEST'], ['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 407 (day 16, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PLANT', 'WHEAT'], ['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 408 (day 17, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'MILK', 18], ['SELL', 'WHEAT', 25], ['SELL', 'STRAWBERRY', 2], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 409 (day 17, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['BUY_SEED', 'WHEAT', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 410 (day 17, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['EAST'], ['PICKUP', 'SHEEP', 1],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['WEST'], ['PICKUP', 'FERTILIZER', 2]],
     'market': []},
    # Step 411 (day 17, hour 3).
    {'farmer': ['NORTH'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'], ['PICKUP', 'WHEAT', 3], ['NORTH'],
               ['WEST'], ['WEST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 412 (day 17, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['CARE'], ['NORTH'], ['FEED', 'WHEAT'], ['HARVEST'], ['SOUTH'], ['WEST'],
               ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 413 (day 17, hour 5).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['CARE'], ['FEED', 'WHEAT'],
               ['WATER'], ['WEST'], ['HARVEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 414 (day 17, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['EAST'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['CARE'], ['WEST'], ['WEST'],
               ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 415 (day 17, hour 7).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['NORTH'], ['WEST'], ['WEST'], ['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'],
               ['NORTH'], ['WATER']],
     'market': []},
    # Step 416 (day 17, hour 8).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WEST'], ['FEED', 'WHEAT'], ['NORTH'], ['WEST'],
               ['NORTH'], ['NORTH'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 417 (day 17, hour 9).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['NORTH'], ['WEST'], ['CARE'], ['HARVEST'], ['WATER'], ['NORTH'], ['WATER'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2], ['SELL', 'WHEAT', 2]]},
    # Step 418 (day 17, hour 10).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['HARVEST'], ['COLLECT_FERTILIZER'],
               ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['EAST'], ['EAST']],
     'market': []},
    # Step 419 (day 17, hour 11).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['HARVEST'], ['WEST'], ['WEST'], ['CARE'], ['WATER'], ['WATER'], ['EAST'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 420 (day 17, hour 12).
    {'farmer': ['SOUTH'],
     'hands': [['CARE'], ['EAST'], ['HARVEST'], ['WEST'], ['COLLECT_FERTILIZER'], ['EAST'], ['EAST'],
               ['SOUTH'], ['EAST']],
     'market': []},
    # Step 421 (day 17, hour 13).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['HARVEST'], ['HARVEST'], ['WEST'], ['WEST'], ['EAST'], ['WATER'], ['WATER'], ['SOUTH'],
               ['WATER']],
     'market': []},
    # Step 422 (day 17, hour 14).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['EAST'], ['HARVEST'], ['NORTH'], ['SOUTH'], ['EAST'], ['EAST'], ['CARE'],
               ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 423 (day 17, hour 15).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['HARVEST'], ['SOUTH'], ['NORTH'], ['FEED', 'WHEAT'], ['WATER'], ['WATER'],
               ['HARVEST'], ['SOUTH']],
     'market': []},
    # Step 424 (day 17, hour 16).
    {'farmer': ['WEST'],
     'hands': [['SOUTH'], ['EAST'], ['HARVEST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['EAST'], ['EAST'],
               ['COLLECT_FERTILIZER'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 425 (day 17, hour 17).
    {'farmer': ['SOUTH'],
     'hands': [['COLLECT_FERTILIZER'], ['HARVEST'], ['WEST'], ['NORTH'], ['SOUTH'], ['WATER'],
               ['WATER'], ['NORTH'], ['SOUTH']],
     'market': []},
    # Step 426 (day 17, hour 18).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['EAST'], ['WATER'], ['DIG'], ['WEST'], ['SOUTH'], ['EAST'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER']],
     'market': []},
    # Step 427 (day 17, hour 19).
    {'farmer': ['PASS'],
     'hands': [['NORTH'], ['HARVEST'], ['HARVEST'], ['BUILD_PASTURE'], ['DROP'], ['WATER'], ['WATER'],
               ['PASS'], ['WATER']],
     'market': [['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 428 (day 17, hour 20).
    {'farmer': ['PASS'],
     'hands': [['NORTH'], ['NORTH'], ['PLANT', 'WHEAT'], ['PLACE', 'SHEEP'], ['PICKUP', 'WHEAT', 1],
               ['EAST'], ['PASS'], ['EAST'], ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 429 (day 17, hour 21).
    {'farmer': ['PASS'],
     'hands': [['HARVEST'], ['HARVEST'], ['WATER'], ['FEED', 'WHEAT'], ['EAST'], ['WATER'], ['PASS'],
               ['EAST'], ['FERTILIZE', 'FERTILIZER']],
     'market': []},
    # Step 430 (day 17, hour 22).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['SOUTH'], ['SOUTH'], ['CARE'], ['FEED', 'WHEAT'], ['PASS'], ['PASS'],
               ['SOUTH'], ['WATER']],
     'market': []},
    # Step 431 (day 17, hour 23).
    {'farmer': ['PASS'],
     'hands': [['HARVEST'], ['SOUTH'], ['HARVEST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['DROP'],
               ['PASS']],
     'market': [['SELL', 'STRAWBERRY', 4], ['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 1]]},
    # Step 432 (day 18, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 28], ['SELL', 'FERTILIZER', 9], ['SELL', 'MILK', 3],
                ['SELL', 'WHEAT', 2], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 433 (day 18, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 434 (day 18, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['PICKUP', 'WHEAT', 3], ['NORTH'], ['SOUTH'],
               ['EAST'], ['PICKUP', 'FERTILIZER', 4], ['WEST']],
     'market': []},
    # Step 435 (day 18, hour 3).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['HARVEST'], ['WEST'], ['NORTH'], ['HARVEST'], ['WATER'], ['NORTH'],
               ['HARVEST'], ['NORTH'], ['SOUTH'], ['EAST'], ['WEST'], ['WEST']],
     'market': []},
    # Step 436 (day 18, hour 4).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WEST'], ['HARVEST'], ['FEED', 'WHEAT'], ['WEST'],
               ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['WATER'], ['NORTH'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 437 (day 18, hour 5).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['CARE'], ['SOUTH'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'], ['NORTH'],
               ['CARE'], ['WATER'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 4]]},
    # Step 438 (day 18, hour 6).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['CARE'],
               ['COLLECT_FERTILIZER'], ['WEST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'],
               ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 439 (day 18, hour 7).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['EAST'], ['WATER'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['WATER'],
               ['WEST'], ['WATER'], ['SOUTH'], ['NORTH'], ['WATER'], ['WEST']],
     'market': []},
    # Step 440 (day 18, hour 8).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['WEST'], ['WEST'],
               ['HARVEST'], ['SOUTH'], ['PASS'], ['WATER'], ['WEST'], ['WATER']],
     'market': []},
    # Step 441 (day 18, hour 9).
    {'farmer': ['WATER'],
     'hands': [['CARE'], ['EAST'], ['WATER'], ['HARVEST'], ['CARE'], ['WATER'], ['WATER'],
               ['FEED', 'WHEAT'], ['WATER'], ['EAST'], ['EAST'], ['FERTILIZE', 'FERTILIZER'],
               ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 442 (day 18, hour 10).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['EAST'], ['WEST'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'],
               ['EAST'], ['WEST'], ['CARE'], ['EAST'], ['WATER'], ['WATER'], ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 443 (day 18, hour 11).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['NORTH'], ['WATER'], ['CARE'], ['NORTH'], ['EAST'], ['WATER'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['SOUTH'], ['EAST'], ['SOUTH'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 444 (day 18, hour 12).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['HARVEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['EAST'],
               ['WEST'], ['WEST'], ['SOUTH'], ['WATER'], ['WATER'], ['FERTILIZE', 'FERTILIZER'],
               ['NORTH']],
     'market': []},
    # Step 445 (day 18, hour 13).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['EAST'], ['WATER'], ['WEST'], ['FEED', 'WHEAT'], ['EAST'], ['WATER'],
               ['WEST'], ['WATER'], ['WEST'], ['NORTH'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 446 (day 18, hour 14).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['HARVEST'], ['EAST'], ['SOUTH'], ['CARE'], ['SOUTH'], ['WEST'], ['WEST'],
               ['EAST'], ['WATER'], ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 447 (day 18, hour 15).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['WEST'], ['WATER'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['WATER'], ['WATER'],
               ['NORTH'], ['WATER'], ['NORTH'], ['SOUTH'], ['EAST'], ['EAST']],
     'market': []},
    # Step 448 (day 18, hour 16).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['NORTH'], ['EAST'], ['FEED', 'WHEAT'], ['EAST'], ['WEST'], ['SOUTH'],
               ['NORTH'], ['WEST'], ['NORTH'], ['SOUTH'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 449 (day 18, hour 17).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['NORTH'], ['WATER'], ['CARE'], ['SOUTH'], ['WATER'], ['WATER'], ['NORTH'],
               ['WEST'], ['NORTH'], ['WATER'], ['NORTH'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 450 (day 18, hour 18).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['NORTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['PASS'], ['PASS'],
               ['NORTH'], ['NORTH'], ['WEST'], ['HARVEST'], ['PASS'], ['EAST']],
     'market': []},
    # Step 451 (day 18, hour 19).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'], ['PASS'], ['WEST'], ['PASS'], ['PASS'],
               ['FEED', 'WHEAT'], ['NORTH'], ['WEST'], ['WEST'], ['PASS'], ['WATER']],
     'market': []},
    # Step 452 (day 18, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['WEST'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PASS'],
               ['NORTH'], ['WEST'], ['WATER'], ['PASS'], ['PASS']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 453 (day 18, hour 21).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WEST'], ['WATER'], ['PASS'], ['DROP'], ['PASS'], ['PASS'], ['PASS'],
               ['HARVEST'], ['WATER'], ['EAST'], ['PASS'], ['PASS']],
     'market': [['SELL', 'MILK', 9]]},
    # Step 454 (day 18, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['WATER'], ['WEST'], ['PASS'], ['EAST'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['SOUTH'], ['PASS'], ['PASS']],
     'market': []},
    # Step 455 (day 18, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['WATER'], ['PASS'], ['EAST'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['WATER'], ['PASS'], ['PASS']],
     'market': []},
    # Step 456 (day 19, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 16], ['SELL', 'MILK', 9], ['SELL', 'STRAWBERRY', 8],
                ['SELL', 'FERTILIZER', 9], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 457 (day 19, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 458 (day 19, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['PICKUP', 'FERTILIZER', 4], ['NORTH'], ['WEST'],
               ['PICKUP', 'FERTILIZER', 1], ['PICKUP', 'FERTILIZER', 5], ['WEST'], ['WEST'], ['NORTH'],
               ['PICKUP', 'FERTILIZER', 6]],
     'market': [['BUY_SEED', 'WHEAT', 3]]},
    # Step 459 (day 19, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WEST'], ['WEST'], ['NORTH'], ['WEST'], ['NORTH'],
               ['NORTH'], ['EAST'], ['WEST'], ['WEST'], ['WEST'], ['NORTH'], ['SOUTH']],
     'market': []},
    # Step 460 (day 19, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['CARE'], ['WATER'], ['FEED', 'WHEAT'], ['HARVEST'], ['WEST'], ['NORTH'],
               ['NORTH'], ['EAST'], ['SOUTH'], ['WEST'], ['NORTH'], ['NORTH'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 461 (day 19, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['WEST'], ['CARE'], ['FEED', 'WHEAT'],
               ['SOUTH'], ['NORTH'], ['HARVEST'], ['EAST'], ['WATER'], ['WEST'], ['NORTH'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 462 (day 19, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['NORTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['CARE'], ['WATER'], ['NORTH'],
               ['DIG'], ['WATER'], ['WEST'], ['WEST'], ['HARVEST'], ['EAST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 463 (day 19, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['NORTH'], ['WEST'], ['WEST'], ['COLLECT_FERTILIZER'], ['WEST'], ['WATER'],
               ['PLANT', 'WHEAT'], ['EAST'], ['WEST'], ['NORTH'], ['DIG'], ['HARVEST'], ['WEST']],
     'market': []},
    # Step 464 (day 19, hour 8).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WATER'], ['HARVEST'], ['NORTH'], ['WATER'], ['HARVEST'],
               ['WATER'], ['WATER'], ['SOUTH'], ['NORTH'], ['PLANT', 'WHEAT'], ['EAST'],
               ['FERTILIZE', 'FERTILIZER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 465 (day 19, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['NORTH'], ['WEST'], ['FEED', 'WHEAT'], ['HARVEST'], ['WEST'],
               ['PLANT', 'WHEAT'], ['WEST'], ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['WATER'],
               ['WATER'], ['HARVEST'], ['WATER']],
     'market': []},
    # Step 466 (day 19, hour 10).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'], ['CARE'], ['FEED', 'WHEAT'], ['WATER'],
               ['WATER'], ['SOUTH'], ['WEST'], ['WATER'], ['NORTH'], ['WEST'], ['EAST'], ['WEST']],
     'market': []},
    # Step 467 (day 19, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['COLLECT_FERTILIZER'], ['CARE'], ['SOUTH'], ['EAST'],
               ['HARVEST'], ['WEST'], ['SOUTH'], ['NORTH'], ['HARVEST'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER']],
     'market': []},
    # Step 468 (day 19, hour 12).
    {'farmer': ['CARE'],
     'hands': [['WATER'], ['WEST'], ['EAST'], ['WEST'], ['COLLECT_FERTILIZER'],
               ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['WEST'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'],
               ['WATER'], ['DIG'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 469 (day 19, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WATER'], ['EAST'], ['WEST'], ['EAST'], ['WATER'], ['WATER'], ['SOUTH'],
               ['NORTH'], ['WATER'], ['EAST'], ['PLANT', 'WHEAT'], ['HARVEST'], ['EAST']],
     'market': []},
    # Step 470 (day 19, hour 14).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['WEST'], ['EAST'], ['NORTH'], ['SOUTH'], ['SOUTH'], ['HARVEST'], ['HARVEST'],
               ['NORTH'], ['EAST'], ['WATER'], ['WATER'], ['WEST'], ['SOUTH']],
     'market': []},
    # Step 471 (day 19, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['WEST'], ['SOUTH'], ['NORTH'], ['FEED', 'WHEAT'], ['FERTILIZE', 'FERTILIZER'],
               ['PLANT', 'WHEAT'], ['WEST'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['WEST'],
               ['HARVEST'], ['PASS']],
     'market': []},
    # Step 472 (day 19, hour 16).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['WATER'], ['WEST'], ['WATER'], ['NORTH'], ['CARE'], ['WATER'], ['WATER'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['WATER'], ['WATER'], ['WEST'], ['PASS']],
     'market': []},
    # Step 473 (day 19, hour 17).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['CARE'], ['SOUTH'], ['NORTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'],
               ['EAST'], ['WATER'], ['SOUTH'], ['EAST'], ['HARVEST'], ['HARVEST'], ['EAST']],
     'market': []},
    # Step 474 (day 19, hour 18).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['HARVEST'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['FEED', 'WHEAT'], ['SOUTH'],
               ['FERTILIZE', 'FERTILIZER'], ['WATER'], ['NORTH'], ['EAST'], ['FERTILIZE', 'FERTILIZER'],
               ['WATER'], ['PLANT', 'WHEAT'], ['EAST'], ['FERTILIZE', 'FERTILIZER']],
     'market': []},
    # Step 475 (day 19, hour 19).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['EAST'], ['SOUTH'], ['EAST'], ['HARVEST'], ['WATER'], ['HARVEST'], ['NORTH'],
               ['EAST'], ['WATER'], ['EAST'], ['WATER'], ['PASS'], ['WATER']],
     'market': []},
    # Step 476 (day 19, hour 20).
    {'farmer': ['WEST'],
     'hands': [['HARVEST'], ['WATER'], ['WATER'], ['EAST'], ['WEST'], ['EAST'], ['PLANT', 'WHEAT'],
               ['NORTH'], ['EAST'], ['EAST'], ['WATER'], ['EAST'], ['WEST'], ['SOUTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 477 (day 19, hour 21).
    {'farmer': ['HARVEST'],
     'hands': [['NORTH'], ['EAST'], ['PASS'], ['PASS'], ['DROP'], ['FERTILIZE', 'FERTILIZER'],
               ['WATER'], ['PASS'], ['PASS'], ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['SOUTH'],
               ['SOUTH'], ['FERTILIZE', 'FERTILIZER']],
     'market': [['SELL', 'MILK', 9]]},
    # Step 478 (day 19, hour 22).
    {'farmer': ['PASS'],
     'hands': [['HARVEST'], ['WATER'], ['PASS'], ['PASS'], ['EAST'], ['WATER'], ['EAST'], ['PASS'],
               ['PASS'], ['WATER'], ['WEST'], ['PASS'], ['SOUTH'], ['PASS']],
     'market': []},
    # Step 479 (day 19, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['CARE'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS']],
     'market': []},
    # Step 480 (day 20, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 34], ['SELL', 'MILK', 3], ['SELL', 'WHEAT', 9], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 481 (day 20, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_SEED', 'WHEAT', 45]]},
    # Step 482 (day 20, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['WEST'], ['PICKUP', 'FERTILIZER', 5],
               ['SOUTH'], ['WEST'], ['NORTH'], ['PICKUP', 'FERTILIZER', 5], ['WEST']],
     'market': []},
    # Step 483 (day 20, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['HARVEST'], ['WEST'], ['WEST'], ['HARVEST'], ['WATER'], ['WEST'], ['WEST'],
               ['NORTH'], ['WATER'], ['WEST'], ['NORTH'], ['EAST'], ['WEST']],
     'market': []},
    # Step 484 (day 20, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['HARVEST'], ['WEST'], ['NORTH'], ['NORTH'], ['HARVEST'], ['NORTH'], ['NORTH'], ['EAST'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 485 (day 20, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['CARE'], ['WATER'], ['FEED', 'WHEAT'], ['CARE'], ['PLANT', 'WHEAT'], ['WEST'],
               ['WATER'], ['NORTH'], ['PLANT', 'WHEAT'], ['NORTH'], ['WATER'], ['NORTH'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 486 (day 20, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['CARE'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['WEST'], ['FERTILIZE', 'FERTILIZER'],
               ['WATER'], ['NORTH'], ['HARVEST'], ['NORTH'], ['PLANT', 'WHEAT']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 487 (day 20, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['WEST'], ['PLANT', 'WHEAT'], ['COLLECT_FERTILIZER'], ['NORTH'], ['EAST'],
               ['HARVEST'], ['WATER'], ['WATER'], ['NORTH'], ['NORTH'], ['PLANT', 'WHEAT'], ['NORTH'],
               ['WATER']],
     'market': []},
    # Step 488 (day 20, hour 8).
    {'farmer': ['CARE'],
     'hands': [['SOUTH'], ['WEST'], ['WATER'], ['EAST'], ['NORTH'], ['DROP'], ['PLANT', 'WHEAT'],
               ['SOUTH'], ['EAST'], ['DROP'], ['WATER'], ['WATER'], ['FERTILIZE', 'FERTILIZER'],
               ['EAST']],
     'market': [['SELL', 'MELON', 12], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 489 (day 20, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['FEED', 'WHEAT'], ['WEST'], ['EAST'], ['NORTH'], ['FEED', 'WHEAT'], ['WEST'], ['WATER'],
               ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['HARVEST'], ['SOUTH'], ['WATER'],
               ['EAST']],
     'market': []},
    # Step 490 (day 20, hour 10).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WEST'], ['NORTH'], ['NORTH'], ['CARE'], ['WEST'], ['EAST'], ['WEST'],
               ['WATER'], ['WEST'], ['PLANT', 'WHEAT'], ['SOUTH'], ['EAST'], ['DROP']],
     'market': [['SELL', 'MELON', 6], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 491 (day 20, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['DROP'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'],
               ['NORTH'], ['EAST'], ['WATER'], ['SOUTH'], ['WEST'], ['WATER'], ['SOUTH'],
               ['FERTILIZE', 'FERTILIZER'], ['WEST']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 492 (day 20, hour 12).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['HARVEST'], ['PICKUP', 'FERTILIZER', 2], ['CARE'], ['EAST'], ['NORTH'],
               ['EAST'], ['EAST'], ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['EAST'], ['DROP'],
               ['WATER'], ['WEST']],
     'market': [['SELL', 'MELON', 6], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 493 (day 20, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['PLANT', 'WHEAT'], ['WEST'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['NORTH'],
               ['DROP'], ['NORTH'], ['WATER'], ['NORTH'], ['SOUTH'], ['NORTH'], ['EAST'], ['WEST']],
     'market': [['SELL', 'MELON', 6]]},
    # Step 494 (day 20, hour 14).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WATER'], ['WEST'], ['WEST'], ['HARVEST'], ['NORTH'], ['SOUTH'], ['NORTH'],
               ['EAST'], ['NORTH'], ['SOUTH'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['WEST']],
     'market': []},
    # Step 495 (day 20, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['NORTH'], ['EAST'], ['SOUTH'], ['WEST'], ['FEED', 'WHEAT'], ['WATER'], ['SOUTH'],
               ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['SOUTH'], ['NORTH'], ['WATER'],
               ['NORTH']],
     'market': []},
    # Step 496 (day 20, hour 16).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['HARVEST'], ['EAST'], ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['CARE'], ['HARVEST'],
               ['HARVEST'], ['NORTH'], ['WATER'], ['WATER'], ['DROP'], ['NORTH'], ['NORTH'],
               ['NORTH']],
     'market': [['SELL', 'MELON', 6], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 497 (day 20, hour 17).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['EAST'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'], ['PLANT', 'WHEAT'],
               ['WEST'], ['WATER'], ['EAST'], ['HARVEST'], ['EAST'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 498 (day 20, hour 18).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['EAST'], ['WEST'], ['NORTH'], ['EAST'], ['WATER'], ['HARVEST'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER'], ['PLANT', 'WHEAT'], ['EAST'], ['HARVEST'], ['WATER'],
               ['NORTH']],
     'market': []},
    # Step 499 (day 20, hour 19).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['DROP'], ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['SOUTH'], ['EAST'],
               ['WEST'], ['PLANT', 'WHEAT'], ['WATER'], ['WATER'], ['EAST'], ['PLANT', 'WHEAT'],
               ['SOUTH'], ['WATER']],
     'market': [['SELL', 'MELON', 6], ['SELL', 'MILK', 3], ['BUY_SEED', 'WHEAT', 2]]},
    # Step 500 (day 20, hour 20).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['SOUTH'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['EAST'],
               ['HARVEST'], ['WATER'], ['EAST'], ['EAST'], ['NORTH'], ['WATER'], ['SOUTH'],
               ['HARVEST']],
     'market': []},
    # Step 501 (day 20, hour 21).
    {'farmer': ['NORTH'],
     'hands': [['HARVEST'], ['SOUTH'], ['WEST'], ['CARE'], ['CARE'], ['SOUTH'], ['WEST'], ['EAST'],
               ['WATER'], ['EAST'], ['WATER'], ['WEST'], ['FERTILIZE', 'FERTILIZER'],
               ['PLANT', 'WHEAT']],
     'market': []},
    # Step 502 (day 20, hour 22).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['SOUTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['SOUTH'], ['HARVEST'], ['PASS'], ['SOUTH'], ['EAST'], ['HARVEST'], ['PLANT', 'WHEAT'],
               ['PASS'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 503 (day 20, hour 23).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['HARVEST'], ['SOUTH'], ['PASS'], ['WEST'], ['SOUTH'], ['EAST'], ['PASS'],
               ['WATER'], ['SOUTH'], ['PLANT', 'WHEAT'], ['WATER'], ['PASS'], ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 504 (day 21, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 12], ['SELL', 'MILK', 9], ['SELL', 'MELON', 18],
                ['SELL', 'WHEAT', 14], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 505 (day 21, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_SEED', 'WHEAT', 1]]},
    # Step 506 (day 21, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'FERTILIZER', 2], ['WEST'], ['WEST'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 507 (day 21, hour 3).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['NORTH'], ['SOUTH'],
               ['WEST'], ['HARVEST'], ['EAST'], ['WEST'], ['WEST'], ['NORTH'], ['NORTH']],
     'market': []},
    # Step 508 (day 21, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['CARE'], ['WEST'], ['NORTH'], ['HARVEST'], ['WATER'], ['WEST'],
               ['FEED', 'WHEAT'], ['EAST'], ['SOUTH'], ['WEST'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 509 (day 21, hour 5).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['HARVEST'],
               ['FEED', 'WHEAT'], ['WEST'], ['WEST'], ['CARE'], ['EAST'], ['HARVEST'], ['NORTH'],
               ['WATER'], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 1], ['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 510 (day 21, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['EAST'], ['SOUTH'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'], ['SOUTH'],
               ['COLLECT_FERTILIZER'], ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['NORTH'], ['WEST'],
               ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 511 (day 21, hour 7).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WATER'], ['CARE'], ['COLLECT_FERTILIZER'], ['EAST'],
               ['SOUTH'], ['NORTH'], ['WATER'], ['SOUTH'], ['NORTH'], ['WATER'], ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 2], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 512 (day 21, hour 8).
    {'farmer': ['NORTH'],
     'hands': [['CARE'], ['NORTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['NORTH'], ['SOUTH'], ['WATER'],
               ['HARVEST'], ['HARVEST'], ['WATER'], ['NORTH'], ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 513 (day 21, hour 9).
    {'farmer': ['HARVEST'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['HARVEST'], ['WEST'], ['HARVEST'], ['WATER'],
               ['WEST'], ['FEED', 'WHEAT'], ['NORTH'], ['WEST'], ['NORTH'], ['WATER'], ['EAST']],
     'market': []},
    # Step 514 (day 21, hour 10).
    {'farmer': ['DIG'],
     'hands': [['EAST'], ['NORTH'], ['EAST'], ['SOUTH'], ['FEED', 'WHEAT'], ['WEST'], ['WATER'],
               ['CARE'], ['DIG'], ['WATER'], ['DIG'], ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 515 (day 21, hour 11).
    {'farmer': ['PLANT', 'WHEAT'],
     'hands': [['EAST'], ['HARVEST'], ['PASS'], ['HARVEST'], ['CARE'], ['WEST'], ['HARVEST'],
               ['COLLECT_FERTILIZER'], ['PLANT', 'WHEAT'], ['WEST'], ['PLANT', 'WHEAT'], ['WATER'],
               ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 516 (day 21, hour 12).
    {'farmer': ['WATER'],
     'hands': [['EAST'], ['EAST'], ['HARVEST'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['SOUTH'], ['WEST'], ['WATER'], ['WATER'], ['WATER'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 517 (day 21, hour 13).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['HARVEST'], ['SOUTH'], ['CARE'], ['EAST'], ['WEST'], ['HARVEST'], ['WEST'],
               ['EAST'], ['SOUTH'], ['WEST'], ['WATER'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 518 (day 21, hour 14).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['EAST'], ['WATER'], ['EAST'], ['SOUTH'], ['NORTH'], ['EAST'], ['WEST'],
               ['SOUTH'], ['WATER'], ['WEST'], ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 519 (day 21, hour 15).
    {'farmer': ['HARVEST'],
     'hands': [['WEST'], ['HARVEST'], ['HARVEST'], ['SOUTH'], ['WEST'], ['NORTH'], ['HARVEST'],
               ['WEST'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['CARE'], ['PLANT', 'WHEAT'],
               ['SOUTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 520 (day 21, hour 16).
    {'farmer': ['DIG'],
     'hands': [['CARE'], ['SOUTH'], ['WEST'], ['DROP'], ['SOUTH'], ['WATER'], ['SOUTH'], ['EAST'],
               ['HARVEST'], ['PASS'], ['PASS'], ['WATER'], ['HARVEST']],
     'market': [['SELL', 'WOOL', 8]]},
    # Step 521 (day 21, hour 17).
    {'farmer': ['PLANT', 'WHEAT'],
     'hands': [['WEST'], ['HARVEST'], ['WATER'], ['PICKUP', 'WHEAT', 1], ['DROP'], ['HARVEST'],
               ['WATER'], ['EAST'], ['NORTH'], ['EAST'], ['EAST'], ['EAST'], ['WEST']],
     'market': [['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 1]]},
    # Step 522 (day 21, hour 18).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WEST'], ['HARVEST'], ['WEST'], ['PICKUP', 'WHEAT', 2], ['PLANT', 'WHEAT'],
               ['HARVEST'], ['EAST'], ['DIG'], ['EAST'], ['EAST'], ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 523 (day 21, hour 19).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WEST'], ['EAST'], ['NORTH'], ['EAST'], ['WATER'], ['WEST'], ['EAST'],
               ['PLANT', 'WHEAT'], ['PASS'], ['PASS'], ['DIG'], ['SOUTH']],
     'market': []},
    # Step 524 (day 21, hour 20).
    {'farmer': ['HARVEST'],
     'hands': [['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'], ['COLLECT_FERTILIZER'], ['NORTH'], ['EAST'],
               ['HARVEST'], ['SOUTH'], ['WATER'], ['PASS'], ['PASS'], ['PLANT', 'WHEAT'], ['HARVEST']],
     'market': []},
    # Step 525 (day 21, hour 21).
    {'farmer': ['DIG'],
     'hands': [['PASS'], ['SOUTH'], ['NORTH'], ['WEST'], ['FEED', 'WHEAT'], ['HARVEST'], ['PASS'],
               ['DROP'], ['PASS'], ['PASS'], ['PASS'], ['WATER'], ['WEST']],
     'market': [['SELL', 'WOOL', 8], ['SELL', 'FERTILIZER', 2]]},
    # Step 526 (day 21, hour 22).
    {'farmer': ['PLANT', 'WHEAT'],
     'hands': [['PASS'], ['DROP'], ['NORTH'], ['SOUTH'], ['EAST'], ['PASS'], ['PASS'], ['WEST'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WEST']],
     'market': [['SELL', 'STRAWBERRY', 8], ['SELL', 'FERTILIZER', 1]]},
    # Step 527 (day 21, hour 23).
    {'farmer': ['WATER'],
     'hands': [['PASS'], ['EAST'], ['NORTH'], ['HARVEST'], ['SOUTH'], ['PASS'], ['PASS'], ['WEST'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WEST']],
     'market': []},
    # Step 528 (day 22, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 42], ['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 5],
                ['SELL', 'MELON', 6], ['SELL', 'WHEAT', 3], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE']]},
    # Step 529 (day 22, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 530 (day 22, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['EAST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['EAST'], ['NORTH'], ['NORTH'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 531 (day 22, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['HARVEST'], ['NORTH'], ['WEST'], ['HARVEST'], ['WATER'], ['EAST'], ['NORTH'],
               ['NORTH'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 532 (day 22, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['WEST'], ['EAST'], ['NORTH'], ['NORTH'], ['HARVEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 533 (day 22, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['CARE'], ['NORTH'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'], ['NORTH'],
               ['WATER'], ['WATER'], ['WEST'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 534 (day 22, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['WATER'], ['CARE'],
               ['COLLECT_FERTILIZER'], ['WEST'], ['HARVEST'], ['NORTH'], ['EAST'], ['HARVEST'],
               ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 535 (day 22, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['EAST'],
               ['WATER'], ['EAST'], ['SOUTH'], ['HARVEST']],
     'market': []},
    # Step 536 (day 22, hour 8).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['EAST'], ['FEED', 'WHEAT'], ['WEST'],
               ['HARVEST'], ['WEST'], ['SOUTH'], ['HARVEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 537 (day 22, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['NORTH'], ['WATER'], ['NORTH'], ['CARE'], ['WATER'], ['WEST'], ['WATER'],
               ['WATER'], ['EAST'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 538 (day 22, hour 10).
    {'farmer': ['WEST'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['EAST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['EAST'],
               ['WEST'], ['SOUTH'], ['WEST'], ['HARVEST'], ['WEST']],
     'market': []},
    # Step 539 (day 22, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['WATER'], ['WATER'], ['FEED', 'WHEAT'], ['NORTH'], ['SOUTH'], ['WEST'],
               ['WATER'], ['NORTH'], ['WEST'], ['HARVEST']],
     'market': []},
    # Step 540 (day 22, hour 12).
    {'farmer': ['CARE'],
     'hands': [['EAST'], ['WEST'], ['EAST'], ['CARE'], ['HARVEST'], ['WATER'], ['WEST'], ['WEST'],
               ['NORTH'], ['SOUTH'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 541 (day 22, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['SOUTH'], ['WATER'], ['WATER'], ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'], ['EAST'],
               ['NORTH'], ['WATER'], ['HARVEST'], ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 542 (day 22, hour 14).
    {'farmer': ['WEST'],
     'hands': [['DIG'], ['WEST'], ['EAST'], ['WEST'], ['WEST'], ['WATER'], ['NORTH'], ['WEST'], ['DIG'],
               ['EAST'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 543 (day 22, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['PLANT', 'WHEAT'], ['WATER'], ['WATER'], ['WEST'], ['SOUTH'], ['EAST'], ['NORTH'],
               ['WATER'], ['PLANT', 'WHEAT'], ['DIG'], ['HARVEST']],
     'market': []},
    # Step 544 (day 22, hour 16).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['WATER'], ['WEST'], ['NORTH'], ['WEST'], ['DROP'], ['WATER'], ['NORTH'], ['NORTH'],
               ['WATER'], ['NORTH'], ['EAST']],
     'market': [['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 2]]},
    # Step 545 (day 22, hour 17).
    {'farmer': ['CARE'],
     'hands': [['EAST'], ['NORTH'], ['WATER'], ['WEST'], ['PICKUP', 'WHEAT', 1], ['EAST'], ['WATER'],
               ['WATER'], ['EAST'], ['NORTH'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 546 (day 22, hour 18).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['WATER'], ['SOUTH'], ['NORTH'], ['EAST'], ['WATER'], ['PASS'], ['WEST'],
               ['WATER'], ['NORTH'], ['SOUTH']],
     'market': []},
    # Step 547 (day 22, hour 19).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['NORTH'], ['SOUTH'], ['NORTH'], ['NORTH'], ['PASS'], ['PASS'], ['SOUTH'],
               ['EAST'], ['NORTH'], ['HARVEST']],
     'market': []},
    # Step 548 (day 22, hour 20).
    {'farmer': ['PASS'],
     'hands': [['WEST'], ['CARE'], ['WATER'], ['FEED', 'WHEAT'], ['CARE'], ['PASS'], ['PASS'],
               ['SOUTH'], ['WATER'], ['DROP'], ['WEST']],
     'market': [['SELL', 'STRAWBERRY', 10]]},
    # Step 549 (day 22, hour 21).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['PASS'], ['PASS'], ['WATER'], ['PASS'], ['SOUTH'], ['HARVEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 550 (day 22, hour 22).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['PASS'], ['PASS'], ['EAST'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 551 (day 22, hour 23).
    {'farmer': ['PASS'],
     'hands': [['CARE'], ['PASS'], ['PASS'], ['PASS'], ['SOUTH'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['SOUTH'], ['HARVEST']],
     'market': []},
    # Step 552 (day 23, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 28], ['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 11],
                ['SELL', 'WHEAT', 1], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 553 (day 23, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 554 (day 23, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'SHEEP', 1], ['PICKUP', 'WHEAT', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['PICKUP', 'FERTILIZER', 5], ['WEST'], ['WEST'], ['EAST'],
               ['PICKUP', 'FERTILIZER', 5], ['EAST'], ['WEST'], ['NORTH'],
               ['PICKUP', 'FERTILIZER', 4]],
     'market': []},
    # Step 555 (day 23, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['PICKUP', 'WHEAT', 2], ['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['NORTH'], ['WEST'],
               ['WEST'], ['WEST'], ['EAST'], ['WEST'], ['EAST'], ['NORTH'], ['NORTH'], ['SOUTH']],
     'market': []},
    # Step 556 (day 23, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['CARE'], ['WEST'], ['NORTH'], ['HARVEST'], ['WEST'], ['WEST'],
               ['NORTH'], ['EAST'], ['WEST'], ['NORTH'], ['NORTH'], ['NORTH'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 557 (day 23, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['SOUTH'], ['NORTH'], ['WATER'], ['WATER'], ['WEST'], ['NORTH'], ['WATER'], ['HARVEST'],
               ['FERTILIZE', 'FERTILIZER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 558 (day 23, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['EAST'], ['HARVEST'], ['CARE'], ['CARE'], ['SOUTH'], ['NORTH'],
               ['WEST'], ['NORTH'], ['WEST'], ['NORTH'], ['HARVEST'], ['DIG'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 559 (day 23, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['EAST'], ['WEST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['WATER'], ['WATER'], ['SOUTH'], ['NORTH'],
               ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 560 (day 23, hour 8).
    {'farmer': ['CARE'],
     'hands': [['EAST'], ['EAST'], ['HARVEST'], ['WEST'], ['NORTH'], ['WATER'], ['WATER'], ['WEST'],
               ['EAST'], ['SOUTH'], ['HARVEST'], ['WATER'], ['WATER'], ['FERTILIZE', 'FERTILIZER']],
     'market': []},
    # Step 561 (day 23, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['PLACE', 'SHEEP'], ['NORTH'], ['NORTH'], ['SOUTH'], ['HARVEST'], ['WEST'], ['HARVEST'],
               ['WATER'], ['WATER'], ['FERTILIZE', 'FERTILIZER'], ['DIG'], ['NORTH'], ['EAST'],
               ['WATER']],
     'market': []},
    # Step 562 (day 23, hour 10).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['FERTILIZE', 'FERTILIZER'], ['PLANT', 'WHEAT'], ['SOUTH'], ['SOUTH'], ['WATER'],
               ['PLANT', 'WHEAT'], ['WATER'], ['SOUTH'], ['SOUTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 563 (day 23, hour 11).
    {'farmer': ['SOUTH'],
     'hands': [['CARE'], ['NORTH'], ['WEST'], ['CARE'], ['CARE'], ['WATER'], ['WATER'], ['WATER'],
               ['WATER'], ['SOUTH'], ['WATER'], ['NORTH'], ['HARVEST'], ['PASS']],
     'market': []},
    # Step 564 (day 23, hour 12).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['WEST'], ['NORTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['EAST'],
               ['WEST'], ['EAST'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'], ['EAST'], ['WATER'], ['DIG'],
               ['PASS']],
     'market': []},
    # Step 565 (day 23, hour 13).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['NORTH'], ['EAST'], ['WEST'], ['EAST'], ['SOUTH'], ['WATER'], ['WATER'],
               ['NORTH'], ['WATER'], ['HARVEST'], ['EAST'], ['PLANT', 'WHEAT'], ['EAST']],
     'market': []},
    # Step 566 (day 23, hour 14).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['WEST'], ['SOUTH'], ['FERTILIZE', 'FERTILIZER'],
               ['HARVEST'], ['EAST'], ['NORTH'], ['EAST'], ['DIG'], ['WATER'], ['WATER'],
               ['FERTILIZE', 'FERTILIZER']],
     'market': []},
    # Step 567 (day 23, hour 15).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['HARVEST'], ['WATER'], ['WEST'], ['FEED', 'WHEAT'], ['WATER'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['NORTH'], ['FERTILIZE', 'FERTILIZER'],
               ['PLANT', 'WHEAT'], ['SOUTH'], ['EAST'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 568 (day 23, hour 16).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['PLANT', 'WHEAT'], ['EAST'], ['NORTH'], ['CARE'], ['SOUTH'], ['WATER'],
               ['NORTH'], ['HARVEST'], ['WATER'], ['WATER'], ['WATER'], ['HARVEST'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 569 (day 23, hour 17).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['NORTH'], ['COLLECT_FERTILIZER'],
               ['FERTILIZE', 'FERTILIZER'], ['WEST'], ['NORTH'], ['DIG'], ['SOUTH'], ['EAST'], ['WEST'],
               ['DIG'], ['WEST']],
     'market': []},
    # Step 570 (day 23, hour 18).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WATER'], ['EAST'], ['SOUTH'], ['NORTH'], ['SOUTH'], ['WATER'], ['WATER'], ['NORTH'],
               ['PLANT', 'WHEAT'], ['FERTILIZE', 'FERTILIZER'], ['SOUTH'], ['WEST'], ['PLANT', 'WHEAT'],
               ['WEST']],
     'market': []},
    # Step 571 (day 23, hour 19).
    {'farmer': ['PASS'],
     'hands': [['HARVEST'], ['WATER'], ['WATER'], ['HARVEST'], ['HARVEST'], ['EAST'], ['HARVEST'],
               ['WATER'], ['WATER'], ['WATER'], ['HARVEST'], ['WATER'], ['WATER'], ['WEST']],
     'market': []},
    # Step 572 (day 23, hour 20).
    {'farmer': ['PASS'],
     'hands': [['PLANT', 'WHEAT'], ['HARVEST'], ['EAST'], ['FEED', 'WHEAT'], ['WEST'],
               ['FERTILIZE', 'FERTILIZER'], ['PLANT', 'WHEAT'], ['WEST'], ['SOUTH'], ['WEST'], ['DIG'],
               ['WEST'], ['WEST'], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 573 (day 23, hour 21).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PLANT', 'WHEAT'], ['WATER'], ['CARE'], ['DROP'], ['WATER'], ['WATER'],
               ['WATER'], ['HARVEST'], ['FERTILIZE', 'FERTILIZER'], ['PLANT', 'WHEAT'], ['WATER'],
               ['SOUTH'], ['NORTH']],
     'market': [['SELL', 'MILK', 11], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 574 (day 23, hour 22).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['WATER'], ['PASS'], ['COLLECT_FERTILIZER'], ['EAST'], ['EAST'], ['NORTH'],
               ['PASS'], ['PASS'], ['WATER'], ['WATER'], ['PASS'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 575 (day 23, hour 23).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['EAST'], ['PASS'], ['PASS'], ['CARE'], ['PLANT', 'WHEAT'], ['WATER'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS']],
     'market': []},
    # Step 576 (day 24, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 5], ['SELL', 'WHEAT', 20], ['SELL', 'FERTILIZER', 2],
                ['SELL', 'STRAWBERRY', 20], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE']]},
    # Step 577 (day 24, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'FERTILIZER', 1], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['HIRE'], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 578 (day 24, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['PICKUP', 'FERTILIZER', 2], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['EAST'], ['WEST'], ['WEST'], ['NORTH'], ['EAST']],
     'market': []},
    # Step 579 (day 24, hour 3).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['HARVEST'], ['SOUTH'], ['NORTH'], ['HARVEST'], ['WEST'], ['NORTH'],
               ['HARVEST'], ['EAST'], ['WATER'], ['WEST'], ['NORTH'], ['EAST']],
     'market': []},
    # Step 580 (day 24, hour 4).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['NORTH'], ['HARVEST'], ['WEST'], ['NORTH'],
               ['EAST']],
     'market': []},
    # Step 581 (day 24, hour 5).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['CARE'], ['HARVEST'], ['FEED', 'WHEAT'], ['CARE'], ['SOUTH'], ['NORTH'],
               ['CARE'], ['WATER'], ['PLANT', 'WHEAT'], ['WEST'], ['WATER'], ['HARVEST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 582 (day 24, hour 6).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['WEST'], ['CARE'],
               ['COLLECT_FERTILIZER'], ['FERTILIZE', 'FERTILIZER'], ['NORTH'], ['COLLECT_FERTILIZER'],
               ['WEST'], ['WATER'], ['NORTH'], ['HARVEST'], ['DIG']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 583 (day 24, hour 7).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['WEST'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'], ['NORTH'],
               ['WEST'], ['NORTH'], ['WEST'], ['NORTH'], ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT']],
     'market': [['SELL', 'FERTILIZER', 1], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 584 (day 24, hour 8).
    {'farmer': ['SOUTH'],
     'hands': [['SOUTH'], ['WEST'], ['SOUTH'], ['NORTH'], ['NORTH'], ['WEST'], ['WATER'], ['HARVEST'],
               ['NORTH'], ['WATER'], ['NORTH'], ['WATER'], ['WATER']],
     'market': []},
    # Step 585 (day 24, hour 9).
    {'farmer': ['SOUTH'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['HARVEST'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['FERTILIZE', 'FERTILIZER'], ['HARVEST'], ['FEED', 'WHEAT'], ['NORTH'], ['HARVEST'],
               ['NORTH'], ['WEST'], ['EAST']],
     'market': []},
    # Step 586 (day 24, hour 10).
    {'farmer': ['SOUTH'],
     'hands': [['CARE'], ['NORTH'], ['EAST'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'],
               ['PLANT', 'WHEAT'], ['CARE'], ['WATER'], ['PLANT', 'WHEAT'], ['WATER'], ['WATER'],
               ['HARVEST']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 587 (day 24, hour 11).
    {'farmer': ['HARVEST'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['HARVEST'], ['CARE'], ['COLLECT_FERTILIZER'],
               ['NORTH'], ['WATER'], ['COLLECT_FERTILIZER'], ['EAST'], ['WATER'], ['HARVEST'],
               ['HARVEST'], ['DIG']],
     'market': []},
    # Step 588 (day 24, hour 12).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['WEST'], ['WEST'], ['SOUTH'], ['EAST'], ['WATER'], ['WEST'], ['EAST'],
               ['EAST'], ['EAST'], ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT']],
     'market': [['SELL', 'FERTILIZER', 1], ['BUY_SEED', 'WHEAT', 2], ['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 589 (day 24, hour 13).
    {'farmer': ['HARVEST'],
     'hands': [['CARE'], ['SOUTH'], ['SOUTH'], ['SOUTH'], ['SOUTH'], ['HARVEST'], ['WATER'], ['DROP'],
               ['EAST'], ['SOUTH'], ['WATER'], ['WATER'], ['WATER']],
     'market': [['SELL', 'WOOL', 4], ['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 2],
                ['SELL', 'WHEAT', 2]]},
    # Step 590 (day 24, hour 14).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['WATER'], ['HARVEST'], ['DROP'], ['HARVEST'], ['PLANT', 'WHEAT'], ['HARVEST'],
               ['PICKUP', 'WHEAT', 1], ['SOUTH'], ['WATER'], ['NORTH'], ['WEST'], ['NORTH']],
     'market': [['SELL', 'WOOL', 8], ['SELL', 'FERTILIZER', 1], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 591 (day 24, hour 15).
    {'farmer': ['HARVEST'],
     'hands': [['SOUTH'], ['EAST'], ['EAST'], ['PICKUP', 'WHEAT', 1], ['WEST'], ['WATER'],
               ['PLANT', 'WHEAT'], ['WEST'], ['DIG'], ['HARVEST'], ['WATER'], ['WEST'], ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 592 (day 24, hour 16).
    {'farmer': ['SOUTH'],
     'hands': [['CARE'], ['EAST'], ['DIG'], ['NORTH'], ['SOUTH'], ['WEST'], ['WATER'], ['WEST'],
               ['PLANT', 'WHEAT'], ['EAST'], ['HARVEST'], ['SOUTH'], ['WEST']],
     'market': [['BUY_SEED', 'WHEAT', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 593 (day 24, hour 17).
    {'farmer': ['HARVEST'],
     'hands': [['WEST'], ['EAST'], ['PLANT', 'WHEAT'], ['NORTH'], ['DROP'], ['WATER'], ['WEST'],
               ['WEST'], ['WATER'], ['NORTH'], ['PLANT', 'WHEAT'], ['SOUTH'], ['WATER']],
     'market': [['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 2], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 594 (day 24, hour 18).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['DROP'], ['WATER'], ['COLLECT_FERTILIZER'], ['PICKUP', 'WHEAT', 2],
               ['HARVEST'], ['SOUTH'], ['WEST'], ['WEST'], ['DROP'], ['WATER'], ['WATER'], ['WEST']],
     'market': [['SELL', 'MILK', 3], ['SELL', 'WHEAT', 2], ['SELL', 'FERTILIZER', 1]]},
    # Step 595 (day 24, hour 19).
    {'farmer': ['HARVEST'],
     'hands': [['WEST'], ['WEST'], ['WEST'], ['WEST'], ['DROP'], ['EAST'], ['WATER'], ['NORTH'],
               ['WEST'], ['WEST'], ['WEST'], ['EAST'], ['SOUTH']],
     'market': [['SELL', 'WHEAT', 2], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 596 (day 24, hour 20).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['NORTH'], ['WEST'], ['SOUTH'], ['PICKUP', 'WHEAT', 2], ['EAST'], ['HARVEST'],
               ['NORTH'], ['SOUTH'], ['SOUTH'], ['SOUTH'], ['EAST'], ['WEST']],
     'market': []},
    # Step 597 (day 24, hour 21).
    {'farmer': ['HARVEST'],
     'hands': [['NORTH'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['HARVEST'], ['EAST'], ['EAST'],
               ['PLANT', 'WHEAT'], ['NORTH'], ['WEST'], ['PLANT', 'WHEAT'], ['WATER'], ['EAST'],
               ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 598 (day 24, hour 22).
    {'farmer': ['EAST'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['EAST'], ['NORTH'], ['EAST'], ['WATER'], ['NORTH'],
               ['PASS'], ['WATER'], ['HARVEST'], ['SOUTH'], ['PASS']],
     'market': []},
    # Step 599 (day 24, hour 23).
    {'farmer': ['EAST'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['SOUTH'], ['FEED', 'WHEAT'], ['DROP'], ['NORTH'],
               ['FEED', 'WHEAT'], ['PASS'], ['EAST'], ['PLANT', 'WHEAT'], ['DROP'], ['PASS']],
     'market': [['SELL', 'WHEAT', 14], ['BUY_SEED', 'WHEAT', 1]]},
    # Step 600 (day 25, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 4], ['SELL', 'WHEAT', 26], ['SELL', 'STRAWBERRY', 28],
                ['SELL', 'FERTILIZER', 5], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 601 (day 25, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'],
                ['BUY_SEED', 'WHEAT', 1]]},
    # Step 602 (day 25, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['NORTH'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['WEST'], ['WEST'], ['NORTH'], ['SOUTH'], ['WEST'],
               ['WEST'], ['EAST']],
     'market': []},
    # Step 603 (day 25, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'], ['WEST'], ['NORTH'], ['WATER'],
               ['WEST'], ['NORTH'], ['NORTH'], ['SOUTH'], ['WEST'], ['WEST'], ['EAST']],
     'market': []},
    # Step 604 (day 25, hour 4).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['CARE'], ['NORTH'], ['FEED', 'WHEAT'], ['HARVEST'], ['HARVEST'], ['WEST'],
               ['NORTH'], ['NORTH'], ['WATER'], ['WEST'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 605 (day 25, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['CARE'], ['FEED', 'WHEAT'],
               ['PLANT', 'WHEAT'], ['SOUTH'], ['WATER'], ['WATER'], ['WEST'], ['WEST'], ['WATER'],
               ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 606 (day 25, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['WEST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['CARE'], ['WATER'], ['SOUTH'],
               ['WEST'], ['EAST'], ['WATER'], ['WEST'], ['HARVEST'], ['WEST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 607 (day 25, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['FEED', 'WHEAT'], ['SOUTH'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['WATER'], ['WATER'], ['SOUTH'], ['EAST'], ['NORTH'], ['PLANT', 'WHEAT'], ['NORTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 608 (day 25, hour 8).
    {'farmer': ['CARE'],
     'hands': [['CARE'], ['SOUTH'], ['EAST'], ['HARVEST'], ['NORTH'], ['WEST'], ['WEST'], ['WEST'],
               ['WATER'], ['SOUTH'], ['NORTH'], ['WATER'], ['NORTH']],
     'market': []},
    # Step 609 (day 25, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'], ['FEED', 'WHEAT'], ['HARVEST'], ['WEST'],
               ['WATER'], ['WATER'], ['EAST'], ['WATER'], ['WATER'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 610 (day 25, hour 10).
    {'farmer': ['NORTH'],
     'hands': [['EAST'], ['PASS'], ['WATER'], ['CARE'], ['FEED', 'WHEAT'], ['WEST'], ['WEST'], ['WEST'],
               ['WATER'], ['WEST'], ['HARVEST'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 611 (day 25, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['WEST'], ['EAST'], ['COLLECT_FERTILIZER'], ['CARE'], ['WATER'], ['WATER'],
               ['SOUTH'], ['EAST'], ['WEST'], ['PLANT', 'WHEAT'], ['WATER'], ['SOUTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 612 (day 25, hour 12).
    {'farmer': ['CARE'],
     'hands': [['NORTH'], ['WATER'], ['WATER'], ['WEST'], ['COLLECT_FERTILIZER'], ['HARVEST'],
               ['SOUTH'], ['SOUTH'], ['SOUTH'], ['NORTH'], ['WATER'], ['HARVEST'], ['DIG']],
     'market': []},
    # Step 613 (day 25, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['WEST'], ['EAST'], ['WEST'], ['EAST'], ['PLANT', 'WHEAT'], ['WATER'],
               ['WATER'], ['WATER'], ['NORTH'], ['NORTH'], ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 614 (day 25, hour 14).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['WATER'], ['WATER'], ['NORTH'], ['SOUTH'], ['WATER'], ['EAST'], ['HARVEST'],
               ['HARVEST'], ['HARVEST'], ['WATER'], ['WATER'], ['WATER']],
     'market': []},
    # Step 615 (day 25, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['SOUTH'], ['WEST'], ['NORTH'], ['FEED', 'WHEAT'], ['SOUTH'], ['EAST'],
               ['PLANT', 'WHEAT'], ['PLANT', 'WHEAT'], ['WEST'], ['EAST'], ['WEST'], ['EAST']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 616 (day 25, hour 16).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['WATER'], ['WATER'], ['SOUTH'], ['NORTH'], ['CARE'], ['SOUTH'], ['EAST'], ['WATER'],
               ['WATER'], ['HARVEST'], ['EAST'], ['NORTH'], ['EAST']],
     'market': []},
    # Step 617 (day 25, hour 17).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['EAST'], ['EAST'], ['NORTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['SOUTH'],
               ['EAST'], ['EAST'], ['WEST'], ['NORTH'], ['NORTH'], ['SOUTH']],
     'market': []},
    # Step 618 (day 25, hour 18).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['SOUTH'], ['WATER'], ['SOUTH'], ['FEED', 'WHEAT'], ['EAST'], ['WATER'], ['WATER'],
               ['NORTH'], ['WATER'], ['NORTH'], ['NORTH'], ['NORTH'], ['DIG']],
     'market': []},
    # Step 619 (day 25, hour 19).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['WEST'], ['WATER'], ['CARE'], ['SOUTH'], ['HARVEST'], ['PASS'], ['WATER'],
               ['HARVEST'], ['PLANT', 'WHEAT'], ['WATER'], ['DIG'], ['PLANT', 'WHEAT']],
     'market': []},
    # Step 620 (day 25, hour 20).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['HARVEST'], ['PASS'], ['COLLECT_FERTILIZER'], ['FEED', 'WHEAT'], ['EAST'],
               ['PASS'], ['HARVEST'], ['PLANT', 'WHEAT'], ['WATER'], ['HARVEST'], ['PLANT', 'WHEAT'],
               ['WATER']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 621 (day 25, hour 21).
    {'farmer': ['PASS'],
     'hands': [['CARE'], ['PASS'], ['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'], ['PLANT', 'WHEAT'],
               ['WATER'], ['PASS'], ['PLANT', 'WHEAT'], ['WATER'], ['PASS']],
     'market': [['BUY_SEED', 'WHEAT', 2]]},
    # Step 622 (day 25, hour 22).
    {'farmer': ['PASS'],
     'hands': [['COLLECT_FERTILIZER'], ['PASS'], ['PASS'], ['PASS'], ['WEST'], ['PASS'], ['PASS'],
               ['WATER'], ['PASS'], ['PASS'], ['WATER'], ['PASS'], ['PASS']],
     'market': []},
    # Step 623 (day 25, hour 23).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['DROP'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'MILK', 6], ['SELL', 'FERTILIZER', 3]]},
    # Step 624 (day 26, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 8], ['SELL', 'MILK', 5], ['SELL', 'FERTILIZER', 11],
                ['SELL', 'WHEAT', 23], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 625 (day 26, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 626 (day 26, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['WEST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['WEST'], ['WEST'], ['NORTH'], ['EAST'], ['SOUTH'], ['WEST'],
               ['WEST'], ['EAST']],
     'market': []},
    # Step 627 (day 26, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['HARVEST'], ['WEST'], ['WEST'], ['HARVEST'], ['WATER'], ['WEST'], ['NORTH'],
               ['EAST'], ['SOUTH'], ['WEST'], ['WEST'], ['EAST']],
     'market': []},
    # Step 628 (day 26, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['SOUTH'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['WEST'], ['WEST'], ['NORTH'], ['EAST'], ['HARVEST'], ['WEST'], ['WEST'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 629 (day 26, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['CARE'], ['SOUTH'], ['FEED', 'WHEAT'], ['CARE'], ['WATER'], ['SOUTH'],
               ['WATER'], ['WATER'], ['DIG'], ['WEST'], ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 630 (day 26, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['HARVEST'], ['CARE'],
               ['COLLECT_FERTILIZER'], ['WEST'], ['SOUTH'], ['NORTH'], ['EAST'], ['PLANT', 'WHEAT'],
               ['SOUTH'], ['SOUTH'], ['HARVEST']],
     'market': [['SELL', 'FERTILIZER', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 631 (day 26, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['WEST'], ['DIG'], ['COLLECT_FERTILIZER'], ['NORTH'], ['WATER'], ['SOUTH'],
               ['WATER'], ['WATER'], ['WATER'], ['SOUTH'], ['SOUTH'], ['PLANT', 'WHEAT']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 632 (day 26, hour 8).
    {'farmer': ['CARE'],
     'hands': [['SOUTH'], ['NORTH'], ['PLANT', 'WHEAT'], ['EAST'], ['NORTH'], ['SOUTH'], ['HARVEST'],
               ['WEST'], ['NORTH'], ['SOUTH'], ['HARVEST'], ['SOUTH'], ['WATER']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 633 (day 26, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['FEED', 'WHEAT'], ['NORTH'], ['WATER'], ['NORTH'], ['FEED', 'WHEAT'], ['WATER'],
               ['DIG'], ['WATER'], ['NORTH'], ['HARVEST'], ['DIG'], ['SOUTH'], ['NORTH']],
     'market': []},
    # Step 634 (day 26, hour 10).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['NORTH'], ['WEST'], ['NORTH'], ['CARE'], ['EAST'], ['PLANT', 'WHEAT'],
               ['SOUTH'], ['NORTH'], ['DIG'], ['PLANT', 'WHEAT'], ['HARVEST'], ['NORTH']],
     'market': [['SELL', 'FERTILIZER', 2]]},
    # Step 635 (day 26, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['WATER'], ['WATER'], ['PLANT', 'WHEAT'],
               ['WATER'], ['DIG'], ['NORTH']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 636 (day 26, hour 12).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['WEST'], ['DIG'], ['CARE'], ['EAST'], ['EAST'], ['SOUTH'], ['WEST'], ['WEST'],
               ['WATER'], ['WEST'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': [['SELL', 'FERTILIZER', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 637 (day 26, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['WATER'], ['PLANT', 'WHEAT'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['WATER'],
               ['HARVEST'], ['WATER'], ['WEST'], ['SOUTH'], ['HARVEST'], ['WATER'], ['EAST']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 638 (day 26, hour 14).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['SOUTH'], ['WATER'], ['WEST'], ['HARVEST'], ['EAST'], ['DIG'], ['WEST'],
               ['WEST'], ['WATER'], ['DIG'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 639 (day 26, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['NORTH'], ['SOUTH'], ['EAST'], ['WEST'], ['FEED', 'WHEAT'], ['EAST'],
               ['PLANT', 'WHEAT'], ['WATER'], ['NORTH'], ['WEST'], ['PLANT', 'WHEAT'], ['HARVEST'],
               ['EAST']],
     'market': [['SELL', 'FERTILIZER', 2]]},
    # Step 640 (day 26, hour 16).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['WATER'], ['CARE'], ['SOUTH'], ['WEST'], ['CARE'], ['EAST'], ['WATER'], ['NORTH'],
               ['WATER'], ['HARVEST'], ['WATER'], ['DIG'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 641 (day 26, hour 17).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['NORTH'], ['WEST'], ['HARVEST'], ['WEST'], ['COLLECT_FERTILIZER'], ['EAST'], ['EAST'],
               ['WATER'], ['HARVEST'], ['PASS'], ['EAST'], ['PLANT', 'WHEAT'], ['WEST']],
     'market': [['SELL', 'FERTILIZER', 1], ['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 642 (day 26, hour 18).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['WEST'], ['DIG'], ['NORTH'], ['EAST'], ['NORTH'], ['DIG'], ['SOUTH'],
               ['PLANT', 'WHEAT'], ['PASS'], ['SOUTH'], ['WATER'], ['SOUTH']],
     'market': [['BUY_SEED', 'WHEAT', 1]]},
    # Step 643 (day 26, hour 19).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['NORTH'], ['PLANT', 'WHEAT'], ['NORTH'], ['SOUTH'], ['NORTH'],
               ['PLANT', 'WHEAT'], ['SOUTH'], ['WATER'], ['PASS'], ['HARVEST'], ['EAST'], ['WATER']],
     'market': [['SELL', 'FERTILIZER', 2]]},
    # Step 644 (day 26, hour 20).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['NORTH'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['CARE'],
               ['WATER'], ['WATER'], ['EAST'], ['PASS'], ['DIG'], ['HARVEST'], ['EAST']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 645 (day 26, hour 21).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['WATER'], ['PASS'], ['CARE'], ['COLLECT_FERTILIZER'], ['NORTH'], ['PASS'],
               ['WEST'], ['SOUTH'], ['PASS'], ['PLANT', 'WHEAT'], ['DIG'], ['SOUTH']],
     'market': [['SELL', 'FERTILIZER', 1], ['SELL', 'WHEAT', 3]]},
    # Step 646 (day 26, hour 22).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PASS'], ['PASS'], ['COLLECT_FERTILIZER'], ['PASS'], ['NORTH'], ['PASS'],
               ['PASS'], ['WATER'], ['PASS'], ['WATER'], ['PLANT', 'WHEAT'], ['WATER']],
     'market': [['SELL', 'FERTILIZER', 1]]},
    # Step 647 (day 26, hour 23).
    {'farmer': ['PASS'],
     'hands': [['EAST'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['WATER'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS'], ['WATER'], ['PASS']],
     'market': []},
    # Step 648 (day 27, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'STRAWBERRY', 28], ['SELL', 'MILK', 12], ['SELL', 'FERTILIZER', 14],
                ['SELL', 'WHEAT', 2], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 649 (day 27, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 650 (day 27, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 1],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['EAST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['WEST'], ['PICKUP', 'WHEAT', 3], ['NORTH'], ['WEST'],
               ['NORTH']],
     'market': []},
    # Step 651 (day 27, hour 3).
    {'farmer': ['WEST'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['NORTH'], ['WATER'],
               ['WEST'], ['HARVEST'], ['NORTH'], ['WEST'], ['NORTH']],
     'market': []},
    # Step 652 (day 27, hour 4).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['CARE'], ['CARE'], ['NORTH'], ['HARVEST'], ['HARVEST'], ['WEST'], ['NORTH'],
               ['FEED', 'WHEAT'], ['NORTH'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 653 (day 27, hour 5).
    {'farmer': ['CARE'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['NORTH'], ['FEED', 'WHEAT'],
               ['FEED', 'WHEAT'], ['WEST'], ['NORTH'], ['CARE'], ['WATER'], ['NORTH'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 654 (day 27, hour 6).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['EAST'], ['NORTH'], ['CARE'], ['CARE'], ['WEST'], ['NORTH'],
               ['COLLECT_FERTILIZER'], ['HARVEST'], ['WATER'], ['NORTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 2]]},
    # Step 655 (day 27, hour 7).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['EAST'], ['WATER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['WEST'],
               ['WATER'], ['WEST'], ['EAST'], ['WEST'], ['WATER']],
     'market': []},
    # Step 656 (day 27, hour 8).
    {'farmer': ['WATER'],
     'hands': [['FEED', 'WHEAT'], ['EAST'], ['EAST'], ['NORTH'], ['NORTH'], ['WATER'], ['HARVEST'],
               ['NORTH'], ['SOUTH'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 657 (day 27, hour 9).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['EAST'], ['EAST'], ['HARVEST'], ['HARVEST'], ['NORTH'], ['WEST'],
               ['FEED', 'WHEAT'], ['WATER'], ['WEST'], ['EAST']],
     'market': []},
    # Step 658 (day 27, hour 10).
    {'farmer': ['WATER'],
     'hands': [['COLLECT_FERTILIZER'], ['NORTH'], ['SOUTH'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'],
               ['WATER'], ['WATER'], ['CARE'], ['HARVEST'], ['WATER'], ['EAST']],
     'market': []},
    # Step 659 (day 27, hour 11).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['WATER'], ['WATER'], ['CARE'], ['CARE'], ['EAST'], ['HARVEST'],
               ['COLLECT_FERTILIZER'], ['EAST'], ['SOUTH'], ['WATER']],
     'market': []},
    # Step 660 (day 27, hour 12).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['EAST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['SOUTH'],
               ['WEST'], ['WEST'], ['WATER'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 661 (day 27, hour 13).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['NORTH'], ['WATER'], ['WEST'], ['EAST'], ['HARVEST'], ['WATER'], ['WEST'],
               ['HARVEST'], ['EAST'], ['SOUTH']],
     'market': []},
    # Step 662 (day 27, hour 14).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['WEST'], ['SOUTH'], ['EAST'], ['HARVEST'], ['WEST'],
               ['EAST'], ['WATER'], ['WATER']],
     'market': []},
    # Step 663 (day 27, hour 15).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WEST'], ['NORTH'], ['SOUTH'], ['FEED', 'WHEAT'], ['HARVEST'], ['WEST'],
               ['NORTH'], ['EAST'], ['WEST'], ['HARVEST']],
     'market': []},
    # Step 664 (day 27, hour 16).
    {'farmer': ['NORTH'],
     'hands': [['NORTH'], ['WEST'], ['NORTH'], ['SOUTH'], ['CARE'], ['EAST'], ['WATER'], ['NORTH'],
               ['NORTH'], ['NORTH'], ['EAST']],
     'market': []},
    # Step 665 (day 27, hour 17).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['WEST'], ['NORTH'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['WATER'],
               ['HARVEST'], ['NORTH'], ['WATER'], ['NORTH'], ['WATER']],
     'market': []},
    # Step 666 (day 27, hour 18).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['SOUTH'], ['WATER'], ['EAST'], ['SOUTH'], ['EAST'], ['EAST'],
               ['FEED', 'WHEAT'], ['SOUTH'], ['NORTH'], ['HARVEST']],
     'market': []},
    # Step 667 (day 27, hour 19).
    {'farmer': ['EAST'],
     'hands': [['WATER'], ['CARE'], ['HARVEST'], ['EAST'], ['HARVEST'], ['SOUTH'], ['NORTH'], ['CARE'],
               ['SOUTH'], ['EAST'], ['EAST']],
     'market': []},
    # Step 668 (day 27, hour 20).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['COLLECT_FERTILIZER'], ['WEST'], ['DROP'], ['WEST'], ['SOUTH'], ['WATER'],
               ['COLLECT_FERTILIZER'], ['SOUTH'], ['EAST'], ['SOUTH']],
     'market': [['SELL', 'WOOL', 8], ['SELL', 'MILK', 3], ['SELL', 'FERTILIZER', 2]]},
    # Step 669 (day 27, hour 21).
    {'farmer': ['WATER'],
     'hands': [['WATER'], ['PASS'], ['WATER'], ['WEST'], ['DROP'], ['SOUTH'], ['NORTH'], ['PASS'],
               ['WATER'], ['NORTH'], ['WATER']],
     'market': [['SELL', 'MILK', 11], ['SELL', 'FERTILIZER', 3]]},
    # Step 670 (day 27, hour 22).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['HARVEST'], ['WEST'], ['EAST'], ['WATER'], ['PASS'], ['PASS'],
               ['PASS'], ['WATER'], ['HARVEST']],
     'market': []},
    # Step 671 (day 27, hour 23).
    {'farmer': ['PASS'],
     'hands': [['WATER'], ['PASS'], ['PASS'], ['CARE'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS'], ['PASS'], ['PASS']],
     'market': []},
    # Step 672 (day 28, hour 0).
    {'farmer': ['PASS'],
     'hands': [],
     'market': [['SELL', 'WOOL', 4], ['SELL', 'WHEAT', 50], ['SELL', 'FERTILIZER', 8],
                ['SELL', 'STRAWBERRY', 4], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 673 (day 28, hour 1).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS']],
     'market': [['SELL', 'FERTILIZER', 2], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 674 (day 28, hour 2).
    {'farmer': ['PICKUP', 'WHEAT', 4],
     'hands': [['PICKUP', 'WHEAT', 2], ['PICKUP', 'WHEAT', 1], ['EAST'], ['PICKUP', 'WHEAT', 3],
               ['PICKUP', 'WHEAT', 4], ['SOUTH'], ['WEST'], ['NORTH'], ['EAST'], ['WEST']],
     'market': []},
    # Step 675 (day 28, hour 3).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['HARVEST'], ['EAST'], ['WEST'], ['HARVEST'], ['SOUTH'], ['WEST'], ['NORTH'],
               ['EAST'], ['WEST']],
     'market': []},
    # Step 676 (day 28, hour 4).
    {'farmer': ['CARE'],
     'hands': [['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['EAST'], ['HARVEST'], ['FEED', 'WHEAT'],
               ['WATER'], ['WEST'], ['NORTH'], ['NORTH'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 677 (day 28, hour 5).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['CARE'], ['CARE'], ['NORTH'], ['FEED', 'WHEAT'], ['CARE'], ['WEST'], ['NORTH'],
               ['WATER'], ['WATER'], ['SOUTH']],
     'market': [['BUY_PRODUCT', 'WHEAT', 3]]},
    # Step 678 (day 28, hour 6).
    {'farmer': ['NORTH'],
     'hands': [['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['WATER'], ['CARE'],
               ['COLLECT_FERTILIZER'], ['WATER'], ['NORTH'], ['HARVEST'], ['WEST'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 679 (day 28, hour 7).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['EAST'], ['WEST'], ['HARVEST'], ['COLLECT_FERTILIZER'], ['NORTH'], ['SOUTH'], ['NORTH'],
               ['WEST'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 680 (day 28, hour 8).
    {'farmer': ['CARE'],
     'hands': [['SOUTH'], ['WATER'], ['NORTH'], ['EAST'], ['NORTH'], ['WATER'], ['NORTH'], ['WATER'],
               ['NORTH'], ['WATER']],
     'market': []},
    # Step 681 (day 28, hour 9).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['FEED', 'WHEAT'], ['HARVEST'], ['WATER'], ['NORTH'], ['FEED', 'WHEAT'], ['EAST'],
               ['WATER'], ['HARVEST'], ['NORTH'], ['WEST']],
     'market': []},
    # Step 682 (day 28, hour 10).
    {'farmer': ['WEST'],
     'hands': [['CARE'], ['WEST'], ['NORTH'], ['NORTH'], ['CARE'], ['WATER'], ['HARVEST'], ['WEST'],
               ['WATER'], ['WATER']],
     'market': []},
    # Step 683 (day 28, hour 11).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['COLLECT_FERTILIZER'], ['WATER'], ['WATER'], ['FEED', 'WHEAT'], ['COLLECT_FERTILIZER'],
               ['WEST'], ['WEST'], ['NORTH'], ['EAST'], ['SOUTH']],
     'market': []},
    # Step 684 (day 28, hour 12).
    {'farmer': ['CARE'],
     'hands': [['WEST'], ['HARVEST'], ['EAST'], ['CARE'], ['EAST'], ['SOUTH'], ['WATER'], ['WATER'],
               ['EAST'], ['WATER']],
     'market': []},
    # Step 685 (day 28, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['WEST'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['SOUTH'], ['WATER'], ['HARVEST'],
               ['WEST'], ['EAST'], ['EAST']],
     'market': []},
    # Step 686 (day 28, hour 14).
    {'farmer': ['WEST'],
     'hands': [['WEST'], ['WATER'], ['WATER'], ['WEST'], ['HARVEST'], ['EAST'], ['NORTH'], ['WEST'],
               ['SOUTH'], ['WATER']],
     'market': []},
    # Step 687 (day 28, hour 15).
    {'farmer': ['SOUTH'],
     'hands': [['WEST'], ['HARVEST'], ['WEST'], ['WEST'], ['FEED', 'WHEAT'], ['WATER'], ['WATER'],
               ['SOUTH'], ['WATER'], ['EAST']],
     'market': []},
    # Step 688 (day 28, hour 16).
    {'farmer': ['FEED', 'WHEAT'],
     'hands': [['NORTH'], ['EAST'], ['WEST'], ['WEST'], ['CARE'], ['HARVEST'], ['HARVEST'], ['WATER'],
               ['HARVEST'], ['WATER']],
     'market': []},
    # Step 689 (day 28, hour 17).
    {'farmer': ['CARE'],
     'hands': [['WATER'], ['EAST'], ['WEST'], ['WEST'], ['COLLECT_FERTILIZER'], ['NORTH'], ['EAST'],
               ['SOUTH'], ['SOUTH'], ['SOUTH']],
     'market': []},
    # Step 690 (day 28, hour 18).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['WEST'], ['SOUTH'], ['NORTH'], ['NORTH'], ['EAST'], ['NORTH'], ['EAST'], ['SOUTH'],
               ['SOUTH'], ['WATER']],
     'market': []},
    # Step 691 (day 28, hour 19).
    {'farmer': ['EAST'],
     'hands': [['SOUTH'], ['WATER'], ['NORTH'], ['NORTH'], ['SOUTH'], ['NORTH'], ['WATER'], ['WATER'],
               ['SOUTH'], ['WEST']],
     'market': []},
    # Step 692 (day 28, hour 20).
    {'farmer': ['NORTH'],
     'hands': [['WATER'], ['HARVEST'], ['WATER'], ['FEED', 'WHEAT'], ['FEED', 'WHEAT'], ['WATER'],
               ['HARVEST'], ['EAST'], ['WATER'], ['WATER']],
     'market': [['BUY_PRODUCT', 'WHEAT', 1]]},
    # Step 693 (day 28, hour 21).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['WEST'], ['EAST'], ['CARE'], ['CARE'], ['WEST'], ['EAST'], ['WATER'],
               ['HARVEST'], ['WEST']],
     'market': [['SELL', 'WHEAT', 1]]},
    # Step 694 (day 28, hour 22).
    {'farmer': ['PLANT', 'WHEAT'],
     'hands': [['WATER'], ['WEST'], ['PLANT', 'WHEAT'], ['COLLECT_FERTILIZER'], ['WEST'], ['WEST'],
               ['WATER'], ['PASS'], ['PASS'], ['WATER']],
     'market': []},
    # Step 695 (day 28, hour 23).
    {'farmer': ['WATER'],
     'hands': [['NORTH'], ['WEST'], ['WATER'], ['PASS'], ['WEST'], ['DIG'], ['HARVEST'], ['PASS'],
               ['PASS'], ['PASS']],
     'market': []},
    # Step 696 (day 29, hour 0).
    {'farmer': ['EAST'],
     'hands': [],
     'market': [['SELL', 'MILK', 12], ['SELL', 'WHEAT', 65], ['SELL', 'FERTILIZER', 13], ['HIRE'],
                ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 697 (day 29, hour 1).
    {'farmer': ['EAST'],
     'hands': [['WEST'], ['WEST'], ['NORTH'], ['WEST'], ['NORTH'], ['SOUTH'], ['EAST']],
     'market': [['HIRE'], ['HIRE'], ['HIRE']]},
    # Step 698 (day 29, hour 2).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['WEST'], ['EAST'], ['WEST'], ['HARVEST'], ['WATER'], ['NORTH'], ['EAST'],
               ['SOUTH'], ['WEST']],
     'market': []},
    # Step 699 (day 29, hour 3).
    {'farmer': ['HARVEST'],
     'hands': [['HARVEST'], ['WEST'], ['HARVEST'], ['HARVEST'], ['NORTH'], ['HARVEST'], ['NORTH'],
               ['WEST'], ['SOUTH'], ['WEST']],
     'market': []},
    # Step 700 (day 29, hour 4).
    {'farmer': ['NORTH'],
     'hands': [['WEST'], ['NORTH'], ['EAST'], ['NORTH'], ['HARVEST'], ['WEST'], ['NORTH'], ['WEST'],
               ['WATER'], ['WEST']],
     'market': []},
    # Step 701 (day 29, hour 5).
    {'farmer': ['WATER'],
     'hands': [['WEST'], ['WATER'], ['EAST'], ['WATER'], ['EAST'], ['SOUTH'], ['NORTH'], ['WEST'],
               ['HARVEST'], ['WEST']],
     'market': []},
    # Step 702 (day 29, hour 6).
    {'farmer': ['HARVEST'],
     'hands': [['WEST'], ['HARVEST'], ['NORTH'], ['HARVEST'], ['EAST'], ['WATER'], ['WATER'], ['WEST'],
               ['SOUTH'], ['WEST']],
     'market': []},
    # Step 703 (day 29, hour 7).
    {'farmer': ['EAST'],
     'hands': [['NORTH'], ['NORTH'], ['WATER'], ['WEST'], ['EAST'], ['HARVEST'], ['HARVEST'], ['WEST'],
               ['WATER'], ['WATER']],
     'market': []},
    # Step 704 (day 29, hour 8).
    {'farmer': ['HARVEST'],
     'hands': [['NORTH'], ['WATER'], ['EAST'], ['WEST'], ['WATER'], ['WEST'], ['NORTH'], ['WATER'],
               ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 705 (day 29, hour 9).
    {'farmer': ['WEST'],
     'hands': [['NORTH'], ['HARVEST'], ['WATER'], ['WATER'], ['HARVEST'], ['WATER'], ['WATER'],
               ['HARVEST'], ['WEST'], ['SOUTH']],
     'market': []},
    # Step 706 (day 29, hour 10).
    {'farmer': ['WEST'],
     'hands': [['HARVEST'], ['WEST'], ['HARVEST'], ['HARVEST'], ['WEST'], ['HARVEST'], ['HARVEST'],
               ['SOUTH'], ['WATER'], ['WATER']],
     'market': []},
    # Step 707 (day 29, hour 11).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['SOUTH'], ['EAST'], ['WEST'], ['EAST'], ['WEST'], ['WEST'], ['WEST'], ['SOUTH'],
               ['HARVEST'], ['HARVEST']],
     'market': []},
    # Step 708 (day 29, hour 12).
    {'farmer': ['WEST'],
     'hands': [['WATER'], ['EAST'], ['WEST'], ['EAST'], ['WEST'], ['WATER'], ['WEST'], ['SOUTH'],
               ['WEST'], ['EAST']],
     'market': []},
    # Step 709 (day 29, hour 13).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['HARVEST'], ['EAST'], ['SOUTH'], ['SOUTH'], ['COLLECT_FERTILIZER'], ['HARVEST'],
               ['SOUTH'], ['WATER'], ['WATER'], ['EAST']],
     'market': []},
    # Step 710 (day 29, hour 14).
    {'farmer': ['WEST'],
     'hands': [['EAST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'],
               ['WEST'], ['EAST'], ['SOUTH'], ['HARVEST'], ['HARVEST'], ['EAST']],
     'market': []},
    # Step 711 (day 29, hour 15).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['SOUTH'], ['WEST'], ['EAST'], ['COLLECT_FERTILIZER'], ['EAST'], ['EAST'],
               ['EAST'], ['EAST'], ['EAST']],
     'market': []},
    # Step 712 (day 29, hour 16).
    {'farmer': ['SOUTH'],
     'hands': [['EAST'], ['COLLECT_FERTILIZER'], ['COLLECT_FERTILIZER'], ['EAST'], ['SOUTH'], ['EAST'],
               ['SOUTH'], ['EAST'], ['EAST'], ['NORTH']],
     'market': []},
    # Step 713 (day 29, hour 17).
    {'farmer': ['COLLECT_FERTILIZER'],
     'hands': [['EAST'], ['EAST'], ['WEST'], ['DROP'], ['SOUTH'], ['NORTH'], ['SOUTH'], ['EAST'],
               ['NORTH'], ['COLLECT_FERTILIZER']],
     'market': [['SELL', 'MILK', 2], ['SELL', 'FERTILIZER', 1], ['SELL', 'WHEAT', 8]]},
    # Step 714 (day 29, hour 18).
    {'farmer': ['DROP'],
     'hands': [['SOUTH'], ['DROP'], ['COLLECT_FERTILIZER'], ['PASS'], ['DROP'], ['NORTH'], ['DROP'],
               ['EAST'], ['NORTH'], ['DROP']],
     'market': [['SELL', 'MILK', 6], ['SELL', 'WOOL', 5], ['SELL', 'WHEAT', 32],
                ['SELL', 'FERTILIZER', 9]]},
    # Step 715 (day 29, hour 19).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['DROP'], ['PASS'], ['PASS'], ['DROP'], ['PASS'], ['NORTH'],
               ['NORTH'], ['PASS']],
     'market': [['SELL', 'MILK', 2], ['SELL', 'WHEAT', 17], ['SELL', 'FERTILIZER', 3]]},
    # Step 716 (day 29, hour 20).
    {'farmer': ['PASS'],
     'hands': [['SOUTH'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['NORTH'],
               ['DROP'], ['PASS']],
     'market': [['SELL', 'WHEAT', 12], ['SELL', 'FERTILIZER', 2]]},
    # Step 717 (day 29, hour 21).
    {'farmer': ['PASS'],
     'hands': [['DROP'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['DROP'], ['PASS'],
               ['PASS']],
     'market': [['SELL', 'WOOL', 9], ['SELL', 'WHEAT', 11]]},
    # Step 718 (day 29, hour 22).
    {'farmer': ['PASS'],
     'hands': [['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'], ['PASS'],
               ['PASS']],
     'market': []},
]
_PRICE_FLOOR = 1
_DEMAND_ALPHA = 0.25
_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}
_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_WEED_STATE = {0: {}, 1: {}}
_WEED_REPLAY_STEPS = 8


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _regime(configuration):
    interval = int(_get(configuration, "townCenterSellInterval", 12) or 12)
    return "rebalance" if interval >= 24 else "legacy"


def _copy_action(action):
    action = copy.deepcopy(action or {})
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],
        "market": [list(order) for order in (action.get("market") or [])],
    }


def _seat(obs):
    return 1 if int(_get(obs, "player", 0) or 0) == 1 else 0


def _farm(obs, seat):
    farms = list(_get(obs, "farms", []) or [])
    return farms[seat] if seat < len(farms) else {}


def _align_hands(action, obs):
    action = _copy_action(action)
    expected = len(_get(_farm(obs, _seat(obs)), "hands", []) or [])
    hands = list(action.get("hands") or [])
    if len(hands) < expected:
        hands.extend([["PASS"] for _ in range(expected - len(hands))])
    action["hands"] = [list(order or ["PASS"]) for order in hands[:expected]]
    return action


def _tile_at(farm, position):
    try:
        x, y = int(position[0]), int(position[1])
        return (_get(farm, "tiles", []) or [])[y][x]
    except (IndexError, TypeError, ValueError):
        return "LOCKED"


def _trace_actor_action(actions, step, actor):
    trace = actions[min(max(int(step), 0), len(actions) - 1)] or {}
    if actor == "farmer":
        return list(trace.get("farmer") or ["PASS"])
    hands = trace.get("hands", []) or []
    return list(hands[actor] if actor < len(hands) else ["PASS"])


def _weed_repair_action(obs, action, actions, step):
    action = _align_hands(action, obs)
    seat = _seat(obs)
    game = _WEED_STATE[seat]
    if step == 0 or step < game.get("last_step", -1):
        game = {"last_step": step, "active": {}}
        _WEED_STATE[seat] = game
    game["last_step"] = step
    farm = _farm(obs, seat)
    positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
    unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    active = game["active"]

    for actor, transaction in list(active.items()):
        index = 0 if actor == "farmer" else int(actor) + 1
        if index >= len(unit_actions):
            active.pop(actor, None)
            continue
        age = step - transaction["start"]
        if age == 1:
            unit_actions[index] = list(transaction["intended"])
        elif 2 <= age <= 1 + _WEED_REPLAY_STEPS:
            unit_actions[index] = _trace_actor_action(actions, step - 1, actor)
        else:
            active.pop(actor, None)

    for index, (position, intended) in enumerate(zip(positions, unit_actions)):
        actor = "farmer" if index == 0 else index - 1
        if actor in active or not isinstance(intended, list) or not intended:
            continue
        if intended[0] not in ("BUILD_PASTURE", "PLANT"):
            continue
        tile = _tile_at(farm, position)
        if not isinstance(tile, dict) or tile.get("kind") != "WEED":
            continue
        active[actor] = {"start": step, "intended": list(intended)}
        unit_actions[index] = ["DIG"]

    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return _align_hands(action, obs)


def _shape(name, value):
    value = max(0.0, float(value))
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1.0 + value)
    raise ValueError(name)


def _market_price(item, inventory):
    base, equilibrium, scale, below_func, below_target, above_func, above_target = (
        _MARKET_PARAMS[item]
    )
    if inventory < equilibrium:
        amplitude = below_target * base / _shape(below_func, scale)
        price = base + amplitude * _shape(below_func, equilibrium - inventory)
    else:
        amplitude = above_target * base / _shape(above_func, scale)
        price = base - amplitude * _shape(above_func, inventory - equilibrium)
    return max(_PRICE_FLOOR, int(round(price)))


def _is_sell(order):
    return (
        isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] in _MARKET_PARAMS
    )


def _impact_score(obs, order):
    if not _is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        quantity = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    prices = _get(market, "prices", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    current_quote = float(
        _get(prices, item, _market_price(item, current_inventory)) or 0
    )
    later_quote = float(_market_price(item, current_inventory + quantity))
    return float(quantity) * max(0.0, current_quote - later_quote)


def _demand_per_day(obs, configuration, item):
    town = _get(obs, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])
    turns_per_day = int(_get(configuration, "turnsPerDay", 24) or 24)
    shop_interval = max(
        1, int(_get(configuration, "townShopSellInterval", 4) or 4)
    )
    demand = 0.0
    for shop in shops:
        products = _SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += (turns_per_day / shop_interval) * (
                2 if len(products) == 1 else 1
            )
    regime = _regime(configuration)
    if item != "FERTILIZER":
        center_default = 24 if regime == "rebalance" else 12
        center_interval = max(
            1,
            int(
                _get(configuration, "townCenterSellInterval", center_default)
                or center_default
            ),
        )
        day = int(_get(obs, "day", int(_get(obs, "step", 0) or 0) // 24) or 0)
        multiplier = (
            1
            if regime == "rebalance"
            else (4 if day >= 20 else 2 if day >= 10 else 1)
        )
        demand += (turns_per_day / center_interval) * multiplier
    return demand


def _order_score(obs, configuration, order):
    score = _impact_score(obs, order)
    if _regime(configuration) != "rebalance" or score <= 0 or not _is_sell(order):
        return score
    item = str(order[1])
    quantity = max(0, int(order[2]))
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    demand = max(0.25, _demand_per_day(obs, configuration, item))
    excess = max(0.0, current_inventory + quantity - 10000)
    urgency = min(1.0, (excess / demand) / 10.0)
    return score * (1.0 + _DEMAND_ALPHA * urgency)


def _rank_sell_slots(obs, action, configuration):
    action = _copy_action(action)
    market = list(action.get("market") or [])
    rows = [
        (_order_score(obs, configuration, order), -index, list(order))
        for index, order in enumerate(market)
        if _is_sell(order)
    ]
    if len(rows) < 2:
        return action
    rows.sort(reverse=True)
    ranked = iter(row[2] for row in rows)
    action["market"] = [next(ranked) if _is_sell(order) else order for order in market]
    return action


def agent(obs, configuration=None):
    try:
        actions = _SEAT1_ACTIONS if _seat(obs) == 1 else _SEAT0_ACTIONS
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)
        action = _weed_repair_action(
            obs, _copy_action(actions[step]), actions, step
        )
        return _align_hands(_rank_sell_slots(obs, action, configuration), obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
            "market": [],
        }


def _kaggle_submission_entrypoint(obs, configuration=None):
    return agent(obs, configuration)


