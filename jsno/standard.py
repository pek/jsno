"""
Jsonification and unjsonification for standard Python types.
"""

import datetime
import decimal
import enum

from types import NoneType


from jsno.abc import unjsonify_sequence
from jsno.jsonify import jsonify
from jsno.unjsonify import unjsonify, typecheck, raise_error, cast
from jsno.utils import format_datetime, get_args


# NoneType, jsonify is not needed

@unjsonify.register(NoneType)
def _(value, as_type):
    typecheck(value, NoneType, as_type)
    return None


# str


@jsonify.register(str)
def _(value):
    return str(value)


@unjsonify.register(str)
def _(value, as_type):
    typecheck(value, str, as_type)
    return cast(value, as_type)


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
    typecheck(value, float, as_type)
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
    if arg_types and len(arg_types) < 2:
        return unjsonify_sequence(value, as_type)

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
    return f'{date.year}-{date.month:02}-{date.day:02}'


@unjsonify.register(datetime.date)
def _(value, as_type):
    typecheck(value, str, as_type)
    try:
        (ys, ms, ds) = value.split('-')
        return as_type(int(ys), int(ms), int(ds))
    except ValueError as exc:
        detail = exc.args[0]

    raise_error(value, as_type, detail)


# datetime.datetime


@jsonify.register(datetime.datetime)
def _(datetime):
    return format_datetime(datetime)


@unjsonify.register(datetime.datetime)
def _(value, as_type):
    typecheck(value, str, as_type)
    try:
        return as_type.fromisoformat(value)
    except ValueError as exc:
        detail = exc.args[0]

    raise_error(value, as_type, detail)


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
