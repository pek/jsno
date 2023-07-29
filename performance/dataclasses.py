import dataclasses
import enum


class Color(enum.Enum):
    Red = 1
    Green = 2
    Blue = 3


class Material(enum.IntEnum):
    Wood = 1
    Metal = 2
    Plastic = 3


@dataclasses.dataclass
class Brick:
    width: int
    height: int
    color: Color
    material: Material | None = None


@dataclasses.dataclass
class Box:
    name: str
    width: float
    height: float

    bricks: list[Brick]


example_box = Box(
    name="Example box",
    width=100.1,
    height=99.8,
    bricks=[
        Brick(width=3, height=2, color=color, material=material)
        for color in Color
        for material in list(Material) + [None]
    ]
)
