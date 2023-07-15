from dataclasses import dataclass

from jsno import jsonify, unjsonify, variant_family


expression_type = variant_family(tag_name='type')


@dataclass
@expression_type("literal")
class Literal:
    value: bool

    def evaluate(self, context):
        return self.value


@dataclass
@expression_type("variable")
class Variable:
    name: str

    def evaluate(self, context):
        return context[self.name]


@dataclass
@expression_type("not")
class Not:
    expr: expression_type

    def evaluate(self, context):
        return not self.expr.evaluate(context)


@dataclass
class BinaryExpression:
    left: expression_type
    right: expression_type


@dataclass
@expression_type("and")
class And(BinaryExpression):
    def evaluate(self, context):
        return self.left.evaluate(context) and self.right.evaluate(context)


@dataclass
@expression_type("or")
class Or(BinaryExpression):
    def evaluate(self, context):
        return self.left.evaluate(context) or self.right.evaluate(context)


expr = And(Not(Variable("x")), Or(Variable("y"), Literal(False)))


def test_expression_evaluation():
   assert expr.evaluate({"x": False, "y": True}) is True


def test_jsonify_variant():
    jsonified =  jsonify(expr)
    assert jsonified == {
        "type": "and",
        "left": {
            "type": "not",
            "expr": {
                "type": "variable",
                "name": "x"
            }
        },
        "right": {
            "type": "or",
            "left": {
                "type": "variable",
                "name": "y"
            },
            "right": {
                "type": "literal",
                "value": False
            }
        }
    }

    unjsonified = unjsonify[expression_type](jsonified)

    assert unjsonified == expr
