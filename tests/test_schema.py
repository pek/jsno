from datetime import date
from typing import NotRequired, Annotated

import pytest

from jsno import unjsonify, UnjsonifyError, property_name, Schema


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


def test_unjsonify_schema():
    assert (
        unjsonify[list[schema]]([{
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": ["2023-08-12"]
        }]) ==
        [{
            "first-name": "Foo",
            "last-name": "Bar",
            "dates-of-birth": [date(2023, 8, 12)],
            "extra-info": None
        }]
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


def test_from_arguments():

    def testfunc(x, foo: str = "FOO", *, dt: date):
        return f"{foo}: {dt.year} [{x}]"

    schema = Schema.from_arguments(testfunc)

    assert (
        testfunc(**schema.unjsonify({"foo": "OOF", "dt": "2023-08-20", "x": 0})) ==
        "OOF: 2023 [0]"
    )

    assert (
        testfunc(**schema.unjsonify({"dt": "2023-08-20", "x": 0})) ==
        "FOO: 2023 [0]"
    )


def test_from_keyword_only_arguments():

    def testfunc(x=1, foo: str = "FOO", *, dt: date):
        return f"{foo}: {dt.year} [{x}]"

    # using "ignore_extra_keys" but no kwargs
    schema = Schema.from_arguments(
        testfunc,
        keywords_only=True,
        ignore_extra_keys=True
    )

    assert (
        testfunc(**schema.unjsonify({"foo": "OOF", "dt": "2023-08-20", "x": 0})) ==
        "FOO: 2023 [1]"
    )


def test_from_keyword_only_arguments_with_kwargs():

    def testfunc(x=1, foo: str = "FOO", *, dt: date, **kwargs):
        return f"{foo}: {dt.year} [{x}] {kwargs}"

    schema = Schema.from_arguments(testfunc)

    assert (
        testfunc(**schema.unjsonify({"foo": "OOF", "dt": "2023-08-20", "z": 0})) ==
        "OOF: 2023 [1] {'z': 0}"
    )


def test_property_name_with_funcion_args_schema():

    def testfunc(class_name: Annotated[str, property_name("class-name")]):
        return class_name

    schema = Schema.from_arguments(testfunc)

    assert testfunc(**schema.unjsonify({"class-name": "abc"})) == "abc"
