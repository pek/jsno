import functools


@functools.singledispatch
def get_extra_data_configuration(arg):
    return None


class IgnoreExtraData:
    pass


Ignore = IgnoreExtraData()


def extra_data(property=None, ignore=None):
    assert property is None or ignore is None

    if ignore is True:
        property = Ignore

    def decorator(cls):
        @get_extra_data_configuration.register(cls)
        def _(arg):
            return property

        return cls

    return decorator
