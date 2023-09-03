import copy
import dataclasses
import functools
import json

from collections.abc import Mapping
from typing import Any, Callable, Required, NotRequired

from jsno.extra_data import get_extra_data_configuration, IgnoreExtraKeys
from jsno.utils import contextvar, get_typename


class UnjsonifyError(TypeError):
    def __init__(self, value, type, detail=None, message=None):
        if message is None:
            try:
                jsonvalue = json.dumps(value)
            except Exception:
                jsonvalue = repr(value)

            message = f"Cannot unjsonify as {get_typename(type)}: {jsonvalue}"
            if detail is not None:
                message = f"{message}: {detail}"

        super().__init__(message)
        self.value = value
        self.type = type
        self.detail = detail


unjsonify_context = contextvar(on_extra_key="error", self_type=None)
"""Context for passing unjsonify-time configuration down to the unjsonifiers"""


def typecheck(value: Any, jsontype: type | tuple[type, ...], as_type: Any) -> None:
    """
    Check if the value is an instance of the type given as `jsontype`
    and if not, raise an appropriate UnjsonifyError
    """

    if not isinstance(value, jsontype):
        raise UnjsonifyError(value=value, type=as_type)


@dataclasses.dataclass(frozen=True, slots=True)
class SchemaField:
    """
    Specification on how to map one field (either a key in a dict or
    a property in a dataclass) from JSON to the Python counterpart.
    """

    name: str
    """Name of the field in the resulting object"""

    json_name: str
    """Name of the field in JSON"""

    unjsonify: Callable
    """Function to unjsonifiy the value of the field"""

    default: Any = NotRequired
    """
    Default value for the field. Special values Required and NotRequired
    can be used instead to control if the value must be present or can
    be omitted from the result.
    """


@dataclasses.dataclass
class FieldsUnjsonifier:
    as_type: type
    fields: list[SchemaField]

    @functools.cached_property
    def source_names(self) -> frozenset[str]:
        """
        The set of keys expected to be in the source (JSON) data
        """
        return frozenset(field.json_name for field in self.fields)

    def unjsonify_fields(self, value: Mapping) -> dict:
        """
        Process a JSON object, unjsonifying each field.
        """

        typecheck(value, (dict, Mapping), self.as_type)

        result = {}
        found_count = 0

        for field in self.fields:
            if field.json_name in value:
                json_value = value[field.json_name]
                result[field.name] = field.unjsonify(json_value)
                found_count += 1
            elif field.default is Required:
                detail = f"Required key not found: {repr(field.json_name)}"
                raise UnjsonifyError(value, self.as_type, detail)

            elif field.default is NotRequired:
                pass
            else:
                result[field.name] = copy.deepcopy(field.default)

        if found_count < len(value):
            self.handle_extra_keys(value, result)

        return result

    def handle_extra_keys(self, value: Mapping, result: dict) -> None:
        if unjsonify_context.on_extra_key != "error":
            return

        extra_keys = {key for key in value if key not in result}
        detail = f"Extra keys: {', '.join(map(repr, extra_keys))}"
        raise UnjsonifyError(value, self.as_type, detail)

    def __call__(self, value):
        return self.unjsonify_fields(value)


@dataclasses.dataclass
class ExtraKeysUnjsonifier(FieldsUnjsonifier):
    """
    Extension of FieldsUnjsonifier that handles extra keys
    in the incoming JSON data.

    The extra values are unjsonified using the default_unjsonifier.
    If extra_data_key is given, any found extra keys are inserted in
    this property. If not, the keys are inserted in the resulting
    dictionary directly.
    """

    default_unjsonifier: Callable
    """Unjsonify function to call on unexpected field values."""

    extra_data_key: str | None
    """key to the property where extra data should be put."""

    def handle_extra_keys(self, value, result):
        # choose where to put the extra values
        if self.extra_data_key is None:
            # extra_data_key not defined -> put extra data
            # directly to the result dict
            extra = result
        else:
            # extra_data_key defined -> put extra data to the property
            # pointed at by it

            if self.extra_data_key not in result:
                # if the extra data property does not exist in
                # result, create it first
                result[self.extra_data_key] = {}

            extra = result[self.extra_data_key]

        # copy the extra values
        for key in value:
            if key not in self.source_names:
                extra[key] = self.default_unjsonifier(value[key])

    @staticmethod
    def create(extra_data_key, default_unjsonifier=None, **kwargs):
        """
        Create an unjsonifier. Chooses the class depending on if
        the extra data handling arguments are present.
        """

        if default_unjsonifier is None and extra_data_key is None:
            return FieldsUnjsonifier(**kwargs)

        if extra_data_key is IgnoreExtraKeys.instance:
            return IgnoreExtraKeysUnjsonifier(**kwargs)

        return ExtraKeysUnjsonifier(
            default_unjsonifier=default_unjsonifier or (lambda it: it),
            extra_data_key=extra_data_key,
            **kwargs
        )


class IgnoreExtraKeysUnjsonifier(FieldsUnjsonifier):
    """
    Extension of FieldsUnjsonifier that ignores extra keys.
    """
    def handle_extra_keys(self, value, result):
        pass


def create_unjsonifier(as_type, fields):
    """
    Create unjsonifier for a type (a dataclass or a TypedDict)
    """

    extra_data_property = get_extra_data_configuration(as_type)

    return ExtraKeysUnjsonifier.create(
        as_type=as_type,
        fields=fields,
        extra_data_key=extra_data_property,
    )
