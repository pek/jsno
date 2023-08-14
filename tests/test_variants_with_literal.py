from dataclasses import dataclass
from typing import Literal

from jsno import jsonify, unjsonify


@dataclass
class A:
    type: Literal["A"]
    my_int: int
    my_bool: bool = False


@dataclass
class B:
    type: Literal["B"]
    my_int: int
    my_bool: bool = True


@dataclass
class C:
    type: Literal["C"]
    my_str: str


@dataclass
class Container:
    objects: list[A | B | C]


def test_variants_container_with_literal_example():

    data = {
        "objects": [
            {"type": "A", "my_int": 42},
            {"type": "C", "my_str": "hello world"},
            {"type": "B", "my_int": 123},
            {"type": "A", "my_int": 321, "my_bool": True}
        ]
    }

    c = unjsonify[Container](data)

    assert (
        c ==
        Container(
            objects=[
                A(type="A", my_int=42, my_bool=False),
                C(type="C", my_str='hello world'),
                B(type="B", my_int=123, my_bool=True),
                A(type="A", my_int=321, my_bool=True)
            ]
        )
    )

    assert unjsonify[Container](jsonify(c)) == c
