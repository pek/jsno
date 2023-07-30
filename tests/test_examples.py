from dataclasses import dataclass
from datetime import date
from random import Random

import json
import pathlib

import jsno


def test_domain_record_example():

    @dataclass
    class DomainRecord:
        domain: str
        ips: list[str]
        enabled_at: date | None = None

    domains = [
        DomainRecord(
            domain="example.com",
            ips=["93.184.216.34"],
            enabled_at=date(1992, 1, 1)
        ),
        DomainRecord(
            domain="another.example.com",
            ips=[]
        ),
    ]
    jsonified = jsno.jsonify(domains)
    assert jsonified == (
        [
            {
                "domain": "example.com",
                "ips": ["93.184.216.34"],
                "enabled_at": "1992-01-01"
            },
            {
                "domain": "another.example.com",
                "ips": [],
            }
        ]
    )

    pathlib.Path('/tmp/domains.json').write_text(json.dumps(jsonified, indent=4))

    jsonified = json.loads(pathlib.Path('/tmp/domains.json').read_text())
    domains = jsno.unjsonify[list[DomainRecord]](jsonified)

    assert domains[0].enabled_at.year == 1992


@jsno.jsonify.register(Random)
def _(value):
    # jsonify the random number generator as it's state
    return jsno.jsonify(value.getstate())


@jsno.unjsonify.register(Random)
def _(value, as_type):
    # first unjsonify the state
    state = jsno.unjsonify[tuple[int, tuple[int, ...], float | None]](value)

    # create a new Random object and install the unjsonified state
    result = Random()
    result.setstate(state)
    return result


def test_random_example():
    rng = Random()

    jsonified = jsno.jsonify(rng)

    a = rng.gauss()

    rng = jsno.unjsonify[Random](jsonified)

    b = rng.gauss()

    assert a == b
