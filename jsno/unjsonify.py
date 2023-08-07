import dataclasses
import functools
import types

from collections.abc import Mapping
from typing import Annotated, Any, Union, Literal, NewType, get_args, get_origin

from jsno.extra_data import get_extra_data_configuration, Ignore
from jsno.utils import contextvar, DictWithoutKey
from jsno.variant import get_variantfamily


unjsonify_context = contextvar(on_extra_key="error")


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
def unjsonify_type(as_type):
    if dataclasses.is_dataclass(as_type):
        return get_unjsonify_dataclass(as_type)

    raise TypeError(f"Unjsonify not defined for {as_type.__qualname__}")


def handle_extra_keys(value, result, as_type):
    extra_data_property = get_extra_data_configuration.dispatch(as_type)(as_type)
    if extra_data_property is not None:
        if extra_data_property is Ignore:
            return

        result[extra_data_property] = {
            key: value[key] for key in value if key not in result
        }

    elif unjsonify_context.on_extra_key == "error":
        extra_keys = {key for key in value if key not in result}
        raise UnjsonifyError(
            f"Extra keys for {as_type.__qualname__}: {', '.join(extra_keys)}"
        )


def get_unjsonify_dataclass(as_type):

    fields = [
        (field.name, unjsonify[field.type])
        for field in dataclasses.fields(as_type)
    ]

    def specialized(value):
        typecheck(value, (dict, Mapping), as_type)

        # collect all properties in the input value that match any of
        # the dataclass fields
        kwargs = {
            name: unjsonify_(value.get(name))
            for (name, unjsonify_) in fields
            if name in value
        }
        if len(kwargs) < len(value):
            handle_extra_keys(value, kwargs, as_type)

        try:
            return as_type(**kwargs)
        except TypeError as exc:
            detail = exc.args[0]

        raise_error(value, as_type, detail)

    return specialized


def get_unjsonify_variant(as_type, family):

    cache = {}

    def specialized(value):
        typecheck(value, (dict, Mapping), as_type)

        label_name = family.label_name

        label = value.get(label_name)
        if label is None:
            raise_error(value, as_type, f"missing {label}")

        func = cache.get(label)
        if func is None:
            variant_type = family.get_variant(label)
            if variant_type is None or not issubclass(variant_type, as_type):
                raise_error(value, as_type, f"unknown {label_name} label: {label}")

            func = unjsonify._dispatch(variant_type)
            cache[label] = func

        return func(DictWithoutKey(base=value, key=label_name))

    return specialized


def get_unjsonify_literal(as_type):
    options = get_args(as_type)

    return lambda value: value if value in options else raise_error(value, as_type)


class Unjsonify:
    def __init__(self):
        self._cache = {}

    def _dispatch(self, type_):
        if isinstance(type_, NewType):
            type_ = type_.__supertype__

        origin = get_origin(type_)
        if origin:
            # special cases needed for constructs in typing module, as
            # singledispatch fails cannot handle Union and Literal
            if origin is Union:
                return get_unjsonify_union(type_)
            elif origin is Literal:
                return get_unjsonify_literal(type_)

        # covers list[X], dict[K,V], etc.
        try:
            func = unjsonify_type.dispatch(origin or type_)
        except TypeError:
            raise UnjsonifyError(f"Cannot unjsonify {type_}")

        return func(type_)

    def __getitem__(self, type_):
        unjsonify = self._cache.get(type_)
        if unjsonify is None:
            if isinstance(type_, type) and (family := get_variantfamily(type_)):
                unjsonify = get_unjsonify_variant(type_, family)
            else:
                unjsonify = self._dispatch(type_)
            self._cache[type_] = unjsonify
        return unjsonify

    def register(self, type_):
        def decorator(func):
            @self.register_factory(type_)
            def _(as_type):
                return lambda value: func(value, as_type)

            return func

        return decorator

    def register_factory(self, type_):
        self._cache.clear()
        return unjsonify_type.register(type_)

    def context(self, **kwargs):
        return unjsonify_context(**kwargs)

    def ignore_extra_keys(self):
        return self.context(on_extra_key="ignore")


unjsonify = Unjsonify()


@unjsonify.register_factory(types.UnionType)
def get_unjsonify_union(as_type):
    """
    Unjsonify a Union type. Tries each option at a time, and
    selects the first one that matches.
    """

    options = get_args(as_type)

    def specialized(value):
        for type_option in options:
            try:
                return unjsonify[type_option](value)
            except UnjsonifyError:
                # try next option
                continue

        raise UnjsonifyError(f"Cannot unjsonify as {as_type}", value)

    return specialized


@unjsonify.register(Any)
def _(value, as_type):
    """Unjsonify Any type: just return the value"""
    return value


@functools.singledispatch
def validate_annotation(arg, value):
    pass


@unjsonify.register(Annotated)
def _(value, as_type):
    args = get_args(as_type)
    result = unjsonify[args[0]](value)

    ix = 1
    while ix < len(args):
        try:
            validate_annotation(args[ix], result)
            ix += 1
            continue
        except ValueError as exc:
            detail = exc.args[0]

        raise_error(result, as_type, detail)

    return result
