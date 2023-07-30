import jsno


def test_dumps_and_loads():

    json = jsno.dumps(complex(1, 2))
    assert json == '"(1+2j)"'

    assert jsno.loads[complex](json) == complex(1, 2)
