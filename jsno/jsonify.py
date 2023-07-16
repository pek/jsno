import dataclasses
import datetime
import enum
import functools

from collections.abc import Mapping, Sequence, Set


from jsno.utils import is_optional, format_datetime
from jsno.variant import get_variantclass



class NoChange:
    pass


NOCHANGE = NoChange()


def jsonify_dataclass(value):
    result = {}

    variantclass = get_variantclass(type(value))
    if variantclass:
        result[variantclass.label_name] = variantclass.get_label(type(value))

    for (key, val) in value.__dict__.items():
        if (val is None and is_optional(value.__annotations__[key])):
            # skip optional values that are None
            continue

        result[key] = jsonify(val)

    return result


@functools.singledispatch
def _jsonify(value):
    if hasattr(value, 'jsonify'):
        return value.jsonify()

    if dataclasses.is_dataclass(value):
        return jsonify_dataclass(value)

    raise TypeError("Don't know how to jsonify", value, type(value))


class Jsonify:

    def __call__(self, value):
        result = _jsonify(value)

        if result is NOCHANGE:
            return value
        else:
            return result

    def register(self, type_):
        return _jsonify.register(type_)


jsonify = Jsonify()


@jsonify.register(str)
@jsonify.register(bool)
@jsonify.register(int)
@jsonify.register(float)
@jsonify.register(type(None))
def _(value):
    return NOCHANGE


@jsonify.register(Mapping)
def _(value):
    return {jsonify(key): jsonify(val) for (key, val) in value.items()}


@jsonify.register(Sequence)
def _(value):
    return [jsonify(val) for val in value]


@jsonify.register(Set)
def _(value):
    """
    Set is not a sequence, so it needs it's own jsonifier.
    Because the order of iterating over a set is not defined, the jsonification
    tries to sort the set first, to make the results more predictable.
    """

    # if possible, sort the values first.
    try:
        value = sorted(value)
    except:
        pass

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
