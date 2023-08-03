from dataclasses import dataclass
from typing import Annotated

import pytest

from jsno import unjsonify, Constraint, UnjsonifyError


def test_function_constraint():
    PositiveInt = Annotated[int, Constraint(lambda x: x > 0)]

    assert unjsonify[PositiveInt](123) == 123

    with pytest.raises(UnjsonifyError):
        unjsonify[PositiveInt](0)


def test_range():
    Number = Annotated[int, Constraint.range(min=1, max=3)]

    assert unjsonify[Number](1) == 1

    with pytest.raises(UnjsonifyError):
        unjsonify[Number](0)


def test_len_range():
    Identifier = Annotated[str, Constraint.len(min=16, max=16)]

    assert unjsonify[Identifier]("1234567890abcdef") == "1234567890abcdef"

    with pytest.raises(UnjsonifyError):
        unjsonify[Identifier]("whaat")


def test_len_min():
    Identifier = Annotated[str, Constraint.len(min=16)]

    assert unjsonify[Identifier]("1234567890abcdef") == "1234567890abcdef"

    with pytest.raises(UnjsonifyError):
        unjsonify[Identifier]("whaat")


def test_len_max():
    Identifier = Annotated[str, Constraint.len(max=3)]

    assert unjsonify[Identifier]("123") == "123"

    with pytest.raises(UnjsonifyError):
        unjsonify[Identifier]("whaat")


@dataclass
class User:
    username: str
    email: Annotated[str, Constraint(lambda it: "@" in it, "Valid email address")]


def test_email_contraint():
    assert (
        unjsonify[User]({"username": "usr", "email": "user@domain.com"}) ==
        User("usr", "user@domain.com")
    )
