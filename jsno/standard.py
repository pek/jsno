"""
Jsonification and unjsonification for standard Python types.

* datetime.datetime
* datetime.date
* datetime.time
* datetime.timezone
* decimal.Decimal
* pathlib.Path
* zoneinfo.ZoneInfo
* enum.Enum
* ranges

"""

import dataclasses
import decimal
import enum
import pathlib
import re
import uuid
import zoneinfo

from types import NoneType, SimpleNamespace
from typing import Any

from jsno.jsonify import jsonify
from jsno.unjsonify import unjsonify, typecheck, UnjsonifyError, cast


def register_cast_factory(type_, jsontype):

    @unjsonify.register_factory(type_)
    def _(as_type):

        def specialized(value):
            if not isinstance(value, jsontype):
                raise UnjsonifyError(value, as_type)

            if isinstance(value, as_type):
                return value

            try:
                return as_type(value)
            except ValueError as exc:
                detail = exc.args[0]

            raise UnjsonifyError(value, as_type, detail)

        return specialized


# marking types to be jsonified as strings


def jsonify_to_string(value: Any) -> str:
    return str(value)


def jsonify_as_string(type_: type, exceptions: type | tuple[type, ...] = ()) -> type:
    jsonify.register(type_)(jsonify_to_string)

    if exceptions:

        @unjsonify.register(type_)
        def _(value, as_type):
            typecheck(value, str, as_type)
            try:
                return cast(value, as_type)
            except Exception as exc:
                if not isinstance(exc, exceptions):
                    raise

                detail = exc.args[0]

            raise UnjsonifyError(value, as_type, detail)

    else:
        register_cast_factory(type_, str)

    return type_


# NoneType, jsonify is not needed

register_cast_factory(NoneType, NoneType)


# str

jsonify_as_string(str)

# bool, jsonify is not needed


register_cast_factory(bool, bool)


# int


@jsonify.register(int)
def _(value):
    return int(value)


register_cast_factory(int, int)


# float


@jsonify.register(float)
def _(value):
    return float(value)


register_cast_factory(float, (float, int))


# enums


@jsonify.register(enum.Enum)
def _(enum):
    return enum.name


@unjsonify.register(enum.Enum)
def _(value, as_type):
    typecheck(value, str, as_type)
    try:
        return getattr(as_type, value)
    except AttributeError:
        pass

    raise UnjsonifyError(value, as_type)


# zoneinfo

jsonify_as_string(zoneinfo.ZoneInfo, exceptions=(zoneinfo.ZoneInfoNotFoundError))

# decimal


@jsonify.register(decimal.Decimal)
def _(value):
    """
    Always jsnonify Decimal as a string.
    """
    return str(value)


@unjsonify.register(decimal.Decimal)
def _(value, as_type):
    typecheck(value, (str, int), as_type)

    return as_type(value)


# pathlib.Path

jsonify_as_string(pathlib.Path)


# uuid.UUID

jsonify_as_string(uuid.UUID)


# complex numbers

jsonify_as_string(complex)


@jsonify.register(range)
def _(value):
    result = {"start": value.start, "stop": value.stop}
    if value.step != 1:
        result["step"] = value.step
    return result


@dataclasses.dataclass(slots=True, frozen=True)
class Range:
    start: int
    stop: int
    step: int | None = None


@unjsonify.register(range)
def _(value, as_type):
    it = unjsonify[Range](value)
    if it.step == 0:
        raise UnjsonifyError(value, as_type, "Range step must not be zero")

    return as_type(it.start, it.stop, it.step or 1)


# re.Pattern


@jsonify.register(re.Pattern)
def _(value):
    return value.pattern


@unjsonify.register(re.Pattern)
def _(value, as_type):
    return re.compile(value)


# types.SimpleNamespace

@jsonify.register(SimpleNamespace)
def _(value):
    return jsonify(value.__dict__)


@unjsonify.register(SimpleNamespace)
def _(value, as_type):
    typecheck(value, dict, as_type)
    return as_type(**value)
