import dataclasses
import datetime
import enum
import functools
import inspect
import types


from collections.abc import Mapping, Sequence, Set
from typing import Any, Union


from jsno.utils import get_origin, get_args, dataclass_has_default


class UnjsonifyError(TypeError):
    pass


@functools.singledispatch
def unjsonify_type(value, as_type):
    raise TypeError(f"Unjsonify not defined for {as_type}")


def unjsonify_dataclass(value, as_type):
    kwargs = {
        name:  unjsonify[type_](value.get(name))
        for (name, type_) in as_type.__annotations__.items()
        if name in value or not dataclass_has_default(as_type, name)
    }
    return as_type(**kwargs)


class Unjsonify:

    def __getitem__(self, type_):
        if dataclasses.is_dataclass(type_):
            return lambda value: unjsonify_dataclass(value, type_)

        origin = get_origin(type_) or type_

        if origin is Union:
            # special case needed, as singledispatch fails cannot handle
            # typing.Union
            func = unjsonify_union
        else:
            func = unjsonify_type.dispatch(origin)

        # return a specialized version of the unjsonify function
        return lambda value: func(value, type_)

    def register(self, type_):
        return unjsonify_type.register(type_)


unjsonify = Unjsonify()


def raise_error(value: Any, as_type: Any, detail=None):
    raise UnjsonifyError(f"Cannot unjsonify as {as_type.__name__}", value, detail)


def typecheck(value: Any, jsontype: type, as_type: Any) -> None:
    """
    Check if the value is an instance of the type given as `jsontype`
    and if not, raise an appropriate UnjsonifyError
    """

    if not isinstance(value, jsontype):
        raise_error(value, as_type)


def cast(value: Any, as_type: Any) -> Any:
    """
    Make sure that the value given has given type, and if not,
    try casting it to that type.
    """

    if isinstance(as_type, type):
        origin_type = as_type
    else:
        origin_type = get_origin(as_type)

    if isinstance(value, origin_type):
        return value

    try:
        return origin_type(value)
    except ValueError as exc:
        detail = exc.args[0]

    raise_error(value, as_type)



@unjsonify.register(type(None))
def _(value, as_type):
    typecheck(value, type(None), as_type)
    return None


@unjsonify.register(float)
def _(value, as_type):
    typecheck(value, float, as_type)
    return cast(value, as_type)


@unjsonify.register(int)
def _(value, as_type):
    typecheck(value, int, as_type)
    return cast(value, as_type)


@unjsonify.register(bool)
def _(value, as_type):
    typecheck(value, bool, as_type)
    return cast(value, as_type)


@unjsonify.register(str)
def _(value, as_type):
    typecheck(value, str, as_type)
    return cast(value, as_type)


@unjsonify.register(Sequence)
@unjsonify.register(Set)
def unjsonify_sequence(value, as_type):
    typecheck(value, list, as_type)

    arg_types = get_args(as_type)

    if not arg_types:
        return cast(value, as_type)
    else:
        unjsonify_item = unjsonify[arg_types[0]]
        return cast([unjsonify_item(item) for item in value], as_type)


@unjsonify.register(tuple)
def _(value, as_type):
    """
    Jsonify tuples.

    Tuples are a subclass of Sequence, but tuples with more
    than one argument are treated specially.
    """

    arg_types = get_args(as_type)
    if arg_types and len(arg_types) < 2:
        return unjsonify_sequence(value, as_type)

    typecheck(value, list, as_type)

    if len(value) != len(arg_types):
        raise_error(value, as_type)

    return as_type(
        unjsonify[type_](item)
        for (item, type_) in zip(value, arg_types)
    )


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
        return as_type({
            unjsonify_key(key): unjsonify_val(val)
            for (key, val) in value.items()
        })


@unjsonify.register(types.UnionType)
def unjsonify_union(value, as_type):
    """
    Unjsonify a Union type. Tries each option at a time, and
    selects the first one that matches.
    """
    for type_option in get_args(as_type):
        try:
            return unjsonify[type_option](value)
        except UnjsonifyError:
            # try next option
            continue

    raise_error(value, as_type)


@unjsonify.register(enum.Enum)
def _(value, as_type):
    typecheck(value, str, as_type)
    try:
        return getattr(as_type, value)
    except AttributeError:
        pass

    raise_error(value, as_type)


@unjsonify.register(datetime.datetime)
def _(value, as_type):
    typecheck(value, str, as_type)
    try:
        return datetime.datetime.fromisoformat(value)
    except ValueError as exc:
        detail = exc.args[0]

    raise_error(value, as_type, detail)


@unjsonify.register(datetime.date)
def _(value, as_type):
    typecheck(value, str, as_type)
    try:
        (ys, ms, ds) = value.split('-')
        return datetime.date(int(ys), int(ms), int(ds))
    except ValueError as exc:
        detail = exc.args[0]

    raise_error(value, as_type, detail)
