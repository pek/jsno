import dataclasses
import enum
import pytest


from jsno import jsonify, unjsonify, UnjsonifyError


class Color(enum.Enum):
    Red = 1
    Green = 2
    Blue = 3

class Material(enum.IntEnum):
    Wood = 1
    Metal = 2
    Plastic = 3


def test_jsonify_enums():
    assert jsonify(Color.Blue) == "Blue"


def test_jsonify_intenums():
    assert jsonify(Material.Metal) == 2

def test_unjsonify_enum():
    assert unjsonify[Color]("Blue") == Color.Blue


def test_unjsonify_enum_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[Color]("White")


def test_unjsonify_intenum():
    assert unjsonify[Material](2) == Material.Metal


def test_unjsonify_intenum_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[Material](0)


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


def test_jsonify_dataclass():
    box = Box(
        name="Testbox",
        width=1000.1,
        height=223.5,
        bricks=[
            Brick(color=Color.Green, width=6, height=1, material=Material.Plastic),
            Brick(color=Color.Red, width=4, height=1),
        ]
    )

    assert jsonify(box) == {
        "name": "Testbox",
        "width": 1000.1,
        "height": 223.5,
        "bricks": [
            {"color": "Green", "width": 6, "height": 1, "material": 3},
            {"color": "Red", "width": 4, "height": 1},
        ]
    }

def test_unjsonify_dataclass():
    json_box = {
        "name": "Testbox",
        "width": 1000.1,
        "height": 223.5,
        "bricks": [
            {"color": "Green", "width": 6, "height": 1, "material": 3},
            {"color": "Red", "width": 4, "height": 1},
        ]
    }

    box = Box(
        name="Testbox",
        width=1000.1,
        height=223.5,
        bricks=[
            Brick(color=Color.Green, width=6, height=1, material=Material.Plastic),
            Brick(color=Color.Red, width=4, height=1),
        ]
    )

    assert unjsonify[Box](json_box) == box

@dataclasses.dataclass
class EmailAddress:
    user: str
    domain: str

    def jsonify(self) -> str:
        return f'{self.user}@{self.domain}'


def test_jsonify_with_jsonify_method():
    email = EmailAddress(user="foobar", domain="example.com")

    assert jsonify(email) == "foobar@example.com"



