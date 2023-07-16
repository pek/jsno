import base64
import dataclasses
import datetime
import enum
import functools

from collections.abc import ByteString, Mapping, Sequence, Set


from jsno.utils import is_optional, format_datetime
from jsno.variant import get_variantclass


"""
valid JSON types.
"""
JSON = bool | int | float | str | list["JSON"] | dict[str, "JSON"] | None


class NoChange:
    """
    Dummy class for representing the "not changed" return value when
    jsonifying.
    """


NOCHANGE = NoChange()


def jsonify_dataclass(value) -> dict[str, JSON]:
    """
    Jsonify a value whose type is a dataclass.
    """
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




def jsonify_list(value: list) -> list[JSON] | NoChange:
    """
    Jsonify a list. If the argument list was already valid JSON,
    return NOCHANGE instead.
    """

    count = len(value)

    if count == 0:
        # shortcut for empty lists
        return NOCHANGE

    ix = 1

    val_json = call_jsonify(value[0])
    if val_json is not NOCHANGE:
        # the first value was transformed. Continue with the same
        # iterator
        result = [val_json]
    else:
        while True:
            if ix == count:
                return NOCHANGE

            val_json = call_jsonify(value[ix])
            if val_json is not NOCHANGE:
                # found the first transformed value
                result = value[:ix]
                result.append(val_json)
                ix += 1
                break
            ix += 1


    while ix < count:
        val_json = call_jsonify(value[ix])
        result.append(value[ix] if val_json is NOCHANGE else val_json)
        ix += 1

    return result


def jsonify_dict(value: dict) -> dict[str, JSON] | NoChange:
    """
    Jsonify a dict. If the argument dict was already valid JSON,
    return NOCHANGE instead.
    """

    result = NOCHANGE
    nonchange_count = 0

    for (key, val) in value.items():

        key_json = key if type(key) is str else str(jsonify(key))
        val_json = call_jsonify(val)

        if result is NOCHANGE:
            if key_json is key and val_json is NOCHANGE:
                nonchange_count += 1
                continue

            result = {}
            if nonchange_count > 0:
                for (k, v) in value.items():
                    result[k] = v
                    nonchange_count -= 1
                    if nonchange_count == 0:
                        break

        result[key_json] = val if val_json is NOCHANGE else val_json

    return result


@functools.singledispatch
def generic_jsonify(value):
    """
    Singledispatch function for defining custom jsonification methods.
    """

    if dataclasses.is_dataclass(value):
        return jsonify_dataclass(value)

    raise TypeError("Don't know how to jsonify", value, type(value))


native_types = (str, int, float, bool, type(None))


def call_jsonify(value) -> JSON | NoChange:
    """
    Call jsonify, using optimised paths for the native JSON types.
    Returns NOCHANGE if the result is the same as the argument.
    """

    if type(value) in native_types:
        return NOCHANGE
    elif type(value) is list:
        return jsonify_list(value)
    elif type(value) is dict:
        return jsonify_dict(value)
    else:
        return generic_jsonify(value)


def call_jsonify_as_type(value, as_type: type) -> JSON | NoChange:

    # this could be combined with call_jsonify, but it seems that
    # complicating call_jsonify has suprisingly big impact on
    # performance, so keeping the duplicated code for now

    if not issubclass(type(value), as_type):
        raise TypeError(f"Cannot jsonify {value} as {as_type}")

    if as_type in native_types:
        return NOCHANGE
    elif as_type is list:
        return jsonify_list(value)
    elif as_type is dict:
        return jsonify_dict(value)
    else:
        return generic_jsonify.dispatch(as_type)(value)


class Jsonify:

    def __call__(self, value) -> JSON:
        """
        Jsonify any value that supports jsonification.
        """
        result = call_jsonify(value)
        return value if result is NOCHANGE else result

    def call_as_type(self, value, as_type: type) -> JSON:
        """
        Jsonify any value that supports jsonification, dispatching
        on the given type.
        """
        result = call_jsonify_as_type(value, as_type)
        return value if result is NOCHANGE else result

    def __getitem__(self, type_):
        return lambda value: jsonify.call_as_type(value, type_)

    def register(self, type_):
        return generic_jsonify.register(type_)


jsonify = Jsonify()


@jsonify.register(str)
def _(value):
    return str(value)


@jsonify.register(bool)
def _(value):
    return bool(value)


@jsonify.register(float)
def _(value):
    return float(value)


@jsonify.register(type(None))
def _(value):
    return None


@jsonify.register(int)
def _(value):
    return int(value)


@jsonify.register(Mapping)
def _(value):
    return {str(jsonify(key)): jsonify(val) for (key, val) in value.items()}


@jsonify.register(Sequence)
def jsonify_sequence(value):
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


@jsonify.register(ByteString)
def _(value):
    return base64.b64encode(value).decode('ascii')

