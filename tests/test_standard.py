import decimal

import pytest

from jsno import jsonify, unjsonify, UnjsonifyError


def test_jsonify_decimal():
    assert jsonify(decimal.Decimal("99.9")) == "99.9"


def test_unjsonify_decimal():
    assert unjsonify[decimal.Decimal]("99.9") == decimal.Decimal("99.9")


def test_unjsonify_decimal_from_int():
    assert unjsonify[decimal.Decimal](100) == decimal.Decimal("100")
