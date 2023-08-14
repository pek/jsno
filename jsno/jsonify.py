import dataclasses
import functools
import typing

from jsno.extra_data import get_extra_data_configuration
from jsno.property_name import get_property_name
from jsno.variant import get_variantfamily


"""
valid JSON types.
"""
JSON = bool | int | float | str | list["JSON"] | dict[str, "JSON"] | None


class FieldSpec(typing.NamedTuple):
    name: str
    json_name: str
    optional: bool


@dataclasses.dataclass(slots=True, frozen=True)
class DataclassJsonification:
    """
    Specialized datacalass jsonifier
    """

    label_name: str | None
    label: str | None

    extra_data_property: str | None

    fields: list[FieldSpec]

    def jsonify(self, value) -> dict[str, JSON]:
        result: dict[str, JSON] = {}

        # if the value's class is a member of a variant family,
        # first add the variant label to the jsonified result
        if self.label_name:
            result[self.label_name] = self.label

        # add regular fields
        for field in self.fields:
            val = getattr(value, field.name)
            if not (val is None and field.optional):
                result[field.json_name] = jsonify(val)

        # if extra data is defined, add it's contents
        if self.extra_data_property:
            if val := getattr(value, self.extra_data_property):
                for (key, subval) in val.items():
                    result[key] = jsonify(subval)

        return result

    @staticmethod
    def create(type_):
        family = get_variantfamily(type_)
        extra_data_property = get_extra_data_configuration(type_)

        return DataclassJsonification(
            label_name=family and family.label_name,
            label=family and family.get_label(type_),
            extra_data_property=extra_data_property,
            fields=[
                FieldSpec(field.name, json_name, field.default is None)
                for field in dataclasses.fields(type_)
                if field.name != extra_data_property
                if (json_name := get_property_name(field.type, field.name))
            ]
        )


class JsonificationCache(dict):
    """
    Specialized dictionary that creates jsonifications on demand

    Could use functools.cache, but directly using this is a
    little bit faster
    """
    def __missing__(self, key: type):
        self[key] = DataclassJsonification.create(key)
        return self[key]


jsonifications = JsonificationCache()


def jsonify_dataclass(value) -> dict[str, JSON]:
    """
    Jsonify a value whose type is a dataclass.
    """
    specialized = jsonifications[type(value)]
    return specialized.jsonify(value)


def jsonify_list(value: list) -> list[JSON]:
    """
    Jsonify a list.
    """

    count = len(value)

    if count == 0:
        # shortcut for empty lists
        return value

    ix = 1

    val_json = call_jsonify(value[0])
    if val_json is not value[0]:
        # the first value was transformed. Continue with the same
        # iterator
        result = [val_json]
    else:
        while True:
            if ix == count:
                return value

            val_json = call_jsonify(value[ix])
            if val_json is not value[ix]:
                # found the first transformed value
                result = value[:ix]
                result.append(val_json)
                ix += 1
                break
            ix += 1

    while ix < count:
        val_json = call_jsonify(value[ix])
        result.append(value[ix] if val_json is value[ix] else val_json)
        ix += 1

    return result


def jsonify_dict(value: dict) -> dict[str, JSON]:
    """
    Jsonify a dict.
    """

    result = None
    nonchange_count = 0

    for (key, val) in value.items():

        key_json = key if type(key) is str else str(jsonify(key))
        val_json = call_jsonify(val)

        if result is None:
            if key_json is key and val_json is val:
                nonchange_count += 1
                continue

            result = {}
            if nonchange_count > 0:
                for (k, v) in value.items():
                    result[k] = v
                    nonchange_count -= 1
                    if nonchange_count == 0:
                        break

        result[key_json] = val_json

    return result or value


@functools.singledispatch
def generic_jsonify(value):
    """
    Singledispatch function for defining custom jsonification methods.
    """

    if dataclasses.is_dataclass(value):
        return jsonify_dataclass(value)

    raise TypeError("Don't know how to jsonify", value, type(value))


native_types = {str, int, float, bool, type(None)}


def call_jsonify(value) -> JSON:
    """
    Call jsonify, using optimised paths for the native JSON types.
    """

    if type(value) in native_types:
        return value
    elif type(value) is list:
        return jsonify_list(value)
    elif type(value) is dict:
        return jsonify_dict(value)
    else:
        return generic_jsonify(value)


def call_jsonify_as_type(value, as_type: type) -> JSON:

    # this could be combined with call_jsonify, but it seems that
    # complicating call_jsonify has suprisingly big impact on
    # performance, so keeping the duplicated code for now

    if not issubclass(type(value), as_type):
        raise TypeError(f"Cannot jsonify {value} as {as_type}")

    if as_type in native_types:
        return value
    elif as_type is list:
        return jsonify_list(value)
    elif as_type is dict:
        return jsonify_dict(value)
    else:
        return generic_jsonify.dispatch(as_type)(value)


class Jsonify:
    """
    Singleton type for the jsonify function
    """

    def __call__(self, value) -> JSON:
        """
        Jsonify any value that supports jsonification.
        """
        return call_jsonify(value)

    def call_as_type(self, value, as_type: type) -> JSON:
        """
        Jsonify any value that supports jsonification, dispatching
        on the given type.
        """
        return call_jsonify_as_type(value, as_type)

    def __getitem__(self, type_):
        return lambda value: jsonify.call_as_type(value, type_)

    def register(self, type_):
        return generic_jsonify.register(type_)


jsonify = Jsonify()
