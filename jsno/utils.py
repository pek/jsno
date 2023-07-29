import dataclasses
import functools
import types
import typing


union_types = (
    typing.Union,  # Union[X] or Optional[X]
    types.UnionType,  # X | Y or X | None
)


@functools.cache
def get_origin(type):
    """
    Cached version typing.get_origin() to make sure it's quick to check.
    """
    return typing.get_origin(type)


@functools.cache
def get_args(type):
    """
    Cached version typing.get_args() to make sure it's quick to check.
    """
    return typing.get_args(type)


@functools.cache
def get_dataclass_fields(cls: type):
    """
    Cache dataclass fields for speed
    """
    return dataclasses.fields(cls)


def is_optional(type_) -> bool:
    """
    Check if a type object is instance of optional type
    (something that could be None)
    """

    return (
        get_origin(type_) in union_types and
        type(None) in get_args(type_)
    )
