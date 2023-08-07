import dataclasses


def as_field(name, arg):
    if isinstance(arg, tuple):
        # argument is a pair.
        (type_, field) = arg
        if isinstance(field, dataclasses.Field):
            # second element is a dataclass field - take it as is
            return (name, type_, field)
        else:
            # sscond element is something other - treat as a default value
            return (name, type_, dataclasses.field(default=field))
    else:
        # Argument is something that's not a tuple - interpret
        # it to be a type

        return (name, arg)


def Record(**kwargs):
    """
    Function that constructs anonoymous dataclasses.
    """

    fields = [as_field(name, arg) for (name, arg) in kwargs.items()]
    return dataclasses.make_dataclass("Record", fields)
