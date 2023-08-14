"""
Decorator for marking a class so that it will be jsonified by a method
call: obj.jsonify()
"""
from typing import Any

from jsno.jsonify import jsonify, JSON
from jsno.unjsonify import unjsonify


def jsonify_with_method_call(value):
    """
    Jsonify function that just calls the jsonify method of
    the value object.
    """
    return value.jsonify()


def unjsonify_with_method_call(value: JSON, as_type) -> Any:
    """
    Unjsonify fuction that just calls the unjsonify class
    method of the type.
    """
    return as_type.unjsonify(value)


def jsonify_with_method(cls: type) -> type:
    """
    Decorator for classes that registers jsonify and unjsonify
    to call the corresponding instance and class methods.
    """

    jsonify.register(cls)(jsonify_with_method_call)
    unjsonify.register(cls)(unjsonify_with_method_call)

    return cls
