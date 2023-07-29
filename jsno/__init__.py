"""
Jsonify Python objects to JSON-compatible values, and unjsonify it back to
Python objects.

Jsonify maps any Python object to a structure consisting of dicts, lists,
and primitive values that is ready to be converted to JSON.

Unjsonify converts such JSON-structure to a given type. The type to convert
to must be given as argument.

The following types are currently supported:
    - int, float, bool
    - None (null in JSON)
    - lists and tuples
    - dicts
    - types defined as dataclass
    - enum types
    - date and datetime

Any type can be made compatible by registering custom functions for converting
to/from a json structure. Example converters for date and datetime are provided.

Note that the jsoniser unjsonisers are matched in reverse registration order,
so if there is a separate jsoniser/unjsoniser defined for both a subclass and
it's superclass, -the superclass must be registered first.

A custom class can be made compatible also by marking it with the
`jsonify_with_method` deorator, and providing jsonify method and
unjsonify class method.

"""

import json

from jsno.jsonify import jsonify
from jsno.jsonize import loads, dumps
from jsno.method import jsonify_with_method
from jsno.unjsonify import unjsonify, UnjsonifyError
from jsno.variant import get_variantfamily, variantfamily, variantlabel

import jsno.abc
import jsno.standard
