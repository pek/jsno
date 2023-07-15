import functools


class VariantClass:

    def __init__(self, cls, label_name):
        self.cls = cls
        self.label_name = label_name

    def get_variant(self, label, cls=None):
        if cls is None:
            cls = self.cls

        if label == cls.__name__:
            return cls

        for sub in cls.__subclasses__():
            if (it := self.get_variant(label, sub)):
                return it

        return None

    def get_label(self, cls):
        return cls.__name__


@functools.singledispatch
def _get_variantclass(cls):
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
