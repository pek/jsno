# jsno

Convert Python data to and from JSON-compatible data structures.

Jsno provides functions that turn any Python values into JSON-compatible
structures and back. The jsonified data can then be used wherever JSON
data is required: it can be dumped into a file, sent over the network
in an API call, or stored in a database that support JSON data.

Note that jsno does not replace the standard _json_ module - it does not
produce JSON encoded string, but instead turns arbitrary Python values into
structures that _can_ be JSON encoded.

Jsno provides jsonification for most of the standard Python datatypes.
It is also easily _extensible_, so that custom jsonification can be
defined for new datatypes.

Jsno has special support for _dataclasses_, so no effort is needed to
make jsonificatiin work for classes defined as dataclasses.

## Basic usage

Data is converted to JSON strutures using the _jsonify_ function:

```py
from datetime import datetime, date
import jsno

jsonified = jsno.jsonify({"date": datetime.utcnow().date()})
assert jsonified == {"date": "2023-07-30"}
```

 Converting the jsonified data back is done using the _unjsonify_ function.
 However, _unjsonify_ can't guess the type of the resulting value that the
 JSON data should be converted to. So it needs to be given it explicitly, using
 "bracket syntax":

 ```py
value = jsno.unjsonify[dict[str, date]](jsonified)
assert value == {"date": datetime.date(2023, 7, 30)}
```

Here the example value had to be typed as  a dictionary with date values.
When working with heterogenous data, it's usually best to define it as
_dataclasses_ instead.

## Example with dataclasses

First, let's define a custom dataclass to keep track of domain data:

```py
from dataclasses import dataclass

@dataclass
class DomainRecord:
    domain: str
    ips: list[str]
    enabled_at: date | None = None
```

Then, let's make a couple of such records:

```py
domains = [
    DomainRecord(
        domain="example.com",
        ips=["93.184.216.34"],
        enabled_at=date(1992, 1, 1)
    ),
    DomainRecord(
        domain="another.example.com",
        ips=[]
    )
]
```

With jsno, these can be turned into JSON and stored in a local file:

```py
import json
import pathlib

jsonified = jsno.jsonify(domains)
pathlib.Path('domains.json').write_text(json.dumps(jsonified, indent=4))
```

The file will look like this:

```json
[
    {
        "domain": "example.com",
        "ips": ["93.184.216.34"],
        "enabled_at": "1992-01-01"
    },
    {
        "domain": "another.example.com",
        "ips": []
    }
]
```

To read and use the domains later:

```py
jsonified = json.loads(pathlib.Path('domains.json').read_text())
domains = jsno.unjsonify[list[DomainRecord]](jsonified)

assert domains[0].enabled_at.year == 1992
```

## Supported types

### Native JSON types

The following types are native JSON types, and they are mapped to themselves
when jsonifying and unjsonifying:

* str
* bool
* int
* float
* NoneType (None maps to JSON's null)
* list (JSON array)
* dict (JSON object)

### Abstract base classes

The operations are also defined to the following abstract base classes, so
any type implementing them can be jsnoified and unjsonified:

* Sequence (maps to list)
* Mapping (maps to dict)
* Set (maps to list)
* ByteString (maps to base64 encoded string)

### Union types

Union types (typing.Union and T | U) are supported. However, when unjsonising
union types, it's important that the JSON representations of two different
types do not overlap. Otherwise, jsno will choose to unjsonify ambiguous data
to the first type in the union that matches.

### Dataclasses

Dataclasses are supported. They get converted to JSON objects. The name of the
class is not included in the result, unless the dataclass is a member of a
_variant family_.

### Other standard Python types

* tuples
* ranges
* enums
* date and, time and datetime objects (converted to ISO-formatted strings)
* timedelta and timezone
* complex
* decimal.Decimal (converted to JSON strings)
* pathlib.Path
* re.Pattern
* zoneinfo.ZoneInfo
* uuid.UUID
* types.SimpleNamespace
* Literal (only int and str literals)
* NamedTuple
* TypedDict
* NewType

## Dumps and loads

Jsno provides shortcut functions _dumps_ and _loads_ with interface that is
similar to the standard _json_ module function. _jsno.dumps_ both jsonifies its argument
and turns it into a JSON-encoded string, similar to standard _json.dumps_
function. Correspondinly, _jsno.loads_ both decodes and unjsonify JSON data.

```py
json = jsno.dumps(date(2023, 7, 30))
assert json == "2023-07-30"

day = jsno.loads[date](json)
assert day == date(2023, 7, 30)
```

## Defining custom jsonification

Jsno's _jsonify_ and _unjsonify_ are defined as _singledispatch_ functions, so
implementations to new types can be registered using a decorator.

For example, Python's standard random number generator can be given json representation:

```py
from random import Random


@jsno.jsonify.register(Random)
def _(value):
    # jsonify the random number generator's state
    state = value.getstate()
    return jsno.jsonify(state)


@jsno.unjsonify.register(Random)
def _(value, as_type):
    # first unjsonify the state
    state = jsno.unjsonify[tuple[int, tuple[int, ...], float | None]](value)

    # create a new Random object and install the unjsonified state
    result = Random()
    result.setstate(state)
    return result
```

Now it's possible to for example have a random number generator as a part of a data
structure defined using dataclasses, and have it converted to and from JSON
automatically:

```py
@dataclass
class GameState:
    identifier: str
    board: list[tuple[int, int, str]]
    rng: Random


def save_game(database, state: GameState):
    database.store(state.identifier, jsonify(state))


def load_game(database, identifier: str) -> GameState:
    json = database.load(identifier)
    return unjsonify[GameState](json)
```

## Unjsonify context

By default, the unjsonify raises an error (UjsonifyError), if the JSON object
that is being converted to a dataclass contains extra keys. This is often the
most appropriate behavior, for example when converting the request body of an API
request, it's best to let the caller know that they might have mistyped property
names in their data. However, sometimes, it's best to just ignore the extra properties,
for example when reading persistent data that could have obsolete properties in it
that are not reflected in the dataclass definition.

The extra key behavior can be controlled by running the unjsonification inside
the approproate _context_:

```py
with unjsonify.ignore_extra_keys:
    state = unjsonify[GameState](data)
```

## Constraints

Jsno support annotating types with constraints that are boolean valued functions
that must return True for the unjsonified value for it to be valid. For example,
to only accept email addresses that contain the "@" character:

```py
from typing import Annotated
from jsno import Constraint

@dataclass
class User:
    username: str
    email: Annotated[str, Constraint(lambda it: "@" in it)]

```

Constraints are always used within Annotated, so there is a shortcut operator to
make the definitions clearer. This is equivalent to the definition above:

```py
@dataclass
class User:
    username: str
    email: str // Constraint(lambda it: "@" in it)

```

Using the `//`-operator, the type of the property is directly after the colon,
not nested inside an Annotated-expression.

The most typical constraints are those that limit the value or the length of a
property to a certain range. For these, jsno provides predefined shortcuts:

```py
@dataclass
class Player:
    username: str // Constraint.len(min=4, max=16)
    credits: int // Constraint.range(min=0)
```

There is also a constraint for matching the value with a regular expression:

```py
@dataclass
class Variable:
    name: str // Constraint.regex("[A-Za-z_][A-Za-z0-9_]*")
```

Constraints can be joined using the or-operator `|`:

```py
LiteralInt = Constraint.regex("[0-9]*")
LiteralString = Constraint.regex('".*"')

@dataclass
class LiteralValue:
    value: str // (LiteralInt | LiteralString)
```

Constraints can be attached to classes as well:

```py
@dataclass
@Constraint(lambda range: range.min <= range.max)
class Range:
    min: int
    max: int
```

The constraint will be validated any time an instance of the class is unjsonified.


## Customizing field names

It could be necessary to map the field names of a dataclass to something other
than the ones defined in the Python class. For example, the classes could be
modeling a HTTP API that uses property names that are not compatible with Python's
naming rules, like using _hyphenated-names_, or names that are reserved in Python,
such as "class". The field name can be customized with an `property_name` annotation
that can be attached to a type similar to a constraint:

```py
@dataclass
class APIRequest:
    class_: str // jsno.property_name("class")
    instance_count: int // jsno.property_name("instance-count")


request = APIRequest(class_="Request", instance_count=1)
json = jsonify(request)

assert json == {"class": "Request", "instance-count": 1}
assert unjsonify[APIRequest](json) == request
```

## Dynamic unjsonification schemas

It is possible to define ad-hoc unjsonifition schemas without declaring new types,
using the `jsno.Schema` class.

For example, defining a schema for HTTP requests:

```py
schema = jsno.Schema({
    "method": str,
    "url": str,
    "headers": dict[str, str],
    "body": bytes,
})
```

Note that the types are given as _values_, not as _annotations_ to the schema.
Unjsonifying with the schema returns a dictionary with the shape similar to
the schema itself.

Unjsonification shemas can be useful when the data format is descrirbed by dynamic
data, for example user-specific settings that are retrieved from a database,
instead of being specified in the source code. TypedDict type from python's
`typing` module can be used for similar purposes, but `Schema` offers a
couple of additional options:

* `ignore_extra_keys` argument can be given to have the unjsonification discard
  unexpected keys, instead of raising an error
* `default_type` argument can be given instead, to have the unjsonification accept
  any key, unjsonifying the unexpected keys to the default type.
* `extra_data_key` argument can be supplied to control where the unexpected
  keys are put. By default, if default type is specified, the extra entries are
  inserted to the resulting dictionary. If `extra_data_key` is supplied, the
  extra entries are inserted to a subdictionary pointed by `extra_data_key`
  instead.
* `total` argument can be set to False in order to make all listed properties
  non-required. `total` is True by default, so all keys must be present in the
  input data. Totality can be overriden for individual properties by annotating
  them with `typing.Required` or `typing.NotRequired` similarly to their usage
  with `TypedDict`.

## Function argument schemas

A typical application of unjsonification schemas is converting messages encoded
in JSON into function arguments, for example converting JSON-encoded HTTP
request bodies into handler function arguments. For this purpose, jsno provides
the `Schema.from_arguments` function that analyses the signature of a function
and produces the corresponding unjsonification schema to convert a JSON object
to the keyword argument expected by the function.

As an example, here is a simple request handler function signature.

```py
def process_event(event_type: str, user_id: int, date: datetime):
    ...
```

And here is a JSON object that should be processed by the function:

```py
json_object = {
    "event_type": "SIGN-IN",
    "user_id": 1002124,
    "date": "2023-08-26T06:42:11Z"
}
```

To feed the object to the handler function, first derive unjsonification schema
and use that to convert the JSON object:

```py
schema = jsno.Schema.from_arguments(process_event)

kwargs = unjsonify[schema](json_object)

process_event(**kwargs)
```

## Variant families

Sometimes it's useful to have a hierarchy of classes, consisting of several subclasses
that need to be stored in JSON. A typical example is defining the AST (abstract syntax
tree) for a domain-specific language. Here's the AST of a simple expression language,
defined using a hierarchy of dataclasses:

```py
class Expression:
    pass


@dataclass
class LiteralInt(Expression):
    value: int

    def evaluate(self, context):
        return self.value


@dataclass
class BinaryOperator(Expression):
    left: Expression
    right: Expression


class Add(BinaryOperator):
    def evaluate(self, context):
        return self.left.evaluate(context) + self.right.evaluate(context)


class Multiply(BinaryOperator):
    def evaluate(self, context):
        return self.left.evaluate(context) * self.right.evaluate(context)

```

Now, it's possible to create syntax trees, evaluate them, and convert them into JSON:

```py
ast = Add(LiteralInt(1), Multiply(LiteralInt(2), Reference("x")))

assert ast.evaluate({"x": 3}) == 7

json = jsno.dumps(ast, indent=4)
```

`json` will contain:
```json
{
    "left": {
        "value": 1
    },
    "right": {
        "left": {
            "value": 2
        },
        "right": {
            "name": "x"
        }
    }
}
```

However, reading the AST back from JSON won't work. Trying to unjsonify it as an
_Expression_ fails:

```py
jsno.unjsonify[Expression](json)
# TypeError: Unjsonify not defined for <class 'Expression'>
```

Even if you defined the base Expression class as a dataclass, jsno wouldn't not which
of the subclasses should it choose.

The solution to the problem is to mark the root of the expression as the root of a
_variant family_, using the `variantfamily` decorator:

```py
@jsno.variantfamily(label="type")
class Expression:
    pass
```

When a class is marked to form a variant family, jsno will add a label to the data
jsonfied from it's, or it's subclasses' instances, to identify the class.

Adter adding the decorator, the JSON produced by _jsonify_ contains labels to
differentiate between the subclasses (variants):

```json
{
    "type": "Add",
    "left": {
        "type": "LiteralInt",
        "value": 1
    },
    "right": {
        "type": "Multiply",
        "left": {
            "type": "LiteralInt",
            "value": 2
        },
        "right": {
            "type": "Reference",
            "name": "x"
        }
    }
}
```

The variant label's name (`type`) was given in the decorator.

Now, jsno is able to unjsonify the AST:

```py
unjsonified_ast = jsno.unjsonify[Expression](json)
assert unjsonified_ast == ast
```

By default, the label for a class is taken from the class name. It's also possible
to give it explicitly using the `variantlabel` decorator:

```py
@jsno.variantlabel('mult')
class Multiply(Expression):
    # ...

```

## Installation

Install jsno with pip:

```bash
pip install jsno
```

Jsno has no 3rd party dependencies.


## Release Notes

### Version 1.2.1

* allow using schemas in unjsonify type arguments
* handle `**kwargs` in function argument schemas
* jsonify datetime.time as hour:minute if seconds is 0
* remove extra zeros from jsonified timedeltas

### Version 1.2.0 (2023-08-20)

* ignore non-field members of dataclasses when unjsonifying
* better error messages
* special handling for optionals
* multi-label variants
* optional inclusion of variant labels in unjsonized data
* JSON type alias
* deriving unjsonification schema from function signature

### Version 1.1.5 (2023-08-14)

* removes a single debug print

### Version 1.1.4 (2023-08-14)

* class constraints

### Version 1.1.3 (2023-08-14)

* support for types.SimpleNamespace and uuid.UUID
* orphan families for tagged variants without family
* unjsonification schemas without a type

### Version 1.1.2 (2023-08-09)

* support for Self type
* support for recursive and mutually recursive dataclasses
* handle type hints in dataclasses given as strings

### Version 1.1.1 (2023-08-07)

* property name annotations
* fix optional value jsonification when no default
* performance improvement for dataclass jsonification

### Version 1.1.0 (2023-08-07)

* regular expression constraints
* operator // for constraints
* joining constraints with | operator
* anonymous Record types
* support for datetime.timezone and datetime.timedelta
* support for re.Pattern
* support for TypedDict and NewType
* support for untyped tuples and namedtuples
* unjsonify context for ignoring extra properties
* specifying target for extra properties in dataclasses
* performance improvements for unjsonify

### Version 1.0.7 (2023-08-04)

* support for typing.Annotated
* constraint annotations

### Version 1.0.6 (2023-08-03)

* support for datetime.time

