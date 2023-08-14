from jsno.utils import DictWithoutKey


def test_dict_without_key():
    base = {"x": 100, "y": 200}
    it = DictWithoutKey(base=base, key="x")

    assert list(it) == ["y"]
    assert len(it) == 1

    assert "y" in it
    assert "x" not in it
    assert it.get("x") is None

    assert it.get("y") == 200
