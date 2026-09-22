!python3 --version

import pydantic

print(f"Pydantic version: {pydantic.__version__}")

from typing import Annotated
from typing import Any
from typing_extensions import override
from typing import Literal
from typing import TypeAlias

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

Crop: TypeAlias = Literal["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
Animal: TypeAlias = Literal["GOOSE", "COW", "SHEEP"]
AnimalProduct: TypeAlias = Literal["EGG", "MILK", "WOOL"]
Product: TypeAlias = Crop | AnimalProduct | Literal["FERTILIZER"]
ShedItem: TypeAlias = Product | Animal
Position: TypeAlias = tuple[int, int]
Direction: TypeAlias = Literal["NORTH", "SOUTH", "EAST", "WEST"]
Quadrant: TypeAlias = Literal["NW", "NE", "SW", "SE"]
Shop: TypeAlias = Literal[
    "BAKERY",
    "PIZZA_SHOP",
    "BRUNCH_SPOT",
    "YARN_STORE",
    "ICE_CREAM_SHOP",
    "PET_CAFE",
    "SMOOTHIE_SHOP",
    "FARMERS_MARKET",
]

class WireModel(BaseModel):
    """Common permissive model configuration for evolving environment payloads."""

    model_config = ConfigDict(extra="ignore")

class PlantTile(WireModel):
    """A planted crop and its current growth, watering, and yield state."""
    kind: Literal["PLANT"]
    crop: Crop
    planted_day: int
    watered_today: bool
    consecutive_unwatered: int = Field(ge=0)
    yield_units: int = Field(ge=0)
    max_lifespan_step: int
    fertilized_until_day: int


class WeedTile(WireModel):
    """An obstructed board tile that can be removed with DIG."""
    kind: Literal["WEED"]


class CoopTile(WireModel):
    """A coop, optionally occupied by a goose."""
    kind: Literal["COOP"]
    animal: Literal["GOOSE"] | None = None
    placed_day: int
    yield_units: int = Field(ge=0)
    fed_today: bool
    consecutive_unfed: int = Field(ge=0)
    cared_today: bool
    fertilizer_available: bool
    pending_care_bonus: int = Field(ge=0)


class PastureTile(WireModel):
    """A pasture, optionally occupied by an animal."""
    kind: Literal["PASTURE"]
    animal: Literal["COW", "SHEEP"] | None = None
    placed_day: int
    yield_units: int = Field(ge=0)
    fed_today: bool
    consecutive_unfed: int = Field(ge=0)
    cared_today: bool
    fertilizer_available: bool
    pending_care_bonus: int = Field(ge=0)

type StructureTile = Annotated[
    PlantTile | WeedTile | CoopTile | PastureTile, Field(discriminator="kind")
]
type Tile = Literal["LOCKED"] | StructureTile | None

class Farm(WireModel):
    """The public state of one player's farm."""
    money: float
    tiles: list[list[Tile]]
    farmer: Position
    hands: list[Position]
    unlocked_quadrants: list[Quadrant]
    hires_today: int = Field(ge=0)


class Market(WireModel):
    """The shared market inventory and current sale prices."""
    inventory: dict[Product, int]
    prices: dict[Product, int]


class Town(WireModel):
    """The currently unlocked town shops."""
    unlocked_shops: list[Shop]


class PrivateState(WireModel):
    """The current player's non-public shed, seeds, and carried items."""
    shed: dict[ShedItem, int]
    seeds: dict[Crop, int]
    inventories: list[dict[ShedItem, int]]


class Observation(WireModel):
    """The complete environment payload supplied to an agent each turn."""
    player: Literal[0, 1]
    step: int = Field(ge=0)
    day: int = Field(ge=0)
    hour: int = Field(ge=0)
    farms: list[Farm] = Field(min_length=2, max_length=2)
    market: Market
    town: Town
    private: PrivateState

class UnitCommand(WireModel):
    """Base model for a single farmer or hired-hand command."""
    op: Any

    def to_wire(self) -> list[Any]:
        return [self.op]


class Move(UnitCommand):
    """Move a unit one tile in a cardinal direction."""
    op: Direction


class Pass(UnitCommand):
    """Leave a unit idle for the current turn."""
    op: Literal["PASS"] = "PASS"

class Pickup(UnitCommand):
    """Take one or more items from the shed."""
    op: Literal["PICKUP"] = "PICKUP"
    item: ShedItem
    amount: int = Field(default=1, ge=1)

    @override
    def to_wire(self) -> list[Any]:
        return [self.op, self.item, self.amount]


class Place(UnitCommand):
    """Place carried items on a structure or into the adjacent shed."""
    op: Literal["PLACE"] = "PLACE"
    item: ShedItem
    amount: int = Field(default=1, ge=1)

    @override
    def to_wire(self) -> list[Any]:
        return [self.op, self.item, self.amount]


class Plant(UnitCommand):
    """Plant a seed on the unit's current tile."""
    op: Literal["PLANT"] = "PLANT"
    crop: Crop

    @override
    def to_wire(self) -> list[Any]:
        return [self.op, self.crop]

class TileOperation(UnitCommand):
    """A no-argument action performed on the unit's current tile."""
    op: Literal[
        "WATER",
        "HARVEST",
        "FERTILIZE",
        "FEED",
        "COLLECT_FERTILIZER",
        "CARE",
        "BUILD_COOP",
        "BUILD_PASTURE",
        "DIG",
        "DROP",
    ]

UnitAction: TypeAlias = Move | Pass | Pickup | Place | Plant | TileOperation

class MarketCommand(WireModel):
    """Base model for one market order."""
    op: Any

    def to_wire(self) -> list[Any]:
        return [self.op]

class BuySeed(MarketCommand):
    """Buy one or more crop seeds."""
    op: Literal["BUY_SEED"] = "BUY_SEED"
    crop: Crop
    amount: int = Field(ge=1)

    @override
    def to_wire(self) -> list[Any]:
        return [self.op, self.crop, self.amount]


class BuyAnimal(MarketCommand):
    """Buy one or more livestock animals."""
    op: Literal["BUY_ANIMAL"] = "BUY_ANIMAL"
    animal: Animal
    amount: int = Field(ge=1)

    @override
    def to_wire(self) -> list[Any]:
        return [self.op, self.animal, self.amount]


class BuyProduct(MarketCommand):
    """Buy wheat or fertilizer from the market."""
    op: Literal["BUY_PRODUCT"] = "BUY_PRODUCT"
    item: Literal["WHEAT", "FERTILIZER"]
    amount: int = Field(ge=1)

    @override
    def to_wire(self) -> list[Any]:
        return [self.op, self.item, self.amount]


class Sell(MarketCommand):
    """Sell harvested product to the market."""
    op: Literal["SELL"] = "SELL"
    item: Product
    amount: int = Field(ge=1)

    @override
    def to_wire(self) -> list[Any]:
        return [self.op, self.item, self.amount]


class Hire(MarketCommand):
    """Hire a farm hand for the rest of the current day."""
    op: Literal["HIRE"] = "HIRE"


class BuyLand(MarketCommand):
    """Unlock the next available farm quadrant."""
    op: Literal["BUY_LAND"] = "BUY_LAND"

MarketAction: TypeAlias = BuySeed | BuyAnimal | BuyProduct | Sell | Hire | BuyLand

def _parse_unit_command(value: Any) -> Any:
    if isinstance(value, UnitCommand):
        return value
    if not isinstance(value, list) or not value or not isinstance(value[0], str):
        return value
    op, *args = value
    if op in {"PICKUP", "PLACE"}:
        return {"op": op, "item": args[0], "amount": args[1] if len(args) > 1 else 1}
    if op == "PLANT":
        return {"op": op, "crop": args[0]}
    return {"op": op}


def _parse_market_command(value: Any) -> Any:
    if isinstance(value, MarketCommand):
        return value
    if not isinstance(value, list) or not value or not isinstance(value[0], str):
        return value
    op, *args = value
    if op == "BUY_SEED":
        return {"op": op, "crop": args[0], "amount": args[1]}
    if op == "BUY_ANIMAL":
        return {"op": op, "animal": args[0], "amount": args[1]}
    if op in {"BUY_PRODUCT", "SELL"}:
        return {"op": op, "item": args[0], "amount": args[1]}
    return {"op": op}

class AgentAction(WireModel):
    """A typed action response that accepts and emits Kaggriculture wire format."""

    farmer: UnitAction = Field(default_factory=Pass)
    hands: list[UnitAction] = Field(default_factory=list)
    market: list[MarketAction] = Field(default_factory=list)

    @field_validator("farmer", mode="before")
    @classmethod
    def parse_farmer(cls, value: Any) -> Any:
        return _parse_unit_command(value)

    @field_validator("hands", mode="before")
    @classmethod
    def parse_hands(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [_parse_unit_command(command) for command in value]
        return value

    @field_validator("market", mode="before")
    @classmethod
    def parse_market(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [_parse_market_command(command) for command in value]
        return value

    def to_wire(self) -> dict[str, Any]:
        return {
            "farmer": self.farmer.to_wire(),
            "hands": [command.to_wire() for command in self.hands],
            "market": [command.to_wire() for command in self.market],
        }

from random import choice

DIRECTIONS: tuple[Direction, ...] = ("NORTH", "SOUTH", "EAST", "WEST")

def random_walk_agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Validate an observation and return one random legal movement action."""

    Observation.model_validate(obs)
    action = AgentAction(farmer=Move(op=choice(DIRECTIONS)))
    return action.to_wire()

from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
result = env.run([random_walk_agent, "random"])

final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s.reward}, status={s.status}")