"""
"Jsonization" functions, for turning data directly into a JSON string and
back. Mimics the standard json module's interface to provide drop-in
replacements.
"""

import json

from jsno.jsonify import jsonify
from jsno.unjsonify import unjsonify


def dumps(value, **kwargs) -> str:
    """
    Turn the argument into JSON. First jsonifies it and then calls
    the standard json.dumps with the result.
    """

    return json.dumps(jsonify(value), **kwargs)


def loads(arg: str, as_type, **kwargs):
    """
    Load a value of given type from a JSON-encoded string.
    """

    return unjsonify[as_type](json.loads(arg, **kwargs))
