import contextlib
import dataclasses
import time


@dataclasses.dataclass
class MeasuredTime:
    total: float = 0


@contextlib.contextmanager
def measure_time(label=None):
    start = time.perf_counter_ns()
    result = MeasuredTime()
    try:
        yield result
    finally:
        result.total = (time.perf_counter_ns() - start) * 0.001

        if label:
            print(f'{label} in {result.total:.2f} milliseconds')
