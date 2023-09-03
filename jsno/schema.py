"""
Constructing unjsonifiers that unjsonify dictionaries.
"""

import dataclasses
import functools
import inspect
from typing import Any, NotRequired, Required, get_origin

from jsno.extra_data import IgnoreExtraKeys
from jsno.property_name import get_property_name
from jsno.unjsonify import unjsonify, get_unjsonify_for_field, SchemaType
from jsno.fields_unjsonifier import ExtraKeysUnjsonifier, SchemaField


@dataclasses.dataclass
class Schema(SchemaType):
    schema: dict
    """ The schema, mapping property names to types and default values """

    total: bool = True
    """ If total is true, the properties are required by default. """

    default_type: type | None = None
    """ Default type to use for extra properties """

    extra_data_key: str | None = None
    """ Extra data key that tells where to put the extra keys """

    ignore_extra_keys: bool = False

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

    @functools.cached_property
    def _unjsonifier(self):
        fields = [
            self._map_schema_field(
                name=key,
                type_=arg[0] if isinstance(arg, tuple) else arg,
                default=arg[1] if isinstance(arg, tuple) else Required
            )
            for (key, arg) in self.schema.items()
        ]

        if self.ignore_extra_keys:
            extra_data_key = IgnoreExtraKeys.instance
        else:
            extra_data_key = self.extra_data_key

        return ExtraKeysUnjsonifier.create(
            as_type=None,
            fields=fields,
            default_unjsonifier=self.default_type and unjsonify[self.default_type],
            extra_data_key=extra_data_key,
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

    @staticmethod
    def from_arguments(function, keywords_only=False, **kwargs):
        """
        Derive a schema from a function's signature.

        If keyeords_only is True, only the keyword-only arguments
        are included.
        """

        argspec = inspect.getfullargspec(inspect.unwrap(function))
        return Schema.from_argspec(argspec, keywords_only=keywords_only, **kwargs)

    @staticmethod
    def from_argspec(argspec, keywords_only=False, **kwargs):
        """
        Derive schema from a FullArgSpec object.
        """

        defaults = argspec.kwonlydefaults or {}
        argnames = argspec.kwonlyargs

        if not keywords_only:
            argdefaults = argspec.defaults or ()
            nodefault_arg_count = len(argspec.args) - len(argdefaults)
            args_with_defaults = argspec.args[nodefault_arg_count:]

            defaults.update(zip(args_with_defaults, argdefaults))
            argnames.extend(argspec.args)

        def get_spec(argname):
            type_ = argspec.annotations.get(argname, Any)
            if defaults and argname in defaults:
                return (type_, defaults[argname])
            else:
                return type_

        if (varkw := argspec.varkw) is not None:
            # **kwargs is given. Allow extra arguments, defaulting to the
            # type of kwargs
            kwargs["default_type"] = get_spec(varkw)

        return Schema(
            schema={argname: get_spec(argname) for argname in argnames},
            **kwargs
        )
