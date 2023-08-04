import dataclasses

from jsno import unjsonify, Record


def test_record():
    items = [
        {"name": "one", "age": 11},
        {"name": "two", "age": 7},
    ]

    records = unjsonify[list[Record(name=str, age=int)]](items)

    assert records[0].name == "one"
    assert records[1].age == 7


def test_record_with_default():
    items = [
        {"name": "one", "age": 11, "bool": True},
        {"name": "two", "age": 7},
    ]

    records = unjsonify[list[Record(name=str, age=int, bool=(bool, False))]](items)

    assert records[0].bool is True
    assert records[1].bool is False


def test_record_with_default_field():
    items = [
        {"name": "one", "things": [1, 2, 3]},
        {"name": "two"},
    ]

    Guy = Record(
        name=str,
        things=(list[int], dataclasses.field(default_factory=list))
    )

    records = unjsonify[list[Guy]](items)

    assert records[0].things == [1, 2, 3]
    assert records[1].things == []
