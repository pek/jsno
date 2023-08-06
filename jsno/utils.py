import dataclasses
import functools
import types
import typing

from collections.abc import Mapping


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


@dataclasses.dataclass(slots=True)
class DictWithoutKey(Mapping):
    base: dict
    key: str

    def get(self, key, default=None):
        if key == self.key:
            return default
        else:
            return self.base[key]

    def __getitem__(self, key):
        if key == self.key:
            raise KeyError(key)
        return self.base[key]

    def __iter__(self):
        for it in self.base:
            if it != self.key:
                yield it

    def __len__(self):
        return len(self.base) - 1
