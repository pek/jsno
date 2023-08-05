import inspect
import typing

from jsno.unjsonify import UnjsonifyError, unjsonify
from jsno.utils import get_args, get_origin


def unjsonify_typeddict(value, as_type):
    result = {}

    for (key, type_) in inspect.get_annotations(as_type).items():

        # unwrap Required/NotRequired fields
        origin = get_origin(type_)
        if origin is typing.NotRequired or origin is typing.Required:
            type_ = get_args(type_)[0]

        if key in value:
            result[key] = unjsonify[type_](value[key])
        elif key in as_type.__required_keys__:
            raise UnjsonifyError(f"Required key missing in {as_type}: {key}")

    # check if all values were handled
    if len(value) > len(result):
        extra_keys = value.keys() - result.keys()
        raise UnjsonifyError(f"Extra keys for {as_type}: {', '.join(extra_keys)}")

    return result
