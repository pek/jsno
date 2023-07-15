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

