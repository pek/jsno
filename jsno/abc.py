"""
Jsonification and unjsonification for abstract base classes
"""

import base64

from collections.abc import ByteString, Mapping, Sequence, Set

from jsno.jsonify import jsonify
from jsno.unjsonify import unjsonify, typecheck, raise_error, cast
from jsno.utils import get_args


# Mapping


@jsonify.register(Mapping)
def _(value):
    return {str(jsonify(key)): jsonify(val) for (key, val) in value.items()}


@unjsonify.register(Mapping)
def _(value, as_type):
    """
    Unjsonify any Mapping type. Expects the input value to be
    a JSON object (dict).
    """

    typecheck(value, dict, as_type)

    arg_types = get_args(as_type)

    if not arg_types:
        return cast(value, as_type)
    else:
        unjsonify_key = unjsonify[arg_types[0]]
        unjsonify_val = unjsonify[arg_types[1]]

        as_dict = {
            unjsonify_key(key): unjsonify_val(val)
            for (key, val) in value.items()
        }
        return cast(as_dict, as_type)


# Sequence


@jsonify.register(Sequence)
def jsonify_sequence(value):
    return [jsonify(val) for val in value]


@unjsonify.register(Sequence)
def unjsonify_sequence(value, as_type):
    typecheck(value, list, as_type)

    arg_types = get_args(as_type)

    if not arg_types:
        return cast(value, as_type)
    else:
        unjsonify_item = unjsonify[arg_types[0]]
        return cast([unjsonify_item(item) for item in value], as_type)


# Set


@jsonify.register(Set)
def _(value):
    """
    Set is not a sequence, so it needs it's own jsonifier.
    Because the order of iterating over a set is not defined, the jsonification
    tries to sort the set first, to make the results more predictable.
    """

    # if possible, sort the values first.
    try:
        value = sorted(value, key=lambda v: (type(v).__name__, v))
    except Exception:
        pass

    return jsonify_sequence(value)


unjsonify.register(Set)(unjsonify_sequence)


# ByteString abstract base class


@jsonify.register(ByteString)
def _(value):
    return base64.b64encode(value).decode("ascii")


@unjsonify.register(ByteString)
def _(value, as_type):
    typecheck(value, str, as_type)

    try:
        return base64.b64decode(value.encode("ascii"))
    except ValueError as exc:
        detail = exc.args[0]

    raise_error(value, as_type, detail)
