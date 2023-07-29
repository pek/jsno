import pytest

from jsno import jsonify, unjsonify, jsonify_with_method, UnjsonifyError


@jsonify_with_method
class NamedList(list):
    """
    Class for testing jsonify/unjsonify methods
    """
    def __init__(self, items=(), *, name):
        super().__init__(items)
        self.name = name

    def jsonify(self):
        return {
            "name": self.name,
            "items": jsonify[list](self)
        }

    @classmethod
    def unjsonify(cls, value):
        name = value['name']
        items = unjsonify[list](value['items'])
        return cls(items, name=name)


def test_overriding_with_jsonify_method():
    """
    Test that the jsnoify method that overrides the basic
    list jsonification works as intended.
    """

    named_list = NamedList([1, 2, 3], name="List")

    assert named_list.name == 'List'

    assert jsonify(named_list) == {'name': 'List', 'items': [1, 2, 3]}


def test_overriding_with_unjsonify_method():
    """
    Test that the unjsnoify method that overrides the basic
    list unjsonification works as intended.
    """
    assert (
        unjsonify[NamedList]({'name': 'List', 'items': [1, 2, 3]})
        ==
        NamedList([1, 2, 3], name="List")
    )


class RenamedList(NamedList):
    """
    Subclass of NmedList, to be registered with custom jsonification
    methods.
    """
    pass


@jsonify.register(RenamedList)
def _(value):
    """
    When jsonifying, add "renamed": true attribute.
    """

    # extend the NamedList's jsonification
    return {**jsonify[NamedList](value), "renamed": True}


@unjsonify.register(RenamedList)
def _(value, as_type):
    """
    When unjsonifying, check that the "renamed" flag is in the
    input data. Note: this is missing proper type checks.
    """

    if value.get("renamed") is not True:
        raise UnjsonifyError()

    return NamedList.unjsonify.__func__(as_type, value)


def test_overriding_with_jsonify_register():
    """
    Test that the registered jsonification method is called
    when jsonifying an instance of RenamedList.
    """

    named_list = RenamedList([1, 2, 3], name="List")

    assert jsonify(named_list) == {'name': 'List', 'items': [1, 2, 3], "renamed": True}


def test_overriding_with_unjsonify_register():
    """
    Test that unjsonifying gives back an instance of RenamedList, and
    make sure that the "renamed" flag is validated.
    """

    jsonified = {'name': 'List', 'items': [1, 2, 3], "renamed": True}
    unjsonified = unjsonify[RenamedList](jsonified)

    assert unjsonified == RenamedList([1, 2, 3], name="List")
    assert type(unjsonified) is RenamedList

    with pytest.raises(UnjsonifyError):
        unjsonify[RenamedList]({'name': 'List', 'items': [1, 2, 3]})
