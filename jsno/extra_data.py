import functools


@functools.singledispatch
def _get_extra_data_configuration(arg):
    return None


IgnoreExtraData = object()


def extra_data(property=None, ignore=None):
    assert property is None or ignore is None

    if ignore is True:
        property = IgnoreExtraData

    def decorator(cls):
        @_get_extra_data_configuration.register(cls)
        def _(arg):
            return property

        return cls

    return decorator


def get_extra_data_configuration(type_):
    return _get_extra_data_configuration.dispatch(type_)(type_)
