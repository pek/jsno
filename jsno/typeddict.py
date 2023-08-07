import functools
import inspect
import typing

from jsno.unjsonify import UnjsonifyError, unjsonify, handle_extra_keys, typecheck


def unwrap_type(type_):
    """
    Unwrap the type for a typed dict key that might have been
    annotated with `Required` or `NotRequired`
    """

    origin = typing.get_origin(type_)
    if origin is typing.NotRequired or origin is typing.Required:
        return typing.get_args(type_)[0]
    else:
        return type_


@functools.cache
def unjsonify_typeddict_factory(as_type):

    annotations = [
        (key, unjsonify[unwrap_type(type_)], key in as_type.__required_keys__)
        for (key, type_) in inspect.get_annotations(as_type).items()
    ]

    def specialized(value):
        typecheck(value, (dict, typing.Mapping), as_type)

        result = {}

        for (key, unjsonify_, required) in annotations:
            if key in value:
                result[key] = unjsonify_(value[key])
            elif required:
                raise UnjsonifyError(f"Required key missing in {as_type}: {key}")

        # check if all values were handled
        if len(result) < len(value):
            handle_extra_keys(value, result, as_type)

        return result

    return specialized
