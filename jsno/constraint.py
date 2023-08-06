import re

from dataclasses import dataclass
from typing import Annotated, Any, Callable

from jsno.unjsonify import validate_annotation


class Constraint:
    """
    Base class for consraints
    """

    def __new__(cls, *args, **kwargs):
        if cls is Constraint:
            # Creating a plain Constraint actually creates a
            # FunctionConstraint
            cls = FunctionConstraint

        obj = object.__new__(cls)
        obj.__init__(*args, **kwargs)
        return obj

    def __rfloordiv__(self, type_):
        """
        Override the // operator: Annotate a type with this constraint.

        type // Constraint(...)
        """
        return Annotated[type_, self]

    def __or__(self, that: "Constraint") -> "Constraint":
        """
        Combining constraints with or-operator
        """
        return OrConstraint(self, that)

    @staticmethod
    def regex(regex, name=None):
        return RegExConstraint(
            name=(name or f"Regular expression {regex}"),
            regex=re.compile(regex),
        )

    def evaluate(self, value) -> bool:
        raise NotImplementedError()  # pragma: no cover


@dataclass(slots=True, frozen=True)
class OrConstraint(Constraint):
    left: Constraint
    right: Constraint

    def evaluate(self, value) -> bool:
        return self.left.evaluate(value) or self.right.evaluate(value)

    @property
    def name(self):
        return f'{self.left.name} or {self.right.name}'


@dataclass(slots=True, frozen=True)
class RangeConstraint(Constraint):
    value_name = "Value"

    min: Any | None = None
    max: Any | None = None

    def evaluate(self, value) -> bool:
        return (
            (self.min is None or value >= self.min) and
            (self.max is None or value <= self.max)
        )

    @property
    def name(self):
        if self.min is None:
            return f"{self.value_name} must be at least {self.min}"
        elif self.max is None:
            return f"{self.value_name} must be at most {self.max}"
        else:
            return f"{self.value_name} must be in range {self.min}..{self.max}"


class LenConstraint(RangeConstraint):
    value_name = "Length"

    def evaluate(self, value) -> bool:
        return super().evaluate(len(value))


@dataclass(slots=True, frozen=True)
class RegExConstraint(Constraint):
    name: str
    regex: re.Pattern

    def evaluate(self, value) -> bool:
        return self.regex.fullmatch(str(value)) is not None


Constraint.range = RangeConstraint  # type: ignore
Constraint.len = LenConstraint  # type: ignore


@dataclass(slots=True, frozen=True)
class FunctionConstraint(Constraint):
    function: Callable[[Any], bool]
    name: str | None = None

    def evaluate(self, value) -> bool:
        return self.function(value)


@validate_annotation.register(Constraint)
def _(constraint, value):
    if not constraint.evaluate(value):
        if constraint.name:
            message = f"Violates constraint: {constraint.name}"
        else:
            message = "Violates a constraint"

        raise ValueError(message)
