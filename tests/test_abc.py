import collections
import datetime
import dataclasses
import os

import pytest

from jsno import jsonify, unjsonify, UnjsonifyError


def test_jsonify_mapping():
    # os.environ is a Mapping type that is not a subclass of dict

    assert jsonify(os.environ) == jsonify(dict(os.environ))


def test_jsonify_mapping_2():
    dc = jsonify(os.environ)

    assert jsonify(collections.UserDict(dc)) == dc


def test_unjsonify_mapping():
    dc = jsonify(os.environ)

    userdict = unjsonify[collections.UserDict](dc)
    assert type(userdict) is collections.UserDict
    assert userdict == dc


def test_unjsonify_untyped_dict():
    assert unjsonify[dict]({"foo": 123}) == {"foo": 123}


def test_unjsonify_bytestring_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[bytes]("foo")


def test_jsonify_mixed_set():
    assert jsonify(set((1, 2, 3, "abc", None))) == [None, 1, 2, 3, "abc"]


def test_jsonify_unsortable():

    @dataclasses.dataclass
    class Wrap:
        value: str

        def __hash__(self):
            return hash(self.value)

    jsonified = jsonify(set((Wrap("x"), Wrap("y"))))

    assert (
        sorted(jsonified, key=lambda it: it["value"]) ==
        [{"value": "x"}, {"value": "y"}]
    )


def test_typed_dict_subtype():
    # test a problematic case of subclass of a typed dict not behaving
    # as expected

    DateDict = dict[str, datetime.date]

    # check that the typed dict is converted correctly
    registry = unjsonify[DateDict]({"today": "2023-08-05"})
    assert registry == {"today": datetime.date(2023, 8, 5)}

    # define a subclass
    class DateRegistry(DateDict):
        pass

    # subclass dictionary values are NOT correctly converted
    subregistry = unjsonify[DateRegistry]({"today": "2023-08-05"})
    assert type(subregistry) == DateRegistry
    assert subregistry == {"today": "2023-08-05"}

    # attach types to circumvent problem
    DateRegistryTyped = DateRegistry[str, datetime.date]

    typedregistry = unjsonify[DateRegistryTyped]({"today": "2023-08-05"})
    assert type(typedregistry) == DateRegistry
    assert registry == {"today": datetime.date(2023, 8, 5)}
