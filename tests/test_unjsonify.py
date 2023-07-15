import collections
import dataclasses
import datetime
import enum
import pytest
import zoneinfo

from typing import Optional, Dict, List

from jsno.unjsonify import unjsonify, UnjsonifyError


helsinki = zoneinfo.ZoneInfo("Europe/Helsinki")
utc = zoneinfo.ZoneInfo("UTC")


def test_unjsonify_none():
    assert unjsonify[type(None)](None) == None


def test_unjsonify_none_from_string_fails():
    with pytest.raises(UnjsonifyError):
        assert unjsonify[type(None)]("foo") == None


def test_unjsonify_string():
    assert unjsonify[str]("foo") == "foo"


def test_unjsonify_float():
    assert unjsonify[float](12.34) == 12.34


def test_unjsonify_dict():
    assert unjsonify[dict]({"x": [123]}) == {"x": [123]}


def test_unjsonify_counter():
    counter = unjsonify[collections.Counter]({"x": 12, "y": 33})
    assert isinstance(counter, collections.Counter)
    assert counter == {"x": 12, "y": 33}


def test_unjsonify_list():
    assert unjsonify[list]([1, 2, 3]) == [1, 2, 3]


def test_unjsonify_typed_dict():
    assert unjsonify[dict[str, int]]({'x': 1, 'y': 2}) == {'x': 1, 'y': 2}


def test_unjsonify_list_of_floats():
    assert unjsonify[list[float]]([1.0, 2.0, 3.0]) == [1, 2, 3.0]


def test_unjsonify_list_of_bools():
    assert unjsonify[list[bool]]([True, False]) == [True, False]


def test_unjsonify_set_of_ints():
    assert unjsonify[set[int]]([2, 3, 4, 102]) == set((2, 3, 4, 102))


def test_unjsonify_list_of_bools_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[list[bool]]([True, 120])


def test_unjsonify_single_typearg_tuple():
    assert unjsonify[tuple[float]]([1.0, 2.0, 3.0]) == (1, 2, 3.0)


def test_unjsonify_multiple_typearg_tuple():
    assert unjsonify[tuple[float, str]]([1.0, "Yes"]) == (1, "Yes")


def test_unjsonify_multiple_typearg_tuple_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[tuple[float, str]]([1.0, "Yes", 3])


def test_unjsonify_list_of_union_types():
    assert unjsonify[List[str | int]](["Yes", 51, "No"]) == ["Yes", 51, "No"]


def test_unjsonify_list_of_union_types2():
    assert unjsonify[List[int | str]](["Yes", 51, "No"]) == ["Yes", 51, "No"]

def test_unjsonify_list_of_union_types3():
    assert unjsonify[List[list[bool] | int | str]](["Yes", 51, [True]]) == ["Yes", 51, [True]]


def test_unjsonify_list_of_typing_optionals():
    assert unjsonify[List[Optional[str]]](["Yes", None, "No"]) == ["Yes", None, "No"]


def test_unjsonify_list_of_option_types():
    assert unjsonify[list[str | None]](["Yes", None, "No"]) == ["Yes", None, "No"]


def test_unjsonify_list_of_datetimes():
    assert (
        unjsonify[list[datetime.datetime]](
            [
                "2023-07-15T08:39:00+03:00",
                "2023-07-15T08:40:10Z",
                "2023-07-15T08:41:20",
                "2023-07-15T08:39:00.000001+03:00",
                "2023-07-15T08:40:10.000120Z",
                "5012-07-15T08:41:20.123400",
            ]
        ) == (
            [
                datetime.datetime(2023, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(2023, 7, 15, 8, 40, 10, tzinfo=utc),
                datetime.datetime(2023, 7, 15, 8, 41, 20),
                datetime.datetime(2023, 7, 15, 8, 39, 0, 1, tzinfo=helsinki),
                datetime.datetime(2023, 7, 15, 8, 40, 10, 120, tzinfo=utc),
                datetime.datetime(5012, 7, 15, 8, 41, 20, 123400),
            ]
        )
    )


def test_unjsonify_dictionary_of_dates():
    assert(
        unjsonify[dict[datetime.date, datetime.date]](
            {
                "2023-07-15": "2023-07-16",
                "2023-07-16": "2023-07-17",
            }
        ) == (
            {
                datetime.date(2023, 7, 15): datetime.date(2023, 7, 16),
                datetime.date(2023, 7, 16): datetime.date(2023, 7, 17),
            }
        )
    )


def test_unjsonify_datetime_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[datetime.datetime]('2023-13-13T12:34:56')

