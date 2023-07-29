import collections
import datetime
import pytest
import zoneinfo

from typing import Any, Callable, Optional, List, Literal

from jsno.unjsonify import unjsonify, UnjsonifyError


helsinki = zoneinfo.ZoneInfo("Europe/Helsinki")
utc = zoneinfo.ZoneInfo("UTC")


def test_unjsonify_none():
    assert unjsonify[type(None)](None) is None


def test_unjsonify_any():
    assert unjsonify[Any](None) is None


def test_unjsonify_none_from_string_fails():
    with pytest.raises(UnjsonifyError):
        assert unjsonify[type(None)]("foo") is None


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
    assert unjsonify[list[float]]([1.0, 2.0, 3.0, 0, -2]) == [1, 2, 3.0, 0, -2]


def test_unjsonify_list_of_bools():
    assert unjsonify[list[bool]]([True, False]) == [True, False]


def test_unjsonify_set_of_ints():
    assert unjsonify[set[int]]([2, 3, 4, 102]) == set((2, 3, 4, 102))


def test_unjsonify_frozenset_of_ints():
    assert unjsonify[frozenset[int]]([2, 3, 4, 102]) == frozenset((2, 3, 4, 102))


def test_unjsonify_list_of_bools_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[list[bool]]([True, 120])


def test_unjsonify_n_ary_tuple():
    assert unjsonify[tuple[float, ...]]([1.0, 2.0, 3.0]) == (1, 2, 3.0)


def test_unjsonify_empty_tuple():
    assert unjsonify[tuple[()]]([]) == ()


def test_unjsonify_malformed_type_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[tuple[bool, str, ...]]([True, "x"])


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


def test_unjsonify_literal():
    assert unjsonify[Literal["A", "B"]]("B") == "B"


def test_unjsonify_literal_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[Literal["A", "B"]]("C")


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


def test_unjsonify_bytes():
    assert unjsonify[bytes]("Zm9vYmFyIQ==") == b"foobar!"


def test_unjsonify_str_subclass():

    class SpecialString(str):
        pass

    assert unjsonify[SpecialString]("special") == SpecialString("special")


def test_unjsonify_float_subclass():

    class SpecialFloat(float):
        pass

    assert unjsonify[SpecialFloat](6.66) == SpecialFloat(6.66)


def test_unjsonify_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[dict]("ffff")


def test_unjsonify_union_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[dict | str](None)


def test_unjsonify_not_defined():
    with pytest.raises(TypeError):
        unjsonify[Callable]("call")


def test_unjsonify_date_failure():
    with pytest.raises(TypeError):
        unjsonify[datetime.date]("today")
