import inspect
import typing

from collections.abc import Sequence
from typing import Callable

from jsno.abc import unjsonify_sequence_factory
from jsno.unjsonify import unjsonify, typecheck, raise_error


def unjsonify_typed_factory(as_type: type) -> Callable:
    arg_types = typing.get_args(as_type)

    if arg_types and len(arg_types) == 2 and arg_types[1] is Ellipsis:
        # special case for a N-length one-type tuple (tuple[T, ...])
        # note: this accepts the empty tuple. This might not be strictly allowed
        return unjsonify_sequence_factory(as_type)

    # tuple types of the form tuple[int, str, ...] are not supported now

    unjsonifiers = [unjsonify[type_] for type_ in arg_types]

    def specialized(value):
        if len(value) != len(arg_types):
            raise_error(value, as_type)

        return as_type(
            unjsonify_(item)
            for (item, unjsonify_) in zip(value, unjsonifiers)
        )

    return specialized


@unjsonify.register_factory(tuple)
def _(as_type):
    """
    Unjsonify tuples. Handles several variants of tuples:

    * plain old untyped tuple: tuple
    * typed tuple: tuple[int, str, bool]
    * n-ary monotyped tuple: tuple[T, ...]
    * untyped namedtuple
    * typing.NamedTuple
    """

    if hasattr(as_type, '__args__'):
        return unjsonify_typed_factory(as_type)

    annotations = inspect.get_annotations(as_type)
    if annotations:
        # typing.NamedTuple

        def specialized_typed_namedtuple(value):
            typecheck(value, (list, Sequence), as_type)

            if len(annotations) != len(value):
                raise_error(value, as_type)

            return as_type(*(
                unjsonify[type_](val)
                for (val, (_, type_)) in zip(value, annotations.items())
            ))

        return specialized_typed_namedtuple

    else:
        # untyped tuple
        def specialized_untyped(value):
            if as_type is tuple:
                # just plain tuple
                return tuple(value)
            else:
                # namedtuple
                return as_type(*value)

        return specialized_untyped
