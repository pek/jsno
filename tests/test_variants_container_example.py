from dataclasses import dataclass

from jsno import jsonify, unjsonify, variantfamily


@variantfamily(label="type")
class Variant:
    ...


@dataclass
class A(Variant):
    my_int: int
    my_bool: bool = False


@dataclass
class B(Variant):
    my_int: int
    my_bool: bool = True


@dataclass
class C(Variant):
    my_str: str


@dataclass
class Container:
    objects: list[Variant]


def test_variants_container_example():

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
