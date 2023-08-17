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
