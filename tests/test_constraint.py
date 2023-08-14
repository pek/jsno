from dataclasses import dataclass
from typing import Annotated

import pytest

from jsno import unjsonify, Constraint, UnjsonifyError, constraint


def test_function_constraint():
    PositiveInt = Annotated[int, Constraint(lambda x: x > 0)]

    assert unjsonify[PositiveInt](123) == 123

    with pytest.raises(UnjsonifyError):
        unjsonify[PositiveInt](0)


def test_range():
    Number = int // Constraint.range(min=1, max=3)

    assert unjsonify[Number](1) == 1

    with pytest.raises(UnjsonifyError):
        unjsonify[Number](0)


def test_len_range():
    Identifier = str // Constraint.len(min=16, max=16)

    assert unjsonify[Identifier]("1234567890abcdef") == "1234567890abcdef"

    with pytest.raises(UnjsonifyError):
        unjsonify[Identifier]("whaat")


def test_len_min():
    Identifier = str // Constraint.len(min=16)

    assert unjsonify[Identifier]("1234567890abcdef") == "1234567890abcdef"

    with pytest.raises(UnjsonifyError):
        unjsonify[Identifier]("whaat")


def test_len_max():
    Identifier = str // Constraint.len(max=3)

    assert unjsonify[Identifier]("123") == "123"

    with pytest.raises(UnjsonifyError):
        unjsonify[Identifier]("whaat")


# defining this outside the type annotation as it confuses flake8
EmailConstraint = Constraint(lambda it: "@" in it, "Valid email address")


@dataclass
class User:
    username: str
    email: str // EmailConstraint


def test_email_contraint():
    assert (
        unjsonify[User]({"username": "usr", "email": "user@domain.com"}) ==
        User("usr", "user@domain.com")
    )


def test_regex():
    Email = str // Constraint.regex(r"[\w\.]+@([\w-]+\.)+[\w-]{2,4}")

    assert unjsonify[Email]("valid.email@example.com") == "valid.email@example.com"

    with pytest.raises(UnjsonifyError):
        unjsonify[Email]("valid.email@example@com")


def test_double_constrait():
    Aaaaa = str // Constraint.regex(r"[a]+") // Constraint.len(min=5)

    assert unjsonify[Aaaaa]("aaaaa") == "aaaaa"

    with pytest.raises(UnjsonifyError):
        unjsonify[Aaaaa]("aaaaaaah")

    with pytest.raises(UnjsonifyError):
        unjsonify[Aaaaa]("aaa")


LiteralInt = Constraint.regex("[0-9]*")
LiteralString = Constraint.regex('".*"')


@dataclass
class LiteralValue:
    value: str // (LiteralInt | LiteralString)


def test_or_constraint():
    assert(
        unjsonify[list[LiteralValue]]([{"value": "123"}, {"value": '"xxx"'}]) ==
        [LiteralValue("123"), LiteralValue('"xxx"')]
    )

    with pytest.raises(UnjsonifyError):
        unjsonify[list[LiteralValue]]([{"value": "foo"}])


@dataclass
class LiteralValues:
    values: list[str // LiteralString]


def test_embedded_constraint():
    with pytest.raises(UnjsonifyError):
        unjsonify[list[LiteralValues]]([{"values": ["foo"]}])


@dataclass
@constraint(lambda it: it.min <= it.max)
class Range:
    min: int
    max: int


def test_dataclass_constraint():
    assert unjsonify[Range]({"min": 0, "max": 99}) == Range(min=0, max=99)

    with pytest.raises(UnjsonifyError):
        unjsonify[Range]({"min": 99, "max": 0})
