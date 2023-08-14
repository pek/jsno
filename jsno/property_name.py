from dataclasses import dataclass

from jsno.utils import Annotation


@dataclass(frozen=True, slots=True)
class PropertyName(Annotation):
    """
    Annotation type for marking a property (a dataclass field), to
    be mapped to something other when converting to JSON.
    """

    name: str
    """The name to use in JSON"""


def property_name(name) -> PropertyName:
    return PropertyName(name)


def get_property_name(type_: type, default: str) -> str:
    """
    Get the property name for a type.

    If there is a property_name annotation attched, use it's
    name. Otherwise return the default.
    """

    annotation = PropertyName.get_annotation(type_)
    if annotation:
        return annotation.name
    else:
        return default
