"""
Jsonification and unjsonification for standard Python types.

* datetime.datetime
* datetime.date
* decimal.Decimal
* pathlib.Path
* zoneinfo.ZoneInfo
* enum.Enum
* tuples
* ranges

"""

import dataclasses
import datetime
import decimal
import enum
import pathlib
import zoneinfo

from types import NoneType


from jsno.abc import unjsonify_sequence
from jsno.jsonify import jsonify
from jsno.unjsonify import unjsonify, typecheck, raise_error, cast
from jsno.utils import get_args


# marking types to be jsonified as strings


def jsonify_to_string(value):
    return str(value)


def unjsonify_from_string(value, as_type):
    typecheck(value, str, as_type)
    return cast(value, as_type)


def jsonify_as_string(type_, exceptions=()):
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


# tuples


@unjsonify.register(tuple)
def _(value, as_type):
    """
    Unjsonify tuples.

    Tuples are a subclass of Sequence, but tuples with more
    than one argument are treated specially.

    """

    arg_types = get_args(as_type)
    if arg_types and len(arg_types) == 2 and arg_types[1] is Ellipsis:
        # special case for a N-length one-type tuple (tuple[T, ...])
        # note: this accepts the empty tuple. This might not be strictly allowed
        return unjsonify_sequence(value, as_type)

    # tuple types of the form tuple[int, str, ...] are not supported now

    typecheck(value, list, as_type)

    if len(value) != len(arg_types):
        raise_error(value, as_type)

    return as_type(
        unjsonify[type_](item)
        for (item, type_) in zip(value, arg_types)
    )


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


# datetime.date


@jsonify.register(datetime.date)
def _(date):
    return f"{date.year}-{date.month:02}-{date.day:02}"


@unjsonify.register(datetime.date)
def _(value, as_type):
    typecheck(value, str, as_type)
    try:
        (ys, ms, ds) = value.split("-")
        return as_type(int(ys), int(ms), int(ds))
    except ValueError as exc:
        detail = exc.args[0]

    raise_error(value, as_type, detail)


# datetime.datetime


UTC = zoneinfo.ZoneInfo("UTC")


def is_utc_datetime(dt) -> bool:
    return (
        dt.tzinfo is not None and
        dt.tzinfo.utcoffset(dt).total_seconds() == 0.0
    )


@jsonify.register(datetime.datetime)
def _(value):
    """
    Format the datetime as a string. Uses isoformat, except  when
    the timezone is UTC, attaches "Z" as the timezone, instead of "+00:00"
    """

    if is_utc_datetime(value):
        return f"{value.date()}T{value.time()}Z"
    else:
        return value.isoformat()


@unjsonify.register(datetime.datetime)
def _(value, as_type):
    typecheck(value, str, as_type)
    try:
        return as_type.fromisoformat(value)
    except ValueError as exc:
        detail = exc.args[0]

    raise_error(value, as_type, detail)


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

# complex numbers

jsonify_as_string(complex)


@jsonify.register(range)
def _(value):
    result = {"start": value.start, "stop": value.stop}
    if value.step != 1:
        result["step"] = value.step
    return result


@dataclasses.dataclass
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
