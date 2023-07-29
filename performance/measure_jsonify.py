import datetime
import json
import sys


from jsno import jsonify
from performance.utils import measure_time
from performance.dataclasses import example_box


def measure_case(n, item):
    name = item['name']

    items = {
        "items": [item for i in range(n)]
    }

    with measure_time() as jsonify_time:
        jsonified = jsonify(items)

    with measure_time() as dump_time:
        dump = json.dumps(jsonified)

    # microseconds per item
    jsonify_per_ms = (n / jsonify_time.total * 1000)
    dump_per_ms = (n / dump_time.total * 1000)

    jsonify_bytes_per_ms = (len(dump) / jsonify_time.total)
    dump_bytes_per_ms = (len(dump) / dump_time.total)

    print(
        f'{name:<28} ({len(dump):>8} bytes)'
        f' | jsonify {jsonify_per_ms:>6.1f} items/ms'
        f' {jsonify_bytes_per_ms:>5.1f} kb/ms'
        f' | dump {dump_per_ms:>6.1f} items/ms'
        f' {dump_bytes_per_ms:>5.1f} kb/ms'
    )


def main(n=10000):
    n = int(n)

    for _ in range(3):
        print()
        print(f'N = {n}')

        measure_case(n, {
            "name": "Pure JSON",
            "counter": 2014123,
            "enabled": False,
            "number": 132.1
        })

        measure_case(n, {
            "name": "Pure with inner structure",
            "subs": [
                {
                    "type": "whatever",
                    "numbers": [i, i, i, i]
                }
                for i in range(10)
            ],
        })

        measure_case(n, {
            "name": "Containing datetime",
            "date": datetime.datetime(2023, 7, 16, 10, 25, 0),
            "counter": 2014123,
            "number": 132.1
        })

        measure_case(n, {
            "name": "Containing dataclass",
            "box": example_box,
        })


if __name__ == '__main__':
    main(*sys.argv[1:])

