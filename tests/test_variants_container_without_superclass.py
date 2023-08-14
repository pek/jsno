from dataclasses import dataclass

from jsno import jsonify, unjsonify, variantlabel


@dataclass
@variantlabel(key="type")
class A:
    my_int: int
    my_bool: bool = False


@dataclass
@variantlabel(key="type")
class B:
    my_int: int
    my_bool: bool = True


@dataclass
@variantlabel(key="type")
class C:
    my_str: str


@dataclass
class Container:
    objects: list[A | B | C]


def test_variants_container_with_orphan_family_example():

    data = {
        "objects": [
            {"type": "A", "my_int": 42},
            {"type": "C", "my_str": "hello world"},
            {"type": "B", "my_int": 123},
            {"type": "A", "my_int": 321, "my_bool": True}
        ]
    }
    # note: no auto-conversion from camelCase

    c = unjsonify[Container](data)

    assert (
        c ==
        Container(
            objects=[
                A(my_int=42, my_bool=False),
                C(my_str='hello world'),
                B(my_int=123, my_bool=True),
                A(my_int=321, my_bool=True)
            ]
        )
    )

    assert unjsonify[Container](jsonify(c)) == c
