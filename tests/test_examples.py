import dataclasses

from jsno import jsonify, unjsonify


def test_domain_record_example():

    @dataclasses.dataclass
    class DomainRecord:
        domain: str
        ips: list[str]
        enabled: bool = False

    domains = [
        DomainRecord(domain="example.com", ips=["93.184.216.34"], enabled=True),
        DomainRecord(domain="another.example.com", ips=[]),
    ]
    jsonified = jsonify(domains)

    assert jsonified == (
        [
            {
                "domain": "example.com",
                "ips": ["93.184.216.34"],
                "enabled": True
            },
            {
                "domain": "another.example.com",
                "ips": [],
                "enabled": False
            }
        ]
    )

    unjsonified = unjsonify[list[DomainRecord]](jsonified)

    assert unjsonified == domains

