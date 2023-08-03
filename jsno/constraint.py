import re

from dataclasses import dataclass
from typing import Annotated, Any, Callable

from jsno.unjsonify import validate_annotation


class Constraint:
    def __new__(cls, *args, **kwargs):
        if cls is Constraint:
            cls = FunctionConstraint

        obj = object.__new__(cls)
        obj.__init__(*args, **kwargs)
        return obj


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

class RegExConstraint(Constraint):

    def __init__(self, regex, name=None):
        self.regex = re.compile(regex)
        self.name = name or f"Regular expression {regex}"

    def evaluate(self, value: str) -> bool:
        return self.regex.fullmatch(value) is not None


Constraint.range = RangeConstraint  # type: ignore
Constraint.len = LenConstraint  # type: ignore
Constraint.regex = RegExConstraint  # type: ignore


@dataclass(slots=True, frozen=True)
class FunctionConstraint(Constraint):
    evaluate: Callable[[Any], bool]
    name: str | None = None


@validate_annotation.register(Constraint)
def _(constraint, value):
    if not constraint.evaluate(value):
        if constraint.name:
            message = f"Violates constraint: {constraint.name}"
        else:
            message = "Violates a constraint"

        raise ValueError(message)
