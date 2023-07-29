# jsno
Convert Python data to and from json-compatible data structures

## Example

First, let's define a custom dataclass to keep track of domain data:

```py
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
jsonized = jsno.dumps(domains, indent=4)
pathlib.Path('domains.json').write_text(jsonized)
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
jsonized = pathlib.Path('domains.json').read_text()
domains = jsno.loads(jsonized, as_type=list[DomainRecord])

assert domains[0].enabled_at.year == 1992
```

## Native JSON types

The following types are native JSON types, and they are mapped to themselves
when jsonifying and unjsonifying:

* str
* bool
* int
* float
* NoneType (None maps to JSON's null)
* list (JSON array)
* dict (JSON object)

## Abstract base classes

The operations are also defined to the following abstract base classes, so
any type implementing them can be jsnoified and unjsonified:

* Sequence (maps to list)
* Mapping (maps to dict)
* Set (maps to list)
* ByteString (maps to base64 encoded string)

## Union types

Union types (typing.Union and T | U) are supported. However, when unjsonising
union types, it's important that the JSON representations of two different
types do not overlap.

## Dataclasses

Dataclasses are supported. They get converted to JSON objects. The name of the
class is not included in the result, unless the dataclass is a member of a
_variant family_.

## Other standard Python types

* tuples
* ranges
* enums
* date and datetime objects (converted to ISO-formatted strings)
* decimals (converted to JSON strings)
* pathlib.Path
* zoneinfo.ZoneInfo
* Literal (only int and str literals)
