from datetime import datetime
from typing import TypedDict, NotRequired, Required, NamedTuple

import pytest

from jsno import jsonify, unjsonify, UnjsonifyError


def test_unjsonify_typed_dict():
    class ApiKey(TypedDict):
        name: NotRequired[str]
        value: str
        created_at: datetime

    apikey = unjsonify[ApiKey]({"value": "XXX", "created_at": "2023-08-05T07:22:33"})

    assert apikey == {"value": "XXX", "created_at": datetime(2023, 8, 5, 7, 22, 33)}


def test_unjsonify_nontotal_typed_dict():
    class ApiKey(TypedDict, total=False):
        name: str
        value: Required[str]
        created_at: datetime

    apikey = unjsonify[ApiKey]({"value": "XXX", "created_at": "2023-08-05T07:22:33"})

    assert apikey == {"value": "XXX", "created_at": datetime(2023, 8, 5, 7, 22, 33)}

    with pytest.raises(UnjsonifyError):
        unjsonify[ApiKey]({"name": "key", "created_at": "2023-08-05T07:22:33"})

    with pytest.raises(UnjsonifyError):
        unjsonify[ApiKey]({"value": "XXX", "treated_at": "2023-08-05T07:22:33"})


def test_namedtuple():

    class LogEntry(NamedTuple):
        date: datetime
        message: str

    entry = LogEntry(date=datetime(2023, 8, 5, 8, 32, 10), message="fail")
    json = ["2023-08-05T08:32:10", "fail"]

    assert jsonify(entry) == json

    assert unjsonify[LogEntry](json) == entry
