import json

from jsno.jsonify import jsonify
from jsno.unjsonify import unjsonify, UnjsonifyError


def dumps(value, **kwargs):
    return json.dumps(jsonify(value), **kwargs)


def loads(value, as_type, **kwargs):
    return json.loads(unjsonify[as_type](value), **kwargs)
