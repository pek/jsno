from datetime import datetime
from typing import TypedDict, NotRequired, Required, NamedTuple

import pytest

from jsno import jsonify, unjsonify, UnjsonifyError


class ApiKey(TypedDict):
    name: NotRequired[str]
    value: str
    created_at: datetime


def test_unjsonify_typed_dict():
    apikey = unjsonify[ApiKey]({"value": "XXX", "created_at": "2023-08-05T07:22:33"})
    assert apikey == {"value": "XXX", "created_at": datetime(2023, 8, 5, 7, 22, 33)}


class ApiKey2(TypedDict, total=False):
    name: str
    value: Required[str]
    created_at: datetime


def test_unjsonify_nontotal_typed_dict():
    apikey = unjsonify[ApiKey2]({"value": "XXX", "created_at": "2023-08-05T07:22:33"})
    assert apikey == {"value": "XXX", "created_at": datetime(2023, 8, 5, 7, 22, 33)}


def test_unjsonify_nontotal_typed_dict_missing_required():
    with pytest.raises(UnjsonifyError):
        unjsonify[ApiKey2]({"name": "key", "created_at": "2023-08-05T07:22:33"})


def test_unjsonify_nontotal_typed_dict_extra_key():
    with pytest.raises(UnjsonifyError):
        unjsonify[ApiKey2]({"value": "XXX", "treated_at": "2023-08-05T07:22:33"})


def test_unjsonify_nontotal_typed_dict_ignore_extra_key():
    with unjsonify.ignore_extra_keys():
        apikey = unjsonify[ApiKey2]({"value": "XXX", "treated_at": "2023-08-05T07:22:33"})
        assert apikey == {"value": "XXX"}


class LogEntry(NamedTuple):
    date: datetime
    message: str


entry = LogEntry(date=datetime(2023, 8, 5, 8, 32, 10), message="fail")
json = ["2023-08-05T08:32:10", "fail"]


def test_jsnoify_namedtuple():
    assert jsonify(entry) == json


def test_unjsonify_namedtuple():
    assert unjsonify[LogEntry](json) == entry


def test_unjsonify_namedtuple_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[LogEntry](["2023-08-05T08:32:10"])
