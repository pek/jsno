"""
Jsonification and unjsonification for the datetime types.

* datetime.datetime
* datetime.date
* datetime.time
* datetime.timezone

"""

import datetime
from typing import Literal

from jsno.jsonify import jsonify
from jsno.standard import jsonify_to_string
from jsno.unjsonify import unjsonify, typecheck


# datetime.date


@jsonify.register(datetime.date)
def _(date):
    return f"{date.year}-{date.month:02}-{date.day:02}"


@unjsonify.register(datetime.date)
def _(value, as_type):
    typecheck(value, str, as_type)
    (ys, ms, ds) = value.split("-")
    return as_type(int(ys), int(ms), int(ds))


# datetime.time


@jsonify.register(datetime.time)
def _(value):
    # time may also contain timezone info, but it is ignored for now

    if value.second == 0 and value.microsecond == 0:
        # minute precision
        return f"{value.hour:02}:{value.minute:02}"

    # by default, stringifies to second or microsecond precision
    return str(value)


@unjsonify.register(datetime.time)
def _(value, as_type):
    typecheck(value, str, as_type)
    return datetime.time.fromisoformat(value)


# datetime.datetime


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
    return as_type.fromisoformat(value)


# datetime.timedelta


@jsonify.register(datetime.timedelta)
def _(value):
    return str(value).removesuffix(", 0:00:00").removesuffix(":00")


def make_time_component(
        multiplier: Literal[-1, 1],
        days: int,
        timestr: str,
        as_type: type = datetime.timedelta
):

    if timestr.find(":") == 1:
        # support 1-digit hour: "4:00"
        timestr = f"0{timestr}"

    time = datetime.time.fromisoformat(timestr)
    return as_type(
        days=multiplier * days,
        hours=multiplier * time.hour,
        minutes=multiplier * time.minute,
        seconds=multiplier * time.second,
        microseconds=multiplier * time.microsecond,
    )


@unjsonify.register(datetime.timedelta)
def _(value, as_type):
    typecheck(value, str, as_type)

    if value.startswith('-'):
        multiplier = -1
        value = value[1:]
    else:
        multiplier = 1

    if value.endswith(" days"):
        # "7 days" ==> ("7", "00:00")
        parts = (value.removesuffix(" days"), "00:00")
    else:
        # "7 days, 01:23:45" ==> ("7", "01:23:45")
        parts = value.split(" days, ")

    days = 0 if len(parts) < 2 else int(parts[0])
    return make_time_component(multiplier, days, parts[-1], as_type)


# datetime.timezone


jsonify.register(datetime.timezone)(jsonify_to_string)


@unjsonify.register(datetime.timezone)
def _(value, as_type):
    typecheck(value, str, as_type)

    if value == 'UTC':
        return datetime.timezone.utc

    if value.startswith('UTC+'):
        time = make_time_component(1, 0, value[4:])
    elif value.startswith('UTC-'):
        time = make_time_component(-1, 0, value[4:])
    else:
        raise ValueError("Timezone must start with 'UTC'")

    # convert timedelta representing the UTC offset to a timezone
    return as_type(time)
