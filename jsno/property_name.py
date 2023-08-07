from dataclasses import dataclass
import typing

from jsno.utils import Annotation


@dataclass(frozen=True, slots=True)
class PropertyName(Annotation):
    name: str


def property_name(name):
    return PropertyName(name)


def resolve_field_name(field):
    if typing.get_origin(field.type) is typing.Annotated:
        for arg in typing.get_args(field.type):
            if isinstance(arg, PropertyName):
                return arg.name

    return field.name
