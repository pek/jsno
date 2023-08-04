import dataclasses


def as_field(name, arg):
    if isinstance(arg, tuple):
        (type_, field) = arg
        if isinstance(field, dataclasses.Field):
            return (name, type_, field)
        else:
            return (name, type_, dataclasses.field(default=field))
    else:
        return (name, arg)


def Record(**kwargs):
    fields = [as_field(name, arg) for (name, arg) in kwargs.items()]
    return dataclasses.make_dataclass("Record", fields)
