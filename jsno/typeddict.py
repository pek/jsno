import functools

from jsno.unjsonify import unjsonify, resolve_field_unjsonifiers, ReferThrough
from jsno.fields_unjsonifier import create_unjsonifier


@functools.cache
def unjsonify_typeddict_factory(as_type):
    if as_type in unjsonify._context_stack:
        return ReferThrough(as_type)

    required_keys = as_type.__required_keys__

    return create_unjsonifier(
        as_type=as_type,
        fields=resolve_field_unjsonifiers(as_type, required_keys=required_keys),
    )
