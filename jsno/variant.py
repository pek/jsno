import functools

from typing import Callable, get_type_hints


class VariantFammilyBase:

    def includes_label(self, variant_type):
        return self.label_name in get_type_hints(variant_type)


class VariantFamily(VariantFammilyBase):
    """
    VariantFamily represents a variant class hierarchy.
    """

    def __init__(self, root_class: type, label_name: str):
        self.root_class = root_class
        self.label_name = label_name

        self._labels_for_class: dict[type, list[str]] = {}
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

        if label in self.get_labels(cls):
            return cls

        for sub in cls.__subclasses__():
            if it := self._search_variant(label, sub):
                return it

        return None

    def get_labels(self, cls: type) -> list[str]:
        """
        Get the labels for a class. If not expiclitly, set, using the
        variantlabel decorator, the label is taken from the class name.
        """
        if labels := self._labels_for_class.get(cls):
            return labels
        else:
            return [cls.__name__]

    def register_variant(self, cls: type, labels: list[str]):
        """
        Register a new variant to be found using the given label.
        """

        for label in labels:
            if self.get_variant(label) is not None:
                raise ValueError(f"Variant with the label '{label}' already registered")

        self._labels_for_class[cls] = labels

        # clear the label search cache, as there might be a change
        self._class_for_label.clear()


class OrphanVariant(VariantFammilyBase):
    def __init__(self, cls, label_name, labels):
        self.cls = cls
        self.label_name = label_name
        self.labels = labels

    def get_variant(self, label: str) -> type | None:
        if label in self.labels:
            return self.cls
        else:
            return None

    def get_labels(self, cls: type) -> str:
        return self.labels


@functools.singledispatch
def _get_variantfamily(cls: type) -> VariantFamily | OrphanVariant | None:
    """
    Get the VariantFamily instance corresponding to a class,
    or None, if it is not part of a variant hierarchy
    """
    return None


def get_variantfamily(cls: type) -> VariantFamily | OrphanVariant | None:
    """
    Get the variant family that the argument type is part of, or
    None if it is not part of any.
    """
    return _get_variantfamily.dispatch(cls)(None)


def register_variantfamily(cls, family):
    """
    Mark the argument class as being the root of a variant family.
    """
    @_get_variantfamily.register(cls)
    def _(cls):
        return family


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
        register_variantfamily(cls, family)
        return cls

    return decorator


def variantlabel(label: str | list[str] | None = None, key: str | None = None) -> Callable[[type], type]:
    """
    Decorator for specifying the variant label of a class

    key is used with orphan variants
    """

    def decorator(cls: type) -> type:
        if label is None:
            # if no label is given, use the class name
            labels = [cls.__name__]
        elif isinstance(label, str):
            labels = [label]
        else:
            labels = label

        family = get_variantfamily(cls)
        if family and isinstance(family, VariantFamily):
            if key is not None and key != family.label_name:
                raise ValueError("Key must match the family label name")

            family.register_variant(cls, labels)
        else:
            if key is None:
                raise ValueError("Key required for orphan variant")

            family = OrphanVariant(cls, key, labels)
            register_variantfamily(cls, family)

        return cls

    return decorator
