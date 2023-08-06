"""
Jsonification and unjsonification for abstract base classes
"""

import base64
import typing

from collections.abc import ByteString, Mapping, Sequence, Set

from jsno.jsonify import jsonify
from jsno.typeddict import unjsonify_typeddict_factory
from jsno.unjsonify import unjsonify, typecheck, raise_error, cast


# Mapping


@jsonify.register(Mapping)
def _(value):
    return {str(jsonify(key)): jsonify(val) for (key, val) in value.items()}


@unjsonify.register_factory(Mapping)
def _(as_type):
    """
    Unjsonify any Mapping type. Expects the input value to be
    a JSON object (dict).
    """
    arg_types = typing.get_args(as_type)

    if arg_types:
        # the mapping has arguments. Expects it to have key and value
        # types like dict[str, int]
        unjsonify_key = unjsonify[arg_types[0]]
        unjsonify_val = unjsonify[arg_types[1]]

        def unjsonify_dict_with_types(value):
            typecheck(value, (dict, Mapping), as_type)

            as_dict = {
                unjsonify_key(key): unjsonify_val(val)
                for (key, val) in value.items()
            }
            return cast(as_dict, as_type)

        return unjsonify_dict_with_types

    if type(as_type) is typing._TypedDictMeta:
        # TypedDicts must be caught at this stage, as they are
        # non-istantiable subclasses of dict.
        return unjsonify_typeddict_factory(as_type)

    # monotyped case: convert from dict
    def unjonify_untyped_mapping(value):
        if not isinstance(value, (dict, Mapping)):
            raise_error(value, as_type)

        return cast(value, as_type)

    return unjonify_untyped_mapping

# Sequence


@jsonify.register(Sequence)
def jsonify_sequence(value):
    return [jsonify(val) for val in value]


@unjsonify.register_factory(Sequence)
def unjsonify_sequence_factory(as_type):
    arg_types = typing.get_args(as_type)

    if not arg_types:
        def specialized_untyped(value):
            typecheck(value, (list, Sequence), as_type)
            return cast(value, as_type)

        return specialized_untyped

    else:
        unjsonify_item = unjsonify[arg_types[0]]

        def specialized_typed(value):
            typecheck(value, (list, Sequence), as_type)
            return cast([unjsonify_item(item) for item in value], as_type)

        return specialized_typed


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


unjsonify.register_factory(Set)(unjsonify_sequence_factory)


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
