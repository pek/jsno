import decimal
import pathlib
import zoneinfo

import pytest

from jsno import jsonify, unjsonify, UnjsonifyError, jsonify_as_string


def run_tests(value, json):
    assert jsonify(value) == json
    assert unjsonify[type(value)](json) == value


def test_jsonify_decimal():
    assert jsonify(decimal.Decimal("99.9")) == "99.9"


def test_unjsonify_decimal():
    assert unjsonify[decimal.Decimal]("99.9") == decimal.Decimal("99.9")


def test_unjsonify_decimal_from_int():
    assert unjsonify[decimal.Decimal](100) == decimal.Decimal("100")


def test_jsonify_path():
    assert jsonify(pathlib.Path("/dev/null")) == "/dev/null"


def test_unjsonify_path():
    assert unjsonify[pathlib.Path]("/dev/null") == pathlib.Path("/dev/null")


def test_jsonify_zoneinfo():
    assert (
        jsonify(zoneinfo.ZoneInfo("Europe/Helsinki")) ==
        "Europe/Helsinki"
    )


def test_unjsonify_zoneinfo():
    assert (
        unjsonify[zoneinfo.ZoneInfo]("Europe/Helsinki") ==
        zoneinfo.ZoneInfo("Europe/Helsinki")
    )


def test_unjsonify_zoneinfo_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[zoneinfo.ZoneInfo]("Europe/Vantaa")


def test_jsonify_as_string_failure():

    class ZoneInfoSub(zoneinfo.ZoneInfo):
        pass

    jsonify_as_string(ZoneInfoSub, exceptions=(TypeError,))

    with pytest.raises(zoneinfo.ZoneInfoNotFoundError):
        unjsonify[ZoneInfoSub]("Europe/Vantaa")


def test_jsonify_range():
    run_tests(range(100), {"start": 0, "stop": 100})
    run_tests(range(10, 0, -1), {"start": 10, "stop": 0, "step": -1})


def test_jsonify_range_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[range]({"start": 1, "stop": 6, "step": 0})
