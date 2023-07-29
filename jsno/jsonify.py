import dataclasses
import functools

from jsno.utils import is_optional, get_dataclass_fields
from jsno.variant import get_variantfamily


"""
valid JSON types.
"""
JSON = bool | int | float | str | list["JSON"] | dict[str, "JSON"] | None


def jsonify_dataclass(value) -> dict[str, JSON]:
    """
    Jsonify a value whose type is a dataclass.
    """
    result: dict[str, JSON] = {}
    value_type: type = type(value)

    if family := get_variantfamily(value_type):
        # if the value's class is a member of a variant family,
        # first add the variant label to the jsonified result
        result[family.label_name] = family.get_label(value_type)

    for field in get_dataclass_fields(value_type):
        val = getattr(value, field.name)

        # skip optional values that are None
        if val is not None or not is_optional(field.type):
            result[field.name] = jsonify(val)

    return result


def jsonify_list(value: list) -> list[JSON]:
    """
    Jsonify a list.
    """

    count = len(value)

    if count == 0:
        # shortcut for empty lists
        return value

    ix = 1

    val_json = call_jsonify(value[0])
    if val_json is not value[0]:
        # the first value was transformed. Continue with the same
        # iterator
        result = [val_json]
    else:
        while True:
            if ix == count:
                return value

            val_json = call_jsonify(value[ix])
            if val_json is not value[ix]:
                # found the first transformed value
                result = value[:ix]
                result.append(val_json)
                ix += 1
                break
            ix += 1

    while ix < count:
        val_json = call_jsonify(value[ix])
        result.append(value[ix] if val_json is value[ix] else val_json)
        ix += 1

    return result


def jsonify_dict(value: dict) -> dict[str, JSON]:
    """
    Jsonify a dict.
    """

    result = None
    nonchange_count = 0

    for (key, val) in value.items():

        key_json = key if type(key) is str else str(jsonify(key))
        val_json = call_jsonify(val)

        if result is None:
            if key_json is key and val_json is val:
                nonchange_count += 1
                continue

            result = {}
            if nonchange_count > 0:
                for (k, v) in value.items():
                    result[k] = v
                    nonchange_count -= 1
                    if nonchange_count == 0:
                        break

        result[key_json] = val_json

    return result or value


@functools.singledispatch
def generic_jsonify(value):
    """
    Singledispatch function for defining custom jsonification methods.
    """

    if dataclasses.is_dataclass(value):
        return jsonify_dataclass(value)

    raise TypeError("Don't know how to jsonify", value, type(value))


native_types = (str, int, float, bool, type(None))


def call_jsonify(value) -> JSON:
    """
    Call jsonify, using optimised paths for the native JSON types.
    """

    if type(value) in native_types:
        return value
    elif type(value) is list:
        return jsonify_list(value)
    elif type(value) is dict:
        return jsonify_dict(value)
    else:
        return generic_jsonify(value)


def call_jsonify_as_type(value, as_type: type) -> JSON:

    # this could be combined with call_jsonify, but it seems that
    # complicating call_jsonify has suprisingly big impact on
    # performance, so keeping the duplicated code for now

    if not issubclass(type(value), as_type):
        raise TypeError(f"Cannot jsonify {value} as {as_type}")

    if as_type in native_types:
        return value
    elif as_type is list:
        return jsonify_list(value)
    elif as_type is dict:
        return jsonify_dict(value)
    else:
        return generic_jsonify.dispatch(as_type)(value)


class Jsonify:
    """
    Singleton type for the jsonify function
    """

    def __call__(self, value) -> JSON:
        """
        Jsonify any value that supports jsonification.
        """
        return call_jsonify(value)

    def call_as_type(self, value, as_type: type) -> JSON:
        """
        Jsonify any value that supports jsonification, dispatching
        on the given type.
        """
        return call_jsonify_as_type(value, as_type)

    def __getitem__(self, type_):
        return lambda value: jsonify.call_as_type(value, type_)

    def register(self, type_):
        return generic_jsonify.register(type_)


jsonify = Jsonify()
