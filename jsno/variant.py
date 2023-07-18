import functools

from typing import Callable


class VariantClass:
    """
    VariantClass represents the root of a variant class hierarchy.
    """

    def __init__(self, cls, label_name):
        self.cls = cls
        self.label_name = label_name

        self.label_for_class = {}

    def get_variant(self, label, cls=None):
        if cls is None:
            cls = self.cls

        if label == self.get_label(cls):
            return cls

        for sub in cls.__subclasses__():
            if (it := self.get_variant(label, sub)):
                return it

        return None

    def get_label(self, cls):
        return self.label_for_class.get(cls) or cls.__name__


@functools.singledispatch
def _get_variantclass(cls: type):
    """
    Get the VariantClass instance corresponding to a class,
    or None, if it is not part of a variant hierarchy
    """
    return None


def get_variantclass(cls : type) -> VariantClass | None:
    """
    Get the variantclass that the argument type is part of,
    or None if it's not part of any.
    """
    if isinstance(cls, type):
        return _get_variantclass.dispatch(cls)(None)
    else:
        return None


def variantclass(label: str = 'label') -> Callable[[type], type]:
    """
    Decorator for marking the root of a variant family.
    """

    def decorator(cls: type) -> type:
        variantclass = VariantClass(cls, label)

        @_get_variantclass.register(cls)
        def _(cls):
            return variantclass

        return cls

    return decorator


def variantlabel(label: str) -> Callable[[type], type]:
    """
    Decorator for specifying the variant label of a class
    """

    def decorator(cls: type) -> type:
        variantclass = get_variantclass(cls)
        if not variantclass:
            raise TypeError(f"Not a variantclass: {cls}")

        variantclass.label_for_class[cls] = label
        return cls


    return decorator
