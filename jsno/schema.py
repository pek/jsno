"""
Constructing unjsonifiers that unjsonify dictionaries.
"""

import dataclasses
from typing import NotRequired, Required, get_origin

from jsno.property_name import get_property_name
from jsno.unjsonify import unjsonify, get_unjsonify_for_field
from jsno.fields_unjsonifier import ExtraKeysUnjsonifier, SchemaField


@dataclasses.dataclass
class Schema:
    schema: dict
    total: bool = True
    default_type: type | None = None
    extra_data_key: str | None = None

    def _resolve_default(self, type_, default):
        """
        Get the default value for a field.
        """

        # Required is used as the "default" default. If it's anything
        # other, just return that.
        if default is not Required:
            return default

        # check if the field type is wrapped in NotRquired or Required
        # annotations, and if so, return that
        origin = get_origin(type_)
        if origin is NotRequired or origin is Required:
            return origin

        # return Required or NotRequired, based on the `total` parameter
        # of this schema
        if self.total:
            return Required
        else:
            return NotRequired

    def _map_schema_field(self, name: str, type_, default) -> SchemaField:
        """
        Get the SchemaField for given field name, type, and default value.
        """

        return SchemaField(
            name=name,
            json_name=get_property_name(type_, name),
            default=self._resolve_default(type_, default),
            unjsonify=get_unjsonify_for_field(type_, name),
        )

    def __post_init__(self):
        fields = [
            self._map_schema_field(
                name=key,
                type_=arg[0] if isinstance(arg, tuple) else arg,
                default=arg[1] if isinstance(arg, tuple) else Required
            )
            for (key, arg) in self.schema.items()
        ]

        self._unjsonifier = ExtraKeysUnjsonifier.create(
            as_type=None,
            fields=fields,
            default_unjsonifier=self.default_type and unjsonify[self.default_type],
            extra_data_key=self.extra_data_key,
        )

    def unjsonify(self, value):
        return self._unjsonifier(value)

    def extend(self, **kwargs):
        """
        Return an extended version of the schema.

        Combines the given "schema" argument with the existing one, and replaces
        the other configuration options.
        """

        if 'schema' in kwargs:
            schema = self.schema.copy()
            for (key, val) in kwargs['schema'].items():
                if val is None:
                    schema.pop(key, None)
                else:
                    schema[key] = val
            kwargs['schema'] = schema

        return dataclasses.replace(self, **kwargs)
