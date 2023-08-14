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

from jsno.jsonify import jsonify, JSON
from jsno.unjsonify import unjsonify, typecheck, raise_error, cast


# marking types to be jsonified as strings


def jsonify_to_string(value: Any) -> str:
    return str(value)


def unjsonify_from_string(value: JSON, as_type: type) -> Any:
    typecheck(value, str, as_type)
    return cast(value, as_type)


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

            raise_error(value, as_type, detail)

    else:
        unjsonify.register(type_)(unjsonify_from_string)

    return type_


# NoneType, jsonify is not needed

@unjsonify.register(NoneType)
def _(value, as_type):
    typecheck(value, NoneType, as_type)
    return None


# str

jsonify_as_string(str)

# bool, jsonify is not needed


@unjsonify.register(bool)
def _(value, as_type):
    typecheck(value, bool, as_type)
    return cast(value, as_type)


# int


@jsonify.register(int)
def _(value):
    return int(value)


@unjsonify.register(int)
def _(value, as_type):
    typecheck(value, int, as_type)
    return cast(value, as_type)


# float


@jsonify.register(float)
def _(value):
    return float(value)


@unjsonify.register(float)
def _(value, as_type):
    typecheck(value, (float, int), as_type)
    return cast(value, as_type)


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

    raise_error(value, as_type)


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
        raise_error(value, as_type, "Range step must not be zero")

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
