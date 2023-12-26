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
    UnjsonifyError, SchemaField, create_unjsonifier, typecheck, unjsonify_context
)
from jsno.constraint import get_validators, get_class_annotations

from jsno.property_name import get_property_name
from jsno.utils import DictWithoutKey, get_typename, JSON
from jsno.variant import get_variantfamily


class SchemaType:
    _unjsonifier = lambda x: x


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

    raise UnjsonifyError(value, as_type, detail)


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


def resolve_field_unjsonifiers(as_type, field_names=None, required_keys=frozenset()):
    type_hints = get_type_hints(as_type, include_extras=True)

    if field_names is None:
        field_types = type_hints.items()
    else:
        field_types = [
            (name, type_)
            for name in field_names
            if (type_ := type_hints.get(name))
        ]

    unjsonify._context_stack.add(as_type)
    try:
        return [
            SchemaField(
                name=name,
                json_name=json_name,
                default=Required if name in required_keys else NotRequired,
                unjsonify=get_unjsonify_for_field(type_, as_type)
            )
            for (name, type_) in field_types
            if (json_name := get_property_name(type_, name))
        ]
    finally:
        unjsonify._context_stack.remove(as_type)


def get_unjsonify_dataclass(as_type):
    if as_type in unjsonify._context_stack:
        return ReferThrough(as_type)

    unjsonifier = create_unjsonifier(
        as_type=as_type,
        fields=resolve_field_unjsonifiers(
            as_type,
            field_names=[field.name for field in dataclasses.fields(as_type)]
        )
    )

    def specialized(value):
        kwargs = unjsonifier.unjsonify_fields(value)
        try:
            return as_type(**kwargs)
        except TypeError as exc:
            detail = exc.args[0]

        raise UnjsonifyError(value, as_type, detail)

    return specialized


def get_unjsonify_variant(as_type, family) -> Callable:
    """
    Get the unjsonify function specialized for a variant family
    """

    # mapping from labels to corresponding unjsonifiers
    cache: dict[str, tuple[Callable, bool]] = {}

    label_name = family.label_name

    def specialized(value):
        typecheck(value, (dict, Mapping), as_type)

        # get the label property from the value
        label = value.get(label_name)
        if not isinstance(label, str):
            raise UnjsonifyError(value, as_type, f"missing {label}")

        entry = cache.get(label)
        if entry is None:
            variant_type = family.get_variant(label)
            if variant_type is None:
                raise UnjsonifyError(value, as_type, f"unknown {label_name}: {label}")
            if not issubclass(variant_type, as_type):
                raise UnjsonifyError(value, as_type, f"not subclass of {as_type}: {label}")

            include_label = family.includes_label(variant_type)
            unjsonify_variant = unjsonify.specialize(variant_type)
            cache[label] = (unjsonify_variant, include_label)
        else:
            (unjsonify_variant, include_label) = entry

        if not include_label:
            value = DictWithoutKey(base=value, key=label_name)

        # call the variant unjsonifier with the input value, but with
        # the label removed
        return unjsonify_variant(value)

    return specialized


def get_unjsonify_literal(as_type):
    options = get_args(as_type)

    def specialized(value):
        if value in options:
            return value

        raise UnjsonifyError(value, as_type)

    return specialized


def unjsonify_self(value):
    self_type = unjsonify_context.self_type
    if self_type is None:
        raise TypeError("Self used without context")

    return unjsonify[self_type](value)


def get_validating_unjsonify(
        as_type: type,
        unjsonify: Callable,
        validators: list[Callable]

) -> Callable:

    """
    Add validators to an unjsonify function.
    """

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

            raise UnjsonifyError(value, as_type, detail)

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

        if origin := get_origin(type_):
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
            typename = get_typename(type(type_))
            raise TypeError(f"Cannot unjsonify as {repr(type_)} of type {typename}")

        unjsonify_ = factory(type_)

        if isinstance(type_, type):
            validators = get_validators(get_class_annotations(type_))
            return get_validating_unjsonify(type_, unjsonify_, validators)
        else:
            return unjsonify_

    def _dispatch(self, type_) -> Callable:
        if isinstance(type_, type) and (family := get_variantfamily(type_)):
            return get_unjsonify_variant(type_, family)
        else:
            return self.specialize(type_)

    def __getitem__(self, type_) -> Callable:
        try:
            unjsonify = self._cache.get(type_)
        except TypeError:
            if isinstance(type_, SchemaType):
                return type_._unjsonifier
            else:
                return self._dispatch(type_)

        if unjsonify is not None:
            return unjsonify

        try:
            # first do a non-blocking lock
            acquired = self._lock.acquire(blocking=False)
            if not acquired:
                # if the locking fails, wait until the lock is free
                self._lock.acquire(blocking=True)

                # check again if the another thread has initialized the
                # unjsonifier already
                if unjsonify := self._cache.get(type_):
                    return unjsonify

            unjsonify = self._dispatch(type_)
            if isinstance(unjsonify, ReferThrough):
                # Don't cache ReferThroughts
                return unjsonify

            if self._delay:
                # only for concurrency testing
                time.sleep(self._delay)

            self._cache[type_] = unjsonify
            return unjsonify

        finally:
            self._lock.release()

    def register(self, type_):
        def decorator(func):
            @self.register_factory(type_)
            def _(as_type):

                def unjsonify(value):
                    try:
                        return func(value, as_type)
                    except ValueError:
                        pass

                    raise UnjsonifyError(value, as_type)

                return unjsonify

            return func

        return decorator

    def register_factory(self, type_):
        self._cache.clear()
        self._cache[JSON] = lambda it: it
        self._cache[Self] = unjsonify_self

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
    args = get_args(as_type)
    if types.NoneType in args:
        # special case for Optional type
        args = tuple(arg for arg in args if arg is not types.NoneType)  # noqa
        unjsonify_type = unjsonify[Union[args]]

        return lambda value: None if value is None else unjsonify_type(value)

    options = [unjsonify[type_option] for type_option in get_args(as_type)]

    def specialized(value):
        for try_option in options:
            try:
                return try_option(value)
            except UnjsonifyError:
                # try next option
                continue

        raise UnjsonifyError(value, as_type)

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
