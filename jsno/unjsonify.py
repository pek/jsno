import dataclasses
import functools
import types


from typing import Any, Union, Literal


from jsno.utils import get_origin, get_args, get_dataclass_fields
from jsno.variant import get_variantfamily


class UnjsonifyError(TypeError):
    pass


def raise_error(value: Any, as_type: Any, detail=None):
    raise UnjsonifyError(f"Cannot unjsonify as {as_type}", value, detail)


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

    raise_error(value, as_type, detail)


@functools.singledispatch
def unjsonify_type(value, as_type):
    if dataclasses.is_dataclass(as_type):
        return unjsonify_dataclass(value, as_type)

    raise TypeError(f"Unjsonify not defined for {as_type}")


def unjsonify_dataclass(value, as_type):
    typecheck(value, dict, as_type)

    # collect all properties in the input value that match any of
    # the dataclass fields
    kwargs = {
        field.name: unjsonify[field.type](value.get(field.name))
        for field in get_dataclass_fields(as_type)
        if field.name in value
    }
    try:
        return as_type(**kwargs)
    except TypeError as exc:
        detail = exc.args[0]

    raise_error(value, as_type, detail)


def unjsonify_variant(value, as_type, family):
    typecheck(value, dict, as_type)

    label_name = family.label_name

    label = value.get(label_name)
    if label is None:
        raise_error(value, as_type, f"missing {label}")

    variant_type = family.get_variant(label)
    if variant_type is None or not issubclass(variant_type, as_type):
        raise_error(value, as_type, f"unknown {label_name} label: {label}")

    return unjsonify._dispatch(variant_type)(value)


def unjsonify_literal(value, as_type):
    options = get_args(as_type)

    if value in options:
        return value

    raise_error(value, as_type)


class Unjsonify:
    def _dispatch(self, type_):

        origin = get_origin(type_) or type_

        # special cases needed for constructs in typing module, as
        # singledispatch fails cannot handle Union and Literal
        if origin is Union:
            func = unjsonify_union
        elif origin is Literal:
            # Literal needs a
            func = unjsonify_literal
        else:
            # covers list[X], dict[K,V], etc.
            func = unjsonify_type.dispatch(origin)

        # return a specialized version of the unjsonify function
        return lambda value: func(value, type_)

    def __getitem__(self, type_):
        if isinstance(type_, type) and (family := get_variantfamily(type_)):
            return lambda value: unjsonify_variant(value, type_, family)

        return self._dispatch(type_)

    def register(self, type_):
        return unjsonify_type.register(type_)


unjsonify = Unjsonify()


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

    raise UnjsonifyError(f"Cannot unjsonify as {as_type}", value)


@unjsonify.register(Any)
def _(value, as_type):
    """Unjsonify Any type: just return the value"""
    return value
