import functools


class VariantClass:

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
def _get_variantclass(cls):
    """
    Get the VariantClass instance corresponding to a class,
    or None, if it is not part of a variant hierarchy
    """
    return None


def variantclass(label: str = 'label'):

    def decorator(cls):
        variantclass = VariantClass(cls, label)

        @_get_variantclass.register(cls)
        def _(cls):
            return variantclass

        return cls

    return decorator


def get_variantclass(cls):
    if isinstance(cls, type):
        return _get_variantclass.dispatch(cls)(None)
    else:
        return None


def variantlabel(label):

    def decorator(cls):
        get_variantclass(cls).label_for_class[cls] = label
        return cls

    return decorator