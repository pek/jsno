import dataclasses
import datetime
import functools
import types
import typing
import zoneinfo


union_types = (
    typing.Union ,   # Union[X] or Optional[X]
    types.UnionType  # X | Y or X | None
)


@functools.cache
def get_origin(type):
    """
    Cached version typing.get_origin() to make sure it's quick to check.
    """
    return typing.get_origin(type)


@functools.cache
def get_args(type):
    """
    Cached version typing.get_args() to make sure it's quick to check.
    """
    return typing.get_args(type)


def is_optional(type_) -> bool:
    """
    Check if a type object is instance of optional type
    (something that could be None)
    """

    return (
        get_origin(type_) in union_types and
        type(None) in get_args(type_)
    )


UTC = zoneinfo.ZoneInfo("UTC")


def format_datetime(dt: datetime.datetime) -> str:
    """
    Format a datetime. Uses isoformat, except when the timezone is UTC,
    attaches "Z" as the timezone, instead of "+00:00"
    """

    if dt.tzinfo == UTC:
        return f"{dt.date()}T{dt.time()}Z"
    else:
        return dt.isoformat()
