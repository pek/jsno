from typing import Callable

import pytest

from jsno.unjsonify import unjsonify, UnjsonifyError


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
