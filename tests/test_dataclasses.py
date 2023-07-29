"""
Tests for jsonifying and unjsonifying dataclasses and enum types.

"""

import dataclasses
import enum
import pytest

from typing import Any, Dict, List

from jsno import jsonify, unjsonify, jsonify_with_method, UnjsonifyError


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
    assert type(jsonify(Material.Metal)) is int


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
@jsonify_with_method
class EmailAddress:
    user: str
    domain: str

    def jsonify(self) -> str:
        return f'{self.user}@{self.domain}'

    @classmethod
    def unjsonify(cls, value):
        user, domain = value.split('@')
        return cls(user=user, domain=domain)


def test_jsonify_with_jsonify_method():
    email = EmailAddress(user="foobar", domain="example.com")

    assert jsonify(email) == "foobar@example.com"


def test_unjsonify_with_unjsonify_classmethod():
    email = unjsonify[EmailAddress]("foobar@example.com")

    assert email == EmailAddress(user="foobar", domain="example.com")


def test_ujsonify_with_missing_properties_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[Brick]({"color": "Yellow"})


def test_ujsonify_with_not_dict_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[Brick]("Something else")


def test_unjsonify_dataclass_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[Box]({})


@dataclasses.dataclass
class User:
    username: str
    password: str = 'pAssW0rd'
    metadata: List[Dict[str, Any]] = dataclasses.field(default_factory=list)


def test_jsonifty_dataclass_with_default_value():
    assert (
        jsonify(User(username="usr")) ==
        {"username": "usr", "password": "pAssW0rd", "metadata": []}
    )

    assert (
        jsonify(User(username="usr", password="", metadata=[{"key": 100}])) ==
        {"username": "usr", "password": "", "metadata": [{"key": 100}]}
    )


def test_unjsonifty_dataclass_with_default_value():
    user = unjsonify[User]({"username": "usr"})

    assert user == User(username="usr")
    assert user.password == "pAssW0rd"

    user = unjsonify[User]({"username": "usr", "password": "", "metadata": [{"key": 100}]})

    assert user == User(username="usr", password="", metadata=[{"key": 100}])
