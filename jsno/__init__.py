import json

from jsno.jsonify import jsonify
from jsno.unjsonify import unjsonify, UnjsonifyError
from jsno.variant import variant_family


def dumps(value, **kwargs):
    return json.dumps(jsonify(value), **kwargs)


def loads(value, as_type, **kwargs):
    return unjsonify[as_type](json.loads(value, **kwargs))
