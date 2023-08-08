import threading

from jsno.unjsonify import unjsonify


def test_concurrent_unjsonify():

    unjsonify._delay = 0.01
    try:
        def run_thread():
            assert unjsonify[tuple[str, ...]]([]) == ()

        threads = [
            threading.Thread(target=run_thread)
            for n in range(100)
        ]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    finally:
        unjsonify._delay = 0
