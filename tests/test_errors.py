from datetime import timedelta
from typing import Callable

import pytest

from jsno import unjsonify, UnjsonifyError, Constraint


def test_unjsonify_dictionary_with_non_string_key():
    assert unjsonify[dict]({(1, 2): "key is not json"}) == {(1, 2): "key is not json"}


def test_unjsonify_typed_dictionary_with_non_string_key():
    with pytest.raises(UnjsonifyError):
        unjsonify[dict[str, str]]({(1, 2): "key is not json"})


def test_unjsonify_typed_dictionary_with_non_jsonifiable_key():
    with pytest.raises(UnjsonifyError):
        unjsonify[dict[str, str]]({(lambda: ()): "key is not json"})


def test_unjsonify_callable():
    with pytest.raises(TypeError) as err:
        unjsonify[Callable]({})

    assert str(err.value) == "Unjsonify not defined for Callable"


def test_unjsonify_list_of_callable():
    with pytest.raises(TypeError) as err:
        unjsonify[list[Callable]]({})

    assert str(err.value) == "Unjsonify not defined for Callable"


def test_unjsonify_list():
    with pytest.raises(TypeError) as err:
        unjsonify[[str]]

    assert str(err.value) == "Cannot unjsonify as [<class 'str'>] of type list"


def test_unjsonify_string():
    with pytest.raises(TypeError) as err:
        unjsonify["xx"]

    assert str(err.value) == "Cannot unjsonify as 'xx' of type str"


def test_range_constraint_error():
    with pytest.raises(UnjsonifyError) as err:
        unjsonify[int // Constraint.range(min=1, max=2)](3)

    assert str(err.value).endswith("Value must be in range 1..2")


def test_min_constraint_error():
    with pytest.raises(UnjsonifyError) as err:
        unjsonify[int // Constraint.range(min=1)](0)

    assert str(err.value).endswith("Value must be at least 1")


def test_regex_error():
    with pytest.raises(UnjsonifyError) as err:
        unjsonify[str // Constraint.regex(r"\d+")]("00x")

    assert str(err.value).endswith("Violates constraint: Regular expression '\\d+'")


def test_unjsonify_timedelta_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[timedelta]("xxx")


def test_unjsonify_timedelta_error2():
    with pytest.raises(UnjsonifyError):
        unjsonify[timedelta]("xx days")
