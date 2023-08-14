import dataclasses
import functools
import threading
import time
import types

from collections.abc import Mapping
from typing import (
    Annotated, Any, Callable, Union, Literal, NewType, Self,
    get_args, get_origin, get_type_hints,
    Required, NotRequired,
)

from jsno.fields_unjsonifier import (
    UnjsonifyError, SchemaField, create_unjsonifier, typecheck, raise_error, unjsonify_context
)
from jsno.constraint import get_validators, get_class_annotations

from jsno.property_name import get_property_name
from jsno.utils import DictWithoutKey
from jsno.variant import get_variantfamily


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
def unjsonify_factory(as_type):
    if dataclasses.is_dataclass(as_type):
        return get_unjsonify_dataclass(as_type)

    raise TypeError(f"Unjsonify not defined for {as_type.__qualname__}")


def contains_self_type(type_: type) -> bool:
    """
    Check if a type contains the Self type in it.
    """
    return (
        type_ is Self or
        any(contains_self_type(arg) for arg in get_args(type_))
    )


@dataclasses.dataclass(slots=True)
class ReferThrough:
    """
    Special class that defers unjsonify resolution to
    the call-time, used for handling recursive definitions.
    """
    as_type: type
    specialized: Callable | None = None

    def __call__(self, value):
        if self.specialized is None:
            self.specialized = unjsonify[self.as_type]

        return self.specialized(value)


def get_unjsonify_for_field(field_type, self_type):

    # Required check for TypedDicts
    origin = get_origin(field_type)
    if origin is NotRequired or origin is Required:
        field_type = get_args(field_type)[0]

    unjsonify_ = unjsonify[field_type]

    if not contains_self_type(field_type):
        return unjsonify_

    def wrapped(value):
        with unjsonify_context(self_type=self_type):
            return unjsonify_(value)

    return wrapped


def resolve_field_unjsonifiers(as_type, required_keys=frozenset()):
    type_hints = get_type_hints(as_type, include_extras=True)

    unjsonify._context_stack.add(as_type)
    try:
        return [
            SchemaField(
                name=name,
                json_name=json_name,
                default=Required if name in required_keys else NotRequired,
                unjsonify=get_unjsonify_for_field(type_, as_type)
            )
            for (name, type_) in type_hints.items()
            if (json_name := get_property_name(type_, name))
        ]
    finally:
        unjsonify._context_stack.remove(as_type)


def get_unjsonify_dataclass(as_type):
    if as_type in unjsonify._context_stack:
        return ReferThrough(as_type)

    unjsonifier = create_unjsonifier(
        as_type=as_type,
        fields=resolve_field_unjsonifiers(as_type),
    )

    def specialized(value):
        kwargs = unjsonifier.unjsonify_fields(value)
        try:
            return as_type(**kwargs)
        except TypeError as exc:
            detail = exc.args[0]

        raise_error(value, as_type, detail)

    return specialized


def get_unjsonify_variant(as_type, family) -> Callable:
    """
    Get the unjsonify function specialized for a variant family
    """

    # mapping from labels to corresponding unjsonifiers
    cache: dict[str, Callable] = {}

    label_name = family.label_name

    def specialized(value):
        typecheck(value, (dict, Mapping), as_type)

        # get the label property from the value
        label = value.get(label_name)
        if not isinstance(label, str):
            raise_error(value, as_type, f"missing {label}")

        unjsonify_variant = cache.get(label)
        if unjsonify_variant is None:
            variant_type = family.get_variant(label)
            if variant_type is None or not issubclass(variant_type, as_type):
                raise_error(value, as_type, f"unknown {label_name} label: {label}")

            unjsonify_variant = unjsonify.specialize(variant_type)
            cache[label] = unjsonify_variant

        # call the variant unjsonifier with the input value, but with
        # the label removed
        return unjsonify_variant(DictWithoutKey(base=value, key=label_name))

    return specialized


def get_unjsonify_literal(as_type):
    options = get_args(as_type)

    return lambda value: value if value in options else raise_error(value, as_type)


def unjsonify_self(value):
    self_type = unjsonify_context.self_type
    if self_type is None:
        raise TypeError("Self used without context")
    return unjsonify[self_type](value)


def get_validating_unjsonify(as_type, unjsonify, validators):
    if not validators:
        return unjsonify

    def specialized(value):
        result = unjsonify(value)
        for validate in validators:
            try:
                validate(result)
                continue
            except ValueError as exc:
                detail = exc.args[0]

            raise UnjsonifyError(f"Validation failed for {as_type}", detail)

        return result

    return specialized


@dataclasses.dataclass
class Unjsonify:
    def __init__(self) -> None:
        self._cache: dict[type, Callable] = {}
        self._lock: threading.RLock = threading.RLock()
        self._context_stack: set[type] = set()
        self._delay: int = 0

    def specialize(self, type_) -> Callable:
        if isinstance(type_, NewType):
            type_ = type_.__supertype__

        if type_ is Self:
            return unjsonify_self

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
            factory = unjsonify_factory.dispatch(origin or type_)
        except TypeError:
            raise UnjsonifyError(f"Cannot unjsonify as {repr(type_)} of type {type(type_)}")

        unjsonify_ = factory(type_)

        if isinstance(type_, type):
            validators = get_validators(get_class_annotations(type_))
            return get_validating_unjsonify(type_, unjsonify_, validators)

        return unjsonify_

    def _dispatch(self, type_) -> Callable:
        if isinstance(type_, type) and (family := get_variantfamily(type_)):
            return get_unjsonify_variant(type_, family)
        else:
            return self.specialize(type_)

    def __getitem__(self, type_) -> Callable:
        unjsonify = self._cache.get(type_)
        if unjsonify is not None:
            return unjsonify

        try:
            acquired = self._lock.acquire(blocking=False)
            if not acquired:
                self._lock.acquire(blocking=True)
                unjsonify = self._cache.get(type_)
                if unjsonify:
                    return unjsonify

            unjsonify = self._dispatch(type_)
            if not isinstance(unjsonify, ReferThrough):

                if self._delay:
                    time.sleep(self._delay)

                self._cache[type_] = unjsonify

            return unjsonify
        finally:
            self._lock.release()

    def register(self, type_):
        def decorator(func):
            @self.register_factory(type_)
            def _(as_type):
                return lambda value: func(value, as_type)

            return func

        return decorator

    def register_factory(self, type_):
        self._cache.clear()
        return unjsonify_factory.register(type_)

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

    options = [
        unjsonify[type_option]
        for type_option in get_args(as_type)
    ]

    def specialized(value):
        for try_option in options:
            try:
                return try_option(value)
            except UnjsonifyError:
                # try next option
                continue

        raise UnjsonifyError(f"Cannot unjsonify as {as_type}", value)

    return specialized


@unjsonify.register(Any)
def _(value, as_type):
    """Unjsonify Any type: just return the value"""
    return value


@unjsonify.register_factory(Annotated)
def _(as_type):
    args = get_args(as_type)
    type_ = args[0]

    return get_validating_unjsonify(type_, unjsonify[type_], get_validators(args[1:]))
