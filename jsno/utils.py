import dataclasses
import threading
import typing

from collections.abc import Mapping


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


class Context:
    def __init__(self, contextvar, values):
        self.contextvar = contextvar
        self.values = values
        self.old_values = {}

    def __enter__(self):
        for (key, val) in self.values.items():
            self.old_values[key] = getattr(self.contextvar, key)
            setattr(self.contextvar, key, val)

    def __exit__(self, type, value, tb):
        for (key, val) in self.old_values.items():
            setattr(self.contextvar, key, val)


def contextvar(**kwargs):
    defaults = kwargs

    threadlocal = threading.local()

    class Contextvar:

        def __getattr__(self, key):
            try:
                return getattr(threadlocal, key)
            except AttributeError:
                pass
            return defaults[key]

        def __setattr__(self, key, value):
            setattr(threadlocal, key, value)

        def __call__(self, **kwargs):
            return Context(self, kwargs)

    return Contextvar()


class Annotation:
    def __rfloordiv__(self, type_):
        """
        Override the // operator: Annotate a type with this annotation.

        type // Annotation(...)
        """
        return typing.Annotated[type_, self]

    @classmethod
    def get_annotation(cls, type_) -> typing.Self | None:
        """
        Get the (first) annotation of this calsss attached to a type, or
        None if it doesn't have one.
        """
        if typing.get_origin(type_) is typing.Annotated:
            for arg in typing.get_args(type_):
                if isinstance(arg, cls):
                    return arg

        return None
