import functools

from typing import Callable


class VariantFamily:
    """
    VariantFamily represents a variant class hierarchy.
    """

    def __init__(self, root_class: type, label_name: str):
        self.root_class = root_class
        self.label_name = label_name

        self._label_for_class: dict[type, str] = {}
        self._class_for_label: dict[str, type | None] = {}

    def get_variant(self, label: str) -> type | None:
        """
        Get the variant class corresponding to the given label,
        or None if there is no class registerd for that label.
        """

        # check the cache first, using VariantFamily as the sentinel!
        cls = self._class_for_label.get(label, VariantFamily)
        if cls is not VariantFamily:
            return cls

        # search subclasses
        cls = self._search_variant(label, self.root_class)
        self._class_for_label[label] = cls

        return cls

    def _search_variant(self, label: str, cls: type) -> type | None:

        if label == self.get_label(cls):
            return cls

        for sub in cls.__subclasses__():
            if it := self._search_variant(label, sub):
                return it

        return None

    def get_label(self, cls: type) -> str:
        """
        Get the label for a class. If not expiclitly, set, using the
        variantlabel decorator, the label is taken from the class name.
        """
        return self._label_for_class.get(cls) or cls.__name__

    def register_variant(self, cls: type, label: str):
        """
        Register a new variant to be found using the given label.
        """

        if self.get_variant(label) is not None:
            raise ValueError(f"Variant with the label '{label}' already registered")

        self._label_for_class[cls] = label

        # clear the label search cache, as there might be a change
        self._class_for_label.clear()


@functools.singledispatch
def _get_variantfamily(cls: type) -> VariantFamily | None:
    """
    Get the VariantFamily instance corresponding to a class,
    or None, if it is not part of a variant hierarchy
    """
    return None


def get_variantfamily(cls: type) -> VariantFamily | None:
    """
    Get the variant family that the argument type is part of, or
    None if it is not part of any.
    """
    return _get_variantfamily.dispatch(cls)(None)


def variantfamily(label: str = "label") -> Callable[[type], type]:
    """
    Decorator for marking the root of a variant family.
    """

    def decorator(cls: type) -> type:

        # make sure that the class is not already part of a variant
        # family, e.g. through a superclass
        if (family := get_variantfamily(cls)) is not None:
            raise ValueError(
                f"Class {cls} is already a member of"
                f"a variant family {family}"
            )

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

        family.register_variant(cls, label)
        return cls

    return decorator
