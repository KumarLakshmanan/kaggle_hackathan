import math
from collections.abc import Callable
from dataclasses import dataclass

IO = 10000

def linear(number: float) -> float:
    return number


def sq(number: float) -> float:
    return number**2


def sqrt(number: float) -> float:
    return number**0.5


def log(number: float) -> float:
    return math.log(1 + number)

class Market:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._global_registry = {}
        return cls._instance

    def register_item(self, item: "Item"):
        if item not in self._global_registry:
            self._global_registry[item] = IO

    def get_inventory(self, item: "Item") -> int:
        return self._global_registry.get(item, 0)

    def set_inventory(self, item: "Item", amount: int):
        if item in self._global_registry:
            self._global_registry[item] = amount
        else:
            raise KeyError("Item is not registered")

@dataclass(eq=False)
class Item:
    base: int
    below_target: float
    above_target: float
    below_function: Callable[[float], float]
    above_function: Callable[[float], float]
    T: int

    def __post_init__(self):
        Market().register_item(self)

Wheat = Item(
    base=25,
    T=400,
    below_function=sqrt,
    below_target=0.8,
    above_function=log,
    above_target=0.2,
)
Carrot = Item(
    base=35,
    T=450,
    below_function=log,
    below_target=0.2,
    above_function=sqrt,
    above_target=0.7,
)
Tomato = Item(
    base=60,
    T=200,
    below_function=linear,
    below_target=0.4,
    above_function=sqrt,
    above_target=0.6,
)
Strawberry = Item(
    base=120,
    T=100,
    below_function=sqrt,
    below_target=0.7,
    above_function=linear,
    above_target=1.6,
)
Melon = Item(
    base=250,
    T=300,
    below_function=log,
    below_target=0.2,
    above_function=sq,
    above_target=3.6,
)
Egg = Item(
    base=50,
    T=332,
    below_function=linear,
    below_target=0.4,
    above_function=log,
    above_target=0.2,
)
Milk = Item(
    base=160,
    T=122,
    below_function=sqrt,
    below_target=0.6,
    above_function=linear,
    above_target=1.6,
)
Wool = Item(
    base=200,
    T=105,
    below_function=log,
    below_target=0.2,
    above_function=sq,
    above_target=3.2,
)
Fertilizer = Item(
    base=100,
    T=200,
    below_function=linear,
    below_target=0.4,
    above_function=linear,
    above_target=0.4,
)

def get_price(item: Item) -> int:
    market = Market()
    inventory = market.get_inventory(item)

    sign = 1 if inventory <= IO else -1

    target = item.below_target if sign > 0 else item.above_target
    func = item.below_function if sign > 0 else item.above_function

    amp = target * item.base / func(item.T)

    delta_inventory = abs(inventory - IO)
    calculated_price = item.base + (sign * amp * func(delta_inventory))

    return max(round(calculated_price), 1)

def print_item_status(item: Item, name: str):
    price = get_price(item)
    inventory = Market().get_inventory(item)
    print(f"📦 {name:<12} | Inventory: {inventory:<6} | Price: ${price}")


market = Market()

print("--- INITIAL STATE (Market Equilibrium) ---")
# By default, all items start with IO inventory (10,000)
# When inventory is at equilibrium, the price must equal the base price.
print_item_status(Wheat, "Wheat")  # Base: 25
print_item_status(Melon, "Melon")  # Base: 250
print_item_status(Tomato, "Tomato")  # Base: 60

print("\n--- SCENARIO 1: Critical Scarcity (Low Inventory) ---")
# Drastically reducing inventories to test 'below_function' behaviors
market.set_inventory(
    Wheat, 9600
)  # Uses square root (sqrt) -> price rises in a controlled manner
market.set_inventory(
    Melon, 9700
)  # Uses logarithm (log) -> price rises quickly at first
market.set_inventory(
    Tomato, 9800
)  # Uses linear -> price rises proportionally

print_item_status(Wheat, "Wheat")
print_item_status(Melon, "Melon")
print_item_status(Tomato, "Tomato")

print("\n--- SCENARIO 2: Extreme Surplus (Excess Inventory) ---")
# Heavily increasing inventories to test 'above_function' behaviors
market.set_inventory(
    Wheat, 10500
)  # Uses logarithm (log) -> price drops smoothly
market.set_inventory(
    Melon, 10300
)  # Uses squared (sq) -> price crashes exponentially
market.set_inventory(
    Tomato, 10200
)  # Uses square root (sqrt) -> price drops moderately

print_item_status(Wheat, "Wheat")
print_item_status(Melon, "Melon")
print_item_status(Tomato, "Tomato")

