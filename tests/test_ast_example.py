from dataclasses import dataclass

import jsno


@jsno.variantfamily(label='type')
class Expression:
    pass


@dataclass
class LiteralInt(Expression):
    value: int

    def evaluate(self, context):
        return self.value


@dataclass
class Reference(Expression):
    name: str

    def evaluate(self, context):
        return context[self.name]


@dataclass
class BinaryOperator(Expression):
    left: Expression
    right: Expression


class Add(BinaryOperator):
    def evaluate(self, context):
        return self.left.evaluate(context) + self.right.evaluate(context)


class Multiply(BinaryOperator):
    def evaluate(self, context):
        return self.left.evaluate(context) * self.right.evaluate(context)


def test_ast():
    ast = Add(LiteralInt(1), Multiply(LiteralInt(2), Reference("x")))

    assert ast.evaluate({"x": 3}) == 7

    dumped = jsno.dumps(ast, indent=4)
    assert jsno.loads[Expression](dumped) == ast
