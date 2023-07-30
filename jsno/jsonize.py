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


class Loads:
    """
    Factory for type-specific loads functions
    """

    def __getitem__(self, type_):
        unjsonify_ = unjsonify[type_]
        return lambda *args, **kwargs: unjsonify_(json.loads(*args, **kwargs))


loads = Loads()
