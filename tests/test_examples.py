from dataclasses import dataclass
from datetime import date

from jsno import jsonify, unjsonify


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
    jsonified = jsonify(domains)
    print(jsonified)
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

    unjsonified = unjsonify[list[DomainRecord]](jsonified)

    assert unjsonified == domains

