"""
Jsonify Python objects to JSON-compatible values, and unjsonify it back to
Python objects.

Jsonify maps any Python object to a structure consisting of dicts, lists,
and primitive values that is ready to be converted to JSON.

Unjsonify converts such JSON-structure to a given type. The type to convert
to must be given as argument.

The following types are currently supported:
    - int, float, bool
    - None (null in JSON)
    - lists and tuples
    - dicts
    - types defined as dataclass
    - enum types
    - date and datetime

When unjsonising, lists and dicts need to be specified with List[T] and
Dict[K,V] constructs.

Any type can be made compatible by registering custom functions for converting
to/from a json structure. Example converters for date and datetime are provided.

Note that the jsoniser unjsonisers are matched in reverse registration order,
so if there is a separate jsoniser/unjsoniser defined for both a subclass and
it's superclass, the superclass must be registered first.

A custom class can be made compatible also by providing jsonify method and
unjsonify class method.

"""

import dataclasses
import datetime
import enum
import functools


from jsno.utils import is_optional, format_datetime


def jsonify_dataclass(value):
    return {
        key: jsonify(val)
        for (key, val) in value.__dict__.items()

        # skip optional values that are None
        if not (val is None and is_optional(value.__annotations__[key]))
    }


@functools.singledispatch
def jsonify(value):
    if hasattr(value, 'jsonify'):
        return value.jsonify()

    if dataclasses.is_dataclass(value):
        return jsonify_dataclass(value)

    raise TypeError("Don't know how to jsonify", value, type(value))


@jsonify.register(str)
@jsonify.register(bool)
@jsonify.register(int)
@jsonify.register(float)
@jsonify.register(type(None))
def _(value):
    return value


@jsonify.register(dict)
def _(value):
    return {key: jsonify(val) for (key, val) in value.items()}


@jsonify.register(list)
@jsonify.register(tuple)
@jsonify.register(set)
def _(value):
    return [jsonify(val) for val in value]


@jsonify.register(enum.Enum)
def _(enum):
    return enum.name


@jsonify.register(datetime.date)
def _(date):
    return f'{date.year}-{date.month:02}-{date.day:02}'


@jsonify.register(datetime.datetime)
def _(datetime):
    return format_datetime(datetime)
