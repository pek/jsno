from datetime import date
from typing import NotRequired

import pytest

from jsno import UnjsonifyError, property_name, Schema


schema = Schema({
    "first-name": str,
    "last-name": str,
    "dates-of-birth": list[date],
    "extra-info": (str | None, None)
})


def test_schema():
    assert (
        schema.unjsonify({
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": ["2023-08-12"]
        }) ==
        {
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": [date(2023, 8, 12)],
            "extra-info": None
        }
    )


def test_schema_missing_property():
    with pytest.raises(UnjsonifyError):
        schema.unjsonify({
            "first-name": "Foo",
            "dates-of-birth": ["2023-08-12"],
        })


def test_schema_non_total():
    assert (
        schema.extend(total=False).unjsonify({
            "first-name": "Foo",
            "dates-of-birth": ["2023-08-12"],
        }) ==
        {
            "first-name": "Foo",
            "dates-of-birth": [date(2023, 8, 12)],
            "extra-info": None
        }
    )


def test_schema_extra_property():
    with pytest.raises(UnjsonifyError):
        schema.unjsonify({
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": [],
            "created_at": "2023-08-13",
        })


def test_schema_default_type():
    assert(
        schema.extend(default_type=date).unjsonify({
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": [],
            "created_at": "2023-08-13",
        }) ==
        {
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": [],
            "extra-info": None,
            "created_at": date(2023, 8, 13)
        }
    )


def test_schema_extend_schema():
    extensions = {
        "dates-of-birth": None,
        "extra-info": None,
        "last-name": str // property_name("LASTNAME")
    }
    assert(
        schema.extend(schema=extensions, extra_data_key="extra").unjsonify({
            "first-name": "Foo",
            "LASTNAME": "Bar",
            "unknown": [123]
        }) ==
        {
            "first-name": "Foo",
            "last-name": "Bar",
            "extra": {"unknown": [123]}
        }
    )

    with pytest.raises(UnjsonifyError):
        schema.extend(schema=extensions).unjsonify({
            "first-name": "Foo",
            "LASTNAME": "Bar",
            "extra-info": "extra",
        })


def test_schema_non_required_property():
    assert(
        schema.extend(schema={"created_at": NotRequired[date]}).unjsonify({
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": [],
        }) ==
        {
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": [],
            "extra-info": None,
        }
    )
