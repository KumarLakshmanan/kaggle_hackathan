from pathlib import Path
import shutil

source = next(p.parent for p in Path('/kaggle/input').rglob('agent_manifest.json')
              if (p.parent / 'ensemble.json').is_file())
FILES = ['main.py', 'router_base.py', 'observation.py', 'actions.json', 'model.json',
         'ensemble.json', 'THIRD_PARTY_NOTICES.txt', 'LICENSE-APACHE-2.0.txt']
for name in FILES:
    shutil.copyfile(source / name, name)


%%writefile main.py
"""Observable-state, CPU-tree ensemble for Kaggriculture late-game routing.

Route/packing assets: Yusuke Hayashi (yhay81), public Shop Router 0908 notebook.
New work: paired counterfactual training, grouped CV, public-opponent features,
conservative ensemble gate, and dependency-free exported-tree inference.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
SHOPS = ("BAKERY", "BRUNCH_SPOT", "FARMERS_MARKET", "ICE_CREAM_SHOP", "PET_CAFE", "PIZZA_SHOP", "SMOOTHIE_SHOP", "YARN_STORE")
ANIMALS = ("GOOSE", "COW", "SHEEP")


def folder():
    return Path(agent.__code__.co_filename).resolve().parent


def load_source(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state_features(obs, early_route):
    """No identity, hidden seed, opponent-private inventory, or future fields."""
    shops = list(obs.get("town", {}).get("unlocked_shops", []))
    seat = int(obs.get("player", 0))
    farms = obs["farms"]
    priv = obs["private"]
    names, values = [], []
    def add(name, value):
        names.append(name)
        values.append(float(value))
    add("early_route", early_route)
    for shop in SHOPS:
        add("shop_count_" + shop, shops.count(shop))
        add("first_shop_" + shop, int(bool(shops) and shops[0] == shop))
    for label, player in (("own", seat), ("opponent", 1 - seat)):
        farm = farms[player]
        add(label + "_money", farm.get("money", 0))
        add(label + "_hands", len(farm.get("hands", [])))
        add(label + "_land", len(farm.get("unlocked_quadrants", [])))
        tiles = [tile for row in farm["tiles"] for tile in row if isinstance(tile, dict)]
        add(label + "_weeds", sum(t.get("kind") == "WEED" for t in tiles))
        for crop in PRODUCTS[:5]:
            selected = [t for t in tiles if t.get("crop") == crop]
            add(label + "_count_" + crop, len(selected))
            add(label + "_yield_" + crop, sum(t.get("yield_units", 0) for t in selected))
        for animal in ANIMALS:
            selected = [t for t in tiles if t.get("animal") == animal]
            add(label + "_count_" + animal, len(selected))
            add(label + "_yield_" + animal, sum(t.get("yield_units", 0) for t in selected))
    add("money_margin_now", farms[seat].get("money", 0) - farms[1-seat].get("money", 0))
    for item in PRODUCTS:
        add("shed_" + item, priv.get("shed", {}).get(item, 0))
        add("carried_" + item, sum(inv.get(item, 0) for inv in priv.get("inventories", [])))
        add("price_" + item, obs["market"]["prices"].get(item, 0))
        add("market_" + item, obs["market"]["inventory"].get(item, 0))
    for crop in PRODUCTS[:5]:
        add("seed_" + crop, priv.get("seeds", {}).get(crop, 0))
    return names, values


def tree_predict(tree, x):
    # Portable common representation: [feature, threshold, left, right] or leaf.
    while isinstance(tree, list):
        feature, threshold, left, right = tree
        tree = left if x[feature] <= threshold else right
    return float(tree)


def model_predict(model, x):
    return model["base"] + sum(tree_predict(tree, x) for tree in model["trees"])


class EnsembleAgent:
    def __init__(self, asset_dir=None, force_route=None, learned=True):
        asset_dir = Path(asset_dir) if asset_dir is not None else folder()
        source = load_source(asset_dir / "router_base.py", "route_base")
        self.router = source.Router(asset_dir)
        self.force_route = force_route
        self.model = json.loads((asset_dir / "ensemble.json").read_text()) if learned and (asset_dir / "ensemble.json").exists() else None
        self.features = None
        self.feature_names = None
        self.baseline_choice = None
        self.chosen = None

    def act(self, obs, config=None):
        step = int(obs.get("step", int(obs.get("day", 0))*24 + int(obs.get("hour", 0))))
        early = self.router.active
        action = self.router.act(obs, config)
        if step == 648:
            self.feature_names, self.features = state_features(obs, early)
            baseline = self.router.active
            self.baseline_choice = baseline
            chosen = baseline
            if self.force_route is not None:
                chosen = int(self.force_route)
            elif self.model is not None and all(math.isfinite(v) for v in self.features):
                if self.feature_names != self.model["features"]:
                    raise ValueError("feature schema changed")
                predictions = []
                for route in range(4):
                    lgb = model_predict(self.model["lightgbm"][route], self.features)
                    xgb = model_predict(self.model["xgboost"][route], self.features)
                    predictions.append(self.model["weight"]*lgb + (1-self.model["weight"])*xgb)
                preferred = max(range(4), key=lambda route: predictions[route])
                if predictions[preferred] - predictions[baseline] > self.model["minimum_gain"]:
                    chosen = preferred
            self.chosen = chosen
            self.router.active = chosen
            action = self.router.tapes[chosen][step]
        return action


_AGENT = None


def agent(obs, config=None):
    global _AGENT
    if _AGENT is None or int(obs.get("step", -1)) == 0:
        _AGENT = EnsembleAgent()
    return _AGENT.act(obs, config)


import gzip
import io
import tarfile
from IPython.display import FileLink, display

buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w') as archive:
    for name in sorted(FILES):
        payload = Path(name).read_bytes()
        info = tarfile.TarInfo(name)
        info.size, info.mode, info.mtime = len(payload), 0o644, 0
        archive.addfile(info, io.BytesIO(payload))
with open('submission.tar.gz', 'wb') as output:
    with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as compressed:
        compressed.write(buffer.getvalue())
display(FileLink('submission.tar.gz'))
