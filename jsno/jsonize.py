"""
"Jsonization" functions, for turning data directly into a JSON string and
back. Mimics the standard json module's interface to provide drop-in
replacements.
"""

import json

from jsno.jsonify import jsonify
from jsno.unjsonify import unjsonify


def dumps(value, **kwargs):
    return json.dumps(jsonify(value), **kwargs)


def loads(value, as_type, **kwargs):
    return unjsonify[as_type](json.loads(value, **kwargs))
