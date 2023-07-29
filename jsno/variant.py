import functools

from typing import Callable


class VariantFamily:
    """
    VariantFamily represents a variant class hierarchy.
    """

    def __init__(self, root_class, label_name: str):
        self.root_class = root_class
        self.label_name = label_name

        self.label_for_class = {}

    def get_variant(self, label: str , cls=None) -> type | None:
        """
        Get the variant class corresponding to the given label,
        or None if there is no class registerd for that label.

        Starts the search from class cls, or from the root class
        if not provided.
        """

        if cls is None:
            cls = self.root_class

        if label == self.get_label(cls):
            return cls

        for sub in cls.__subclasses__():
            if (it := self.get_variant(label, sub)):
                return it

        return None

    def get_label(self, cls: type) -> str:
        """
        Get the label for a class. If not expiclitly, set, using the
        variantlabel decorator, the label is taken from the class name.
        """
        return self.label_for_class.get(cls) or cls.__name__


@functools.singledispatch
def _get_variantfamily(cls: type) -> VariantFamily | None:
    """
    Get the VariantFamily instance corresponding to a class,
    or None, if it is not part of a variant hierarchy
    """
    return None


def get_variantfamily(cls : type) -> VariantFamily:
    """
    Get the variant family that the argument type is part of.
    """
    return _get_variantfamily.dispatch(cls)(None)


def variantfamily(label: str = 'label') -> Callable[[type], type]:
    """
    Decorator for marking the root of a variant family.
    """

    def decorator(cls: type) -> type:
        family = VariantFamily(cls, label)

        @_get_variantfamily.register(cls)
        def _(cls):
            return family

        return cls

    return decorator


def variantlabel(label: str) -> Callable[[type], type]:
    """
    Decorator for specifying the variant label of a class
    """

    def decorator(cls: type) -> type:
        family = get_variantfamily(cls)
        if not family:
            raise TypeError(f"Not member of a variant family: {cls}")

        family.label_for_class[cls] = label
        return cls


    return decorator
