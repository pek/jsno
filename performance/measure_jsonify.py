import dataclasses
import datetime
import json
import sys


from jsno import jsonify, unjsonify
from performance.utils import measure_time
from tests.test_variant import Expression, expr
from tests.test_dataclasses import Box, Brick, Color, Material


def measure_case(n, item, as_type):
    name = item['name']

    items = {
        "items": [item for i in range(n)]
    }

    with measure_time() as jsonify_time:
        jsonified = jsonify(items)

    with measure_time() as dump_time:
        dump = json.dumps(jsonified)

    bytecount = len(dump)

    with measure_time() as loads_time:
        loaded = json.loads(dump)

    @dataclasses.dataclass
    class Items:
        items: list[as_type]

    with measure_time() as unjsonify_time:
        unjsonify[Items](loaded)

    jsonify_per_ms = (n / jsonify_time.total * 1000)
    dump_per_ms = (n / dump_time.total * 1000)
    loads_per_ms = (n / loads_time.total * 1000)
    unjsonify_per_ms = (n / unjsonify_time.total * 1000)

    jsonify_bytes_per_ms = (bytecount / jsonify_time.total)
    dump_bytes_per_ms = (bytecount / dump_time.total)
    loads_bytes_per_ms = (bytecount / loads_time.total)
    unjsonify_bytes_per_ms = (bytecount / unjsonify_time.total)

    print(
        f'{name:<28} ({bytecount:>8} bytes)'
        f' | jsonify {jsonify_per_ms:>6.1f} n/ms'
        f' {jsonify_bytes_per_ms:>5.1f} kb/ms'
        f' | dump {dump_per_ms:>6.1f} n/ms'
        f' {dump_bytes_per_ms:>5.1f} kb/ms'
        f' | loads {loads_per_ms:>6.1f} n/ms'
        f' {loads_bytes_per_ms:>6.1f} kb/ms'
        f' | unjsonify {unjsonify_per_ms:>6.1f} n/ms'
        f' {unjsonify_bytes_per_ms:>6.1f} kb/ms'
    )


def main(n=10000):
    n = int(n)
    for _ in range(3):
        print()
        print(f'N = {n}')

        measure_case(
            n,
            {
                "name": "Pure JSON",
                "counter": 2014123,
                "enabled": False,
                "number": 132.1
            },
            as_type=dict
        )

        @dataclasses.dataclass
        class Item1:
            name: str
            subs: list[dict]

        measure_case(
            n,
            {
                "name": "Pure with inner structure",
                "subs": [
                    {
                        "type": "whatever",
                        "numbers": [i, i, i, i]
                    }
                    for i in range(10)
                ],
            },
            as_type=Item1
        )

        @dataclasses.dataclass
        class Item2:
            name: str
            date: datetime.datetime
            counter: int
            number: float

        measure_case(
            n,
            {
                "name": "Containing datetime",
                "date": datetime.datetime(2023, 7, 16, 10, 25, 0),
                "counter": 2014123,
                "number": 132.1
            },
            as_type=Item2
        )

        @dataclasses.dataclass
        class Item3:
            name: str
            box: Box

        measure_case(
            n,
            {
                "name": "Containing dataclass",
                "box": Box(
                    name="Example box",
                    width=100.1,
                    height=99.8,
                    bricks=[
                        Brick(width=3, height=2, color=color, material=material)
                        for color in Color
                        for material in list(Material) + [None]
                    ]
                ),
            },
            as_type=Item3
        )

        @dataclasses.dataclass
        class Item4:
            name: str
            expression: Expression

        measure_case(
            n,
            {
                "name": "Containing variants",
                "expression": expr,
            },
            as_type=Item4
        )



if __name__ == '__main__':
    main(*sys.argv[1:])
