import dataclasses
import datetime
import enum
import zoneinfo

from jsno.jsonify import jsonify


helsinki = zoneinfo.ZoneInfo("Europe/Helsinki")
utc = zoneinfo.ZoneInfo("UTC")


def test_jsonify_none():
    assert jsonify(None) == None


def test_jsonify_string():
    assert jsonify("foo") == "foo"


def test_jsonify_int():
    assert jsonify(123) == 123


def test_jsonify_dict():
    assert jsonify({"x": {"z": 123}}) == {"x": {"z": 123}}


def test_jsonify_list_of_bools():
    assert jsonify([True, False]) == [True, False]


def test_jsonify_dates():

    assert (
        jsonify(
            [
                datetime.datetime(2023, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(2023, 7, 15, 8, 40, 10, tzinfo=utc),
                datetime.datetime(2023, 7, 15, 8, 41, 20),
                datetime.datetime(2023, 7, 15, 8, 39, 0, 1, tzinfo=helsinki),
                datetime.datetime(2023, 7, 15, 8, 40, 10, 120, tzinfo=utc),
                datetime.datetime(5012, 7, 15, 8, 41, 20, 123400),
            ]
        ) == [
            "2023-07-15T08:39:00+03:00",
            "2023-07-15T08:40:10Z",
            "2023-07-15T08:41:20",
            "2023-07-15T08:39:00.000001+03:00",
            "2023-07-15T08:40:10.000120Z",
            "5012-07-15T08:41:20.123400",
        ]
    )

def test_jsonify_old_dates():
    assert (
        jsonify(
            [
                datetime.datetime(1940, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(1960, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(1980, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(1981, 7, 15, 8, 39, 0, tzinfo=helsinki),
            ]
        ) == [
            "1940-07-15T08:39:00+02:00",
            "1960-07-15T08:39:00+02:00",
            "1980-07-15T08:39:00+02:00",
            "1981-07-15T08:39:00+03:00",
        ]
    )

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
