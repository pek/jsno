from dataclasses import dataclass

import pytest

from jsno import jsonify, unjsonify, variantclass, variantlabel, dumps, UnjsonifyError



@variantclass(label='type')
class Expression:
    pass


@dataclass
class Literal(Expression):
    value: bool

    def evaluate(self, context):
        return self.value


@dataclass
class Variable(Expression):
    name: str

    def evaluate(self, context):
        return context[self.name]


@dataclass
@variantlabel('NOT')
class Not(Expression):
    expr: Expression

    def evaluate(self, context):
        return not self.expr.evaluate(context)


@dataclass
class BinaryExpression(Expression):
    left: Expression
    right: Expression


@dataclass
class And(BinaryExpression):
    def evaluate(self, context):
        return self.left.evaluate(context) and self.right.evaluate(context)


@dataclass
class Or(BinaryExpression):
    def evaluate(self, context):
        return self.left.evaluate(context) or self.right.evaluate(context)


expr = And(Not(Variable("x")), Or(Variable("y"), Literal(False)))


def test_expression_evaluation():
   assert expr.evaluate({"x": False, "y": True}) is True


def test_jsonify_variant():
    jsonified =  jsonify(expr)
  #  print(dumps(expr, indent=4 ))
    assert jsonified == {
        "type": "And",
        "left": {
            "type": "NOT",
            "expr": {
                "type": "Variable",
                "name": "x"
            }
        },
        "right": {
            "type": "Or",
            "left": {
                "type": "Variable",
                "name": "y"
            },
            "right": {
                "type": "Literal",
                "value": False
            }
        }
    }

    unjsonified = unjsonify[Expression](jsonified)

    assert unjsonified == expr


def test_jsonify_variant_not_subclass_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[Or]({"type": "Literal", "value": False})


def test_jsonify_variant_unknown_label_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[Expression]({"type": "Whatever", "value": False})


def test_jsonify_variant_no_label_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[Expression]({"x-type": "Literal", "value": False})

def test_jsonify_variant_not_dict_error():
    with pytest.raises(UnjsonifyError):
        unjsonify[Expression]("Something else")
